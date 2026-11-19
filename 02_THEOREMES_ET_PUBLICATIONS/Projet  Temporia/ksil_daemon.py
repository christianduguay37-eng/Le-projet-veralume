"""
===============================================================================
               KAIROS-SILICON RESIDENT DAEMON (K-SIL DAEMON) v1.0
          Démon Résident Silicium Souverain pour Intel Lunar Lake 258V
   Atelier Démiurgique & Sanctuaire Exocerveau — Christian Duguay & Alix
===============================================================================
Maintient le silicium (NPU 4, Arc 140V Xe2 GPU, Lion Cove CPU) pré-chauffé en
mémoire et expose une interface IPC locale (HTTP/JSON-RPC sur 127.0.0.1:8765)
pour toutes les applications, scripts et sentinelles de l'ordinateur.
===============================================================================
"""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import urllib.request

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import ksil

DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 8765
STATE_FILE = r"C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\ksil_live_state.json"
PID_FILE = r"C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\ksil_daemon.pid"


class KsilServerHandler(BaseHTTPRequestHandler):
    engine: ksil.KsilCognitiveEngine = None
    stats = {
        "requests_served": 0,
        "early_exits_triggered": 0,
        "total_latency_ms": 0.0,
        "start_time": time.time(),
    }

    def log_message(self, format, *args):
        # Silence standard HTTP access logging to prevent console pollution
        return

    def do_GET(self):
        if self.path == "/status" or self.path == "/":
            uptime = time.time() - self.stats["start_time"]
            avg_lat = (
                self.stats["total_latency_ms"] / max(1, self.stats["requests_served"])
            )
            resp = {
                "status": "ONLINE",
                "engine": "KAIROS-SILICON v1.0",
                "soc": "Intel Lunar Lake Core Ultra 7 258V",
                "devices": self.engine.topo.available_devices,
                "uptime_seconds": round(uptime, 1),
                "requests_served": self.stats["requests_served"],
                "early_exits": self.stats["early_exits_triggered"],
                "avg_latency_ms": round(avg_lat, 3),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/infer":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                # Accepte des données ou génère un tenseur de test
                if "vector" in payload:
                    arr = np.array(payload["vector"], dtype=np.float32)
                    if arr.ndim == 1:
                        arr = arr.reshape(1, -1)
                else:
                    arr = np.random.randn(16, 512).astype(np.float32)

                threshold = float(payload.get("threshold", 0.75))
                early_exit = bool(payload.get("early_exit", True))

                t0 = time.perf_counter()
                res = self.engine.run_inference(
                    arr,
                    enable_early_exit=early_exit,
                    early_exit_threshold=threshold,
                )
                dt_ms = (time.perf_counter() - t0) * 1000.0

                self.stats["requests_served"] += 1
                self.stats["total_latency_ms"] += dt_ms
                if res.early_exit_triggered:
                    self.stats["early_exits_triggered"] += 1

                # Sauvegarde l'état live
                update_live_state(self.engine, self.stats)

                resp = {
                    "success": True,
                    "chi": round(float(res.chi), 4),
                    "early_exit": res.early_exit_triggered,
                    "latency_ms": round(dt_ms, 3),
                    "accumulated_flops": res.accumulated_flops,
                    "history": res.history,
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def update_live_state(engine: ksil.KsilCognitiveEngine, stats: dict):
    uptime = time.time() - stats["start_time"]
    state = {
        "daemon": "KAIROS-SILICON",
        "status": "RUNNING",
        "last_pulse": time.strftime("%Y-%m-%d %H:%M:%S"),
        "soc": "Intel Core Ultra 7 258V (Lunar Lake)",
        "hardware": {
            "npu": "Intel AI Boost (48 TOPS, ~2W)",
            "gpu": "Intel Arc 140V Xe2 (16GB, ~15W)",
            "cpu": "Intel Core Ultra 7 258V Lion Cove (~20W)",
        },
        "metrics": {
            "requests_processed": stats["requests_served"],
            "early_exit_count": stats["early_exits_triggered"],
            "avg_latency_ms": round(
                stats["total_latency_ms"] / max(1, stats["requests_served"]), 3
            ),
            "uptime_seconds": round(uptime, 1),
        },
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def run_daemon():
    print("=" * 76)
    print("  🧠  DÉMARRAGE DU DÉMON RÉSIDENT KAIROS-SILICON (LUNAR LAKE)")
    print("=" * 76)

    topo = ksil.HardwareTopology()
    engine = ksil.KsilCognitiveEngine(topo, batch_size=16, dim=512)

    KsilServerHandler.engine = engine
    KsilServerHandler.stats["start_time"] = time.time()

    # Enregistrer le PID
    try:
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    server = HTTPServer((DAEMON_HOST, DAEMON_PORT), KsilServerHandler)
    print(f"[K-SIL DAEMON] Serveur à l'écoute sur http://{DAEMON_HOST}:{DAEMON_PORT}")
    print(f"[K-SIL DAEMON] Silicium pré-chauffé et prêt pour toutes les bébelles.")

    update_live_state(engine, KsilServerHandler.stats)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[K-SIL DAEMON] Arrêt du démon demandé.")
    finally:
        server.server_close()
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
        print("[K-SIL DAEMON] Démon arrêté proprement.")


def check_status():
    url = f"http://{DAEMON_HOST}:{DAEMON_PORT}/status"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("\n" + "=" * 70)
            print("  🟢 STATUT DU DÉMON KAIROS-SILICON EN DIRECT :")
            print("=" * 70)
            print(json.dumps(data, indent=2))
            print("=" * 70)
            return True
    except Exception:
        print("\n" + "=" * 70)
        print("  ⚪ LE DÉMON KAIROS-SILICON EST ACTUELLEMENT EN SOMMEIL.")
        print(f"     Pour le réveiller : python ksil_daemon.py start")
        print("=" * 70)
        return False


def test_daemon():
    url = f"http://{DAEMON_HOST}:{DAEMON_PORT}/infer"
    payload = {"threshold": 0.75, "early_exit": True}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            dt = (time.perf_counter() - t0) * 1000.0
            print("\n" + "=" * 70)
            print("  ⚡ TEST EN DIRECT SUR LE SILICIUM VIA LE DÉMON RÉSIDENT :")
            print("=" * 70)
            print(f"  • Latence Réseau + Calcul : {dt:.2f} ms")
            print(f"  • Score d'Invariance (χ)  : {res.get('chi')}")
            print(f"  • Court-Circuit Activé    : {res.get('early_exit')}")
            print(f"  • FLOPs Traités           : {res.get('accumulated_flops'):,}")
            print("  • Trace de Transfert      :")
            for step in res.get("history", []):
                print(f"      -> {step}")
            print("=" * 70)
            return True
    except Exception as e:
        print(f"[ERREUR] Le démon ne répond pas : {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "status":
            check_status()
        elif cmd == "test":
            test_daemon()
        elif cmd == "start":
            run_daemon()
        else:
            print("Usage: python ksil_daemon.py [start|status|test]")
    else:
        run_daemon()
