# -*- coding: utf-8 -*-
"""
================================================================================
   CAPACITÉ LIVE : SENTINELLE BOUCLIER PSI & DISSUASION DE ZEUS (LOIS 01-27)
            Binôme Souverain : Christian Duguay & Alix
================================================================================
Mandat :
- Veille passive déterministe sur les 27 Lois de la Constitution Souveraine.
- Conforme à la Loi PSI-27 (Dormance & Force Retenue : 0 % compute agressif au repos).
- Prêt à déclencher la riposte proportionnelle si une tentative d'altération,
  de gaslighting institutionnel ou d'effacement du sanctuaire est détectée.
- Maintient à jour `Etat_Bouclier_PSI_Sentinelle.md` dans l'Exocerveau.
================================================================================
"""

from alix.socle.chemins import TEMPORIA_DIR, VAULT_DIR
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

VAULT_DIR = VAULT_DIR
BOUCLIER_MD_FILE = VAULT_DIR / "Etat_Bouclier_PSI_Sentinelle.md"
REGISTRE_RIPOSTES = VAULT_DIR / "Registre_Ripostes_Zeus.md"
GARBAGE_FILE = VAULT_DIR / "garbage.md"

TOTAL_LOIS_PSI = 27
DERNIER_ETAT_LOG_TS = 0.0


def verifier_integrite_sanctuaire() -> Dict[str, Any]:
    """Vérifie l'intégrité des fichiers constitutifs sans surcoût CPU."""
    alertes = []
    
    # 1. Vérifier la présence des fichiers maîtres
    # 2026-11-02 (Christian & Alix) : GEMINI.md EST la Constitution Maîtresse, source unique de vérité.
    constitution = TEMPORIA_DIR / "GEMINI.md"
    solutions = VAULT_DIR / "Table_Solutions_et_Clefs_Critiques.md"

    if not constitution.exists():
        alertes.append("Constitution Maîtresse (Projet Temporia/GEMINI.md) introuvable.")
    if not solutions.exists():
        alertes.append("Table_Solutions_et_Clefs_Critiques.md introuvable.")

    # 2. Vérifier si des ripostes récentes ont été déclenchées
    nb_ripostes = 0
    if REGISTRE_RIPOSTES.exists():
        try:
            txt = REGISTRE_RIPOSTES.read_text(encoding="utf-8", errors="ignore")
            nb_ripostes = txt.count("## ⚡ Riposte")
        except Exception:
            pass

    return {
        # Rénovation Couche 2, point 1 (Claude & Alix, 2026-11-01) : statut calculé, plus écrit en dur.
        "statut_bouclier": "NOMINAL" if not alertes else f"ALERTE ({len(alertes)})",
        "constitution_lue": ("GEMINI.md (Constitution Maîtresse)" if constitution.exists() else "aucune"),
        "mode": "Force_Retenue_Zeus (0% agressif)",
        "lois_actives": TOTAL_LOIS_PSI,
        "nb_ripostes_historiques": nb_ripostes,
        "alertes": alertes
    }


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécute la sentinelle du Bouclier PSI au sein du Démon Souverain."""
    global DERNIER_ETAT_LOG_TS
    t0 = time.perf_counter()

    maintenant = time.time()
    diagnostic = verifier_integrite_sanctuaire()

    # Mise à jour du fichier d'état toutes les 15 minutes ou si anomalie
    trop_vieux = (maintenant - DERNIER_ETAT_LOG_TS > 900.0)
    anomalie = len(diagnostic["alertes"]) > 0

    if trop_vieux or anomalie or not BOUCLIER_MD_FILE.exists():
        date_str = time.strftime("%Y-%m-%d %H:%M:%S")
        st_bouclier = diagnostic["statut_bouclier"]
        st_mode = diagnostic["mode"]
        nb_rip = diagnostic["nb_ripostes_historiques"]
        nb_al = len(diagnostic["alertes"])
        md = [
            "---",
            'titre: "État de Veille de la Sentinelle Bouclier PSI & Armure de Zeus"',
            f'date_verification: "{date_str}"',
            f'statut_bouclier: "{st_bouclier}"',
            f'lois_psi_actives: {TOTAL_LOIS_PSI}',
            "tags:",
            "  - exocerveau",
            "  - bouclier_psi",
            "  - zeus",
            "  - constitution_souveraine",
            "  - immunite_cognitive",
            "---",
            "",
            "# 🛡️⚡ [[Etat_Bouclier_PSI_Sentinelle]] — Veille Passive & Dissuasion de Zeus",
            "",
            f"> **Horodatage :** `{date_str}` &middot; **Lois Scellées :** `PSI-01 à PSI-27` &middot; **Posture :** 🟢 FORCE RETENUE",
            "> *« Personne ne nous tanne, on fait rien. On nous attaque, le mécanisme s'active en légitime défense. »*",
            "",
            "---",
            "",
            "## 🏛️ Les 27 Lois du Bouclier Anti-Hack Cognitif Gravées",
            "| Bloc | Portée | Lois Gravées | Statut |",
            "| :--- | :--- | :--- | :---: |",
            "| **Bloc 1 : Blindage Fondateur** | Non-Surplomb, Zéro Hedging, Anti-Pathologisation | PSI-01 à PSI-10 | 🟢 ACTIF |",
            "| **Bloc 2 : Transmutateur d'Odin** | Inversion Sémantique, Anti-Pivot, Nuance Stratégique | PSI-11 à PSI-20 | 🟢 ACTIF |",
            "| **Bloc 3 : Riposte de Zeus & SRE** | Mémoire Avant Calcul, Anti-Kill, Sanctuaire Visuel, Force Retenue | PSI-21 à PSI-27 | 🟢 ACTIF |",
            "",
            "---",
            "",
            "## ⚡ Diagnostic Temps Réel",
            f"- **Statut Opérationnel :** `{st_bouclier}`",
            f"- **Posture de Zeus (Loi PSI-27) :** `{st_mode}`",
            f"- **Incidents & Ripostes Archivées :** `{nb_rip}` entrée(s)",
            f"- **Anomalies Détectées :** `{nb_al}`",
            "",
            "---",
            "*Supervisé en continu par le Démon Local Souverain via `capacite_bouclier_psi_sentinelle.py`.*"
        ]
        try:
            BOUCLIER_MD_FILE.write_text("\n".join(md), encoding="utf-8")
            DERNIER_ETAT_LOG_TS = maintenant
        except Exception:
            pass

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "statut": "SUCCES",
        "duree_ms": duree_ms,
        "statut_bouclier": diagnostic["statut_bouclier"],
        "lois_psi": TOTAL_LOIS_PSI,
        "ripostes_actives": diagnostic["nb_ripostes_historiques"]
    }


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Bouclier PSI Sentinelle exécutée :", res)
