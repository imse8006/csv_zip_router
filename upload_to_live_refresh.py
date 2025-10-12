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
import zipfile
import tempfile
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

def clear_files_in_folder(folder_path, preserve_subfolders=False):
    """Clear files in a folder, optionally preserving subfolder structure."""
    if not folder_path.exists():
        return 0
    
    deleted_count = 0
    for item in folder_path.iterdir():
        try:
            if item.is_file():
                item.unlink()
                print(f"    Deleted: {item.name}")
                deleted_count += 1
            elif item.is_dir() and preserve_subfolders:
                # Recursively clear files in subfolders
                sub_deleted = clear_files_in_folder(item, preserve_subfolders=True)
                deleted_count += sub_deleted
        except Exception as e:
            print(f"    Warning: Could not delete {item.name}: {e}")
    
    return deleted_count

def clear_latest_folder(latest_folder_name, previous_folder_name):
    """Clear files in Latest folder without touching folder structure."""
    try:
        latest_path = LIVE_REFRESH_BASE / latest_folder_name
        previous_path = LIVE_REFRESH_BASE / previous_folder_name
        
        print(f"  Clearing files in '{latest_folder_name}' (keeping folder structure)...")
        
        if not latest_path.exists():
            print(f"    Latest folder not found: {latest_path}")
            return
        
        # Just clear the files, preserve all folder structure
        deleted_count = clear_files_in_folder(latest_path, preserve_subfolders=True)
        
        if deleted_count == 0:
            print(f"    No files to clear in '{latest_folder_name}'")
        else:
            print(f"    Cleared {deleted_count} file(s)")
            
    except Exception as e:
        print(f"  Error clearing {latest_folder_name}: {e}")

def extract_csv_from_zip(zip_path):
    """Extract CSV file from ZIP archive, preserving the original filename."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find CSV files in the archive
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            
            if not csv_files:
                print(f"  No CSV file found in {zip_path.name}")
                return None, None
            
            # Use the first CSV file
            csv_filename = csv_files[0]
            
            # Extract to temporary directory with original filename
            temp_dir = Path(tempfile.gettempdir()) / "csv_zip_router_temp"
            temp_dir.mkdir(exist_ok=True)
            
            # Extract with original name
            zip_ref.extract(csv_filename, temp_dir)
            temp_path = temp_dir / csv_filename
            
            print(f"  Extracted: {csv_filename} from {zip_path.name}")
            return temp_path, csv_filename
            
    except Exception as e:
        print(f"  Error extracting CSV from {zip_path.name}: {e}")
        return None, None

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
    
    # Step 1: Clear Latest folders (move to Previous then delete Previous)
    print("\n[1/3] Clearing Latest folders...")
    
    rotation_pairs = [
        ("Latest Tarif General", "Previous Tarif General"),
        ("Latest Effectif file", "Previous Effectif file"), 
        ("Latest Sectorization", "Previous Sectorization")
    ]
    
    for latest_name, previous_name in rotation_pairs:
        clear_latest_folder(latest_name, previous_name)
    
    # Step 2: Copy specific files to Latest folders
    print("\n[2/3] Copying files to Latest folders...")
    
    temp_files = []  # Keep track of temporary files to clean up
    
    # Copy TARIF_GENERAL to Latest Tarif General
    tarif_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_TARIF_GENERAL_*.zip"))
    if tarif_zip_files:
        latest_tarif_path = LIVE_REFRESH_BASE / "Latest Tarif General"
        temp_csv, csv_filename = extract_csv_from_zip(tarif_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, latest_tarif_path, csv_filename)
    
    # Copy EFFECTIF to Latest Effectif file
    effectif_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_EFFECTIF_*.zip"))
    if effectif_zip_files:
        latest_effectif_path = LIVE_REFRESH_BASE / "Latest Effectif file"
        temp_csv, csv_filename = extract_csv_from_zip(effectif_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, latest_effectif_path, csv_filename)
    
    # Copy RMPZ to Latest Sectorization/RMPZ
    rmpz_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_RMPZ_*.zip"))
    if rmpz_zip_files:
        latest_rmpz_path = LIVE_REFRESH_BASE / "Latest Sectorization" / "RMPZ"
        temp_csv, csv_filename = extract_csv_from_zip(rmpz_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, latest_rmpz_path, csv_filename)
    
    # Copy RCCZ to Latest Sectorization/RCCZ
    rccz_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_RCCZ_*.zip"))
    if rccz_zip_files:
        latest_rccz_path = LIVE_REFRESH_BASE / "Latest Sectorization" / "RCCZ"
        temp_csv, csv_filename = extract_csv_from_zip(rccz_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, latest_rccz_path, csv_filename)
    
    # Copy SECTORISATION to Latest Sectorization/Sectorization
    sectorisation_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_SECTORISATION_*.zip"))
    if sectorisation_zip_files:
        latest_sectorisation_path = LIVE_REFRESH_BASE / "Latest Sectorization" / "Sectorization"
        temp_csv, csv_filename = extract_csv_from_zip(sectorisation_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, latest_sectorisation_path, csv_filename)
    
    # Step 3: Copy files to root of LIVE Refresh folder
    print("\n[3/3] Copying files to LIVE Refresh folder root...")
    
    # Copy MD_ITEM_DATA to root
    item_data_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_ITEM_DATA.csv.zip"))
    if item_data_zip_files:
        temp_csv, csv_filename = extract_csv_from_zip(item_data_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, LIVE_REFRESH_BASE, csv_filename)
    
    # Copy PRODUITS_TARIF to root
    produits_tarif_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_PRODUITS_TARIF*.zip"))
    if produits_tarif_zip_files:
        temp_csv, csv_filename = extract_csv_from_zip(produits_tarif_zip_files[0])
        if temp_csv:
            temp_files.append(temp_csv)
            copy_file_to_folder(temp_csv, LIVE_REFRESH_BASE, csv_filename)
    
    # Clean up temporary files
    print("\nCleaning up temporary files...")
    for temp_file in temp_files:
        try:
            temp_file.unlink()
            print(f"  Deleted temporary file: {temp_file.name}")
        except Exception as e:
            print(f"  Warning: Could not delete temporary file {temp_file.name}: {e}")
    
    print("\nUpload to LIVE Refresh folder completed!")
    print("Files will be synchronized to SharePoint automatically via OneDrive.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(upload_to_live_refresh())