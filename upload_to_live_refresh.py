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
import ssl
from pathlib import Path
import time

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

from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.files.file import File
from office365.runtime.auth.authentication_context import AuthenticationContext

# SharePoint Configuration - using environment variables
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "https://sysco.sharepoint.com/sites/PGMDatabaseSyscoandBain")
CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID", "2e4aa039-2d8a-4974-991a-063b4aa97378")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET", "")

# Base path for LIVE Refresh folder (to be updated with correct path)
LIVE_REFRESH_BASE = "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/FR/3. Exports de données pour Bain/2. Exports hebdomadaires/LIVE Refresh folder"

# Local directory where processed files are located
FRANCE_FILES_DIR = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files")

def get_sharepoint_context():
    """Get authenticated SharePoint context."""
    try:
        if not CLIENT_SECRET:
            print("Error: SHAREPOINT_CLIENT_SECRET environment variable not set")
            return None
            
        ctx = ClientContext(SHAREPOINT_SITE_URL).with_credentials(
            ClientCredential(CLIENT_ID, CLIENT_SECRET)
        )
        ctx.load(ctx.web)
        ctx.execute_query()
        print("SharePoint authentication successful")
        return ctx
    except Exception as e:
        print(f"SharePoint authentication failed: {e}")
        return None

def move_latest_to_previous(ctx, latest_folder_name, previous_folder_name):
    """Move all content from Latest folder to Previous folder."""
    try:
        latest_path = f"{LIVE_REFRESH_BASE}/{latest_folder_name}"
        previous_path = f"{LIVE_REFRESH_BASE}/{previous_folder_name}"
        
        print(f"  Moving content from '{latest_folder_name}' to '{previous_folder_name}'...")
        
        # Get Latest folder
        latest_folder = ctx.web.get_folder_by_server_relative_url(latest_path)
        ctx.load(latest_folder)
        ctx.execute_query()
        
        # Get Previous folder
        previous_folder = ctx.web.get_folder_by_server_relative_url(previous_path)
        ctx.load(previous_folder)
        ctx.execute_query()
        
        # Get all files in Latest folder
        files = latest_folder.files
        ctx.load(files)
        ctx.execute_query()
        
        if files:
            for file in files:
                # Copy file to Previous folder
                file_url = f"{previous_path}/{file.properties['Name']}"
                file.move_to(file_url)
                ctx.execute_query()
                print(f"    Moved: {file.properties['Name']}")
        else:
            print(f"    No files to move in '{latest_folder_name}'")
            
    except Exception as e:
        print(f"  Error moving {latest_folder_name} to {previous_folder_name}: {e}")

def upload_file_to_folder(ctx, local_file_path, target_folder_path, filename=None):
    """Upload a local file to a SharePoint folder."""
    try:
        if not local_file_path.exists():
            print(f"  File not found: {local_file_path}")
            return False
            
        target_folder = ctx.web.get_folder_by_server_relative_url(target_folder_path)
        ctx.load(target_folder)
        ctx.execute_query()
        
        # Use provided filename or original filename
        upload_filename = filename or local_file_path.name
        
        with open(local_file_path, "rb") as file_content:
            target_folder.files.add(upload_filename, file_content, True)  # True = overwrite
            ctx.execute_query()
        
        print(f"  Uploaded: {upload_filename} -> {target_folder_path}")
        return True
        
    except Exception as e:
        print(f"  Error uploading {local_file_path.name}: {e}")
        return False

def upload_to_live_refresh():
    """Main function to upload files to LIVE Refresh folder with rotation."""
    print("Starting upload to LIVE Refresh folder...")
    
    ctx = get_sharepoint_context()
    if not ctx:
        return 1
    
    # Step 1: Rotate Latest -> Previous folders
    print("\n[1/3] Rotating Latest -> Previous folders...")
    
    rotation_pairs = [
        ("Latest Tarif General", "Previous Tarif General"),
        ("Latest Effectif file", "Previous Effectif file"), 
        ("Latest Sectorization", "Previous Sectorization")
    ]
    
    for latest_name, previous_name in rotation_pairs:
        move_latest_to_previous(ctx, latest_name, previous_name)
    
    # Step 2: Upload specific files to Latest folders
    print("\n[2/3] Uploading files to Latest folders...")
    
    # Upload TARIF_GENERAL to Latest Tarif General
    tarif_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_TARIF_GENERAL_*.csv"))
    if tarif_files:
        latest_tarif_path = f"{LIVE_REFRESH_BASE}/Latest Tarif General"
        upload_file_to_folder(ctx, tarif_files[0], latest_tarif_path)
    
    # Upload EFFECTIF to Latest Effectif file
    effectif_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_EFFECTIF_*.csv"))
    if effectif_files:
        latest_effectif_path = f"{LIVE_REFRESH_BASE}/Latest Effectif file"
        upload_file_to_folder(ctx, effectif_files[0], latest_effectif_path)
    
    # Upload RMPZ to Latest Sectorization/RMPZ
    rmpz_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_RMPZ_*.csv"))
    if rmpz_files:
        latest_rmpz_path = f"{LIVE_REFRESH_BASE}/Latest Sectorization/RMPZ"
        upload_file_to_folder(ctx, rmpz_files[0], latest_rmpz_path)
    
    # Upload RCCZ to Latest Sectorization/RCCZ
    rccz_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_RCCZ_*.csv"))
    if rccz_files:
        latest_rccz_path = f"{LIVE_REFRESH_BASE}/Latest Sectorization/RCCZ"
        upload_file_to_folder(ctx, rccz_files[0], latest_rccz_path)
    
    # Upload SECTORISATION to Latest Sectorization/Sectorization
    sectorisation_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_SECTORISATION_*.csv"))
    if sectorisation_files:
        latest_sectorisation_path = f"{LIVE_REFRESH_BASE}/Latest Sectorization/Sectorization"
        upload_file_to_folder(ctx, sectorisation_files[0], latest_sectorisation_path)
    
    # Step 3: Upload files to root of LIVE Refresh folder
    print("\n[3/3] Uploading files to LIVE Refresh folder root...")
    
    # Upload MD_ITEM_DATA to root
    item_data_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_MD_ITEM_DATA.csv"))
    if item_data_files:
        upload_file_to_folder(ctx, item_data_files[0], LIVE_REFRESH_BASE)
    
    # Upload PRODUITS_TARIF to root
    produits_tarif_files = list(FRANCE_FILES_DIR.glob("SYSFR_PGM_PRODUITS_TARIF*.csv"))
    if produits_tarif_files:
        upload_file_to_folder(ctx, produits_tarif_files[0], LIVE_REFRESH_BASE)
    
    print("\nUpload to LIVE Refresh folder completed!")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(upload_to_live_refresh())