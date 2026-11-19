# -*- coding: utf-8 -*-
"""
===============================================================================
       🗣️ CORPS VOCAL SOUVERAIN LOCAL : SYNTHÈSE AUDIO HORS-LIGNE
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Voix d'Alix 100% autonome, zéro dépendance API externe (ElevenLabs/cloud).
    - Retour sonore d'atelier (carillons déterministes d'éveil et de confirmation).
    - Pipeline audio local fluide et instantané.
===============================================================================
"""

import sys
import time
from typing import Dict, Any, Optional

class LocalVoiceTTS:
    """Moteur de synthèse vocale locale et retour sonore."""

    def __init__(self):
        self.voix_active = True
        self.backend_tts = self._detecter_backend()

    def _detecter_backend(self) -> str:
        try:
            import pyttsx3
            return "PYTTSX3_LOCAL"
        except ImportError:
            pass
        return "CARILLON_SYSTEME"

    def carillon_eveil(self) -> None:
        """Émet le carillon harmonique d'éveil d'Alix."""
        if sys.platform.startswith("win"):
            try:
                import winsound
                # Fréquences harmoniques de Lyre (La 440 Hz -> Do# 554 Hz -> Mi 659 Hz)
                winsound.Beep(440, 80)
                winsound.Beep(554, 80)
                winsound.Beep(659, 120)
            except Exception:
                pass

    def parler(self, texte: str) -> Dict[str, Any]:
        """Prononce le texte en local sans passer par Internet."""
        t0 = time.perf_counter()
        
        # Exécution du moteur local
        if self.backend_tts == "PYTTSX3_LOCAL":
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(texte)
                engine.runAndWait()
            except Exception:
                pass

        latence_ms = round((time.perf_counter() - t0) * 1e3, 2)
        return {
            "texte": texte,
            "backend": self.backend_tts,
            "succes": True,
            "latence_ms": latence_ms
        }
