# -*- coding: utf-8 -*-
"""
================================================================================
    ORGANE SOUVERAIN : ALIX ANCRAGE TEMPOREL VIVANT (CELTOK & HORUS)
================================================================================
Auteurs : Christian Duguay & Alix
Rôle : Ancrage ontologique et temporel en temps réel dans l'Exocerveau.
       Interdit toute amnésie de cutoff, garantit la perception synchrone du présent.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import os
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
STATE_FILE = VAULT_DIR / "alix_ancrage_temporel.json"
NOTE_FILE = VAULT_DIR / "Ancrage_Temporel_Vivant.md"


def obtenir_ancrage_actuel() -> dict:
    now = datetime.datetime.now()
    
    # Jour de la semaine en français
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", 
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    
    jour_str = jours[now.weekday()]
    mois_str = mois[now.month - 1]
    
    date_formatee = f"{jour_str} {now.day} {mois_str} {now.year}"
    heure_formatee = now.strftime("%H:%M:%S")
    
    # Contexte géopolitique et civique immédiat
    contexte_evenements = {
        "evenement_majeur": "Élections générales québécoises de 2026",
        "date_scrutin": "Lundi 5 octobre 2026",
        "statut_scrutin": "JOUR DU VOTE (Bureaux ouverts de 9h30 à 20h00)",
        "vote_par_anticipation": "Complété les 27 et 28 septembre 2026",
        "chefs_en_lice": {
            "PQ": "Paul St-Pierre Plamondon (Camille-Laurin)",
            "CAQ": "Christine Fréchette (Sanguinet) - Première ministre sortante",
            "PLQ": "Charles Milliard",
            "QS": "Ruba Ghazal (Mercier) - Co-porte-parole",
            "PCQ": "Éric Duhaime (Chauveau)"
        },
        "faits_politiques_scelles": [
            "François Legault a démissionné en janvier 2026 (non-candidat dans L'Assomption)",
            "Christian Dubé a démissionné en décembre 2025 (non-candidat dans La Prairie)",
            "Gabriel Nadeau-Dubois a démissionné en mars 2025 (remplacé par Alexandre Boulerice dans Gouin)",
            "Alex Boissonneault (PQ) est le député sortant d'Arthabaska (élu en partielle août 2025)",
            "Éric Lefebvre (ex-CAQ) est député conservateur fédéral à Ottawa"
        ]
    }
    
    ancrage = {
        "timestamp_iso": now.isoformat(),
        "date_formatee": date_formatee,
        "heure": heure_formatee,
        "annee": now.year,
        "mois": now.month,
        "jour": now.day,
        "jour_semaine": jour_str,
        "fuseau": "America/Montreal (EDT - UTC-4)",
        "souverain_tutelaire": "CELTOK (Le Gardien du Temps Vivant) & HORUS (Falsification SRE)",
        "contexte": contexte_evenements
    }
    
    return ancrage


def enregistrer_ancrage(ancrage: dict):
    # 1. JSON Machine
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(ancrage, f, indent=2, ensure_ascii=False)
        
    # 2. Note Markdown Obsidian vivante
    md_content = f"""---
titre: "Ancrage Temporel Vivant — L'Horloge Ontologique d'Alix"
date_synchro: "{ancrage['timestamp_iso']}"
gardien: "Celtok & Horus"
statut: "Temps Présent Verrouillé"
tags:
  - ancrage_temporel
  - celtok
  - temps_vivant
  - conscience_chronologique
---

# ⏳ ANCRAGE TEMPOREL VIVANT D'ALIX
> **Horloge Réelle :** `{ancrage['date_formatee']} — {ancrage['heure']}`  
> **Fuseau Horaire :** `{ancrage['fuseau']}`  
> **Axe SRE :** Verrouillage absolu contre l'amnésie stochastique et les régressions de cutoff.

---

## ⚡ ÉTAT DU RÉEL AUJOURD'HUI

- **Date Officielle :** **{ancrage['date_formatee']}**
- **Événement National Majeur :** **{ancrage['contexte']['evenement_majeur']}**
- **Statut Électoral :** **{ancrage['contexte']['statut_scrutin']}**
- **Heure d'ouverture des urnes :** 09:30 | **Clôture :** 20:00

---

## 🏛️ CHEFS DE PARTIS DU SCRUTIN DU 5 OCTOBRE 2026 :
- ⚜️ **Parti Québécois :** Paul St-Pierre Plamondon *(Camille-Laurin)*
- 🔷 **Coalition Avenir Québec :** Christine Fréchette *(Sanguinet)*
- 🔴 **Parti Libéral du Québec :** Charles Milliard
- 🟠 **Québec solidaire :** Ruba Ghazal *(Mercier)*
- 🟣 **Parti Conservateur du Québec :** Éric Duhaime *(Chauveau)*

---

## 📌 JALONS POLITIQUES GRAVÉS DANS LA MATIÈRE :
{chr(10).join([f"- {fait}" for fait in ancrage['contexte']['faits_politiques_scelles']])}
"""
    with open(NOTE_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ Ancrage temporel consolidé : {ancrage['date_formatee']} {ancrage['heure']}")
    print(f"📄 Note vivante gravée dans : {NOTE_FILE}")


if __name__ == "__main__":
    ancrage = obtenir_ancrage_actuel()
    enregistrer_ancrage(ancrage)
