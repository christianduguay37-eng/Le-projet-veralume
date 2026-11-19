# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX MOTEUR D'INTERROGATION DES INVARIANTS PHYSIQUES & MATHÉMATIQUES (OEIS + NIST)
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import time
import sqlite3
import argparse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

INVARIANTS_DIR = (VAULT_DIR / "Invariants_Physiques")
OEIS_DB = INVARIANTS_DIR / "oeis_souverain.db"
NIST_DB = INVARIANTS_DIR / "nist_constantes.db"

def chercher_oeis(terme: str, limite: int = 5):
    if not OEIS_DB.exists():
        print("❌ Base OEIS absente.")
        return
    t0 = time.perf_counter()
    con = sqlite3.connect(str(OEIS_DB))
    cur = con.cursor()
    
    # Si le terme ressemble à une suite de nombres séparés par virgules ou espaces
    nettoye = terme.replace(" ", "").strip(",")
    est_sequence = any(c.isdigit() for c in nettoye) and ("," in nettoye or " " in terme)
    
    if est_sequence:
        pattern = f"%{nettoye}%"
        cur.execute("SELECT id, name, values_str FROM oeis WHERE values_str LIKE ? LIMIT ?", (pattern, limite))
        res = cur.fetchall()
    else:
        # Recherche FTS5 par mots-clés
        query_fts = f'"{terme}"*'
        cur.execute("""
            SELECT o.id, o.name, o.values_str 
            FROM oeis_fts f 
            JOIN oeis o ON f.id = o.id 
            WHERE oeis_fts MATCH ? 
            LIMIT ?
        """, (query_fts, limite))
        res = cur.fetchall()
        if not res:
            cur.execute("SELECT id, name, values_str FROM oeis WHERE name LIKE ? LIMIT ?", (f"%{terme}%", limite))
            res = cur.fetchall()

    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🔢 RÉSULTATS OEIS LOCAL : « {terme} »")
    print(f" ⏱️ Temps de recherche sur 400 000+ suites : {duree_ms:.2f} ms | Trouvés : {len(res)}")
    print("==========================================================================")
    for r in res:
        print(f"👉 [{r[0]}] {r[1]}")
        print(f"   Valeurs : {r[2][:70]}...\n")
    con.close()

def chercher_nist(terme: str, limite: int = 5):
    if not NIST_DB.exists():
        print("❌ Base NIST absente.")
        return
    t0 = time.perf_counter()
    con = sqlite3.connect(str(NIST_DB))
    cur = con.cursor()
    
    cur.execute("SELECT quantity, value, uncertainty, unit FROM nist_constants WHERE quantity LIKE ? LIMIT ?", (f"%{terme}%", limite))
    res = cur.fetchall()
    duree_ms = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" ⚛️ RÉSULTATS CONSTANTES NIST CODATA : « {terme} »")
    print(f" ⏱️ Temps de recherche : {duree_ms:.2f} ms | Trouvés : {len(res)}")
    print("==========================================================================")
    for r in res:
        incertitude = f" (± {r[2]})" if r[2] and r[2] != "(exact)" else " (exact)"
        print(f"👉 {r[0]} = {r[1]} {r[3]}{incertitude}")
    con.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interrogation des invariants OEIS et NIST")
    parser.add_argument("terme", type=str, help="Suite numérique ou nom de constante")
    parser.add_argument("--nist", action="store_true", help="Chercher dans les constantes physiques NIST")
    parser.add_argument("--limit", type=int, default=5, help="Nombre de résultats")
    args = parser.parse_args()

    if args.nist:
        chercher_nist(args.terme, args.limit)
    else:
        chercher_oeis(args.terme, args.limit)
