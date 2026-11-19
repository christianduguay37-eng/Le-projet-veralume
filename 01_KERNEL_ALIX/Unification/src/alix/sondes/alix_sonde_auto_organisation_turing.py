# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX SONDE TRANSVERSALE : AUTO-ORGANISATION, TURING & OSCILLATEURS COUPLÉS
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import sys
import time
import json
import sqlite3
from pathlib import Path
import pyarrow.dataset as ds
import pyarrow.compute as pc

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
INVARIANTS_DIR = VAULT_DIR / "Invariants_Physiques"
OEIS_DB = INVARIANTS_DIR / "oeis_souverain.db"
NIST_DB = INVARIANTS_DIR / "nist_constantes.db"
ARXIV_DIR = VAULT_DIR / "Arxiv_Souverain" / "data"
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"
DIR_VIVANT = CATHEDRALE_DIR / "03_Vivant_PubMed_BioRxiv"
DIR_BREVETS = CATHEDRALE_DIR / "04_Ingenierie_Brevets_USPTO"
DIR_LEAN = CATHEDRALE_DIR / "05_Preuves_Formelles_Lean4"
DIR_GUTENBERG = CATHEDRALE_DIR / "06_Temps_Profond_Gutenberg"
GUTENBERG_DB = DIR_GUTENBERG / "gutenberg_souverain.db"

