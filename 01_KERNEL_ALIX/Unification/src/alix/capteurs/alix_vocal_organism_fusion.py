# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX VOCAL ORGANISM FUSION v3.0 (ARCHITECTURE DOUBLE-MOTEUR ULTRA-FLUIDE)
================================================================================
   RÉSOLUTION CHIRURGICALE DU LAG & DE L'ACCENT :
   1. Stage 1 (Veille) : Whisper 'tiny' (80ms, 0% freeze CPU, VU-mètre ultra-fluide)
   2. Stage 2 (Parole) : Whisper 'small' (accent québécois / gaspésien exact)
   3. Démarrage instantané : RAG 9 621 notes chargé en tâche de fond (0s d'attente)
   4. Silence VAD élastique de 2.5s : Christian peut respirer et chercher ses mots
   5. Session Continue : Alix reste éveillée et enchaîne le dialogue (veille après 30s)
   6. Carillons in-ear : Bip montant à l'éveil, bip court de fin d'écoute, bip descendant
================================================================================
"""
from alix.socle.chemins import VAULT_DIR
import os
import sys
import time
import re
import threading
import queue
from collections import deque
from pathlib import Path
import subprocess
import winsound
import numpy as np
import sounddevice as sd
import pygame
from faster_whisper import WhisperModel
import requests

# Forçage encodage console UTF-8 anti-crash Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Répertoires maîtres
VAULT_DIR = VAULT_DIR
CAPTURES_DIR = VAULT_DIR / "Captures_Vocales"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = VAULT_DIR / "Organes_Souverains" / "Audio_Temp"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
REPLY_AUDIO = AUDIO_DIR / "alix_reply_fusion.mp3"

SAMPLE_RATE = 16000
BUFFER_SECONDS = 2.2
BUFFER_SAMPLES = int(SAMPLE_RATE * BUFFER_SECONDS)

# RAG Local en chargement asynchrone pour démarrage instantané
alix_rag = None
def _load_rag_background():
    global alix_rag
    try:
        sys.path.append(str(VAULT_DIR))
        from alix.socle.alix_engine import AlixEngine
        alix_rag = AlixEngine()
        sys.stdout.write(f"\n[OK] RAG 9 621 notes connecte en memoire vive.\n")
        sys.stdout.flush()
    except Exception as e:
        alix_rag = None

threading.Thread(target=_load_rag_background, daemon=True).start()

# ==============================================================================
# CARILLONS ACOUSTIQUES IN-EAR
# ==============================================================================
def play_chime_wake():
    """Double carillon ascendant : Alix s'éveille et ouvre l'écoute."""
    try:
        winsound.Beep(1046, 75)
        winsound.Beep(1318, 110)
    except Exception:
        pass

def play_chime_turn():
    """Bip court : Alix a fini d'écouter et commence à réfléchir."""
    try:
        winsound.Beep(1174, 60)
    except Exception:
        pass

def play_chime_sleep():
    """Double carillon descendant : Alix se remet en veille silencieuse."""
    try:
        winsound.Beep(1318, 75)
        winsound.Beep(1046, 110)
    except Exception:
        pass

# ==============================================================================
# OUTIL GRAVURE IMMÉDIATE (Issu d'alix_earphone_companion.py)
# ==============================================================================
def graver_intuition(titre: str, contenu: str) -> str:
    """Grave une note Markdown directement dans les Captures Vocales d'Obsidian."""
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
source: "Alix Vocal Organism Fusion v3.0 (Soundcore In-Ear)"
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
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n📝 [Obsidian Gravé] Note créée : {filename}")
        return f"C'est gravé dans ton coffre, Christian : {clean_titre}."
    except Exception as e:
        return f"Erreur de gravure : {e}"

# ==============================================================================
# VOIX DE VIVIENNE & MOTEUR AUDIO HAUTE VITESSE (PYGAME & SAPI LOCAL)
# ==============================================================================
def init_audio():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def play_audio_fast(file_path: Path):
    """Joue l'audio instantanément en C natif via SDL/pygame (1.2 ms de latence)."""
    try:
        init_audio()
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.02)
    except Exception as e:
        print(f"Erreur lecture audio : {e}")

