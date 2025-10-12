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
import re
import shutil
import zipfile
import tempfile
from pathlib import Path

# Local paths - using OneDrive synchronized folder
LIVE_REFRESH_BASE = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Fichiers de Ramwani, Shruti 179 - Better Selling\LIVE Refresh folder")
FRANCE_FILES_DIR = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files")

def extract_week_number(filename):
    """Extract week number from filename (e.g., EFFECTIF_2025_40.csv -> 202540)."""
    match = re.search(r'_(\d{4})_(\d{2})\.csv', str(filename))
    if match:
        year = int(match.group(1))
        week = int(match.group(2))
        return year * 100 + week  # Returns 202540 for comparison
    return 0

def check_if_update_needed():
    """Check if new files are more recent than existing ones in Latest folder."""
    try:
        # Check one representative file (TARIF_GENERAL)
        new_zip_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_TARIF_GENERAL_*.zip"))
        
        if not new_zip_files:
            print(f"\n{'='*80}")
            print(f"[X] LIVE Refresh update SKIPPED")
            print(f"{'='*80}")
            print(f"Reason: No new files found in France files directory")
            print(f"France files directory: {FRANCE_FILES_DIR}")
            print(f"{'='*80}\n")
            return False  # STOP if no files
        
        # Extract week number from new file
        new_week = extract_week_number(new_zip_files[0].name)
        
        if new_week == 0:
            print(f"\n{'='*80}")
            print(f"[X] LIVE Refresh update SKIPPED")
            print(f"{'='*80}")
            print(f"Reason: Cannot extract week number from file: {new_zip_files[0].name}")
            print(f"{'='*80}\n")
            return False
        
        # Check existing file in Latest folder
        latest_folder = LIVE_REFRESH_BASE / "Latest Tarif General"
        if not latest_folder.exists():
            print(f"\n✓ Version check passed: Latest folder doesn't exist yet, proceeding with initial upload")
            return True
        
        existing_files = list(latest_folder.glob("SYSFR_PGM_TARIF_GENERAL_*.csv"))
        
        if not existing_files:
            print(f"\n✓ Version check passed: No existing files in Latest folder, proceeding with initial upload")
            return True
        
        # Extract week number from existing file
        old_week = extract_week_number(existing_files[0].name)
        
        if old_week == 0:
            print(f"\n✓ Version check passed: Cannot determine existing version, proceeding with update")
            return True
        
        # Compare versions
        if new_week <= old_week:
            print(f"\n{'='*80}")
            print(f"[!] LIVE Refresh update SKIPPED")
            print(f"{'='*80}")
            print(f"Reason: New files (week {new_week % 100}) are NOT more recent than existing files (week {old_week % 100})")
            print(f"New file: {new_zip_files[0].name}")
            print(f"Existing file: {existing_files[0].name}")
            print(f"{'='*80}\n")
            return False
        
        print(f"\n{'='*80}")
        print(f"[OK] Version check PASSED")
        print(f"{'='*80}")
        print(f"New files (week {new_week % 100}) are more recent than existing files (week {old_week % 100})")
        print(f"New file: {new_zip_files[0].name}")
        print(f"Existing file: {existing_files[0].name}")
        print(f"Proceeding with rotation and update...")
        print(f"{'='*80}\n")
        return True
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"[X] LIVE Refresh update SKIPPED")
        print(f"{'='*80}")
        print(f"Reason: Error checking version: {e}")
        print(f"{'='*80}\n")
        return False  # STOP on error to avoid data loss

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

def rotate_files_to_previous(latest_folder_name, previous_folder_name):
    """Move files from Latest to Previous, preserving folder structure."""
    try:
        latest_path = LIVE_REFRESH_BASE / latest_folder_name
        previous_path = LIVE_REFRESH_BASE / previous_folder_name
        
        print(f"  Rotating '{latest_folder_name}' -> '{previous_folder_name}'...")
        
        if not latest_path.exists():
            print(f"    Latest folder not found: {latest_path}")
            return
        
        # Ensure previous folder exists
        previous_path.mkdir(parents=True, exist_ok=True)
        
        # First, clear old files in Previous folder
        print(f"    Clearing old files in '{previous_folder_name}'...")
        old_deleted = clear_files_in_folder(previous_path, preserve_subfolders=True)
        if old_deleted > 0:
            print(f"    Deleted {old_deleted} old file(s)")
        
        # Now move files from Latest to Previous
        moved_count = move_files_between_folders(latest_path, previous_path)
        
        if moved_count == 0:
            print(f"    No files to rotate in '{latest_folder_name}'")
        else:
            print(f"    Moved {moved_count} file(s) to '{previous_folder_name}'")
            
    except Exception as e:
        print(f"  Error rotating {latest_folder_name}: {e}")

def move_files_between_folders(source_folder, dest_folder):
    """Move files from source to destination, preserving subfolder structure."""
    if not source_folder.exists():
        return 0
    
    moved_count = 0
    for item in source_folder.iterdir():
        try:
            if item.is_file():
                # Move file to destination
                dest_file = dest_folder / item.name
                shutil.move(str(item), str(dest_file))
                print(f"    Moved: {item.name}")
                moved_count += 1
            elif item.is_dir():
                # Recursively move files in subdirectories
                dest_subfolder = dest_folder / item.name
                dest_subfolder.mkdir(parents=True, exist_ok=True)
                sub_moved = move_files_between_folders(item, dest_subfolder)
                moved_count += sub_moved
        except Exception as e:
            print(f"    Warning: Could not move {item.name}: {e}")
    
    return moved_count

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
    
    # Check if update is needed (version check)
    if not check_if_update_needed():
        return 0  # Exit gracefully, no update needed
    
    # Step 1: Rotate Latest -> Previous folders
    print("\n[1/3] Rotating Latest -> Previous folders...")
    
    rotation_pairs = [
        ("Latest Tarif General", "Previous Tarif General"),
        ("Latest Effectif file", "Previous Effectif file"), 
        ("Latest Sectorization", "Previous Sectorization")
    ]
    
    for latest_name, previous_name in rotation_pairs:
        rotate_files_to_previous(latest_name, previous_name)
    
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