#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
csv_zip_router.py

Scan a directory for *.csv.zip files, extract CSVs, and route them to the
right destination folders using a user-provided mapping of filename patterns.

- Mapping supports glob-style patterns (e.g., "sales_*.csv", "*/kpi_*.csv").
- Patterns are matched against the inner CSV filename (fallback: zip name).
- Supports JSON or YAML mapping files.
- Options: dry-run, verbose, on-conflict behavior (overwrite|skip|rename).

Usage examples:
  python csv_zip_router.py /path/to/zips \
    --mapping routes.json \
    --default-dest /data/landing/misc \
    --on-conflict rename \
    --workers 4 \
    --dry-run

  python csv_zip_router.py /path/to/zips \
    --mapping routes.yaml \
    --verbose
"""

from __future__ import annotations
import argparse
import fnmatch
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

try:
    import yaml  # optional
except Exception:
    yaml = None

# keep dependencies minimal; no Excel conversions here


# --------------------------- Month logic utilities ---------------------------

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def get_next_month(current_month: str) -> str:
    """Get the next month in the cycle. Dec -> Jan."""
    try:
        current_index = MONTHS.index(current_month)
        next_index = (current_index + 1) % 12
        return MONTHS[next_index]
    except ValueError:
        return "Jan"  # fallback

def find_latest_month_in_destination(dest_dir: Path, base_filename: str) -> Optional[str]:
    """
    Find the latest month suffix in the destination directory for a given base filename.
    Returns the month string (e.g., 'Aug') or None if no files found.
    """
    if not dest_dir.exists():
        return None
    
    # Pattern to match: BASE_RISTOURNABLE_2025_Aug.csv
    pattern = re.compile(rf"^{re.escape(base_filename)}_({'|'.join(MONTHS)})\.csv$")
    
    found_months = []
    for file_path in dest_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == '.csv':
            match = pattern.match(file_path.name)
            if match:
                found_months.append(match.group(1))
    
    if not found_months:
        return None
    
    # Return the latest month (last in alphabetical order for our use case)
    return max(found_months)

def add_month_suffix_to_filename(filename: str, month: str) -> str:
    """Add month suffix to filename before the extension."""
    path = Path(filename)
    return f"{path.stem}_{month}{path.suffix}"

# removed previous helpers for date suffix and excel conversion

# --------------------------- Mapping utilities ---------------------------

def load_mapping(mapping_path: Path) -> List[Dict[str, str]]:
    """
    Load a mapping file (JSON or YAML). Expected schema:

    JSON (array form):
      [
        {"pattern": "sales_*.csv", "dest": "/data/landing/sales"},
        {"pattern": "inventory_*.csv", "dest": "/data/landing/inventory"}
      ]

    YAML (equivalent):
      - pattern: "sales_*.csv"
        dest: "/data/landing/sales"
      - pattern: "inventory_*.csv"
        dest: "/data/landing/inventory"

    Returns a list of dicts with keys: pattern, dest.
    Raises on invalid schema.
    """
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

    if mapping_path.suffix.lower() in {".json"}:
        data = json.loads(mapping_path.read_text(encoding="utf-8"))
    elif mapping_path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is not installed. Install with: pip install pyyaml")
        data = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Unsupported mapping file type. Use .json, .yml, or .yaml")

    if not isinstance(data, list):
        raise ValueError("Mapping file must be a list of {pattern, dest} entries.")

    cleaned = []
    for i, row in enumerate(data):
        if not isinstance(row, dict) or "pattern" not in row or "dest" not in row:
            raise ValueError(f"Invalid mapping at index {i}: expected keys 'pattern' and 'dest'")
        pattern = str(row["pattern"]).strip()
        dest = str(row["dest"]).strip()
        if not pattern or not dest:
            raise ValueError(f"Empty pattern/dest at index {i}")
        cleaned.append({"pattern": pattern, "dest": dest})
    return cleaned


def resolve_destinations(
    csv_name: str,
    mapping: List[Dict[str, str]],
    default_dest: Optional[Path]
) -> List[Path]:
    """
    Given a CSV filename and the mapping rules, return all matching destination Paths.
    Returns all destinations that match the pattern (not just the first one).
    """
    destinations = []
    
    for rule in mapping:
        if fnmatch.fnmatch(csv_name, rule["pattern"]):
            dest_path = Path(rule["dest"])
            destinations.append(dest_path)
    
    # If no destinations found, use default
    if not destinations and default_dest:
        destinations.append(default_dest)
    
    return destinations


# --------------------------- Extraction logic ---------------------------

def safe_write(
    src_tmp: Path,
    dest_dir: Path,
    on_conflict: str,
    dest_filename: Optional[str] = None
) -> Path:
    """
    Move src_tmp into dest_dir respecting on_conflict:
      - overwrite: replace existing file
      - skip: keep existing file, discard src_tmp
      - rename: add _1, _2, ... suffix before extension
    Returns final path (even if skipped, returns existing path).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / (dest_filename or src_tmp.name)

    if target.exists():
        if on_conflict == "overwrite":
            target.unlink()
            return shutil.move(str(src_tmp), str(target)) and target
        elif on_conflict == "skip":
            src_tmp.unlink(missing_ok=True)
            return target
        elif on_conflict == "rename":
            stem = target.stem
            suffix = target.suffix
            counter = 1
            while True:
                candidate = dest_dir / f"{stem}_{counter}{suffix}"
                if not candidate.exists():
                    return shutil.move(str(src_tmp), str(candidate)) and candidate
                counter += 1
        else:
            src_tmp.unlink(missing_ok=True)
            raise ValueError(f"Unknown on_conflict strategy: {on_conflict}")
    else:
        return shutil.move(str(src_tmp), str(target)) and target


