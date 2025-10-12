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
    [ValidateSet('overwrite','skip','rename')] [string]$OnConflict = 'overwrite'
)

$ErrorActionPreference = 'Stop'

# Resolve repo paths relative to this script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Downloader = Join-Path $ScriptDir 'download_sharepoint_latest.py'
$Router    = Join-Path $ScriptDir 'csv_zip_router.py'
$Lumpsums  = Join-Path $ScriptDir 'deduplicate_lumpsums.py'
$NonSysfr  = Join-Path $ScriptDir 'process_non_sysfr_files.py'
$UploadLive = Join-Path $ScriptDir 'upload_to_live_refresh.py'
$Mapping   = Join-Path $ScriptDir 'routes.json'

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

# Petite pause (fichiers lourds) avant tout traitement/ upload en aval
if ($PauseSeconds -gt 0) {
  Write-Host "Waiting $PauseSeconds second(s) before continuing..." -ForegroundColor Yellow
  Start-Sleep -Seconds $PauseSeconds
}

Write-Host "[3/7] Run lumpsums deduplication on France files" -ForegroundColor Cyan
& py $Lumpsums

Write-Host "[4/7] Process non-SYSFR_PGM_ files" -ForegroundColor Cyan
& py $NonSysfr

Write-Host "[5/7] Route downloaded files according to routes.json" -ForegroundColor Cyan
$argsRoute = @(
    $Router,
    $OutDir,
    '--mapping', $Mapping,
    '--default-dest', 'C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\_UNROUTED',
    '--on-conflict', $OnConflict,
    '--workers', $Workers,
    '--verbose'
)

& py @argsRoute

Write-Host "[6/7] Route individual processed files" -ForegroundColor Cyan
& py route_individual_files.py

Write-Host "[7/7] Upload files to LIVE Refresh folder with rotation" -ForegroundColor Cyan
& py $UploadLive

Write-Host "Pipeline done." -ForegroundColor Green


