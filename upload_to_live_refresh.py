#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
upload_to_live_refresh.py

Upload files to SharePoint "LIVE Refresh folder" with rotation logic:
1. Move all content from "Latest xxx" folders to "Previous xxx" folders
2. Upload new files to appropriate "Latest xxx" folders
3. Upload some files to root of "LIVE Refresh folder"

Usage:
    python upload_to_live_refresh.py
"""

import os
import shutil
from pathlib import Path

# Local paths - using OneDrive synchronized folder
LIVE_REFRESH_BASE = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Fichiers de Ramwani, Shruti 179 - LIVE Refresh folder")
FRANCE_FILES_DIR = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files")

def check_local_folder_access():
    """Check if we can access the local LIVE Refresh folder."""
    try:
        if not LIVE_REFRESH_BASE.exists():
            print(f"Error: LIVE Refresh folder not found at: {LIVE_REFRESH_BASE}")
            print("Make sure OneDrive is synchronized and the folder is accessible.")
            return False
        
        print(f"LIVE Refresh folder found at: {LIVE_REFRESH_BASE}")
        return True
        
    except Exception as e:
        print(f"Error accessing LIVE Refresh folder: {e}")
        return False

def move_latest_to_previous(latest_folder_name, previous_folder_name):
    """Move all content from Latest folder to Previous folder."""
    try:
        latest_path = LIVE_REFRESH_BASE / latest_folder_name
        previous_path = LIVE_REFRESH_BASE / previous_folder_name
        
        print(f"  Moving content from '{latest_folder_name}' to '{previous_folder_name}'...")
        
        if not latest_path.exists():
            print(f"    Latest folder not found: {latest_path}")
            return
        
        # Create previous folder if it doesn't exist
        previous_path.mkdir(parents=True, exist_ok=True)
        
        # Move all files from latest to previous
        moved_count = 0
        for item in latest_path.iterdir():
            if item.is_file():
                target = previous_path / item.name
                shutil.move(str(item), str(target))
                print(f"    Moved: {item.name}")
                moved_count += 1
            elif item.is_dir():
                # For subdirectories, move them as well
                target = previous_path / item.name
                shutil.move(str(item), str(target))
                print(f"    Moved directory: {item.name}")
                moved_count += 1
        
        if moved_count == 0:
            print(f"    No files to move in '{latest_folder_name}'")
        else:
            print(f"    Moved {moved_count} item(s)")
            
    except Exception as e:
        print(f"  Error moving {latest_folder_name} to {previous_folder_name}: {e}")

def copy_file_to_folder(local_file_path, target_folder_path, filename=None):
    """Copy a local file to a local target folder."""
    try:
        if not local_file_path.exists():
            print(f"  File not found: {local_file_path}")
            return False
        
        # Create target folder if it doesn't exist
        target_folder_path.mkdir(parents=True, exist_ok=True)
        
        # Use provided filename or original filename
        target_filename = filename or local_file_path.name
        target_file = target_folder_path / target_filename
        
        # Copy file (overwrite if exists)
        shutil.copy2(local_file_path, target_file)
        
        print(f"  Copied: {target_filename} -> {target_folder_path}")
        return True
        
    except Exception as e:
        print(f"  Error copying {local_file_path.name}: {e}")
        return False

def upload_to_live_refresh():
    """Main function to copy files to LIVE Refresh folder with rotation."""
    print("Starting upload to LIVE Refresh folder...")
    
    # Check if we can access the LIVE Refresh folder
    if not check_local_folder_access():
        return 1
    
    # Step 1: Rotate Latest -> Previous folders
    print("\n[1/3] Rotating Latest -> Previous folders...")
    
    rotation_pairs = [
        ("Latest Tarif General", "Previous Tarif General"),
        ("Latest Effectif file", "Previous Effectif file"), 
        ("Latest Sectorization", "Previous Sectorization")
    ]
    
    for latest_name, previous_name in rotation_pairs:
        move_latest_to_previous(latest_name, previous_name)
    
    # Step 2: Copy specific files to Latest folders
    print("\n[2/3] Copying files to Latest folders...")
    
    # Copy TARIF_GENERAL to Latest Tarif General
    tarif_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_TARIF_GENERAL_*.csv"))
    if tarif_files:
        latest_tarif_path = LIVE_REFRESH_BASE / "Latest Tarif General"
        copy_file_to_folder(tarif_files[0], latest_tarif_path)
    
    # Copy EFFECTIF to Latest Effectif file
    effectif_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_EFFECTIF_*.csv"))
    if effectif_files:
        latest_effectif_path = LIVE_REFRESH_BASE / "Latest Effectif file"
        copy_file_to_folder(effectif_files[0], latest_effectif_path)
    
    # Copy RMPZ to Latest Sectorization/RMPZ
    rmpz_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_RMPZ_*.csv"))
    if rmpz_files:
        latest_rmpz_path = LIVE_REFRESH_BASE / "Latest Sectorization" / "RMPZ"
        copy_file_to_folder(rmpz_files[0], latest_rmpz_path)
    
    # Copy RCCZ to Latest Sectorization/RCCZ
    rccz_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_RCCZ_*.csv"))
    if rccz_files:
        latest_rccz_path = LIVE_REFRESH_BASE / "Latest Sectorization" / "RCCZ"
        copy_file_to_folder(rccz_files[0], latest_rccz_path)
    
    # Copy SECTORISATION to Latest Sectorization/Sectorization
    sectorisation_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_SECTORISATION_*.csv"))
    if sectorisation_files:
        latest_sectorisation_path = LIVE_REFRESH_BASE / "Latest Sectorization" / "Sectorization"
        copy_file_to_folder(sectorisation_files[0], latest_sectorisation_path)
    
    # Step 3: Copy files to root of LIVE Refresh folder
    print("\n[3/3] Copying files to LIVE Refresh folder root...")
    
    # Copy MD_ITEM_DATA to root
    item_data_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_ITEM_DATA.csv"))
    if item_data_files:
        copy_file_to_folder(item_data_files[0], LIVE_REFRESH_BASE)
    
    # Copy PRODUITS_TARIF to root
    produits_tarif_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_PRODUITS_TARIF*.csv"))
    if produits_tarif_files:
        copy_file_to_folder(produits_tarif_files[0], LIVE_REFRESH_BASE)
    
    print("\nUpload to LIVE Refresh folder completed!")
    print("Files will be synchronized to SharePoint automatically via OneDrive.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(upload_to_live_refresh())