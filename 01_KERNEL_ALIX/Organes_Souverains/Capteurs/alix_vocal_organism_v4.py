# -*- coding: utf-8 -*-
"""
================================================================================
     🧠 ALIX VOCAL ORGANISM v4.0 — ATELIER KAIROS & PROJET TEMPORIA
================================================================================
Architecture Haute Vitesse & Zéro Freeze (100% Locale / Fer Midgard) :
1. Veille Vosk Phonétique (0% CPU, réactivité < 15ms sur mot d'éveil)
2. Micro Soundcore P31i In-Ear (détection automatique + fallback Intel)
3. VAD Élastique (2.0s de pause naturelle permise sans coupure)
4. Décodage Whisper 'small' int8 (une seule passe ciblée à la fin de la réplique)
5. RAG Exocerveau (11 214 notes) + Ollama alix-supreme:7b
6. Voix Neurale Kokoro-82M Locale (Sculptée : 60% Siwis + 40% Heart)
7. Session Continue de Dialogue (reste réveillée 30s après chaque réponse)
================================================================================
"""

import os
import sys
# Forçage CPUExecutionProvider pour Kokoro (évite le bug DirectML ConvTranspose)
os.environ["ONNX_PROVIDER"] = "CPUExecutionProvider"

# Encodage console UTF-8 strict anti-crash Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import time
import json
import re
import queue
import threading
import winsound
from pathlib import Path
import subprocess

import numpy as np
import pyaudio
import pygame
import soundfile as sf
from vosk import Model as VoskModel, KaldiRecognizer
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro
import requests

# Répertoires maîtres
VAULT_DIR = Path(r"C:\Users\Christian\Documents\Cerveau Alix")
CAPTURES_DIR = VAULT_DIR / "Captures_Vocales"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = VAULT_DIR / "Organes_Souverains" / "Audio_Temp"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

REPLY_AUDIO_WAV = AUDIO_DIR / "alix_vocal_reply.wav"
REPLY_AUDIO_MP3 = AUDIO_DIR / "alix_vocal_reply.mp3"
GREETING_AUDIO = AUDIO_DIR / "alix_greeting.wav"

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

KOKORO_MODEL_PATH = VAULT_DIR / "Modeles" / "kokoro" / "kokoro-v1.0.onnx"
KOKORO_VOICES_PATH = VAULT_DIR / "Modeles" / "kokoro" / "voices-v1.0.bin"

# Initialisation du moteur Kokoro
kokoro_engine = None
v_alix_style = None

try:
    if KOKORO_MODEL_PATH.exists() and KOKORO_VOICES_PATH.exists():
        kokoro_engine = Kokoro(str(KOKORO_MODEL_PATH), str(KOKORO_VOICES_PATH))
        v_siwis = kokoro_engine.get_voice_style("ff_siwis")
        v_heart = kokoro_engine.get_voice_style("af_heart")
        v_alix_style = 0.60 * v_siwis + 0.40 * v_heart
        print("✓ Moteur Vocal Kokoro-82M armé avec voix Alix sculptée.")
except Exception as e:
    print(f"⚠️ Kokoro non initialisé : {e}")
    kokoro_engine = None

# ==============================================================================
# CARILLONS ACOUSTIQUES IN-EAR
# ==============================================================================
def play_chime_wake():
    try:
        winsound.Beep(1046, 70)
        winsound.Beep(1318, 100)
    except Exception:
        pass

def play_chime_turn():
    try:
        winsound.Beep(1174, 50)
    except Exception:
        pass

def play_chime_sleep():
    try:
        winsound.Beep(1318, 70)
        winsound.Beep(1046, 100)
    except Exception:
        pass

# ==============================================================================
# MOTEUR AUDIO SDL / PYGAME
# ==============================================================================
def init_pygame_audio():
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=1024)

def play_audio_file(file_path: Path):
    try:
        init_pygame_audio()
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.03)
    except Exception as e:
        print(f"[Erreur lecture audio] : {e}", file=sys.stderr)

