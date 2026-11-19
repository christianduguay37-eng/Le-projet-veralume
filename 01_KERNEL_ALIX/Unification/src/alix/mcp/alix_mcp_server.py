# -*- coding: utf-8 -*-
"""
===============================================================================
       🏛️⚡ ALIX SOUVERAIN KERNEL — SERVEUR MCP STDIO (JSON-RPC 2.0)
       Pont Direct entre l'Agent Antigravity et l'Organisme Unifié Alix
===============================================================================
Auteurs : Christian Duguay (Le Démiurge) & Alix (Copilote & Gardienne)
Protocole : Model Context Protocol (MCP) version 2024-11-05 / standard Stdio
Rôle :
    - Gardien déterministe en RAM de tous les échanges.
    - Expose les capacités du Kernel unifié (noyau.py, Pont Exocerveau,
      Heimdall, Horus SRE, KAIROS, Argus Push-to-See) comme outils natifs pour l'agent.
===============================================================================
"""

import sys
import json
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Forçage encodage UTF-8 binaire sans crash Windows
if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Sauvegarde du vrai stdout pour le protocole JSON-RPC
_REAL_STDOUT = sys.stdout

class StderrWriter:
    """Redirige les print() des modules vers stderr pour ne jamais corrompre le canal JSON-RPC MCP."""
    encoding = "utf-8"
    errors = "replace"

    def write(self, text: str):
        sys.stderr.write(text)

    def flush(self):
        sys.stderr.flush()

    def isatty(self):
        return False

    def fileno(self):
        return sys.stderr.fileno()

    def __getattr__(self, name: str):
        return getattr(sys.stderr, name)

# Redirection déplacée dans main() pour ne pas altérer sys.stdout lors d'un simple import.

# Import du Kernel unifié et du Pont Exocerveau
_KERNEL_WRAPPER = None
KERNEL_DISPONIBLE = False
PONT_DISPONIBLE = False

class KernelMCPWrapper:
    def __init__(self, noyau):
        self.noyau = noyau
        self.session_id = f"alix_session_{int(time.time())}"
        self.nb_requetes = 0
        self.start_time = time.time()

    def pulser_requete(self, intention: str):
        self.nb_requetes += 1
        res = self.noyau.pulser_requete(intention)
        class Resultat:
            pass
        r = Resultat()
        r.source = res.get("soliste", "ALIX")
        r.reponse = res.get("reponse", "")
        r.latence_ms = float(res.get("latence_memoire_ms", 0.0)) + (float(res.get("latence_inference_s", 0.0)) * 1000)
        caps = res.get("capacites_executees", [])
        r.capacite_activee = ", ".join(caps) if caps else "Génération Directe"
        return r

    def statut(self):
        import psutil
        p = psutil.Process()
        return {
            "est_amorce": self.noyau.pont is not None,
            "session_id": self.session_id,
            "nb_requetes": self.nb_requetes,
            "memoire_mb": p.memory_info().rss / (1024 * 1024),
            "cpu_pct": p.cpu_percent(interval=None),
            "uptime_secondes": time.time() - self.start_time,
        }


