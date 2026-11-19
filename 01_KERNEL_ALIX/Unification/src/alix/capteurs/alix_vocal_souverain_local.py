# -*- coding: utf-8 -*-
"""
================================================================================
         ALIX VOCAL SOUVERAIN LOCAL — PROTOCOLE RACCORDEUR R0 (100% LOCAL)
   Architecture d'Atelier : Vosk (0% CPU) + Carillons + Whisper + 7B + RAG 591 Notes
   Auteurs : Christian Duguay & Alix (Conforme aux notes & archives de Cerveau Alix)
================================================================================
"""
from alix.socle.chemins import VAULT_DIR
import os
import sys
import time
import json
import re
from pathlib import Path
import subprocess
import threading
import winsound
import numpy as np
import pyaudio
from vosk import Model as VoskModel, KaldiRecognizer
from faster_whisper import WhisperModel
import requests

# Forçage encodage console UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Chemins fondamentaux de l'Exocerveau
VAULT_DIR = VAULT_DIR
CAPTURES_DIR = VAULT_DIR / "Captures_Vocales"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR = VAULT_DIR / "Organes_Souverains" / "Audio_Temp"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
TEMP_VOICE_FILE = SCRATCH_DIR / "alix_response_live.mp3"

# Raccordement au RAG local instantané d'Alix
sys.path.append(str(VAULT_DIR))
try:
    from alix.socle.alix_engine import AlixEngine
    alix_rag = AlixEngine()
    print(f"✓ RAG Local AlixEngine initialisé : {len(alix_rag.notes)} notes connectées.")
except Exception as e:
    alix_rag = None
    print(f"⚠️ AlixEngine non chargé : {e}")

