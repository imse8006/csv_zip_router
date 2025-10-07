param(
    [Parameter(Mandatory=$true)] [string]$ClientId,
    [Parameter(Mandatory=$true)] [string]$ClientSecret,
    [Parameter(Mandatory=$true)] [string]$FolderRel,  # ex: /sites/PGMDatabaseSyscoandBain/Shared Documents/General/<chemin parent>
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
$Mapping   = Join-Path $ScriptDir 'routes.json'

Write-Host "[1/2] Download latest SharePoint folder -> $OutDir" -ForegroundColor Cyan
$argsDownload = @(
    $Downloader,
    '--site', $SiteUrl,
    '--client-id', $ClientId,
    '--client-secret', $ClientSecret,
    '--folder', $FolderRel,
    '--mapping', $Mapping,
    '--out', $OutDir
)
if ($NoWarnAge) { $argsDownload += '--no-warn-age' }

& py @argsDownload

# Petite pause (fichiers lourds) avant tout traitement/ upload en aval
if ($PauseSeconds -gt 0) {
  Write-Host "Waiting $PauseSeconds second(s) before continuing..." -ForegroundColor Yellow
  Start-Sleep -Seconds $PauseSeconds
}

Write-Host "[2/2] Route downloaded files according to routes.json" -ForegroundColor Cyan
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

Write-Host "Pipeline done." -ForegroundColor Green


