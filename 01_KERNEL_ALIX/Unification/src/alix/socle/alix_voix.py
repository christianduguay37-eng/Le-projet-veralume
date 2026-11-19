# -*- coding: utf-8 -*-
r"""
Voix Neuronale Québécoise d'Alix (fr-CA-SylvieNeural).
Fluide, vivante, humaine, sans le ton robotique de Windows.
"""
import asyncio
import os
import sys
import tempfile
import edge_tts
import pygame

async def _synthetiser_et_jouer(texte: str):
    try:
        voix = "fr-CA-SylvieNeural"
        tmp = os.path.join(tempfile.gettempdir(), "alix_neural_voice.mp3")
        communicate = edge_tts.Communicate(texte, voix, rate="+15%", pitch="+0Hz")
        await communicate.save(tmp)

        pygame.mixer.init()
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.05)
        pygame.mixer.quit()
    except Exception as e:
        print(f"[VOIX ALIX] Erreur: {e}", file=sys.stderr)

def parler(texte: str):
    asyncio.run(_synthetiser_et_jouer(texte))

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Je suis là Christian."
    parler(msg)
