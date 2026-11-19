# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX SONDE TRANSVERSALE SUR LES 6 PILIERS — LIMITE DE LANDAUER & THERMODYNAMIQUE
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
"""

import os
import sys
import time
import json
import gzip
import sqlite3
from pathlib import Path
import pyarrow.dataset as ds
import pyarrow.compute as pc

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
INVARIANTS_DIR = VAULT_DIR / "Invariants_Physiques"
OEIS_DB = INVARIANTS_DIR / "oeis_souverain.db"
NIST_DB = INVARIANTS_DIR / "nist_constantes.db"
ARXIV_DIR = VAULT_DIR / "Arxiv_Souverain" / "data"
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"
DIR_VIVANT = CATHEDRALE_DIR / "03_Vivant_PubMed_BioRxiv"
DIR_BREVETS = CATHEDRALE_DIR / "04_Ingenierie_Brevets_USPTO"
DIR_LEAN = CATHEDRALE_DIR / "05_Preuves_Formelles_Lean4"
DIR_GUTENBERG = CATHEDRALE_DIR / "06_Temps_Profond_Gutenberg"

def scan_nist():
    t0 = time.perf_counter()
    con = sqlite3.connect(str(NIST_DB))
    cur = con.cursor()
    cur.execute("SELECT quantity, value, uncertainty, unit FROM nist_constants WHERE quantity LIKE '%Boltzmann constant%' LIMIT 2")
    res = cur.fetchall()
    con.close()
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_oeis():
    t0 = time.perf_counter()
    con = sqlite3.connect(str(OEIS_DB))
    cur = con.cursor()
    cur.execute("SELECT id, name, values_str FROM oeis WHERE id = 'A002162' LIMIT 1")
    res = cur.fetchall()
    if not res:
        cur.execute("SELECT id, name, values_str FROM oeis WHERE values_str LIKE '%6,9,3,1,4,7%' LIMIT 1")
        res = cur.fetchall()
    con.close()
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_arxiv():
    t0 = time.perf_counter()
    dataset = ds.dataset(str(ARXIV_DIR), format="parquet")
    filtre = pc.match_substring(pc.utf8_lower(ds.field("title")), "landauer") | pc.match_substring(pc.utf8_lower(ds.field("title")), "reversible computing")
    scan = dataset.scanner(columns=["id", "title", "authors", "update_date", "abstract"], filter=filtre, batch_size=65536)
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
    # Recherche dans bioRxiv et PubMed
    termes = ["atp synthase", "kinetic proofreading"]
    
    # 1. bioRxiv
    biorxiv_file = DIR_VIVANT / "data" / "train-00000-of-00001-f6af2da28b2b059f.parquet"
    if biorxiv_file.exists():
        try:
            dataset = ds.dataset(str(biorxiv_file), format="parquet")
            filtre = pc.match_substring(pc.utf8_lower(ds.field("abstract")), "atp synthase") | pc.match_substring(pc.utf8_lower(ds.field("abstract")), "kinetic proofreading")
            scan = dataset.scanner(columns=["abstract"], filter=filtre, batch_size=2048)
            for batch in scan.to_batches():
                for txt in batch["abstract"].to_pylist():
                    res.append({"source": "bioRxiv", "texte": txt.replace("\n", " ")})
                    if len(res) >= 2:
                        break
                if len(res) >= 2:
                    break
        except Exception:
            pass

    # 2. PubMed si besoin
    if len(res) < 2:
        for gz_file in DIR_VIVANT.glob("*.jsonl.gz"):
            try:
                with gzip.open(gz_file, "rt", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line_low = line.lower()
                        if "atp synthase" in line_low or "kinetic proofreading" in line_low:
                            d = json.loads(line)
                            res.append({"source": f"PubMed ({gz_file.stem})", "texte": d.get("title", "") + " — " + d.get("abstract", "")[:250]})
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
            filtre = pc.match_substring(pc.utf8_lower(ds.field("text")), "adiabatic") | pc.match_substring(pc.utf8_lower(ds.field("text")), "subthreshold")
            scan = dataset.scanner(columns=["text", "label"], filter=filtre, batch_size=2048)
            for batch in scan.to_batches():
                tb = batch.to_pydict()
                for i in range(len(tb["text"])):
                    res.append({"label": tb["label"][i], "texte": tb["text"][i].replace("\n", " ").strip()})
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
    
    # 1. Vérification dans Mathlib 4 Core (Analyse Convexe du Logarithme & Entropie)
    convex_log_file = mathlib_core_dir / "Convex_Log_Basic.lean"
    if convex_log_file.exists():
        content = convex_log_file.read_text(encoding="utf-8", errors="ignore")
        for block in content.split("\n\n"):
            if "strictConcaveOn_log_Ioi" in block:
                lines = [l.strip() for l in block.split("\n") if l.strip() and not l.strip().startswith("--")]
                formal_stmt = " ".join(lines[:3])
                res.append({
                    "nl": "La concavité stricte du logarithme népérien sur (0, +∞) qui fonde l'inégalité de Gibbs et l'entropie de Shannon",
                    "formal": formal_stmt,
                    "preuve_exacte": "theorem strictConcaveOn_log_Ioi : StrictConcaveOn ℝ (Ioi 0) log"
                })
                break

    # 2. Complément ProofNet Parquet
    data_dir = DIR_LEAN / "data"
    if data_dir.exists() and len(res) < 2:
        try:
            dataset = ds.dataset(str(data_dir), format="parquet")
            for batch in dataset.to_batches():
                tb = batch.to_pydict()
                for i in range(len(tb["formal_statement"])):
                    formal = tb.get("formal_statement", [""])[i]
                    nl = tb.get("nl_statement", [""])[i] if "nl_statement" in tb else ""
                    if "log" in formal.lower() or "entropy" in formal.lower():
                        res.append({"nl": nl, "formal": formal, "preuve_exacte": formal})
                        if len(res) >= 2:
                            break
                if len(res) >= 2:
                    break
        except Exception:
            pass
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def scan_gutenberg():
    t0 = time.perf_counter()
    res = []
    data_dir = DIR_GUTENBERG / "data"
    if data_dir.exists():
        try:
            dataset = ds.dataset(str(data_dir), format="parquet")
            filtre = pc.match_substring(pc.utf8_lower(ds.field("TEXT")), "maxwell") & pc.match_substring(pc.utf8_lower(ds.field("TEXT")), "demon")
            scan = dataset.scanner(columns=["METADATA", "TEXT"], filter=filtre, batch_size=16)
            for batch in scan.to_batches():
                tb = batch.to_pydict()
                for i in range(len(tb["TEXT"])):
                    txt = tb["TEXT"][i]
                    meta = tb.get("METADATA", [""])[i]
                    pos = txt.lower().find("maxwell")
                    snippet = txt[max(0, pos-40):min(len(txt), pos+200)].replace("\n", " ").strip()
                    res.append({"meta": meta[:60], "snippet": snippet})
                    if len(res) >= 1:
                        break
                if len(res) >= 1:
                    break
        except Exception:
            pass
    d_ms = (time.perf_counter() - t0) * 1000
    return res, d_ms

def main():
    print("==========================================================================")
    print(" 🌟 SONDE TRANSVERSALE UNIVERSELLE : LIMITE DE LANDAUER & INFORMATION ")
    print("==========================================================================")
    print()

    # 1. NIST
    nist_res, t_nist = scan_nist()
    print(f"⚛️ [NIST CODATA] Boltzmann constant ({t_nist:.2f} ms) :")
    for r in nist_res:
        print(f"   • {r[0]} = {r[1]} {r[3]} ({r[2]})")
    print()

    # 2. OEIS
    oeis_res, t_oeis = scan_oeis()
    print(f"🔢 [OEIS] A002162 - ln(2) ({t_oeis:.2f} ms) :")
    for r in oeis_res:
        print(f"   • [{r[0]}] {r[1]}")
        print(f"     Valeurs : {r[2][:60]}...")
    print()

    # 3. arXiv
    arxiv_res, t_arxiv = scan_arxiv()
    print(f"📄 [arXiv 3.2M] Landauer limit / Reversible computing ({t_arxiv:.2f} ms) :")
    for r in arxiv_res:
        print(f"   • [{r['id']}] {r['title']} ({r['date']})")
        print(f"     Abstract : {r['abstract'][:200]}...")
    print()

    # 4. Le Vivant
    vivant_res, t_vivant = scan_vivant()
    print(f"🧬 [Vivant - bioRxiv / PubMed] ATP synthase / Kinetic proofreading ({t_vivant:.2f} ms) :")
    for r in vivant_res:
        print(f"   • Source : {r['source']}")
        print(f"     Extrait : {r['texte'][:220]}...")
    print()

    # 5. Brevets
    brev_res, t_brev = scan_brevets()
    print(f"⚙️ [Brevets - Le Fer] Adiabatic CMOS / Subthreshold ({t_brev:.2f} ms) :")
    for r in brev_res:
        print(f"   • Classe : {r['label']}")
        print(f"     Extrait : {r['texte'][:220]}...")
    print()

    # 6. Lean 4
    lean_res, t_lean = scan_lean()
    print(f"📐 [Lean 4] Real.log / Entropy ({t_lean:.2f} ms) :")
    for r in lean_res:
        print(f"   • Théorème : {r['nl'][:80]}...")
        print(f"     Formalisation : {r['formal']}")
    print()

    # 7. Gutenberg
    gut_res, t_gut = scan_gutenberg()
    print(f"📜 [Gutenberg] Maxwell / Demon ({t_gut:.2f} ms) :")
    for r in gut_res:
        print(f"   • Extrait : {r['snippet']}...")
    print()

    total_t = t_nist + t_oeis + t_arxiv + t_vivant + t_brev + t_lean + t_gut
    print("==========================================================================")
    print(f"⏱️ TEMPS DE SCAN GLOBAL CUMULÉ SUR LES 6 PILIERS : {total_t:.2f} ms")
    print("==========================================================================")

if __name__ == "__main__":
    main()

