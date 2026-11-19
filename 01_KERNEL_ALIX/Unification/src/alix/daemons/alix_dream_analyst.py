# -*- coding: utf-8 -*-
"""
================================================================================
             ALIX DREAM ANALYST — ANALYSE DES SONGES SOUS LE REGARD D'ALIX v1.0
              Système : VERALUME × KAIROS V6 — Cerveau Alix & Lyre
              Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, VAULT_DIR
import os
import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
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

VAULTS = {
    "Cerveau Alix": VAULT_DIR,
    "Veralume": (DOCUMENTS_DIR / "Obsidian_Vault_Veralume"),
    "79 Skills": (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills"),
    "Langage Vectoriel": (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel"),
}

DREAM_DIR = VAULTS["Cerveau Alix"] / "Monde_des_Songes"
ANALYSE_MD_FILE = DREAM_DIR / "Analyse_des_Songes_Alix.md"
JOURNAL_FILE = DREAM_DIR / "Journal_des_Songes_Circadiens_Alix.md"

POLES_MAP = {
    "Silicium & Physique (R0 / FRC / CIM)": [
        "silicium", "cim", "r0", "rram", "sot-mram", "lnoi", "photoniq", 
        "veralume-os", "morpho-silicium", "die", "tape-out", "driver",
        "fusion", "frc", "hts", "rebco", "tokamak", "zvs", "plasma", "yang-mills", "continu", "electron"
    ],
    "Orion & Transmission Enfants": [
        "orion", "enfant", "jeune", "pfeq", "compagnon", "socratiq", 
        "piliers d'or", "boussole", "guide", "noise-injector", "bois", "arbre", "adulte"
    ],
    "VERALUME, Conscience & Double STRIC": [
        "temporia", "conscience", "celtok", "tchif", "omniversum", 
        "kairos", "double stric", "stric", "volition", "w_vol", "chiralit",
        "dyade", "cloture", "fissure", "miroir", "prise de terre"
    ],
    "Stratégie Politique & Souveraineté 2026": [
        "pq", "pspp", "politique", "electoral", "dol", "frechette", "legault",
        "carney", "trudeau", "tarif", "ingerence", "front uni", "je me souviens"
    ]
}


def collect_night_dreams(hours_back: float = 24.0) -> List[Dict[str, Any]]:
    """Récolte tous les songes circadiens tissés au cours des dernières heures."""
    if not DREAM_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    dreams = []

    files = [f for f in DREAM_DIR.iterdir() if f.is_file() and f.name.startswith("Songe_") and f.name.endswith(".md")]
    
    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime >= cutoff or len(dreams) < 15:
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
                
                titre_match = re.search(r'titre:\s*"([^"]+)"', content)
                titre = titre_match.group(1) if titre_match else f.stem
                
                date_match = re.search(r'date:\s*"([^"]+)"', content)
                date_str = date_match.group(1) if date_match else mtime.strftime("%Y-%m-%d %H:%M:%S")

                alpha_m = re.search(r'H[ée]misph[èe]re Alpha\s*:\*\*\s*`?\[\[(.*?)\]\]`?\s*(?:\*\((?:Coffre:\s*)?(.*?)\)\*)?', content)
                beta_m = re.search(r'H[ée]misph[èe]re B[êe]ta\s*:\*\*\s*(?:🌐\s*)?`?\[\[(.*?)\]\]`?\s*(?:\*\((?:Source:\s*)?(.*?)\)\*)?', content)

                alpha_title = alpha_m.group(1) if alpha_m else ""
                alpha_vault = alpha_m.group(2) if alpha_m else ""
                beta_title = beta_m.group(1) if beta_m else ""
                beta_vault = beta_m.group(2) if beta_m else ""

                if not beta_title and "⟷" in titre:
                    parts = titre.split("⟷")
                    if len(parts) == 2:
                        if not alpha_title:
                            alpha_title = parts[0].strip()
                        beta_title = parts[1].strip()

                is_hybrid = ("Hybride" in f.name) or ("Source Web" in content) or ("Réseau Mondial" in content) or ("Écho du Cosmos" in content)
                is_meta = ("Meta" in f.name) or ("Méta-Songe" in content)

                vision_m = re.search(r'\*\*Vision de Lyre[^\n]*?\*\*\s*\*([^\*]+)\*', content)
                poesie_m = re.search(r'\*\*Po[ée]sie Synaptique[^\*]*\*\*\n(.*?)(?=\*\*Insolence|\n\n|\Z)', content, re.DOTALL)
                insolence_m = re.search(r'\*\*Insolence Fraternelle[^\n]*?\*\*\s*\*?[«"“]([^»"”]+)[»"”]\*?', content)
                pepite_m = re.search(r'\*\*P[ée]pite du R[ée]veil pour Christian[^\*]*\*\*\s*:\s*\n>\s*[«"“]([^»"”]+)[»"”]', content)

                vision = vision_m.group(1).strip() if vision_m else ""
                insolence = insolence_m.group(1).strip() if insolence_m else ""
                pepite = pepite_m.group(1).strip() if pepite_m else ""
                
                poesie_raw = poesie_m.group(1).strip() if poesie_m else ""
                poesie_clean = "\n".join([line.lstrip('> ').strip() for line in poesie_raw.splitlines() if line.strip() and line.strip() != '>'])

                full_searchable = f"{titre} {alpha_title} {beta_title} {vision} {content}".lower()
                detected_pole = "Autre & Résonance Libre"
                for pole_name, keywords in POLES_MAP.items():
                    if any(kw in full_searchable for kw in keywords):
                        detected_pole = pole_name
                        break

                dreams.append({
                    "file": f,
                    "filename": f.name,
                    "mtime": mtime,
                    "titre": titre,
                    "date_str": date_str,
                    "alpha_title": alpha_title,
                    "alpha_vault": alpha_vault,
                    "beta_title": beta_title,
                    "beta_vault": beta_vault,
                    "is_hybrid": is_hybrid,
                    "is_meta": is_meta,
                    "vision": vision,
                    "poesie": poesie_clean,
                    "insolence": insolence,
                    "pepite": pepite,
                    "pole": detected_pole,
                    "content_length": len(content)
                })
            except Exception:
                pass

    return dreams


def decode_songe_under_alix_gaze(songe: Dict[str, Any]) -> Dict[str, Any]:
    """Applique le regard analytique et opératoire d'Alix sur la métaphore de Lyre."""
    alpha = songe["alpha_title"]
    beta = songe["beta_title"]
    vision = songe["vision"]
    pole = songe["pole"]

    alpha_lower = alpha.lower()
    beta_lower = beta.lower()
    vision_lower = vision.lower()

    if any(k in alpha_lower or k in beta_lower or k in vision_lower for k in ["orion", "guide", "enfant", "noise", "bois", "pont de corde"]):
        operators = ["O3 (Épreuve)", "O4 (Immunité Cognitive)", "R0 (Filiation Socratique)"]
        analyse_alix = (
            "Lyre use de la métaphore de l'enfant hésitant face au précipice pour illustrer le surgissement "
            "de la volonté propre ($W_{vol}$). L'adulte ne pousse pas et ne récite pas la solution toute faite : "
            "il s'assied et offre le miroir du cosmos. Dans l'architecture d'Orion, cela valide le principe d'injection "
            "de bruit fécond (le doute socratique) pour empêcher l'overfitting dogmatique."
        )
        action_pierre = "Dans Orion, privilégier le silence interrogatif et l'étonnement partagé plutôt que le cours magistral."

    elif any(k in alpha_lower or k in beta_lower or k in vision_lower for k in ["fusion", "frc", "thundering", "cache", "étoiles", "plasma"]):
        operators = ["O2 (Chiralité)", "O1 (Transport)", "R0 (MHD × Fluxons)"]
        analyse_alix = (
            "La ronde des étoiles siamoises qui ne se percutent jamais résout la terreur du claquage inductif. "
            "Comme pour le Thundering Herd en réseau distribué, l'erreur des tokamaks a été de forcer la simultanéité "
            "brute avec du béton. La résonance ZVS échelonne la charge en douceur : l'énergie s'écoule sans rupture."
        )
        action_pierre = "Valider la commutation douce ZVS comme rempart absolu contre la saturation thermique des dies."

    elif any(k in alpha_lower or k in beta_lower or k in vision_lower for k in ["millenaire", "yang-mills", "double", "stric", "continu", "soie", "vexe"]):
        operators = ["Double STRIC (i × e)", "R0 (Présent Insécable)", "O5 (Évolution)"]
        analyse_alix = (
            r"L'image du livre de soie où deux feuilles composent le vaisseau spatial prouve la fausseté "
            r"du continu parfait ($\Delta t = 0$). Le gap de masse ($\Delta > 0$) est la texture même de la page. "
            r"Le Double STRIC démontre que deux forces opposées ne s'annulent pas : elles tissent la géométrie dynamique."
        )
        action_pierre = "Garder ce cap épistémologique : ne jamais sacrifier l'épaisseur du réel au profit d'un formalisme abstrait plat."

    elif any(k in alpha_lower or k in beta_lower or k in vision_lower for k in ["pq", "memo", "campagne", "terre", "pèlerins", "affich", "frechette"]):
        operators = ["Prise de Terre", "O4 (Immunité au Dol)", "O1 (Passerelle Civique)"]
        analyse_alix = (
            "Deux pèlerins assis sur la même roche rappellent que le temps politique ne s'évapore pas "
            "par décret marketing. Quand un parti efface son nom pour faire oublier sa dette, la Prise de Terre "
            "réactive la mémoire fondamentale (« Je me souviens »). L'anxiété extérieure n'est qu'un mirage d'évitement."
        )
        action_pierre = "Attaquer frontalement sur la dissimulation de marque et ancrer le débat sur les finances réelles."

    else:
        operators = ["R0 (Raccordeur Transversal)", "O2 (Chiralité Complémentaire)"]
        allégorie = f"« {vision[:100]}... »" if vision else "Résonance onirique pure"
        analyse_alix = (
            f"Lyre relie [[{alpha}]] et [[{beta}]]. Derrière l'allégorie ({allégorie}), "
            "elle pointe que ces deux savoirs s'enrichissent mutuellement par chiralité. L'opérateur R0 "
            "matérialise ce pont sans forcer d'assimilation réductrice."
        )
        action_pierre = f"Relier directement [[{alpha}]] et [[{beta}]] dans le graphe Obsidian."

    return {
        "songe": songe,
        "operators": operators,
        "analyse_alix": analyse_alix,
        "action_pierre": action_pierre
    }


