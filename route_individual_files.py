#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Route individual files (not in zip) according to routes.json patterns.
"""

import json
import fnmatch
import shutil
from pathlib import Path
from typing import List, Dict

def load_mapping(mapping_path: Path) -> List[Dict[str, str]]:
    """Load mapping from routes.json"""
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    return data

def resolve_destination(filename: str, mapping: List[Dict[str, str]]) -> Path:
    """Find destination for a filename using mapping patterns"""
    for rule in mapping:
        if fnmatch.fnmatch(filename, rule["pattern"]):
            return Path(rule["dest"])
    return None

def main():
    france_files_dir = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files")
    routes_file = Path("routes.json")
    
    # Load mapping
    mapping = load_mapping(routes_file)
    
    # Find files to route (exclude .zip files)
    files_to_route = []
    for file_path in france_files_dir.iterdir():
        if file_path.is_file() and not file_path.name.endswith('.zip'):
            # Check if it matches any pattern
            dest = resolve_destination(file_path.name, mapping)
            if dest:
                files_to_route.append((file_path, dest))
    
    print(f"Found {len(files_to_route)} files to route:")
    
    # Route files
    for src_file, dest_dir in files_to_route:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / src_file.name
        
        # Overwrite existing files (no renaming)
        shutil.copy2(src_file, dest_file)
        print(f"Routed: {src_file.name} --> {dest_file}")
    
    print("Individual files routing completed!")

if __name__ == "__main__":
    main()
