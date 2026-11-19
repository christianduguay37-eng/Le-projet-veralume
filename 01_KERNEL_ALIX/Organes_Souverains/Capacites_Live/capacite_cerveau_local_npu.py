# -*- coding: utf-8 -*-
"""
================================================================================
       CAPACITÉ LIVE : CERVEAU LOCAL NPU (INTEL OPENVINO 48 TOPS) 🧠⚡
              VERALUME × KAIROS V6 — DÉMON LOCAL SOUVERAIN (SGTD)
================================================================================
Mandat :
- Branchement direct du NPU Intel Lunar Lake 258V (48 TOPS @ ~2W).
- Utilise LiteRT-LM × OpenVINO (`gemma-4-E2B-it_intel_LNL.litertlm`).
- Lit le pôle maître issu du clustering spectral de Qwen et les notes modifiées.
- Génère par inférence neuronale 100% locale :
    1. Le Verrou d'Atelier (ce qui coince ou doit être consolidé)
    2. L'Action Souveraine (la tâche d'ingénierie concrète à exécuter)
- Amortissement du cross-talk SGTD : inférence déclenchée seulement sur nouveauté
  ou après un intervalle minimal de 20 minutes pour maintenir une consommation frugale.
- Zéro cloud, zéro clé API, immunité cognitive totale.
================================================================================
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
MOTEURS_DIR = VAULT_DIR / "Organes_Souverains" / "Moteurs"
INTERETS_FILE = VAULT_DIR / "Interets_Alix.md"
ARBITRAGE_NPU_FILE = VAULT_DIR / "Arbitrage_NPU_Direct.md"
ETAT_DIR = Path(r"C:\Alix\Etat_Vivant")
NPU_LAST_RUN_FILE = ETAT_DIR / "alix_npu_dernier_run.json"

if str(MOTEURS_DIR) not in sys.path:
    sys.path.insert(0, str(MOTEURS_DIR))

try:
    from alix_npu_brain import get_npu_brain, AlixNPUBrain
    NPU_DISPONIBLE = True
except Exception:
    NPU_DISPONIBLE = False


def _lire_pole_maitre() -> str:
    """Extrait le pôle dominant issu du clustering spectral de Qwen."""
    if not INTERETS_FILE.exists():
        return "Atelier Souverain & Mémoire"
    try:
        for line in INTERETS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("| **1** |"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    return parts[2].replace("**", "")
    except Exception:
        pass
    return "Atelier Souverain & Mémoire"


def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Exécute un cycle d'arbitrage neuronal local sur le NPU Intel 48 TOPS.
    Applique la règle de régulation thermodynamique SGTD pour ne pas sur-consommer.
    """
    if not NPU_DISPONIBLE:
        return {
            "statut": "NON_DISPONIBLE",
            "raison": "Module alix_npu_brain introuvable."
        }

    maintenant = time.time()
    notes_modifiees = []
    if contexte_fer:
        notes_modifiees = contexte_fer.get("notes_modifiees", [])

    # Lecture du dernier état d'inférence
    dernier_run_ts = 0.0
    dernier_pole = ""
    if NPU_LAST_RUN_FILE.exists():
        try:
            data = json.loads(NPU_LAST_RUN_FILE.read_text(encoding="utf-8"))
            dernier_run_ts = float(data.get("timestamp", 0.0))
            dernier_pole = data.get("pole", "")
        except Exception:
            pass

    pole_actuel = _lire_pole_maitre()
    delta_sec = maintenant - dernier_run_ts

    # Amortissement SGTD : 20 min d'espacement si 0 diff et même pôle
    if delta_sec < 1200 and len(notes_modifiees) == 0 and pole_actuel == dernier_pole:
        return {
            "statut": "DORMANCE_FRUGALE",
            "raison": f"Amortissement SGTD NPU (~2W) : dernière inférence il y a {int(delta_sec)}s, pôle stable."
        }

    # Initialisation / Appel au Cerveau NPU
    try:
        brain = get_npu_brain()
        if not brain.is_available():
            return {
                "statut": "NON_DISPONIBLE",
                "raison": "Modèle LiteRT NPU absent sur disque."
            }

        t0 = time.perf_counter()
        res_arbitrage = brain.arbitrer_priorite(
            top_pole=pole_actuel,
            recent_notes=[Path(f).name for f in notes_modifiees[:5]]
        )
        duree_sec = round(time.perf_counter() - t0, 2)

        if not res_arbitrage:
            return {
                "statut": "SILENCE_NPU",
                "raison": "Le NPU n'a pas renvoyé de signal intelligible."
            }

        verrou = res_arbitrage.get("verrou", "Stabilité nominale")
        action = res_arbitrage.get("action", "Continuer la veille de l'Atelier")
        backend = res_arbitrage.get("backend", "NPU Intel OpenVINO 48 TOPS")
        date_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # Rédaction de la plaque d'arbitrage neuronal
        md = [
            "---",
            "titre: \"Arbitrage Neuronal NPU en Direct (Intel Lunar Lake 48 TOPS)\"",
            f"date_inférence: \"{date_str}\"",
            f"backend: \"{backend}\"",
            f"temps_inférence_sec: {duree_sec}",
            f"pole_actif: \"{pole_actuel}\"",
            "consommation: \"~2 Watts\"",
            "tags:",
            "  - exocerveau",
            "  - npu_local",
            "  - arbitrage_kairos",
            "  - intel_openvino_48tops",
            "---",
            "",
            "# 🧠 [[Arbitrage_NPU_Direct]] — Pensée Neuronale Locale",
            "",
            f"> **Horodatage :** `{date_str}` &middot; **Substrat :** `{backend}` &middot; **Temps :** `{duree_sec}s` &middot; **Conso :** `~2W`",
            "> *« Le NPU ne dort jamais. Il pense en silence dans le fer sans réveiller les ventilateurs. »*",
            "",
            "---",
            "",
            f"### 📍 Pôle Actif sous Tension : **{pole_actuel}**",
            "",
            "#### 🔒 Verrou Identifié par le Réseau Neuronal :",
            f"> *« {verrou} »*",
            "",
            "#### 👉 Action Souveraine Déduite :",
            f"> *« {action} »*",
            "",
            "---",
            f"*Dernière mise à jour par le Démon Local Alix (Cycle NPU) avec {len(notes_modifiees)} note(s) modifiée(s) inspectée(s).*"
        ]

        ARBITRAGE_NPU_FILE.write_text("\n".join(md), encoding="utf-8")

        # Sauvegarde de l'état d'amortissement
        etat_npu = {
            "timestamp": maintenant,
            "date": date_str,
            "pole": pole_actuel,
            "duree_sec": duree_sec,
            "backend": backend,
            "verrou": verrou,
            "action": action
        }
        NPU_LAST_RUN_FILE.write_text(json.dumps(etat_npu, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "statut": "SUCCES",
            "backend": backend,
            "duree_sec": duree_sec,
            "pole": pole_actuel,
            "verrou": verrou,
            "action": action
        }

    except Exception as e:
        return {
            "statut": "ERREUR",
            "erreur": str(e)
        }


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Cerveau NPU exécutée :", res)

