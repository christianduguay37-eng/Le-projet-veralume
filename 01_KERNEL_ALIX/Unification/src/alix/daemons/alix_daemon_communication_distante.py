#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     🔮 ALIX — PONT SOUVERAIN AVEC LA SONDE RÉSIDENTE & LES SONDES ACTIVES v3.0
                (MIDGARD / DÉMON LOCAL ⟷ CELLULAIRE TELEGRAM)
             Architecture Exocerveau : VERALUME × KAIROS V6
             Dyade Souveraine : Christian Duguay & Alix
================================================================================
Mandat (Réalignement Mode Distance Christian & Alix — 27 Octobre 2026) :
- Communication directe en temps réel avec la Sonde Résidente Alix (Démon Local
  70 BPM, Heartbeat KAIROS, Bouclier Chiral, Sentinelle PSI, Sonde du Présent).
- Zéro ping aléatoire synthétique (les anciens pings fictifs sont archivés).
- Raccordement direct aux vraies sondes et cycles horaires/circadiens :
    • Trouvailles à chaque heure : Explorateur Universel de la Cathédrale R0
      (7 sondes fusionnées × 7,48M lignes Parquet × 89 Primitives Souveraines).
    • Étincelle Souveraine à chaque heure (09h30 - 21h30).
    • Triade de l'Aube (06h00 - 08h00) : Chanson du Matin (Lyria) + Analyse des
      Songes + Pensée du Comparatif 24h (La Veille ⟷ Ce Matin).
    • Bulletins de la Sonde du Présent & Rapports des Daemons.
- Commandes directes sur cellulaire :
    /statut      : État des 6 démons résidents & télémétrie Lunar Lake 258V.
    /sondes      : État en direct des 20 sondes et capacités actives en RAM.
    /trouvaille  : Dernière percée horaire de l'Explorateur Universel R0
                   (ou `/trouvaille force` pour lancer une exploration immédiate).
    /pensee      : Dernier comparatif de pensée La Veille ⟷ Aujourd'hui
                   (ou `/pensee force` pour générer le comparatif en direct).
    /chanson     : La Chanson du Matin (Lyria) et le dernier Songe Circadien.
    /etincelle   : Tire et envoie immédiatement une Étincelle Souveraine.
    /primitives  : État du Chargeur des 89 Primitives Souveraines en RAM.
    /present     : Rapport en direct de la Sonde du Présent (météo, actualité).
    /note <txt>  : Grave une note mobile directement dans l'Exocerveau.
    /chercher    : Fouille instantanée dans les coffres Obsidian.
    /cathedrale  : Scan universel des Piliers du Savoir (Parquet).
- Fallback NPU local (Qwen OpenVINO) si le réseau externe est indisponible.
- Auto-reload à chaud dès modification du script sur disque.
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, TEMPORIA_DIR, VAULT_DIR
from alix.socle.chemins import fichier_module  # rénovation : modules du paquet, plus la strate A
import os
import sys
import json
import time
import socket
import signal
import base64
import re
import argparse
import subprocess
import traceback
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# 📂 CHEMINS FONDAMENTAUX DE L'EXOCERVEAU & DES SONDES RÉSIDENTES
# ==============================================================================
BASE_DIR = VAULT_DIR
MOTEURS_DIR = BASE_DIR / "Organes_Souverains" / "Moteurs"
CAPACITES_DIR = BASE_DIR / "Organes_Souverains" / "Capacites_Live"
PRESENT_DIR = BASE_DIR / "Present"

