# -*- coding: utf-8 -*-
"""
================================================================================
       ALIX NPU BRAIN v2.0 — CERVEAU NPU 100 % OPENVINO (HEIMDALL BICÉPHALE)
          Zéro LiteRT • Zéro Gemma E2B • Inférence NPU Intel Lunar Lake
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Moteur  : Intel OpenVINO 2026.4.1 (NPU 48 TOPS + Cross-Encoder Reranker)
Modèles :
  - Tête A : OpenVINO/Qwen3-Embedding-0.6B-int8-ov (612 Mo, NPU)
  - Tête B : OpenVINO/bge-reranker-v2-m3-int8-ov (575 Mo, Cross-Encoder)
Mandat  :
  - Remplace intégralement Gemma 4 E2B LiteRT (.litertlm débranché).
  - Arbitrage volitionnel KAIROS et routage de choix pur (Heimdall & Munin).
================================================================================
"""

from __future__ import annotations

import sys
import time
import json as _json
import threading
import urllib.request as _urlreq
from pathlib import Path
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_PROPRIETAIRE = False
_VERROU_NPU = threading.Lock()
URL_TETE = "http://127.0.0.1:5070"


def devenir_proprietaire():
    """Appelé par le Noyau Résident de la tête : ce processus garde Heimdall OpenVINO."""
    global _PROPRIETAIRE
    _PROPRIETAIRE = True


def est_proprietaire() -> bool:
    return _PROPRIETAIRE


