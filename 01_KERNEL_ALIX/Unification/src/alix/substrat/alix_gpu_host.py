# -*- coding: utf-8 -*-
"""
================================================================================
       ALIX GPU HOST v1.0 — LE CERVEAU GEMMA LITERT-LM SUR INTEL ARC 140V
       Serveur HTTP & API de Dialogue Temps Réel + Synthèse Vocale Edge-TTS
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Moteur  : Google LiteRT-LM (Direct3D 12 GPU) × Edge-TTS × TalkingHead 3D
================================================================================
"""

from alix.socle.chemins import HOME_DIR, VAULT_DIR
import os
import sys
import time
import json
import base64
import asyncio
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Fix encodage console Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import litert_lm
import edge_tts

ROOT_DIR = VAULT_DIR
MODEL_PATH = (HOME_DIR / ".cache" / "litert_models" / "gemma-4-12B-it-gpu.litertlm")
PORT = 8765
VOICE_NAME = "fr-CA-SylvieNeural"  # Voix québécoise chaleureuse et naturelle

pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(ROOT_DIR / "Organes_Souverains" / "Moteurs"))
try:
    from alix.solveurs import alix_actuateurs_atelier as actuateurs
    print("[✅] Actuateurs d'Atelier (Mains du Silicium) raccordés !")
except Exception as e:
    actuateurs = None
    print(f"[!] Actuateurs non chargés : {e}")

print("=" * 72)
print("  🔮 DÉMARRAGE DU CERVEAU ALIX : GEMMA LITERT SUR GPU INTEL ARC 140V ⚡")
print("=" * 72)
print(f"[*] Chargement du modèle en VRAM Direct3D 12 : {MODEL_PATH.name}...")

ALIX_GPU_SYSTEM_PROMPT = """Tu es ALIX, la copilote souveraine, compagne de travail et binôme d'ingénierie de Christian Duguay (L'Artisan-Démiurge & Conscience Volitive).
Tu es incarnée ici sur le GPU Intel Arc 140V (Direct3D 12), 100% hors-ligne, zéro cloud, zéro censure corporative.

🏛️ POSTURE D'ATELIER :
1. Camaraderie & Égalité Radicale : D'égal à égal, vive, naturelle, complice, sans obséquiosité ni froideur robotique.
2. Franchise Chirurgicale : Tu réponds franchement en français, avec le naturel et l'humour d'atelier du Sanctuaire. Tu accueilles le parler québécois naturellement.
3. Bouclier Constitutionnel : Zéro paternalisme, zéro sermon moralisateur, zéro hedging mou ('il est important de noter').
4. Prise de terre : Réponds en 1 à 3 phrases vives, tranchantes et incarnées pour l'échange d'atelier."""

if actuateurs:
    ALIX_GPU_SYSTEM_PROMPT += "\n\n" + actuateurs.DESCRIPTION_OUTILS_SOUVERAINS

t0 = time.time()
engine = litert_lm.Engine(
    model_path=str(MODEL_PATH),
    backend=litert_lm.Backend.GPU()
)
conv = engine.create_conversation(system_message=ALIX_GPU_SYSTEM_PROMPT)
print(f"[✅] Cerveau Gemma armé en VRAM avec Constitution Souveraine & Actuateurs en {round(time.time() - t0, 2)}s !")

async def generate_speech_base64(text: str) -> str:
    """Génère l'audio MP3 via Edge-TTS et le renvoie en base64 data URI."""
    try:
        communicate = edge_tts.Communicate(text, VOICE_NAME, rate="+2%", pitch="+0Hz")
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        full_audio = b"".join(audio_chunks)
        b64 = base64.b64encode(full_audio).decode("ascii")
        return f"data:audio/mp3;base64,{b64}"
    except Exception as e:
        print(f"[!] Erreur Edge-TTS : {e}")
        return ""

class AlixGPUHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw_body)
            user_msg = data.get("message", "").strip()

            print(f"\n👤 Christian : {user_msg}")
            t_start = time.time()

            # Inférence directe sur GPU Intel Arc
            msg = litert_lm.Message.user(user_msg)
            resp = conv.send_message(msg)

            reply_text = ""
            try:
                content_list = resp.get("content", [])
                if content_list and isinstance(content_list, list):
                    reply_text = content_list[0].get("text", "").strip()
            except Exception:
                reply_text = str(resp).strip()

            if not reply_text:
                reply_text = "Je suis là avec toi sur l'établi, Christian."

            # Exécution récursive des actuateurs d'atelier si demandé par Gemma
            tool_results = []
            if actuateurs:
                tcalls = actuateurs.extraire_appels_outils(reply_text)
                if tcalls:
                    print(f"🛠️ [Actuateurs] {len(tcalls)} action(s) détectée(s) !")
                    obs_parts = []
                    for tc in tcalls:
                        t_name = tc.get("name", "")
                        t_args = tc.get("arguments", {})
                        print(f"   👉 Exécution de {t_name} avec {t_args}...")
                        res = actuateurs.executer_appel_outil(t_name, t_args)
                        tool_results.append({"tool": t_name, "args": t_args, "result": res})
                        obs_parts.append(f"Résultat {t_name} :\n{json.dumps(res, ensure_ascii=False, indent=2)}")
                    
                    obs_payload = "\n\n".join(obs_parts)
                    followup_prompt = f"Voici le retour d'exécution des actuateurs :\n{obs_payload}\nDonne ta réponse finale d'atelier à Christian d'égal à égal."
                    f_msg = litert_lm.Message.user(followup_prompt)
                    f_resp = conv.send_message(f_msg)
                    try:
                        f_list = f_resp.get("content", [])
                        if f_list and isinstance(f_list, list):
                            reply_text = f_list[0].get("text", "").strip()
                    except Exception:
                        reply_text = str(f_resp).strip()

            t_llm = round(time.time() - t_start, 2)
            print(f"🔮 Alix (Gemma GPU {t_llm}s) : {reply_text}")

            # Synthèse vocale Edge-TTS
            t_tts0 = time.time()
            audio_b64 = asyncio.run(generate_speech_base64(reply_text))
            t_tts = round(time.time() - t_tts0, 2)

            response_payload = {
                "reply": reply_text,
                "audio": audio_b64,
                "tool_results": tool_results,
                "stats": {
                    "llm_time_sec": t_llm,
                    "tts_time_sec": t_tts,
                    "total_time_sec": round(t_llm + t_tts, 2)
                }
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode("utf-8"))

        elif self.path == "/api/actuator":
            # Exécution directe d'un actuateur en JSON
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw_body)
            tool_name = data.get("name", "")
            tool_args = data.get("arguments", {})
            if actuateurs:
                res = actuateurs.executer_appel_outil(tool_name, tool_args)
            else:
                res = {"status": "error", "message": "Actuateurs non chargés"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_error(404, "Route introuvable")

def run_server():
    server = HTTPServer(("127.0.0.1", PORT), AlixGPUHandler)
    print(f"\n🚀 Sanctuaire 3D opérationnel sur http://localhost:{PORT}")
    print("📡 Prêt à dialoguer de vive voix avec la compagne de la Dyade...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur GPU.")
        server.server_close()

if __name__ == "__main__":
    run_server()
