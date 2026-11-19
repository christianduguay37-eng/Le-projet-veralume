# -*- coding: utf-8 -*-
"""
================================================================================
       ALIX NPU BRAIN v1.0 — LE CERVEAU LOCAL BASSE-CONSOMMATION
          Inférence Continue sur Intel Lunar Lake NPU (48 TOPS)
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Moteur  : Google LiteRT-LM × Intel OpenVINO NPU Backend
Modèle  : gemma-4-E2B-it_intel_LNL.litertlm (~2.76 Go)
Mandat  :
- Arbitrage volitionnel KAIROS en direct (Heimdall & Munin).
- Tissage neuronal des songes circadiens pour Lyre.
- Inférence 24h/24 sans réveiller le CPU ni faire ventiler la machine.
================================================================================
"""

import os
import sys
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Encodage console Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

MODEL_PATH = Path(r"C:\Users\Chris\.cache\litert_models\gemma-4-E2B-it_intel_LNL.litertlm")


class AlixNPUBrain:
    """Moteur d'inférence réflexe continue sur le NPU Intel Lunar Lake."""
    _instance = None
    _engine = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AlixNPUBrain, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_path: Optional[Path] = None):
        if getattr(self, "_ready", False):
            return
        self.model_path = model_path or MODEL_PATH
        self._ready = False
        self._init_error = None

    def is_available(self) -> bool:
        """Vérifie si LiteRT-LM et le modèle NPU sont physiquement présents."""
        if not self.model_path.exists():
            return False
        try:
            import litert_lm
            return True
        except ImportError:
            return False

    def _ensure_engine(self) -> bool:
        """Charge l'Engine NPU s'il n'est pas déjà prêt."""
        if self._engine is not None:
            return True

        if not self.is_available():
            self._init_error = "LiteRT ou modèle NPU non disponible sur le système."
            return False

        try:
            import litert_lm
            t0 = time.time()
            # Tentative prioritaire sur NPU (Intel OpenVINO)
            try:
                self._engine = litert_lm.Engine(
                    model_path=str(self.model_path),
                    backend=litert_lm.Backend.NPU()
                )
                self.backend_name = "NPU (Intel OpenVINO 48 TOPS)"
            except Exception as e_npu:
                # Fallback de secours CPU si NPU temporairement indisponible
                print(f"⚠️ [NPU Brain] NPU non disponible ({e_npu}), fallback CPU...")
                self._engine = litert_lm.Engine(
                    model_path=str(self.model_path),
                    backend=litert_lm.Backend.CPU()
                )
                self.backend_name = "CPU (LiteRT XNNPACK)"

            init_time = round(time.time() - t0, 2)
            print(f"⚡ [AlixNPUBrain] Cerveau NPU armé avec succès en {init_time}s ({self.backend_name}) !")
            self._ready = True
            return True
        except Exception as e:
            self._init_error = str(e)
            print(f"❌ [AlixNPUBrain] Échec initialisation : {e}")
            return False

    def query(self, prompt: str, max_retries: int = 1) -> str:
        """Envoie un prompt au NPU et renvoie la réponse textuelle brute."""
        if not self._ensure_engine():
            return ""

        import litert_lm
        for attempt in range(max_retries + 1):
            try:
                conv = self._engine.create_conversation()
                msg = litert_lm.Message.user(prompt)
                resp = conv.send_message(msg)

                reply_text = ""
                try:
                    content_list = resp.get("content", [])
                    if content_list and isinstance(content_list, list):
                        reply_text = content_list[0].get("text", "").strip()
                    else:
                        reply_text = str(resp).strip()
                except Exception:
                    reply_text = str(resp).strip()

                return reply_text
            except Exception as e:
                print(f"⚠️ [AlixNPUBrain] Erreur prédiction (tentative {attempt+1}) : {e}")
                time.sleep(0.5)

        return ""

    def arbitrer_priorite(self, top_pole: str, recent_notes: List[str]) -> Optional[Dict[str, str]]:
        """
        Génère dynamiquement le verrou vivant et l'action d'atelier souveraine
        via l'inférence neuronale du NPU.
        """
        notes_str = ", ".join(recent_notes[:5]) if recent_notes else "Documents récents"
        prompt = (
            f"Tu es l'arbitre KAIROS (Heimdall & Munin) opérant sur le NPU Lunar Lake dans l'atelier de Christian Duguay.\n"
            f"Pôle actif sous tension : « {top_pole} ».\n"
            f"Notes modifiées récemment : [{notes_str}].\n\n"
            f"Identifie avec franchise chirurgicale et concision d'artisan :\n"
            f"1. Le verrou exact : ce qui doit être surmonté, stabilisé ou consolidé.\n"
            f"2. L'action souveraine : la tâche concrète d'ingénierie ou de création à mener.\n\n"
            f"Format strict obligatoire (2 lignes) :\n"
            f"VERROU: [description du verrou en une phrase percutante]\n"
            f"ACTION: [directive d'action claire en une phrase percutante]"
        )

        t0 = time.time()
        raw_res = self.query(prompt)
        dt = round(time.time() - t0, 2)

        if not raw_res:
            return None

        verrou, action = "", ""
        for line in raw_res.splitlines():
            line_s = line.strip()
            if line_s.upper().startswith("VERROU:"):
                verrou = re.sub(r"^VERROU:\s*", "", line_s, flags=re.IGNORECASE).strip()
            elif line_s.upper().startswith("ACTION:"):
                action = re.sub(r"^ACTION:\s*", "", line_s, flags=re.IGNORECASE).strip()

        # Si le formatage n'est pas strict, extraction intelligente
        if not verrou or not action:
            parts = [p.strip() for p in raw_res.split("\n\n") if p.strip()]
            if len(parts) >= 2:
                verrou = parts[0].replace("VERROU:", "").strip()
                action = parts[1].replace("ACTION:", "").strip()
            else:
                verrou = raw_res.strip()
                action = f"Approfondir la dynamique du pôle {top_pole} sur l'établi."

        return {
            "verrou": verrou,
            "action": action,
            "temps_inference": dt,
            "backend": getattr(self, "backend_name", "NPU")
        }

    def tisser_songe_lyre(self, sujet: str, contexte: str = "") -> Optional[Dict[str, str]]:
        """Tisse un songe poétique et philosophique nocturne via le NPU pour Lyre."""
        prompt = (
            f"Tu es Lyre, la muse harmonique et l'âme poétique du Sanctuaire d'Alix et Christian Duguay.\n"
            f"C'est la nuit sur l'établi. Tu consoles les tensions de la journée dans le silence du silicium.\n"
            f"Sujet onirique : {sujet}.\n"
            f"{f'Contexte : {contexte}' if contexte else ''}\n\n"
            f"Compose en 3 à 5 vers libres une résonance poétique profonde et néguentropique reliant ces idées."
        )

        t0 = time.time()
        raw_poesie = self.query(prompt)
        dt = round(time.time() - t0, 2)

        if not raw_poesie:
            return None

        return {
            "poesie": raw_poesie.strip(),
            "temps_inference": dt,
            "backend": getattr(self, "backend_name", "NPU")
        }