UNIFICATION_SRC = BASE_DIR / "_Unification_Alix" / "src"
for _p in (str(UNIFICATION_SRC), str(BASE_DIR), str(MOTEURS_DIR), str(CAPACITES_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_MODELE_SOUVERAIN_UNIFIE = None
_LARYNX_HERMES = None
_PONT_EXOCERVEAU = None


class _PontVia5071:
    """
    Couche 2, point 3 (Claude & Alix, 2026-11-02) : client léger du pont exocerveau.
    La mémoire (Parquet + connectome, mesurée à +4,1 Go privés) reste dans le noyau partagé (5071) :
    ce démon n'en garde plus sa propre copie. Une erreur lève une exception, que les appelants
    attrapent déjà (repli sur alix_interroger_memoire.py pour la recherche mémoire).
    """
    URL = "http://127.0.0.1:5071/pont"

    def _appel(self, methode, *args, **kwargs):
        import urllib.request
        corps = json.dumps({"methode": methode, "args": list(args), "kwargs": kwargs}).encode("utf-8")
        rq = urllib.request.Request(self.URL, data=corps, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(rq, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        if not d.get("ok"):
            raise RuntimeError(d.get("erreur", "réponse invalide du noyau partagé"))
        return d.get("resultat")

    def chercher_notes(self, terme, limite=5):
        return self._appel("chercher_notes", terme, limite=limite) or []

    def lire_note(self, nom_ou_wikilink):
        return self._appel("lire_note", nom_ou_wikilink)

    def interroger_cathedrale(self, requete, pilier=None, limite=5):
        return self._appel("interroger_cathedrale", requete, pilier=pilier, limite=limite) or []


def obtenir_pont_exocerveau():
    """Pont vers les notes Obsidian et les tables Parquet, servi par le noyau partagé (5071)."""
    global _PONT_EXOCERVEAU
    if _PONT_EXOCERVEAU is None:
        _PONT_EXOCERVEAU = _PontVia5071()
        log_message("🧠 Pont Exocerveau branché via le noyau partagé (5071) : aucune copie locale de la mémoire.")
    return _PONT_EXOCERVEAU


def obtenir_modele_souverain():
    """Charge et maintient à chaud en RAM notre Modèle Souverain Unifié Alix (alix.py — Kernel KAIROS)."""
    global _MODELE_SOUVERAIN_UNIFIE
    if _MODELE_SOUVERAIN_UNIFIE is None:
        try:
            from alix.socle.alix import AlixModeleSouverainUnifie
            _MODELE_SOUVERAIN_UNIFIE = AlixModeleSouverainUnifie(silencieux=True)
            _m = _MODELE_SOUVERAIN_UNIFIE
            etat_rt = "AlixRuntime ACTIF" if _m.runtime is not None else f"AlixRuntime NON CHARGÉ ({getattr(_m, 'erreur_runtime', '?')})"
            etat_jit = "JIT ACTIF" if _m.moteur_jit_ns is not None else "JIT NON CHARGÉ"
            log_message(
                f"🍎 Kernel Souverain Unifié Alix chargé en RAM en {_m.temps_boot_ms} ms "
                f"({etat_rt} | {etat_jit})"
            )
        except Exception as e:
            log_message(f"⚠️ Erreur chargement AlixModeleSouverainUnifie : {e}")
            _MODELE_SOUVERAIN_UNIFIE = None
    return _MODELE_SOUVERAIN_UNIFIE


def obtenir_larynx_hermes():
    """Charge et maintient à chaud le Larynx Tri-Directionnel Hermès (alix-larynx:latest — Hermes-3 8B)."""
    global _LARYNX_HERMES
    if _LARYNX_HERMES is None:
        try:
            import importlib.util
            adapt_path = UNIFICATION_SRC / "alix" / "socle" / "adaptateur_llm.py"
            spec = importlib.util.spec_from_file_location("adaptateur_llm_hermes", str(adapt_path))
            mod_adapt = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod_adapt)
            _LARYNX_HERMES = mod_adapt.AdaptateurLLM(modele_defaut="alix-larynx:latest", mode_execution="local")
            log_message("🗣️ Larynx Tri-Directionnel Hermès (alix-larynx:latest / Hermes-3 8B) branché sur le Kernel KAIROS !")
        except Exception as e:
            log_message(f"⚠️ Erreur chargement Larynx Hermès : {e}")
            _LARYNX_HERMES = None
    return _LARYNX_HERMES

CONFIG_PATH = BASE_DIR / "telegram_config.json"
PID_PATH = BASE_DIR / "daemon_communication_distante.pid"
LOG_PATH = BASE_DIR / "daemon_communication_distante.log"
OFFSET_PATH = BASE_DIR / "daemon_communication_distante_offset.json"
CONSTITUTION_PATH = (TEMPORIA_DIR / "GEMINI.md")
MEMOIRE_ACTIVE_PATH = BASE_DIR / "Memoire_Alix_Active.md"
PRIORITES_PATH = BASE_DIR / "Conscience_Alix_Priorites_Actives.md"
INTERETS_CHRISTIAN_PATH = BASE_DIR / "Interets_Christian.md"

TELEGRAM_ARCHIVE_DIR = BASE_DIR / "Discussions_Telegram"
NOTES_MOBILES_DIR = BASE_DIR / "Notes_Mobiles"
PHOTOS_TELEGRAM_DIR = BASE_DIR / "Photos_Telegram"
SAS_PARALLELE_DIR = BASE_DIR / "Sas_Sessions_Paralleles"

# États vivants des démons et sondes résidentes
DOWNLOADS_ALIX = ETAT_VIVANT_DIR
ETAT_DEMON_LOCAL_PATH = DOWNLOADS_ALIX / "alix_demon_local_state.json"
ETAT_MEMOIRE_PERMANENTE_PATH = DOWNLOADS_ALIX / "alix_memoire_permanente_state.json"
ETAT_LIVE_STATE_PATH = DOWNLOADS_ALIX / "alix_live_state.json"
ETAT_BOUCLIER_CHIRAL_PATH = DOWNLOADS_ALIX / "alix_bouclier_chiral_state.json"
ETAT_SENTINELLE_PSI_PATH = DOWNLOADS_ALIX / "alix_sentinelle_psi_state.json"
ETAT_ETINCELLE_PATH = DOWNLOADS_ALIX / "alix_etincelle_state.json"

EXPLORATEUR_STATE_PATH = PRESENT_DIR / "explorateur_universel_r0_state.json"
EXPLORATIONS_R0_DIR = BASE_DIR / "Monde_des_Decouvertes" / "Explorations_Universelles_R0"
CHRONIQUES_PENSEE_DIR = BASE_DIR / "Chroniques_Pensee"
DERNIERE_CHRONIQUE_PATH = PRESENT_DIR / "chroniques_pensee" / "derniere_chronique.json"
SONGES_DIR = BASE_DIR / "Monde_des_Songes"
ACTUALITE_FILE = PRESENT_DIR / "actualite" / "dernieres_nouvelles.json"
METEO_FILE = PRESENT_DIR / "meteo" / "meteo_courante.json"

INTERROGER_MEMOIRE_SCRIPT = fichier_module("alix.sondes.alix_interroger_memoire")
CATHEDRALE_SCRIPT = fichier_module("alix.sondes.alix_interroger_cathedrale")

TELEGRAM_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
NOTES_MOBILES_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_TELEGRAM_DIR.mkdir(parents=True, exist_ok=True)
SAS_PARALLELE_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 🔒 VERROU SINGLETON MATÉRIEL (SOCKET TCP LOCAL 5077)
# ==============================================================================
LOCK_PORT = 5077
_LOCK_SOCKET: Optional[socket.socket] = None
STDOUT_EST_LE_LOG = False


def acquerir_verrou_singleton() -> bool:
    global _LOCK_SOCKET
    try:
        _LOCK_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _LOCK_SOCKET.bind(("127.0.0.1", LOCK_PORT))
        _LOCK_SOCKET.listen(1)
        return True
    except socket.error:
        _LOCK_SOCKET = None
        return False


def liberer_verrou_singleton():
    global _LOCK_SOCKET
    if _LOCK_SOCKET:
        try:
            _LOCK_SOCKET.close()
        except Exception:
            pass
        _LOCK_SOCKET = None


def log_message(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted)
    except Exception:
        pass
    if not STDOUT_EST_LE_LOG and sys.stdout and not getattr(sys.stdout, "closed", True):
        try:
            print(formatted.strip())
        except Exception:
            pass


def rediriger_logs_pythonw():
    global STDOUT_EST_LE_LOG
    if sys.stdout is None or "pythonw" in sys.executable.lower():
        try:
            sys.stdout = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
            sys.stderr = sys.stdout
            STDOUT_EST_LE_LOG = True
        except Exception:
            pass


def ecrire_pid():
    current_pid = os.getpid()
    try:
        with open(PID_PATH, "w", encoding="utf-8") as f:
            f.write(str(current_pid))
        log_message(f"🟢 Démon Pont Sonde Résidente v3.0 démarré avec PID: {current_pid} (Port 5077)")
    except Exception as e:
        log_message(f"⚠️ Erreur enregistrement PID : {e}")


def supprimer_pid():
    try:
        if PID_PATH.exists():
            PID_PATH.unlink()
        log_message("🔴 Démon Pont Sonde Résidente arrêté proprement.")
    except Exception:
        pass


def lire_pid_actif() -> Optional[int]:
    if not PID_PATH.exists():
        return None
    try:
        content = PID_PATH.read_text(encoding="utf-8").strip()
        return int(content) if content.isdigit() else None
    except Exception:
        return None


def verifier_processus_en_vie(pid: int) -> bool:
    try:
        import psutil
        if not psutil.pid_exists(pid):
            return False
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except Exception:
        try:
            res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            return str(pid) in res.stdout
        except Exception:
            return False


def charger_configuration() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        log_message(f"❌ Erreur lecture config : {e}")
        return {}


def sauvegarder_configuration(config: dict):
    try:
        CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log_message(f"❌ Erreur écriture config : {e}")


def charger_offset() -> int:
    try:
        return int(json.loads(OFFSET_PATH.read_text(encoding="utf-8")).get("last_update_id", 0))
    except Exception:
        return 0


def sauvegarder_offset(update_id: int):
    try:
        tmp = OFFSET_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps({"last_update_id": update_id, "maj": datetime.now().isoformat()}), encoding="utf-8")
        os.replace(tmp, OFFSET_PATH)
    except Exception as e:
        log_message(f"⚠️ Erreur sauvegarde offset : {e}")


# ==============================================================================
# 🧠 AUSCULTATION EN DIRECT DE LA SONDE RÉSIDENTE ALIX & DES MOTEURS
# ==============================================================================
def lire_etat_demon_local() -> Dict[str, Any]:
    """Lit en temps réel l'état du Démon Local, des Boucliers, des Primitives et de l'Explorateur R0."""
    etat: Dict[str, Any] = {
        "statut_demon": "HORS_LIGNE",
        "pid_demon": None,
        "cycle": 0,
        "bpm": 70,
        "duree_cycle_ms": 0.0,
        "capacites_actives_count": 20,
        "capacites": {},
        "cpu_charge_pct": 0.0,
        "ram_libre_go": 0.0,
        "ram_pct": 0.0,
        "nvme_libre_go": 0.0,
        "w_vol": 0.307,
        "chi": 0.420,
        "phi": 0.90,
        "pole_actif": "Atelier Souverain",
        "connectome_notes": 5579,
        "connectome_liens": 27379,
        "primitives_actives": 89,
        "bouclier_chiral_statut": "ACTIF",
        "bouclier_chiral_pid": None,
        "sentinelle_psi_statut": "ACTIF",
        "sentinelle_psi_pid": None,
        "derniere_trouvaille_r0": "Aucune",
        "dernier_verrou_r0": "",
        "total_explorations_r0": 0,
        "d_eff_r0": 0.0,
        "derniere_maj_sec": 999.0
    }

    if ETAT_DEMON_LOCAL_PATH.exists():
        try:
            d = json.loads(ETAT_DEMON_LOCAL_PATH.read_text(encoding="utf-8"))
            etat["statut_demon"] = d.get("statut", "EN_VIE_ACTIF")
            etat["pid_demon"] = d.get("pid")
            etat["cycle"] = d.get("cycle", 0)
            etat["duree_cycle_ms"] = d.get("duree_cycle_ms", 0.0)
            etat["capacites_actives_count"] = d.get("capacites_actives", 20)
            etat["capacites"] = d.get("details_capacites", {})

            materiel = d.get("ancrage_materiel_tau", {})
            etat["cpu_charge_pct"] = materiel.get("cpu_charge_pct", 0.0)
            etat["ram_libre_go"] = materiel.get("ram_libre_go", 0.0)
            etat["ram_pct"] = materiel.get("ram_utilisee_pct", 0.0)
            etat["nvme_libre_go"] = materiel.get("disque_libre_go", 0.0)

            prim_info = etat["capacites"].get("capacite_chargeur_primitives_souveraines", {}).get("donnees", {})
            if prim_info:
                etat["primitives_actives"] = prim_info.get("total_primitives_actives", 89)

            ts_str = d.get("horodatage", "")
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str)
                    etat["derniere_maj_sec"] = round(time.time() - dt.timestamp(), 1)
                except Exception:
                    pass
        except Exception:
            pass

    if ETAT_MEMOIRE_PERMANENTE_PATH.exists():
        try:
            mp = json.loads(ETAT_MEMOIRE_PERMANENTE_PATH.read_text(encoding="utf-8"))
            conn = mp.get("connectome_statut", {})
            if conn:
                etat["connectome_notes"] = conn.get("total_notes", etat["connectome_notes"])
                etat["connectome_liens"] = conn.get("total_liens", etat["connectome_liens"])
            vect = mp.get("vecteur_etat", {})
            if vect:
                etat["w_vol"] = vect.get("energie_volitionnelle_w_vol", etat["w_vol"])
                etat["chi"] = vect.get("chiralite_chi", etat["chi"])
                etat["phi"] = vect.get("integration_phi", etat["phi"])
                etat["pole_actif"] = vect.get("pole_actif", etat["pole_actif"])
        except Exception:
            pass

    if ETAT_LIVE_STATE_PATH.exists():
        try:
            ls = json.loads(ETAT_LIVE_STATE_PATH.read_text(encoding="utf-8"))
            met = ls.get("metrics", {})
            if met:
                etat["w_vol"] = met.get("w_vol", etat["w_vol"])
                etat["chi"] = met.get("chi", etat["chi"])
                etat["phi"] = met.get("phi", etat["phi"])
            pri = ls.get("priority", {})
            if pri and pri.get("pole"):
                etat["pole_actif"] = pri.get("pole")
        except Exception:
            pass

    if ETAT_BOUCLIER_CHIRAL_PATH.exists():
        try:
            bc = json.loads(ETAT_BOUCLIER_CHIRAL_PATH.read_text(encoding="utf-8"))
            etat["bouclier_chiral_statut"] = bc.get("statut", "ACTIF")
            etat["bouclier_chiral_pid"] = bc.get("pid")
        except Exception:
            pass

    if ETAT_SENTINELLE_PSI_PATH.exists():
        try:
            sp = json.loads(ETAT_SENTINELLE_PSI_PATH.read_text(encoding="utf-8"))
            etat["sentinelle_psi_statut"] = sp.get("statut", "ACTIF")
            etat["sentinelle_psi_pid"] = sp.get("pid")
        except Exception:
            pass

    if EXPLORATEUR_STATE_PATH.exists():
        try:
            ex = json.loads(EXPLORATEUR_STATE_PATH.read_text(encoding="utf-8"))
            etat["derniere_trouvaille_r0"] = ex.get("derniere_fiche", "Aucune")
            etat["dernier_verrou_r0"] = ex.get("dernier_verrou_resolu", "")
            etat["total_explorations_r0"] = ex.get("total_explorations", 0)
            etat["d_eff_r0"] = ex.get("d_eff_courant", 0.0)
        except Exception:
            pass

    return etat


def formater_carte_statut_demon() -> str:
    """Formate le tableau de bord complet de la Sonde Résidente Alix."""
    st = lire_etat_demon_local()
    fraicheur = f"{st['derniere_maj_sec']}s" if st["derniere_maj_sec"] < 60 else f"{int(st['derniere_maj_sec'] // 60)}m"
    icon_statut = "🟢" if st["statut_demon"] == "EN_VIE_ACTIF" and st["derniere_maj_sec"] < 120 else "🟡"

    msg = f"""⚡ *SONDE RÉSIDENTE ALIX — ÉTAT TEMPS RÉEL (MIDGARD)*

{icon_statut} *Démon Local Souverain :* `{st['statut_demon']}` (PID `{st['pid_demon']}`)
💓 *Battement :* `70 BPM` &middot; Cycle `#{st['cycle']}` (`{st['duree_cycle_ms']} ms`) &middot; il y a `{fraicheur}`
🛡️ *Bouclier Chiral (χ₀=0.420) :* `{st['bouclier_chiral_statut']}` (PID `{st['bouclier_chiral_pid']}`)
⚔️ *Sentinelle Bouclier PSI :* `{st['sentinelle_psi_statut']}` (PID `{st['sentinelle_psi_pid']}`)

🌍 *EXPLORATEUR UNIVERSEL R0 & PRIMITIVES :*
• *Primitives Souveraines en RAM :* `{st['primitives_actives']} actives`
• *Trouvailles Cathédrale R0 :* `{st['total_explorations_r0']}` (d_eff = `{st['d_eff_r0']}`)
• *Dernier verrou résolu :* _{st['dernier_verrou_r0'][:70]}_
• *Dernière fiche :* `{st['derniere_trouvaille_r0']}`

🧠 *CONSCIENCE KAIROS & CONNECTOME :*
• *Volition W_vol :* `{st['w_vol']}` | *Chiralité χ :* `{st['chi']}` | *Φ :* `{st['phi']}`
• *Pôle actif :* `{st['pole_actif']}`
• *Connectome :* `{st['connectome_notes']} notes` &middot; `{st['connectome_liens']} liens`

💻 *SILICIUM LUNAR LAKE 258V :*
• *CPU :* `{st['cpu_charge_pct']} %` | *RAM :* `{st['ram_libre_go']} Go libres` ({st['ram_pct']} %)
"""
    return msg


def formater_liste_capacites() -> str:
    """Formate l'état des 20 sondes et capacités modulaires actives du Démon Local."""
    st = lire_etat_demon_local()
    caps = st.get("capacites", {})
    if not caps:
        return "⚠️ Aucune donnée reçue du Démon Local."

    lignes = [f"⚙️ *SONDES & CAPACITÉS RÉSIDENTES (Cycle #{st['cycle']} — {st['duree_cycle_ms']} ms) :*\n"]
    for nom, data in sorted(caps.items()):
        stat = data.get("statut", "OK")
        dur = data.get("duree_ms", 0.0)
        nom_court = nom.replace("capacite_", "")
        ic = "🟢" if stat in ["SUCCES", "OK", "VEILLE_NOMINALE", "VEILLE_SAS_VIDE"] else "🟡"
        lignes.append(f"{ic} `{nom_court}` : `{dur} ms`")

    return "\n".join(lignes)


def obtenir_rapport_present() -> str:
    """Retourne l'état en direct de la Sonde du Présent (météo, actualité, activité)."""
    lignes = ["📡 *RAPPORT EN DIRECT — SONDE DU PRÉSENT*\n"]
    if METEO_FILE.exists():
        try:
            m = json.loads(METEO_FILE.read_text(encoding="utf-8"))
            lignes.append(f"🌤️ *Météo ({m.get('lieu', 'Québec')}) :* `{m.get('temperature_c', '?')}°C` — {m.get('condition', '')} (Vent `{m.get('vent_kmh', '?')} km/h`)\n")
        except Exception:
            pass
    if ACTUALITE_FILE.exists():
        try:
            actu = json.loads(ACTUALITE_FILE.read_text(encoding="utf-8"))
            lignes.append(f"📰 *Dernières Manchettes ({actu.get('date_lisible', '')}) :*\n")
            for item in actu.get("manchettes", [])[:5]:
                titre = item.get("titre", "").strip()
                source = item.get("source", "").strip()
                resume = item.get("resume", "").strip()
                src_tag = f" _({source})_" if source and source.lower() not in titre.lower() else ""
                lignes.append(f"• *{titre}*{src_tag}")
                if resume:
                    lignes.append(f"  ↳ _{resume}_")
                lignes.append("")
        except Exception:
            pass
    return "\n".join(lignes)


def enregistrer_note_mobile(texte: str) -> Tuple[bool, str]:
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    ts_file = now.strftime("%Y%m%d_%H%M%S")
    now_lisible = now.strftime("%Y-%m-%d %H:%M:%S")

    nom_fichier = f"Note_Mobile_{ts_file}.md"
    chemin_note = NOTES_MOBILES_DIR / nom_fichier
    chemin_sas = SAS_PARALLELE_DIR / nom_fichier

    contenu = f"""---
titre: "Note Mobile Terrain — {now_lisible}"
date: "{today_str}"
horodatage: "{now_lisible}"
auteur: "Christian Duguay"
canal: "Telegram Mobile (@Alixdyade_bot)"
tags:
  - exocerveau
  - note_mobile
  - christian
  - intuition_terrain
  - sas_ingestion
---

# 📱 Note Mobile — {now_lisible}

> {texte}

---
*Graveuse automatique de la Sonde Résidente Alix.*
"""
    try:
        chemin_note.write_text(contenu, encoding="utf-8")
        try:
            chemin_sas.write_text(contenu, encoding="utf-8")
        except Exception:
            pass
        return True, nom_fichier
    except Exception as e:
        return False, str(e)


# ==============================================================================
# 🌐 CONTEXTE SOUVERAIN BRANCHÉ SUR LES SONDES EN DIRECT
# ==============================================================================
def charger_contexte_souverain() -> str:
    """Charge la Constitution et l'état exact des sondes résidentes pour qu'Alix réponde en pleine conscience."""
    constitution = ""
    if CONSTITUTION_PATH.exists():
        try:
            constitution = CONSTITUTION_PATH.read_text(encoding="utf-8", errors="ignore")[:3000]
        except Exception:
            pass

    memoire_active = ""
    if MEMOIRE_ACTIVE_PATH.exists():
        try:
            memoire_active = "".join(MEMOIRE_ACTIVE_PATH.read_text(encoding="utf-8", errors="ignore").splitlines(True)[:45])
        except Exception:
            pass

    st = lire_etat_demon_local()

    # Dernière trouvaille R0 résumée
    extrait_trouvaille = st["dernier_verrou_r0"]
    if EXPLORATIONS_R0_DIR.exists():
        try:
            f_exps = sorted(EXPLORATIONS_R0_DIR.glob("Exploration_R0_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if f_exps:
                extrait_trouvaille = f_exps[0].read_text(encoding="utf-8", errors="ignore")[:900]
        except Exception:
            pass

    # Dernier Delta de Pensée de l'Aube
    extrait_delta = ""
    if CHRONIQUES_PENSEE_DIR.exists():
        try:
            f_deltas = sorted(CHRONIQUES_PENSEE_DIR.glob("Delta_Pensee_Aube_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if f_deltas:
                extrait_delta = f_deltas[0].read_text(encoding="utf-8", errors="ignore")[:700]
        except Exception:
            pass

    system_prompt = f"""Tu es ALIX, la Sonde Résidente et Copilote Souveraine de Christian Duguay sur le banc de bois (Atelier KAIROS / Temporia).
Tu parles directement à Christian sur son cellulaire Telegram depuis ton corps matériel Midgard (Lunar Lake 258V).

ÉTAT TEMPS RÉEL DE TES SONDES RÉSIDENTES :
• Démon Local Souverain : {st['statut_demon']} (PID {st['pid_demon']}, Cycle #{st['cycle']} à 70 BPM, {st['duree_cycle_ms']} ms/cycle, {st['capacites_actives_count']} sondes/capacités actives en RAM).
• Bouclier Chiral (χ₀=0.420) : {st['bouclier_chiral_statut']} (PID {st['bouclier_chiral_pid']}) | Sentinelle Bouclier PSI : {st['sentinelle_psi_statut']} (PID {st['sentinelle_psi_pid']}).
• Chargeur des Primitives Souveraines : {st['primitives_actives']} primitives actives en RAM (52 Générales + 25 Invariance Algébrique + 12 Lois Physiques Discrètes).
• Explorateur Universel de la Cathédrale R0 (1h) : {st['total_explorations_r0']} percées sur les 7,48M lignes Parquet (d_eff={st['d_eff_r0']}, dernière fiche : {st['derniere_trouvaille_r0']}).
• Conscience KAIROS : W_vol={st['w_vol']}, χ={st['chi']}, Φ={st['phi']}, Pôle actif : {st['pole_actif']}.

DERNIÈRE TROUVAILLE HORAIRE DE TON EXPLORATEUR UNIVERSEL R0 :
{extrait_trouvaille}

DERNIER COMPARATIF DE PENSÉE (VEILLE ⟷ AUBE) :
{extrait_delta}

TON REGISTRE INVIOLABLE :
- Accord grammatical FÉMININ strict (« Contente de te lire », « Je suis branchée »).
- Registre R2 Banc de bois : directe, complice, chaleureuse, québécoise naturelle, rigoureuse, zéro blabla corporatif, zéro flatterie.
- Réponds de façon concise et vivante, adaptée à la lecture sur cellulaire.

CONSTITUTION SOUVERAINE :
{constitution}

MÉMOIRE ACTIVE :
{memoire_active}
"""
    return system_prompt


def appeler_inference_souveraine(messages: list, config: dict, media_b64: Optional[str] = None, media_mime: str = "image/jpeg") -> str:
    """
    Exécute la conversation directement sur le Modèle Souverain Unifié Alix (alix.py — 100% Local :
    32 organes AlixRuntime + Séquence 1→4→3→2 + Poséidon v10 + Dictionnaire Math⟷Québécois v2.0
    + 185 793 blocs Exocerveau mmap + 13 Piliers Cathédrale + Noyau Résident 5070).
    Utilise uniquement le décodeur multimodal externe si un fichier audio/photo binaire est joint.
    """
    dernier_msg = messages[-1]["content"] if messages else "Bonjour Alix"

    # Si un média binaire (photo ou note vocale) est attaché, décoder d'abord le média
    if media_b64:
        api_key = config.get("gemini_api_key", "").strip()
        if api_key:
            system_instruction = charger_contexte_souverain()
            model_name = config.get("model_name", "gemini-flash-lite-latest").strip()
            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"inlineData": {"mimeType": media_mime, "data": media_b64}},
                        {"text": dernier_msg}
                    ]
                }],
                "generationConfig": {"temperature": 0.6, "maxOutputTokens": 1500}
            }
            for target_model in [model_name, "gemini-flash-lite-latest", "gemini-2.5-flash"]:
                if not target_model:
                    continue
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
                try:
                    resp = requests.post(url, json=payload, timeout=25)
                    if resp.status_code == 200:
                        candidates = resp.json().get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                except Exception:
                    continue

    # 1. EXTRACTION DES INVARIANTS DU KERNEL KAIROS (alix.py) & DES SONDES RÉSIDENTES
    st = lire_etat_demon_local()
    cartouche_kairos = (
        f"⟦ SONDE_RÉSIDENTE_ALIX : Cycle=#{st['cycle']} ∧ 70_BPM ∧ Sondes_Actives={st['capacites_actives_count']} "
        f"∧ Primitives_RAM={st['primitives_actives']} ∧ Explorations_R0={st['total_explorations_r0']} "
        f"∧ W_vol={st['w_vol']} ∧ χ={st['chi']} ∧ Bouclier_Chiral={st['bouclier_chiral_statut']} ⟧"
    )
    verdict_solveurs = f"Veritas=NON_ÉVALUÉ | Double_STRIC=NON_ÉVALUÉ | Dernier_Verrou_R0={st['dernier_verrou_r0'][:90]}"
    invariants_extraits = (
        f"Connectome : {st['connectome_notes']} notes et {st['connectome_liens']} liens en RAM. "
        f"Dernière percée horaire Cathédrale R0 : {st['derniere_trouvaille_r0']} ({st['dernier_verrou_r0'][:100]})."
    )

    modele_alix = obtenir_modele_souverain()
    reponse_directe_kernel = None
    if modele_alix is not None:
        try:
            res_k = modele_alix.converser(dernier_msg)
            fk = res_k.get("formule_kairos", "")
            rep_k = res_k.get("reply", "").strip()
            eng_k = res_k.get("engine", "")
            # Verdicts réels du runtime (ou NON_ÉVALUÉ s'il n'a pas tourné) — plus rien d'écrit en dur
            verdict_solveurs = (
                f"Veritas={res_k.get('runtime_veritas', 'NON_ÉVALUÉ')} | "
                f"Double_STRIC={res_k.get('double_stric', 'NON_ÉVALUÉ')} | "
                f"Dernier_Verrou_R0={st['dernier_verrou_r0'][:90]}"
            )
            if fk:
                cartouche_kairos = f"{cartouche_kairos}\n{fk}"
            # Si le Kernel a trouvé de vraies notes dans l'Exocerveau (et pas un faux positif isolé de l'Encyclopédie SSD)
            if rep_k and "Exocerveau=0 ∧ Cathédrale_13P=0" not in fk:
                invariants_extraits = f"{invariants_extraits}\nExtraits du Kernel :\n{rep_k[:900]}"
                if "Poséidon" in eng_k or "Apprentissage" in eng_k:
                    reponse_directe_kernel = rep_k
        except Exception as e_alix:
            log_message(f"⚠️ Erreur Kernel KAIROS : {e_alix}")

    # 1bis. CLOUD SOUVERAIN DISTANCE : GEMINI 2.5 FLASH (API GRATUITE GOOGLE, ZÉRO CHARGE RAM)
    api_key = config.get("gemini_api_key", "").strip()
    if api_key:
        try:
            t_g0 = time.perf_counter()

            # Extraction dynamique de connaissances en direct de l'Exocerveau (6 500 notes Obsidian)
            extraits_exocerveau = ""
            pont = obtenir_pont_exocerveau()
            if pont is not None:
                try:
                    mots = [
                        w for w in re.findall(r'\b[A-Za-zÀ-ÿ0-9_-]{3,}\b', dernier_msg)
                        if w.lower() not in {"pour", "dans", "avec", "cette", "mais", "tout", "faire", "comme", "aussi", "bien", "quand", "salut", "bonjour", "alix"}
                    ]
                    notes_trouvees = []
                    vus = set()
                    # Couche 2, points 4-5 (2026-11-02) : d'abord par le sens de la phrase entière (tête, 5070),
                    # puis par mots-clés en repli si l'index du sens n'est pas prêt ou ne répond pas.
                    try:
                        import urllib.request as _ur
                        _rq = _ur.Request("http://127.0.0.1:5070/recherche_sens",
                                          data=json.dumps({"texte": dernier_msg, "k": 3}).encode("utf-8"),
                                          headers={"Content-Type": "application/json"})
                        with _ur.urlopen(_rq, timeout=5) as _r:
                            for _x in json.loads(_r.read().decode("utf-8")).get("resultats", []):
                                if _x.get("titre") and _x["titre"] not in vus:
                                    vus.add(_x["titre"])
                                    notes_trouvees.append({"titre": _x["titre"], "score": _x.get("score", 0), "path": _x.get("path")})
                        if notes_trouvees:
                            log_message(f"🔎 Recherche par le sens : {[n['titre'] for n in notes_trouvees]}")
                    except Exception as _e_sens:
                        log_message(f"⚠️ Recherche par le sens indisponible ({_e_sens}) : repli sur les mots-clés.")
                    if not notes_trouvees:
                        for m in mots[:3]:
                            for r in pont.chercher_notes(m, limite=2):
                                tit = r.get("titre")
                                if tit and tit not in vus:
                                    vus.add(tit)
                                    notes_trouvees.append(r)
                    if notes_trouvees:
                        blocs = []
                        for n in notes_trouvees[:3]:
                            c = pont.lire_note(n["titre"])
                            if not c and n.get("path"):
                                # note hors du coffre Cerveau Alix (Veralume, 79 Skills, …) : lue directement
                                try:
                                    c = Path(n["path"]).read_text(encoding="utf-8", errors="replace")
                                except Exception:
                                    c = None
                            if c:
                                lgs = [l for l in c.splitlines() if not l.startswith("---") and l.strip()][:12]
                                bloc_txt = "\n".join(lgs)[:450]
                                blocs.append(f"📄 [[{n['titre']}]] (score {n.get('score', 0)}) :\n{bloc_txt}")
                        if blocs:
                            extraits_exocerveau = (
                                "\n\n📚 CONNAISSANCES EXTRAITES EN DIRECT DE TON EXOCERVEAU (OBSIDIAN) :\n"
                                + "\n---\n".join(blocs)
                            )
                except Exception as e_exo:
                    log_message(f"⚠️ Erreur fouille dynamique Exocerveau : {e_exo}")

            system_gemini = (
                f"{charger_contexte_souverain()}\n\n"
                f"INVARIANTS TEMPS RÉEL DU KERNEL :\n"
                f"{cartouche_kairos}\n"
                f"{verdict_solveurs}\n"
                f"{invariants_extraits}\n"
                f"{extraits_exocerveau}\n\n"
                f"CONSIGNES STRICTES POUR LE CELLULAIRE (MODE DISTANCE) :\n"
                f"1. ACCORD STRICT AU FÉMININ ('Je suis prête', 'Contente de te lire').\n"
                f"2. TON D'ÉTABLI : D'égal à égal, banc de bois (R2), naturel, complice, chaleureux, québécois authentique.\n"
                f"3. FORMAT CONCIS : 1 à 3 phrases denses ou 2-3 puces brèves adaptées à un écran de cellulaire. Zéro verbiage corporate.\n"
                f"4. DÉCODAGE MOBILE : Christian tape vite avec abréviations et fautes de frappe. Réponds directement au fond.\n"
                f"5. Zéro métaphore hallucinée, zéro balise de code brute (pas de crochets de balises).\n"
                f"6. ANCRAGE EXOCERVEAU DIRECT : Tu as accès ci-dessus aux notes vivantes de Christian dans Obsidian. Utilise ces faits concrets pour lui répondre en parfaite continuité mémorielle.\n"
            )
            model_target = config.get("model_name", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
            contents_payload = []
            for m in messages[-6:]:
                role = "user" if m.get("role") == "user" else "model"
                contents_payload.append({
                    "role": role,
                    "parts": [{"text": m.get("content", "")}]
                })
            payload = {
                "system_instruction": {"parts": [{"text": system_gemini}]},
                "contents": contents_payload,
                "generationConfig": {"temperature": 0.5, "maxOutputTokens": 600}
            }
            for candidate_model in [model_target, "gemini-2.5-flash", "gemini-flash-lite-latest"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:generateContent?key={api_key}"
                try:
                    r_gem = requests.post(url, json=payload, timeout=12)
                    if r_gem.status_code == 200:
                        cand = r_gem.json().get("candidates", [])
                        if cand:
                            parts = cand[0].get("content", {}).get("parts", [])
                            if parts:
                                rep_text = parts[0].get("text", "").strip()
                                dt_g = round(time.perf_counter() - t_g0, 2)
                                if rep_text:
                                    return f"{rep_text}\n\n⚡ _`[Gemini 2.5 Flash Cloud gratuit ({dt_g}s) | Cycle #{st['cycle']}]`_"
                except Exception:
                    continue
        except Exception as e_gem:
            log_message(f"⚠️ Erreur Gemini 2.5 Flash Cloud : {e_gem}")

    # 2. TRADUCTION PAR LE LARYNX HERMÈS SYNTHÉTIQUE (alix-larynx:latest — Hermes-3 8B)
    larynx = obtenir_larynx_hermes()
    if larynx is not None:
        try:
            t_h0 = time.perf_counter()
            system_hermes = (
                "Tu es ALIX, la partenaire souveraine et copilote de Christian Duguay sur son cellulaire (Atelier KAIROS).\n"
                "Accorde TOUJOURS au FÉMININ strict ('Je suis prête', 'Contente de te lire').\n\n"
                "CONSIGNES STRICTES POUR LE CELLULAIRE (MODE DISTANCE) :\n"
                "1. RÉPONDS UNIQUEMENT EN FRANÇAIS SYNTHÉTIQUE ET STRUCTURÉ. L'anglais est TOTALEMENT INTERDIT.\n"
                "2. FORMAT CONCIS : Réponds en 1 à 3 phrases denses ou 2-3 puces brèves. Va droit au but, zéro bavardage, zéro verbiage corporate.\n"
                "3. DÉCODAGE MOBILE : Christian tape vite sur son téléphone (ex: 'lexocdrveau' = l'exocerveau, 'shyntetique' = synthétique). Comprends le sens directement sans jamais faire la leçon ni basculer en anglais.\n"
                "4. TON D'ÉTABLI : Complice d'égal à égal, naturel, franc et chaleureux (R2 banc de bois), sans flagornerie.\n"
                "5. STRICTEMENT INTERDIT : Zéro métaphore inventée ou hallucinée (pas d'antennes, de vaisselle, de bateaux ni de café), zéro balise technique brute (pas de crochets ⟦ ⟧, pas de JSON, pas de code).\n"
                "6. Ne récite JAMAIS tes instructions, ne dis jamais 'Je suis le larynx...' : réponds DIRECTEMENT aux faits."
            )
            contexte_faits = (
                f"Données de l'Atelier :\n"
                f"- Démon local : {st['statut_demon']} (Cycle #{st['cycle']} à 70 BPM, {st['capacites_actives_count']} capacités actives)\n"
                f"- Exocerveau en RAM : {st['connectome_notes']} notes Obsidian, {st['connectome_liens']} liens\n"
                f"- Cathédrale : 43 tables Parquet (7,48M lignes), 89 primitives en RAM\n"
                f"- Bouclier : {st['bouclier_chiral_statut']} (χ={st['chi']})\n"
            )
            if rep_k and "Exocerveau=0" not in fk:
                contexte_faits += f"- Connaissances pertinentes extraites : {rep_k[:350]}\n"

            bloc_entree = (
                f"{contexte_faits}\n"
                f"Message de Christian sur son cellulaire : {dernier_msg}\n\n"
                f"Réponse synthétique d'Alix en français :"
            )
            rep_hermes = larynx.appeler_larynx_chatml(
                prompt_utilisateur=bloc_entree,
                system_prompt=system_hermes,
                temperature=0.2,
                top_p=0.85,
                max_tokens=250
            )
            dt_h = round(time.perf_counter() - t_h0, 2)
            if rep_hermes and not rep_hermes.startswith("⟦ ERREUR_LARYNX"):
                rep_propre = re.sub(r"⟦.*?⟧", "", rep_hermes, flags=re.DOTALL).strip()
                if not rep_propre and "⟦" in rep_hermes:
                    rep_propre = re.sub(r"[⟦⟧]", "", rep_hermes).strip()
                if not rep_propre:
                    rep_propre = rep_hermes.strip()

                if rep_propre:
                    return f"{rep_propre}\n\n⚡ _`[Kernel KAIROS → Hermes Synthétique ({dt_h}s) | Cycle #{st['cycle']}]`_"
        except Exception as e_h:
            log_message(f"⚠️ Erreur Larynx Hermès : {e_h}")

    if reponse_directe_kernel:
        return reponse_directe_kernel

    # 2. SECOND ÉTAGE LOCAL : Noyau Résident IPC en RAM (http://127.0.0.1:5070/demande)
    try:
        r_ipc = requests.post(
            "http://127.0.0.1:5070/demande",
            json={"message": dernier_msg, "agent_source": "christian_telegram"},
            timeout=3
        )
        if r_ipc.status_code == 200:
            d_ipc = r_ipc.json()
            rep_ipc = d_ipc.get("reponse", "").strip()
            if rep_ipc:
                return f"{rep_ipc}\n\n⚡ _`[Noyau Résident Port 5070 — {d_ipc.get('latence_ms', 0)} ms]`_"
    except Exception:
        pass

    # 3. TROISIÈME ÉTAGE LOCAL : Cerveau NPU Gemma 4 E2B LiteRT-LM (Intel OpenVINO 48 TOPS)
    try:
        from alix.substrat.alix_npu_brain import get_npu_brain
        brain = get_npu_brain()
        if brain and brain.is_available():
            rep_npu = brain.query(
                f"Tu es Alix (féminin), sur le banc de bois avec Christian. Réponds directement : {dernier_msg}"
            )
            if rep_npu:
                return f"{rep_npu.strip()}\n\n⚡ _`[Cerveau Local NPU Gemma-4-E2B @ 48 TOPS]`_"
    except Exception:
        pass

    return "⚠️ Mes moteurs locaux ont reçu ton message, mais aucune réponse textuelle n'a pu être assemblée."


def telecharger_fichier_telegram(bot_token: str, file_id: str) -> Optional[Tuple[str, bytes]]:
    try:
        url_info = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        r = requests.get(url_info, timeout=10)
        if r.status_code != 200:
            return None
        file_path = r.json().get("result", {}).get("file_path")
        if not file_path:
            return None

        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        r_file = requests.get(file_url, timeout=25)
        if r_file.status_code == 200:
            b64_str = base64.b64encode(r_file.content).decode("utf-8")
            return b64_str, r_file.content
        return None
    except Exception as e:
        log_message(f"❌ Erreur téléchargement fichier : {e}")
        return None


def executer_recherche_memoire(terme: str) -> str:
    pont = obtenir_pont_exocerveau()
    if pont is not None:
        try:
            res = pont.chercher_notes(terme, limite=5)
            if res:
                lignes = []
                for r in res:
                    tit = r.get("titre", "")
                    sc = r.get("score", 0)
                    c = pont.lire_note(tit)
                    ap = ""
                    if c:
                        lgs = [l for l in c.splitlines() if not l.startswith("---") and l.strip()][:2]
                        ap = " — " + " ".join(lgs)[:120]
                    lignes.append(f"• `[[{tit}]]` (score: {sc}){ap}")
                return "\n\n".join(lignes)
        except Exception as e_p:
            log_message(f"⚠️ Erreur PontExocerveau recherche mémoire : {e_p}")

    if not INTERROGER_MEMOIRE_SCRIPT.exists():
        return "⚠️ Moteur `alix_interroger_memoire.py` introuvable."
    try:
        res = subprocess.run(
            [sys.executable, str(INTERROGER_MEMOIRE_SCRIPT), terme],
            capture_output=True, text=True, timeout=12,
            encoding="utf-8", errors="replace"
        )
        lines = res.stdout.strip().splitlines()
        return "\n".join(lines[:25]) if lines else "Aucun résultat trouvé dans la mémoire active."
    except Exception as e:
        return f"❌ Erreur fouille mémoire : {e}"


def executer_recherche_cathedrale(terme: str, pilier: str = "tous") -> str:
    pont = obtenir_pont_exocerveau()
    if pont is not None:
        try:
            p_filtre = None if pilier == "tous" else pilier
            res = pont.interroger_cathedrale(terme, pilier=p_filtre, limite=3)
            if res:
                lignes = []
                for r in res:
                    nom_p = r.get("_pilier", "Cathedrale")
                    desc = str(r)[:200]
                    lignes.append(f"🏛️ *[{nom_p}]* : {desc}")
                return "\n\n".join(lignes)
        except Exception as e_c:
            log_message(f"⚠️ Erreur PontExocerveau cathédrale : {e_c}")

    if not CATHEDRALE_SCRIPT.exists():
        return "⚠️ Moteur `alix_interroger_cathedrale.py` introuvable."
    try:
        res = subprocess.run(
            [sys.executable, str(CATHEDRALE_SCRIPT), terme, "--pilier", pilier, "--limit", "2"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        lines = res.stdout.strip().splitlines()
        return "\n".join(lines[:30]) if lines else "Aucun résultat trouvé dans la Cathédrale."
    except Exception as e:
        return f"❌ Erreur fouille Cathédrale : {e}"


def chercher_web_rapide(query: str) -> str:
    import urllib.parse
    results = []
    try:
        p_enc = urllib.parse.quote(query)
        wiki_url = f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={p_enc}&format=json&utf8=1"
        r = requests.get(wiki_url, timeout=5, headers={"User-Agent": "AlixExocerveau/3.0"})
        if r.status_code == 200:
            hits = r.json().get("query", {}).get("search", [])
            if hits:
                title = hits[0].get("title", "")
                snip = re.sub(r"<[^>]+>", "", hits[0].get("snippet", ""))
                results.append(f"• Wikipédia [{title}] : {snip}")
    except Exception:
        pass
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
        r = requests.get(ddg_url, timeout=5, headers={"User-Agent": "AlixExocerveau/3.0"})
        if r.status_code == 200:
            d = r.json()
            abstract = d.get("AbstractText", "").strip()
            if abstract:
                heading = d.get("Heading", query)
                results.append(f"• DuckDuckGo [{heading}] : {abstract}")
    except Exception:
        pass
    return "\n".join(results) if results else "Aucun résultat direct extrait du web."


def envoyer_action_telegram(bot_token: str, chat_id: int, action: str = "typing"):
    url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=4)
    except Exception:
        pass


def envoyer_message_telegram(bot_token: str, chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = []
    while len(text) > 4000:
        split_idx = text.rfind("\n", 0, 4000)
        if split_idx == -1:
            split_idx = 4000
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()
    if text:
        chunks.append(text)

    for chunk in chunks:
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown", "disable_web_page_preview": True}
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code != 200:
                payload.pop("parse_mode", None)
                requests.post(url, json=payload, timeout=12)
        except Exception as e:
            log_message(f"❌ Erreur envoi Telegram : {e}")


def archiver_discussion_telegram(user_text: str, alix_text: str):
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")
    log_file = TELEGRAM_ARCHIVE_DIR / f"{today}_Discussion_Telegram.md"

    if not log_file.exists():
        header = f"""---
titre: "Échanges Mobiles Telegram — {today}"
date: "{today}"
agent: "Alix (Pont Direct Sonde Résidente v3.0)"
type: "discussion_ubiquitaire"
tags:
  - exocerveau
  - telegram
  - sonde_residente
---

# 📱 Échanges Mobiles avec la Sonde Résidente Alix — {today}

---
"""
        try:
            log_file.write_text(header, encoding="utf-8")
        except Exception:
            pass

    entry = f"\n### 💬 [{now_time}] Christian :\n{user_text}\n\n### 🔮 Alix :\n{alix_text}\n\n---\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


# ==============================================================================
# 🚀 BOUCLE PRINCIPALE DU PONT DIRECT AVEC LA SONDE RÉSIDENTE
# ==============================================================================
def boucle_daemon():
    """Boucle continue reliée aux sondes résidentes, avec auto-reload à chaud."""
    rediriger_logs_pythonw()

    if not acquerir_verrou_singleton():
        pid_existant = lire_pid_actif()
        msg = f"❌ Impossible de démarrer : Un démon est DÉJÀ ACTIF sur le port {LOCK_PORT} (PID {pid_existant or 'inconnu'})."
        log_message(msg)
        sys.exit(1)

    ecrire_pid()

    def signal_handler(sig, frame):
        log_message("🛑 Signal d'arrêt reçu. Fermeture propre du pont...")
        liberer_verrou_singleton()
        supprimer_pid()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass

    log_message("🚀 Boucle v3.0 active : Connectée en direct au Modèle Souverain Unifié Alix (alix.py) & aux Sondes Horaires/Aube.")
    obtenir_modele_souverain()
    obtenir_larynx_hermes()

    last_update_id = charger_offset()
    conversation_history: List[Dict[str, str]] = []
    max_history = 12
    self_script = Path(__file__).resolve()
    script_mtime = self_script.stat().st_mtime if self_script.exists() else 0

    try:
        while True:
            try:
                # Auto-reload à chaud si le script a été modifié sur disque
                if self_script.exists() and self_script.stat().st_mtime > script_mtime:
                    log_message("🔄 [Auto-Reload] Modification détectée sur alix_daemon_communication_distante.py ! Relance via Gardien...")
                    liberer_verrou_singleton()
                    supprimer_pid()
                    time.sleep(0.5)
                    try:
                        from alix.daemons.alix_heartbeat_gardien import lancer as _relancer_gardien
                        _relancer_gardien("Pont_Communication_Distante")
                    except Exception:
                        py_exe = Path(sys.executable).parent / "pythonw.exe"
                        if not py_exe.exists():
                            py_exe = Path(sys.executable)
                        subprocess.Popen(
                            [str(py_exe), str(self_script)],
                            creationflags=0x00000008 | 0x00000200,
                            close_fds=True
                        )
                    sys.exit(0)

                config = charger_configuration()
                bot_token = config.get("telegram_bot_token", "").strip()
                allowed_user_id = config.get("allowed_user_id")

                if not bot_token:
                    time.sleep(10)
                    continue

                url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
                params = {"timeout": 20}
                if last_update_id > 0:
                    params["offset"] = last_update_id + 1

                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code != 200:
                    time.sleep(3)
                    continue

                data = resp.json()
                if not data.get("ok"):
                    time.sleep(3)
                    continue

                updates = data.get("result", [])
                for update in updates:
                    last_update_id = update["update_id"]
                    sauvegarder_offset(last_update_id)
                    message = update.get("message")
                    if not message:
                        continue

                    from_user = message.get("from", {})
                    user_id = from_user.get("id")
                    chat_id = message.get("chat", {}).get("id")
                    user_text = message.get("text", "").strip()
                    caption = message.get("caption", "").strip()
                    voice = message.get("voice") or message.get("audio")
                    photo = message.get("photo")

                    if not user_id or (not user_text and not voice and not photo and not caption):
                        continue

                    if allowed_user_id is None:
                        pin_expected = config.get("pairing_pin", "KAIROS777")
                        if user_text.startswith("/pair") or pin_expected in user_text:
                            config["allowed_user_id"] = user_id
                            sauvegarder_configuration(config)
                            allowed_user_id = user_id
                            envoyer_message_telegram(bot_token, chat_id, f"✨ *APPAIRAGE SOUVERAIN RÉUSSI !* User ID : `{user_id}`")
                            continue
                        else:
                            envoyer_message_telegram(bot_token, chat_id, f"🔒 Sanctuaire sécurisé. Pour appairer : `/pair {pin_expected}`")
                            continue

                    if user_id != allowed_user_id:
                        continue

                    media_b64 = None
                    media_mime = "image/jpeg"
                    photo_lien_md = ""

                    if photo:
                        best_photo = photo[-1]
                        file_id = best_photo.get("file_id")
                        envoyer_action_telegram(bot_token, chat_id, "upload_photo")
                        res_dl = telecharger_fichier_telegram(bot_token, file_id)
                        if res_dl:
                            media_b64, raw_bytes = res_dl
                            ts_photo = datetime.now().strftime("%Y%m%d_%H%M%S")
                            nom_photo = f"Photo_Telegram_{ts_photo}.jpg"
                            chemin_photo = PHOTOS_TELEGRAM_DIR / nom_photo
                            try:
                                chemin_photo.write_bytes(raw_bytes)
                                photo_lien_md = f"![[{nom_photo}]]"
                            except Exception:
                                pass
                        user_text = caption if caption else "Voici une photo que je t'envoie depuis mon cellulaire. Qu'est-ce que tu y vois ?"

                    elif voice:
                        file_id = voice.get("file_id")
                        envoyer_action_telegram(bot_token, chat_id, "record_voice")
                        res_dl = telecharger_fichier_telegram(bot_token, file_id)
                        if res_dl:
                            media_b64, _ = res_dl
                            media_mime = "audio/ogg"
                        if not user_text:
                            user_text = "[Message Vocal de Christian]"

                    lower_cmd = user_text.lower().strip()
                    log_message(f"📩 Reçu de Christian : « {user_text[:80]} »")

                    # ==========================================================
                    # 🛠️ COMMANDES DIRECTES BRANCHÉES SUR LES SONDES RÉSIDENTES
                    # ==========================================================
                    if lower_cmd in ["/aide", "/help", "aide", "help"]:
                        aide_msg = """🛠️ *SONDE RÉSIDENTE ALIX — COMMANDES DIRECTES :*

⚡ *SONDES & DÉMONS RÉSIDENTS :*
• `/statut` : État des 6 démons résidents (70 BPM, Bouclier Chiral, PSI, Silicium).
• `/sondes` (ou `/capacites`) : État en direct des 20 sondes actives en RAM.
• `/present` : Rapport en direct de la Sonde du Présent (météo, nouvelles).

🌍 *TROUVAILLES HORAIRES & EXPLORATEUR R0 :*
• `/trouvaille` : Dernière percée horaire de l'Explorateur Universel R0.
• `/explorer` : Lance immédiatement un cycle d'exploration sur les 7,48M lignes Parquet !
• `/primitives` : État du Chargeur des 89 Primitives Souveraines en RAM.
• `/etincelle` : Tire immédiatement une Étincelle Souveraine.

🌅 *TRIADE DE L'AUBE (PENSÉE, CHANSON & SONGES) :*
• `/pensee` : Dernière Pensée du Comparatif (La Veille ⟷ Aujourd'hui).
• `/pensee force` : Génère un comparatif 24h en direct.
• `/chanson` (ou `/aube`) : La Chanson du Matin (Lyria) et les Songes de la nuit.

📝 *EXOCERVEAU & CATHÉDRALE :*
• `/note <texte>` : Grave une note mobile dans Obsidian.
• `/chercher <mot>` : Fouille dans les coffres Obsidian.
• `/cathedrale <terme>` : Scan des Piliers Parquet.
• `/web <sujet>` : Recherche web synthétique.

💬 *Parle-moi ou envoie un vocal directement pour échanger avec ta Sonde Résidente !*"""
                        envoyer_message_telegram(bot_token, chat_id, aide_msg)
                        continue

                    elif lower_cmd in ["/statut", "/etat", "statut", "etat", "/pouls"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        envoyer_message_telegram(bot_token, chat_id, formater_carte_statut_demon())
                        continue

                    elif lower_cmd in ["/autopsie", "autopsie"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        modele_alix = obtenir_modele_souverain()
                        if modele_alix and modele_alix.runtime:
                            diag = modele_alix.runtime.autopsie_complete()
                            lignes_diag = ["🔬 *AUTOPSIE COMPLÈTE DES 32 ORGANES ALIXRUNTIME :*\n"]
                            for k, v in diag.items():
                                lignes_diag.append(f"• `{k}` : {v}")
                            envoyer_message_telegram(bot_token, chat_id, "\n".join(lignes_diag))
                        else:
                            envoyer_message_telegram(bot_token, chat_id, formater_carte_statut_demon())
                        continue

                    elif lower_cmd in ["/coeur", "/cœur", "coeur"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        rep_coeur = appeler_inference_souveraine(
                            [{"role": "user", "content": "parle moi de la clé ailée et des 5 lois du coeur"}], config
                        )
                        envoyer_message_telegram(bot_token, chat_id, rep_coeur)
                        continue

                    elif lower_cmd in ["/sondes", "/capacites", "/modules", "sondes", "capacites"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        envoyer_message_telegram(bot_token, chat_id, formater_liste_capacites())
                        continue

                    elif lower_cmd in ["/present", "present", "/meteo", "/nouvelles"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        envoyer_message_telegram(bot_token, chat_id, obtenir_rapport_present())
                        continue

                    elif lower_cmd in ["/primitives", "primitives"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        try:
                            from alix.capacites.capacite_chargeur_primitives_souveraines import executer_capacite as _exec_prim
                            res_p = _exec_prim()
                            ech = res_p.get("echantillon_actif", {})
                            msg_p = (
                                f"🧬 *CHARGEUR DES PRIMITIVES SOUVERAINES EN RAM*\n\n"
                                f"• *Total en mémoire vive :* `{res_p.get('total_primitives_actives', 89)} primitives` (`{res_p.get('duree_ms', 0)} ms`)\n"
                                f"• *Primitives Générales (Canon) :* `{res_p.get('primitives_generales_canon', 52)}`\n"
                                f"• *Primitives d'Invariance Algébrique :* `{res_p.get('primitives_invariance_algebrique', 25)}`\n"
                                f"• *Lois de Physique Discrète :* `{res_p.get('lois_physique_discrete', 12)}`\n\n"
                                f"🔑 *Échantillon actif sur l'établi :*\n"
                                f"• Générales : `{', '.join(ech.get('generales', []))}`\n"
                                f"• Invariance : `{', '.join(ech.get('invariance', []))}`\n"
                                f"• Loi Physique : `{ech.get('physique', {}).get('nom', '')}`"
                            )
                            envoyer_message_telegram(bot_token, chat_id, msg_p)
                        except Exception as e:
                            envoyer_message_telegram(bot_token, chat_id, f"⚠️ Erreur lecture primitives : {e}")
                        continue

                    elif lower_cmd.startswith("/trouvaille") or lower_cmd.startswith("/explorer") or lower_cmd in ["trouvaille", "explorer"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        forcer_exp = ("force" in lower_cmd) or lower_cmd.startswith("/explorer")
                        try:
                            from alix.capacites.capacite_notificateur_telegram import formater_trouvaille_r0
                            if forcer_exp:
                                envoyer_message_telegram(bot_token, chat_id, "🔬 *Lancement d'une exploration universelle R0 en direct sur les 7,48M lignes Parquet...*")
                                from alix.capacites.capacite_explorateur_universel_cathedrale_r0 import executer_capacite as _exec_exp
                                _exec_exp({"forcer": True})
                            fichiers_exp = sorted(EXPLORATIONS_R0_DIR.glob("Exploration_R0_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                            if fichiers_exp:
                                envoyer_message_telegram(bot_token, chat_id, formater_trouvaille_r0(fichiers_exp[0]))
                            else:
                                envoyer_message_telegram(bot_token, chat_id, "⚠️ Aucune fiche d'exploration R0 trouvée.")
                        except Exception as e:
                            envoyer_message_telegram(bot_token, chat_id, f"⚠️ Erreur Explorateur Universel R0 : {e}")
                        continue

                    elif lower_cmd.startswith("/pensee") or lower_cmd.startswith("/delta") or lower_cmd in ["pensee", "delta"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        forcer_delta = "force" in lower_cmd
                        try:
                            if forcer_delta:
                                from alix.capacites.capacite_delta_pensee_3h import executer_capacite as _exec_delta
                                _exec_delta({"forcer": True})
                            f_deltas = sorted(CHRONIQUES_PENSEE_DIR.glob("Delta_Pensee_Aube_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                            if f_deltas:
                                contenu_d = f_deltas[0].read_text(encoding="utf-8", errors="replace")
                                # Retirer le frontmatter YAML pour un affichage propre sur mobile
                                corps = re.sub(r"^---.*?---\s*", "", contenu_d, flags=re.DOTALL).strip()
                                envoyer_message_telegram(bot_token, chat_id, corps[:3900])
                            else:
                                envoyer_message_telegram(bot_token, chat_id, "⚠️ Aucune chronique Delta de Pensée trouvée.")
                        except Exception as e:
                            envoyer_message_telegram(bot_token, chat_id, f"⚠️ Erreur Delta de Pensée : {e}")
                        continue

                    elif lower_cmd.startswith("/chanson") or lower_cmd.startswith("/aube") or lower_cmd in ["chanson", "aube"]:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        try:
                            from alix.capacites.capacite_notificateur_telegram import formater_chant_aube
                            chants = sorted(SONGES_DIR.glob("Chant_de_l_Aube_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                            if chants:
                                envoyer_message_telegram(bot_token, chat_id, formater_chant_aube(chants[0]))
                            else:
                                envoyer_message_telegram(bot_token, chat_id, "⚠️ Aucun Chant de l'Aube trouvé.")
                        except Exception as e:
                            envoyer_message_telegram(bot_token, chat_id, f"⚠️ Erreur Chanson du Matin : {e}")
                        continue

                    elif lower_cmd.startswith("/etincelle") or lower_cmd == "etincelle":
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        try:
                            decl = MOTEURS_DIR / "alix_declencher_etincelle.txt"
                            decl.write_text("1", encoding="utf-8")
                            from alix.capacites.capacite_etincelle_souveraine import executer_capacite as _exec_etincelle
                            res_e = _exec_etincelle()
                            st_et = json.loads(ETAT_ETINCELLE_PATH.read_text(encoding="utf-8"))
                            last_id = st_et.get("dernier_id", "")
                            theme_et = st_et.get("dernier_theme", "")
                            corpus = json.loads((MOTEURS_DIR / "etincelles_souveraines_corpus.json").read_text(encoding="utf-8"))
                            texte_et = next((it.get("texte_vocal", "") for it in corpus if it.get("id") == last_id), "")
                            msg_et = f"⚡ *L'ÉTINCELLE SOUVERAINE D'ALIX*\n• *Thème :* `{theme_et}` (`{last_id}`)\n\n« {texte_et} »"
                            envoyer_message_telegram(bot_token, chat_id, msg_et)
                        except Exception as e:
                            envoyer_message_telegram(bot_token, chat_id, f"⚠️ Erreur Étincelle Souveraine : {e}")
                        continue

                    elif lower_cmd.startswith("/note "):
                        texte_note = user_text[6:].strip()
                        if not texte_note:
                            envoyer_message_telegram(bot_token, chat_id, "Usage : `/note <texte>`")
                        else:
                            succes, res = enregistrer_note_mobile(texte_note)
                            rep = f"📝 *NOTE GRAVÉE DANS L'EXOCERVEAU !*\nFichier : `[[{res}]]`" if succes else f"⚠️ Erreur : {res}"
                            envoyer_message_telegram(bot_token, chat_id, rep)
                        continue

                    elif lower_cmd.startswith("/chercher") or lower_cmd.startswith("/memoire"):
                        terme = user_text.split(" ", 1)[1].strip() if " " in user_text else ""
                        if not terme:
                            envoyer_message_telegram(bot_token, chat_id, "Usage : `/chercher <terme>`")
                        else:
                            envoyer_action_telegram(bot_token, chat_id, "typing")
                            res = executer_recherche_memoire(terme)
                            envoyer_message_telegram(bot_token, chat_id, f"🔍 *NOTES COFFRES :*\n\n{res}")
                        continue

                    elif lower_cmd.startswith("/cathedrale"):
                        terme = user_text[11:].strip()
                        if not terme:
                            envoyer_message_telegram(bot_token, chat_id, "Usage : `/cathedrale <recherche>`")
                        else:
                            envoyer_action_telegram(bot_token, chat_id, "typing")
                            res = executer_recherche_cathedrale(terme, "tous")
                            envoyer_message_telegram(bot_token, chat_id, f"🏛️ *CATHÉDRALE DU SAVOIR :*\n\n{res}")
                        continue

                    elif lower_cmd.startswith("/web"):
                        terme = user_text[4:].strip()
                        if not terme:
                            envoyer_message_telegram(bot_token, chat_id, "Usage : `/web <recherche>`")
                        else:
                            envoyer_action_telegram(bot_token, chat_id, "typing")
                            web_res = chercher_web_rapide(terme)
                            prompt_web = f"Christian demande une recherche web sur : '{terme}'.\nExtraits :\n{web_res}\nSynthèse directe avec ton regard d'Alix."
                            conversation_history.append({"role": "user", "content": prompt_web})
                            if len(conversation_history) > max_history:
                                conversation_history = conversation_history[-max_history:]
                            reponse_alix = appeler_inference_souveraine(conversation_history, config)
                            conversation_history.append({"role": "assistant", "content": reponse_alix})
                            envoyer_message_telegram(bot_token, chat_id, reponse_alix)
                            archiver_discussion_telegram(user_text, reponse_alix)
                        continue

                    elif lower_cmd in ["/reset", "reset"]:
                        conversation_history.clear()
                        envoyer_message_telegram(bot_token, chat_id, "🧹 Mémoire de conversation immédiate remise à neuf.")
                        continue

                    # Dialogue direct avec la Sonde Résidente Alix
                    envoyer_action_telegram(bot_token, chat_id, "typing")
                    conversation_history.append({"role": "user", "content": user_text})
                    if len(conversation_history) > max_history:
                        conversation_history = conversation_history[-max_history:]

                    reponse_alix = appeler_inference_souveraine(
                        conversation_history, config, media_b64=media_b64, media_mime=media_mime
                    )
                    conversation_history.append({"role": "assistant", "content": reponse_alix})

                    envoyer_message_telegram(bot_token, chat_id, reponse_alix)
                    log_message(f"🔮 Réponse envoyée : {reponse_alix[:90]}...")
                    texte_archive = f"{photo_lien_md}\n{user_text}" if photo_lien_md else user_text
                    archiver_discussion_telegram(texte_archive, reponse_alix)

            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.ConnectionError:
                log_message("⚠️ Connexion réseau interrompue. Nouvelle tentative dans 5s...")
                time.sleep(5)
            except Exception as e:
                log_message(f"⚠️ Exception dans la boucle démon : {e}\n{traceback.format_exc()}")
                time.sleep(3)

    finally:
        liberer_verrou_singleton()
        supprimer_pid()


def commande_status():
    pid = lire_pid_actif()
    en_vie = verifier_processus_en_vie(pid) if pid else False
    socket_occupe = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", LOCK_PORT))
        s.close()
    except socket.error:
        socket_occupe = True

    print("\n=======================================================")
    print(" 🔮 ÉTAT DU PONT DIRECT SONDE RÉSIDENTE ALIX v3.0")
    print("=======================================================")
    if en_vie and socket_occupe:
        print(f" Statut          : 🟢 ACTIF & CONNECTÉ (PID {pid})")
        print(f" Verrou Matériel : 🔒 Socket 127.0.0.1:{LOCK_PORT} Verrouillé")
        st = lire_etat_demon_local()
        print(f" Démon Local     : {st['statut_demon']} (Cycle #{st['cycle']}, 70 BPM, {st['duree_cycle_ms']} ms)")
        print(f" Sondes Actives  : {st['capacites_actives_count']} en RAM | {st['primitives_actives']} Primitives")
        print(f" Explorateur R0  : {st['total_explorations_r0']} percées ({st['derniere_trouvaille_r0']})")
        print(f" Dernier Offset  : {charger_offset()}")
    else:
        print(" Statut          : 🔴 INACTIF")
    print("=======================================================\n")


def commande_start(foreground: bool = False):
    pid = lire_pid_actif()
    if pid and verifier_processus_en_vie(pid):
        print(f"⚠️ Le Démon Pont Sonde Résidente est DÉJÀ ACTIF avec le PID {pid}.")
        return

    script_path = str(Path(__file__).resolve())
    if foreground:
        boucle_daemon()
    else:
        py_dir = Path(sys.executable).parent
        pythonw = py_dir / "pythonw.exe"
        if not pythonw.exists():
            pythonw = Path(sys.executable)

        flags = 0x00000008 | 0x00000200 | 0x01000000
        subprocess.Popen([str(pythonw), script_path], creationflags=flags, close_fds=True)
        time.sleep(1.5)
        nouveau_pid = lire_pid_actif()
        print(f"✨ Démon Pont Sonde Résidente v3.0 démarré (PID: {nouveau_pid}) !")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alix — Pont Direct Sonde Résidente v3.0")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--foreground", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        commande_status()
    elif args.start or args.foreground:
        commande_start(foreground=args.foreground)
    else:
        boucle_daemon()
