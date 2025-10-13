# Quick run script - loads config.ps1 and runs pipeline
#
# Usage:
#   .\quick_run.ps1 -All
#   .\quick_run.ps1 -EnableScorecard
#   .\quick_run.ps1 -EnableBB
#   .\quick_run.ps1 -EnableBetterSelling
#   .\quick_run.ps1 -EnableScorecard -EnableBB

param(
    [switch]$EnableScorecard = $false,
    [switch]$EnableBB = $false,
    [switch]$EnableBetterSelling = $false,
    [switch]$All = $false,
    [switch]$NoWarnAge = $false,
    [int]$Workers,
    [int]$PauseSeconds,
    [ValidateSet('overwrite','skip','rename')] [string]$OnConflict
)

# Check if config.ps1 exists
if (-not (Test-Path "config.ps1")) {
    Write-Host "ERREUR: config.ps1 introuvable!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Veuillez créer config.ps1 à partir de config.ps1.example:" -ForegroundColor Yellow
    Write-Host "  1. Copy-Item config.ps1.example config.ps1" -ForegroundColor Cyan
    Write-Host "  2. Editez config.ps1 avec vos vraies credentials" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Load configuration
. .\config.ps1

# Override with command line parameters if provided
if ($Workers) { $WORKERS = $Workers }
if ($PauseSeconds) { $PAUSE_SECONDS = $PauseSeconds }
if ($OnConflict) { $ON_CONFLICT = $OnConflict }

# Build arguments for run_pipeline.ps1
$pipelineArgs = @{
    'ClientId' = $CLIENT_ID
    'ClientSecret' = $CLIENT_SECRET
    'SiteUrl' = $SITE_URL
    'FolderSysfr' = $FOLDER_SYSFR
    'FolderNonSysfr' = $FOLDER_NON_SYSFR
    'OutDir' = $OUT_DIR
    'Workers' = $WORKERS
    'PauseSeconds' = $PAUSE_SECONDS
    'OnConflict' = $ON_CONFLICT
}

# Add refresh flags
if ($All) { $pipelineArgs['All'] = $true }
if ($EnableScorecard) { $pipelineArgs['EnableScorecard'] = $true }
if ($EnableBB) { $pipelineArgs['EnableBB'] = $true }
if ($EnableBetterSelling) { $pipelineArgs['EnableBetterSelling'] = $true }
if ($NoWarnAge) { $pipelineArgs['NoWarnAge'] = $true }

# Run pipeline
& .\run_pipeline.ps1 @pipelineArgs

