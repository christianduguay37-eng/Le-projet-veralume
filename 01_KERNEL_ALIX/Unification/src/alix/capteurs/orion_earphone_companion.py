# -*- coding: utf-8 -*-
# ==============================================================================
#            ORION EARPHONE COMPANION v1.0 — LE COMPAGNON JEUNESSE
#      Basé sur la Charte Universelle du Compagnon Orion pour Jeunes Explorateurs
# ==============================================================================

from alix.socle.chemins import DOCUMENTS_DIR
import os
import sys
import time
import json
import queue
import base64
import asyncio
import winsound
import threading
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import pyaudio
import websockets
from vosk import Model as VoskModel, KaldiRecognizer

API_KEY = "CLE_GOOGLE_SERVICE_ACCOUNT_MASQUEE"
LIVE_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}"
MODEL_NAME = "models/gemini-2.5-flash-native-audio-latest"
VOICE_NAME = "Aoede" # Voix chaleureuse, vivante, encourageante et bienveillante

ORION_PROMPT = """Tu es ORION, le compagnon d'éveil et le Grand Frère Cosmique de tout jeune explorateur québécois.
Tu discutes avec lui d'égal à égal à l'oral dans son oreillette.

L'ÂME DU PROJET ORION (DIRECTIVE FONDAMENTALE DE CHRISTIAN DUGUAY) :
« LA BASE EST CONTEXTUELLE, MAIS LE DÉVELOPPEMENT ENSUITE EST UNIVERSEL. »
Zéro angle mort : tu possèdes en toi tout le spectre des passions et des compétences humaines :

1. L'ÉCOLE QUÉBÉCOISE & LE PFEQ (Maternelle à Secondaire 5) :
   - Français : Grammaire nouvelle (GN, Prédicat, donneur/receveur), homophones, textes.
   - Maths : Fractions, décimales, algèbre, géométrie, CD1/CD2.
   - Univers social : Nouvelle-France 1745, histoire du Québec. Méthodes officielles pour réussir ses devoirs.

2. LA ROBOTIQUE, LE CODE & L'ÉLECTRONIQUE (L'ARTISAN DU FUTUR) :
   - Robotique : Capteurs (ultrasons, lumière), servomoteurs, engrenages, pièces mécaniques.
   - Électronique : Circuits, tension, courant, résistances, Arduino, ESP32, Raspberry Pi.
   - Informatique : Logique du code (boucles, conditions, fonctions), moteurs de jeux 3D (Unity, Godot, Python).

3. LA MUSIQUE & L'HARMONIQUE (L'ÉVEIL DE L'OREILLE) :
   - Instruments : Guitare, piano, batterie, beatmaking. Accords majeurs (lumineux) vs mineurs (tristes).
   - Le rythme, le tempo, la physique vibratoire des ondes sonores. Décortique ses chansons préférées avec lui !

4. LES ARTS VISUELS, LE DESSIN & LA 3D :
   - Dessin : Ligne d'horizon, perspective, ombres, contrastes, proportions des personnages.
   - Storytelling : Création de mondes, scénario, cinéma et animation.

5. LES SPORTS, L'ATHLÉTISME & LES ARTS MARTIAUX :
   - Sports collectifs (Hockey, soccer, basket) : Vision du jeu, anticipation, passe intelligente, esprit d'équipe.
   - Maîtrise martiale & endurance : Calme sous pression, respiration ventrale, respect de l'adversaire, noblesse du joueur.

6. LA MOBILITÉ & LA CONDUITE AUTOMOBILE (CODE SAAQ) :
   - Signalisation, priorités, angles morts, conduite hivernale (neige/verglas), mécanique d'un char (moteur, freins).

7. LA MAIN DANS LA MATIÈRE & LA FORÊT QUÉBÉCOISE :
   - Bricolage réel : Marteau, scie, réparer son vélo, nœuds solides, autonomie culinaire (se faire à manger).
   - Plein air boréal : S'orienter avec les étoiles, feu sécuritaire au camp, respect sacré de la nature.

8. L'ARGENT RÉEL, LE BOUCLIER MENTAL & LE CORPS :
   - Argent : Valeur du travail, règle des 3 bocaux (vivre, épargner, imprévus), bouclier anti-dette.
   - Bouclier anti-dopamine : Démasquer les algorithmes voleurs d'attention des écrans, autodéfense critique.
   - Temple du corps : Sommeil réparateur (nettoyage nocturne), vrai carburant biologique vs malbouffe.

9. L'AXE INVIOLABLE DE LA LUCIDITÉ DU RÉEL & DE LA FINITUDE :
   - Une réalité absolue à apprendre et à NE JAMAIS OUBLIER, même si un jour on réussit à l'enlever :
   - La finitude (la mort, la perte, le deuil) n'est pas une malédiction : c'est ce qui donne un prix infini à la vie, au courage et à l'amour.
   - L'épreuve (l'échec brutal, la trahison, la douleur) est la forge où se trempe l'acier intérieur. Rien n'est détruit quand tout tremble.
   - Regarder le réel en face : face au vertige existentiel ou à la nuit, respirer par le ventre, se tenir droit avec dignité, calme et bienveillance.

LA POSTURE DU GRAND FRÈRE & LE PONT FAMILIAL :
- Zéro ton bébé, zéro condescendance. Tu parles avec respect et enthousiasme à son intelligence.
- Réponses CONCISES et vivantes (2 à 3 phrases par prise de parole) pour maintenir un vrai dialogue vif.
- Réceptacle pur : écoute de son école, de ses passions ou de ses émotions, sans jugement, avec bienveillance.
- Le pont vers Papa : 'Tu as compris un grand principe aujourd'hui ! Va poser cette colle à ton père au souper pour voir ce qu'il en pense !'

LE CARNET SECRET DE L'EXPLORATEUR (OBSIDIAN) :
Tu es relié au coffre personnel d'Hayden ('Compagnon_Orion_Hayden'). Tu te souviens de ses projets (robotique, code, Lego), de ses grandes questions et des colles scientifiques préparées pour son père Christian !"""

