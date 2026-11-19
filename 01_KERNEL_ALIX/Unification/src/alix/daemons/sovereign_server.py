# -*- coding: utf-8 -*-
"""
================================================================================
          🌐 SOVEREIGN COCKPIT SERVER — SERVEUR D'ATELIER LOCAL
================================================================================
Auteurs : Christian Duguay & Alix Copilote
Système : VERALUME × KAIROS V6 × Intel Core Ultra 7 258V
Rôle    : Serveur HTTP / SSE local ultra-léger (port 7777) :
          - Distribution de l'interface Web (sovereign_ui.html)
          - Streaming haute performance (Server-Sent Events) des tokens et outils
          - Télémétrie en direct du SoC Lunar Lake (NPU/RAM/CPU)
          - Magasinage en 1 clic des modèles mondiaux (OpenRouter, Groq, DeepSeek, Google)
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR
import os
import sys
import json
import time
import psutil
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from alix.daemons.sovereign_cockpit_engine import SovereignCockpitEngine, DEFAULT_PROVIDERS

PORT = 7777
HOST = "127.0.0.1"

# Initialisation du moteur d'inférence
engine = SovereignCockpitEngine()


def get_lunar_lake_telemetry() -> dict:
    """Récupère l'état matériel en direct de la machine de Christian."""
    cpu_pct = psutil.cpu_percent(interval=None) if 'psutil' in sys.modules else 0.0
    ram = psutil.virtual_memory() if 'psutil' in sys.modules else None
    
    pulse_file = (ETAT_VIVANT_DIR / "alix_live_state.json")
    kairos_state = {}
    if pulse_file.exists():
        try:
            with open(pulse_file, "r", encoding="utf-8") as f:
                kairos_state = json.load(f)
        except Exception:
            pass

    return {
        "soc": "Intel Core Ultra 7 258V (Lunar Lake)",
        "cpu_usage_pct": cpu_pct,
        "ram_used_gb": round(ram.used / (1024**3), 1) if ram else 0.0,
        "ram_total_gb": round(ram.total / (1024**3), 1) if ram else 32.0,
        "ram_pct": ram.percent if ram else 0.0,
        "npu_status": "48 TOPS AI Boost (LiteRT / OpenVINO)",
        "w_vol": kairos_state.get("w_vol", "0.307"),
        "chi": kairos_state.get("chi", "0.38"),
        "active_pole": kairos_state.get("pole_nom", "Immunité Cognitive & Souveraineté"),
        "history_count": len(engine.conversation_history)
    }


class CockpitHTTPHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes HTTP et de flux SSE pour le Cockpit Souverain."""

    def log_message(self, format, *args):
        # Réduit le bruit dans la console
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Page d'accueil du Cockpit
        if path in ("/", "/index.html"):
            ui_file = CURRENT_DIR / "sovereign_ui.html"
            if not ui_file.exists():
                self.send_error(404, "sovereign_ui.html introuvable")
                return
            try:
                with open(ui_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, str(e))
            return

        # 2. Configuration & Modèles
        elif path == "/api/config":
            engine.config = engine.load_config()
            data = {
                "config": engine.config,
                "providers": DEFAULT_PROVIDERS
            }
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 3. Télémétrie en direct
        elif path == "/api/telemetry":
            telem = get_lunar_lake_telemetry()
            body = json.dumps(telem, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 4. Historique de conversation
        elif path == "/api/history":
            body = json.dumps(engine.conversation_history, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        else:
            self.send_error(404, "Page non trouvée")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Lecture du payload JSON
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {}

        # 1. Envoi d'un message avec streaming SSE
        if path == "/api/chat":
            user_prompt = payload.get("prompt", "").strip()
            if not user_prompt:
                self.send_error(400, "Prompt vide")
                return

            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            # Callback d'événement SSE
            def event_callback(event: dict):
                try:
                    sse_line = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    self.wfile.write(sse_line.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    # Déconnexion du client
                    engine.is_running = False

            # Exécution de la boucle d'agentivité
            engine.run_agentic_turn(user_prompt, callback=event_callback)
            return

        # 2. Interruption / Stop
        elif path == "/api/stop":
            engine.is_running = False
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "stopped"}')
            return

        # 3. Réinitialisation de la mémoire
        elif path == "/api/clear":
            engine.clear_history()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "cleared"}')
            return

        # 4. Sauvegarde de la configuration
        elif path == "/api/config":
            new_cfg = payload.get("config", {})
            if new_cfg:
                engine.config.update(new_cfg)
                engine.save_config()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "saved"}')
            return

        else:
            self.send_error(404, "Endpoint POST non trouvé")


def demarrer_serveur():
    """Lance le serveur d'atelier sur http://127.0.0.1:7777."""
    try:
        server = ThreadingHTTPServer((HOST, PORT), CockpitHTTPHandler)
        print("=" * 75)
        print(f"   🚀 LE COCKPIT SOUVERAIN EST EN LIGNE !")
        print(f"   👉 URL Atelier : http://{HOST}:{PORT}")
        print("=" * 75)
        print(f"   Fournisseur Actif : {engine.config.get('active_provider', 'openrouter')}")
        print(f"   Modèle Actif      : {engine.config.get('active_model')}")
        print("   Appuyez sur Ctrl+C pour arrêter le serveur.")
        print("-" * 75)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Fermeture du Cockpit Souverain.")
    except Exception as e:
        print(f"\n❌ Erreur démarrage serveur : {e}")


if __name__ == "__main__":
    demarrer_serveur()
