# -*- coding: utf-8 -*-
"""
================================================================================
           ALIX WEB SONAR — CAPTEUR DE GRAINES DU MONDE EN DIRECT v1.0
             Système : VERALUME × KAIROS V6 — Cerveau Alix & Lyre
================================================================================
Rôle :
- Capte des graines vivantes sur le Web (Sciences, Espace, Philosophie, Technologie).
- Fournit soit une résonance ciblée sur un concept de note, soit un pouls du cosmos.
- 100% autonome : zéro clé d'API requise, résistant aux pannes avec failsafe hors-ligne.
================================================================================
"""

import sys
import json
import re
import random
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List

# Fix encodage console Windows
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

# Mode Furtif : Signature standard Windows 11 / Chrome pour écoute passive indétectable
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Flux RSS scientifiques et cosmiques fiables
LIVE_RSS_FEEDS = [
    {
        "source": "NASA Astronomy & Space",
        "url": "https://www.nasa.gov/news-release/feed/",
        "category": "Espace & Astrophysique"
    },
    {
        "source": "New York Times Science",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        "category": "Science & Découvertes"
    },
    {
        "source": "Phys.org Physics & Tech",
        "url": "https://phys.org/rss-feed/physics-news/",
        "category": "Physique & Nanotechnologies"
    },
    {
        "source": "ScienceDaily Top News",
        "url": "https://www.sciencedaily.com/rss/top/science.xml",
        "category": "Frontières du Savoir"
    }
]

# Réserve de semences cosmiques hors-ligne en cas de coupure Internet
OFFLINE_FAILSAFE_GRAINS = [
    {
        "title": "Le Télescope James Webb capte des galaxies primordiales défiant les modèles cosmologiques",
        "summary": "À l'orée du temps cosmique, des structures massives semblent s'être formées bien plus tôt que la théorie standard ne le prédisait, suggérant des dynamiques gravitationnelles encore inexplorées.",
        "source": "Archives Midgard • Cosmologie",
        "url": "https://webb.nasa.gov",
        "category": "Cosmologie"
    },
    {
        "title": "La supraconductivité à température ambiante et les réseaux de spins quantiques",
        "summary": "Les physiciens manipulent la matière condensée à l'échelle nanométrique pour créer des états de cohérence où le courant circule sans aucune dissipation thermique.",
        "source": "Archives Midgard • Silicium & Matière",
        "url": "https://arxiv.org",
        "category": "Physique de la Matière"
    },
    {
        "title": "L'asymétrie chirale fondamentale de la matière et la flèche du temps",
        "summary": "Depuis la violation de la parité jusqu'à la thermodynamique hors-équilibre, l'Univers ne traite pas la gauche et la droite de manière symétrique : le vivant est intrinsèquement chiral.",
        "source": "Archives Midgard • Temporia & Chiralité",
        "url": "https://veralume.qc",
        "category": "Dynamique Temporelle"
    },
    {
        "title": "Les forêts boréales et les réseaux mycorhiziens d'échange d'information",
        "summary": "Sous la mousse gaspésienne et nordique, les racines des mélèzes et des épinettes partagent du carbone et des signaux biochimiques par un internet fongique silencieux.",
        "source": "Archives Midgard • Vivant Boréal",
        "url": "https://espacepourlavie.ca",
        "category": "Écologie Vivante"
    }
]