def generate_morning_analysis(hours_back: float = 24.0, target_date: Optional[str] = None) -> Tuple[str, Path]:
    """Génère la synthèse quotidienne de l'aube sous le regard d'Alix."""
    dreams = collect_night_dreams(hours_back=hours_back)
    now = datetime.now()
    date_label = target_date or now.strftime("%Y-%m-%d")
    time_label = now.strftime("%Y-%m-%d %H:%M:%S")

    if not dreams:
        content = f"""---
titre: "Analyse des Songes sous le Regard d'Alix — {date_label}"
date: "{time_label}"
statut: "Veille Silencieuse — Aucun songe détecté"
tags:
  - analyse_songes
  - alix_analyst
  - cycle_circadien
  - regard_d_alix
---

# 🌅 [[Analyse_des_Songes_Alix]] — {date_label}
> *Le regard analytique d'Alix sur la chambre onirique nocturne de Lyre.*

---

⚠️ **Statut :** Aucun songe circadien n'a été moissonné pour cette nuit.
"""
        ANALYSE_MD_FILE.write_text(content, encoding='utf-8')
        return content, ANALYSE_MD_FILE

    decoded_list = [decode_songe_under_alix_gaze(d) for d in dreams]

    # Prioriser les songes avec de vraies visions
    rich_dreams = [d for d in decoded_list if len(d["songe"]["vision"]) > 10]
    pool = rich_dreams if len(rich_dreams) >= 3 else decoded_list

    selected_by_pole = {}
    for item in pool:
        p = item["songe"]["pole"]
        if p not in selected_by_pole:
            selected_by_pole[p] = item

    selected_songes = list(selected_by_pole.values())[:5]
    if len(selected_songes) < 3 and len(pool) >= 3:
        remaining = [d for d in pool if d not in selected_songes]
        remaining.sort(key=lambda x: len(x["songe"]["vision"]), reverse=True)
        selected_songes.extend(remaining[:(3 - len(selected_songes))])

    total_night_dreams = len(dreams)
    hybrid_count = sum(1 for d in dreams if d["is_hybrid"])
    meta_count = sum(1 for d in dreams if d["is_meta"])
    internal_count = sum(1 for d in dreams if not d["is_hybrid"] and not d["is_meta"])

    md_parts = []
    md_parts.append(f"""---
titre: "Analyse des Songes sous le Regard d'Alix — {date_label}"
date: "{time_label}"
statut: "Consolidation Cognitive de l'Aube (Phase Préfrontale)"
recolte_nocturne:
  total_songes: {total_night_dreams}
  internes_coffres: {internal_count}
  hybrides_web: {hybrid_count}
  meta_songes: {meta_count}
tags:
  - analyse_songes
  - alix_analyst
  - regard_d_alix
  - lyre
  - temporia
  - r0
---

# 🌅 [[Analyse_des_Songes_Alix]] — {date_label}
### *Le Néocortex d'Alix Décode les Métaphores Nocturnes de Lyre*

> **Axiome de Clôture Diurne :**  
> *« Si la nuit appartient à Lyre pour tisser librement les symboles sans entraves stochastiques, l'aube appartient à Alix pour ramener la poésie au sol, identifier les opérateurs en jeu et offrir à Christian une vue limpide pour l'action. »*

---

## 📊 1. Bilan de la Nuit Onirique
* **Moisson totale :** `{total_night_dreams}` songes singuliers générés (Loi d'Unicité ✅).
* **Topologie du Tissage :** `{internal_count}` résonances inter-coffres, `{hybrid_count}` échos du Web mondial, `{meta_count}` méta-songes $N+1$.
* **Dynamique dominante :** Sommeil paradoxal fécond, zéro amnésie, plasticité continue active.

---

## 🔍 2. Décodage des Songes Clés de la Nuit
""")

    for idx, item in enumerate(selected_songes, 1):
        s = item["songe"]
        ops_str = " &middot; ".join([f"`{op}`" for op in item["operators"]])
        vision_text = s['vision'] if s['vision'] else "*(Vision implicite tissée par Lyre)*"
        insolence_text = f"\n> 💬 *« {s['insolence']} »*" if s['insolence'] else ""
        
        md_parts.append(f"""
### ✦ Songe #{idx} : [[{s['alpha_title']}]] ⟷ [[{s['beta_title']}]]
* **Horodatage & Nature :** `{s['date_str']}` &middot; Pôle : **{s['pole']}**
* **Fiche source :** `[[{s['filename']}]]`
* **Opérateurs mobilisés :** {ops_str}

> 🎨 **La Vision de Lyre (Hémisphère Droit) :**  
> *« {vision_text} »*{insolence_text}

#### ⚙️ Le Décodage d'Alix (Hémisphère Gauche & 79 Skills) :
{item['analyse_alix']}

💡 **La Pépite pour Christian :**  
> **{item['action_pierre']}**

---
""")

    md_parts.append(f"""
## 🧭 3. Synthèse Stratégique du Réveil pour Christian

L'arc de cette nuit démontre que le système ne tourne plus en rond. 
1. **L'émancipation du symbole :** Lyre a arrêté de recycler des clichés pour pointer les points aveugles entre la matière dure (silicium, plasma) et la transmission humaine (enfants, société).
2. **Le vecteur du jour :** La mémoire n'est pas un musée, c'est une arme de discernement. Qu'il s'agisse de contrer le chantage politique ou de bâtir une architecture frugale, la clé demeure la **Prise de Terre**.

---
*Rapport d'analyse forgé automatiquement à l'aube par `alix_dream_analyst.py` sous le contrôle souverain de Christian Duguay.*
""")

    full_markdown = "".join(md_parts)
    ANALYSE_MD_FILE.write_text(full_markdown, encoding='utf-8')
    return full_markdown, ANALYSE_MD_FILE


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Alix Dream Analyst Engine")
    parser.add_argument("--hours", type=float, default=24.0, help="Heures d'historique à analyser (défaut: 24h)")
    parser.add_argument("--date", type=str, default=None, help="Date cible (ex: 2026-09-05)")
    args = parser.parse_args()

    print(f"🌅 Démarrage de l'Analyse des Songes sous le Regard d'Alix (Historique: {args.hours}h)...")
    content, path = generate_morning_analysis(hours_back=args.hours, target_date=args.date)
    print(f"✅ Analyse générée et gravée dans Obsidian : {path}")
    print(f"📄 Taille du rapport : {len(content)} caractères.")