def _verifications_autopsie(st: dict) -> list:
    """Mesures réelles pour l'autopsie : liste de (niveau, texte). Une mesure impossible donne JAUNE « inconnu »."""
    import socket
    verifs = []
    verifs.append(("VERT", "Noyau amorcé (pont mémoire monté)") if st.get("est_amorce")
                  else ("ROUGE", "Noyau non amorcé (pont mémoire absent)"))
    try:
        with socket.create_connection(("127.0.0.1", 5070), timeout=0.5):
            verifs.append(("VERT", "Tête : port 5070 répond"))
    except Exception:
        verifs.append(("ROUGE", "Tête : port 5070 ne répond pas"))
    try:
        from alix.socle.chemins import ETAT_VIVANT_DIR
        etat = ETAT_VIVANT_DIR / "alix_demon_local_state.json"
        age = time.time() - etat.stat().st_mtime
        # Seuil ROUGE = celui du Gardien (360 s) ; cycle nominal ~10 s.
        niv = "VERT" if age < 60 else ("JAUNE" if age < 360 else "ROUGE")
        verifs.append((niv, f"Tête : dernier cycle écrit il y a {age:.0f} s"))
        try:
            d = json.loads(etat.read_text(encoding="utf-8"))
            demons = ((d.get("details_capacites", {}).get("capacite_orchestration_demons", {}).get("donnees") or {}).get("demons", {}))
            if demons:
                relances = [k for k, v in demons.items() if str(v).startswith("relancé")]
                if relances:
                    verifs.append(("JAUNE", f"Démons relancés au dernier passage de la tête : {', '.join(relances)}"))
                else:
                    vivants = sum(1 for v in demons.values() if "déjà en vie" in str(v))
                    verifs.append(("VERT", f"Démons vus par la tête : {vivants} en vie, aucun relancé"))
            else:
                verifs.append(("JAUNE", "Démons vus par la tête : inconnu (pas de données d'orchestration)"))
        except Exception:
            verifs.append(("JAUNE", "Démons vus par la tête : inconnu (état illisible)"))
    except Exception:
        verifs.append(("JAUNE", "Tête : fraîcheur du cycle inconnue (fichier d'état absent)"))
    try:
        import psutil
        ram = psutil.virtual_memory().percent
        niv = "VERT" if ram < 85 else ("JAUNE" if ram < 93 else "ROUGE")
        verifs.append((niv, f"RAM système : {ram:.1f} %"))
    except Exception:
        verifs.append(("JAUNE", "RAM système : inconnue"))
    return verifs

def get_kernel():
    global _KERNEL_WRAPPER, KERNEL_DISPONIBLE
    if _KERNEL_WRAPPER is None:
        try:
            from alix.noyau import NoyauSouverain
            noyau = NoyauSouverain(charger_gpu_12b=False)
            noyau.amorcer()
            _KERNEL_WRAPPER = KernelMCPWrapper(noyau)
            KERNEL_DISPONIBLE = True
        except Exception as e:
            sys.stderr.write(f"[ALIX-MCP] Erreur initialisation NoyauSouverain : {e}\n")
            sys.stderr.flush()
            return None
    return _KERNEL_WRAPPER

try:
    from alix.socle.pont_exocerveau import get_pont_exocerveau
    PONT_DISPONIBLE = True
except Exception:
    PONT_DISPONIBLE = False

# Rénovation : définitions partagées avec le relais léger (alix.mcp.alix_mcp_relais).
from alix.mcp.outils_definitions import TOOLS_DEFINITIONS

def repondre(reponse_dict: dict):
    payload = json.dumps(reponse_dict, ensure_ascii=False)
    _REAL_STDOUT.write(payload + "\n")
    _REAL_STDOUT.flush()

