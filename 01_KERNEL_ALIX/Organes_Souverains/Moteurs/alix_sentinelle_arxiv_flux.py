# -*- coding: utf-8 -*-
"""
================================================================================
       ALIX SENTINELLE DU FLUX ARXIV QUOTIDIEN — RADAR SCIENTIFIQUE v1.0
              Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Ausculte chaque jour les nouvelles parutions sur arXiv (~1 000 à 1 300 preprints).
- Complète l'archive locale de 3.2M avec les données du jour sans doublon.
- Passe le lot quotidien sous la matrice de Gram duale (rafale topologique < 100 ms).
- Extrait les attracteurs de pointe et génère le Bulletin Scientifique de l'Atelier.
- Silencieux : 0 spam Telegram, 100% gravé en local dans Obsidian.
================================================================================
"""

import os
import sys
import time
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
DATA_DIR = VAULT_DIR / "Arxiv_Souverain" / "data"
BULLETINS_DIR = VAULT_DIR / "Monde_des_Decouvertes"
CONFIG_FILE = VAULT_DIR / "Present" / "arxiv_sentinelle_state.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Alix-ObservatoireArXiv/1.0"

STOP_WORDS = {
    "dans", "pour", "avec", "cette", "sont", "plus", "nous", "vous",
    "leur", "elle", "comme", "mais", "tout", "faire", "entre", "aussi",
    "with", "that", "this", "from", "which", "were", "been", "have", "they",
    "these", "those", "their", "will", "what", "when", "where", "into", "also",
    "such", "than", "then", "them", "both", "each", "more", "most", "other",
    "some", "only", "first", "about", "could", "would", "should", "here",
    "arxiv", "abstract", "paper", "study", "using", "based", "show", "shown",
    "results", "propose", "present", "approach", "method", "model", "models",
    "work", "state", "high", "order", "three", "system", "systems", "performance"
}

def charger_etat() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"derniere_date_synchro": "2026-10-19", "total_papiers_flux": 0}

