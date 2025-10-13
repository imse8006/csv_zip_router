#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to validate the target filtering logic for routes.
"""

import json
from pathlib import Path

def load_routes():
    """Load routes.json"""
    with open('routes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_routes(routes, target_filter):
    """Filter routes based on target (scorecard, bb, or None for all)"""
    if target_filter is None:
        return routes
    
    filtered = []
    for route in routes:
        dest = route['dest'].lower()
        if target_filter == 'scorecard' and 'scorecard' in dest:
            filtered.append(route)
        elif target_filter == 'bb' and '\\fr bb\\' in dest:
            filtered.append(route)
    
    return filtered

def test_filters():
    """Test the filtering logic"""
    routes = load_routes()
    
    print("=" * 80)
    print("TEST DE FILTRAGE DES ROUTES")
    print("=" * 80)
    
    # Test 1: All routes
    print("\n[TEST 1] Toutes les routes (target=None)")
    all_routes = filter_routes(routes, None)
    print(f"  Nombre total de routes: {len(all_routes)}")
    
    # Test 2: Scorecard only
    print("\n[TEST 2] Routes Scorecard uniquement (target='scorecard')")
    scorecard_routes = filter_routes(routes, 'scorecard')
    print(f"  Nombre de routes Scorecard: {len(scorecard_routes)}")
    print("  Patterns routés vers Scorecard:")
    for route in scorecard_routes:
        print(f"    - {route['pattern']}")
    
    # Test 3: BB only
    print("\n[TEST 3] Routes Better Buying uniquement (target='bb')")
    bb_routes = filter_routes(routes, 'bb')
    print(f"  Nombre de routes BB: {len(bb_routes)}")
    print("  Patterns routés vers BB:")
    for route in bb_routes:
        print(f"    - {route['pattern']}")
    
    # Test 4: Overlap analysis
    print("\n[TEST 4] Analyse des fichiers routés vers plusieurs destinations")
    pattern_count = {}
    for route in routes:
        pattern = route['pattern']
        if pattern not in pattern_count:
            pattern_count[pattern] = []
        dest = route['dest']
        if 'scorecard' in dest.lower():
            pattern_count[pattern].append('Scorecard')
        elif '\\fr bb\\' in dest.lower():
            pattern_count[pattern].append('BB')
    
    multi_dest = {p: dests for p, dests in pattern_count.items() if len(dests) > 1}
    print(f"  Fichiers routés vers plusieurs destinations: {len(multi_dest)}")
    for pattern, dests in multi_dest.items():
        print(f"    - {pattern} -> {', '.join(dests)}")
    
    # Test 5: Validation
    print("\n[TEST 5] Validation")
    total = len(all_routes)
    scorecard_only = len([r for r in scorecard_routes if r not in bb_routes])
    bb_only = len([r for r in bb_routes if r not in scorecard_routes])
    both = len([r for r in scorecard_routes if r in bb_routes])
    
    print(f"  Total routes: {total}")
    print(f"  Scorecard uniquement: {scorecard_only}")
    print(f"  BB uniquement: {bb_only}")
    print(f"  Partagées (Scorecard + BB): {both}")
    print(f"  Vérification: {scorecard_only} + {bb_only} + {both} = {scorecard_only + bb_only + both} (doit être <= {total})")
    
    if scorecard_only + bb_only + both == total:
        print("  [OK] VALIDATION REUSSIE: Tous les routes sont bien categorises!")
    else:
        print(f"  [ERREUR] Certaines routes ne sont ni Scorecard ni BB!")
        uncategorized = total - (scorecard_only + bb_only + both)
        print(f"    Routes non categorisees: {uncategorized}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_filters()