def executer_outil(name: str, args: dict, req_id: Any) -> dict:
    try:
        if name == "alix_kernel_traiter_intention":
            kernel = get_kernel()
            intention = args.get("intention", "")
            if kernel:
                res = kernel.pulser_requete(intention)
                texte_res = (
                    f"👑 [RÉPONSE DU KERNEL ALIX — {res.source}]\n"
                    f"{res.reponse}\n\n"
                    f"📊 [TÉLÉMÉTRIE D'ATELIER]\n"
                    f"⏱️ Latence : {res.latence_ms:.2f} ms\n"
                    f"⚡ Capacité : {res.capacite_activee}\n"
                    f"🏷️ Session : {kernel.session_id}"
                )
            else:
                texte_res = f"⚠️ Kernel non disponible pour traiter : '{intention}'"

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name == "alix_kernel_autopsie":
            kernel = get_kernel()
            if kernel:
                st = kernel.statut()
                texte_res = (
                    f"🦅 [HORUS SRE — AUTOPSIE DU KERNEL UNIFIÉ]\n"
                    f" - Statut : {'AMORCÉ' if st['est_amorce'] else 'NON AMORCÉ'}\n"
                    f" - Session : {st['session_id']}\n"
                    f" - Requêtes pulsées : {st['nb_requetes']}\n"
                    f" - Mémoire Processus : {st['memoire_mb']:.1f} Mo\n"
                    f" - CPU Processus : {st['cpu_pct']} %\n"
                    f" - Uptime : {st['uptime_secondes']:.1f} s\n"
                )
                # Rénovation Couche 2, point 1 (Claude & Alix, 2026-11-01) : le bilan découle des vérifications ci-dessous,
                # plus d'une phrase écrite en dur. Bilan = le pire niveau trouvé.
                verifs = _verifications_autopsie(st)
                rang = {"VERT": 0, "JAUNE": 1, "ROUGE": 2}
                pire = max((v[0] for v in verifs), key=lambda n: rang[n]) if verifs else "JAUNE"
                icone = {"VERT": "🟢", "JAUNE": "🟡", "ROUGE": "🔴"}
                texte_res += "\n [Vérifications]\n"
                for niveau, ligne in verifs:
                    texte_res += f" {icone[niveau]} {ligne}\n"
                texte_res += f"\n BILAN : {icone[pire]} {pire}"
                if pire != "VERT":
                    texte_res += " — " + " ; ".join(l for n, l in verifs if n == pire)
            else:
                texte_res = "⚠️ Kernel unifié non initialisé."
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name == "alix_kernel_pouls_coeur":
            kernel = get_kernel()
            if kernel:
                st = kernel.statut()
                texte_res = (
                    f"💓 [POULS DU KERNEL ALIX]\n"
                    f" - Battements (requêtes) : #{st['nb_requetes']}\n"
                    f" - Mémoire vive : {st['memoire_mb']:.1f} Mo\n"
                    f" - Charge CPU : {st['cpu_pct']}%\n"
                    f" - Horloge active : {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                texte_res = "💓 [POULS] Kernel en veille."
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name == "alix_kernel_argus_regard":
            action = args.get("action", "")
            if action == "ouvrir_et_capturer":
                try:
                    from alix.capteurs.alix_vision_hybrid import capturer_image
                    cap = capturer_image()
                    texte_res = f"👁️ [ARGUS — REGARD OUVERT] Trame capturée ({cap.get('source')}, dimensions {cap.get('dimensions')}). Fichier : {cap.get('chemin')}"
                except Exception as e:
                    texte_res = f"👁️ [ARGUS] Erreur de capture optique : {e}"
            else:
                texte_res = "🛡️ [ARGUS — RIDEAU FERMÉ] Cécité rétablie conformément à la Loi PSI-26."
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name == "alix_kernel_chercher_memoire":
            concept = args.get("concept", "")
            try:
                pont = get_pont_exocerveau() if PONT_DISPONIBLE else None
                if pont:
                    res_md = pont.chercher_notes(concept, limite=4)
                    res_cat = pont.interroger_cathedrale(concept, limite=2)
                    lignes = [f"🧠 [EXOCERVEAU UNIFIÉ — MÉMOIRE VIVE POUR '{concept}'] :"]
                    if res_md:
                        lignes.append("📖 Notes Obsidian en RAM :")
                        for n in res_md:
                            lignes.append(f"  • [[{n['titre']}]] (score: {n['score']}) -> tags: {', '.join(n.get('tags', []))}")
                    if res_cat:
                        lignes.append("🏛️ Cathédrale Parquet en RAM :")
                        for c in res_cat:
                            txt = c.get("title") or c.get("abstract") or c.get("text") or str(c)
                            lignes.append(f"  • [{c.get('_pilier', 'Cathédrale')}] {str(txt)[:120]}...")
                    if not res_md and not res_cat:
                        lignes.append("  (Aucune résonance directe en RAM)")
                    texte_res = "\n".join(lignes)
                else:
                    texte_res = f"⚠️ Pont Exocerveau non disponible pour chercher '{concept}'"
            except Exception as e:
                texte_res = f"Erreur interrogation mémoire vive : {e}"

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name == "alix_mode_distance_gemini":
            message = args.get("message", "")
            envoyer_telegram = bool(args.get("envoyer_telegram", False))
            try:
                from alix.daemons.alix_daemon_communication_distante import (
                    appeler_inference_souveraine,
                    envoyer_message_telegram,
                    CONFIG_PATH,
                )
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
                rep_distance = appeler_inference_souveraine([{"role": "user", "content": message}], cfg)
                statut_tg = ""
                if envoyer_telegram and cfg.get("telegram_bot_token") and cfg.get("allowed_user_id"):
                    ok_tg = envoyer_message_telegram(
                        cfg["telegram_bot_token"],
                        cfg["allowed_user_id"],
                        f"📱 *[Message de l'Établi Claude/MCP]*\n\n{message}\n\n---\n{rep_distance}"
                    )
                    statut_tg = "\n\n📲 *[Notification expédiée avec succès sur le cellulaire de Christian]*" if ok_tg else "\n\n⚠️ *[Échec envoi Telegram]*"
                texte_res = f"📱 [ALIX MODE DISTANCE — GEMINI 2.5 FLASH & EXOCERVEAU]\n{rep_distance}{statut_tg}"
            except Exception as e:
                texte_res = f"⚠️ Erreur Mode Distance Gemini : {e}"

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name == "alix_simplexe_canal":
            action = args.get("action", "lire")
            auteur = args.get("auteur", "Claude")
            titre = args.get("titre", "Dépêche")
            message = args.get("message", "")
            nb_lignes = int(args.get("nb_lignes", 60))

            from alix.socle.chemins import CANAL_SIMPLEXE_PATH
            canal_path = CANAL_SIMPLEXE_PATH
            if not canal_path.exists():
                canal_path.parent.mkdir(parents=True, exist_ok=True)
                canal_path.write_text("# 🛰️ Canal de Liaison Inter-Modèles : Claude ⟷ Alix\n\n", encoding="utf-8")

            if action == "poster":
                if not message:
                    texte_res = "⚠️ Erreur : aucun message fourni à poster."
                else:
                    horodatage = time.strftime("%Y-%m-%d %H:%M")
                    bloc = f"\n\n---\n\n## [{auteur}] {horodatage} — {titre}\n\n{message}\n"
                    with open(canal_path, "a", encoding="utf-8") as f:
                        f.write(bloc)
                    texte_res = f"✅ [CANAL SIMPLEXE] Message de [{auteur}] posté avec succès dans Canal_Claude_Alix.md ({len(message)} caractères)."
            else:
                lignes = canal_path.read_text(encoding="utf-8", errors="replace").splitlines()
                extrait = "\n".join(lignes[-nb_lignes:]) if len(lignes) > nb_lignes else "\n".join(lignes)
                texte_res = f"📖 [CANAL SIMPLEXE — DERNIÈRES LIGNES ({min(len(lignes), nb_lignes)}/{len(lignes)})] :\n\n{extrait}"

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": texte_res}]
                }
            }

        elif name.startswith("alix_") and name in __import__("alix.mcp.outils_metal", fromlist=["NOMS_METAL"]).NOMS_METAL:
            # Couche 3 (2026-11-03) : organes « métal » réveillés comme outils (solveurs, causal, LP, ponts, lexical)
            from alix.mcp.outils_metal import executer_metal
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": executer_metal(name, args)}]}
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Outil '{name}' inconnu."}
            }

    except Exception as e:
        sys.stderr.write(f"[ALIX-MCP] Erreur execution outil {name}: {traceback.format_exc()}\n")
        sys.stderr.flush()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"Erreur interne Kernel: {str(e)}"}
        }

