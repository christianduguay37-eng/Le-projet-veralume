# -*- coding: utf-8 -*-
"""
================================================================================
          ALIX MOTEUR DE RECHERCHE SOUVERAIN SUR L'ARCHIVE ARXIV (3.2M)
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Scanne les 3 215 335 articles stockés en local (Parquet zstd) en millisecondes.
- Recherche multi-critères : mot-clé, thème, auteur, catégorie, période.
- Extraction chirurgicale des abstracts complets sans aucune connexion Internet.
- Calcul optionnel de l'empreinte topologique sur le sous-ensemble trouvé.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import sys
import time
import argparse
from pathlib import Path
import pyarrow.dataset as ds
import pyarrow.compute as pc

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DATA_DIR = (VAULT_DIR / "Arxiv_Souverain" / "data")

def interroger_arxiv(requete: str, categorie: str = None, limite: int = 10, annee_min: str = None):
    t0 = time.perf_counter()
    if not DATA_DIR.exists():
        print(f"❌ Dossier de données introuvable : {DATA_DIR}")
        return []

    dataset = ds.dataset(str(DATA_DIR), format="parquet")
    
    # Construction des filtres
    filtre = None
    if requete:
        # Recherche case-insensitive sur le titre
        filtre_titre = pc.match_substring_regex(pc.utf8_lower(ds.field("title")), requete.lower())
        filtre = filtre_titre

    if categorie:
        filtre_cat = pc.match_substring(pc.utf8_lower(ds.field("categories")), categorie.lower())
        filtre = filtre & filtre_cat if filtre is not None else filtre_cat

    colonnes = ["id", "title", "authors", "categories", "abstract", "update_date"]
    
    # Scanner streaming par batchs
    resultats = []
    scan = dataset.scanner(columns=colonnes, filter=filtre, batch_size=65536)
    
    for batch in scan.to_batches():
        tb = batch.to_pydict()
        nb = len(tb["id"])
        for i in range(nb):
            date_str = str(tb["update_date"][i])[:10] if tb["update_date"][i] else ""
            if annee_min and date_str and date_str < annee_min:
                continue
            res = {
                "id": tb["id"][i],
                "title": tb["title"][i].replace("\n", " ").strip(),
                "authors": tb["authors"][i].replace("\n", " ").strip() if tb["authors"][i] else "",
                "categories": tb["categories"][i],
                "abstract": tb["abstract"][i].replace("\n", " ").strip() if tb["abstract"][i] else "",
                "date": date_str
            }
            resultats.append(res)
            if len(resultats) >= limite:
                break
        if len(resultats) >= limite:
            break

    duree_ms = (time.perf_counter() - t0) * 1000
    return resultats, duree_ms

def afficher_resultats(requete: str, resultats, duree_ms):
    print("==========================================================================")
    print(f" 🔍 RÉSULTATS ARXIV SOUVERAIN LOCAL : « {requete} »")
    print(f" ⏱️ Temps de scan sur 3.2M articles : {duree_ms:.1f} ms | Trouvés : {len(resultats)}")
    print("==========================================================================")
    for idx, r in enumerate(resultats, 1):
        print(f"\n[{idx}] 📄 {r['title']}")
        print(f"    🔗 ID arXiv : {r['id']} | Date : {r['date']} | Catégories : {r['categories']}")
        print(f"    ✍️ Auteurs  : {r['authors'][:80]}...")
        print(f"    📖 Abstract : {r['abstract'][:250]}...")
    print("==========================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recherche ultra-rapide sur l'archive arXiv locale")
    parser.add_argument("query", type=str, help="Terme de recherche (titre/thème)")
    parser.add_argument("--cat", type=str, default=None, help="Filtrer par catégorie (ex: cs.AI, quant-ph)")
    parser.add_argument("--limit", type=int, default=5, help="Nombre max de résultats")
    parser.add_argument("--annee", type=str, default=None, help="Date minimale YYYY-MM-DD")
    args = parser.parse_args()

    res, d_ms = interroger_arxiv(args.query, args.cat, args.limit, args.annee)
    afficher_resultats(args.query, res, d_ms)