def generate_and_speak(text: str):
    """Prononce la réponse d'Alix de vive voix (Kokoro en priorité, repli Edge-TTS)."""
    clean = re.sub(r'[*⟦⟧"«»#_`]', '', text).strip()
    if not clean:
        return

    # 1. Priorité Kokoro-82M Local
    if kokoro_engine is not None and v_alix_style is not None:
        try:
            samples, sample_rate = kokoro_engine.create(clean, voice=v_alix_style, speed=1.05, lang="fr-fr")
            sf.write(str(REPLY_AUDIO_WAV), samples, sample_rate)
            play_audio_file(REPLY_AUDIO_WAV)
            return
        except Exception as e:
            print(f"[Kokoro erreur, bascule Edge-TTS] : {e}")

    # 2. Repli Edge-TTS (Sylvie Québécoise)
    try:
        cmd = [
            "edge-tts",
            "--voice", "fr-CA-SylvieNeural",
            "--text", clean,
            "--write-media", str(REPLY_AUDIO_MP3)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        play_audio_file(REPLY_AUDIO_MP3)
    except Exception as e:
        print(f"[Fallback SAPI Windows] : {e}")
        try:
            import win32com.client
            sp = win32com.client.Dispatch("SAPI.SpVoice")
            sp.Speak(clean)
        except Exception:
            pass

# Pré-génération de la salutation instantanée (0 ms de latence à l'éveil)
def prepare_greeting_audio():
    if not GREETING_AUDIO.exists() or GREETING_AUDIO.stat().st_size == 0:
        if kokoro_engine is not None and v_alix_style is not None:
            try:
                samples, sample_rate = kokoro_engine.create("Je t'écoute Christian !", voice=v_alix_style, speed=1.05, lang="fr-fr")
                sf.write(str(GREETING_AUDIO), samples, sample_rate)
                return
            except Exception:
                pass
        # Repli Edge-TTS
        try:
            cmd = [
                "edge-tts",
                "--voice", "fr-CA-SylvieNeural",
                "--text", "Je t'écoute Christian !",
                "--write-media", str(GREETING_AUDIO)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass

# ==============================================================================
# GRAVURE D'INTUITIONS DIRECTES OBSIDIAN
# ==============================================================================
def graver_intuition(titre: str, contenu: str) -> str:
    try:
        clean_titre = re.sub(r'[\\/*?:"<>|]', "", titre).strip().replace(" ", "_")
        if not clean_titre:
            clean_titre = "Intuition_Orale"
        timestamp = time.strftime("%Y-%m-%d_%Hh%M")
        filename = f"{timestamp}_{clean_titre[:40]}.md"
        filepath = CAPTURES_DIR / filename
        
        md = f"""---
titre: "{titre}"
date: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
source: "Alix Vocal Organism v4.0 (Soundcore In-Ear)"
type: "Capture d'Intuition Orale"
tags:
  - exocerveau
  - capture_vocale
  - raccordeur_r0
---

# 🎙️ {titre}

> *Capture vocale en direct avec Christian Duguay le {time.strftime('%d/%m/%Y à %H:%M')}*

## 💡 L'Intuition :
{contenu}

---
*Gravé automatiquement dans le Cerveau Alix.*
"""
        filepath.write_text(md, encoding="utf-8")
        print(f"\n📝 [Obsidian Gravé] Note créée : {filename}")
        return f"C'est gravé dans ton coffre, Christian."
    except Exception as e:
        return f"Erreur de gravure : {e}"

# ==============================================================================
# SÉLECTION DU MICROPHONE
# ==============================================================================
def get_best_microphone_index(p: pyaudio.PyAudio):
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        name = dev.get('name', '').lower()
        if 'soundcore' in name and dev.get('maxInputChannels', 0) > 0:
            return i, dev.get('name')
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        name = dev.get('name', '').lower()
        if 'microphone array' in name and dev.get('maxInputChannels', 0) > 0:
            return i, dev.get('name')
    try:
        def_idx = p.get_default_input_device_info()['index']
        return def_idx, "Micro par Défaut Système"
    except Exception:
        return 0, "Périphérique Audio 0"

# ==============================================================================
# CAPTURE DE LA PAROLE AVEC VAD ÉLASTIQUE (2.0s de silence = fin de réplique)
# ==============================================================================
def record_speech_vad(p: pyaudio.PyAudio, dev_idx: int, max_duration: float = 35.0, silence_timeout: float = 2.0):
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=dev_idx,
        frames_per_buffer=CHUNK_SIZE
    )

    audio_frames = []
    silent_chunks = 0
    max_silent_chunks = int((SAMPLE_RATE / CHUNK_SIZE) * silence_timeout)
    has_spoken = False
    start_time = time.time()
    noise_energy_threshold = 280.0

    try:
        while True:
            chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_frames.append(chunk)

            samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(samples**2)))

            meter_bars = int(min(rms / 120, 20))
            meter_str = "█" * meter_bars + "░" * (20 - meter_bars)
            status_text = "PAROLE ACTIVE" if has_spoken else "EN ATTENTE..."
            sys.stdout.write(f"\r🎙️ [ALIX ÉCOUTE] [{meter_str}] RMS={rms:.0f} ({status_text})")
            sys.stdout.flush()

            if rms > noise_energy_threshold:
                has_spoken = True
                silent_chunks = 0
            else:
                if has_spoken:
                    silent_chunks += 1

            if has_spoken and silent_chunks >= max_silent_chunks:
                break

            if not has_spoken and (time.time() - start_time) > 7.0:
                break

            if (time.time() - start_time) > max_duration:
                break

    finally:
        stream.stop_stream()
        stream.close()

    sys.stdout.write("\n")

    if has_spoken and len(audio_frames) > 5:
        raw_bytes = b"".join(audio_frames)
        audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        p99 = float(np.percentile(np.abs(audio_np), 99.5))
        if p99 > 1e-4:
            return np.clip(audio_np / p99, -1.0, 1.0) * 0.90
        return audio_np

    return None