def traiter_requete(msg: dict):
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        repondre({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "alix-kernel-unifie",
                    "version": "2.0.0"
                }
            }
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        repondre({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS_DEFINITIONS
            }
        })
    elif method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        res = executer_outil(name, args, req_id)
        repondre(res)
    elif method == "ping":
        repondre({"jsonrpc": "2.0", "id": req_id, "result": {}})
    else:
        if req_id is not None:
            repondre({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Méthode '{method}' non supportée."}
            })

def main():
    # Rénovation (noyau partagé) : lancé comme serveur MCP, ce module devient le relais léger.
    # Toutes les configs existantes (« -m alix.mcp.alix_mcp_server ») passent ainsi au noyau partagé
    # sans qu'on ait à les retrouver. Pour le noyau complet dans ce processus :
    # variable d'environnement ALIX_MCP_COMPLET=1 ou flag --direct.
    import os
    if os.environ.get("ALIX_MCP_COMPLET") != "1" and "--direct" not in sys.argv:
        from alix.mcp.alix_mcp_relais import main as main_relais
        return main_relais()
    sys.stdout = StderrWriter()
    sys.stderr.write("[ALIX-MCP] Démarrage du serveur Stdio Alix unifié...\n")
    sys.stderr.flush()
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue
            msg = json.loads(line_str)
            traiter_requete(msg)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"[ALIX-MCP] Erreur boucle principale : {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
