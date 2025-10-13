#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Route individual files (not in zip) according to routes.json patterns.
"""

import argparse
import json
import fnmatch
import shutil
from pathlib import Path
from typing import List, Dict

def load_mapping(mapping_path: Path) -> List[Dict[str, str]]:
    """Load mapping from routes.json"""
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    return data

def resolve_destinations(filename: str, mapping: List[Dict[str, str]], target_filter: str = None) -> List[Path]:
    """Find all destinations for a filename using mapping patterns
    
    Args:
        filename: Name of file to route
        mapping: List of routing rules
        target_filter: Optional filter - 'scorecard', 'bb', or None for all
    
    Returns:
        List of destination paths
    """
    destinations = []
    for rule in mapping:
        if fnmatch.fnmatch(filename, rule["pattern"]):
            dest_path = Path(rule["dest"])
            
            # Apply filter if specified
            if target_filter:
                dest_str = str(dest_path).lower()
                if target_filter == 'scorecard' and 'scorecard' not in dest_str:
                    continue
                elif target_filter == 'bb' and '\\fr bb\\' not in dest_str:
                    continue
            
            destinations.append(dest_path)
    
    return destinations

def main():
    parser = argparse.ArgumentParser(description="Route individual files to destinations")
    parser.add_argument('--target', choices=['scorecard', 'bb', 'all'], default='all',
                        help='Filter destinations: scorecard, bb, or all')
    args = parser.parse_args()
    
    france_files_dir = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files")
    routes_file = Path("routes.json")
    
    # Load mapping
    mapping = load_mapping(routes_file)
    
    # Set filter
    target_filter = None if args.target == 'all' else args.target
    
    # Find files to route (exclude .zip files)
    files_to_route = []
    for file_path in france_files_dir.iterdir():
        if file_path.is_file() and not file_path.name.endswith('.zip'):
            # Check if it matches any pattern (with filter)
            destinations = resolve_destinations(file_path.name, mapping, target_filter)
            for dest in destinations:
                files_to_route.append((file_path, dest))
    
    if not files_to_route:
        print(f"No files to route (target filter: {args.target})")
        return
    
    print(f"Found {len(files_to_route)} file routing operations (target: {args.target}):")
    
    # Route files
    routed_count = 0
    for src_file, dest_dir in files_to_route:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / src_file.name
        
        # Overwrite existing files (no renaming)
        shutil.copy2(src_file, dest_file)
        print(f"  Routed: {src_file.name} --> {dest_file}")
        routed_count += 1
    
    print(f"Individual files routing completed! ({routed_count} operations)")

if __name__ == "__main__":
    main()
