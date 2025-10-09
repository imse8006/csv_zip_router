#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
process_non_sysfr_files.py

Process the 5 non-SYSFR_PGM_ files downloaded from SharePoint:
1. Lumpsums - already handled by deduplicate_lumpsums.py
2. SUPPLIERS_PROMOTION_DATA - convert XLSB to CSV with number formatting
3. PROMOS_PONCTUELLES - no processing needed
4. PROMOS_PERMANENTES - no processing needed  
5. BIBLE - convert XLSB to XLSX with month suffix

Usage:
    python process_non_sysfr_files.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re

# Try to import pyxlsb for .xlsb files
try:
    import pyxlsb
    HAS_PYXLSB = True
except ImportError:
    HAS_PYXLSB = False
    print("Warning: pyxlsb not installed. Cannot read .xlsb files. Install with: pip install pyxlsb")

# Base directory where downloads are placed
FRANCE_FILES_DIR = Path(r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files")

# Keep processed files in France files directory for routing

# Month names in English
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def get_previous_month() -> str:
    """Get the previous month in English format."""
    now = datetime.now()
    prev_month_index = (now.month - 2) % 12  # 0-based index for previous month
    return MONTHS_EN[prev_month_index]

def process_suppliers_promotion_data():
    """Process SUPPLIERS_PROMOTION_DATA file: convert XLSB to CSV with number formatting."""
    print("Processing SUPPLIERS_PROMOTION_DATA...")
    
    # Find the file
    pattern = "SYSFR_PGM_SUPPLIERS_PROMOTION_DATA*.xlsb"
    files = list(FRANCE_FILES_DIR.glob(pattern))
    
    if not files:
        print(f"  No file found matching pattern: {pattern}")
        return
    
    input_file = files[0]
    print(f"  Found file: {input_file.name}")
    
    if not HAS_PYXLSB:
        print(f"  Error: Cannot process .xlsb files without pyxlsb. Install with: pip install pyxlsb")
        return
    
    try:
        # Read XLSB file using pyxlsb
        df = pd.read_excel(input_file, engine='pyxlsb')
        
        # Convert columns F and G to numeric
        if 'Remises / Promo' in df.columns:
            df['Remises / Promo'] = pd.to_numeric(df['Remises / Promo'], errors='coerce')
        if 'Total Spend' in df.columns:
            df['Total Spend'] = pd.to_numeric(df['Total Spend'], errors='coerce')
        
        # Create output filename (keep in France files for routing)
        output_file = FRANCE_FILES_DIR / f"{input_file.stem}.csv"
        
        # Save as CSV UTF-8 with semicolon separator
        df.to_csv(output_file, index=False, encoding='utf-8', sep='|')
        print(f"  Saved to: {output_file}")
        
    except Exception as e:
        print(f"  Error processing SUPPLIERS_PROMOTION_DATA: {e}")

def process_bible():
    """Process BIBLE file: rename with previous month suffix."""
    print("Processing BIBLE...")
    
    # Find the file
    pattern = "Bible 3xNET Conso *.xlsb"
    files = list(FRANCE_FILES_DIR.glob(pattern))
    
    if not files:
        print(f"  No file found matching pattern: {pattern}")
        return
    
    input_file = files[0]
    print(f"  Found file: {input_file.name}")
    
    try:
        # Extract year from filename (e.g., "Bible 3xNET Conso 2025.xlsb" -> "2025")
        year_match = re.search(r'(\d{4})', input_file.stem)
        if not year_match:
            print(f"  Could not extract year from filename: {input_file.name}")
            return
        
        year = year_match.group(1)
        prev_month = get_previous_month()
        
        # Create new filename with previous month
        new_filename = f"Bible 3xNET Conso {year} {prev_month}.xlsb"
        output_file = FRANCE_FILES_DIR / new_filename
        
        # Check for existing files in France files directory (excluding the current file)
        existing_files = [f for f in FRANCE_FILES_DIR.glob("Bible 3xNET Conso *.xlsb") 
                         if f.name != input_file.name and ' ' in f.stem.split()[-1]]
        
        if existing_files:
            # Get the most recent file
            latest_existing = max(existing_files, key=lambda p: p.stat().st_mtime)
            # Extract month from latest existing file
            latest_month_match = re.search(r'\b(' + '|'.join(MONTHS_EN) + r')\b', latest_existing.stem)
            
            if latest_month_match:
                latest_month = latest_month_match.group(1)
                # Get expected previous month (should be 2 months before current)
                expected_prev_month = MONTHS_EN[(datetime.now().month - 3) % 12]
                
                if latest_month != expected_prev_month:
                    print(f"  WARNING: Latest existing file has month '{latest_month}', expected '{expected_prev_month}'")
                else:
                    print(f"  ✓ Verified: Latest existing file month is correct ({latest_month})")
        
        # Rename the file
        input_file.rename(output_file)
        print(f"  Renamed to: {output_file.name}")
        
    except Exception as e:
        print(f"  Error processing BIBLE: {e}")

def process_promos_ponctuelles():
    """Process PROMOS_PONCTUELLES file: no processing needed."""
    print("Processing PROMOS_PONCTUELLES...")
    
    pattern = "SYSFR_PGM_LISTE_PRIX_PROMOS_PONCT*.xlsx"
    files = list(FRANCE_FILES_DIR.glob(pattern))
    
    if not files:
        print(f"  No file found matching pattern: {pattern}")
        return
    
    print(f"  Found file: {files[0].name} - no processing needed")

def process_promos_permanentes():
    """Process PROMOS_PERMANENTES file: no processing needed."""
    print("Processing PROMOS_PERMANENTES...")
    
    pattern = "SYSFR_PGM_LISTE_PRIX_PROMOS_PERMAN*.xlsx"
    files = list(FRANCE_FILES_DIR.glob(pattern))
    
    if not files:
        print(f"  No file found matching pattern: {pattern}")
        return
    
    print(f"  Found file: {files[0].name} - no processing needed")

def main():
    """Process all non-SYSFR_PGM_ files."""
    print("Processing non-SYSFR_PGM_ files...")
    print(f"Source directory: {FRANCE_FILES_DIR}")
    
    if not FRANCE_FILES_DIR.exists():
        print(f"Error: Source directory does not exist: {FRANCE_FILES_DIR}")
        return 1
    
    # Process each file type
    process_suppliers_promotion_data()
    process_bible()
    process_promos_ponctuelles()
    process_promos_permanentes()
    
    print("Non-SYSFR_PGM_ files processing completed.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