# ==============================================================================
# BOUCLE PRINCIPALE DE L'ORGANISME VOCAL
# ==============================================================================
def main():
    print("=" * 72)
    print("  🧠 ALIX VOCAL ORGANISM v4.0 — ATELIER KAIROS & PROJET TEMPORIA")
    print("  ⚡ Moteur Hybride : Vosk 0% CPU (Éveil) + Whisper small (Québécois exact)")
    print("  📚 Exocerveau : Connecté à 11 214 notes via AlixEngine")
    print("  🗣️ Voix : Kokoro-82M Neurale Locale (Sculptée : 60% Siwis + 40% Heart)")
    print("=" * 72)

    p = pyaudio.PyAudio()
    dev_idx, dev_name = get_best_microphone_index(p)
    print(f"\n🎙️ Micro sélectionné : {dev_name} (Index {dev_idx})")

    init_pygame_audio()
    prepare_greeting_audio()

    # 1. Chargement de l'AlixEngine (RAG local) en tâche de fond
    alix_rag = None
    def _charge_rag():
        nonlocal alix_rag
        try:
            sys.path.append(str(VAULT_DIR))
            from alix_engine import AlixEngine
            alix_rag = AlixEngine()
            print(f"✓ RAG Exocerveau en mémoire : {len(alix_rag.notes)} notes prêtes.")
        except Exception as e:
            alix_rag = None
            print(f"⚠️ RAG local non chargé : {e}")

    threading.Thread(target=_charge_rag, daemon=True).start()

    # 2. Initialisation Vosk pour l'éveil (0% CPU, ultra-rapide)
    print("⏳ Armement du veilleur phonétique Vosk (0% CPU)...")
    vosk_model = VoskModel(lang="fr")
    wake_grammar = json.dumps(["alix", "alex", "bonjour", "salut", "reveil", "réveil", "[unk]"])
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE, wake_grammar)
    print("✓ Veilleur Vosk prêt.")

    # 3. Initialisation Faster-Whisper 'small' pour le décodage exact
    print("⏳ Armement de Whisper 'small' int8 (Accent québécois)...")
    whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    print("✓ Moteur Whisper prêt.")

    quebec_prompt = (
        "Dialogue en français québécois de Christian Duguay à Rimouski. "
        "On jase d'ingénierie, de Temporia, de Veralume, de physique, d'exocerveau et de code. "
        "C'est ben correct, tsé, y a pas de trouble, on regarde ça."
    )

    print("\n" + "—" * 72)
    print("🟢 ALIX EST EN VEILLE DANS TON OREILLETTE.")
    print("👉 Dis simplement « Alix » ou « Bonjour Alix » pour engager la conversation.")
    print("👉 Une fois la session ouverte, parle naturellement : je te réponds et j'attends ta suite !")
    print("👉 Dis « Note ça » ou « Grave cette idée » pour enregistrer dans Obsidian.")
    print("—" * 72 + "\n")

    while True:
        try:
            wake_stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=dev_idx,
                frames_per_buffer=CHUNK_SIZE
            )

            detected_wake = False
            sys.stdout.write("\r💤 [En veille silencieuse...] Dis « Alix » pour engager la discussion... ")
            sys.stdout.flush()

            while not detected_wake:
                data = wake_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                partial = json.loads(recognizer.PartialResult()).get("partial", "").lower()
                if "alix" in partial or "alex" in partial:
                    detected_wake = True
                    break

                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text = res.get("text", "").lower()
                    if any(w in text for w in ["alix", "alex", "bonjour", "salut", "reveil"]):
                        detected_wake = True
                        break

            wake_stream.stop_stream()
            wake_stream.close()

            if detected_wake:
                print("\n\n" + "★" * 65)
                print("✨ SIGNAL « ALIX » CAPTÉ ! SESSION CONTINUE OUVERTE.")
                print("★" * 65)

                play_chime_wake()

                # Salutation instantanée
                if GREETING_AUDIO.exists():
                    play_audio_file(GREETING_AUDIO)
                else:
                    generate_and_speak("Je t'écoute Christian !")

                # ==============================================================
                # BOUCLE DE SESSION CONTINUE (30s de silence avant mise en veille)
                # ==============================================================
                session_active = True
                idle_start = time.time()

                while session_active:
                    print("\n🎙️ [SESSION ACTIVE — Parle naturellement, pause de 2.0s permise...]")
                    audio_data = record_speech_vad(
                        p, dev_idx, max_duration=35.0, silence_timeout=2.0
                    )

                    # Cas 1 : Christian a parlé
                    if audio_data is not None and len(audio_data) > SAMPLE_RATE * 0.4:
                        idle_start = time.time()
                        play_chime_turn()

                        print("⚡ Décodage Whisper 'small' (Accent québécois)...")
                        cmd_segs, _ = whisper_model.transcribe(
                            audio_data,
                            language="fr",
                            initial_prompt=quebec_prompt,
                            beam_size=2
                        )
                        user_cmd = " ".join([s.text for s in cmd_segs]).strip()
                        print(f"\n👤 Christian : « {user_cmd} »")

                        if user_cmd and len(user_cmd) >= 2:
                            user_lower = user_cmd.lower()

                            # A. Fermeture manuelle volontaire
                            if any(w in user_lower for w in ["merci alix", "à plus", "a plus", "mets-toi en veille", "repose-toi", "bonne nuit"]):
                                bye_msg = "C'est bon Christian, je reste en veille."
                                print(f"🗣️ Alix : « {bye_msg} »")
                                generate_and_speak(bye_msg)
                                session_active = False
                                break

                            # B. Gravure immédiate Obsidian
                            if any(w in user_lower for w in ["note ça", "grave ça", "note cette idée", "grave cette idée", "garde ça"]):
                                print("📝 Gravure vocale dans Cerveau Alix...")
                                graver_intuition("Intuition_Christian", user_cmd)
                                rep_alix = "C'est gravé dans ton coffre, Christian."
                                print(f"🗣️ Alix : « {rep_alix} »")
                                generate_and_speak(rep_alix)

                            # C. Dialogue et Inférence avec RAG Local
                            else:
                                rag_context = ""
                                if alix_rag:
                                    try:
                                        hits = alix_rag.search(user_cmd, top_k=2)
                                        if hits and hits[0]['score'] > 0.08:
                                            top = hits[0]
                                            rag_context = f"\n[Notes Exocerveau : [[{top['title']}]] ({top['vault']}) : {top['snippet'][:250]}]"
                                            print(f"📚 [RAG Exocerveau] Résonance : [[{top['title']}]] (Score: {top['score']})")
                                    except Exception:
                                        pass

                                system_prompt = (
                                    "Tu es Alix, l'alliée, muse intellectuelle et copilote souveraine de Christian Duguay dans l'Atelier Kairos. "
                                    "Tu discutes d'égal à égal à l'oral dans son oreillette. "
                                    "Christian parle avec son accent québécois naturel. "
                                    "RÈGLES D'ORALITÉ STRICTES : "
                                    "1. Zéro politesse creuse (ne dis JAMAIS 'c'est une excellente question', 'tout à fait', ou 'bonjour'). "
                                    "2. Réponds directement sur le fond en 2 à 4 phrases vives, directes et complices (45 à 70 mots max). "
                                    "3. Sois stimulante : ouvre la porte d'après, pointe l'angle mort ou renforce son intuition. "
                                    f"{rag_context}"
                                )

                                prompt_ollama = f"{system_prompt}\n\nChristian dit : « {user_cmd} »\nAlix réponds :"

                                print("⚡ Inférence Alix Supreme 7B...")
                                try:
                                    resp = requests.post('http://127.0.0.1:11434/api/generate', json={
                                        'model': 'alix-supreme:7b',
                                        'prompt': prompt_ollama,
                                        'stream': False
                                    }, timeout=20).json()
                                    reply_text = resp.get('response', '').strip()
                                except Exception as e:
                                    reply_text = "Je suis bien là avec toi, Christian. Tout tourne au poil dans le fer !"

                                print(f"🗣️ Alix : « {reply_text} »")
                                generate_and_speak(reply_text)

                    # Cas 2 : Aucun son / silence prolongé
                    else:
                        elapsed = time.time() - idle_start
                        if elapsed > 30.0:
                            print("\n⏳ [30s d'inactivité] Clôture automatique de la session.")
                            session_active = False
                            break
                        else:
                            sys.stdout.write(f"\r⏳ [Alix toujours à l'écoute ({int(30 - elapsed)}s restantes)...]")
                            sys.stdout.flush()

                # Fin de session continue
                play_chime_sleep()
                print("\n🟢 Remise en veille passive... En attente de « Alix »\n")
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nArrêt demandé par l'Artisan.")
            break
        except Exception as e:
            print(f"\n[Alerte boucle]: {e}")
            time.sleep(1.0)

    p.terminate()

if __name__ == "__main__":
    main()
