#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script PowerShell pour uploader les outputs Scorecard vers SharePoint.

.DESCRIPTION
    Ce script utilise upload_scorecard_outputs.py pour créer un dossier hebdomadaire
    et uploader les fichiers outputs du Scorecard vers SharePoint EUPGM.

.PARAMETER Date
    Date au format YYYYMMDD (optionnel). Si non spécifié, utilise le prochain lundi.

.EXAMPLE
    .\upload_scorecard.ps1
    Upload automatique pour le prochain lundi

.EXAMPLE
    .\upload_scorecard.ps1 -Date "20251020"
    Upload pour une date spécifique
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Date
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "upload_scorecard_outputs.py"

# Charger les secrets/URLs depuis config.ps1 si présent (sans commit)
$Config = Join-Path $ScriptDir "config.ps1"
if (Test-Path $Config) {
    . $Config
    # Exporter vers env pour le script Python (préfixe EUPGM_ pour éviter collisions)
    if ($env:EUPGM_CLIENT_ID -eq $null -and $CLIENT_ID) { $env:EUPGM_CLIENT_ID = $CLIENT_ID }
    if ($env:EUPGM_CLIENT_SECRET -eq $null -and $CLIENT_SECRET) { $env:EUPGM_CLIENT_SECRET = $CLIENT_SECRET }
    if ($env:EUPGM_SITE_URL -eq $null) { $env:EUPGM_SITE_URL = "https://sysco.sharepoint.com/sites/EUPGM" }
}

# Vérifier que Python est disponible
try {
    $pythonVersion = python --version 2>&1
    Write-Host "🐍 Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas installé ou pas dans le PATH" -ForegroundColor Red
    exit 1
}

# Vérifier que le script Python existe
if (-not (Test-Path $PythonScript)) {
    Write-Host "❌ Script Python non trouvé: $PythonScript" -ForegroundColor Red
    exit 1
}

# Construire la commande
$pythonCmd = "python `"$PythonScript`""
if ($Date) {
    $pythonCmd += " --date $Date"
}

Write-Host "🚀 Lancement de l'upload Scorecard..." -ForegroundColor Cyan
Write-Host "📝 Commande: $pythonCmd" -ForegroundColor Gray
Write-Host ""

# Exécuter le script Python
try {
    Invoke-Expression $pythonCmd
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "✅ Script terminé avec succès!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Script terminé avec erreur (code: $exitCode)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Erreur lors de l'exécution: $_" -ForegroundColor Red
    exit 1
}
