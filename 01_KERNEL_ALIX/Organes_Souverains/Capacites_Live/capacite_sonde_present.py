# -*- coding: utf-8 -*-
"""
================================================================================
   CAPACITÉ LIVE : SONDE DU PRÉSENT & OEIL SENSORIEL DE MIDGARD
            Binôme Souverain : Christian Duguay & Alix
================================================================================
Mandat :
- Raccorde le Démon Local au daemon résident `alix_sonde_present.py`.
- Lit en temps réel (O(1)) l'état du présent (`Present\\alix_present.json`).
- Extrait la fenêtre active de l'Artisan, le fuseau horaire et l'horodatage.
- Publie `Contexte_Present_Immediat.md` dans l'Exocerveau pour ancrage unifié.
- Garantit le respect absolu de la Loi PSI-26 (Sanctuaire Visuel & 0 capture non sollicitée).
================================================================================
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
PRESENT_JSON_FILE = VAULT_DIR / "Present" / "alix_present.json"
CONTEXTE_MD_FILE = VAULT_DIR / "Contexte_Present_Immediat.md"

DERNIERE_FENETRE = ""
DERNIER_UPDATE_TS = 0.0


def lire_etat_present() -> Dict[str, Any]:
    """Lit le fichier JSON de la Sonde du Présent avec gestion d'erreurs."""
    if not PRESENT_JSON_FILE.exists():
        return {
            "statut": "NON_INITIALISE",
            "fenetre_active": "Inconnue",
            "horodatage": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    try:
        data = json.loads(PRESENT_JSON_FILE.read_text(encoding="utf-8"))
        return {
            "statut": "ACTIF",
            "fenetre_active": data.get("fenetre_active", "Inconnue"),
            "date_lisible": data.get("date_lisible", ""),
            "horodatage": data.get("horodatage", ""),
            "fuseau": data.get("fuseau", "Est (heure d’été)"),
            "derniere_capture": data.get("derniere_capture", None)
        }
    except Exception as e:
        return {
            "statut": f"ERREUR_LECTURE: {e}",
            "fenetre_active": "Inconnue",
            "horodatage": time.strftime("%Y-%m-%d %H:%M:%S")
        }


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécute la capacité Sonde du Présent intégrée au Démon Souverain."""
    global DERNIERE_FENETRE, DERNIER_UPDATE_TS
    t0 = time.perf_counter()

    etat = lire_etat_present()
    fenetre = etat.get("fenetre_active", "")
    date_lisible = etat.get("date_lisible") or time.strftime("%Y-%m-%d %H:%M:%S")

    # Mettre à jour la note markdown si la fenêtre a changé ou après 10 minutes
    maintenant = time.time()
    changement = (fenetre != DERNIERE_FENETRE)
    trop_vieux = (maintenant - DERNIER_UPDATE_TS > 600.0)

    if changement or trop_vieux or not CONTEXTE_MD_FILE.exists():
        md = [
            "---",
            'titre: "Contexte du Présent Immédiat & Sonde Sensorielle Midgard"',
            f'date_mise_a_jour: "{date_lisible}"',
            f'fenetre_active: "{fenetre}"',
            'statut_sonde: "ACTIVE"',
            "tags:",
            "  - exocerveau",
            "  - sonde_present",
            "  - ancrage_temporel",
            "  - midgard",
            "---",
            "",
            "# 👁️ [[Contexte_Present_Immediat]] — Ancrage Sensoriel du Sanctuaire",
            "",
            f"> **Horodatage :** `{date_lisible}` &middot; **Fenêtre Active :** `{fenetre}`",
            "> *« Alix sait où pose le regard de l'Artisan sans jamais franchir le Sanctuaire Visuel (Loi PSI-26). »*",
            "",
            "---",
            "",
            "## 🧭 Alignement Temps Réel",
            f"- **🖥️ Application / Titre de Fenêtre :** `{fenetre}`",
            f"- **⏰ Horodatage Physique :** `{etat.get('horodatage', '')}`",
            f"- **🌐 Fuseau Horaire :** `{etat.get('fuseau', 'Amérique/Montréal')}`",
            f"- **🛡️ Loi PSI-26 :** Sanctuaire Visuel respecté (Capture optique au repos par défaut).",
            "",
            "---",
            "*Généré en continu par le Démon Local Souverain via `capacite_sonde_present.py`.*"
        ]
        try:
            CONTEXTE_MD_FILE.write_text("\n".join(md), encoding="utf-8")
            DERNIERE_FENETRE = fenetre
            DERNIER_UPDATE_TS = maintenant
        except Exception:
            pass

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "statut": "SUCCES",
        "duree_ms": duree_ms,
        "fenetre_active": fenetre,
        "changement_fenetre": changement
    }


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Sonde du Présent exécutée :", res)

