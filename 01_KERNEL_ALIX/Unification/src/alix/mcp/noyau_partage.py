# -*- coding: utf-8 -*-
"""
===============================================================================
       NOYAU PARTAGÉ D'ALIX — un seul cerveau, plusieurs voix (rénovation 2026-10-30)
===============================================================================
Avant : chaque client MCP (Antigravity/Gemini, app Claude, …) lançait son propre
noyau complet (≈ 4,2 Go chacun). Ici, UN processus garde le noyau et la mémoire
chauds et répond sur http://127.0.0.1:5071 :
    GET  /ping   -> état
    POST /outil  -> {"name": ..., "arguments": {...}}  (mêmes outils que le serveur MCP)
    POST /pont   -> {"methode": chercher_notes|lire_note|interroger_cathedrale, "args": [...], "kwargs": {...}}
Chaque client branche le relais léger `alix.mcp.alix_mcp_relais` (≈ 50 Mo).
Ce démon est gardé en vie par le Démon Local (la tête), via le Gardien (« Noyau_Partage »).
===============================================================================
"""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from alix.socle.chemins import ETAT_VIVANT_DIR

PORT = int(os.environ.get("ALIX_NOYAU_PARTAGE_PORT", "5071"))
HOTE = "127.0.0.1"
PID_FILE = ETAT_VIVANT_DIR / "alix_noyau_partage.pid"
LOG_FILE = ETAT_VIVANT_DIR / "noyau_partage.log"

# Sous pythonw il n'y a ni stdout ni stderr : tout va dans le journal, AVANT d'importer le serveur.
ETAT_VIVANT_DIR.mkdir(parents=True, exist_ok=True)
_journal = open(LOG_FILE, "a", encoding="utf-8", buffering=1, errors="replace")
sys.stdout = _journal
sys.stderr = _journal

import alix.mcp.alix_mcp_server as srv  # noqa: E402  (redirige ses propres print vers stderr = journal)

_VERROU_KERNEL = threading.Lock()    # une intention à la fois dans le noyau
_VERROU_MEMOIRE = threading.Lock()   # une recherche mémoire à la fois
_DEBUT = time.time()
_NB = {"appels": 0}
_PRET = threading.Event()
# Couche 2, point 3 (Claude & Alix, 2026-11-02) : le pont distant lit la mémoire ici au lieu d'en charger
# sa propre copie (mesuré : pont exocerveau = +4,1 Go privés par processus). Lecture seule, liste fermée.
_METHODES_PONT = {"chercher_notes", "lire_note", "interroger_cathedrale", "statut_memoire"}


def _log(msg: str):
    _journal.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def _rechauffer():
    """Charge le noyau et la mémoire dès le démarrage, pour que le premier appel soit rapide."""
    t0 = time.time()
    try:
        srv.get_kernel()
        if srv.PONT_DISPONIBLE:
            srv.get_pont_exocerveau()
        _log(f"Noyau et mémoire chauds en {time.time() - t0:.1f} s")
    except Exception as e:
        _log(f"Réchauffement incomplet : {e}")
    finally:
        _PRET.set()


class _Gestionnaire(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, data):
        corps = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        if self.path.split("?")[0] == "/ping":
            self._json(200, {"ok": True, "pid": os.getpid(), "pret": _PRET.is_set(),
                             "appels": _NB["appels"], "uptime_s": round(time.time() - _DEBUT)})
        else:
            self._json(404, {"erreur": "inconnu"})

    def do_POST(self):
        chemin = self.path.split("?")[0]
        if chemin == "/recharger":
            try:
                import importlib
                import alix.mcp.outils_metal as outils_met
                import alix.mcp.outils_definitions as outils_def
                importlib.reload(outils_met)
                importlib.reload(outils_def)
                importlib.reload(srv)
                _log("Noyau partagé : modules outils et serveur rechargés à chaud.")
                return self._json(200, {"ok": True, "recharge": True, "message": "Outils rechargés à chaud sans coupure de socket."})
            except Exception as e:
                _log(f"Erreur rechargement : {e}")
                return self._json(500, {"ok": False, "erreur": str(e)})

        if chemin == "/pont":
            try:
                n = int(self.headers.get("Content-Length", "0"))
                req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
                methode = req.get("methode", "")
                if methode not in _METHODES_PONT:
                    return self._json(400, {"ok": False, "erreur": f"méthode non permise : {methode}"})
                _PRET.wait(timeout=180)
                pont = srv.get_pont_exocerveau() if srv.PONT_DISPONIBLE else None
                if pont is None:
                    return self._json(503, {"ok": False, "erreur": "pont exocerveau indisponible dans le noyau partagé"})
                _NB["appels"] += 1
                with _VERROU_MEMOIRE:
                    res = getattr(pont, methode)(*(req.get("args") or []), **(req.get("kwargs") or {}))
                return self._json(200, {"ok": True, "resultat": json.loads(json.dumps(res, ensure_ascii=False, default=str))})
            except Exception as e:
                _log(f"Erreur /pont : {e}")
                return self._json(500, {"ok": False, "erreur": str(e)})

        if chemin != "/outil":
            return self._json(404, {"erreur": "inconnu"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            nom = req.get("name", "")
            args = req.get("arguments", {}) or {}
            _PRET.wait(timeout=180)
            _NB["appels"] += 1
            if nom == "alix_kernel_traiter_intention":
                with _VERROU_KERNEL:
                    rep = srv.executer_outil(nom, args, 0)
            elif nom == "alix_kernel_chercher_memoire":
                with _VERROU_MEMOIRE:
                    rep = srv.executer_outil(nom, args, 0)
            else:
                rep = srv.executer_outil(nom, args, 0)
            self._json(200, rep)
        except Exception as e:
            _log(f"Erreur /outil : {e}")
            self._json(500, {"jsonrpc": "2.0", "id": 0, "error": {"code": -32000, "message": str(e)}})


def main():
    try:
        serveur = ThreadingHTTPServer((HOTE, PORT), _Gestionnaire)
    except OSError:
        _log(f"Port {PORT} déjà pris : un noyau partagé tourne déjà. Sortie.")
        return
    serveur.daemon_threads = True
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    _log(f"Noyau partagé démarré (PID {os.getpid()}) sur http://{HOTE}:{PORT}")
    threading.Thread(target=_rechauffer, daemon=True).start()
    try:
        serveur.serve_forever()
    finally:
        try:
            PID_FILE.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
