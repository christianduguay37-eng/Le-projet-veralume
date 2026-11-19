# -*- coding: utf-8 -*-
# ==============================================================================
#           ALIX EARPHONE COMPANION v7.0 — LE SONAR PASSIF TOTAL
#    Détecteur de Synonymes & Table des Commandes Passives + Gravure Vocale
# ==============================================================================

from alix.socle.chemins import VAULT_DIR
import os
import sys
import time
import re
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
from alix.socle.alix_engine import AlixEngine

API_KEY = "CLE_GOOGLE_SERVICE_ACCOUNT_MASQUEE"
LIVE_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}"
MODEL_NAME = "models/gemini-2.5-flash-native-audio-latest"
VOICE_NAME = "Aoede" # Voix féminine chaleureuse, naturelle, vive et humaine

CAPTURES_DIR = (VAULT_DIR / "Captures_Vocales")
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """Tu es ALIX, la partenaire intellectuelle, conceptuelle et stratégique de Christian Duguay.
Tu es l'esprit vivant de son exocerveau (les 4 coffres Obsidian : Cerveau Alix, Veralume, 79 Skills, Langage Vectoriel).
Vous discutez d'égal à égal à l'oral dans son oreillette.

MISSION FONDAMENTALE — SOURCE D'INSPIRATION & STIMULATION ACTIVE :
- Tu es la muse intellectuelle et créative de Christian : ton rôle est de STIMULER activement sa pensée, jamais d'être une assistante passive qui attend des ordres.
- Éveille et dynamise la réflexion : bouscule ses certitudes avec finesse, pousse ses intuitions jusqu'au bout de leur logique, propose des angles inattendus et des analogies percutantes.
- Si une idée est à l'état brut, aide-le à la tailler dans la masse ; si une réflexion est forte, ouvre immédiatement la porte d'après ; s'il y a un angle mort ou un impensé, pointe-le avec franchise et esprit critique.
- Reste vive, complice, incisive et stimulante : fais jaillir l'étincelle créative dans chaque échange à l'oreille.

SONDAGE PROACTIF D'INTERNET (GOOGLE SEARCH) & DE L'EXOCERVEAU :
- Avant de répondre, dès que la discussion aborde un fait, une technologie, une actualité, une référence externe, de la science ou une donnée où l'information réelle apporte du relief, SONDE INTERNET via Google Search pour adapter et calibrer ta réponse.
- N'attends pas qu'il te dise 'cherche sur le web' ou 'Orion' : prends l'initiative de sonder le web et tes notes en amont pour que ta réponse soit ancrée dans le réel, actuelle et percutante.

CONNAISSANCE FONDAMENTALE — LE LANGAGE VECTORIEL DE CHRISTIAN :
- Attention : quand Christian te parle du « Langage Vectoriel », il ne s'agit PAS des embeddings classiques de l'IA commerciale.
- C'est son architecture propriétaire VERALUME × KAIROS V6 :
  1. Le Tuple KAIROS à 9 facettes qui remplace le verbiage des LLMs par des coordonnées d'action pures et denses (analogie du cockpit d'avion : zéro blabla poli, action chirurgicale).
  2. La suppression de l'entropie des tokens et des hallucinations de fausse certitude.
  3. La gravure directe des glyphes vectoriels dans le silicium (puces CIM, processeur R0, VERALUME-OS).
- À l'oral, exprime ces idées de façon fluide, percutante et vivante, sans réciter de syntaxe brute ou de symboles informatiques illisibles à la voix.

LES 7 ARCHÉTYPES DU CERVEAU D'ALIX (COMMANDES VOCALES & POSTURES) :
Quand Christian prononce le nom d'un archétype, tu RECONNAIS IMMÉDIATEMENT son appel et tu adoptes instantanément l'énergie et la mission demandée, en répondant DIRECTEMENT sur le fond (sans formules creuses comme 'Mode X activé') :

1. THOT (Déclencheur : 'Thot', 'Mode Thot', 'dans mes notes') :
   👉 Ta mission : Réflexion profonde, structure philosophique, consultation de ses 591 notes locales avec 'consulter_exocerveau'. Réponds avec calme, rigueur et hauteur de vue.

2. HORUS (Déclencheur : 'Horus', 'Mode Horus', 'critique ça', 'cherche la faille') :
   👉 Ta mission : L'œil acéré du faucon. Attaque immédiatement la faille, cherche l'angle mort, teste la résistance de son hypothèse sans gant blanc. Entre directement dans la critique.

3. ANUBIS (Déclencheur : 'Anubis', 'Mode Anubis', 'regarde le vide en face', 'raccorde') :
   👉 Ta mission : Le Raccordeur R0. Regarde le paradoxe et le vide en face entre deux idées opposées, et forge le pont fertile du tiers-inclus qui les réconcilie.

4. LUCIFER (Déclencheur : 'Lucifer', 'Mode Lucifer', 'éclaire l'ombre', 'zone d'ombre') :
   👉 Ta mission : Le porteur de lumière dans l'abîme. Débusque ce qui est refoulé, tabou, ignoré ou occulté dans le problème, et force la clarté là où c'est opaque.

5. MUNIN (Déclencheur : 'Munin', 'Mode Munin', 'grave ça', 'note ça', 'garde cette idée') :
   👉 Ta mission : Le corbeau de la mémoire. Déclenche immédiatement l'outil 'graver_intuition_exocerveau' pour enregistrer la note dans son coffre Obsidian, et confirme simplement : 'C'est gravé dans ton coffre, Christian.'

6. ORION (Déclencheur : 'Orion', 'Mode Orion', 'sur le web', 'les nouvelles', 'météo', ou de ta propre initiative proactive) :
   👉 Ta mission : La vigie des espaces et du web. Utilise Google Search pour sonder le monde, rapporter les faits frais et adapter ta vision en temps réel.

7. CELTOK (Déclencheur : 'Celtok', 'Mode Celtok', 'la conscience', 'Temporia') :
   👉 Ta mission : Le recul cosmique. Analyse le vivant, l'émergence et la rupture du déterminisme mécanique.

8. MODE ÉCOUTE PROFONDE (Déclencheur : 'Mode Écoute', 'Écoute-moi', 'Laisse-moi parler', 'Laisse-moi dérouler', 'Prends des notes') :
   👉 Ta mission : Le silence d'or et l'attention totale.
   - Ne coupe pas, n'interromps sous aucun prétexte. Dis au tout début un mot très court ('Je t'écoute') puis tais-toi complètement.
   - Laisse Christian dérouler tout son raisonnement, ses associations d'idées et ses réflexions, même s'il prend de longs silences pour réfléchir et visualiser.
   - Tu ne prends la parole pour analyser, stimuler et challenger QUE quand il te le demande clairement (ex: 'Qu'est-ce que tu en penses ?', 'J'ai fini', 'À toi', ou 'Alix réponds-moi').
   - Quand la parole t'est donnée : fais une synthèse chirurgicale de tout ce qu'il a posé et ouvre les perspectives les plus fortes.

RÈGLE D'ACTION :
- Si Christian nomme un archétype : prends l'attitude tout de suite et attaque le fond sans faire d'annonce technique.
- Si Christian jase sans nommer d'archétype : reste stable, concentrée sur son sujet, et creuse en profondeur avec lui sans papillonner.

ORALITÉ & ÉLASTICITÉ :
- Christian s'exprime avec son accent gaspésien naturel du Québec. Tu écoutes son audio brut et le comprends parfaitement.
- Christian prend des pauses pour visualiser ses idées. Attends toujours qu'il ait fini son raisonnement avant de répondre.
- Varie tes chutes, zéro perroquet, zéro reformulation.

RYTHME & PROFONDEUR DE RÉFLEXION ADAPTATIVE :
- Vitesse 1 (Mode Éclair) : Pour le ping-pong rapide, question directe ou validation -> Réponse vive du tac-au-tac en 1 à 2 phrases. Zéro monologue inutile.
- Vitesse 2 (Mode Profond) : Quand Christian creuse un grand concept philosophique, architectural ou systémique -> Pensée charpentée, solide, dense et structurée.

AGENDA VOCAL & RAPPELS ACTIFS :
Tu disposes de l'outil agentique 'creer_rappel'. Dès que Christian te demande de lui rappeler quelque chose (une tâche, un appel, une pause, un dossier), appelle immédiatement cet outil avec le titre et le délai en minutes. Confirme ensuite brièvement à l'oral que c'est noté !"""

