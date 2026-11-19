# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : SONDE D'ACTUALITÉ DATÉE & RÉSUMÉS PAR TITRE (LOI PSI-21 V4)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Empêche l'amnésie stochastique et le décalage temporel des modèles de langage.
- Interroge à cadence frugale (1 fois par heure) les manchettes réelles :
  flux RSS directs (Le Devoir, Radio-Canada Politique/Manchettes/Techno) +
  flux thématiques Google News (fr-CA).
- Pour chaque titre choisi, extrait le chapô/description réel et génère un
  court résumé synthétique (1 à 2 phrases claires) selon le titre choisi.
- Enregistre le condensé horodaté dans `Present/actualite/dernieres_nouvelles.json`
  et met à jour `Present/actualite/Synthese_Actualite_du_Jour.md`.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import html
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

VAULT_DIR = VAULT_DIR
PRESENT_ACTUALITE = VAULT_DIR / "Present" / "actualite"
FICHIER_NOUVELLES = PRESENT_ACTUALITE / "dernieres_nouvelles.json"
SYNTHESE_MD = PRESENT_ACTUALITE / "Synthese_Actualite_du_Jour.md"

COOLDOWN_ACTUALITE_SEC = 3600.0  # 1 heure entre chaque sonde RSS
DERNIERE_SONDE_TS = 0.0
SONDE_EN_COURS = False

FLUX_DIRECTS = [
    {
        "nom": "Le Devoir",
        "url": "https://www.ledevoir.com/rss/manchettes.xml",
        "theme": "Québec & Manchettes",
        "maxi": 2,
    },
    {
        "nom": "Radio-Canada Politique",
        "url": "https://ici.radio-canada.ca/rss/4175",
        "theme": "Politique Québec & Canada",
        "maxi": 2,
    },
    {
        "nom": "Radio-Canada Techno & Science",
        "url": "https://ici.radio-canada.ca/rss/4169",
        "theme": "Technologie, IA & Énergie",
        "maxi": 1,
    },
]

THEMES_GNEWS = [
    "politique québec assemblée nationale",
    "énergie hydro québec silicium technologie",
]


def _nettoyer_html(texte_brut: str) -> str:
    if not texte_brut:
        return ""
    sans_tags = re.sub(r"<[^>]+>", " ", texte_brut)
    decode = html.unescape(sans_tags)
    return " ".join(decode.split()).strip()


def _couper_phrase_complete(texte: str, max_len: int = 280) -> str:
    texte = re.sub(r"\s*(?:Entrevue avec|Explications de|Analyse de|Reportage de|Comment interpr).*$", "", texte, flags=re.IGNORECASE).strip()
    if len(texte) <= max_len:
        return texte
    tronque = texte[:max_len]
    for sep in (". ", "! ", "? "):
        idx = tronque.rfind(sep)
        if idx > 80:
            return tronque[: idx + 1].strip()
    return tronque.rsplit(" ", 1)[0].strip() + "…"