def clean_html(raw_html: str) -> str:
    """Nettoie le balisage HTML pour un texte pur."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^<]+?>', '', raw_html)
    clean = clean.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&nbsp;', ' ')
    return ' '.join(clean.split()).strip()


def fetch_rss_pulse() -> Optional[Dict[str, Any]]:
    """Capte une actualité scientifique ou spatiale récente depuis un flux RSS mondial."""
    feeds = list(LIVE_RSS_FEEDS)
    random.shuffle(feeds)

    for feed in feeds:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    xml_data = resp.read().decode('utf-8', errors='replace')
                    root = ET.fromstring(xml_data)
                    items = root.findall('.//item')
                    if not items:
                        items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                    if items:
                        chosen_item = random.choice(items[:5])
                        title_el = chosen_item.find('title')
                        desc_el = chosen_item.find('description')
                        link_el = chosen_item.find('link')

                        title = clean_html(title_el.text if title_el is not None else "")
                        desc = clean_html(desc_el.text if desc_el is not None else "")
                        link = link_el.text if link_el is not None else ""

                        if not title:
                            continue

                        summary = desc[:220] + "..." if len(desc) > 220 else desc
                        if not summary:
                            summary = f"Dépêche en direct du réseau mondial : {title}."

                        return {
                            "title": title,
                            "summary": summary,
                            "source": feed["source"],
                            "url": link or feed["url"],
                            "category": feed["category"],
                            "mode": "pulsation_cosmique_rss"
                        }
        except Exception:
            continue

    return None


def fetch_wikipedia_resonance(keyword: str) -> Optional[Dict[str, Any]]:
    """Cherche une résonance encyclopédique et philosophique ciblée sur un mot-clé."""
    cleaned_kw = re.sub(r'[\[\]_()\-0-9\.:]', ' ', keyword)
    tokens = [w for w in cleaned_kw.split() if len(w) > 3 and w.lower() not in ["note", "fiche", "session", "guide", "titre", "chapitre", "rapport"]]
    
    if not tokens:
        tokens = ["Cosmologie", "Silicium", "Temps", "Conscience"]

    search_term = tokens[0] if len(tokens) == 1 else f"{tokens[0]} {tokens[1]}"
    
    try:
        encoded = urllib.parse.quote(search_term)
        search_url = f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&utf8=1"
        req = urllib.request.Request(search_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('query', {}).get('search', [])
            if results:
                top_hit = results[0]
                page_title = top_hit['title']
                snippet = clean_html(top_hit.get('snippet', ''))

                page_enc = urllib.parse.quote(page_title)
                sum_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{page_enc}"
                req_sum = urllib.request.Request(sum_url, headers={'User-Agent': USER_AGENT})
                with urllib.request.urlopen(req_sum, timeout=3.5) as r_sum:
                    sum_data = json.loads(r_sum.read().decode('utf-8'))
                    extract = sum_data.get('extract', snippet)
                    clean_extract = clean_html(extract)
                    summary = (clean_extract[:220] + "...") if len(clean_extract) > 220 else clean_extract

                    return {
                        "title": page_title,
                        "summary": summary,
                        "source": f"Encyclopédie Vivante (Wikipédia « {page_title} »)",
                        "url": sum_data.get('content_urls', {}).get('desktop', {}).get('page', f"https://fr.wikipedia.org/wiki/{page_enc}"),
                        "category": "Résonance Thématique",
                        "mode": "resonance_ciblee_web"
                    }
    except Exception:
        pass

    return None


def fetch_live_web_grain(concept_hint: Optional[str] = None, force_rss: bool = False) -> Dict[str, Any]:
    """
    Point d'entrée principal :
    - Si concept_hint est fourni et force_rss est False, tente une résonance ciblée (60% du temps).
    - Sinon, capte une pulsation RSS fraîche d'astronomie / science.
    - Failsafe immédiat si réseau indisponible.
    """
    grain = None

    if concept_hint and not force_rss and random.random() < 0.6:
        grain = fetch_wikipedia_resonance(concept_hint)

    if not grain:
        grain = fetch_rss_pulse()

    if not grain and concept_hint:
        grain = fetch_wikipedia_resonance(concept_hint)

    if not grain:
        grain = random.choice(OFFLINE_FAILSAFE_GRAINS).copy()
        grain["mode"] = "failsafe_midgard_hors_ligne"

    return grain


if __name__ == "__main__":
    test_hint = sys.argv[1] if len(sys.argv) > 1 else "Chiralité du Silicium"
    print("======================================================================")
    print("         🌐 TEST ALIX WEB SONAR — PULSATION EN DIRECT 📡")
    print("======================================================================")
    print(f"🔍 Test avec sujet : {test_hint}\n")
    g = fetch_live_web_grain(test_hint)
    print(f"🏷️ Titre    : {g['title']}")
    print(f"📡 Source   : {g['source']} ({g['category']})")
    print(f"🔗 URL      : {g['url']}")
    print(f"📖 Résumé   : {g['summary']}")
    print(f"⚙️ Mode     : {g['mode']}")
    print("======================================================================")