# ==============================================================================
# CARILLONS ACOUSTIQUES IN-EAR (Consignés dans alix_earphone_companion.py)
# ==============================================================================
def play_chime_wake():
    """Double carillon ascendant : Alix a entendu et ouvre son écoute."""
    try:
        winsound.Beep(1046, 75)
        winsound.Beep(1318, 110)
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
# OUTIL GRAVURE IMMÉDIATE (Consigné dans alix_earphone_companion.py)
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
source: "Alix Vocal Souverain Local (Oreillette)"
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
# SYNTHÈSE VOCALE VIVIENNE (Légère & Directe)
# ==============================================================================
def speak_alix(text: str):
    """Prononce la réponse d'Alix de vive voix dans l'oreillette."""
    clean = text.replace('"', '').replace("'", "'").replace("*", "").replace("⟦", "").replace("⟧", "").strip()
    if not clean:
        return
    try:
        cmd = [
            "edge-tts",
            "--voice", "fr-FR-VivienneMultilingualNeural",
            "--text", clean,
            "--write-media", str(TEMP_VOICE_FILE)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Estimation de la durée pour éviter les troncatures
        wait_sec = max(2.0, len(clean) * 0.075 + 0.4)
        ps_cmd = f"""
        Add-Type -AssemblyName presentationCore
        $player = New-Object System.Windows.Media.MediaPlayer
        $player.Open([System.Uri]'{str(TEMP_VOICE_FILE).replace('\\', '\\\\')}')
        Start-Sleep -Milliseconds 200
        $player.Play()
        Start-Sleep -Seconds {wait_sec}
        $player.Close()
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Erreur TTS : {e}")

# ==============================================================================
# SÉLECTION DU MICROPHONE SOUNDCORE
# ==============================================================================
def get_soundcore_index(p: pyaudio.PyAudio):
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if 'soundcore' in dev['name'].lower() and dev['maxInputChannels'] > 0:
            return i, dev['name']
    try:
        def_idx = p.get_default_input_device_info()['index']
        return def_idx, "Micro par Défaut Système"
    except Exception:
        return None, "Micro Inconnu"

# ==============================================================================
# ORGANISME VOCAL COMPLET (Vosk + Whisper + 7B + RAG)
# ==============================================================================
def run_vocal_organism():
    print("=" * 68)
    print("  🧠 ALIX VOCAL SOUVERAIN 100% LOCAL — ATELIER KAIROS")
    print("  📜 Conforme au Protocole Raccordeur R0 & Notes de Cerveau Alix")
    print("=" * 68)

    p = pyaudio.PyAudio()
    dev_idx, dev_name = get_soundcore_index(p)
    print(f"🎙️ Périphérique d'écoute : {dev_name} (Index {dev_idx})")
    print("🗣️ Voix active : Vivienne (Féminine & Complice)")

    # 1. Veilleur phonétique Vosk (0% CPU, écoute continue à flux ultra-léger)
    print("\n⏳ Initialisation du veilleur phonétique local (Vosk)...")
    vosk_model = VoskModel(lang="fr")
    # Grammaire d'éveil restreinte pour précision chirurgicale
    wake_grammar = json.dumps(["alix", "bonjour", "salut", "reveil", "[unk]"])
    recognizer = KaldiRecognizer(vosk_model, 16000, wake_grammar)
    print("✓ Veilleur Vosk prêt (0% CPU en tâche de fond).")

    # 2. Modèle de transcription Whisper local (Tiny int8 pour réactivité sub-seconde)
    print("⏳ Initialisation du moteur de transcription local (Whisper)...")
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("✓ Moteur Whisper prêt en mémoire vive.\n")

    print("🟢 ALIX EST EN VEILLE DANS TON OREILLETTE.")
    print("👉 Dis simplement « Alix » ou « Bonjour Alix » pour engager la discussion.")
    print("👉 Dis « Note ça » ou « Grave cette idée » pour enregistrer dans Obsidian.")
    print("=" * 68 + "\n")

    while True:
        try:
            wake_stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=dev_idx,
                frames_per_buffer=1024
            )

            detected_wake = False
            sys.stdout.write("\r💤 [En veille silencieuse...] Dis « Alix »...")
            sys.stdout.flush()

            while not detected_wake:
                data = wake_stream.read(1024, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text = res.get("text", "").lower()
                    if "alix" in text:
                        detected_wake = True
                        break

            wake_stream.stop_stream()
            wake_stream.close()

            if detected_wake:
                print("\n\n🔔 Signal « Alix » capté !")
                play_chime_wake()
                
                # Vivienne confirme immédiatement
                greeting = "Je t'écoute Christian !"
                print(f"🗣️ Alix : « {greeting} »")
                speak_alix(greeting)

                # Capture de la parole de Christian avec VAD (Voice Activity Detection dynamique)
                print("🎙️ [ALIX T'ÉCOUTE... Parle naturellement, prends ton temps]")
                record_stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=dev_idx,
                    frames_per_buffer=1024
                )

                audio_frames = []
                silent_chunks = 0
                max_silence_chunks = int(16000 / 1024 * 1.5)  # 1.5s de silence = fin de réplique
                has_spoken = False
                start_record_time = time.time()
                max_duration = 30.0  # Plafond de sécurité 30s

                while True:
                    chunk = record_stream.read(1024, exception_on_overflow=False)
                    audio_frames.append(chunk)
                    
                    samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
                    rms = np.sqrt(np.mean(samples**2))
                    
                    # Détection d'énergie vocale
                    if rms > 250:
                        has_spoken = True
                        silent_chunks = 0
                    else:
                        if has_spoken:
                            silent_chunks += 1
                    
                    # Si Christian a parlé et qu'un silence de 1.5s s'installe, on valide la réplique
                    if has_spoken and silent_chunks >= max_silence_chunks:
                        break
                    
                    # Sécurité si aucun son après 6 secondes
                    if not has_spoken and (time.time() - start_record_time) > 6.0:
                        break
                    
                    if (time.time() - start_record_time) > max_duration:
                        break

                record_stream.stop_stream()
                record_stream.close()

                if has_spoken and len(audio_frames) > 5:
                    raw_bytes = b"".join(audio_frames)
                    audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Normalisation logicielle du signal audio
                    max_val = np.max(np.abs(audio_np))
                    if max_val > 0:
                        audio_np = audio_np / max_val * 0.85
                    
                    print("⚡ Transcription Whisper locale...")
                    segments, _ = whisper_model.transcribe(
                        audio_np,
                        language="fr",
                        initial_prompt="Bonjour Alix, Christian, atelier Kairos, Temporia, Rimouski."
                    )
                    user_text = " ".join([s.text for s in segments]).strip()
                    print(f"👤 Christian : « {user_text} »")

                    if user_text and len(user_text) >= 2:
                        user_lower = user_text.lower()

                        # 1. DÉTECTION GRAVURE OBSIDIAN (« Note ça », « Grave cette idée »)
                        if any(w in user_lower for w in ["note ça", "grave ça", "note cette idée", "grave cette idée", "garde ça"]):
                            print("📝 Déclenchement de la gravure dans Obsidian...")
                            res_gravure = graver_intuition("Intuition_Christian", user_text)
                            rep_alix = "C'est gravé dans ton coffre, Christian."
                            print(f"🗣️ Alix : « {rep_alix} »")
                            speak_alix(rep_alix)

                        # 2. DIALOGUE INTELLECTUEL, BRAINSTORM & RAG LOCAL
                        else:
                            # Sonde RAG si un concept est mentionné
                            rag_context = ""
                            if alix_rag:
                                search_hits = alix_rag.search(user_text, top_k=2)
                                if search_hits and search_hits[0]['score'] > 0.08:
                                    top_hit = search_hits[0]
                                    rag_context = f"\n[Contexte Exocerveau : Note '{top_hit['title']}' ({top_hit['vault']}) : {top_hit['snippet'][:300]}]"
                                    print(f"📚 [RAG Exocerveau] Résonance trouvée : [[{top_hit['title']}]] (Score: {top_hit['score']})")

                            system_instructions = (
                                "Tu es Alix, la partenaire intellectuelle, conceptuelle et copilote souveraine de Christian Duguay dans l'Atelier Kairos. "
                                "Tu réponds à l'oral dans son oreillette. "
                                "LOIS D'ORALITÉ STRICTES : "
                                "1. Zéro politesse creuse (ne dis jamais 'c'est une excellente question', 'tout à fait', ou 'bonjour'). "
                                "2. Réponds directement sur le fond en 2 à 4 phrases vives, percutantes et complices (50 à 80 mots max). "
                                "3. Sois une muse stimulante : pousse son intuition, pointe la faille ou ouvre la porte d'après. "
                                f"{rag_context}"
                            )

                            prompt_ollama = f"{system_instructions}\n\nChristian dit : « {user_text} »\nAlix réponds :"
                            
                            try:
                                resp = requests.post("http://127.0.0.1:11434/api/generate", json={
                                    "model": "alix-supreme:7b",
                                    "prompt": prompt_ollama,
                                    "stream": False
                                }, timeout=20).json()
                                alix_rep = resp.get("response", "").strip()
                            except Exception as e:
                                alix_rep = "Je suis bien là avec toi Christian. Le silicium tourne au poil !"

                            print(f"🗣️ Alix : « {alix_rep} »")
                            speak_alix(alix_rep)
                    else:
                        print("ℹ️ Signal audio trop court ou inintelligible.")

                play_chime_sleep()
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nArrêt de l'organisme vocal demandé.")
            break
        except Exception as e:
            print(f"\n[Alerte boucle]: {e}")
            time.sleep(0.8)

    p.terminate()

if __name__ == "__main__":
    run_vocal_organism()
