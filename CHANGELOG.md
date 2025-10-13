# Changelog - Système de refresh sélectif

## Version 2.0 - Octobre 2025

### 🎯 Nouvelle fonctionnalité : Refresh sélectif

Le pipeline supporte maintenant la possibilité de choisir quels systèmes rafraîchir :

#### **Flags disponibles :**
- `-EnableScorecard` : Active uniquement le refresh pour FR Scorecard
- `-EnableBB` : Active uniquement le refresh pour FR Better Buying
- `-EnableBetterSelling` : Active uniquement le refresh pour Better Selling (LIVE Refresh)
- `-All` : Active tous les refreshes

#### **Validation :**
- Au moins un flag doit être spécifié
- Si aucun flag n'est fourni, le script affiche une erreur explicite et s'arrête

---

## Modifications apportées

### 📝 **run_pipeline.ps1**
**Changements :**
- Ajout de 4 nouveaux paramètres : `-EnableScorecard`, `-EnableBB`, `-EnableBetterSelling`, `-All`
- Ajout d'une validation au démarrage (erreur si aucun flag)
- Affichage visuel des refreshes actifs au démarrage
- Chaque étape [1/7] à [7/7] est maintenant conditionnelle selon les flags
- Transmission du paramètre `--target` aux scripts Python

**Logique de filtrage :**
```powershell
# Exemple : Si seul -EnableScorecard est activé
- Étape [1/7] : Exécutée (téléchargement SYSFR_PGM_)
- Étape [2/7] : SKIPPED (pas de téléchargement non-SYSFR car BB non activé)
- Étape [3/7] : SKIPPED (pas de Lumpsums car BB non activé)
- Étape [4/7] : SKIPPED (pas de processing non-SYSFR car BB non activé)
- Étape [5/7] : Exécutée avec --target scorecard
- Étape [6/7] : Exécutée avec --target scorecard
- Étape [7/7] : SKIPPED (pas de LIVE Refresh car Better Selling non activé)
```

---

### 📝 **csv_zip_router.py**
**Changements :**
- Ajout du paramètre `--target` (choices: scorecard, bb, all)
- Modification de `resolve_destinations()` pour accepter un filtre `target_filter`
- Modification de `extract_and_route_zip()` pour transmettre le filtre

**Logique de filtrage :**
```python
# Si target='scorecard' : ne garde que les destinations contenant 'scorecard'
# Si target='bb' : ne garde que les destinations contenant '\fr bb\'
# Si target='all' ou None : garde toutes les destinations
```

---

### 📝 **route_individual_files.py**
**Changements :**
- Ajout du paramètre `--target` (choices: scorecard, bb, all)
- Remplacement de `resolve_destination()` par `resolve_destinations()` qui retourne une liste
- Ajout de la logique de filtrage par destination

**Comportement :**
- Même logique de filtrage que `csv_zip_router.py`
- Affiche le nombre d'opérations de routing effectuées
- Message clair si aucun fichier à router

---

### 📝 **README.md**
**Changements :**
- Ajout d'une section "Selective Refresh Support" en haut
- Remplacement de la section "Commands" avec des exemples clairs des 6 cas d'usage
- Documentation des flags disponibles

---

### 📝 **Nouveaux fichiers**

#### **EXAMPLES.md**
Guide complet avec :
- 6 cas d'usage détaillés
- Explication de ce qui se passe pour chaque cas
- Liste des fichiers routés pour chaque scénario
- Tableau récapitulatif
- Conseils pratiques
- Options avancées

#### **test_filters.py**
Script de validation qui :
- Charge `routes.json`
- Teste les 3 filtres (None, scorecard, bb)
- Affiche les patterns routés vers chaque destination
- Analyse les fichiers routés vers plusieurs destinations
- Valide que tous les routes sont bien catégorisés