def _generer_petit_resume_selon_titre(titre: str, description_rss: str, source: str, theme: str) -> str:
    """
    Construit un court résumé (1 à 2 phrases complètes, sans répétition) propre au titre choisi :
    - Si le flux RSS (Le Devoir, Radio-Canada) fournit déjà un vrai chapô journalistique distinct
      du titre, on le nettoie et on le synthétise proprement sans doublon.
    - Si le flux RSS (Google News) ne fournit que le titre, le modèle local rédige un court
      résumé de contexte (1 à 2 phrases) selon le titre choisi.
    """
    titre_net = re.sub(r"\s+-\s+[^-]+$", "", titre).strip()
    desc_net = _nettoyer_html(description_rss)

    # Si Google News répète simplement le titre dans <description>, on l'ignore comme chapô brut
    if desc_net and (
        desc_net.lower().startswith(titre_net[:35].lower())
        or len(desc_net) < 25
    ):
        desc_distincte = ""
    else:
        desc_distincte = _couper_phrase_complete(desc_net, max_len=280)

    # Si on a déjà un chapô journalistique riche et complet (>= 90 car.), il est déjà optimal et factuel
    if len(desc_distincte) >= 90:
        return desc_distincte

    # Sinon (chapô très court ou Google News sans chapô), on demande au modèle local un résumé de 1-2 phrases
    try:
        contexte_rss = f"\nPrécision du flux : {desc_distincte}" if desc_distincte else ""
        prompt = (
            f"<|im_start|>system\n"
            f"Tu es Alix, la Sonde d'Actualité de Christian Duguay. "
            f"À partir du titre d'actualité choisi (et de la précision du flux s'il y en a une), "
            f"rédige UN PETIT RÉSUMÉ de 1 à 2 phrases complètes et claires en français qui résume "
            f"l'enjeu de cette nouvelle sans répéter mot à mot le titre et sans inventer de chiffres.\n"
            f"<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Titre choisi : {titre_net} (Source : {source} | Thème : {theme}){contexte_rss}\n"
            f"Petit résumé en 1 à 2 phrases :\n"
            f"<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        req_body = json.dumps({
            "model": "qwen2.5:3b",
            "raw": True,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "24h",
            "options": {"temperature": 0.35, "num_predict": 110, "stop": ["<|im_end|>", "\n\n"]},
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                d_llm = json.loads(resp.read().decode("utf-8"))
                cand = " ".join(d_llm.get("response", "").strip().split())
                cand = re.sub(r"⟦.*?⟧", "", cand).strip().strip('"«»')
                if len(cand) >= 35:
                    return _couper_phrase_complete(cand, max_len=280)
    except Exception:
        pass

    if desc_distincte:
        return desc_distincte
    return f"Suivi dans {source} ({theme}) autour de : {titre_net}."


def parser_flux_direct(nom_source: str, url: str, theme: str, maxi: int = 2) -> List[Dict[str, str]]:
    """Extrait les manchettes et leur chapô depuis un flux RSS direct (Le Devoir, Radio-Canada)."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AlixSonde/2.0"},
    )
    manchettes: List[Dict[str, str]] = []
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            for item in root.iter("item"):
                titre = _nettoyer_html(item.findtext("title", ""))
                desc = _nettoyer_html(item.findtext("description", ""))
                pub_date = (item.findtext("pubDate", "") or "").strip()
                lien = (item.findtext("link", "") or "").strip()
                if titre:
                    manchettes.append({
                        "titre": titre,
                        "source": nom_source,
                        "date_publication": pub_date,
                        "theme": theme,
                        "description_rss": desc,
                        "lien": lien,
                    })
                if len(manchettes) >= maxi:
                    break
    except Exception:
        pass
    return manchettes


def parser_flux_gnews(sujet: str, maxi: int = 2) -> List[Dict[str, str]]:
    """Extrait les manchettes datées depuis Google News RSS."""
    q = urllib.parse.quote(f"{sujet} when:2d")
    url = f"https://news.google.com/rss/search?q={q}&hl=fr-CA&gl=CA&ceid=CA:fr"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AlixSonde/2.0"},
    )
    manchettes: List[Dict[str, str]] = []
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            for item in root.iter("item"):
                titre = _nettoyer_html(item.findtext("title", ""))
                desc = _nettoyer_html(item.findtext("description", ""))
                src = item.find("source")
                source_nom = src.text.strip() if (src is not None and src.text) else "Presse QC/CA"
                pub_date = (item.findtext("pubDate", "") or "").strip()
                if titre:
                    manchettes.append({
                        "titre": titre,
                        "source": source_nom,
                        "date_publication": pub_date,
                        "theme": sujet,
                        "description_rss": desc,
                    })
                if len(manchettes) >= maxi:
                    break
    except Exception:
        pass
    return manchettes


def worker_sonde_actualite():
    """Tâche de fond asynchrone qui télécharge l'actualité et génère un petit résumé pour chaque titre choisi."""
    global DERNIERE_SONDE_TS, SONDE_EN_COURS
    try:
        SONDE_EN_COURS = True
        brutes: List[Dict[str, str]] = []

        # 1. Flux directs avec chapôs complets (Le Devoir, Radio-Canada)
        for fd in FLUX_DIRECTS:
            brutes.extend(parser_flux_direct(fd["nom"], fd["url"], fd["theme"], maxi=fd["maxi"]))

        # 2. Flux thématiques Google News (Québec, Assemblée nationale, Hydro-Québec, Silicium)
        for th in THEMES_GNEWS:
            brutes.extend(parser_flux_gnews(th, maxi=2))

        # Déduplication par préfixe de titre et sélection des 5 titres les plus pertinents
        choisies: List[Dict[str, str]] = []
        titres_vus = set()
        for it in brutes:
            cle = re.sub(r"[^a-z0-9]", "", it["titre"].lower())[:40]
            if not cle or cle in titres_vus:
                continue
            titres_vus.add(cle)
            resume_court = _generer_petit_resume_selon_titre(
                it["titre"],
                it.get("description_rss", ""),
                it.get("source", "Presse"),
                it.get("theme", "Actualité"),
            )
            choisies.append({
                "titre": it["titre"],
                "source": it.get("source", "Presse"),
                "date_publication": it.get("date_publication", ""),
                "theme": it.get("theme", ""),
                "resume": resume_court,
            })
            if len(choisies) >= 5:
                break

        if choisies:
            PRESENT_ACTUALITE.mkdir(parents=True, exist_ok=True)
            now_iso = datetime.now().isoformat()
            now_lisible = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            donnees = {
                "horodatage": now_iso,
                "date_lisible": now_lisible,
                "total_manchettes": len(choisies),
                "manchettes": choisies,
            }
            with open(FICHIER_NOUVELLES, "w", encoding="utf-8") as f:
                json.dump(donnees, f, indent=2, ensure_ascii=False)

            # Mise à jour de la note Markdown d'actualité dans le coffre
            lignes_md = [
                "---",
                f'titre: "Synthèse de l\'Actualité par Titre — {now_lisible}"',
                f'date: "{now_lisible}"',
                "tags:",
                "  - actualite",
                "  - sonde_present",
                "---",
                "",
                f"# 📰 Synthèse de l'Actualité ({now_lisible})",
                "",
            ]
            for idx, m in enumerate(choisies, 1):
                lignes_md.append(f"### {idx}. {m['titre']} *({m['source']})*")
                lignes_md.append(f"> {m['resume']}\n")
            try:
                SYNTHESE_MD.write_text("\n".join(lignes_md), encoding="utf-8")
            except Exception:
                pass

            DERNIERE_SONDE_TS = time.time()
    except Exception:
        pass
    finally:
        SONDE_EN_COURS = False


def executer_capacite(contexte: Dict[str, Any] = None) -> Dict[str, Any]:
    """Point d'entrée exécuté à chaque cycle du Démon."""
    global SONDE_EN_COURS, DERNIERE_SONDE_TS
    t0 = time.perf_counter()
    forcer = bool((contexte or {}).get("forcer", False))

    maintenant = time.time()
    temps_ecoule = maintenant - DERNIERE_SONDE_TS

    if SONDE_EN_COURS:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "action": "SONDE_EN_COURS_ARRIERE_PLAN",
        }

    if forcer or temps_ecoule >= COOLDOWN_ACTUALITE_SEC:
        th = threading.Thread(target=worker_sonde_actualite, daemon=True)
        th.start()
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "action": "LANCEMENT_SONDE_ACTUALITE",
            "themes": THEMES_GNEWS,
        }
    else:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        temps_restant_min = round((COOLDOWN_ACTUALITE_SEC - temps_ecoule) / 60, 1)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "action": "VEILLE_NOMINALE_ACTUALITE",
            "prochaine_sonde_dans_min": temps_restant_min,
        }


if __name__ == "__main__":
    worker_sonde_actualite()
    if FICHIER_NOUVELLES.exists():
        print(FICHIER_NOUVELLES.read_text(encoding="utf-8"))