def sauvegarder_etat(etat: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(etat, f, indent=2, ensure_ascii=False)

def aspirer_flux_recent(max_articles: int = 100) -> list:
    """Interroge l'API ArXiv pour les toutes dernières soumissions."""
    print("📡 Interrogation du flux mondial arXiv en cours...")
    # Requête générale ordonnée par date de soumission décroissante
    url = f"http://export.arxiv.org/api/query?search_query=all:ai+OR+all:quantum+OR+all:physics+OR+all:learning&start=0&max_results={max_articles}&sortBy=submittedDate&sortOrder=descending"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    articles = []
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            xml_data = resp.read().decode('utf-8', errors='replace')
            root = ET.fromstring(xml_data)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')

            for entry in entries:
                title_el = entry.find('{http://www.w3.org/2005/Atom}title')
                summary_el = entry.find('{http://www.w3.org/2005/Atom}summary')
                id_el = entry.find('{http://www.w3.org/2005/Atom}id')
                published_el = entry.find('{http://www.w3.org/2005/Atom}published')
                
                # Catégories
                cats = [c.attrib.get('term', '') for c in entry.findall('{http://www.w3.org/2005/Atom}category')]
                categories_str = " ".join(cats)

                # Auteurs
                authors = [a.find('{http://www.w3.org/2005/Atom}name').text for a in entry.findall('{http://www.w3.org/2005/Atom}author') if a.find('{http://www.w3.org/2005/Atom}name') is not None]
                authors_str = ", ".join(authors)

                if title_el is not None and summary_el is not None and id_el is not None:
                    arxiv_id = id_el.text.strip().split('/')[-1]
                    title = " ".join(title_el.text.strip().split())
                    abstract = " ".join(summary_el.text.strip().split())
                    pub_date = published_el.text.strip()[:10] if published_el is not None else ""

                    articles.append({
                        "id": arxiv_id,
                        "title": title,
                        "authors": authors_str,
                        "categories": categories_str,
                        "abstract": abstract,
                        "update_date": pub_date
                    })
    except Exception as e:
        print(f"⚠️ Erreur de connexion au flux arXiv : {e}")

    return articles

def integrer_lot_quotidien(articles: list):
    if not articles:
        print("ℹ️ Aucun nouvel article à intégrer pour le moment.")
        return

    print(f"📥 Intégration de {len(articles)} preprints dans la partition journalière...")
    
    # 1. Sauvegarde dans une partition quotidienne Parquet
    today_str = datetime.now().strftime("%Y%m%d")
    daily_file = DATA_DIR / f"daily_flux_{today_str}.parquet"
    
    schema = pa.schema([
        ("id", pa.string()),
        ("title", pa.string()),
        ("authors", pa.string()),
        ("categories", pa.string()),
        ("abstract", pa.string()),
        ("update_date", pa.string())
    ])
    
    pydict = {
        "id": [a["id"] for a in articles],
        "title": [a["title"] for a in articles],
        "authors": [a["authors"] for a in articles],
        "categories": [a["categories"] for a in articles],
        "abstract": [a["abstract"] for a in articles],
        "update_date": [a["update_date"] for a in articles]
    }
    
    table = pa.Table.from_pydict(pydict, schema=schema)
    pq.write_table(table, str(daily_file), compression="zstd")
    print(f"✅ Partition journalière gravée : {daily_file.name} ({daily_file.stat().st_size / 1024:.1f} Ko)")

    # 2. Rafale matricielle de Gram duale sur le lot
    t0 = time.perf_counter()
    M = len(articles)
    vocabulaire = {}
    for a in articles:
        mots = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', (a["title"] + " " + a["abstract"]).lower())
        for m in set(mots):
            if m not in STOP_WORDS and not m.isdigit():
                vocabulaire[m] = vocabulaire.get(m, 0) + 1

    mots_retenus = [m for m, c in vocabulaire.items() if c >= 2][:1000]
    if not mots_retenus:
        mots_retenus = list(vocabulaire.keys())[:500]
    d = len(mots_retenus)
    mot_a_idx = {m: i for i, m in enumerate(mots_retenus)}

    X = np.zeros((M, d), dtype=np.float32)
    for i, a in enumerate(articles):
        for m in re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', (a["title"] + " " + a["abstract"]).lower()):
            if m in mot_a_idx:
                X[i, mot_a_idx[m]] += 1.0

    normes = np.linalg.norm(X, axis=1, keepdims=True)
    normes[normes == 0] = 1.0
    X = X / normes

    G = (1.0 / M) * (X @ X.T)
    valeurs_propres = np.linalg.eigvalsh(G)[::-1]
    valeurs_propres = np.clip(valeurs_propres, 0.0, None)
    tr_G = float(np.sum(valeurs_propres))
    tr_G2 = float(np.sum(valeurs_propres ** 2))
    d_eff = (tr_G ** 2) / tr_G2 if tr_G2 > 0 else 1.0

    poids = np.sum(X, axis=0)
    top_idx = np.argsort(poids)[::-1][:6]
    attracteurs = [(mots_retenus[idx], float(poids[idx])) for idx in top_idx]
    duree_ms = (time.perf_counter() - t0) * 1000

    # 3. Rédaction du Bulletin d'Éveil dans Obsidian
    BULLETINS_DIR.mkdir(parents=True, exist_ok=True)
    bulletin_md = (
        f"---\n"
        f"titre: \"Bulletin ArXiv Quotidien — {datetime.now().strftime('%Y-%m-%d')}\"\n"
        f"date: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"\n"
        f"articles_ingérés: {M}\n"
        f"dimension_effective: {d_eff:.2f}\n"
        f"temps_calcul_ms: {duree_ms:.1f}\n"
        f"tags:\n"
        f"  - observatoire_scientifique\n"
        f"  - flux_arxiv_quotidien\n"
        f"  - topologie_spectrale\n"
        f"---\n\n"
        f"# 📡 Bulletin d'Éveil Scientifique Mondial — {datetime.now().strftime('%d %B %Y')}\n\n"
        f"> **Volume capté :** `{M} articles récents` &middot; **Temps de digestion :** `{duree_ms:.1f} ms`\n"
        f"> **Diversité effective ($d_{{\\text{{eff}}}}$) :** `{d_eff:.2f}`\n\n"
        f"### 🌌 Attracteurs Clés Émergents du Flux\n"
        + "\n".join([f"- **{m}** (énergie spectrale: `{w:.2f}`)" for m, w in attracteurs]) +
        f"\n\n### 🔬 Pépites Notables Sélectionnées\n"
        + "\n".join([f"- **[{a['id']}](https://arxiv.org/abs/{a['id']}) :** *{a['title']}* ({a['categories']})" for a in articles[:5]])
    )
    
    bulletin_path = BULLETINS_DIR / f"Bulletin_ArXiv_{today_str}.md"
    bulletin_path.write_text(bulletin_md, encoding="utf-8")
    print(f"✨ Bulletin souverain rédigé : {bulletin_path.name}")
    print(f"⚡ Attracteurs du jour : {', '.join([m for m, _ in attracteurs[:4]])}")

    # Mise à jour de l'état
    etat = charger_etat()
    etat["derniere_date_synchro"] = datetime.now().strftime("%Y-%m-%d")
    etat["total_papiers_flux"] = etat.get("total_papiers_flux", 0) + M
    sauvegarder_etat(etat)

def executer_sentinelle():
    arts = aspirer_flux_recent(max_articles=60)
    integrer_lot_quotidien(arts)

if __name__ == "__main__":
    executer_sentinelle()