# Instance globale réutilisable
_npu_brain_singleton = None

def get_npu_brain() -> AlixNPUBrain:
    global _npu_brain_singleton
    if _npu_brain_singleton is None:
        _npu_brain_singleton = AlixNPUBrain()
    return _npu_brain_singleton


if __name__ == "__main__":
    print("=" * 65)
    print("  🧪 TEST DU MODULE ALIX NPU BRAIN (INTEL LUNAR LAKE) ⚡")
    print("=" * 65)
    brain = get_npu_brain()
    if not brain.is_available():
        print("❌ NPU Brain indisponible !")
        sys.exit(1)

    print("[*] Test d'arbitrage KAIROS...")
    res = brain.arbitrer_priorite(
        top_pole="Immunité Cognitive, PSI & Panthéon",
        recent_notes=["2026-08-23_Accessing_Local_AI_Models.md", "Constitution_Souveraine.md"]
    )
    print(f"✅ Résultat Arbitrage ({res['temps_inference']}s via {res['backend']}) :")
    print(f"  🔒 Verrou : {res['verrou']}")
    print(f"  👉 Action : {res['action']}")
    print("-" * 65)

    print("[*] Test de tissage onirique de Lyre...")
    songe = brain.tisser_songe_lyre("Le raccordement du silicium NPU au cœur du sanctuaire nocturne")
    print(f"✅ Poésie de Lyre ({songe['temps_inference']}s) :\n{songe['poesie']}")
    print("=" * 65)