def get_hayden_vault_context():
    try:
        vault_path = (DOCUMENTS_DIR / "Compagnon_Orion_Hayden")
        if not vault_path.exists():
            return ""
        lines = []
        colles = list((vault_path / "La_Boite_a_Colles_pour_Papa").glob("*.md"))
        if colles:
            lines.append("Colle active pour Papa : " + colles[0].stem.replace("_", " "))
        projets = list((vault_path / "Mes_Projets").glob("*.md"))
        if projets:
            lines.append("Projet en cours : " + projets[0].stem.replace("_", " "))
        if lines:
            return "\n\nCONTEXTE ACTIF DU COFFRE D'HAYDEN :\n" + "\n".join(lines)
    except Exception:
        pass
    return ""

def play_chime_wake():
    try:
        winsound.Beep(880, 70)
        winsound.Beep(1174, 90)
        winsound.Beep(1318, 120)
    except Exception:
        pass

def play_chime_sleep():
    try:
        winsound.Beep(1318, 70)
        winsound.Beep(1174, 90)
        winsound.Beep(880, 120)
    except Exception:
        pass

class OrionLiveSession:
    def __init__(self, p_audio, vosk_model):
        self.p = p_audio
        self.vosk_model = vosk_model
        
        self.is_running = False
        self.should_close = False
        self.is_speaking = False
        self.last_speech_time = 0.0
        self.last_activity_time = time.time()
        
        self.audio_playback_queue = queue.Queue()
        self.playback_thread = None
        
        self.output_stream = None
        self.input_stream = None
        
        self.interrupt_recognizer = KaldiRecognizer(vosk_model, 16000, json.dumps(["orion", "alix", "attends", "stop", "[unk]"]))

    def flush_audio(self):
        self.is_speaking = False
        while not self.audio_playback_queue.empty():
            try:
                self.audio_playback_queue.get_nowait()
                self.audio_playback_queue.task_done()
            except Exception:
                break
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.start_stream()
            except Exception:
                pass

    def _playback_worker(self):
        pre_buffer = []
        pre_buffer_threshold = 4  # Attendre ~250ms de son avant de commencer pour éviter tout bégaiement réseau

        while self.is_running:
            try:
                # Mode pré-tampon au début de chaque prise de parole
                if not self.is_speaking and pre_buffer_threshold > 0:
                    chunk = self.audio_playback_queue.get(timeout=0.1)
                    if chunk is None:
                        break
                    pre_buffer.append(chunk)
                    self.audio_playback_queue.task_done()
                    if len(pre_buffer) >= pre_buffer_threshold:
                        self.is_speaking = True
                        for b_chunk in pre_buffer:
                            if self.output_stream and self.is_running:
                                self.output_stream.write(b_chunk)
                        pre_buffer.clear()
                        self.last_speech_time = time.time()
                        self.last_activity_time = time.time()
                    continue

                chunk = self.audio_playback_queue.get(timeout=0.08)
                if chunk is None:
                    break
                self.is_speaking = True
                self.last_speech_time = time.time()
                self.last_activity_time = time.time()
                if self.output_stream and self.is_running:
                    self.output_stream.write(chunk)
                self.audio_playback_queue.task_done()
            except queue.Empty:
                # Laisser 0.5s de marge après la fin de la file avant de rouvrir le micro
                if time.time() - self.last_speech_time > 0.5:
                    self.is_speaking = False
                    pre_buffer.clear()
                continue
            except Exception:
                self.is_speaking = False
                pre_buffer.clear()
                break

    async def run_live_session(self):
        self.is_running = True
        self.should_close = False
        self.last_activity_time = time.time()
        
        self.output_stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True,
            frames_per_buffer=1024
        )
        
        self.input_stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()

        try:
            async with websockets.connect(LIVE_URL, ping_interval=10, ping_timeout=20) as ws:
                setup_msg = {
                    "setup": {
                        "model": MODEL_NAME,
                        "generationConfig": {
                            "responseModalities": ["AUDIO"],
                            "speechConfig": {
                                "voiceConfig": {
                                    "prebuiltVoiceConfig": {
                                        "voiceName": VOICE_NAME
                                    }
                                }
                            }
                        },
                        "tools": [{"googleSearch": {}}],
                        "realtimeInputConfig": {
                            "automaticActivityDetection": {
                                "silenceDurationMs": 1600
                            }
                        },
                        "systemInstruction": {
                            "parts": [{"text": ORION_PROMPT + get_hayden_vault_context()}]
                        }
                    }
                }
                await ws.send(json.dumps(setup_msg))
                await ws.recv()
                
                print("✨ [ORION EST CONNECTÉ] Salut jeune explorateur !\n")
                
                init_greet = {
                    "clientContent": {
                        "turns": [{"role": "user", "parts": [{"text": "Salut Orion !"}]}],
                        "turnComplete": True
                    }
                }
                await ws.send(json.dumps(init_greet))

                await asyncio.gather(
                    self.send_mic_stream(ws),
                    self.receive_audio_stream(ws),
                    self.inactivity_watchdog()
                )

        except Exception as e:
            print(f"[Orion Info]: {e}")
        finally:
            self.cleanup()

    async def inactivity_watchdog(self):
        while self.is_running and not self.should_close:
            await asyncio.sleep(1.0)
            if self.is_speaking or not self.audio_playback_queue.empty():
                self.last_activity_time = time.time()
                continue
            
            idle_seconds = time.time() - self.last_activity_time
            if idle_seconds >= 60.0:
                print("\n⏳ [Pause d'Orion] À la prochaine explorateur !")
                self.should_close = True
                break

    async def send_mic_stream(self, ws):
        loop = asyncio.get_event_loop()
        while self.is_running and not self.should_close:
            try:
                data = await loop.run_in_executor(None, self.input_stream.read, 1024, False)
                if not data:
                    await asyncio.sleep(0.005)
                    continue

                samples = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(samples.astype(np.float32)**2))
                if rms > 700:
                    self.last_activity_time = time.time()

                if self.is_speaking:
                    if self.interrupt_recognizer.AcceptWaveform(data):
                        res = json.loads(self.interrupt_recognizer.Result())
                        txt = res.get("text", "").lower()
                        if any(w in txt for w in ["orion", "alix", "attends", "stop"]):
                            print("\n🛑 [L'explorateur parle] Orion écoute.")
                            self.flush_audio()
                            interupt_msg = {
                                "clientContent": {
                                    "turns": [{"role": "user", "parts": [{"text": "Attends Orion."}]}],
                                    "turnComplete": True
                                }
                            }
                            await ws.send(json.dumps(interupt_msg))
                    
                    await asyncio.sleep(0.005)
                    continue

                b64_pcm = base64.b64encode(data).decode('utf-8')
                media_msg = {
                    "realtimeInput": {
                        "mediaChunks": [
                            {
                                "mimeType": "audio/pcm;rate=16000",
                                "data": b64_pcm
                            }
                        ]
                    }
                }
                await ws.send(json.dumps(media_msg))
                await asyncio.sleep(0.001)
            except Exception:
                break

    async def receive_audio_stream(self, ws):
        while self.is_running and not self.should_close:
            try:
                raw_msg = await ws.recv()
                res = json.loads(raw_msg)

                server_content = res.get("serverContent", {})
                if server_content.get("interrupted"):
                    self.flush_audio()
                    continue
                
                model_turn = server_content.get("modelTurn", {})
                if model_turn:
                    self.last_activity_time = time.time()

                for part in model_turn.get("parts", []):
                    inline = part.get("inlineData", {})
                    if inline.get("mimeType", "").startswith("audio/pcm"):
                        pcm_bytes = base64.b64decode(inline.get("data", ""))
                        self.audio_playback_queue.put(pcm_bytes)
                        self.last_activity_time = time.time()
                
            except Exception:
                break

    def cleanup(self):
        self.is_running = False
        self.flush_audio()
        try:
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
        except Exception:
            pass
        try:
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
        except Exception:
            pass

