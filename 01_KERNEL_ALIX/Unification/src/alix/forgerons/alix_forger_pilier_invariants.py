# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX PILIER 3 : INVARIANTS DU MONDE PHYSIQUE & MATHÉMATIQUE (OEIS + NIST)
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Rapatrie l'intégralité de l'OEIS (400 000+ suites mathématiques).
- Rapatrie la table NIST CODATA complète (365 constantes fondamentales de la physique).
- Crée la base haute performance SQLite FTS5 indexée pour identification en < 1 ms.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import sys
import time
import gzip
import sqlite3
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
INVARIANTS_DIR = VAULT_DIR / "Invariants_Physiques"
INVARIANTS_DIR.mkdir(parents=True, exist_ok=True)
OEIS_DB = INVARIANTS_DIR / "oeis_souverain.db"
NIST_DB = INVARIANTS_DIR / "nist_constantes.db"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Alix-Invariants/1.0"

def forger_pilier_oeis():
    print("==========================================================================")
    print(" 🔢 FORGE DE L'OEIS (ON-LINE ENCYCLOPEDIA OF INTEGER SEQUENCES) — 400K+ ")
    print("==========================================================================")
    
    url_names = "https://oeis.org/names.gz"
    url_stripped = "https://oeis.org/stripped.gz"
    
    t0 = time.time()
    print("📥 Rapatriement de names.gz (définitions des suites)...", end=" ", flush=True)
    req = urllib.request.Request(url_names, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        names_data = gzip.decompress(resp.read()).decode('utf-8', errors='replace')
    print("OK.")
    
    print("📥 Rapatriement de stripped.gz (valeurs numériques brutes)...", end=" ", flush=True)
    req = urllib.request.Request(url_stripped, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        stripped_data = gzip.decompress(resp.read()).decode('utf-8', errors='replace')
    print("OK.")
    
    # Parser les définitions
    dict_names = {}
    for line in names_data.strip().split('\n'):
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split(' ', 1)
        if len(parts) == 2:
            dict_names[parts[0].strip()] = parts[1].strip()

    print(f"🧩 {len(dict_names):,} noms de suites parsés.")

    # Création base SQLite
    if OEIS_DB.exists():
        OEIS_DB.unlink()
        
    con = sqlite3.connect(str(OEIS_DB))
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("""
        CREATE TABLE oeis (
            id TEXT PRIMARY KEY,
            name TEXT,
            values_str TEXT
        )
    """)
    cur.execute("CREATE VIRTUAL TABLE oeis_fts USING fts5(id, name, values_str)")

    records = []
    records_fts = []
    for line in stripped_data.strip().split('\n'):
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split(' ', 1)
        if len(parts) == 2:
            seq_id = parts[0].strip()
            # La séquence contient des virgules : ,1,2,3,4,
            raw_vals = parts[1].strip().strip(',')
            nom = dict_names.get(seq_id, "")
            records.append((seq_id, nom, raw_vals))
            records_fts.append((seq_id, nom, raw_vals))

    print(f"💾 Insertion de {len(records):,} suites dans SQLite...", end=" ", flush=True)
    cur.executemany("INSERT INTO oeis VALUES (?, ?, ?)", records)
    cur.executemany("INSERT INTO oeis_fts VALUES (?, ?, ?)", records_fts)
    cur.execute("CREATE INDEX idx_values ON oeis(values_str)")
    con.commit()
    con.close()
    
    duree = time.time() - t0
    taille_mo = OEIS_DB.stat().st_size / (1024 * 1024)
    print(f"TERMINÉ en {duree:.1f}s ! ({taille_mo:.1f} Mo)")

def forger_pilier_nist():
    print()
    print("==========================================================================")
    print(" ⚛️ FORGE DES CONSTANTES FONDAMENTALES NIST CODATA (VÉRITÉ TERRAIN PHYSIQUE)")
    print("==========================================================================")
    url_nist = "https://physics.nist.gov/cuu/Constants/Table/allascii.txt"
    t0 = time.time()
    req = urllib.request.Request(url_nist, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        nist_data = resp.read().decode('utf-8', errors='replace')

    lines = nist_data.strip().split('\n')
    
    if NIST_DB.exists():
        NIST_DB.unlink()
        
    con = sqlite3.connect(str(NIST_DB))
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE nist_constants (
            quantity TEXT PRIMARY KEY,
            value TEXT,
            uncertainty TEXT,
            unit TEXT
        )
    """)
    cur.execute("CREATE VIRTUAL TABLE nist_fts USING fts5(quantity, value, unit)")

    constantes = []
    # Les données commencent après la ligne d'en-tête (vers ligne 10)
    for l in lines:
        if len(l) < 60 or "---" in l or "Quantity" in l:
            continue
        # Format fixe NIST :
        # Quantity (0-60) | Value (60-85) | Uncertainty (85-110) | Unit (110+)
        q = l[0:60].strip()
        v = l[60:85].strip()
        u = l[85:110].strip() if len(l) > 85 else ""
        unit = l[110:].strip() if len(l) > 110 else ""
        if q and v:
            constantes.append((q, v, u, unit))

    cur.executemany("INSERT INTO nist_constants VALUES (?, ?, ?, ?)", constantes)
    cur.executemany("INSERT INTO nist_fts (quantity, value, unit) VALUES (?, ?, ?)", [(c[0], c[1], c[3]) for c in constantes])
    con.commit()
    con.close()
    
    print(f"✅ {len(constantes)} constantes fondamentales gravées dans {NIST_DB.name} en {time.time()-t0:.2f}s !")

if __name__ == "__main__":
    forger_pilier_oeis()
    forger_pilier_nist()
