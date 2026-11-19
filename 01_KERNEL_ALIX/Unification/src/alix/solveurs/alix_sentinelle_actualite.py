# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX SENTINELLE ACTUALITÉ — OBSERVATOIRE DU RÉEL VIVANT & BOULE DE NEIGE
              Système : VERALUME × KAIROS V6 — Démon d'Actualité Souverain
================================================================================
Doctrine de l'Artisan (Christian Duguay) :
« Chaque texte exploré, chaque article ou information doit servir à grossir 
  le champ lexical de recherche. »

Rôle :
1. Moissonne les flux d'actualité réels (Radio-Canada, Le Devoir, BBC, Hacker News, Ars).
2. Fait tourner la vraie BOULE DE NEIGE SÉMANTIQUE :
   - Extrait en direct les nouvelles entités (acteurs, institutions, lois, technologies).
   - Auto-étend récursivement le Lexique_Vivant_Actualite_Reelle.md.
   - Génère des recombinaisons sémantiques émergentes pour les futures battues.
3. Convertit les informations en format compressible pur dans le coffre :
   - Registre_Faits_Actualite_Compressibles.md (Invariants déterministes, 0 bavardage).
   - Synthese_Actualite_du_Jour.md (Horodatage strict, signal 100%).
   - Pistes_Actualite.md (Carnet d'intuitions de Christian connecté au flux).
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import sys
import re
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import Counter

# Encodage console
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

CERVEAU_ALIX = VAULT_DIR
ACTUALITE_DIR = CERVEAU_ALIX / "Present" / "actualite"
ACTUALITE_DIR.mkdir(parents=True, exist_ok=True)

# Chemins maîtres dans le coffre
LEXIQUE_VIVANT_MD = CERVEAU_ALIX / "Lexique_Vivant_Actualite_Reelle.md"
LEXIQUE_JSON = ACTUALITE_DIR / "lexique_actualite_state.json"
REGISTRE_FAITS_MD = ACTUALITE_DIR / "Registre_Faits_Actualite_Compressibles.md"
PISTES_ACTUALITE_MD = ACTUALITE_DIR / "Pistes_Actualite.md"
SYNTHESE_MD = ACTUALITE_DIR / "Synthese_Actualite_du_Jour.md"
ETAT_JSON = ACTUALITE_DIR / "dernieres_nouvelles.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (Alix-BouleDeNeige-Reel/3.0)"

FLUX_ACTUALITE = {
    "quebec_canada": [
        {"nom": "Radio-Canada Manchettes", "url": "https://ici.radio-canada.ca/rss/4159", "poids": 1},
        {"nom": "Radio-Canada Politique", "url": "https://ici.radio-canada.ca/rss/4175", "poids": 1},
        {"nom": "Le Devoir Manchettes", "url": "https://www.ledevoir.com/rss/manchettes.xml", "poids": 1},
    ],
    "geopolitique_monde": [
        {"nom": "BBC News World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "poids": 1},
    ],
    "techno_ia_silicium": [
        {"nom": "Radio-Canada Techno", "url": "https://ici.radio-canada.ca/rss/4169", "poids": 1},
        {"nom": "Hacker News (Top)", "url": "https://news.ycombinator.com/rss", "poids": 1},
        {"nom": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "poids": 1},
    ]
}

GLOBAL_STOP_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "et", "ou",
    "en", "dans", "par", "pour", "vers", "avec", "sans", "sur", "sous", "chez",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
    "mes", "tes", "ses", "nos", "vos", "leurs", "qui", "que", "quoi", "dont",
    "où", "est", "sont", "ont", "a", "à", "au", "aux", "ne", "pas", "plus",
    "moins", "tout", "tous", "toute", "toutes", "faire", "fait", "comme",
    "aussi", "bien", "très", "ici", "là", "alors", "donc", "car", "mais",
    "si", "même", "être", "avoir", "alix", "christian", "duguay", "true",
    "false", "none", "après", "avant", "encore", "toujours", "déjà", "pres",
    "the", "and", "for", "with", "that", "this", "from", "which", "were",
    "been", "have", "they", "will", "what", "when", "where", "into", "also",
    "about", "their", "after", "says", "more", "first", "over", "time", "year",
    "hier", "aujourd", "hui", "deux", "trois", "rapport", "article", "source", "titre"
}

LEXIQUE_INITIAL_SEED = {
    "acteurs_et_dirigeants": [
        "Christian Duguay", "Justin Trudeau", "François Legault", "Pierre Poilievre",
        "Mark Carney", "Paul St-Pierre Plamondon", "Lorne Doerkson", "Donald Trump",
        "Kamala Harris", "Luiz Inacio Lula da Silva", "Flavio Bolsonaro", "Aleksandar Vučić"
    ],
    "institutions_et_appareils": [
        "Parti Québécois", "Coalition Avenir Québec", "Parti Conservateur", "Bloc Québécois",
        "Hydro-Québec", "SEAO", "CRTC", "Cour Suprême", "CHSLD", "Congrès mondial ouïghour"
    ],
    "lois_et_cadres_juridiques": [
        "Loi 101", "Loi 21", "Loi 96", "Bill C-11", "Bill C-63", "Charte des droits", "CLOUD Act"
    ],
    "technologies_et_souverainete": [
        "CIM 3D IC", "FRC-HTS", "Lunar Lake", "F-35", "OpenVINO", "NPU Intel", "NeXT Computer", "Semi-conducteurs"
    ],
    "geopolitique_et_territoires": [
        "Québec", "Canada", "Alberta", "Colombie-Britannique", "États-Unis", "Brésil", "Serbie", "Venezuela", "Arctique"
    ]
}


def clean_text(raw_text: str) -> str:
    """Nettoie balises HTML, entités XML et espaces multiples."""
    if not raw_text:
        return ""
    clean = re.sub(r'<[^<]+?>', '', raw_text)
    clean = clean.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&nbsp;', ' ')
    clean = clean.replace('&#39;', "'").replace('&lt;', '<').replace('&gt;', '>').replace('&#x27;', "'")
    return ' '.join(clean.split()).strip()


# ------------------------------------------------------------------------------
# 1. GESTION DU LEXIQUE VIVANT (BOULE DE NEIGE SÉMANTIQUE)
# ------------------------------------------------------------------------------
def charger_lexique() -> dict:
    """Charge le lexique vivant depuis le JSON ou initialise le seed."""
    if LEXIQUE_JSON.exists():
        try:
            return json.loads(LEXIQUE_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass

    lex = {k: list(v) for k, v in LEXIQUE_INITIAL_SEED.items()}
    lex.setdefault("termes_auto_decouverts", [])
    sauvegarder_lexique(lex)
    return lex


def sauvegarder_lexique(lexique: dict):
    """Sauvegarde le JSON machine et régénère la note Obsidian du Lexique Vivant."""
    try:
        with open(LEXIQUE_JSON, "w", encoding="utf-8") as f:
            json.dump(lexique, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erreur écriture {LEXIQUE_JSON} : {e}")

    # Synchroniser la note Markdown vivante dans Cerveau Alix
    synchroniser_lexique_obsidian(lexique)


def synchroniser_lexique_obsidian(lexique: dict):
    """Régénère la note Obsidian Lexique_Vivant_Actualite_Reelle.md."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_termes = sum(len(v) for k, v in lexique.items() if isinstance(v, list))
    auto_terms = lexique.get("termes_auto_decouverts", [])

    md = f"""---
titre: "Lexique Vivant — Actualité Réelle & Souveraineté (Auto-Expansion Sémantique)"
agent: "Alix & Sentinelle Actualité"
systeme: "VERALUME × KAIROS V6 — Boule de Neige Sémantique"
date_mise_a_jour: "{now_str}"
termes_totaux: {total_termes}
termes_auto_decouverts: {len(auto_terms)}
tags:
  - exocerveau
  - lexique_vivant
  - boule_de_neige
  - actualite_reelle
  - veille_souveraine
---

# ❄️ [[Lexique_Vivant_Actualite_Reelle]] — Le Champ Lexical Auto-Évolutif

> **Règle Fondatrice de l'Artisan (Christian Duguay) :**  
> *« Chaque texte exploré, chaque article ou information doit servir à grossir le champ lexical de recherche. »*  
> **Total Entités Actives :** `{total_termes} termes` &middot; **Dernière expansion Boule de Neige :** `{now_str}`

---

## 🏔️ 1. Termes Découverts en Battue Récente ({len(auto_terms)})
Ces termes ont été extraits automatiquement lors du passage de la sentinelle sur les flux réels :
"""
    if auto_terms:
        # Afficher les 40 derniers découverts
        for t in reversed(auto_terms[-40:]):
            md += f"- ⏱️ `{t['date']}` &middot; **`{t['terme']}`** *(contexte : {t['contexte']})*\n"
    else:
        md += "*En attente de la première récolte de battue...*\n"

    md += "\n---\n\n## 🏛️ 2. Répertoire des Pôles Invariants\n\n"
    for cat, items in lexique.items():
        if cat == "termes_auto_decouverts" or not isinstance(items, list):
            continue
        cat_label = cat.replace("_", " ").title()
        md += f"### 🔹 {cat_label} ({len(items)})\n"
        for item in sorted(items, key=lambda x: str(x).lower()):
            md += f"- `{item}`\n"
        md += "\n"

    md += "---\n*Lexique réactualisé automatiquement par la Boule de Neige Sémantique d'Alix.*\n"

    try:
        with open(LEXIQUE_VIVANT_MD, "w", encoding="utf-8") as f:
            f.write(md)
    except Exception as e:
        print(f"⚠️ Erreur écriture {LEXIQUE_VIVANT_MD} : {e}")


def extraire_et_etendre_boule_de_neige(text: str, source_titre: str, lexique: dict) -> list[str]:
    """
    Cœur de la Boule de Neige :
    Extrait les entités nommées réelles et les intègre au lexique vivant.
    """
    nouveaux_termes = []
    
    # 1. Candidats en majuscules (Acteurs, institutions, entreprises, toponymes)
    candidats = re.findall(r'\b[A-ZÀ-ÖØ][a-zA-Z0-9À-ÖØ-öø-ÿ_-]{2,}(?:\s+[A-ZÀ-ÖØ][a-zA-Z0-9À-ÖØ-öø-ÿ_-]{2,})*\b', text)
    
    # 2. Entités critiques, acronymes et projets de loi
    specialises = re.findall(r'\b(?:F-35|F-\d+|C-\d+|Bill\s+[A-Z]-\d+|CHSLD|SEAO|CRTC|DSA|CETA|WEF|FMI|IMF|McKinsey|Northvolt|Brookfield|iPod|NeXT|BioWare|Nvidia|OpenVINO|NPU)\b', text, re.IGNORECASE)
    candidats.extend(specialises)

    # Recensement des termes déjà connus en minuscules
    connus = set()
    for cat, items in lexique.items():
        if isinstance(items, list):
            for it in items:
                t_nom = it.get("terme", "") if isinstance(it, dict) else str(it)
                connus.add(t_nom.strip().lower())

    now_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    for cand in set(candidats):
        c_clean = cand.strip().strip("-.,;:'\"")
        c_low = c_clean.lower()

        # Filtrage du bruit
        if len(c_clean) < 3 or c_low in GLOBAL_STOP_WORDS or c_low in connus:
            continue

        # Inscription dans la boule de neige
        item = {
            "terme": c_clean,
            "date": now_date,
            "contexte": source_titre[:70]
        }
        lexique.setdefault("termes_auto_decouverts", []).append(item)
        connus.add(c_low)
        nouveaux_termes.append(c_clean)

    if nouveaux_termes:
        sauvegarder_lexique(lexique)

    return nouveaux_termes


# ------------------------------------------------------------------------------
# 2. MOISSONNAGE & CONDENSATION FORMAT COMPRESSIBLE (INVARIANTS PURS)
# ------------------------------------------------------------------------------
def moissonner_flux(nom_source: str, url: str, limite: int = 5) -> list[dict]:
    """Télécharge et extrait les items d'un flux RSS ou Atom."""
    depeches = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
            tree = ET.fromstring(xml_data)

            items = tree.findall('.//item')
            if not items:
                items = tree.findall('.//{http://www.w3.org/2005/Atom}entry')

            for item in items[:limite]:
                titre = ""
                lien = ""
                resume = ""
                pubdate = ""

                t_elem = item.find('title') if item.find('title') is not None else item.find('{http://www.w3.org/2005/Atom}title')
                if t_elem is not None and t_elem.text:
                    titre = clean_text(t_elem.text)

                l_elem = item.find('link') if item.find('link') is not None else item.find('{http://www.w3.org/2005/Atom}link')
                if l_elem is not None:
                    lien = l_elem.text or l_elem.attrib.get('href', '')
                    if lien:
                        lien = lien.strip()

                d_elem = item.find('description') if item.find('description') is not None else item.find('{http://www.w3.org/2005/Atom}summary')
                if d_elem is not None and d_elem.text:
                    resume = clean_text(d_elem.text)

                p_elem = item.find('pubDate') if item.find('pubDate') is not None else item.find('{http://www.w3.org/2005/Atom}published')
                if p_elem is not None and p_elem.text:
                    pubdate = p_elem.text.strip()

                if titre:
                    depeches.append({
                        "source": nom_source,
                        "titre": titre,
                        "lien": lien,
                        "resume": resume[:280] + ("..." if len(resume) > 280 else ""),
                        "date_source": pubdate,
                        "horodatage_capture": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
    except Exception as e:
        print(f"⚠️ Erreur moissonnage [{nom_source}] ({url}) : {e}")

    return depeches


def enregistrer_faits_compressibles(depeches: list[dict], horodatage: str):
    """
    Enregistre les faits bruts sous format hautement compressible dans le coffre :
    Registre_Faits_Actualite_Compressibles.md (Table canonique sans bavardage).
    """
    table_rows = []
    for d in depeches:
        titre_clean = d['titre'].replace('|', '-').strip()
        resume_court = d['resume'].replace('|', '-').strip()[:140]
        src_label = f"[{d['source']}]({d['lien']})" if d['lien'] else d['source']
        table_rows.append(f"| `{d['horodatage_capture']}` | **{titre_clean}** | {resume_court} | {src_label} |")

    if not REGISTRE_FAITS_MD.exists():
        header = f"""---
titre: "Registre Forensique des Faits d'Actualité Compressibles"
date_creation: "{horodatage}"
statut: "Données Brutes Souveraines (Signal 100%)"
tags:
  - exocerveau
  - actualite_condensee
  - faits_empiriques
  - boucle_fer
---

# 🗄️ [[Registre_Faits_Actualite_Compressibles]] — Signal Brut & Invariants du Réel

> **Doctrine Déterministe :**  
> *Zéro bavardage journalistique. Chaque fait empirique est extrait sous forme d'invariant dense, horodaté et sourcé, directement injectable dans nos solveurs et le NPU.*

| Horodatage | Fait Invariant Compressé | Données & Contexte Factuel | Source Directe |
| :--- | :--- | :--- | :--- |
"""
        contenu = header + "\n".join(table_rows) + "\n"
    else:
        # Append au registre existant
        contenu = "\n".join(table_rows) + "\n"

    try:
        with open(REGISTRE_FAITS_MD, "a" if REGISTRE_FAITS_MD.exists() else "w", encoding="utf-8") as f:
            f.write(contenu)
        print(f"✅ [REGISTRE COMPRESSIBLE] {len(depeches)} faits purs gravés dans {REGISTRE_FAITS_MD.name}")
    except Exception as e:
        print(f"⚠️ Erreur écriture {REGISTRE_FAITS_MD} : {e}")


def generer_recombinaisons_emergentes(lexique: dict, count: int = 4) -> list[str]:
    """Génère des croisements sémantiques inédits pour orienter les prochaines battues."""
    auto_terms = [t["terme"] for t in lexique.get("termes_auto_decouverts", []) if isinstance(t, dict)]
    seed_terms = []
    for cat, items in lexique.items():
        if cat != "termes_auto_decouverts" and isinstance(items, list):
            seed_terms.extend(items)

    recombinaisons = []
    if auto_terms and seed_terms:
        import random
        for _ in range(count):
            t_auto = random.choice(auto_terms)
            t_seed = random.choice(seed_terms)
            recombinaisons.append(f"« {t_auto} » ⟷ « {t_seed} »")
    return recombinaisons


# ------------------------------------------------------------------------------
# 3. EXÉCUTION MAÎTRESSE DE LA SENTINELLE
# ------------------------------------------------------------------------------
def executer_veille_complete() -> dict:
    """Exécute un cycle complet : moissonnage, boule de neige, enregistrement compressible."""
    t0 = time.time()
    now_dt = datetime.now()
    horodatage_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    date_jour = now_dt.strftime("%Y-%m-%d")

    # 1. Charger le Lexique Vivant
    lexique = charger_lexique()

    resultats = {
        "horodatage": horodatage_str,
        "date_jour": date_jour,
        "piliers": {
            "quebec_canada": [],
            "geopolitique_monde": [],
            "techno_ia_silicium": []
        },
        "stats": {
            "total_depeches": 0,
            "termes_decouverts": 0,
            "duree_sec": 0.0
        },
        "nouveaux_termes": []
    }

    toutes_les_depeches = []

    # 2. Moissonnage et passage à la Boule de Neige
    for pilier, sources in FLUX_ACTUALITE.items():
        for src in sources:
            items = moissonner_flux(src["nom"], src["url"], limite=5)
            resultats["piliers"][pilier].extend(items)
            resultats["stats"]["total_depeches"] += len(items)

            for it in items:
                toutes_les_depeches.append(it)
                # La Boule de Neige tourne sur chaque titre et résumé
                corpus = f"{it['titre']}. {it['resume']}"
                nouveaux = extraire_et_etendre_boule_de_neige(corpus, it['titre'], lexique)
                resultats["nouveaux_termes"].extend(nouveaux)

    # Dédoublonnage des termes découverts lors de ce cycle
    resultats["nouveaux_termes"] = list(set(resultats["nouveaux_termes"]))
    resultats["stats"]["termes_decouverts"] = len(resultats["nouveaux_termes"])
    resultats["stats"]["duree_sec"] = round(time.time() - t0, 2)

    # 3. Recombinaisons sémantiques émergentes
    recombinaisons = generer_recombinaisons_emergentes(lexique, count=4)
    resultats["recombinaisons"] = recombinaisons

    # 4. Sauvegarde JSON machine d'état
    try:
        with open(ETAT_JSON, "w", encoding="utf-8") as f:
            json.dump(resultats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Impossible d'écrire {ETAT_JSON} : {e}")

    # 5. Gravure du Registre des Faits Compressibles
    enregistrer_faits_compressibles(toutes_les_depeches, horodatage_str)

    # 6. Génération de la Note Vivante Maître
    generer_note_synthese_markdown(resultats, recombinaisons)

    return resultats


def generer_note_synthese_markdown(data: dict, recombinaisons: list[str]):
    """Génère la note Obsidian avec horodatage strict et synthèse structurée."""
    horodatage = data["horodatage"]
    date_jour = data["date_jour"]
    nouveaux = data.get("nouveaux_termes", [])

    md_content = f"""---
titre: "Synthèse de l'Actualité Vivante du Réel — {date_jour}"
date_maj: "{horodatage}"
statut: "Observatoire du Présent & Boule de Neige (Loi PSI-21)"
tags:
  - exocerveau
  - actualite
  - etat_du_monde
  - veille_souveraine
  - boule_de_neige
  - present
---

# 🌍 [[Synthese_Actualite_du_Jour]] — Observatoire du Réel Vivant

> **Dernière Synchronisation :** `{horodatage}`  
> **Cycle Démon :** Actif &middot; {data['stats']['total_depeches']} dépêches analysées en {data['stats']['duree_sec']}s  
> **Effet Boule de Neige :** **+{len(nouveaux)} nouvelles entités** découvertes et greffées dans `[[Lexique_Vivant_Actualite_Reelle]]`.  
> **Format Compressible :** Gravé dans `[[Registre_Faits_Actualite_Compressibles]]`.

---

## ❄️ 1. Battue Boule de Neige (Nouveaux Concepts Découverts)

"""
    if nouveaux:
        md_content += f"> **Entités fraîches capturées ce cycle :**  \n"
        md_content += f"> `{', '.join(sorted(nouveaux))}`\n\n"
    else:
        md_content += "> *Toutes les entités du cycle étaient déjà répertoriées dans le Lexique Vivant.*\n\n"

    if recombinaisons:
        md_content += "### 🔀 Recombinaisons Émergentes (Nouvelles Pistes de Battue) :\n"
        for rec in recombinaisons:
            md_content += f"- 🎯 {rec}\n"
        md_content += "\n"

    md_content += """---

## ⚜️ 2. Québec & Canada (Institutions, Énergie, Souveraineté)

"""
    items_qc = data["piliers"]["quebec_canada"]
    if items_qc:
        for it in items_qc:
            md_content += f"- ⏱️ `{it['horodatage_capture']}` &middot; **[{it['titre']}]({it['lien']})** — *{it['source']}*\n"
            if it['resume']:
                md_content += f"  > 💡 `{it['resume']}`\n"
    else:
        md_content += "*Aucune dépêche récente capturée dans ce cycle.*\n"

    md_content += "\n---\n\n## 🌐 3. Géopolitique Mondiale & Dynamiques d'Appareil\n\n"
    items_geo = data["piliers"]["geopolitique_monde"]
    if items_geo:
        for it in items_geo:
            md_content += f"- ⏱️ `{it['horodatage_capture']}` &middot; **[{it['titre']}]({it['lien']})** — *{it['source']}*\n"
            if it['resume']:
                md_content += f"  > 💡 `{it['resume']}`\n"
    else:
        md_content += "*Aucune dépêche récente capturée dans ce cycle.*\n"

    md_content += "\n---\n\n## 💻 4. Silicium, Intelligence Artificielle & Ruptures Technologiques\n\n"
    items_tech = data["piliers"]["techno_ia_silicium"]
    if items_tech:
        for it in items_tech:
            md_content += f"- ⏱️ `{it['horodatage_capture']}` &middot; **[{it['titre']}]({it['lien']})** — *{it['source']}*\n"
            if it['resume']:
                md_content += f"  > 💡 `{it['resume']}`\n"
    else:
        md_content += "*Aucune dépêche récente capturée dans ce cycle.*\n"

    md_content += f"""
---

## 🧭 5. Raccordement Synaptique & Diapason de l'Atelier
- Lexique Vivant Auto-Évolutif : `[[Lexique_Vivant_Actualite_Reelle]]`
- Registre Forensique Compressible : `[[Registre_Faits_Actualite_Compressibles]]`
- Carnet d'Intuitions de Christian : `[[Pistes_Actualite]]`
- Coffre Cathédrale : `[[Cathedrale_du_Savoir_Universel]]` (Savoir canonique complémentaire)
"""

    try:
        with open(SYNTHESE_MD, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ [ACTUALITÉ] Note de synthèse mise à jour avec succès : {SYNTHESE_MD.name}")
    except Exception as e:
        print(f"⚠️ Erreur écriture {SYNTHESE_MD} : {e}")


if __name__ == "__main__":
    print("==========================================================================")
    print("   🌍 ALIX SENTINELLE ACTUALITÉ — VRAIE BOULE DE NEIGE SÉMANTIQUE ❄️⏱️")
    print("==========================================================================")
    res = executer_veille_complete()
    print(f"📊 Moissonnage terminé : {res['stats']['total_depeches']} dépêches | +{res['stats']['termes_decouverts']} nouvelles entités capturées en {res['stats']['duree_sec']}s")
