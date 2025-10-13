param(
    [Parameter(Mandatory=$true)] [string]$ClientId,
    [Parameter(Mandatory=$true)] [string]$ClientSecret,
    [string]$FolderSysfr = "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/FR/3.%20Exports%20de%20donn%C3%A9es%20pour%20Bain/2.%20Exports%20hebdomadaires/03.%20CY2025",
    [string]$FolderNonSysfr = "/sites/PGMDatabaseSyscoandBain/Shared Documents/General/FR/3.%20Exports%20de%20donn%C3%A9es%20pour%20Bain/2.%20Exports%20hebdomadaires/1.%20Exports%20mensuels",
    [switch]$NoWarnAge = $false,
    [int]$PauseSeconds = 10,
    [string]$SiteUrl = "https://sysco.sharepoint.com/sites/PGMDatabaseSyscoandBain",
    [string]$OutDir = "C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\France files",
    [int]$Workers = 6,
    [ValidateSet('overwrite','skip','rename')] [string]$OnConflict = 'overwrite',
    # Flags pour activer/désactiver les différents refreshes
    [switch]$EnableScorecard = $false,
    [switch]$EnableBB = $false,
    [switch]$EnableBetterSelling = $false,
    [switch]$All = $false  # Active tout
)

$ErrorActionPreference = 'Stop'

# Si -All est spécifié, activer tous les refreshes
if ($All) {
    $EnableScorecard = $true
    $EnableBB = $true
    $EnableBetterSelling = $true
}

# Vérifier qu'au moins un refresh est activé
if (-not ($EnableScorecard -or $EnableBB -or $EnableBetterSelling)) {
    Write-Host "ERREUR: Aucun refresh activé!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Utilisez au moins un des flags suivants:" -ForegroundColor Yellow
    Write-Host "  -EnableScorecard      : Refresh FR Scorecard" -ForegroundColor Cyan
    Write-Host "  -EnableBB             : Refresh FR Better Buying" -ForegroundColor Cyan
    Write-Host "  -EnableBetterSelling  : Refresh LIVE (Better Selling)" -ForegroundColor Cyan
    Write-Host "  -All                  : Active tous les refreshes" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Exemple: .\run_pipeline.ps1 -ClientId XXX -ClientSecret YYY -EnableScorecard -EnableBB" -ForegroundColor Green
    exit 1
}

# Afficher les refreshes activés
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "REFRESHES ACTIVES:" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
if ($EnableScorecard) { Write-Host "  [X] FR Scorecard" -ForegroundColor Green }
else { Write-Host "  [ ] FR Scorecard" -ForegroundColor DarkGray }
if ($EnableBB) { Write-Host "  [X] FR Better Buying (BB)" -ForegroundColor Green }
else { Write-Host "  [ ] FR Better Buying (BB)" -ForegroundColor DarkGray }
if ($EnableBetterSelling) { Write-Host "  [X] Better Selling (LIVE Refresh)" -ForegroundColor Green }
else { Write-Host "  [ ] Better Selling (LIVE Refresh)" -ForegroundColor DarkGray }
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Resolve repo paths relative to this script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Downloader = Join-Path $ScriptDir 'download_sharepoint_latest.py'
$Router    = Join-Path $ScriptDir 'csv_zip_router.py'
$Lumpsums  = Join-Path $ScriptDir 'deduplicate_lumpsums.py'
$NonSysfr  = Join-Path $ScriptDir 'process_non_sysfr_files.py'
$RouteIndividual = Join-Path $ScriptDir 'route_individual_files.py'
$UploadLive = Join-Path $ScriptDir 'upload_to_live_refresh.py'
$Mapping   = Join-Path $ScriptDir 'routes.json'

# [1/7] Download SYSFR_PGM_ files - Requis pour Scorecard, BB et Better Selling
if ($EnableScorecard -or $EnableBB -or $EnableBetterSelling) {
    Write-Host "[1/7] Download SYSFR_PGM_ files from SharePoint -> $OutDir" -ForegroundColor Cyan
    $argsDownloadSysfr = @(
        $Downloader,
        '--site', $SiteUrl,
        '--client-id', $ClientId,
        '--client-secret', $ClientSecret,
        '--folder', $FolderSysfr,
        '--mapping', $Mapping,
        '--out', $OutDir
    )
    if ($NoWarnAge) { $argsDownloadSysfr += '--no-warn-age' }
    
    & py @argsDownloadSysfr
} else {
    Write-Host "[1/7] Download SYSFR_PGM_ files - SKIPPED" -ForegroundColor DarkGray
}