def extract_and_route_zip(
    zip_path: Path,
    mapping: List[Dict[str, str]],
    default_dest: Optional[Path],
    work_dir: Path,
    on_conflict: str,
    dry_run: bool = False,
    verbose: bool = False
) -> List[Tuple[Path, Optional[Path]]]:
    """
    Process one .csv.zip:
      - open zip
      - for each *.csv inside, figure destination via mapping
      - extract to temp/work dir, then move to destination
    Returns a list of (zip_path, final_csv_path_or_None_if_skipped)
    """
    results: List[Tuple[Path, Optional[Path]]] = []

    if verbose:
        logging.info(f"[ZIP] {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        logging.warning(f"Not a valid zip: {zip_path}")
        return results

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
        if not members:
            logging.warning(f"No CSV found in: {zip_path.name}")
            return results

        for member in members:
            inner_name = Path(member).name  # ignore internal folders
            dest_dirs = resolve_destinations(inner_name, mapping, default_dest)
            if not dest_dirs:
                logging.warning(f"No route for '{inner_name}'. Skipped. (Add a mapping or set --default-dest)")
                results.append((zip_path, None))
                continue

            # Use original filename for all destinations (month suffix logic is handled per destination)
            modified_name = inner_name

            if dry_run:
                for dest_dir in dest_dirs:
                    # Special handling for BASE_RISTOURNABLE files in dry-run
                    current_filename = modified_name
                    if "BASE_RISTOURNABLE" in modified_name and "P&L" in str(dest_dir):
                        base_filename = Path(modified_name).stem
                        latest_month = find_latest_month_in_destination(dest_dir, base_filename)
                        if latest_month:
                            next_month = get_next_month(latest_month)
                            current_filename = add_month_suffix_to_filename(modified_name, next_month)
                        else:
                            current_filename = add_month_suffix_to_filename(modified_name, "Sep")
                    
                    logging.info(f"[DRY-RUN] {zip_path.name} -> {current_filename} => {dest_dir}")
                    results.append((zip_path, dest_dir / current_filename))
                continue

            # Extract to a temp staging area inside work_dir
            staging_dir = work_dir / f"__staging__{zip_path.stem}"
            staging_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract once to staging area
            extracted_tmp = staging_dir / modified_name
            with zf.open(member, "r") as src, open(extracted_tmp, "wb") as dst:
                shutil.copyfileobj(src, dst)
            
            # Copy to all destinations
            temp_files_created = []
            try:
                for i, dest_dir in enumerate(dest_dirs):
                    # Special handling for BASE_RISTOURNABLE files
                    current_filename = modified_name
                    if "BASE_RISTOURNABLE" in modified_name and "P&L" in str(dest_dir):
                        # Extract base filename without extension
                        base_filename = Path(modified_name).stem
                        
                        # Find the latest month in destination directory
                        latest_month = find_latest_month_in_destination(dest_dir, base_filename)
                        
                        if latest_month:
                            # Get next month
                            next_month = get_next_month(latest_month)
                            # Add month suffix to the filename
                            current_filename = add_month_suffix_to_filename(modified_name, next_month)
                            logging.info(f"Auto-detected next month for {base_filename}: {next_month}")
                        else:
                            # No existing files, default to Sep (current month)
                            current_filename = add_month_suffix_to_filename(modified_name, "Sep")
                            logging.info(f"No existing files found, defaulting to Sep for {base_filename}")
                    
                    # Create a temporary copy for each destination to avoid conflicts
                    if current_filename != modified_name:
                        temp_file = staging_dir / current_filename
                        shutil.copy2(extracted_tmp, temp_file)
                        temp_files_created.append(temp_file)
                        final_path = safe_write(temp_file, dest_dir, on_conflict=on_conflict, dest_filename=current_filename)
                    else:
                        # Create a unique temporary copy for this destination
                        temp_file = staging_dir / f"{modified_name}_temp_{i}"
                        shutil.copy2(extracted_tmp, temp_file)
                        temp_files_created.append(temp_file)
                        final_path = safe_write(temp_file, dest_dir, on_conflict=on_conflict, dest_filename=current_filename)
                    
                    logging.info(f"Routed: {current_filename}  -->  {final_path}")
                    results.append((zip_path, final_path))
            finally:
                # Clean up all temporary files
                extracted_tmp.unlink(missing_ok=True)
                for temp_file in temp_files_created:
                    temp_file.unlink(missing_ok=True)

    return results


# --------------------------- CLI ---------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract *.csv.zip and route inner CSVs to destination folders via pattern mapping."
    )
    p.add_argument("source_dir", type=Path, help="Directory containing *.csv.zip files.")
    p.add_argument("--mapping", type=Path, required=True, help="JSON or YAML mapping file.")
    p.add_argument("--default-dest", type=Path, default=None,
                   help="Fallback destination if no pattern matches. If omitted, unmatched CSVs are skipped.")
    p.add_argument("--work-dir", type=Path, default=Path("./.csv_zip_router_work"),
                   help="Working directory for temporary extraction.")
    p.add_argument("--on-conflict", choices=["overwrite", "skip", "rename"], default="rename",
                   help="Behavior when destination file exists. Default: rename.")
    p.add_argument("--workers", type=int, default=4, help="Parallel workers. Default: 4.")
    p.add_argument("--dry-run", action="store_true", help="Do not write files, just log actions.")
    p.add_argument("--verbose", action="store_true", help="Verbose logging.")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()

    log_level = logging.INFO if args.verbose or args.dry_run else logging.WARNING
    logging.basicConfig(level=log_level, format="%(levelname)s | %(message)s")

    src_dir: Path = args.source_dir
    if not src_dir.exists():
        logging.error(f"Source directory does not exist: {src_dir}")
        return 2

    try:
        mapping = load_mapping(args.mapping)
    except Exception as e:
        logging.error(f"Failed to load mapping: {e}")
        return 2

    zips = sorted(src_dir.glob("*.csv.zip"))
    if not zips:
        logging.warning(f"No .csv.zip files found in {src_dir}")
        return 0

    args.work_dir.mkdir(parents=True, exist_ok=True)

    results: List[Tuple[Path, Optional[Path]]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [
            ex.submit(
                extract_and_route_zip,
                zp, mapping, args.default_dest, args.work_dir,
                args.on_conflict, args.dry_run, args.verbose
            )
            for zp in zips
        ]
        for fut in as_completed(futures):
            try:
                results.extend(fut.result())
            except Exception as e:
                logging.error(f"Error processing zip: {e}")

    # Cleanup empty staging dirs
    if not args.dry_run:
        for p in args.work_dir.glob("__staging__*"):
            try:
                shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass

    # Summary
    routed = sum(1 for _, dest in results if dest is not None)
    skipped = sum(1 for _, dest in results if dest is None)
    logging.info(f"Done. Routed: {routed} | Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