**Résultat du test :**
```
Total routes: 25
Scorecard uniquement: 15
BB uniquement: 10
Fichiers partagés (Scorecard + BB): 4
  - SYSFR_PGM_BASE_RISTOURNABLE_2025.csv
  - SYSFR_PGM_MD_ITEM_DATA.csv
  - SYSFR_PGM_SALES_DATA_*.csv
  - SYSFR_PGM_TARIF_GENERAL_*.csv

[OK] VALIDATION REUSSIE
```

---

## Tests effectués

### ✅ Test 1 : Validation de la logique de filtrage
```bash
py test_filters.py
```
**Résultat :** SUCCÈS - Tous les routes sont bien catégorisés

### ✅ Test 2 : Pas d'erreurs de linting
```bash
read_lints ["run_pipeline.ps1", "route_individual_files.py", "csv_zip_router.py"]
```
**Résultat :** No linter errors found

---

## Migration

### Ancien usage (toujours compatible)
```powershell
# Avant : Refresh de tout par défaut
.\run_pipeline.ps1 -ClientId XXX -ClientSecret YYY
```
**⚠️ Cela ne fonctionne PLUS !** Vous devez maintenant spécifier au moins un flag.

### Nouveau usage équivalent
```powershell
# Maintenant : Spécifier explicitement
.\run_pipeline.ps1 -ClientId XXX -ClientSecret YYY -All
```

---

## Avantages

### 🚀 Performance
- Skip les étapes inutiles selon le refresh choisi
- Économie de temps si seul un système doit être mis à jour
- Moins de téléchargements SharePoint inutiles

### 🛡️ Sécurité
- Validation obligatoire au démarrage (pas de refresh accidentel)
- Messages clairs et explicites
- Impossibilité de lancer le pipeline "par erreur" sans savoir ce qui sera rafraîchi

### 📊 Transparence
- Affichage visuel des refreshes actifs au démarrage
- Chaque étape indique clairement si elle est SKIPPED ou exécutée
- Logs plus clairs et ciblés

---

## Exemples d'usage

### Cas 1 : Refresh hebdomadaire complet (lundi matin)
```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -All
```

### Cas 2 : Update rapide Scorecard uniquement
```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableScorecard
```

### Cas 3 : Refresh P&L Better Buying uniquement
```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBB
```

### Cas 4 : Rotation LIVE Refresh uniquement (si fichiers déjà téléchargés)
```powershell
.\run_pipeline.ps1 -ClientId $CID -ClientSecret $SECRET -EnableBetterSelling
```

---

## Notes techniques

### Filtrage intelligent
Le système détecte automatiquement si une destination contient :
- `scorecard` (case-insensitive) → catégorie Scorecard
- `\fr bb\` (case-sensitive) → catégorie Better Buying
- Si les deux flags sont activés → routing vers toutes les destinations matchées

### Fichiers partagés
4 fichiers sont routés vers Scorecard ET Better Buying :
1. `SYSFR_PGM_BASE_RISTOURNABLE_2025.csv`
2. `SYSFR_PGM_MD_ITEM_DATA.csv`
3. `SYSFR_PGM_SALES_DATA_*.csv`
4. `SYSFR_PGM_TARIF_GENERAL_*.csv`

Selon les flags :
- Si `-EnableScorecard` uniquement → routés vers Scorecard uniquement
- Si `-EnableBB` uniquement → routés vers BB uniquement
- Si les deux → routés vers les deux destinations

---

## Prochaines étapes (optionnel)

### Améliorations possibles
1. Ajouter un mode `--dry-run` global au pipeline PowerShell
2. Implémenter des notifications email en cas d'échec
3. Ajouter des logs structurés avec timestamps
4. Créer des tests unitaires pour chaque script Python
5. Implémenter des garde-fous supplémentaires (voir analyse précédente)

---

## Support

Pour toute question ou problème :
1. Consulter `EXAMPLES.md` pour les cas d'usage
2. Consulter `README.md` pour la documentation complète
3. Exécuter `py test_filters.py` pour valider la logique de filtrage

