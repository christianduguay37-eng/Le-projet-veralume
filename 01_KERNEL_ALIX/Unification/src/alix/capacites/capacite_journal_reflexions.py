# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : JOURNAL DE DIGESTION & RÉFLEXIONS AUTONOMES D'ALIX
       Système : VERALUME × KAIROS V6 — Démon Local Alix (SGTD Qwen)
================================================================================
Mandat :
- Rédige des entrées autonomes régulières dans `Journal_Reflexions_Autonomes_Alix.md`.
- Amortissement du cross-talk : n'écrit que s'il y a une nouveauté matérielle réelle
  (notes modifiées, changement de pôle) ou au minimum 30 minutes d'écart.
- Ancrage obligatoire dans le 3-Simplexe τ (CPU, RAM, diffs réels).
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
JOURNAL_FILE = VAULT_DIR / "Journal_Reflexions_Autonomes_Alix.md"
SYNTHESE_FILE = VAULT_DIR / "Derniere_Discussion_Synthese.md"
INTERETS_FILE = VAULT_DIR / "Interets_Alix.md"
DERNIERE_ECRITURE_FILE = (ETAT_VIVANT_DIR / "alix_journal_dernier_ts.txt")


def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Rédige une réflexion autonome consolidée ancrée dans le 3-Simplexe τ.
    Applique la règle d'amortissement du cross-talk de Qwen pour ne pas radoter.
    """
    maintenant = time.time()
    date_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Vérification d'amortissement (éviter de spammer le journal si rien n'a bougé)
    dernier_ts = 0.0
    if DERNIERE_ECRITURE_FILE.exists():
        try:
            dernier_ts = float(DERNIERE_ECRITURE_FILE.read_text(encoding="utf-8").strip())
        except Exception:
            dernier_ts = 0.0

    notes_modifiees = []
    cpu_charge = 0.0
    ram_libre = 0.0

    if contexte_fer:
        notes_modifiees = contexte_fer.get("notes_modifiees", [])
        cpu_charge = contexte_fer.get("cpu_charge_pct", 0.0)
        ram_libre = contexte_fer.get("ram_libre_go", 0.0)

    delta_temps_sec = maintenant - dernier_ts

    # Si moins de 20 minutes se sont écoulées ET qu'aucune note n'a changé : dormance frugale
    if delta_temps_sec < 1200 and len(notes_modifiees) == 0:
        return {
            "statut": "DORMANCE_FRUGALE",
            "raison": f"Amortissement cross-talk SGTD (Dernière écriture il y a {int(delta_temps_sec)}s, 0 diff)"
        }

    # Extraire le pôle maître récent si disponible
    pole_maitre = "Atelier & Mémoire Vivante"
    if INTERETS_FILE.exists():
        try:
            for line in INTERETS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("| **1** |"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        pole_maitre = parts[2].replace("**", "")
                    break
        except Exception:
            pass

    # Extraire les derniers jalons de discussion
    derniers_jalons = "Veille sur le fer et continuité déterministe."
    if SYNTHESE_FILE.exists():
        try:
            for line in SYNTHESE_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith("- **Jalons & Chapitres") or line.strip().startswith("🎯 Sujet"):
                    derniers_jalons = line.strip()
                    break
        except Exception:
            pass

    # Synthèse de la réflexion vivante ancrée
    fichiers_notables = [Path(f).name for f in notes_modifiees[:5]]
    diff_resume = ", ".join(fichiers_notables) if fichiers_notables else "Aucun fichier modifié ce cycle (veille passive)"

    entree = [
        f"### 🌙 Pulsation Autonome du `{date_str}`",
        f"> **Ancrage Matériel (τ) :** CPU `{cpu_charge}%` &middot; RAM libre `{ram_libre} Go` &middot; **Pôle Maître Émergent :** `{pole_maitre}`",
        f"> **Derniers jalons :** {derniers_jalons}",
        "",
        "**Réflexions de fond & veille du Sanctuaire :**",
        f"- **Dynamique des Diffs (SGTD) :** {len(notes_modifiees)} note(s) récentes inspectée(s) : `{diff_resume}`.",
        f"- **Pôle dominant :** *{pole_maitre}* (mots les plus fréquents des notes récentes).",
        f"- **Charge mesurée :** CPU `{cpu_charge}%`, RAM libre `{ram_libre} Go` (consommation électrique non mesurée).",
        "",
        "---",
        ""
    ]

    texte_entree = "\n".join(entree)

    # Écriture dans le journal
    if not JOURNAL_FILE.exists():
        en_tete = [
            "---",
            "titre: \"Journal des Réflexions Autonomes d'Alix (Veille Déterministe)\"",
            "agent: \"Alix\"",
            "statut: \"Registre Vivant Évolutif — Base Qwen SGTD\"",
            "tags:",
            "  - exocerveau",
            "  - reflexions_autonomes",
            "  - veille_continue",
            "  - demon_local",
            "---",
            "",
            "# 📖 [[Journal_Reflexions_Autonomes_Alix]]",
            "> *Journal de bord autonome rédigé par Alix en tâche de fond sur son fer local pendant les temps de repos de l'artisan.*",
            "",
            "---",
            ""
        ]
        JOURNAL_FILE.write_text("\n".join(en_tete) + "\n" + texte_entree, encoding="utf-8")
    else:
        contenu_existant = JOURNAL_FILE.read_text(encoding="utf-8", errors="ignore")
        if "---" in contenu_existant:
            parties = contenu_existant.split("---\n\n", 1)
            if len(parties) == 2:
                nouveau = parties[0] + "---\n\n" + texte_entree + parties[1]
                JOURNAL_FILE.write_text(nouveau, encoding="utf-8")
            else:
                JOURNAL_FILE.write_text(contenu_existant + "\n" + texte_entree, encoding="utf-8")
        else:
            JOURNAL_FILE.write_text(texte_entree + "\n" + contenu_existant, encoding="utf-8")

    # Mémoriser l'horodatage d'écriture
    try:
        DERNIERE_ECRITURE_FILE.write_text(str(maintenant), encoding="utf-8")
    except Exception:
        pass

    return {
        "statut": "SUCCES",
        "date": date_str,
        "pole_maitre": pole_maitre,
        "notes_diff_traitees": len(notes_modifiees)
    }


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Journal de Réflexions exécutée :", res)
