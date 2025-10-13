# Exemples d'utilisation du Pipeline

## 🎯 Cas d'usage courants

### 1. Refresh hebdomadaire complet (tous les systèmes)
**Quand ?** Chaque lundi matin pour mettre à jour toutes les données.

```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All
```

**Ce qui se passe :**
- ✅ Téléchargement des fichiers SYSFR_PGM_
- ✅ Téléchargement des fichiers non-SYSFR (Bible, Lumpsums, etc.)
- ✅ Processing de Lumpsums (déduplication)
- ✅ Processing des fichiers non-SYSFR (conversions)
- ✅ Routing vers Scorecard
- ✅ Routing vers Better Buying
- ✅ Upload vers Better Selling (LIVE Refresh) avec rotation

---

### 2. Refresh UNIQUEMENT Scorecard
**Quand ?** Mise à jour rapide des indicateurs Scorecard uniquement.

```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard
```

**Ce qui se passe :**
- ✅ Téléchargement des fichiers SYSFR_PGM_
- ❌ Pas de téléchargement des fichiers non-SYSFR (Bible, Lumpsums)
- ❌ Pas de processing Lumpsums
- ❌ Pas de processing non-SYSFR
- ✅ Routing vers Scorecard UNIQUEMENT (pas vers BB)
- ❌ Pas d'upload vers Better Selling

**Fichiers routés :**
- `SYSFR_PGM_EFFECTIF_*.csv`
- `SYSFR_PGM_KPI_SV_*.csv`, `SYSFR_PGM_KPI_TV_*.csv`
- `SYSFR_PGM_MD_ITEM_DATA.csv`
- `SYSFR_PGM_MD_RMPZ_*.csv`, `SYSFR_PGM_MD_RCCZ_*.csv`
- `SYSFR_PGM_MD_SECTORISATION_*.csv`
- `SYSFR_PGM_PRODUITS_TARIF*.csv`
- `SYSFR_PGM_SALES_DATA_*.csv`
- `SYSFR_PGM_SALES_LIV_DATA_*.csv`
- `SYSFR_PGM_SESAME_*.csv`
- `SYSFR_PGM_TARIF_GENERAL_*.csv`
- `SYSFR_PGM_BASE_RISTOURNABLE_*.csv`

---

### 3. Refresh UNIQUEMENT Better Buying (BB)
**Quand ?** Mise à jour des données P&L et achats uniquement.

```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBB
```

**Ce qui se passe :**
- ✅ Téléchargement des fichiers SYSFR_PGM_
- ✅ Téléchargement des fichiers non-SYSFR (Bible, Lumpsums, Promos)
- ✅ Processing de Lumpsums (déduplication)
- ✅ Processing des fichiers non-SYSFR (Bible → XLSX, SUPPLIERS_PROMOTION_DATA → CSV)
- ✅ Routing vers Better Buying UNIQUEMENT (pas vers Scorecard)
- ❌ Pas d'upload vers Better Selling

**Fichiers routés :**
- `SYSFR_PGM_SUPPLIERS_PROMOTION_DATA*.csv` (converti en CSV avec `;`)
- `Lumpsums*_output.xlsx` (dédupliqué)
- `Bible 3xNET Conso ???? ???.xlsb` + `.xlsx` (avec mois précédent)
- `SYSFR_PGM_LISTE_PRIX_PROMOS_PONCT*.xlsx`
- `SYSFR_PGM_LISTE_PRIX_PROMOS_PERMAN*.xlsx`
- `SYSFR_PGM_MD_ITEM_DATA.csv`
- `SYSFR_PGM_SALES_DATA_*.csv`
- `SYSFR_PGM_TARIF_GENERAL_*.csv`
- `SYSFR_PGM_BASE_RISTOURNABLE_*.csv` (avec mois précédent)

---

### 4. Refresh UNIQUEMENT Better Selling (LIVE Refresh)
**Quand ?** Mise à jour hebdomadaire des données temps réel avec rotation automatique.

```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBetterSelling
```

**Ce qui se passe :**
- ✅ Téléchargement des fichiers SYSFR_PGM_
- ❌ Pas de téléchargement des fichiers non-SYSFR
- ❌ Pas de processing Lumpsums
- ❌ Pas de processing non-SYSFR
- ❌ Pas de routing vers Scorecard ou BB
- ✅ Upload vers Better Selling avec rotation automatique

**Rotation automatique :**
1. **Check version** : Vérifie que les nouveaux fichiers sont plus récents (basé sur le numéro de semaine)
2. **Si OK** :
   - Previous xxx ← Latest xxx (déplacement des anciens fichiers)
   - Latest xxx ← France files (copie des nouveaux fichiers)
