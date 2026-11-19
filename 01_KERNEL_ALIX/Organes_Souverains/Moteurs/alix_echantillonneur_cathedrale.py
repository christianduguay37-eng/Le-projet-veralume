# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX ÉCHANTILLONNEUR CATHÉDRALE — EXPLORATION ALÉATOIRE DU SAVOIR UNIVERSEL
        Système : VERALUME × KAIROS V6 — Démon des Songes & Lyre
================================================================================
Rôle :
- Tire aléatoirement et instantanément (< 20 ms) une pépite de connaissance
  dans les 11 piliers Parquet de la Cathédrale du Savoir Universel :
    * 03_Vivant_PubMed_BioRxiv
    * 04_Ingenierie_Brevets_USPTO
    * 05_Preuves_Formelles_Lean4
    * 06_Temps_Profond_Gutenberg
    * 07_MIT_Science_et_Cybernetique
    * 08_Mythes_Legendes_Cosmogonies
    * 09_Savoirs_Pratiques_et_Traditions
    * 10_Matiere_Materiaux_et_Chimie
    * 11_Dynamique_Historique_et_Macro_Sociale (Seshat)
    * 12_Heuristique_Innovation_et_Biomimetisme
    * 13_Geometrie_Semantique_et_Biais_Cognitifs
- Fournit la matière brute universelle pour la transmutation poétique de Lyre.
================================================================================
"""

import os
import sys
import random
from pathlib import Path
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"

_CACHE_PARQUETS = {}


def lister_parquets_par_pilier() -> dict[str, list[Path]]:
    """Indexe en cache mémoire les fichiers Parquet disponibles par pilier."""
    global _CACHE_PARQUETS
    if _CACHE_PARQUETS:
        return _CACHE_PARQUETS

    if not CATHEDRALE_DIR.exists():
        return {}

    parquets_par_pilier = {}
    for d in CATHEDRALE_DIR.iterdir():
        if d.is_dir() and d.name.startswith("0") or d.name.startswith("1"):
            pqs = list(d.rglob("*.parquet"))
            if pqs:
                parquets_par_pilier[d.name] = pqs

    _CACHE_PARQUETS = parquets_par_pilier
    return _CACHE_PARQUETS


def echantillonner_pepite_cathedrale() -> dict | None:
    """Tire une pépite aléatoire dans l'un des piliers de la Cathédrale."""
    piliers_map = lister_parquets_par_pilier()
    if not piliers_map:
        return None

    # Choix aléatoire d'un pilier
    pilier_nom = random.choice(list(piliers_map.keys()))
    pq_files = piliers_map[pilier_nom]
    pq_file = random.choice(pq_files)

    try:
        table = pq.read_table(str(pq_file))
        n_rows = len(table)
        if n_rows == 0:
            return None

        idx = random.randint(0, n_rows - 1)
        cols = table.column_names

        # Extraction intelligente du titre et du contenu
        titre = ""
        texte = ""
        source_label = pilier_nom

        for col in ["titre", "title", "name", "id", "concept"]:
            if col in cols:
                val = table[col][idx].as_py()
                if val:
                    titre = str(val).strip()
                    break

        if not titre:
            titre = f"{pilier_nom} #{idx}"

        # Recherche du texte explicatif
        for col in ["texte", "text", "abstract", "summary", "description", "invariant_kairos", "theme"]:
            if col in cols:
                val = table[col][idx].as_py()
                if val:
                    texte = str(val).strip()
                    if len(texte) > 30:
                        break

        if not texte and len(cols) > 0:
            # Fallback : assembler les premières colonnes textuelles
            parties = []
            for c in cols[:4]:
                v = table[c][idx].as_py()
                if v and len(str(v)) < 150:
                    parties.append(f"{c}: {v}")
            texte = " | ".join(parties)

        # Nettoyage et troncature équilibrée
        texte_clean = " ".join(texte.split())[:350]

        return {
            "pilier": pilier_nom,
            "titre": titre[:80],
            "texte": texte_clean,
            "source": f"Cathédrale Universelle • {pilier_nom}",
            "fichier": pq_file.name
        }
    except Exception as e:
        return None


if __name__ == "__main__":
    print("==========================================================================")
    print("   🏛️ TEST ÉCHANTILLONNAGE ALÉATOIRE CATHÉDRALE DU SAVOIR UNIVERSEL 🔮")
    print("==========================================================================")
    for i in range(3):
        res = echantillonner_pepite_cathedrale()
        if res:
            print(f"\n👉 [TIRAGE #{i+1}] {res['source']}")
            print(f"   📜 Titre : {res['titre']}")
            print(f"   💡 Texte : {res['texte'][:140]}...")

