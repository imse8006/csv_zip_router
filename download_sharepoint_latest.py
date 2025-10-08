#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Download the most recent folder from a SharePoint location and its files.

Behavior:
- Auth using client credentials (app registration)
- List folders in the target library/path, pick the most recently created
- If the most recent folder is older than 7 days, print a WARNING
- Download all files in that folder to a local directory

Usage:
  python download_sharepoint_latest.py \
    --site https://sysco.sharepoint.com/sites/PGMDatabaseSyscoandBain \
    --client-id <APP_ID> \
    --client-secret <APP_SECRET> \
    --folder "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/..." \
    --out ./_downloads
"""

from __future__ import annotations
import argparse
from datetime import datetime, timedelta
import json
import fnmatch
from pathlib import Path
import sys
import ssl
import os

# Disable SSL verification BEFORE importing office365
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# Patch requests to disable SSL verification
import requests
requests.packages.urllib3.disable_warnings()

original_request = requests.Session.request
def patched_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, *args, **kwargs)
requests.Session.request = patched_request

try:
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.client_credential import ClientCredential
except Exception as e:
    print("Please install office365-rest-python-client: pip install Office365-REST-Python-Client", file=sys.stderr)
    raise


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download the latest folder contents from SharePoint")
    p.add_argument("--site", required=True, help="SharePoint site URL")
    p.add_argument("--client-id", required=True, help="Azure AD App Client ID")
    p.add_argument("--client-secret", required=True, help="Azure AD App Client Secret")
    p.add_argument("--folder", required=True, help="Target server-relative folder path")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("C:/Users/il00030293/OneDrive - Sysco Corporation/Documents/PGM/France files"),
        help="Local output directory for downloaded files",
    )
    p.add_argument("--mapping", required=True, type=Path, help="Path to routes.json used to filter which files to download")
    p.add_argument("--include-non-sysfr", action="store_true", help="Also include non-SYSFR_PGM_* patterns from routes.json (e.g., Bible, Lumpsums)")
    p.add_argument("--no-warn-age", action="store_true", help="Do not warn if latest folder is older than 7 days")
    return p.parse_args()


def pick_latest_subfolder(ctx, parent_rel_url: str):
    print(f"Looking for subfolders in: {parent_rel_url}")
    folder = ctx.web.get_folder_by_server_relative_url(parent_rel_url)
    subfolders = folder.folders
    ctx.load(subfolders)
    ctx.execute_query()

    print(f"Found {len(subfolders)} subfolders")
    for i, sf in enumerate(subfolders):
        print(f"  {i+1}. {sf.properties.get('Name', 'Unknown')}")

    latest = None
    for sf in subfolders:  # type: ignore
        # Created time may require loading list item properties
        sf_properties = sf.list_item_all_fields
        ctx.load(sf_properties)
        ctx.execute_query()
        created = sf_properties.properties.get("Created")
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00")) if isinstance(created, str) else None
        except Exception:
            created_dt = None
        if latest is None or (created_dt and created_dt > latest[1]):
            latest = (sf, created_dt)

    return latest  # (folder_obj, created_dt)


def load_patterns(mapping_path: Path, only_sysfr: bool) -> list[str]:
    """Load patterns from routes.json.
    When only_sysfr=True, restrict to those starting with SYSFR_PGM_.
    Transform .csv patterns to .csv.zip for SharePoint search.
    """
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    patterns = []
    for row in data:
        try:
            pat = str(row.get("pattern", ""))
        except Exception:
            continue
        if not pat:
            continue
        
        # Transform .csv patterns to .csv.zip for SharePoint search
        if pat.endswith(".csv"):
            pat = pat[:-4] + ".csv.zip"
        
        if only_sysfr:
            if pat.startswith("SYSFR_PGM_"):
                # Exclure les promos du premier téléchargement SYSFR_PGM_
                if pat.startswith("SYSFR_PGM_LISTE_PRIX_PROMOS_PONCT"):
                    continue
                if pat.startswith("SYSFR_PGM_LISTE_PRIX_PROMOS_PERMAN"):
                    continue
                patterns.append(pat)
        else:
            patterns.append(pat)
    return patterns


def matches_any(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def download_files_in_folder(ctx, folder_rel_url: str, out_dir: Path, patterns: list[str]) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    folder = ctx.web.get_folder_by_server_relative_url(folder_rel_url)
    files = folder.files
    ctx.load(files)
    ctx.execute_query()

    count = 0
    for f in files:  # type: ignore
        name = f.properties["Name"]
        if patterns and not matches_any(name, patterns):
            continue
        target = out_dir / name
        with open(target, "wb") as fh:
            fh.write(f.read())
        count += 1
    return count


# French month names with proper accents and Title Case
MONTHS_FR_TITLE = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


def previous_month_title_fr() -> str:
    now = datetime.now()
    idx = (now.month - 2) % 12  # previous month, 0-based
    return MONTHS_FR_TITLE[idx]


def main() -> int:
    args = parse_args()
    
    ctx = ClientContext(args.site).with_credentials(ClientCredential(args.client_id, args.client_secret))
    ctx.load(ctx.web)
    ctx.execute_query()

    latest = pick_latest_subfolder(ctx, args.folder)
    if latest is None:
        print("No subfolders found.")
        return 1

    folder_obj, created_dt = latest
    rel_url = folder_obj.serverRelativeUrl  # type: ignore
    print(f"Latest folder: {rel_url}")
    if created_dt is not None and not getattr(args, "no_warn_age", False):
        age_days = (datetime.utcnow() - created_dt.replace(tzinfo=None)).days
        if age_days > 7:
            print(f"WARNING: Latest folder is {age_days} days old (>7 days)")
    # Additional check for the 5-file drop: folder name should contain last month in French (Title Case)
    if getattr(args, "include_non_sysfr", False):
        expected_month = previous_month_title_fr()
        folder_name = rel_url.rsplit('/', 1)[-1]
        if expected_month not in folder_name:
            print(f"WARNING: Expected month name '{expected_month}' not found in folder name '{folder_name}'")

    patterns = load_patterns(args.mapping, only_sysfr=not args.include_non_sysfr)
    downloaded = download_files_in_folder(ctx, rel_url, args.out, patterns)
    print(f"Downloaded {downloaded} file(s) from latest folder into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