3. **Si KO** : Rien ne se passe, message clair affiché

**Fichiers uploadés :**
- `SYSFR_PGM_TARIF_GENERAL_*.csv` → Latest Tarif General
- `SYSFR_PGM_EFFECTIF_*.csv` → Latest Effectif File
- `SYSFR_PGM_MD_RMPZ_*.csv` → Latest Sectorization/RMPZ
- `SYSFR_PGM_MD_RCCZ_*.csv` → Latest Sectorization/RCCZ
- `SYSFR_PGM_MD_SECTORISATION_*.csv` → Latest Sectorization/Sectorization
- `SYSFR_PGM_MD_ITEM_DATA.csv` → racine LIVE Refresh
- `SYSFR_PGM_PRODUITS_TARIF*.csv` → racine LIVE Refresh

---

### 5. Refresh Scorecard + BB (sans Better Selling)
**Quand ?** Mise à jour complète des rapports sans toucher aux données temps réel.

```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard -EnableBB
```

**Ce qui se passe :**
- ✅ Téléchargement des fichiers SYSFR_PGM_
- ✅ Téléchargement des fichiers non-SYSFR
- ✅ Processing de Lumpsums
- ✅ Processing des fichiers non-SYSFR
- ✅ Routing vers Scorecard ET Better Buying
- ❌ Pas d'upload vers Better Selling

---

### 6. Refresh BB + Better Selling (sans Scorecard)
**Quand ?** Mise à jour des données P&L et temps réel uniquement.

```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBB -EnableBetterSelling
```

**Ce qui se passe :**
- ✅ Téléchargement des fichiers SYSFR_PGM_
- ✅ Téléchargement des fichiers non-SYSFR
- ✅ Processing de Lumpsums
- ✅ Processing des fichiers non-SYSFR
- ✅ Routing vers Better Buying UNIQUEMENT
- ✅ Upload vers Better Selling avec rotation

---

## 🛡️ Garde-fous et sécurité

### Check de version (Better Selling)
Avant chaque upload vers LIVE Refresh, le script vérifie :
- ✅ Les fichiers existent dans `France files`
- ✅ Les nouveaux fichiers ont un numéro de semaine **strictement supérieur** à ceux dans "Latest"
- ❌ Si KO : **Aucune action**, message clair affiché

### Messages d'erreur
Si aucun flag n'est spécifié :
```
ERREUR: Aucun refresh activé!

Utilisez au moins un des flags suivants:
  -EnableScorecard      : Refresh FR Scorecard
  -EnableBB             : Refresh FR Better Buying
  -EnableBetterSelling  : Refresh LIVE (Better Selling)
  -All                  : Active tous les refreshes
```

---

## 📊 Tableau récapitulatif

| Flag | Étapes exécutées | Destinations |
|------|------------------|--------------|
| `-EnableScorecard` | [1/7], [5/7], [6/7] | FR Scorecard uniquement |
| `-EnableBB` | [1/7], [2/7], [3/7], [4/7], [5/7], [6/7] | FR BB uniquement |
| `-EnableBetterSelling` | [1/7], [7/7] | LIVE Refresh uniquement |
| `-EnableScorecard -EnableBB` | [1/7], [2/7], [3/7], [4/7], [5/7], [6/7] | Scorecard + BB |
| `-All` | Toutes les étapes [1/7] à [7/7] | Scorecard + BB + Better Selling |

---

## 💡 Conseils pratiques

### Workflow hebdomadaire recommandé
1. **Lundi matin** : `.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All`
2. **En cas de problème Better Selling** : `.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBetterSelling`
3. **Update rapide Scorecard** : `.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard`

### Debugging
Pour tester sans risque, utilisez un flag à la fois :
```powershell
# Tester uniquement Scorecard
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard

# Vérifier les logs, puis si OK :
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBB

# Vérifier les logs, puis si OK :
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBetterSelling
```

---

## 🔧 Options avancées

### Modifier le comportement en cas de conflit
Par défaut, les fichiers sont écrasés. Vous pouvez changer ce comportement :

```powershell
# Écraser les fichiers existants (défaut)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All -OnConflict overwrite

# Sauter les fichiers existants
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All -OnConflict skip

# Renommer les fichiers (ajouter un suffixe)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All -OnConflict rename
```

### Modifier le nombre de workers (parallélisation)
```powershell
# Utiliser 10 workers au lieu de 6 (par défaut)
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All -Workers 10
```

### Désactiver l'avertissement si dossier > 7 jours
```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All -NoWarnAge
```