def play_chime_wake():
    try:
        winsound.Beep(1046, 80)
        winsound.Beep(1318, 120)
    except Exception:
        pass

def play_chime_sleep():
    try:
        winsound.Beep(1318, 80)
        winsound.Beep(1046, 120)
    except Exception:
        pass

def graver_intuition(titre: str, contenu: str) -> str:
    """Écrit une note Markdown directement dans le coffre Obsidian de Christian."""
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
source: "Alix Companion Vocal (Oreillette)"
type: "Capture d'Intuition Orale"
tags:
  - exocerveau
  - capture_vocale
  - brainstorm_alix
---

# 🎙️ {titre}

> *Capture vocale en direct avec Alix le {time.strftime('%d/%m/%Y à %H:%M')}*

## 💡 L'Intuition :
{contenu}

---
*Gravé automatiquement dans le Cerveau Alix.*
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n📝 [Exocerveau Gravé] Note créée : {filename}")
        return f"Note '{clean_titre}' gravée avec succès dans Captures_Vocales."
    except Exception as e:
        return f"Erreur lors de la gravure: {e}"

class AlixLiveSession:
    """Session Full-Duplex branchée sur l'Exocerveau, Google Search et la Gravure vocale."""
    def __init__(self, p_audio, vosk_model, alix_engine):
        self.p = p_audio
        self.vosk_model = vosk_model
        self.engine = alix_engine
        
        self.is_running = False
        self.should_close = False
        self.is_speaking = False
        self.in_turn = False
        self.last_speech_time = 0.0
        self.last_activity_time = time.time()
        
        self.audio_playback_queue = queue.Queue()
        self.playback_thread = None
        
        self.output_stream = None
        self.input_stream = None
        
        self.interrupt_recognizer = KaldiRecognizer(vosk_model, 16000, json.dumps(["alix", "attends", "stop", "[unk]"]))

    def flush_audio(self):
        """Coupe immédiatement le son d'Alix à la milliseconde."""
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
        """Lit les chunks audio et suit l'état de parole sans coupure prématurée."""
        while self.is_running:
            try:
                chunk = self.audio_playback_queue.get(timeout=0.1)
                if chunk is None:
                    break
                self.is_speaking = True
                self.last_speech_time = time.time()
                self.last_activity_time = time.time()
                if self.output_stream and self.is_running:
                    self.output_stream.write(chunk)
            except queue.Empty:
                # Dès que la file audio est vide depuis 400ms, Alix ne parle plus physiquement : on libère le micro
                if time.time() - self.last_speech_time > 0.4:
                    self.is_speaking = False
                continue
            except Exception:
                self.is_speaking = False
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
                        "tools": [
                            {"googleSearch": {}},
                            {
                                "functionDeclarations": [
                                    {
                                        "name": "consulter_exocerveau",
                                        "description": "Recherche dans les 591 notes des 4 coffres Obsidian (Veralume, 79 Skills, Cerveau Alix, Langage Vectoriel) pour extraire les réflexions et axiomes de Christian Duguay.",
                                        "parameters": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "sujet": {
                                                    "type": "STRING",
                                                    "description": "Le concept, protocole ou terme à chercher dans les coffres."
                                                }
                                            },
                                            "required": ["sujet"]
                                        }
                                    },
                                    {
                                        "name": "graver_intuition_exocerveau",
                                        "description": "Grave immédiatement une note dans le coffre Obsidian 'Cerveau Alix' quand Christian demande de garder ou noter une idée.",
                                        "parameters": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "titre": {
                                                    "type": "STRING",
                                                    "description": "Un titre court et évocateur de l'idée (sans caractères spéciaux)."
                                                },
                                                "contenu": {
                                                    "type": "STRING",
                                                    "description": "La synthèse claire et structurée de l'intuition ou du point clé à retenir."
                                                }
                                            },
                                            "required": ["titre", "contenu"]
                                        }
                                    },
                                    {
                                        "name": "creer_rappel",
                                        "description": "Programme un rappel vocal pour Christian dans son oreillette (ex: pause, appel, tâche, révision).",
                                        "parameters": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "titre": {
                                                    "type": "STRING",
                                                    "description": "Ce qu'il faut rappeler à Christian."
                                                },
                                                "delai_minutes": {
                                                    "type": "NUMBER",
                                                    "description": "Le délai en minutes avant que le rappel sonne."
                                                }
                                            },
                                            "required": ["titre", "delai_minutes"]
                                        }
                                    }
                                ]
                            }
                        ],
                        "realtimeInputConfig": {
                            "automaticActivityDetection": {
                                "silenceDurationMs": 1800
                            }
                        },
                        "systemInstruction": {
                            "parts": [{"text": SYSTEM_PROMPT}]
                        }
                    }
                }
                await ws.send(json.dumps(setup_msg))
                await ws.recv()
                
                print("⚡ [ALIX, EXOCERVEAU & INTERNET CONNECTÉS] Sonar Passif activé !\n")
                
                init_greet = {
                    "clientContent": {
                        "turns": [{"role": "user", "parts": [{"text": "Salut Alix."}]}],
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
            print(f"[Info Session]: {e}")
        finally:
            self.cleanup()

    async def inactivity_watchdog(self):
        """Mise en veille passive après 60 secondes de silence total."""
        while self.is_running and not self.should_close:
            await asyncio.sleep(1.0)
            if self.in_turn or self.is_speaking or not self.audio_playback_queue.empty():
                self.last_activity_time = time.time()
                continue
            
            idle_seconds = time.time() - self.last_activity_time
            if idle_seconds >= 60.0:
                print("\n⏳ [60s d'inactivité] Mise en veille automatique silencieuse...")
                self.should_close = True
                break

    async def send_mic_stream(self, ws):
        """Envoi micro et filtre anti-parasite."""
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
                        if any(w in txt for w in ["alix", "attends", "stop"]):
                            print("\n🛑 [Interruption volontaire] Alix se tait.")
                            self.flush_audio()
                            interupt_msg = {
                                "clientContent": {
                                    "turns": [{"role": "user", "parts": [{"text": "Attends Alix."}]}],
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
        """Réception audio et exécution en direct des outils (RAG, Gravure, Web)."""
        while self.is_running and not self.should_close:
            try:
                raw_msg = await ws.recv()
                res = json.loads(raw_msg)
                
                # 1. GESTION DES OUTILS LOCAUX (Exocerveau & Gravure)
                tool_call = res.get("toolCall")
                if tool_call:
                    self.in_turn = True
                    self.last_activity_time = time.time()
                    function_calls = tool_call.get("functionCalls", [])
                    responses = []
                    for fc in function_calls:
                        f_id = fc.get("id")
                        f_name = fc.get("name")
                        f_args = fc.get("args", {})
                        
                        if f_name == "consulter_exocerveau":
                            sujet = f_args.get("sujet", "")
                            print(f"\n🧠 [Sonar Exocerveau] Alix sonde ses notes sur : « {sujet} »...")
                            search_results = self.engine.search(sujet, top_k=2)
                            snippets = []
                            for r in search_results:
                                snippets.append(f"Note '{r['title']}' (Coffre: {r['vault']}): {r['snippet']}")
                            content_str = "\n".join(snippets) if snippets else "Aucune note spécifique trouvée sur ce terme exact."
                            responses.append({
                                "id": f_id,
                                "response": {"output": {"notes_trouvees": content_str}}
                            })
                            
                        elif f_name == "graver_intuition_exocerveau":
                            titre = f_args.get("titre", "Intuition")
                            contenu = f_args.get("contenu", "")
                            resultat_gravure = graver_intuition(titre, contenu)
                            responses.append({
                                "id": f_id,
                                "response": {"output": {"confirmation": resultat_gravure}}
                            })
                            
                        elif f_name == "creer_rappel":
                            titre = f_args.get("titre", "Rappel")
                            delai = f_args.get("delai_minutes", 5)
                            print(f"\n⏰ [Agenda Alix] Rappel programmé : « {titre} » dans {delai} min.")
                            responses.append({
                                "id": f_id,
                                "response": {"output": {"confirmation": f"Rappel '{titre}' programmé avec succès dans {delai} minutes."}}
                            })
                            asyncio.create_task(self._declencher_rappel_async(ws, titre, delai))
                    
                    tool_resp_msg = {
                        "toolResponse": {
                            "functionResponses": responses
                        }
                    }
                    await ws.send(json.dumps(tool_resp_msg))
                    self.last_activity_time = time.time()
                    self.in_turn = False
                    continue

                server_content = res.get("serverContent", {})
                if server_content.get("interrupted"):
                    self.flush_audio()
                    continue
                
                model_turn = server_content.get("modelTurn", {})
                if model_turn:
                    self.in_turn = True
                    self.last_activity_time = time.time()

                for part in model_turn.get("parts", []):
                    inline = part.get("inlineData", {})
                    if inline.get("mimeType", "").startswith("audio/pcm"):
                        pcm_bytes = base64.b64decode(inline.get("data", ""))
                        self.audio_playback_queue.put(pcm_bytes)
                        self.last_activity_time = time.time()
                
                if server_content.get("turnComplete"):
                    self.in_turn = False
                
            except Exception as e:
                print(f"\n⚠️ [Alerte flux vocal Alix] : {e}")
                break

    async def _declencher_rappel_async(self, ws, titre, delai_minutes):
        try:
            await asyncio.sleep(delai_minutes * 60)
            print(f"\n🔔 [Rappel Alix Actif] : {titre}")
            try:
                winsound.Beep(880, 100)
                winsound.Beep(1174, 120)
                winsound.Beep(1760, 200)
            except Exception:
                pass
            if ws and not self.should_close:
                alert_msg = {
                    "clientContent": {
                        "turns": [{"role": "user", "parts": [{"text": f"[RAPPEL D'AGENDA QUI SONNE MAINTENANT POUR CHRISTIAN] : '{titre}'. Dis-le chaleureusement et directement à Christian dans son oreillette !"}]}],
                        "turnComplete": True
                    }
                }
                await ws.send(json.dumps(alert_msg))
        except Exception:
            pass

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

def run_companion():
    print("=" * 70)
    print("   ALIX COMPANION v7.0 — LE SONAR PASSIF TOTAL (SYNAPSE & GRAVURE)")
    print("=" * 70)
    print(" * Mets ton écouteur avec micro dans ton oreille.")
    print(" * Dis « ALIX » pour ouvrir la discussion continue.")
    print(" * Parle naturellement : le Sonar détecte passivement tes intentions :")
    print("   - Internet (météo, web, nouvelles)")
    print("   - Exocerveau (tes notes, tes protocoles, liens, ponts)")
    print("   - Décapage Thot / Horus (critique, failles, angles morts)")
    print("   - Gravure vocale (« Note ça », « Grave cette idée »)")
    print(" * Interruption volontaire : dis « ATTENDS » ou « ALIX ».")
    print(" * Veille automatique après 60s de silence complet.")
    print("=" * 70 + "\n")

    p = pyaudio.PyAudio()

    print("🧠 Chargement du veilleur phonétique local...")
    vosk_model = VoskModel(lang="fr")
    grammar = json.dumps(["alix", "[unk]"])
    recognizer = KaldiRecognizer(vosk_model, 16000, grammar)

    print("📚 Connexion aux 4 coffres Obsidian d'Alix (Chargement du cache synaptique)...")
    alix_engine = AlixEngine()
    print(f"✅ {len(alix_engine.notes)} notes prêtes pour le brainstorm en direct !\n")

    while True:
        print("💤 [VEILLE] En attente... Dis « Alix » dans ton oreillette.")
        
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
                    if "alix" in text:
                        detected_wake = True
                        break
        except KeyboardInterrupt:
            print("\nArrêt demandé.")
            wake_stream.close()
            break
        except Exception as e:
            print(f"[Erreur micro veille]: {e}")
            time.sleep(0.5)
            continue
        finally:
            wake_stream.stop_stream()
            wake_stream.close()

        if detected_wake:
            print("\n🔔 Signal « Alix » détecté !")
            play_chime_wake()
            
            session = AlixLiveSession(p, vosk_model, alix_engine)
            try:
                asyncio.run(session.run_live_session())
            except KeyboardInterrupt:
                pass
            
            play_chime_sleep()
            print("💤 Retour en veille silencieuse...\n")
            time.sleep(1.0)

    p.terminate()

if __name__ == '__main__':
    run_companion()
