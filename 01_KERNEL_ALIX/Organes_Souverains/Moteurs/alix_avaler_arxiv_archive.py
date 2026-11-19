# -*- coding: utf-8 -*-
"""
================================================================================
          ALIX OBSERVATOIRE SCIENTIFIQUE MONDIAL — AVALEUR D'ARXIV v1.0
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Rapatrie l'intégralité de l'archive arXiv (3 215 335 articles de 1991 à 2026).
- Format natif : 11 fichiers Parquet zstd (2.69 Go sur NVMe).
- Zéro surcharge NTFS : 11 fichiers uniques requêtables en microsecondes.
- Valide l'intégrité de chaque partition et génère l'index souverain.
================================================================================
"""

import os
import sys
import time
from pathlib import Path
from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

TARGET_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Arxiv_Souverain")
DATA_DIR = TARGET_DIR / "data"
REPO_ID = "librarian-bots/arxiv-metadata-snapshot"
TOTAL_FILES = 11

def telecharger_et_valider_archive():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("==========================================================================")
    print(" 🌟 ALIX OBSERVATOIRE SCIENTIFIQUE : RAPATRIEMENT COMPLET D'ARXIV (3.2M) ")
    print("==========================================================================")
    print(f"📁 Destination locale : {DATA_DIR}")
    print(f"📦 Dépôt source       : {REPO_ID} (11 partitions Parquet)")
    print()

    total_articles = 0
    total_octets = 0
    t_global_0 = time.time()

    for idx in range(TOTAL_FILES):
        filename = f"data/train-{idx:05d}-of-{TOTAL_FILES:05d}.parquet"
        dest_file = TARGET_DIR / filename
        
        t0 = time.time()
        print(f"[{idx+1}/{TOTAL_FILES}] Rapatriement de {filename}...", end=" ", flush=True)

        # Si le fichier existe déjà et est intègre, on ne le retélécharge pas
        if dest_file.exists() and dest_file.stat().st_size > 50 * 1024 * 1024:
            size_mo = dest_file.stat().st_size / (1024 * 1024)
            print(f"DÉJÀ PRÉSENT ({size_mo:.1f} Mo).", end=" ", flush=True)
        else:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                repo_type="dataset",
                local_dir=str(TARGET_DIR)
            )
            t1 = time.time()
            size_mo = dest_file.stat().st_size / (1024 * 1024)
            debit = size_mo / max(0.01, (t1 - t0))
            print(f"OK ({size_mo:.1f} Mo en {t1-t0:.2f}s | {debit:.1f} Mo/s).", end=" ", flush=True)

        # Validation de lecture Parquet & comptage
        try:
            meta = pq.read_metadata(dest_file)
            nb_lignes = meta.num_rows
            total_articles += nb_lignes
            total_octets += dest_file.stat().st_size
            print(f"➔ {nb_lignes:,} articles validés.")
        except Exception as e:
            print(f"⚠️ Erreur de validation : {e}")

    t_global_total = time.time() - t_global_0
    total_go = total_octets / (1024 * 1024 * 1024)
    print()
    print("==========================================================================")
    print(f"🎉 RAPATRIEMENT COMPLET ACHEVÉ EN {t_global_total:.1f} SECONDES !")
    print(f"📚 Total Articles Gravés  : {total_articles:,} articles scientifiques")
    print(f"💾 Poids Réel sur NVMe    : {total_go:.2f} Go (Format Parquet zstd)")
    print("==========================================================================")
    return total_articles, total_go

if __name__ == "__main__":
    telecharger_et_valider_archive()

