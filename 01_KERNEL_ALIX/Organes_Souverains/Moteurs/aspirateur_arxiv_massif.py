# -*- coding: utf-8 -*-
"""
================================================================================
     ASPIRATEUR ARXIV MASSIF POUR LE SAS D'ASSIMILATION D'ALIX
================================================================================
Rôle :
- Interroge l'API officielle ArXiv sur nos 4 pôles de recherche de pointe.
- Télécharge 60 à 100 abstracts récents complets avec métadonnées.
- Dépose chaque article en fichier Markdown individuel dans :
  `Cerveau Alix/SAS_Assimilation_Massive/`.
- Permet à la Sonde d'Apprentissage Accéléré de déclencher sa rafale topologique.
================================================================================
"""

import os
import sys
import time
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
SAS_DIR = VAULT_DIR / "SAS_Assimilation_Massive"
SAS_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Alix-Souveraine-ArXiv/1.0"

REQUETES = [
    ("topologie_simpliciale", "all:simplicial+AND+all:topology+AND+all:neural"),
    ("calcul_en_memoire_cim3d", "all:neuromorphic+AND+all:crossbar+AND+all:memristor"),
    ("dimension_effective_gram", "all:gram+AND+all:matrix+AND+all:effective+AND+all:dimension"),
    ("fusion_frc_plasma", "all:field+AND+all:reversed+AND+all:configuration+AND+all:plasma")
]


def telecharger_lot_arxiv(nom_theme: str, query: str, max_articles: int = 20) -> int:
    print(f"📡 Interrogation ArXiv sur [{nom_theme}] (cible: {max_articles} articles)...")
    url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_articles}&sortBy=submittedDate&sortOrder=descending"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    articles_sauvegardes = 0
    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            xml_data = resp.read().decode('utf-8', errors='replace')
            root = ET.fromstring(xml_data)

            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            print(f"  📥 {len(entries)} articles reçus du dépôt ArXiv.")

            for i, entry in enumerate(entries):
                title_el = entry.find('{http://www.w3.org/2005/Atom}title')
                summary_el = entry.find('{http://www.w3.org/2005/Atom}summary')
                id_el = entry.find('{http://www.w3.org/2005/Atom}id')
                published_el = entry.find('{http://www.w3.org/2005/Atom}published')

                if title_el is not None and summary_el is not None:
                    title = " ".join(title_el.text.strip().split())
                    summary = " ".join(summary_el.text.strip().split())
                    arxiv_id = id_el.text.strip() if id_el is not None else f"id_{i}"
                    published = published_el.text.strip()[:10] if published_el is not None else ""

                    # Nettoyage du nom de fichier
                    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', title[:45]).strip('_')
                    fichier_nom = f"arxiv_{nom_theme}_{i+1}_{slug}.md"
                    fichier_path = SAS_DIR / fichier_nom

                    contenu_md = (
                        f"# {title}\n\n"
                        f"- **ArXiv ID :** `{arxiv_id}`\n"
                        f"- **Date de publication :** `{published}`\n"
                        f"- **Thème :** `{nom_theme}`\n\n"
                        f"## Abstract\n\n{summary}\n"
                    )

                    fichier_path.write_text(contenu_md, encoding="utf-8")
                    articles_sauvegardes += 1

    except Exception as e:
        print(f"  ⚠️ Erreur lors de la requête ArXiv [{nom_theme}] : {e}")

    return articles_sauvegardes


def main():
    print("=" * 70)
    print("🌌 ASPIRATION ARXIV MASSIF DANS LE SAS D'ALIX")
    print("=" * 70)

    total = 0
    for nom, q in REQUETES:
        nb = telecharger_lot_arxiv(nom, q, max_articles=20)
        total += nb
        time.sleep(2.0)  # Politesse API ArXiv

    print("=" * 70)
    print(f"🏆 TOTAL : {total} articles scientifiques déposés dans le SAS !")
    print(f"📂 Répertoire SAS : {SAS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()

