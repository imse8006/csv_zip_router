# csv_zip_router – Complete Pipeline Documentation

## Overview
This pipeline automatically downloads files from SharePoint, processes them, and routes them to their correct destinations based on pattern matching rules.

**🆕 NEW: Selective Refresh Support**
You can now choose which systems to refresh:
- **FR Scorecard**: Data for Scorecard reports
- **FR Better Buying (BB)**: P&L and purchasing data
- **Better Selling (LIVE Refresh)**: Real-time data with weekly rotation

Use flags `-EnableScorecard`, `-EnableBB`, `-EnableBetterSelling`, or `-All` to activate the desired refreshes.

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

### Option 1: Quick Run with config.ps1 (RECOMMENDED)

**First time setup:**
```powershell
# 1. Create config file from template
Copy-Item config.ps1.example config.ps1

# 2. Edit config.ps1 with your credentials
notepad config.ps1
```

**Then use quick_run.ps1:**
```powershell
# Refresh ALL systems (Scorecard + BB + Better Selling)
.\quick_run.ps1 -All

# Refresh ONLY Scorecard
.\quick_run.ps1 -EnableScorecard

# Refresh ONLY Better Buying (BB)
.\quick_run.ps1 -EnableBB

# Refresh ONLY Better Selling (LIVE Refresh)
.\quick_run.ps1 -EnableBetterSelling

# Combinations
.\quick_run.ps1 -EnableScorecard -EnableBB
.\quick_run.ps1 -EnableBB -EnableBetterSelling
```

**⚠️ IMPORTANT:** `config.ps1` is in `.gitignore` and will NEVER be committed to git!

### Option 2: Manual with credentials

```powershell
# Set your credentials
$CID    = "<YOUR_CLIENT_ID>"
$SECRET = "<YOUR_CLIENT_SECRET>"

# Example 1: Refresh ALL systems (Scorecard + BB + Better Selling)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All

# Example 2: Refresh ONLY Scorecard
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard

# Example 3: Refresh ONLY Better Buying (BB)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBB

# Example 4: Refresh ONLY Better Selling (LIVE Refresh)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBetterSelling

# Example 5: Refresh Scorecard + BB (no Better Selling)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard -EnableBB

# Example 6: Refresh BB + Better Selling (no Scorecard)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBB -EnableBetterSelling
```

**Available Flags:**
- `-EnableScorecard`: Active le refresh pour FR Scorecard
- `-EnableBB`: Active le refresh pour FR Better Buying (P&L, Lumpsums, Bible, etc.)
- `-EnableBetterSelling`: Active le refresh pour Better Selling (LIVE Refresh avec rotation)
- `-All`: Active tous les refreshes (équivalent à `-EnableScorecard -EnableBB -EnableBetterSelling`)

**⚠️ Important:** Au moins un flag doit être spécifié, sinon le pipeline affiche une erreur et s'arrête.

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