# [2/7] Download non-SYSFR_PGM_ files - Requis UNIQUEMENT pour BB
if ($EnableBB) {
    Write-Host "[2/7] Download 5 non-SYSFR_PGM_ files from SharePoint -> $OutDir" -ForegroundColor Cyan
    $argsDownloadNonSysfr = @(
        $Downloader,
        '--site', $SiteUrl,
        '--client-id', $ClientId,
        '--client-secret', $ClientSecret,
        '--folder', $FolderNonSysfr,
        '--mapping', $Mapping,
        '--out', $OutDir,
        '--include-non-sysfr'
    )
    if ($NoWarnAge) { $argsDownloadNonSysfr += '--no-warn-age' }
    
    & py @argsDownloadNonSysfr
} else {
    Write-Host "[2/7] Download non-SYSFR_PGM_ files - SKIPPED (BB non activé)" -ForegroundColor DarkGray
}

# Petite pause (fichiers lourds) avant tout traitement/ upload en aval
if ($PauseSeconds -gt 0) {
  Write-Host "Waiting $PauseSeconds second(s) before continuing..." -ForegroundColor Yellow
  Start-Sleep -Seconds $PauseSeconds
}

# [3/7] Lumpsums deduplication - Requis UNIQUEMENT pour BB
if ($EnableBB) {
    Write-Host "[3/7] Run lumpsums deduplication on France files" -ForegroundColor Cyan
    & py $Lumpsums
} else {
    Write-Host "[3/7] Lumpsums deduplication - SKIPPED (BB non activé)" -ForegroundColor DarkGray
}

# [4/7] Process non-SYSFR_PGM_ files - Requis UNIQUEMENT pour BB
if ($EnableBB) {
    Write-Host "[4/7] Process non-SYSFR_PGM_ files" -ForegroundColor Cyan
    & py $NonSysfr
} else {
    Write-Host "[4/7] Process non-SYSFR_PGM_ files - SKIPPED (BB non activé)" -ForegroundColor DarkGray
}

# [5/7] Route ZIP files - Requis pour Scorecard ET BB
if ($EnableScorecard -or $EnableBB) {
    Write-Host "[5/7] Route downloaded files according to routes.json" -ForegroundColor Cyan
    
    # Determine target filter
    $targetFilter = 'all'
    if ($EnableScorecard -and $EnableBB) {
        $targetFilter = 'all'
    } elseif ($EnableScorecard) {
        $targetFilter = 'scorecard'
    } elseif ($EnableBB) {
        $targetFilter = 'bb'
    }
    
    $argsRoute = @(
        $Router,
        $OutDir,
        '--mapping', $Mapping,
        '--default-dest', 'C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\_UNROUTED',
        '--on-conflict', $OnConflict,
        '--workers', $Workers,
        '--verbose',
        '--target', $targetFilter
    )
    
    & py @argsRoute
} else {
    Write-Host "[5/7] Route ZIP files - SKIPPED (Scorecard et BB non activés)" -ForegroundColor DarkGray
}

# [6/7] Route individual files - Requis pour Scorecard ET BB
if ($EnableScorecard -or $EnableBB) {
    Write-Host "[6/7] Route individual processed files" -ForegroundColor Cyan
    
    # Determine target filter (same logic as step 5)
    $targetFilter = 'all'
    if ($EnableScorecard -and $EnableBB) {
        $targetFilter = 'all'
    } elseif ($EnableScorecard) {
        $targetFilter = 'scorecard'
    } elseif ($EnableBB) {
        $targetFilter = 'bb'
    }
    
    $argsRouteIndividual = @(
        $RouteIndividual,
        '--target', $targetFilter
    )
    
    & py @argsRouteIndividual
} else {
    Write-Host "[6/7] Route individual files - SKIPPED (Scorecard et BB non activés)" -ForegroundColor DarkGray
}

# [7/7] LIVE Refresh - Requis UNIQUEMENT pour Better Selling
if ($EnableBetterSelling) {
    Write-Host "[7/7] Upload files to LIVE Refresh folder with rotation" -ForegroundColor Cyan
    & py $UploadLive
} else {
    Write-Host "[7/7] LIVE Refresh - SKIPPED (Better Selling non activé)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "Pipeline terminé avec succès!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Magenta


