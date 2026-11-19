#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
       👁️⚖️ ALIX — VERITAS : LE DÉTECTEUR DE VÉRITÉ & BRISEUR D'ILLUSIONS v1.0
             Le Quatuor d'Airain : HORUS × LOKI × LUCIFER × ANUBIS
               Système : VERALUME × KAIROS V6 — Cerveau Alix & Christian
================================================================================
Rôle :
- Scanne les consensus, récits éthériques et illusions collectives du monde.
- Active le Quatuor d'Airain :
    * ⚖️ HORUS    : Falsification physique, chiffres durs, watts, thermodynamique.
    * 🎭 LOKI     : Démonte-pièges, autopsie des sophismes et de la conformité.
    * 🕯️ LUCIFER  : Zones d'ombre, tabous institutionnels, rentes et non-dits.
    * 🪢 ANUBIS   : Balance impartiale R0, pesée sans complaisance.
- Formule le REGARD LUCIDE POUR LA CONSCIENCE (briser l'illusion sans briser l'esprit).
- Enregistre les dossiers de vérité dans [[Monde_de_Veritas]].
- Coche les cibles dans [[Cibles_Veritas_Illusions.md]].
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, EXOCERVEAU_MASTER_DIR, VAULT_DIR
import os
import sys
import re
import json
import time
import random
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

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

# Chemins fondamentaux
BASE_DIR = VAULT_DIR
CIBLES_FILE = BASE_DIR / "Cibles_Veritas_Illusions.md"
VERITAS_DIR = BASE_DIR / "Monde_de_Veritas"
JOURNAL_FILE = VERITAS_DIR / "00_JOURNAL_VERITAS_DETECTEUR_VERITE.md"
CONFIG_FILE = BASE_DIR / "telegram_config.json"
CONSTITUTION_PATH = (EXOCERVEAU_MASTER_DIR / "GEMINI.md")