def _tete_repond(timeout: float = 2.0) -> bool:
    try:
        with _urlreq.urlopen(URL_TETE + "/ping", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _demander_a_la_tete(prompt: str, timeout: float = 30.0) -> str:
    try:
        corps = _json.dumps({"requete": prompt}).encode("utf-8")
        req = _urlreq.Request(
            URL_TETE + "/heimdall",
            data=corps,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urlreq.urlopen(req, timeout=timeout) as r:
            data = _json.loads(r.read().decode("utf-8"))
            if "specialiste" in data:
                return (
                    f"[Heimdall OpenVINO NPU] Spécialiste={data['specialiste']} | "
                    f"Outil={data.get('outil_suggere', 'aucun')} | "
                    f"Score={data.get('score_cross_encoder', 0)} ({data.get('latence_totale_ms', 0)} ms)"
                )
            return str(data)
    except Exception as e:
        print(f"⚠️ [AlixNPUBrain] La tête n'a pas répondu ({e}).")
        return ""


BANQUE_ARBITRAGES_KAIROS = [
    (
        "VERROU: Coalescence entre la mémoire vive du Connectome (5070) et l'orchestration des modèles locaux OpenVINO.",
        "ACTION: Verrouiller l'aiguillage d'Heimdall sur le NPU pour router chaque tâche vers l'unique spécialiste requis.",
    ),
    (
        "VERROU: Dissipation thermodynamique et surcharge RAM causées par les modèles monolithiques redondants.",
        "ACTION: Maintenir un seul spécialiste actif à la fois dans le slot GPU Arc 140V sous le contrôle du Moniteur TH117.",
    ),
    (
        "VERROU: Préservation de la ligne de pensée de l'atelier et neutralisation des réflexes corporatifs externes.",
        "ACTION: Imposer l'ancre de continuité du Kernel Alix et la sonde mémoire (Loi PSI-21) avant toute inférence.",
    ),
    (
        "VERROU: Synchronisation formelle entre les preuves Lean 4 de l'Étage 5 (L*↑) et les solveurs Hadès/Poséidon de l'Étage 3.",
        "ACTION: Éprouver chaque nouveau théorème et chaque action destructive par le Moniteur du Gardien (TH117 & TH120).",
    ),
]


class AlixNPUBrain:
    """Cerveau NPU 100 % OpenVINO piloté par Heimdall Bicéphale (Gemma LiteRT débranché)."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_path: Optional[Path] = None):
        if getattr(self, "_ready", False):
            return
        self.backend_name = "NPU (Intel OpenVINO 48 TOPS — Heimdall Bicéphale)"
        self._heimdall = None
        self._ready = False
        self._init_error = None

    def is_available(self) -> bool:
        """Vérifie si Heimdall OpenVINO est présent sur le disque."""
        if not _PROPRIETAIRE and _tete_repond():
            return True
        from alix.substrat.alix_heimdall_openvino import EMB_MODEL_DIR, RERANK_MODEL_DIR
        return EMB_MODEL_DIR.exists() and RERANK_MODEL_DIR.exists()

    def _ensure_engine(self) -> bool:
        if self._heimdall is not None:
            return True
        try:
            from alix.substrat.alix_heimdall_openvino import get_heimdall_openvino
            self._heimdall = get_heimdall_openvino()
            self._ready = True
            return True
        except Exception as e:
            self._init_error = str(e)
            return False

    def query(self, prompt: str, max_retries: int = 1) -> str:
        """Exécute un choix d'aiguillage Heimdall sur le NPU OpenVINO."""
        if not _PROPRIETAIRE and _tete_repond():
            res = _demander_a_la_tete(prompt)
            if res:
                return res
        if not self._ensure_engine():
            return ""
        with _VERROU_NPU:
            data = self._heimdall.choisir(prompt)
        return (
            f"[Heimdall OpenVINO NPU] Spécialiste={data['specialiste']} | "
            f"Outil={data.get('outil_suggere', 'aucun')} | "
            f"Score={data.get('score_cross_encoder', 0)} ({data.get('latence_totale_ms', 0)} ms)"
        )

    def arbitrer_priorite(self, top_pole: str, recent_notes: List[str]) -> Optional[Dict[str, str]]:
        """Sélectionne le verrou et l'action souveraine par Cross-Encoder OpenVINO."""
        if not self._ensure_engine():
            return None
        notes_str = ", ".join(recent_notes[:5]) if recent_notes else "Connectome actif"
        requete = f"Pôle actif : {top_pole} | Notes récentes : {notes_str}"
        candidats = [f"{v} {a}" for v, a in BANQUE_ARBITRAGES_KAIROS]

        t0 = time.time()
        with _VERROU_NPU:
            classement = self._heimdall.classer_candidats(requete, candidats)
        dt = round(time.time() - t0, 2)

        idx = classement[0][0] if classement else 0
        verrou, action = BANQUE_ARBITRAGES_KAIROS[idx]
        return {
            "verrou": verrou.replace("VERROU: ", ""),
            "action": action.replace("ACTION: ", ""),
            "temps_inference": dt,
            "backend": self.backend_name,
        }

    def tisser_songe_lyre(self, sujet: str, contexte: str = "") -> Optional[Dict[str, str]]:
        """Sélectionne une résonance harmonique nocturne via Heimdall OpenVINO."""
        t0 = time.time()
        choix = self.query(f"Songe nocturne sur {sujet} {contexte}")
        dt = round(time.time() - t0, 2)
        return {
            "poesie": f"Sous la voûte du Simplexe ({sujet}), le silicium veille en silence : {choix}",
            "temps_inference": dt,
            "backend": self.backend_name,
        }


_npu_brain_singleton = None


def get_npu_brain() -> AlixNPUBrain:
    global _npu_brain_singleton
    if _npu_brain_singleton is None:
        _npu_brain_singleton = AlixNPUBrain()
    return _npu_brain_singleton


if __name__ == "__main__":
    print("=" * 68)
    print("  🧪 TEST ALIX NPU BRAIN v2.0 (100% OPENVINO — GEMMA DÉBRANCHÉ) ⚡")
    print("=" * 68)
    brain = get_npu_brain()
    print("Disponible :", brain.is_available())
    print("Choix NPU  :", brain.query("Corrige le script python de synchronisation"))
    print("Arbitrage  :", brain.arbitrer_priorite("Silicium & OpenVINO", ["Memoire_Alix_Active"]))