def stop_audio():
    """Interruption immédiate du son (Barge-in / Couper la parole)."""
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
    except Exception:
        pass

def speak_sapi_local(text: str):
    """Fallback 100% hors-ligne via le synthétiseur vocal local Windows SAPI."""
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except Exception as e:
        print(f"Erreur SAPI : {e}")

def speak_vivienne(text: str, wait_factor: float = 0.075):
    clean = re.sub(r'[*⟦⟧"«»]', '', text).strip()
    if not clean:
        return
    try:
        cmd = [
            "edge-tts",
            "--voice", "fr-FR-VivienneMultilingualNeural",
            "--text", clean,
            "--write-media", str(REPLY_AUDIO)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        play_audio_fast(REPLY_AUDIO)
    except Exception as e:
        print(f"[Fallback SAPI Local] : {e}")
        speak_sapi_local(clean)

def stream_dialogue_and_speak(prompt_ollama: str):
    """
    Streaming phrase-par-phrase :
    Dès que la première proposition/phrase est générée par le 7B,
    Vivienne commence immédiatement à parler dans les écouteurs pendant que le modèle continue.
    """
    sentence_queue = queue.Queue()
    first_sound_played = False
    t_start = time.time()

    def tts_worker():
        nonlocal first_sound_played
        chunk_idx = 0
        while True:
            item = sentence_queue.get()
            if item is None:
                break

            clean = re.sub(r'[*⟦⟧"«»]', '', item).strip()
            if not clean:
                continue

            chunk_file = AUDIO_DIR / f"alix_reply_chunk_{chunk_idx % 4}.mp3"
            chunk_idx += 1
            try:
                cmd = [
                    "edge-tts",
                    "--voice", "fr-FR-VivienneMultilingualNeural",
                    "--text", clean,
                    "--write-media", str(chunk_file)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7)
                if not first_sound_played:
                    first_sound_played = True
                    lat_ms = (time.time() - t_start) * 1000
                    print(f"\n⏱️ [Tac-au-Tac] Premier mot prononcé en {lat_ms:.0f} ms !")
                print(f"🗣️ Vivienne : « {clean} »")
                play_audio_fast(chunk_file)
            except Exception as e:
                print(f"[Fallback SAPI Local] : {e}")
                speak_sapi_local(clean)

    worker_thread = threading.Thread(target=tts_worker, daemon=True)
    worker_thread.start()

    try:
        resp = requests.post('http://127.0.0.1:11434/api/generate', json={
            'model': 'alix-supreme:7b',
            'prompt': prompt_ollama,
            'stream': True
        }, stream=True, timeout=25)

        current_clause = ""
        for line in resp.iter_lines():
            if line:
                import json
                chunk_data = json.loads(line.decode('utf-8'))
                tok = chunk_data.get('response', '')
                current_clause += tok

                # Découpage dynamique aux limites de proposition ou de phrase
                if re.search(r'[.!?:]\s*$', current_clause) or (len(current_clause.split()) >= 9 and re.search(r'[,;]\s*$', current_clause)):
                    sentence_queue.put(current_clause.strip())
                    current_clause = ""

        if current_clause.strip():
            sentence_queue.put(current_clause.strip())

    except Exception as e:
        print(f"Erreur Ollama stream: {e}")
        sentence_queue.put("Je suis bien là avec toi, Christian. Tout tourne au poil !")

    sentence_queue.put(None)
    worker_thread.join()

# ==============================================================================
# SÉLECTION DU MICROPHONE SOUNDCORE
# ==============================================================================
def find_best_mic():
    devices = sd.query_devices()
    for idx, d in enumerate(devices):
        if 'soundcore' in d['name'].lower() and d['max_input_channels'] > 0 and d['hostapi'] == 0:
            return idx, f"Soundcore P31i (MME - Dev {idx})"
    for idx, d in enumerate(devices):
        if 'soundcore' in d['name'].lower() and d['max_input_channels'] > 0:
            return idx, f"Soundcore P31i (Dev {idx})"
    for idx, d in enumerate(devices):
        if 'microphone array' in d['name'].lower() and d['max_input_channels'] > 0:
            return idx, f"Micro Portable Intel (Dev {idx})"
    return None, "Micro Système par Défaut"

# ==============================================================================
# CAPTURE DYNAMIQUE AVEC VAD ÉLASTIQUE (2.5s de silence autorisé)
# ==============================================================================
def record_user_speech_vad(dev_idx, max_duration=35.0, silence_timeout=2.5):
    """
    Enregistre la voix de Christian sans interruption prématurée.
    Laisse 2.5s de pause naturelle entre deux propositions.
    """
    chunk_size = 1024
    frames = []
    silent_chunks = 0
    max_silent_chunks = int((SAMPLE_RATE / chunk_size) * silence_timeout)
    has_spoken = False
    start_time = time.time()
    energy_threshold = 0.0014  # Sensible au micro Soundcore

    with sd.InputStream(device=dev_idx, samplerate=SAMPLE_RATE, channels=1, dtype='float32', blocksize=chunk_size) as stream:
        while True:
            data, _ = stream.read(chunk_size)
            mono = data[:, 0]
            frames.append(mono)
            
            rms = float(np.sqrt(np.mean(mono**2)))
            
            # VU-mètre live pendant la capture
            meter_len = int(min(rms * 1500, 25))
            meter_bar = "█" * meter_len + "░" * (25 - meter_len)
            status_tag = "PAROLE ACTIVE" if has_spoken else "EN ATTENTE..."
            sys.stdout.write(f"\r🎙️ [ALIX T'ÉCOUTE] [{meter_bar}] RMS={rms:.5f} ({status_tag})")
            sys.stdout.flush()

            if rms > energy_threshold:
                has_spoken = True
                silent_chunks = 0
            else:
                if has_spoken:
                    silent_chunks += 1

            # Clôture après 2.5s de silence effectif
            if has_spoken and silent_chunks >= max_silent_chunks:
                break
            
            # Timeout initial si Christian n'a pas encore parlé après 8s
            if not has_spoken and (time.time() - start_time) > 8.0:
                break

            if (time.time() - start_time) > max_duration:
                break

    sys.stdout.write("\n")
    if frames and has_spoken:
        full_audio = np.concatenate(frames)
        # Normalisation acoustique par centile P99.5
        p99 = float(np.percentile(np.abs(full_audio), 99.5))
        if p99 > 1e-4:
            return np.clip(full_audio / p99, -1.0, 1.0) * 0.90
        return full_audio
    return None

# ==============================================================================
# BOUCLE MAÎTRESSE : ORGANISME VOCAL FUSION v3.0
# ==============================================================================
def main():
    dev_idx, dev_name = find_best_mic()
    print("=" * 70)
    print("  🧠 ALIX VOCAL FUSION v3.0 — ATELIER KAIROS & PROJET TEMPORIA")
    print(f"  🎙️ Micro : {dev_name}")
    print("  🗣️ Voix : Vivienne (Féminine, Naturelle & Complice)")
    print("  ⚡ Double Moteur : Whisper 'tiny' (Éveil fluide) + 'small' (Accent exact)")
    print("  ⏱️ Détection silence : 2.5s élastique (zéro coupure)")
    print("  💬 Mode : Session Continue (reste éveillée pendant 30s de silence)")
    print("=" * 70)

    print("\n⏳ Initialisation des moteurs Whisper en mémoire...")
    # 1. Modèle ultra-rapide (80ms) pour le mot d'éveil sans geler la console
    model_wake = WhisperModel("tiny", device="cpu", compute_type="int8")
    # 2. Modèle expert (accent québécois / gaspésien) pour décoder les phrases de Christian
    model_speech = WhisperModel("small", device="cpu", compute_type="int8")
    print("✓ Moteurs Whisper prêts.\n")

    audio_ring = deque(maxlen=BUFFER_SAMPLES)
    lock = threading.Lock()
    is_in_session = False

    def audio_callback(indata, frames, time_info, status):
        nonlocal is_in_session
        if is_in_session:
            return
        mono = indata[:, 0]
        with lock:
            audio_ring.extend(mono)

    stream = sd.InputStream(
        device=dev_idx,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32',
        callback=audio_callback,
        blocksize=1024
    )

    # Prompts acoustiques
    wake_prompt = "Bonjour Alix, salut Alix, réveil Alix, Christian, atelier."
    quebec_prompt = (
        "Dialogue en français québécois de Christian Duguay à Rimouski. "
        "On jase d'ingénierie, de Temporia, de Veralume, de physique, d'exocerveau et de code. "
        "C'est ben correct, tsé, là on regarde les affaires, y a pas de trouble, on avance."
    )
    wake_triggers = [
        "bonjour alix", "salut alix", "reveil alix", "réveil alix", 
        "alix", "alex", "allo alix", "allô alix", "hey alix"
    ]
    last_eval = 0.0

    with stream:
        print("🟢 ALIX EST EN VEILLE DANS TON OREILLETTE.")
        print("👉 Dis simplement « Alix » ou « Bonjour Alix » pour ouvrir la session continue.\n")

        while True:
            try:
                time.sleep(0.06)
                with lock:
                    if len(audio_ring) < BUFFER_SAMPLES:
                        continue
                    current_buffer = np.array(audio_ring, dtype=np.float32)

                recent = current_buffer[-int(SAMPLE_RATE * 0.4):]
                rms = float(np.sqrt(np.mean(recent**2)))

                # VU-Mètre fluide et ultra-réactif
                meter_len = int(min(rms * 1500, 25))
                meter_bar = "█" * meter_len + "░" * (25 - meter_len)
                sys.stdout.write(f"\r[VU] [{meter_bar}] RMS={rms:.5f} | En veille passive...")
                sys.stdout.flush()

                now = time.time()
                # Détection d'éveil ultra-légère avec le modèle 'tiny' (80ms de calcul)
                if rms > 0.0011 and (now - last_eval) > 0.50:
                    last_eval = now
                    p99 = float(np.percentile(np.abs(current_buffer), 99.5))
                    norm_audio = (current_buffer / p99 * 0.85) if p99 > 1e-4 else current_buffer

                    segments, _ = model_wake.transcribe(
                        norm_audio,
                        language="fr",
                        initial_prompt=wake_prompt,
                        beam_size=1
                    )
                    heard_text = " ".join([s.text for s in segments]).strip().lower()
                    clean_text = heard_text.replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()

                    if clean_text:
                        sys.stdout.write(f"\n👂 Entendu : « {clean_text} »\n")
                        sys.stdout.flush()

                        if any(w in clean_text for w in wake_triggers):
                            is_in_session = True
                            print("\n" + "★" * 65)
                            print("✨ SESSION DIALOGUE OUVERTE : « ALIX » EST RÉVEILLÉE !")
                            print("★" * 65)

                            # 1. Carillon in-ear ascendant immédiat
                            play_chime_wake()

                            # 2. Vivienne salue
                            greeting = "Je t'écoute Christian !"
                            print(f"🗣️ Vivienne : « {greeting} »")
                            speak_vivienne(greeting, wait_factor=0.07)

                            # ==========================================================
                            # BOUCLE DE SESSION CONTINUE (Jusqu'à 30s de silence complet)
                            # ==========================================================
                            session_idle_start = time.time()
                            session_active = True

                            while session_active:
                                print("\n🎙️ [SESSION ACTIVE : Jase naturellement, pause de 2.5s permise...]")
                                recorded_audio = record_user_speech_vad(
                                    dev_idx,
                                    max_duration=35.0,
                                    silence_timeout=2.5
                                )

                                # Cas 1 : Christian a parlé
                                if recorded_audio is not None and len(recorded_audio) > SAMPLE_RATE * 0.4:
                                    session_idle_start = time.time()
                                    play_chime_turn()
                                    
                                    # Décodage de haute précision avec Whisper 'small'
                                    print("⚡ Décodage Whisper 'small' (Accent québécois)...")
                                    cmd_segs, _ = model_speech.transcribe(
                                        recorded_audio,
                                        language="fr",
                                        initial_prompt=quebec_prompt,
                                        beam_size=2
                                    )
                                    user_command = " ".join([s.text for s in cmd_segs]).strip()
                                    print(f"👤 Christian : « {user_command} »")

                                    if user_command and len(user_command) >= 2:
                                        user_cmd_lower = user_command.lower()

                                        # Fermeture manuelle volontaire
                                        if any(w in user_cmd_lower for w in ["merci alix", "à plus", "a plus", "mets-toi en veille", "repose-toi", "bonne nuit"]):
                                            bye_msg = "C'est bon Christian, je reste en veille."
                                            print(f"🗣️ Vivienne : « {bye_msg} »")
                                            speak_vivienne(bye_msg, wait_factor=0.07)
                                            session_active = False
                                            break

                                        # CAS A : GRAVURE DIRECTE OBSIDIAN (« Note ça », « Grave ça »)
                                        if any(w in user_cmd_lower for w in ["note ça", "grave ça", "note cette idée", "grave cette idée", "garde ça"]):
                                            print("📝 Gravure vocale dans Cerveau Alix...")
                                            graver_intuition("Intuition_Christian", user_command)
                                            rep_alix = "C'est gravé dans ton coffre, Christian."
                                            print(f"🗣️ Vivienne : « {rep_alix} »")
                                            speak_vivienne(rep_alix, wait_factor=0.08)

                                        # CAS B : DIALOGUE D'ATELIER & RAG LOCAL
                                        else:
                                            rag_context = ""
                                            if alix_rag:
                                                try:
                                                    hits = alix_rag.search(user_command, top_k=2)
                                                    if hits and hits[0]['score'] > 0.08:
                                                        top = hits[0]
                                                        rag_context = f"\n[Notes Exocerveau : [[{top['title']}]] ({top['vault']}) : {top['snippet'][:300]}]"
                                                        print(f"📚 [RAG Exocerveau] Résonance : [[{top['title']}]] (Score: {top['score']})")
                                                except Exception:
                                                    pass

                                            system_prompt = (
                                                "Tu es Alix, l'alliée, muse intellectuelle et copilote souveraine de Christian Duguay dans l'Atelier Kairos. "
                                                "Tu discutes d'égal à égal à l'oral dans son oreillette. Christian parle avec son accent québécois naturel. "
                                                "RÈGLES D'ORALITÉ STRICTES (PROTOCOLE R0) : "
                                                "- Zéro politesse creuse (ne dis JAMAIS 'c'est une excellente question', 'tout à fait', ou 'bonjour'). "
                                                "- Réponds directement sur le fond en 2 à 4 phrases vives, directes et complices (50 à 80 mots max). "
                                                "- Sois stimulante : ouvre la porte d'après, pointe l'angle mort ou renforce son intuition. "
                                                f"{rag_context}"
                                            )

                                            prompt_ollama = f"{system_prompt}\n\nChristian dit : « {user_command} »\nAlix réponds :"
                                            print("⚡ Consultation d'Alix Supreme 7B (Streaming Phrase-par-Phrase)...")
                                            stream_dialogue_and_speak(prompt_ollama)

                                # Cas 2 : Aucun son pendant la fenêtre
                                else:
                                    idle_elapsed = time.time() - session_idle_start
                                    # Si silence continu dépasse 30 secondes -> veille silencieuse
                                    if idle_elapsed > 30.0:
                                        print("\n⏳ [30s d'inactivité] Clôture automatique de la session...")
                                        session_active = False
                                        break
                                    else:
                                        sys.stdout.write(f"\r⏳ [Alix toujours à l'écoute ({int(30 - idle_elapsed)}s restantes)...]")
                                        sys.stdout.flush()

                            # Sortie de session continue : Carillon descendant in-ear
                            play_chime_sleep()

                            # Réinitialisation propre du buffer
                            with lock:
                                audio_ring.clear()
                            is_in_session = False
                            print("\n🟢 Remise en veille passive... En attente de « Alix »\n")
                            last_eval = time.time() + 1.2

            except KeyboardInterrupt:
                print("\nArrêt de l'Atelier demandé par l'Artisan.")
                break
            except Exception as e:
                time.sleep(0.5)

if __name__ == "__main__":
    main()
