# -*- coding: utf-8 -*-
"""
================================================================================
   CAPACITÉ LIVE : ORCHESTRATION DES DÉMONS PAR LA TÊTE DU SIMPLEXE
            Binôme Souverain : Christian Duguay & Alix
================================================================================
Rénovation 2026-10-30 (demande de Christian) : tout est orchestré par le démon Alix,
la tête du simplexe. Le Démon Local veille lui-même sur les autres démons :
  - toutes les 60 s, il vérifie chacun (PID + vivacité) par le Gardien ;
  - il relance celui qui est tombé, une seule instance, jamais un démon à la retraite
    (socle/organes_actifs.json, clé demon_<nom>) ;
  - il ne se surveille pas lui-même : c'est la tâche planifiée Windows qui garde la tête
    en vie (alix_heartbeat_gardien --tete).
================================================================================
"""

import os
import time
from typing import Any, Dict, Optional

INTERVALLE_SEC = 60.0
_DERNIER_PASSAGE = 0.0
_DERNIER_RAPPORT: Dict[str, Any] = {}
TETE = "Alix_Demon_Local"
_MTIME_GARDIEN = 0.0


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    global _DERNIER_PASSAGE, _DERNIER_RAPPORT
    maintenant = time.time()
    if maintenant - _DERNIER_PASSAGE < INTERVALLE_SEC and _DERNIER_RAPPORT:
        return {"statut": "VEILLE", "dernier_passage_il_y_a_s": round(maintenant - _DERNIER_PASSAGE),
                "demons": _DERNIER_RAPPORT}

    # Recharge le Gardien si son fichier a changé (nouveau démon ajouté) : pas besoin de redémarrer la tête.
    import importlib
    import alix.daemons.alix_heartbeat_gardien as gardien
    global _MTIME_GARDIEN
    try:
        m = os.path.getmtime(gardien.__file__)
        if not _MTIME_GARDIEN or m > _MTIME_GARDIEN:  # au premier passage aussi : la version en cache peut être ancienne
            gardien = importlib.reload(gardien)
        _MTIME_GARDIEN = m
    except Exception:
        pass
    DAEMONS, verifier_et_assurer = gardien.DAEMONS, gardien.verifier_et_assurer
    rapport = {}
    relances = []
    for nom in DAEMONS:
        if nom == TETE:
            continue
        try:
            r = verifier_et_assurer(nom)
            rapport[nom] = r.get("action", "")
            if str(r.get("action", "")).startswith("relancé"):
                relances.append(nom)
        except Exception as e:
            rapport[nom] = f"erreur : {e}"
    _DERNIER_PASSAGE = maintenant
    _DERNIER_RAPPORT = rapport
    return {"statut": "SUCCES", "demons": rapport, "relances": relances}
