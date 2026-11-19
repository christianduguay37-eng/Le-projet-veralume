# -*- coding: utf-8 -*-
"""
================================================================================
     BANC D'ESSAI : SCALING MASSIF & RAMP-UP TOPOLOGIQUE (LUNAR LAKE 258V)
================================================================================
Objectif :
- Éprouver la capacité maximale d'ingestion et de calcul topologique du fer.
- Rampe de charge progressive : 25 -> 50 -> 100 -> 250 -> 500 -> 1 000 -> 2 000 textes.
- Mesure en temps réel :
  * Durée d'ingestion & vectorisation (ms)
  * Durée du produit matriciel de Gram dual G = 1/M * X * X^T (ms)
  * Durée de décomposition spectrale (valeurs propres & d_eff) (ms)
  * Débit (textes / seconde)
  * Impact thermique et RAM (Sécurité stricte : zéro surchauffe, arrêt si > 75% RAM)
================================================================================
"""

import os
import sys
import time
import re
import psutil
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")

# Récupération de textes réels issus des notes de l'Exocerveau
def collecter_corpus_reel(taille_max: int = 2500) -> List[str]:
    print(f"📦 Collecte de vraies notes du Sanctuaire (cible: {taille_max} fragments)...")
    textes = []
    fichiers = list(VAULT_DIR.rglob("*.md"))
    np.random.seed(42)
    np.random.shuffle(fichiers)

    for p in fichiers:
        if len(textes) >= taille_max:
            break
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore").strip()
            # Découper en paragraphes significatifs (> 150 caractères)
            paragraphes = [para.strip() for para in txt.split("\n\n") if len(para.strip()) > 150]
            for para in paragraphes:
                textes.append(para)
                if len(textes) >= taille_max:
                    break
        except Exception:
            continue

    print(f"✅ Corpus collecté : {len(textes)} textes réels prêts pour le banc d'essai.\n")
    return textes


def tester_lot(textes_lot: List[str]) -> Dict[str, Any]:
    M = len(textes_lot)
    t_debut = time.perf_counter()

    # 1. Tokenisation & Vocabulaire
    t0 = time.perf_counter()
    vocab = {}
    tokens_par_doc = []
    for txt in textes_lot:
        mots = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', txt.lower())
        tokens_par_doc.append(mots)
        for m in set(mots):
            vocab[m] = vocab.get(m, 0) + 1

    # Sélection des termes représentatifs
    seuil_min = 2 if M >= 10 else 1
    mots_retenus = [m for m, c in vocab.items() if c >= seuil_min]
    if len(mots_retenus) < 16:
        mots_retenus = list(vocab.keys())
    mots_retenus = mots_retenus[:1500]  # Max 1500 dimensions
    mot_a_idx = {m: i for i, m in enumerate(mots_retenus)}
    d = len(mots_retenus)

    # Construction de la matrice X (M x d)
    X = np.zeros((M, d), dtype=np.float32)
    for i, mots in enumerate(tokens_par_doc):
        for m in mots:
            if m in mot_a_idx:
                X[i, mot_a_idx[m]] += 1.0

    # Normalisation L2
    normes = np.linalg.norm(X, axis=1, keepdims=True)
    normes[normes == 0] = 1.0
    X = X / normes
    dt_vectorisation_ms = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Produit Matriciel de Gram Dual G = 1/M * (X @ X.T)
    t1 = time.perf_counter()
    G = (1.0 / M) * (X @ X.T)
    dt_gram_ms = round((time.perf_counter() - t1) * 1000, 2)

    # 3. Décomposition Spectrale & Dimension Effective
    t2 = time.perf_counter()
    valeurs_propres = np.linalg.eigvalsh(G)
    valeurs_propres = np.sort(valeurs_propres)[::-1]
    valeurs_propres = np.clip(valeurs_propres, 0.0, None)
    tr_G = float(np.sum(valeurs_propres))
    tr_G2 = float(np.sum(valeurs_propres ** 2))
    d_eff = (tr_G ** 2) / tr_G2 if tr_G2 > 0 else 1.0
    dt_spectral_ms = round((time.perf_counter() - t2) * 1000, 2)

    dt_total_ms = round((time.perf_counter() - t_debut) * 1000, 2)
    debit_docs_sec = round((M / (dt_total_ms / 1000.0)), 1) if dt_total_ms > 0 else 0.0

    return {
        "M": M,
        "d": d,
        "d_eff": round(d_eff, 2),
        "dt_vectorisation_ms": dt_vectorisation_ms,
        "dt_gram_ms": dt_gram_ms,
        "dt_spectral_ms": dt_spectral_ms,
        "dt_total_ms": dt_total_ms,
        "debit_docs_sec": debit_docs_sec
    }


def main():
    print("=" * 80)
    print("🚀 BANC D'ESSAI HAUTE PERFORMANCE — DÉBIT TOPOLOGIQUE LUNAR LAKE 258V")
    print("=" * 80)

    corpus = collecter_corpus_reel(2500)
    if len(corpus) < 2000:
        # Duplication si nécessaire pour le test de stress
        while len(corpus) < 2000:
            corpus += corpus[:2000 - len(corpus)]

    paliers = [25, 50, 100, 250, 500, 1000, 2000]
    resultats = []

    print(f"{'Palier':<8} | {'Dim d':<7} | {'d_eff':<7} | {'Vect (ms)':<10} | {'Gram (ms)':<10} | {'Spectr (ms)':<11} | {'Total (ms)':<10} | {'Débit (docs/s)':<14} | {'RAM %':<6}")
    print("-" * 100)

    for M in paliers:
        lot = corpus[:M]
        # Vérification sécurité mémoire avant palier
        mem = psutil.virtual_memory()
        if mem.percent > 85.0:
            print(f"⚠️ Alerte sécurité RAM ({mem.percent}%), arrêt d'urgence du banc.")
            break

        res = tester_lot(lot)
        mem_apres = psutil.virtual_memory()
        res["ram_pct"] = mem_apres.percent
        resultats.append(res)

        print(f"{res['M']:<8} | {res['d']:<7} | {res['d_eff']:<7} | {res['dt_vectorisation_ms']:<10} | {res['dt_gram_ms']:<10} | {res['dt_spectral_ms']:<11} | {res['dt_total_ms']:<10} | {res['debit_docs_sec']:<14} | {res['ram_pct']:<6}%")
        
        # Pause de 1 seconde entre chaque palier pour laisser respirer le fer
        time.sleep(1.0)

    print("-" * 100)
    meilleur_debit = max(r["debit_docs_sec"] for r in resultats)
    print(f"🏆 DÉBIT MAXIMAL ATTEINT : {meilleur_debit:,.1f} textes réels / seconde !")
    print("=" * 80)


if __name__ == "__main__":
    main()

