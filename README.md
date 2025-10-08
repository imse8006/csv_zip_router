# csv_zip_router – Complete Pipeline Documentation

## Overview
This pipeline automatically downloads files from SharePoint, processes them, and routes them to their correct destinations based on pattern matching rules.

## Complete Process Flow

### 1. Download SharePoint Files
- **SYSFR_PGM_ files**: Downloads all SYSFR_PGM_ files that are defined in `routes.json` (excluding Promo Ponctuelle/Permanente) from the first SharePoint link
- **5 non-SYSFR_PGM_ files**: Downloads 5 specific files from the second SharePoint link:
  - `SYSFR_PGM_SUPPLIERS_PROMOTION_DATA*.xlsb`
  - `Lumpsums - v*.xlsb`
  - `Bible 3xNET Conso *.xlsb`
  - `SYSFR_PGM_LISTE_PRIX_PROMOS_PONCT*.xlsb`
  - `SYSFR_PGM_LISTE_PRIX_PROMOS_PERMAN*.xlsb`
- **Destination**: All files go to `C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files`
- **Validations**: 
  - Warns if the latest folder is older than 7 days
  - Checks that folder name contains the previous month in French (e.g., "Septembre" in October)

### 2. Pause (configurable, default 10s)
- Allows large files to stabilize before processing

### 3. Process Lumpsums
- Finds the latest `Lumpsums - v*.xlsb` file in France files
- Applies deduplication on "Code Article / Code Sous-Gamme" column (splits on `,` and `-`)
- Saves as `Lumpsums - v*.xlsb_output.xlsx` in France files

### 4. Process Non-SYSFR_PGM_ Files
- **SUPPLIERS_PROMOTION_DATA**: Converts XLSB → CSV UTF-8, converts columns F/G to numbers, saves in France files
- **BIBLE**: Converts XLSB → XLSX with previous month suffix (e.g., "Bible 3xNET Conso 2025 Sep.xlsx"), saves in France files
- **PROMOS_PONCTUELLES/PERMANENTES**: No processing needed

### 5. Final Routing
- Routes all files according to `routes.json` patterns
- Files go to their defined destinations
- Unrouted files go to `_UNROUTED` folder

## Prerequisites
- Python 3 (available as `py` or `python`)
- PowerShell
- Dependencies:
```powershell
pip install Office365-REST-Python-Client PyYAML pywin32 pandas openpyxl pyxlsb
```

## Setup

### 1. Create/activate virtual environment
```powershell
cd C:\Dev\csv_zip_router
py -m venv venv
.\venv\Scripts\Activate.ps1
```
If activation is blocked:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
pip install Office365-REST-Python-Client PyYAML pywin32 pandas openpyxl pyxlsb
```

## Commands

### Option 1: One-Shot Pipeline (Recommended)

**Note**: The pipeline currently handles only one SharePoint folder. You need to run it twice (once for SYSFR_PGM_ files, once for the 5 non-SYSFR_PGM_ files) or use Option 2 for full control.

```powershell
# Set your credentials
$SITE   = "https://sysco.sharepoint.com/sites/PGMDatabaseSyscoandBain"
$CID    = "<YOUR_CLIENT_ID>"
$SECRET = "<YOUR_CLIENT_SECRET>"
$OUT    = "C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files"

# Example: Run for SYSFR_PGM_ files
.\run_pipeline.ps1 `
  -ClientId $CID `
  -ClientSecret $SECRET `
  -FolderRel "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/FR/3. Exports de données pour Bain/2. Exports hebdomadaires/03. CY2025" `
  -PauseSeconds 10 `
  -SiteUrl $SITE `
  -OutDir $OUT `
  -Workers 6 `
  -OnConflict overwrite
```

### Option 2: Manual Step-by-Step
```powershell
# Set variables
$SITE   = "https://sysco.sharepoint.com/sites/PGMDatabaseSyscoandBain"
$CID    = "<YOUR_CLIENT_ID>"
$SECRET = "<YOUR_CLIENT_SECRET>"
$MAP    = "C:\Dev\csv_zip_router\routes.json"
$OUT    = "C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files"

# Step 1: Download SYSFR_PGM_ files
python C:\Dev\csv_zip_router\download_sharepoint_latest.py `
  --site $SITE `
  --client-id $CID `
  --client-secret $SECRET `
  --folder "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/FR/3. Exports de données pour Bain/2. Exports hebdomadaires/03. CY2025" `
  --mapping $MAP `
  --out $OUT

# Step 2: Download 5 non-SYSFR_PGM_ files
python C:\Dev\csv_zip_router\download_sharepoint_latest.py `
  --site $SITE `
  --client-id $CID `
  --client-secret $SECRET `
  --folder "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/FR/3. Exports de données pour Bain/2. Exports hebdomadaires/1. Exports mensuels" `
  --mapping $MAP `
  --out $OUT `
  --include-non-sysfr

# Step 3: Process Lumpsums
python C:\Dev\csv_zip_router\deduplicate_lumpsums.py

# Step 4: Process other non-SYSFR_PGM_ files
python C:\Dev\csv_zip_router\process_non_sysfr_files.py

# Step 5: Route all files
python C:\Dev\csv_zip_router\csv_zip_router.py `
  "$OUT" `
  --mapping "$MAP" `
  --default-dest "C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\_UNROUTED" `
  --on-conflict overwrite `
  --workers 6 `
  --verbose
```

## Troubleshooting

### Common Issues
- **Folder age warning**: The latest SharePoint folder is older than 7 days
- **Month name warning**: Folder name doesn't contain the previous month in French
- **Import errors**: Ensure virtual environment is activated and dependencies are installed
- **Path errors**: Ensure Windows paths in `routes.json` use doubled backslashes `\\`

### Verify Dependencies
```powershell
# In the activated venv
python -c "from office365.runtime.auth.client_credential import ClientCredential; print('office365 ok')"
python -c "import yaml; print('yaml', yaml.__version__)"
python -c "import win32com.client; print('pywin32 ok')"
```

### File Patterns in routes.json
- SYSFR_PGM_ files: `.csv` extension
- SUPPLIERS_PROMOTION_DATA: `.csv` extension (converted from XLSB)
- BIBLE: `.xlsx` extension (converted from XLSB with month suffix)
- Lumpsums: `*.*` pattern (matches both original and processed files)
- PROMOS: `.csv` extension