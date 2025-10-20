#!/usr/bin/env python3
"""
Script pour créer un dossier hebdomadaire dans SharePoint et uploader les outputs Scorecard.

Usage:
    python upload_scorecard_outputs.py [--date YYYYMMDD]
    
Si --date n'est pas fourni, le script calcule automatiquement le prochain lundi.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import requests
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential

# Configuration (no secrets in code)
CLIENT_ID = os.environ.get("EUPGM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("EUPGM_CLIENT_SECRET")

# SharePoint EUPGM (différent du PGMDatabaseSyscoandBain)
SITE_URL = os.environ.get("EUPGM_SITE_URL", "https://sysco.sharepoint.com/sites/EUPGM")
SCORECARD_FOLDER = "/sites/EUPGM/Shared Documents/General/France/PGM Outputs/Scorecard"

# Chemins des fichiers à uploader
FILES_TO_UPLOAD = [
    {
        "name": "{date}_Hierarchy.yxdb",
        "source": r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\1. Input consolidation\Final output\{date}_Hierarchy.yxdb"
    },
    {
        "name": "{date}_Sales output.yxdb", 
        "source": r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\2. Sales\Final Output\{date}_Sales output.yxdb"
    },
    {
        "name": "{date}_PL 1 2 3 output.yxdb",
        "source": r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\2. Sales\Final Output\{date}_PL 1 2 3 output.yxdb"
    },
    {
        "name": "{date}_New Indicators + Clicks.yxdb",
        "source": r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\3. Clicks and other indicators\Final Output\{date}_New Indicators + Clicks.yxdb"
    },
    {
        "name": "{date}_Scorecard.hyper",
        "source": r"C:\Users\il00030293\OneDrive - Sysco Corporation\Documents\PGM\FR Scorecard\4. Output consolidation\Final output\{date}_Scorecard.hyper"
    }
]


def get_next_monday():
    """Calcule la date du prochain lundi au format YYYYMMDD."""
    today = datetime.now()
    
    # Calculer les jours jusqu'au prochain lundi (0 = lundi)
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:  # Si on est déjà lundi
        days_until_monday = 7   # Prendre le lundi suivant
    
    next_monday = today + timedelta(days=days_until_monday)
    return next_monday.strftime("%Y%m%d")


def check_files_exist(date_str):
    """Vérifie que tous les fichiers sources existent."""
    print(f"🔍 Vérification des fichiers sources pour la date {date_str}...")
    
    missing_files = []
    existing_files = []
    
    for file_info in FILES_TO_UPLOAD:
        source_path = Path(file_info["source"].format(date=date_str))
        
        if source_path.exists():
            size_mb = source_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {source_path.name} ({size_mb:.1f} MB)")
            existing_files.append(file_info)
        else:
            print(f"  ❌ {source_path.name} - FICHIER MANQUANT")
            missing_files.append(source_path)
    
    if missing_files:
        print(f"\n🚨 ERREUR: {len(missing_files)} fichier(s) manquant(s):")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False, []
    
    print(f"\n✅ Tous les fichiers sont présents ({len(existing_files)} fichiers)")
    return True, existing_files


def create_sharepoint_context():
    """Crée le contexte SharePoint pour l'authentification."""
    try:
        if not CLIENT_ID or not CLIENT_SECRET:
            raise RuntimeError("EUPGM_CLIENT_ID / EUPGM_CLIENT_SECRET non définis dans l'environnement")
        credentials = ClientCredential(CLIENT_ID, CLIENT_SECRET)
        ctx = ClientContext(SITE_URL).with_credentials(credentials)
        
        # Test de connexion
        web = ctx.web.get().execute_query()
        print(f"✅ Connecté à SharePoint: {web.title}")
        return ctx
        
    except Exception as e:
        print(f"❌ Erreur de connexion SharePoint: {e}")
        return None


def create_folder_if_not_exists(ctx, folder_path):
    """Crée le dossier s'il n'existe pas déjà."""
    try:
        # Vérifier si le dossier existe déjà
        folder = ctx.web.get_folder_by_server_relative_url(folder_path)
        folder.load().execute_query()
        print(f"📁 Dossier existe déjà: {folder_path}")
        return True
        
    except Exception:
        try:
            # Créer le dossier
            folder = ctx.web.get_folder_by_server_relative_url(SCORECARD_FOLDER)
            new_folder = folder.folders.add(folder_path.split('/')[-1])
            ctx.execute_query()
            print(f"📁 Dossier créé: {folder_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du dossier: {e}")
            return False


def upload_file(ctx, local_file_path, sharepoint_folder_path, filename):
    """Upload un fichier vers SharePoint."""
    try:
        # Lire le fichier local
        with open(local_file_path, 'rb') as file:
            file_content = file.read()
        
        # Chemin SharePoint complet
        sharepoint_file_path = f"{sharepoint_folder_path}/{filename}"
        
        # Upload
        folder = ctx.web.get_folder_by_server_relative_url(sharepoint_folder_path)
        uploaded_file = folder.upload_file(filename, file_content)
        ctx.execute_query()
        
        size_mb = len(file_content) / (1024 * 1024)
        print(f"  ✅ {filename} uploadé ({size_mb:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur upload {filename}: {e}")
        return False


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Upload des outputs Scorecard vers SharePoint")
    parser.add_argument("--date", help="Date au format YYYYMMDD (par défaut: prochain lundi)")
    args = parser.parse_args()
    
    # Déterminer la date
    if args.date:
        date_str = args.date
        print(f"📅 Date spécifiée: {date_str}")
    else:
        date_str = get_next_monday()
        print(f"📅 Prochain lundi calculé: {date_str}")
    
    print(f"\n{'='*60}")
    print(f"🚀 UPLOAD SCORECARD OUTPUTS - {date_str}")
    print(f"{'='*60}")
    
    # 1. Vérifier les fichiers sources
    files_exist, existing_files = check_files_exist(date_str)
    if not files_exist:
        print("\n❌ Arrêt du script - fichiers manquants")
        sys.exit(1)
    
    # 2. Connexion SharePoint
    print(f"\n🔗 Connexion à SharePoint...")
    ctx = create_sharepoint_context()
    if not ctx:
        print("❌ Arrêt du script - impossible de se connecter")
        sys.exit(1)
    
    # 3. Créer le dossier
    folder_name = date_str
    folder_path = f"{SCORECARD_FOLDER}/{folder_name}"
    
    print(f"\n📁 Création du dossier: {folder_path}")
    if not create_folder_if_not_exists(ctx, folder_path):
        print("❌ Arrêt du script - impossible de créer le dossier")
        sys.exit(1)
    
    # 4. Upload des fichiers
    print(f"\n⬆️  Upload des fichiers vers SharePoint...")
    success_count = 0
    
    for file_info in existing_files:
        local_path = Path(file_info["source"].format(date=date_str))
        filename = file_info["name"].format(date=date_str)
        
        if upload_file(ctx, local_path, folder_path, filename):
            success_count += 1
    
    # 5. Résumé
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ")
    print(f"{'='*60}")
    print(f"📁 Dossier créé: {folder_path}")
    print(f"⬆️  Fichiers uploadés: {success_count}/{len(existing_files)}")
    
    if success_count == len(existing_files):
        print(f"✅ SUCCÈS: Tous les fichiers ont été uploadés!")
        print(f"🌐 Accès SharePoint: {SITE_URL}")
    else:
        print(f"⚠️  ATTENTION: {len(existing_files) - success_count} fichier(s) en échec")
        sys.exit(1)


if __name__ == "__main__":
    main()