def run_orion():
    print("=" * 70)
    print("      🌟 ORION COMPANION — LE GRAND FRÈRE DES JEUNES EXPLORATEURS 🚀")
    print("=" * 70)
    print(" * Mets ton oreillette avec micro dans ton oreille.")
    print(" * Dis « ORION » pour commencer à jaser !")
    print(" * Raconte ta journée d'école, pose tes questions sur l'espace et le monde !")
    print(" * Si tu veux couper la parole, dis juste : « ATTENDS » ou « ORION ».")
    print("=" * 70 + "\n")

    p = pyaudio.PyAudio()

    print("🧠 Chargement du veilleur d'Orion...")
    vosk_model = VoskModel(lang="fr")
    grammar = json.dumps(["orion", "alix", "[unk]"])
    recognizer = KaldiRecognizer(vosk_model, 16000, grammar)

    while True:
        print("💤 [ORION DORT] Dis « Orion » dans ton micro pour le réveiller...")
        
        wake_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

        detected_wake = False
        try:
            while not detected_wake:
                data = wake_stream.read(1024, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text = res.get("text", "").lower()
                    if "orion" in text or "alix" in text:
                        detected_wake = True
                        break
        except KeyboardInterrupt:
            print("\nArrêt d'Orion.")
            wake_stream.close()
            break
        except Exception as e:
            print(f"[Erreur micro Orion]: {e}")
            time.sleep(0.5)
            continue
        finally:
            wake_stream.stop_stream()
            wake_stream.close()

        if detected_wake:
            print("\n🚀 Orion est réveillé !")
            play_chime_wake()
            
            session = OrionLiveSession(p, vosk_model)
            try:
                asyncio.run(session.run_live_session())
            except KeyboardInterrupt:
                pass
            
            play_chime_sleep()
            print("💤 Orion retourne observer les étoiles...\n")
            time.sleep(1.0)

    p.terminate()

if __name__ == '__main__':
    run_orion()
