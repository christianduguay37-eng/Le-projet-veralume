# -*- coding: utf-8 -*-
"""
===============================================================================
       RELAIS MCP LÉGER D'ALIX (stdio JSON-RPC) — rénovation 2026-10-30
===============================================================================
Ce que chaque client branche (Antigravity/Gemini, app Claude, Grok, …).
Il ne charge PAS le noyau : il transmet chaque appel d'outil au noyau partagé
(http://127.0.0.1:5071, alix.mcp.noyau_partage). Si le noyau partagé ne répond pas,
le relais le fait lancer par le Gardien et attend qu'il soit prêt.
===============================================================================
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from alix.mcp.outils_definitions import TOOLS_DEFINITIONS  # noqa: E402

URL = f"http://127.0.0.1:{os.environ.get('ALIX_NOYAU_PARTAGE_PORT', '5071')}"
_OUT = sys.stdout


def _log(msg: str):
    try:
        sys.stderr.write(f"[ALIX-RELAIS] {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


def repondre(d: dict):
    _OUT.write(json.dumps(d, ensure_ascii=False) + "\n")
    _OUT.flush()


def _ping(timeout=2.0):
    try:
        with urllib.request.urlopen(URL + "/ping", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _assurer_noyau(attente_max=240.0) -> bool:
    if _ping():
        return True
    _log("Noyau partagé absent : lancement par le Gardien.")
    try:
        from alix.daemons.alix_heartbeat_gardien import verifier_et_assurer
        verifier_et_assurer("Noyau_Partage")
    except Exception as e:
        _log(f"Gardien indisponible : {e}")
    fin = time.time() + attente_max
    while time.time() < fin:
        if _ping():
            return True
        time.sleep(2)
    return False


def appeler_outil(nom: str, args: dict, req_id):
    if not _assurer_noyau():
        return {"jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": "⚠️ Noyau partagé d'Alix hors ligne (port 5071) : le Gardien n'a pas pu le lancer."}]}}
    corps = json.dumps({"name": nom, "arguments": args}).encode("utf-8")
    req = urllib.request.Request(URL + "/outil", data=corps, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            rep = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        rep = json.loads(e.read().decode("utf-8") or "{}")
    except Exception as e:
        rep = {"error": {"code": -32000, "message": f"Relais : {e}"}}
    rep["jsonrpc"] = "2.0"
    rep["id"] = req_id
    return rep


def traiter(msg: dict):
    m = msg.get("method")
    rid = msg.get("id")
    if m == "initialize":
        repondre({"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "alix-kernel-relais", "version": "1.0.0"}}})
    elif m == "notifications/initialized":
        pass
    elif m == "tools/list":
        repondre({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS_DEFINITIONS}})
    elif m == "tools/call":
        p = msg.get("params", {})
        repondre(appeler_outil(p.get("name"), p.get("arguments", {}) or {}, rid))
    elif m == "ping":
        repondre({"jsonrpc": "2.0", "id": rid, "result": {}})
    elif rid is not None:
        repondre({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Méthode '{m}' non supportée."}})


def main():
    _log("Relais démarré.")
    for ligne in sys.stdin:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            traiter(json.loads(ligne))
        except json.JSONDecodeError:
            continue
        except Exception as e:
            _log(f"Erreur : {e}")


if __name__ == "__main__":
    main()