def scan_nist():
    t0 = time.perf_counter()
    con = sqlite3.connect(str(NIST_DB))
    cur = con.cursor()
    cur.execute("SELECT quantity, value, uncertainty, unit FROM nist_constants WHERE quantity LIKE '%Faraday%'")
    res = cur.fetchall()
    con.close()
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_oeis():
    t0 = time.perf_counter()
    con = sqlite3.connect(str(OEIS_DB))
    cur = con.cursor()
    cur.execute("SELECT id, name, values_str FROM oeis WHERE id = 'A001622'")
    res = cur.fetchall()
    con.close()
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_arxiv():
    t0 = time.perf_counter()
    dataset = ds.dataset(str(ARXIV_DIR), format="parquet")
    filtre = pc.match_substring(pc.utf8_lower(ds.field("title")), "kuramoto") | pc.match_substring(pc.utf8_lower(ds.field("title")), "reaction-diffusion")
    scan = dataset.scanner(columns=["id", "title", "update_date", "abstract"], filter=filtre, batch_size=65536)
    res = []
    for batch in scan.to_batches():
        tb = batch.to_pydict()
        for i in range(len(tb["id"])):
            res.append({
                "id": tb["id"][i],
                "title": tb["title"][i].replace("\n", " ").strip(),
                "date": str(tb["update_date"][i])[:10] if tb["update_date"][i] else "",
                "abstract": tb["abstract"][i].replace("\n", " ").strip()
            })
            if len(res) >= 2:
                break
        if len(res) >= 2:
            break
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_vivant():
    t0 = time.perf_counter()
    res = []
    biorxiv_file = DIR_VIVANT / "data" / "train-00000-of-00001-f6af2da28b2b059f.parquet"
    if biorxiv_file.exists():
        try:
            dataset = ds.dataset(str(biorxiv_file), format="parquet")
            filtre = pc.match_substring(pc.utf8_lower(ds.field("abstract")), "gap junction") | pc.match_substring(pc.utf8_lower(ds.field("abstract")), "bioelectric")
            scan = dataset.scanner(columns=["abstract"], filter=filtre, batch_size=2048)
            for batch in scan.to_batches():
                for txt in batch["abstract"].to_pylist():
                    res.append({"source": "bioRxiv", "texte": txt.replace("\n", " ").strip()})
                    if len(res) >= 2:
                        break
                if len(res) >= 2:
                    break
        except Exception:
            pass
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_brevets():
    t0 = time.perf_counter()
    res = []
    abstract_dir = DIR_BREVETS / "abstract"
    if abstract_dir.exists():
        try:
            dataset = ds.dataset(str(abstract_dir), format="parquet")
            filtre = pc.match_substring(pc.utf8_lower(ds.field("text")), "oscillator")
            scan = dataset.scanner(columns=["text", "label"], filter=filtre, batch_size=2048)
            label_map = {
                0: "Human Necessities", 1: "Operations/Transport", 2: "Chemistry/Metallurgy",
                5: "Mechanical Engineering", 6: "Physics", 7: "Electricity / Electronics", 8: "Emerging Tech"
            }
            for batch in scan.to_batches():
                tb = batch.to_pydict()
                for i in range(len(tb["text"])):
                    t = tb["text"][i].lower()
                    if "phase" in t and ("coupl" in t or "lock" in t or "synchron" in t):
                        lbl = label_map.get(tb["label"][i], f"Classe {tb['label'][i]}")
                        res.append({"classe": lbl, "texte": tb["text"][i].replace("\n", " ").strip()})
                        if len(res) >= 2:
                            break
                if len(res) >= 2:
                    break
        except Exception:
            pass
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_lean():
    t0 = time.perf_counter()
    res = []
    mathlib_core_dir = DIR_LEAN / "mathlib_core"
    
    # 1. Inégalité de Jensen (Mathlib Jensen.lean)
    jensen_file = mathlib_core_dir / "Jensen.lean"
    if jensen_file.exists():
        txt = jensen_file.read_text(encoding="utf-8", errors="ignore")
        for line in txt.splitlines():
            if "theorem ConvexOn.map_sum_le" in line:
                res.append({
                    "theoreme": "ConvexOn.map_sum_le",
                    "module": "Mathlib.Analysis.Convex.Jensen",
                    "statement": line.strip(),
                    "role": "Inégalité de Jensen discrète : f(∑ w_i x_i) ≤ ∑ w_i f(x_i)"
                })
                break
        for line in txt.splitlines():
            if "lemma StrictConvexOn.map_sum_lt" in line:
                res.append({
                    "theoreme": "StrictConvexOn.map_sum_lt",
                    "module": "Mathlib.Analysis.Convex.Jensen",
                    "statement": line.strip(),
                    "role": "Inégalité de Jensen stricte pour fonctions strictement convexes"
                })
                break

    # 2. Convexité analytique du Log / mul_log (Convex_Log_Basic.lean & Convex_Log_Deriv.lean)
    basic_file = mathlib_core_dir / "Convex_Log_Basic.lean"
    if basic_file.exists():
        txt = basic_file.read_text(encoding="utf-8", errors="ignore")
        for line in txt.splitlines():
            if "theorem strictConcaveOn_log_Ioi" in line:
                res.append({
                    "theoreme": "strictConcaveOn_log_Ioi",
                    "module": "Mathlib.Analysis.Convex.SpecificFunctions.Basic",
                    "statement": line.strip(),
                    "role": "Concavité stricte de ln(x) sur (0, +∞), impliquant la convexité stricte de x ln(x)"
                })
                break

    deriv_file = mathlib_core_dir / "Convex_Log_Deriv.lean"
    if deriv_file.exists():
        txt = deriv_file.read_text(encoding="utf-8", errors="ignore")
        for line in txt.splitlines():
            if "theorem strictConcaveOn_sqrt_mul_log_Ioi" in line:
                res.append({
                    "theoreme": "strictConcaveOn_sqrt_mul_log_Ioi",
                    "module": "Mathlib.Analysis.Convex.SpecificFunctions.Deriv",
                    "statement": line.strip(),
                    "role": "Concavité stricte de √x * ln(x) sur (0, +∞)"
                })
                break

    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_gutenberg():
    t0 = time.perf_counter()
    res = []
    if GUTENBERG_DB.exists():
        con = sqlite3.connect(str(GUTENBERG_DB))
        cur = con.cursor()
        sql = """
        SELECT title, authors, subjects, snippet(gutenberg_fts, 5, '« ', ' »', '...', 22)
        FROM gutenberg_fts
        WHERE gutenberg_fts MATCH '(authors: Poincar* OR authors: Wentworth) AND (dynamic* OR form OR phyllotaxis)'
          AND subjects NOT LIKE '%Fiction%'
          AND (subjects LIKE '%Science%' OR subjects LIKE '%Mathematics%' OR subjects LIKE '%Physics%' OR subjects LIKE '%Morphology%')
        LIMIT 2
        """
        cur.execute(sql)
        rows = cur.fetchall()
        for r in rows:
            res.append({"title": r[0], "author": r[1], "subjects": r[2], "snippet": r[3].replace("\n", " ").strip()})
        con.close()
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def main():
    print("=" * 80)
    print(" 🌟 SONDE TRANSVERSALE : AUTO-ORGANISATION, MORPHOGENÈSE & OSCILLATEURS")
    print("=" * 80)
    print()

    # 1. NIST
    nist_res, t_nist = scan_nist()
    print(f"⚛️ [NIST CODATA] Faraday constant ({t_nist:.2f} ms) :")
    for r in nist_res:
        print(f"   • {r[0]} = {r[1]} {r[3]} ({r[2]})")
    print()

    # 2. OEIS
    oeis_res, t_oeis = scan_oeis()
    print(f"🔢 [OEIS] A001622 — Nombre d'Or phi ({t_oeis:.2f} ms) :")
    for r in oeis_res:
        print(f"   • [{r[0]}] {r[1]}")
        print(f"     Séquence : {r[2][:60]}...")
    print()

    # 3. arXiv
    arxiv_res, t_arxiv = scan_arxiv()
    print(f"📄 [arXiv 3.2M] Reaction-diffusion / Kuramoto model ({t_arxiv:.2f} ms) :")
    for r in arxiv_res:
        print(f"   • [{r['id']}] {r['title']} ({r['date']})")
        print(f"     Abstract : {r['abstract'][:180]}...")
    print()

    # 4. Le Vivant
    vivant_res, t_vivant = scan_vivant()
    print(f"🧬 [Vivant - bioRxiv] Bioelectric signaling / Gap junctions ({t_vivant:.2f} ms) :")
    for r in vivant_res:
        print(f"   • Source : {r['source']}")
        print(f"     Extrait : {r['texte'][:200]}...")
    print()

    # 5. Brevets (Le Fer)
    brev_res, t_brev = scan_brevets()
    print(f"⚙️ [Brevets - Le Fer] Coupled oscillators / Phase synchronization ({t_brev:.2f} ms) :")
    for r in brev_res:
        print(f"   • Classe : {r['classe']}")
        print(f"     Extrait : {r['texte'][:200]}...")
    print()

    # 6. Lean 4
    lean_res, t_lean = scan_lean()
    print(f"📐 [Lean 4 Mathlib] Inégalité de Jensen & Convexité analytique ({t_lean:.2f} ms) :")
    for r in lean_res:
        print(f"   • [{r['module']}] {r['theoreme']}")
        print(f"     Énoncé : {r['statement']}")
        print(f"     Rôle   : {r['role']}")
    print()

    # 7. Gutenberg
    gut_res, t_gut = scan_gutenberg()
    print(f"📜 [Gutenberg FTS5] Systèmes dynamiques / Poincare ({t_gut:.2f} ms) :")
    for r in gut_res:
        print(f"   • Titre  : {r['title']} ({r['author']})")
        print(f"     Extrait: {r['snippet']}")
    print()

    total_t = t_nist + t_oeis + t_arxiv + t_vivant + t_brev + t_lean + t_gut
    print("=" * 80)
    print(f"⏱️ TEMPS DE SCAN GLOBAL CUMULÉ : {total_t:.2f} ms")
    print(f"🚀 GAIN GUTENBERG : De 830.00 ms (Parquet text) à {t_gut:.2f} ms (SQLite FTS5) -> Facteur {830.0 / max(0.01, t_gut):.1f}x plus rapide !")
    print("=" * 80)

if __name__ == "__main__":
    main()
