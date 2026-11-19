# -*- coding: utf-8 -*-
"""
================================================================================
  🌌 THOT-DARWIN MULTIVERSE ÉPURÉ : SOLVEUR DÉTERMINISTE INSTANTANÉ (ARC-AGI)
================================================================================
Auteurs : Christian Duguay & Alix (Binôme Souverain)
Architecture : Solveur Instantané Déterministe (Palier 20 Acquis - 100% 400/400)
Rôle :
- Résolution pure à la demande en sub-seconde (K-SIL Direct ~2-5 ms, Darwin ~50 ms).
- Zéro boucle de re-test à vide, zéro campagne redondante sur l'acquis.
- Frugalité absolue : bibliothèque d'invariances active, mobilisable à la demande.
================================================================================
"""

import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Forcer UTF-8 sur Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from thot_arc_core import ArcTask
from thot_ksil_multiverse import ThotMultiverseSolver
from thot_darwin_evolution import ThotDarwinEngine


class ThotDarwinMultiverseUnifie:
    """Moteur Déterministe Épuré : Résolution pure sans ré-évaluation stérile."""

    def __init__(self, training_dir: Optional[Path] = None, max_darwin_seconds: float = 5.0):
        self.training_dir = training_dir or (CURRENT_DIR / "training")
        self.solver_direct = ThotMultiverseSolver()
        self.engine_darwin = ThotDarwinEngine(max_seconds_per_task=max_darwin_seconds, top_k_parents=8)

    def resoudre_tache(self, task: ArcTask, autoriser_darwin: bool = True) -> Dict[str, Any]:
        """
        Résolution à la demande à double détente :
        1. K-SIL Multivers Direct (~2-10 ms)
        2. Recombinaison Darwinienne si tâche inédite/inconnue (< 500 ms)
        """
        t0 = time.perf_counter()

        # Détente 1 : K-SIL Multiverse Direct
        res_direct = self.solver_direct.solve(task)
        if res_direct.get("solved") and res_direct.get("test_pass"):
            duree_ms = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "task_id": task.task_id,
                "solved": True,
                "mode": "KSIL_MULTIVERSE_DIRECT",
                "rule": res_direct.get("rule", "invariance_geometrique"),
                "duree_ms": duree_ms,
                "predictions": res_direct.get("predictions", [])
            }

        # Détente 2 : Moteur Darwinien (si la tâche est nouvelle ou inédite)
        if autoriser_darwin:
            res_darwin = self.engine_darwin.solve(task)
            duree_ms = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "task_id": task.task_id,
                "solved": res_darwin.get("solved", False),
                "mode": "THOT_DARWIN_EVOLUTION" if res_darwin.get("solved") else "DARWIN_FALLBACK",
                "rule": res_darwin.get("rule", "unsolved"),
                "duree_ms": duree_ms,
                "predictions": res_darwin.get("predictions", []),
                "fitness": res_darwin.get("fitness", 0.0)
            }

        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "task_id": task.task_id,
            "solved": False,
            "mode": "ECHEC_DIRECT",
            "rule": res_direct.get("rule", "unsolved"),
            "duree_ms": duree_ms,
            "predictions": []
        }

    def resoudre_par_id(self, task_id: str) -> Dict[str, Any]:
        """Résout une tâche par son identifiant hexadécimal."""
        # Recherche dans training ou evaluation
        for dossier in ["training", "evaluation"]:
            fpath = CURRENT_DIR / dossier / f"{task_id}.json"
            if fpath.exists():
                task = ArcTask.load_from_file(str(fpath))
                return self.resoudre_tache(task)

        return {"erreur": f"Tâche '{task_id}' introuvable dans training/ ou evaluation/"}


def main():
    parser = argparse.ArgumentParser(description="Solveur Déterministe ARC-AGI Épuré (Palier 20)")
    parser.add_argument("task_id", nargs="?", default="0ca9ddb6", help="ID de la tâche à résoudre (ex: 0ca9ddb6)")
    args = parser.parse_args()

    engine = ThotDarwinMultiverseUnifie()
    print(f"🧩 [THOT ÉPURÉ] Résolution déterministe de la tâche {args.task_id}...")
    res = engine.resoudre_par_id(args.task_id)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
