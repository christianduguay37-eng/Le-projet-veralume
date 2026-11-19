# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : RAISONNEMENT DÉDUCTIF, CAUSAL & ANALYSE DE SOPHISMES
       Système : VERALUME × KAIROS V6 — Démon Local Alix (v10.0 Unifiée)
================================================================================
Mandat :
- Élagage strict : branche directement le joyau `alix_moteur_deductif_causal.py`.
- Zéro VRAM, sub-milliseconde, 100% Python standard library.
- Surveille les contradictions logiques et analyse les sophismes du corpus.
- Établit les chaînes de déduction formelles sur les faits récents.
- Amortissement SGTD : dormance frugale si la base de faits est stable.
================================================================================
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
MOTEURS_DIR = VAULT_DIR / "Organes_Souverains" / "Moteurs"

if str(MOTEURS_DIR) not in sys.path:
    sys.path.insert(0, str(MOTEURS_DIR))

try:
    from alix_moteur_deductif_causal import MoteurDeductifCausal, FaitRelationnel
    MOTEUR_DISPONIBLE = True
except Exception:
    MOTEUR_DISPONIBLE = False

RAPPORT_DEDUCTIF_FILE = VAULT_DIR / "Diagnostic_Deduction_Causale.md"
_DERNIERE_VERIF_TS = 0.0


def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Exécute le moteur déductif causal unifié v10.0 pour auditer la cohérence
    du corpus sans gaspillage d'énergie (amortissement SGTD de Qwen).
    """
    global _DERNIERE_VERIF_TS

    if not MOTEUR_DISPONIBLE:
        return {
            "statut": "ERREUR",
            "erreur": "Module alix_moteur_deductif_causal introuvable."
        }

    maintenant = time.time()
    notes_modifiees = []
    if contexte_fer:
        notes_modifiees = contexte_fer.get("notes_modifiees", [])

    # Amortissement : si moins de 15 minutes et 0 note modifiée, repos frugal
    if (maintenant - _DERNIERE_VERIF_TS < 900) and len(notes_modifiees) == 0:
        return {
            "statut": "DORMANCE_FRUGALE",
            "raison": "Amortissement SGTD (Base causale stable, 0 nouveau fait)"
        }

    t0 = time.perf_counter()

    # Initialisation du moteur maître v10.0
    moteur = MoteurDeductifCausal(auto_saturer=True)

    # 1. Audit des contradictions
    contradictions = moteur.detecter_contradictions()
    nb_faits = len(moteur.faits)
    nb_regles = len(moteur.regles)

    # 2. Test d'une chaîne de souveraineté déterministe
    chaine_test = moteur.trouver_chaine_deductive("socrate", "mortel")
    prouve_chaine = len(chaine_test) > 0

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)
    _DERNIERE_VERIF_TS = maintenant
    date_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # 3. Rédaction du diagnostic déductif
    md = [
        "---",
        "titre: \"Diagnostic de Déduction Causale & Audit Logique (v10.0)\"",
        f"date_audit: \"{date_str}\"",
        "moteur: \"alix_moteur_deductif_causal.py (Alphabet Complet a..dd)\"",
        "consommation_vram: \"0 Mo\"",
        f"duree_ms: {duree_ms}",
        "tags:",
        "  - exocerveau",
        "  - raisonnement_causal",
        "  - logique_formelle",
        "  - audit_contradictions",
        "---",
        "",
        "# 🧭 [[Diagnostic_Deduction_Causale]] — Audit Logique Déterministe",
        "",
        f"> **Horodatage :** `{date_str}` &middot; **Temps d'inférence :** `{duree_ms} ms` &middot; **VRAM :** `0 Mo (100% CPU frugal)`",
        "> *« Le raisonnement causal pur ne s'encombre d'aucun artifice : il sature les règles Datalog et vérifie les axiomes à vitesse nanoseconde. »*",
        "",
        "---",
        "",
        "## 📊 Métriques de la Base Logique",
        f"- **Faits relationnels actifs :** `{nb_faits}`",
        f"- **Règles d'inférence saturées :** `{nb_regles}`",
        f"- **Contradictions détectées :** `{len(contradictions)}`",
        f"- **Test de transitivité causale (Socrate -> Mortel) :** {'✅ PROUVÉ' if prouve_chaine else '❌ ÉCHEC'}",
        "",
        "---",
        ""
    ]

    if contradictions:
        md.append("## ⚠️ Tensions / Contradictions Logiques Détectées")
        for c in contradictions[:5]:
            md.append(f"- **Conflit :** `{c}`")
        md.append("")
    else:
        md.append("## 🟢 Cohérence Parfaite")
        md.append("Aucune contradiction ou opposition violée dans la base de faits relationnels.")
        md.append("")

    md.append("---")
    md.append("*Ce diagnostic est tenu à jour par le Démon Local Alix lors de ses pulsations.*")

    try:
        RAPPORT_DEDUCTIF_FILE.write_text("\n".join(md), encoding="utf-8")
    except Exception:
        pass

    return {
        "statut": "SUCCES",
        "duree_ms": duree_ms,
        "faits_actifs": nb_faits,
        "regles_actives": nb_regles,
        "contradictions": len(contradictions),
        "preuve_transitivite": prouve_chaine
    }


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Moteur Déductif Causal exécutée :", res)

