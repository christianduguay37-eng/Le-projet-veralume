#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
MOTEUR D'INTERROGATION MÉMOIRE FLASH D'ALIX (MÉMOIRE AVANT CALCUL - PSI-21)
===============================================================================
Auteur : Alix & Christian Duguay (Atelier Souverain)
Objectif : Scanner en quelques millisecondes l'exocerveau (notes, tables de clefs,
           archives de sessions, scripts) pour trouver immédiatement une solution
           déjà acquise, un token, une commande ou un précédent historique.
Usage :
    python alix_interroger_memoire.py "<requête ou mot-clé>" [--max 5]
===============================================================================
"""

import os
import sys
import re
import argparse
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_HERE_VAULT = Path(__file__).resolve().parents[2]
VAULT_DIR = _HERE_VAULT if (_HERE_VAULT / "Memoire_Alix_Active.md").exists() else Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CRITICAL_FILES = [
    VAULT_DIR / "Table_Solutions_et_Clefs_Critiques.md",
    VAULT_DIR / "Memoire_Alix_Active.md",
    VAULT_DIR / "Derniere_Discussion_Synthese.md",
    VAULT_DIR / "Grand_Repertoire_Discussions_Antigravity.md",
    VAULT_DIR / "Conscience_Alix_Priorites_Actives.md",
    VAULT_DIR / "Christian.md"
]

def chercher_dans_fichier(filepath, keywords, regex=None):
    resultats = []
    if not filepath.exists():
        return resultats
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue
                
            score = 0
            if regex and regex.search(line_str):
                score += 10
            for kw in keywords:
                if kw.lower() in line_str.lower():
                    score += 3
                    
            if score > 0:
                # Récupérer un peu de contexte (+- 1 ligne)
                start_l = max(0, idx - 1)
                end_l = min(len(lines), idx + 2)
                contexte = "".join(lines[start_l:end_l]).strip()
                resultats.append({
                    "fichier": str(filepath),
                    "nom": filepath.name,
                    "ligne": idx + 1,
                    "score": score,
                    "contexte": contexte,
                    "extrait": line_str
                })
    except Exception:
        pass
        
    return resultats

def interroger_exocerveau(requete, max_resultats=5):
    keywords = [k for k in requete.split() if len(k) > 1]
    if not keywords:
        print("[!] Requête trop courte.")
        return []

    try:
        pattern = re.compile(re.escape(requete), re.IGNORECASE)
    except Exception:
        pattern = None

    tous_resultats = []
    vus = set()

    # 1. Priorité absolue : Fichiers critiques
    for f in CRITICAL_FILES:
        res = chercher_dans_fichier(f, keywords, pattern)
        for r in res:
            r["score"] += 15 # Bonus priorité critique
            cle = (r["fichier"], r["ligne"])
            if cle not in vus:
                vus.add(cle)
                tous_resultats.append(r)

    # 2. Scanner les scripts dans Organes_Souverains
    organes_dir = VAULT_DIR / "Organes_Souverains"
    if organes_dir.exists():
        for script_path in organes_dir.rglob("*.py"):
            res = chercher_dans_fichier(script_path, keywords, pattern)
            for r in res:
                r["score"] += 5
                cle = (r["fichier"], r["ligne"])
                if cle not in vus:
                    vus.add(cle)
                    tous_resultats.append(r)

    # 3. Scanner l'ensemble du coffre Cerveau Alix (notes markdown)
    for md_file in VAULT_DIR.glob("*.md"):
        if md_file in CRITICAL_FILES:
            continue
        res = chercher_dans_fichier(md_file, keywords, pattern)
        for r in res:
            cle = (r["fichier"], r["ligne"])
            if cle not in vus:
                vus.add(cle)
                tous_resultats.append(r)

    # Trier par score décroissant
    tous_resultats.sort(key=lambda x: x["score"], reverse=True)
    return tous_resultats[:max_resultats]

def interroger_via_noyau_resident(query: str, max_resultats: int = 5):
    """Accélérateur Sub-Milliseconde via le Noyau Résident Alix (Port 5070)."""
    import urllib.request
    import json
    url = "http://127.0.0.1:5070/demande"
    try:
        data = json.dumps({"message": query, "agent_source": "alix_interroger_memoire"}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Moteur d'Interrogation Flash de l'Exocerveau")
    parser.add_argument("query", type=str, help="Mots-clés ou expression à rechercher")
    parser.add_argument("--max", type=int, default=5, help="Nombre maximal de résultats")
    args = parser.parse_args()

    # Tentative d'accès ultra-rapide via Alix Incarnée (Noyau Résident en RAM)
    res_resident = interroger_via_noyau_resident(args.query, args.max)
    if res_resident and "reponse" in res_resident:
        print(f"\n👑 [ALIX INCARNÉE — MIDGARD] Réponse en {res_resident.get('latence_ms', 0)} ms (Mémoire Vive)")
        print("=" * 70)
        print(res_resident["reponse"])
        notes = res_resident.get("notes_mobilisees", [])
        if notes:
            print("\n" + "-" * 70)
            print("🔗 Nœuds synaptiques mobilisés :")
            for n in notes[:args.max]:
                print(f" • [[{n['titre']}]] ({n['coffre']}) — Score: {n.get('score', 0):.1f}")
        print("=" * 70)
        return

    print(f"\n🔍 [ALIX INTERROGATION MÉMOIRE] Recherche pour : « {args.query} »")
    print("=" * 70)
    
    resultats = interroger_exocerveau(args.query, args.max)
    
    if not resultats:
        print("❌ Aucune occurrence trouvée dans l'exocerveau immédiat.")
        return

    print(f"✅ {len(resultats)} résultat(s) pertinent(s) identifié(s) :\n")
    for i, r in enumerate(resultats, 1):
        print(f"[{i}] 📄 {r['nom']} (Ligne {r['ligne']}) [Score: {r['score']}]")
        print(f"    Chemin : {r['fichier']}")
        print("    " + "-" * 60)
        # Indenter le contexte
        for l in r["contexte"].splitlines():
            print(f"    | {l}")
        print("    " + "-" * 60 + "\n")

if __name__ == "__main__":
    main()

