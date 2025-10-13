# Guide de Configuration - Première Installation

## 📋 Prérequis

1. **Python 3** installé (disponible via `py` ou `python`)
2. **PowerShell** (déjà présent sur Windows)
3. **Azure AD App Registration** avec accès SharePoint

---

## ⚙️ Installation - Étape par étape

### 1. Cloner le repository
```powershell
cd C:\Dev
git clone <votre-repo-url> csv_zip_router
cd csv_zip_router
```

### 2. Créer l'environnement virtuel
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

**Si l'activation est bloquée :**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances
```powershell
pip install Office365-REST-Python-Client PyYAML pywin32 pandas openpyxl pyxlsb
```

### 4. Configurer vos credentials

#### Option A : Fichier de configuration (Recommandé)
```powershell
# Copier le template
Copy-Item config.ps1.example config.ps1

# Éditer avec vos vraies credentials
notepad config.ps1
```

**Dans `config.ps1`, remplissez :**
```powershell
$CLIENT_ID = "votre-client-id-ici"
$CLIENT_SECRET = "votre-client-secret-ici"
```

**⚠️ IMPORTANT :** `config.ps1` est dans `.gitignore` et ne sera JAMAIS commité !

#### Option B : Variables d'environnement PowerShell
```powershell
$env:AZURE_CLIENT_ID = "votre-client-id"
$env:AZURE_CLIENT_SECRET = "votre-client-secret"
```

---

## 🚀 Premier lancement

### Méthode 1 : Avec config.ps1 (le plus simple)
```powershell
# Lancer avec config.ps1
.\quick_run.ps1 -All
```

### Méthode 2 : Avec paramètres explicites
```powershell
.\run_pipeline.ps1 `
  -ClientId "votre-client-id" `
  -ClientSecret "votre-client-secret" `
  -All
```

---

## ✅ Vérification de l'installation

### Test 1 : Script de validation
```powershell
py test_filters.py
```

**Résultat attendu :**
```
================================================================================
TEST DE FILTRAGE DES ROUTES
================================================================================
...
[OK] VALIDATION REUSSIE: Tous les routes sont bien categorises!
================================================================================
```

### Test 2 : Dry-run du pipeline
```powershell
# Tester sans vraiment télécharger/modifier
.\run_pipeline.ps1 `
  -ClientId "test" `
  -ClientSecret "test" `
  -EnableScorecard `
  -NoWarnAge
```

---

## 📁 Structure des fichiers

```
csv_zip_router/
├── venv/                          # Environnement virtuel (gitignored)
├── .csv_zip_router_work/          # Fichiers temporaires (gitignored)
│
├── config.ps1                     # VOS credentials (gitignored)
├── config.ps1.example             # Template de configuration
│
├── run_pipeline.ps1               # Pipeline principal
├── quick_run.ps1                  # Raccourci avec config.ps1
│
├── download_sharepoint_latest.py  # Téléchargement SharePoint
├── csv_zip_router.py              # Routing des ZIPs
├── route_individual_files.py      # Routing des fichiers individuels
├── deduplicate_lumpsums.py        # Processing Lumpsums
├── process_non_sysfr_files.py     # Processing Bible, Suppliers, etc.
├── upload_to_live_refresh.py      # Upload vers Better Selling
│
├── routes.json                    # Mapping des patterns -> destinations
├── test_filters.py                # Script de validation
│
├── README.md                      # Documentation générale
├── EXAMPLES.md                    # Exemples d'utilisation
├── CHANGELOG.md                   # Historique des modifications
└── SETUP.md                       # Ce fichier
```

---

## 🔐 Sécurité - À NE PAS commiter

Les fichiers suivants sont dans `.gitignore` et ne doivent **JAMAIS** être commités :

- ✅ `config.ps1` - Vos credentials
- ✅ `venv/` - Environnement virtuel
- ✅ `.csv_zip_router_work/` - Fichiers temporaires
- ✅ `*.csv`, `*.xlsx`, `*.xlsb` - Fichiers de données
- ✅ `France files/` - Dossier OneDrive local

---

## 🛠️ Troubleshooting

### Problème : "py : The term 'py' is not recognized"
**Solution :**
```powershell
# Utiliser python au lieu de py
python -m venv venv
```

### Problème : "Activate.ps1 cannot be loaded"
**Solution :**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Problème : "config.ps1 introuvable"
**Solution :**
```powershell
Copy-Item config.ps1.example config.ps1
notepad config.ps1  # Éditer avec vos credentials
```

### Problème : "SharePoint authentication failed"
**Causes possibles :**
1. Client ID ou Secret incorrect
2. App Registration n'a pas les permissions SharePoint
3. Tenant ID incorrect

**Solution :**
- Vérifier vos credentials dans Azure AD
- Vérifier les permissions de l'App Registration
- Contacter votre admin Azure si nécessaire

### Problème : "No .csv.zip files found"
**Causes possibles :**
1. Le dossier SharePoint n'a pas encore été actualisé cette semaine
2. Le chemin du dossier SharePoint est incorrect

**Solution :**
- Vérifier manuellement sur SharePoint que les fichiers existent
- Vérifier les chemins dans `config.ps1`

---

## 📚 Documentation

- **Usage général** : `README.md`
- **Exemples détaillés** : `EXAMPLES.md`
- **Historique** : `CHANGELOG.md`
- **Configuration** : Ce fichier (`SETUP.md`)

---

## 🎯 Prochaines étapes

Une fois l'installation terminée, consultez `EXAMPLES.md` pour voir les cas d'usage :

1. **Refresh complet** : `.\quick_run.ps1 -All`
2. **Scorecard uniquement** : `.\quick_run.ps1 -EnableScorecard`
3. **Better Buying uniquement** : `.\quick_run.ps1 -EnableBB`
4. **Better Selling uniquement** : `.\quick_run.ps1 -EnableBetterSelling`

---

## 💡 Conseils

### Workflow hebdomadaire recommandé
```powershell
# Lundi matin - Refresh complet
cd C:\Dev\csv_zip_router
.\venv\Scripts\Activate.ps1
.\quick_run.ps1 -All
```

### Pour les mises à jour du code
```powershell
# Récupérer les dernières modifications
git pull

# Réinstaller les dépendances si nécessaire
pip install -r requirements.txt  # Si vous créez ce fichier
```

### Sauvegarde de config.ps1
```powershell
# Sauvegarder votre config (hors git)
Copy-Item config.ps1 config.ps1.backup
```

---

## ✅ Checklist de première installation

- [ ] Python 3 installé et accessible via `py`
- [ ] Repository cloné dans `C:\Dev\csv_zip_router`
- [ ] Environnement virtuel créé (`venv/`)
- [ ] Dépendances installées (Office365, pandas, etc.)
- [ ] `config.ps1` créé avec vos vraies credentials
- [ ] Test de validation réussi (`py test_filters.py`)
- [ ] Premier run du pipeline réussi (`.\quick_run.ps1 -All`)
- [ ] `.gitignore` présent et config.ps1 non commité

**Si tous les points sont cochés, vous êtes prêt ! 🎉**

