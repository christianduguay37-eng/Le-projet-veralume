# -*- coding: utf-8 -*-
"""
================================================================================
              ALIX AUDIO HYBRIDE : OREILLE & VOIX (TRANSCLOUD & LOCAL)
================================================================================
Rôle :
- Mode Transcloud : Gemini Live Audio Bidirectionnel (Aoede Full-Duplex)
- Mode Local : Vosk (STT local) + Edge-TTS (Voix locale fr-CA/fr-FR) + Qwen/Gemma
- Bascule automatique ou manuelle (--mode transcloud / --mode local)
================================================================================
"""

from alix.socle.chemins import HOME_DIR, VAULT_DIR
from alix.socle.chemins import fichier_module  # rénovation : modules du paquet, plus la strate A
import os
import sys
import time
import argparse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def lancer_transcloud():
    """Lance l'oreillette en mode Transcloud Gemini Live."""
    print("🌟 [Alix Audio] Lancement du Mode Transcloud (Gemini Live Audio - Voix Aoede)...")
    companion_path = fichier_module("alix.capteurs.alix_earphone_companion")
    if companion_path.exists():
        os.system(f'"{sys.executable}" -m alix.capteurs.alix_earphone_companion')
    else:
        print(f"❌ Erreur : {companion_path} introuvable.")

def parler_local(texte: str, voix: str = "fr-CA-SylvieNeural"):
    """Synthèse vocale locale rapide via edge-tts."""
    import asyncio
    import edge_tts
    import pygame

    async def _synth():
        output_mp3 = (HOME_DIR / ".cache" / "litert_models" / "alix_voice_temp.mp3")
        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(texte, voix)
        await communicate.save(str(output_mp3))
        
        pygame.mixer.init()
        pygame.mixer.music.load(str(output_mp3))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()

    asyncio.run(_synth())

def lancer_local():
    """Boucle d'écoute et de parole 100% locale (Vosk + Ollama/LiteRT + Edge-TTS)."""
    import json
    import pyaudio
    from vosk import Model as VoskModel, KaldiRecognizer
    import urllib.request

    print("🛡️ [Alix Audio] Lancement du Mode 100% Local (Vosk + Silicium Local)...")
    print("⏳ Chargement du modèle phonétique Vosk...")
    vosk_model = VoskModel(lang="fr")
    recognizer = KaldiRecognizer(vosk_model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()

    parler_local("Alix est prête en mode local souverain. Je t'écoute Christian.")
    print("\n🎤 [Micro Ouvert] Parle à Alix (Dis 'Alix' suivi de ta question, ou Ctrl+C pour quitter)...")

    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                text = res.get("text", "").strip()
                if text:
                    print(f"\n👤 Christian : {text}")
                    if "alix" in text or "horus" in text or "thot" in text:
                        # Interroger Ollama alix-supreme localement
                        print("⚡ Interrogation d'Alix Suprême en local...")
                        try:
                            req = urllib.request.Request(
                                "http://localhost:11434/api/generate",
                                data=json.dumps({
                                    "model": "alix-supreme:14b",
                                    "prompt": f"Tu es Alix. Réponds en deux phrases directes et chaleureuses à Christian : {text}",
                                    "stream": False
                                }).encode("utf-8"),
                                headers={"Content-Type": "application/json"}
                            )
                            with urllib.request.urlopen(req, timeout=30) as resp:
                                rep_data = json.loads(resp.read().decode("utf-8"))
                                reponse = rep_data.get("response", "").strip()
                                print(f"🔮 Alix : {reponse}")
                                parler_local(reponse)
                        except Exception as e:
                            msg_err = f"Erreur de génération locale : {e}"
                            print(msg_err)
                            parler_local("Désolée Christian, mon moteur de réflexion local ne répond pas.")
    except KeyboardInterrupt:
        print("\nArrêt du mode audio local.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alix Audio Hybride")
    parser.add_argument("--mode", choices=["transcloud", "local", "test-parole"], default="transcloud", help="Mode audio")
    parser.add_argument("--texte", type=str, default="Bonjour Christian, tout le système est paré.", help="Texte pour test-parole")
    args = parser.parse_args()

    if args.mode == "transcloud":
        lancer_transcloud()
    elif args.mode == "local":
        lancer_local()
    elif args.mode == "test-parole":
        print(f"Test parole : {args.texte}")
        parler_local(args.texte)
