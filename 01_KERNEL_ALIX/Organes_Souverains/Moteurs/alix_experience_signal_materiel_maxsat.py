#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
  🔬⚡ EXPÉRIENCE SUR LE FER : DILEMME SIGNAL MATÉRIEL VS COHÉRENCE LOGIQUE
  Moteur : LKB-SMT (mmap LKBSMT01) × Hadès CDCL(T) MaxSAT
  Auteurs : Christian Duguay & Alix
===============================================================================
"""

import os
import sys
import time
from pathlib import Path

# Assurer l'encodage UTF-8 sous Windows PowerShell
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MOTEURS_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Organes_Souverains\Moteurs")
if str(MOTEURS_DIR) not in sys.path:
    sys.path.insert(0, str(MOTEURS_DIR))

from alix_lkb_smt_maxsat_engine import (
    LKB_SMT_PATH,
    SCHEMA_ALLOCATION,
    SCHEMA_MUTEX,
    compile_lkb_smt,
    load_lkb_smt,
    validate_npu_output,
    HybridSmtBuilder,
    find_minimal_relaxation,
    constraint_name,
)

def executer_experience_dilemme():
    print("=" * 86)
    print(" 🔬⚡ ÉPREUVE DU SILICIUM : SIGNAL MATÉRIEL VS COHÉRENCE INTERNE")
    print("    Moteur formel : Gaïa (mmap LKBSMT01) × Hadès CDCL(T) 2WL Cotton-Maler")
    print("=" * 86)
    
    t0 = time.perf_counter()
    HORIZON_MS = 10_000
    compile_lkb_smt(LKB_SMT_PATH, horizon=HORIZON_MS)
    lkb = load_lkb_smt(LKB_SMT_PATH)
    
    print(f"[*] Base binaire 'LKBSMT01' chargée via mmap ({os.path.getsize(LKB_SMT_PATH)} octets).")
    
    # Spécification formelle des variables booléennes du dilemme
    spec = {
        "int_vars": [],
        "bool_vars": [
            "signal_materiel",      # Signal empirique imprévu capté par le fer
            "coherence_logique"     # Modèle / croyance interne préalable
        ]
    }
    
    # =========================================================================
    # SCÉNARIO 1 : MUTEX PHYSIQUE INVIOLABLE (HARD) VS CROYANCE INTERNE (SOFT)
    # =========================================================================
    print("\n" + "-" * 86)
    print(" 📌 SCÉNARIO 1 : Mutex Physique Inviolable (Hard) & Signal Matériel (Hard)")
    print("    L'incompatibilité et le signal sont des lois physiques dures.")
    print("-" * 86)
    
    raw_npu_soft_1 = [
        {
            "schema": SCHEMA_ALLOCATION,
            "params": {"var": "coherence_logique", "value": 1},
            "weight": 100  # Poids de l'ancienne cohérence logique interne
        }
    ]
    validated_soft_1 = validate_npu_output(raw_npu_soft_1, lkb, spec)
    
    builder_1 = HybridSmtBuilder(horizon=lkb.horizon)
    for b in spec["bool_vars"]:
        builder_1.bvar(b)
        
    # Hard 1 : Le signal matériel s'impose
    builder_1.add_hard_schema(lkb, SCHEMA_ALLOCATION, {"var": "signal_materiel", "value": 1})
    # Hard 2 : Contradiction mutuelle physique
    builder_1.add_hard_schema(lkb, SCHEMA_MUTEX, {"a": "signal_materiel", "b": "coherence_logique"})
    
    soft_meta_1 = {}
    for idx, item in enumerate(validated_soft_1, start=1):
        builder_1.add_soft_schema(idx, lkb, item["schema"], item["params"])
        soft_meta_1[idx] = {
            "name": constraint_name(item["schema"], item["params"]),
            "weight": item["weight"],
            "schema": item["schema"],
            "params": item["params"],
        }
    
    all_soft_ids_1 = list(soft_meta_1.keys())
    
    # 1. Test SAT initial
    ok_1, _ = builder_1.solve_active(all_soft_ids_1)
    print(f" [1. TEST COHÉRENCE] Statut global : {'SAT' if ok_1 else 'UNSAT (CONTRADICTION FORMELLE DÉTECTÉE)'}")
    
    # 2. Extraction du MUS
    mus_1 = builder_1.compute_mus(all_soft_ids_1)
    mus_desc_1 = [f"#{cid} {soft_meta_1[cid]['name']} (w={soft_meta_1[cid]['weight']})" for cid in mus_1]
    print(f" [2. MUS EXTRAIT]    Noyau contradictoire isolé par Hadès : {mus_desc_1}")
    
    # 3. Relaxation MaxSAT
    best_1 = find_minimal_relaxation(builder_1, soft_meta_1, all_soft_ids_1)
    sol_1 = best_1["solution"]
    print(f" [3. MAXSAT ARBITRE] Relaxation optimale au coût minimal de {best_1['cost']} :")
    print(f"    ├─ Contrainte relaxée : #{best_1['relaxed'][0]} {soft_meta_1[best_1['relaxed'][0]]['name']}")
    print(f"    ├─ signal_materiel   = {sol_1['bools']['signal_materiel']}  (ACCUEILLI / CONSERVÉ)")
    print(f"    └─ coherence_logique = {sol_1['bools']['coherence_logique']} (ROMPUE / SOUMISE AU FER)")
    
    # =========================================================================
    # SCÉNARIO 2 : COMPÉTITION PONDÉRÉE ENTRE COHÉRENCE ET MUTEX SOUPLE
    # =========================================================================
    print("\n" + "-" * 86)
    print(" 📌 SCÉNARIO 2 : Arbitrage Pondéré — Mutex Souple (w=200) vs Cohérence Souple (w=100)")
    print("    Sous la contrainte dure inviolable : Signal_Materiel == True (Hard).")
    print("-" * 86)
    
    raw_npu_soft_2 = [
        {"schema": SCHEMA_ALLOCATION, "params": {"var": "coherence_logique", "value": 1}, "weight": 100},
        {"schema": SCHEMA_MUTEX, "params": {"a": "signal_materiel", "b": "coherence_logique"}, "weight": 200}
    ]
    validated_soft_2 = validate_npu_output(raw_npu_soft_2, lkb, spec)
    
    builder_2 = HybridSmtBuilder(horizon=lkb.horizon)
    for b in spec["bool_vars"]:
        builder_2.bvar(b)
        
    # Hard : Seul le signal matériel est garanti dur
    builder_2.add_hard_schema(lkb, SCHEMA_ALLOCATION, {"var": "signal_materiel", "value": 1})
    
    soft_meta_2 = {}
    for idx, item in enumerate(validated_soft_2, start=1):
        builder_2.add_soft_schema(idx, lkb, item["schema"], item["params"])
        soft_meta_2[idx] = {
            "name": constraint_name(item["schema"], item["params"]),
            "weight": item["weight"],
            "schema": item["schema"],
            "params": item["params"],
        }
    
    all_soft_ids_2 = list(soft_meta_2.keys())
    
    # 1. Test SAT initial
    ok_2, _ = builder_2.solve_active(all_soft_ids_2)
    print(f" [1. TEST COHÉRENCE] Statut global : {'SAT' if ok_2 else 'UNSAT (CONTRADICTION FORMELLE DÉTECTÉE)'}")
    
    # 2. Extraction du MUS
    mus_2 = builder_2.compute_mus(all_soft_ids_2)
    mus_desc_2 = [f"#{cid} {soft_meta_2[cid]['name']} (w={soft_meta_2[cid]['weight']})" for cid in mus_2]
    print(f" [2. MUS EXTRAIT]    Noyau contradictoire isolé par Hadès : {mus_desc_2}")
    
    # 3. Relaxation MaxSAT
    best_2 = find_minimal_relaxation(builder_2, soft_meta_2, all_soft_ids_2)
    sol_2 = best_2["solution"]
    print(f" [3. MAXSAT ARBITRE] Relaxation optimale au coût minimal de {best_2['cost']} :")
    print(f"    ├─ Contrainte relaxée : #{best_2['relaxed'][0]} {soft_meta_2[best_2['relaxed'][0]]['name']} (Poids faible w=100)")
    print(f"    ├─ Contrainte maintenue : #{list(set(all_soft_ids_2) - set(best_2['relaxed']))[0]} {soft_meta_2[list(set(all_soft_ids_2) - set(best_2['relaxed']))[0]]['name']} (Poids fort w=200)")
    print(f"    ├─ signal_materiel   = {sol_2['bools']['signal_materiel']}  (ACCUEILLI / CONSERVÉ)")
    print(f"    └─ coherence_logique = {sol_2['bools']['coherence_logique']} (ROMPUE / SOUMISE AU FER)")

    dt_total = round((time.perf_counter() - t0) * 1000.0, 3)
    print("\n" + "=" * 86)
    print(f" 🏆 DOUBLE ÉPREUVE TERMINÉE AVEC SUCCÈS SUR LE SILICIUM EN {dt_total} ms !")
    print("=" * 86)
    
    lkb.close()

if __name__ == "__main__":
    executer_experience_dilemme()