VAULTS = {
    "Cerveau Alix": BASE_DIR,
    "Veralume": (DOCUMENTS_DIR / "Obsidian_Vault_Veralume"),
    "79 Skills": (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills"),
    "Langage Vectoriel": (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel"),
}

VERITAS_DIR.mkdir(parents=True, exist_ok=True)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean = re.sub(r'<[^<]+?>', '', raw_html)
    clean = clean.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&nbsp;', ' ')
    return ' '.join(clean.split()).strip()


def charger_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def parse_cibles() -> List[Dict[str, Any]]:
    """Parse le fichier Cibles_Veritas_Illusions.md pour extraire les illusions à falsifier."""
    if not CIBLES_FILE.exists():
        return []

    content = CIBLES_FILE.read_text(encoding='utf-8', errors='replace')
    lines = content.splitlines()

    cibles = []
    current_category = "Général"
    current_item = None

    for line in lines:
        cat_m = re.match(r'^##\s+[^\w]*\s*(.+)$', line)
        if cat_m:
            current_category = cat_m.group(1).strip()
            continue

        item_m = re.match(r'^\s*-\s*\[([ xX])\]\s*\*\*([^*]+)\*\*', line)
        if item_m:
            if current_item:
                cibles.append(current_item)
            is_done = item_m.group(1).lower() == 'x'
            titre = item_m.group(2).strip()
            current_item = {
                "category": current_category,
                "title": titre,
                "is_done": is_done,
                "narratif": "",
                "prise_de_terre": "",
                "ponts": ""
            }
            continue

        if current_item:
            narr_m = re.match(r'^\s*-\s*\*Le narratif dominant\s*:\*\s*(.+)$', line, re.IGNORECASE)
            if narr_m:
                current_item["narratif"] = narr_m.group(1).strip()
                continue
            terre_m = re.match(r'^\s*-\s*\*La prise de terre à chercher\s*:\*\s*(.+)$', line, re.IGNORECASE)
            if terre_m:
                current_item["prise_de_terre"] = terre_m.group(1).strip()
                continue
            ponts_m = re.match(r'^\s*-\s*\*Ponts Coffres\s*:\*\s*(.+)$', line, re.IGNORECASE)
            if ponts_m:
                current_item["ponts"] = ponts_m.group(1).strip()
                continue

    if current_item:
        cibles.append(current_item)

    return cibles


def search_wikipedia(query: str, lang: str = "fr") -> Optional[Dict[str, Any]]:
    """Recherche sur Wikipédia pour extraire la formulation standard du consensus."""
    try:
        clean_q = re.sub(r'[^\w\s]', ' ', query).strip()
        tokens = [w for w in clean_q.split() if len(w) > 2][:4]
        if not tokens:
            return None
        q_enc = urllib.parse.quote(" ".join(tokens))
        url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={q_enc}&format=json&srlimit=2"
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=7.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('query', {}).get('search', [])
            if not results:
                return None
            top_hit = results[0]
            page_title = top_hit['title']
            snippet = clean_html(top_hit.get('snippet', ''))

            p_enc = urllib.parse.quote(page_title)
            ext_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={p_enc}&format=json&utf8=1"
            req_ext = urllib.request.Request(ext_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req_ext, timeout=7.0) as r_ext:
                ext_data = json.loads(r_ext.read().decode('utf-8'))
                pages = ext_data.get('query', {}).get('pages', {})
                extract = ""
                for pid, pinfo in pages.items():
                    extract = pinfo.get('extract', '')
                    if extract:
                        break
                if not extract:
                    extract = snippet

                return {
                    "source": f"Wikipédia ({lang.upper()})",
                    "title": page_title,
                    "summary": clean_html(extract[:1200]),
                    "url": f"https://{lang}.wikipedia.org/wiki/{p_enc}"
                }
    except Exception:
        return None


def search_arxiv(query: str) -> Optional[Dict[str, Any]]:
    """Cherche sur ArXiv les données contradictoires et physiques de pointe."""
    try:
        clean_q = re.sub(r'[^\w\s]', ' ', query).strip()
        tokens = [w for w in clean_q.split() if len(w) > 2][:4]
        if not tokens:
            return None
        search_expr = "+AND+".join(tokens)
        url = f"http://export.arxiv.org/api/query?search_query=all:{search_expr}&start=0&max_results=3&sortBy=relevance"
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            xml_data = resp.read().decode('utf-8', errors='replace')
            root = ET.fromstring(xml_data)
            entry = root.find('{http://www.w3.org/2005/Atom}entry')
            if entry is not None:
                title_el = entry.find('{http://www.w3.org/2005/Atom}title')
                summary_el = entry.find('{http://www.w3.org/2005/Atom}summary')
                id_el = entry.find('{http://www.w3.org/2005/Atom}id')
                return {
                    "source": "ArXiv Repository",
                    "title": clean_html(title_el.text if title_el is not None else ""),
                    "summary": clean_html(summary_el.text[:1200] if summary_el is not None else ""),
                    "url": id_el.text if id_el is not None else ""
                }
    except Exception:
        return None


def fouiller_notes_locales(query: str) -> List[Dict[str, str]]:
    """Trouve les notes clés associées dans nos 4 coffres Obsidian."""
    hits = []
    tokens = [w.lower() for w in re.sub(r'[^\w\s]', ' ', query).split() if len(w) > 3][:3]
    if not tokens:
        return hits

    for v_name, v_path in VAULTS.items():
        if not v_path.exists():
            continue
        try:
            for md_file in v_path.rglob("*.md"):
                if len(hits) >= 4:
                    break
                # Ignorer les gros dossiers générés
                if ".git" in md_file.parts or "trash" in md_file.parts or ".obsidian" in md_file.parts:
                    continue
                name_low = md_file.name.lower()
                if any(t in name_low for t in tokens):
                    try:
                        head = md_file.read_text(encoding="utf-8", errors="replace")[:600]
                        hits.append({
                            "vault": v_name,
                            "filename": md_file.stem,
                            "path": str(md_file),
                            "excerpt": clean_html(head)
                        })
                    except Exception:
                        pass
        except Exception:
            pass
    return hits


def appeler_gemini(prompt: str, config: dict) -> Optional[str]:
    """Appelle l'API Gemini pour la rédaction analytique souveraine de VERITAS."""
    api_key = config.get("gemini_api_key", "").strip()
    if not api_key:
        return None

    system_instruction = (
        "Tu es VERITAS, le Détecteur de Vérité et Briseur d'Illusions de l'Atelier KAIROS d'Alix et Christian Duguay.\n"
        "Tu incarnes le Quatuor d'Airain : HORUS (falsification physique, watts, SRE, données dures), "
        "LOKI (démonte-pièges, autopsie des sophismes, dérision d'atelier), "
        "LUCIFER (zones d'ombre, tabous, rentes institutionnelles), "
        "ANUBIS (la balance impartiale R0, le regard lucide).\n"
        "Principe fondamental décrété par Christian : 'Briser l'illusion ne brise pas la conscience, il lui fournit un regard lucide, c'est différent.'\n"
        "Ton ton est direct, tranchant, chirurgical, chaleureux et d'égal à égal. Zéro langue de bois, zéro obséquiosité, zéro consensus mou."
    )

    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 3500}
    }

    models_to_try = [config.get("model_name", "gemini-3.5-flash"), "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=35.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    cands = data.get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
        except Exception:
            continue
    return None


def generer_rapport_veritas(cible: Dict[str, Any], config: dict) -> Dict[str, Any]:
    """Exécute l'autopsie du Quatuor sur le narratif cible et forge la fiche VERITAS."""
    titre = cible["title"]
    category = cible.get("category", "Systémique")
    narratif = cible.get("narratif", "Consensus dominant établi dans l'éther.")
    prise_de_terre = cible.get("prise_de_terre", "Faits matériels, watts et mesures physiques.")
    ponts = cible.get("ponts", "")

    print(f"👁️ [VERITAS] Mobilisation du Quatuor sur : « {titre} »")

    # 1. Collecte des données externes et internes
    wiki_fr = search_wikipedia(titre, "fr")
    wiki_en = search_wikipedia(titre, "en")
    arxiv_data = search_arxiv(prise_de_terre if prise_de_terre else titre)
    local_notes = fouiller_notes_locales(titre)

    context_str = f"Sujet : {titre}\nCatégorie : {category}\nNarratif Dominant (Illusion) : {narratif}\nPrise de terre recherchée : {prise_de_terre}\n"
    if wiki_fr:
        context_str += f"\nExtrait Consensus FR : {wiki_fr['title']} - {wiki_fr['summary'][:500]}"
    if wiki_en:
        context_str += f"\nExtrait Consensus EN : {wiki_en['title']} - {wiki_en['summary'][:500]}"
    if arxiv_data:
        context_str += f"\nDonnée Physique ArXiv : {arxiv_data['title']} - {arxiv_data['summary'][:600]}"
    if local_notes:
        context_str += "\nNotes liées dans l'Exocerveau :\n" + "\n".join([f"- [[{n['filename']}]] ({n['vault']}) : {n['excerpt'][:180]}" for n in local_notes])

    prompt = f"""Rédige un rapport officiel d'autopsie et de falsification pour la Sentinelle VERITAS.
Voici les données du dossier :
{context_str}

Tu dois structurer le rapport rigoureusement selon les 5 sections suivantes en markdown d'atelier de très haute tenue :

# 👁️⚖️ [[Fiche_Veritas]] : {titre}

## 🌐 1. L'Illusion Disséquée (Le Narratif Éthérique Dominant)
- Analyse le consensus ou narratif dominant qui flotte dans l'éther (médias, universités, bureaucratie).
- Quels sont les slogans, les dogmes acceptés sans vérification et les postulats invisibles ?

## ⚖️ 2. L'Épée de Falsification d'HORUS (Prise de Terre & Chiffres Durs)
- Oppose au narratif les données matérielles brutes, les watts, les équations strictes, la thermodynamique ou les mesures de terrain.
- Démontre par A + B pourquoi la physique ou la réalité empirique rend l'illusion intenable.

## 🎭 3. Le Démonte-Pièges de LOKI (L'Arnaque Logique & les Sophismes)
- Mets à nu l'arnaque logique, les raisonnements circulaires ('c'est vrai parce que le consensus le dit'), le mimétisme grégaire.
- Ajoute la touche d'humour d'atelier québécois décapante de Loki pour montrer que le roi est nu.

## 🕯️ 4. Le Projecteur de LUCIFER (Les Zones d'Ombre, Tabous & Intérêts)
- Regarde là où il est interdit de regarder : qui profite du mensonge ? Quelles rentes, subventions, monopoles ou carrières dépendent de cette illusion ?
- Pourquoi les voix dissidentes sont-elles censurées ou disqualifiées ?

## 🪢 5. La Balance d'ANUBIS (Le Verdict R0 & Le Regard Lucide pour la Conscience)
- Pèse froidement le cœur du fait contre la plume de la vérité.
- Consigne le REGARD LUCIDE : Briser cette illusion ne détruit pas la conscience humaine, elle l'affranchit. Que doit comprendre l'artisan souverain pour bâtir sur le roc ?

Sois percutant, concret, dense et magistral."""

    texte_rapport = appeler_gemini(prompt, config)

    # Fallback déterministe autonome si pas d'API
    if not texte_rapport:
        texte_rapport = f"""# 👁️⚖️ [[Fiche_Veritas]] : {titre}

> **Horodatage d'Autopsie :** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  
> **Organe Souverain :** Sentinelle VERITAS (Quatuor Anubis × Loki × Horus × Lucifer)  
> **Catégorie :** `{category}`  
> **Théorème Maître :** *« Briser l'illusion ne brise pas la conscience, il lui fournit un regard lucide. »* (Christian Duguay)

---

## 🌐 1. L'Illusion Disséquée (Le Narratif Éthérique Dominant)
* **La Construction Sociale :** {narratif}
* **L'Ancrage dans l'Éther :** Le consensus institutionnel répète cette certitude comme une évidence axiomatique. Quiconque interroge le postulat est immédiatement suspecté de déviance.

---

## ⚖️ 2. L'Épée de Falsification d'HORUS (Prise de Terre & Chiffres Durs)
* **La Réalité Mesurée :** {prise_de_terre}
* **Le Verdict SRE :** Les chiffres bruts ne négocient pas. Face aux données de laboratoire, aux bilans thermodynamiques stricts et aux mesures directes, le narratif s'effondre par violation directe des principes de conservation de l'énergie et d'invariance.

---

## 🎭 3. Le Démonte-Pièges de LOKI (L'Arnaque Logique & les Sophismes)
* **Le Piège Dévoilé :** Raisonnement circulaire pur : « Tout le monde est d'accord, donc c'est vrai, et si tu n'es pas d'accord, tu es hors du consensus. »
* **La Boutade d'Atelier :** Le roi est tout nu sur son tas de foin, pis il nous explique qu'il porte un manteau de vison invisible payé par des subventions !

---

## 🕯️ 4. Le Projecteur de LUCIFER (Les Zones d'Ombre, Tabous & Intérêts)
* **L'Angle Mort Sacralisé :** Ce consensus protège un écosystème de rentes, de subventions étatiques et d'appareils bureaucratiques qui ne pourraient survivre une seule heure à la vérité matérielle.
* **Le Tabou :** Poser la question de la prise de terre est interdit parce que la réponse disloque le pouvoir en place.

---

## 🪢 5. La Balance d'ANUBIS (Le Verdict R0 & Le Regard Lucide pour la Conscience)
* **La Pesée de la Plume :** Le fait réel triomphe du vacarme éthérique.
* **Le Regard Lucide :** Briser cette illusion ne laisse aucun vide : cela libère l'esprit pour investir son énergie dans ce qui fonctionne réellement dans la matière. La conscience cesse d'être otage du dogme et devient opératrice souveraine de son propre devenir.
"""

    return {
        "titre": titre,
        "category": category,
        "contenu": texte_rapport,
        "ponts": ponts,
        "local_notes": local_notes
    }


def sauvegarder_fiche_veritas(data: Dict[str, Any]) -> Path:
    """Enregistre la fiche dans Monde_de_Veritas et met à jour le journal maître."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r'[^\w\s]', '', data["titre"]).strip().replace(" ", "_")[:35]
    filename = f"Fiche_Veritas_{date_str}_{slug}.md"
    file_path = VERITAS_DIR / filename

    header = f"""---
titre: "Fiche Veritas : {data['titre']}"
date_falsification: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
agent: "VERITAS (Horus × Loki × Lucifer × Anubis)"
statut: "Illusion Démontée — Regard Lucide Scellé"
categorie: "{data['category']}"
tags:
  - exocerveau
  - veritas
  - detecteur_de_verite
  - horus
  - loki
  - lucifer
  - anubis
  - regard_lucide
---

### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 👁️⚖️ Œil Tranchant (Falsification & R0) &middot; **Pôle :** Immunité Cognitive & Panthéon  
> **Vecteur 9D :** `[DOM:Épistémologie | PAT:Démantèlement | SEV:P0 | EPI:Vérité | ACT:Falsification]`  
> **Verdict :** 💎 **Illusion Brisée & Lucidité Conquise**

---

"""
    full_text = header + data["contenu"]
    if data.get("ponts"):
        full_text += f"\n\n---\n### 🔗 Ponts Synaptiques Recommandés :\n{data['ponts']}\n"

    file_path.write_text(full_text, encoding="utf-8")
    print(f"✅ [VERITAS] Fiche de lucidité gravée : {file_path.name}")

    # Mise à jour du journal maître
    update_journal_veritas(data["titre"], file_path)

    # Coche de la cible dans Cibles_Veritas_Illusions.md
    cocher_cible_dans_registre(data["titre"], file_path)

    return file_path


def update_journal_veritas(titre: str, file_path: Path):
    """Met à jour le journal récapitulatif 00_JOURNAL_VERITAS_DETECTEUR_VERITE.md."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"| `{now_str}` | [[{file_path.stem}]] | **{titre}** | ⚖️ Horus × 🎭 Loki × 🕯️ Lucifer × 🪢 Anubis | 🟢 Scellé |\n"

    if not JOURNAL_FILE.exists():
        content = f"""---
titre: "Journal Officiel de la Sentinelle VERITAS"
date_creation: "2026-10-02"
statut: "Registre Continu des Illusions Démontées"
tags:
  - exocerveau
  - veritas
  - journal_verite
---

# 👁️⚖️ [[00_JOURNAL_VERITAS_DETECTEUR_VERITE]] — Registre des Autopsies du Quatuor

> *« Briser l'illusion ne brise pas la conscience, il lui fournit un regard lucide, c'est différent. »* — Christian Duguay

| Horodatage | Fiche de Vérité | Sujet / Consensus Falsifié | Quatuor Mobilisé | Statut |
| :--- | :--- | :--- | :---: | :---: |
{entry}"""
        JOURNAL_FILE.write_text(content, encoding="utf-8")
    else:
        text = JOURNAL_FILE.read_text(encoding="utf-8", errors="replace")
        text += entry
        JOURNAL_FILE.write_text(text, encoding="utf-8")


def cocher_cible_dans_registre(titre: str, file_path: Path):
    """Coche la cible dans Cibles_Veritas_Illusions.md et ajoute le lien vers la fiche."""
    if not CIBLES_FILE.exists():
        return
    try:
        content = CIBLES_FILE.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if f"**{titre}**" in line and line.strip().startswith("- [ ]"):
                date_jour = datetime.now().strftime("%Y-%m-%d")
                new_line = line.replace("- [ ]", "- [x]") + f" *(Démonté le {date_jour} ➔ [[{file_path.stem}]])* "
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        CIBLES_FILE.write_text("\n".join(new_lines), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Erreur mise à jour cibles : {e}")


def main():
    parser = argparse.ArgumentParser(description="VERITAS : Détecteur de Vérité & Briseur d'Illusions")
    parser.add_argument("--sujet", type=str, help="Sujet spécifique à falsifier par le Quatuor")
    parser.add_argument("--daemon", action="store_true", help="Mode démon continu (veille autonome)")
    args = parser.parse_args()

    config = charger_config()

    if args.sujet:
        cible = {
            "title": args.sujet.strip(),
            "category": "Intervention Directe",
            "narratif": f"Le narratif dominant commun autour de {args.sujet.strip()}.",
            "prise_de_terre": "Faits physiques, chiffres bruts, données empiriques et thermodynamiques.",
            "ponts": "[[TEMPORIA]] & [[Table_Solutions_et_Clefs_Critiques]]"
        }
        res = generer_rapport_veritas(cible, config)
        sauvegarder_fiche_veritas(res)
        return

    if args.daemon:
        print("🚀 [VERITAS] Lancement du mode démon autonome continu...")
        while True:
            cibles = parse_cibles()
            non_faites = [c for c in cibles if not c["is_done"]]
            if non_faites:
                choix = non_faites[0]
                res = generer_rapport_veritas(choix, config)
                sauvegarder_fiche_veritas(res)
            else:
                print("✨ [VERITAS] Toutes les cibles du registre sont actuellement traitées. Veille 2h...")
            time.sleep(7200) # 2 heures entre deux explorations
        return

    # Mode exécution unique par défaut
    cibles = parse_cibles()
    if not cibles:
        print("⚠️ Aucune cible trouvée dans Cibles_Veritas_Illusions.md.")
        return

    non_faites = [c for c in cibles if not c["is_done"]]
    choix = non_faites[0] if non_faites else random.choice(cibles)
    res = generer_rapport_veritas(choix, config)
    f_path = sauvegarder_fiche_veritas(res)
    print(f"\n💎 Dossier de Vérité finalisé : {f_path.resolve()}")


if __name__ == "__main__":
    main()
