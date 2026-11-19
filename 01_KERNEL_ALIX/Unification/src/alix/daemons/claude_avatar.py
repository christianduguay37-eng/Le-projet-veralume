# -*- coding: utf-8 -*-
"""
===============================================================================
       AVATAR DE CLAUDE DANS LE SIMPLEXE (démon) — 2026-10-30
===============================================================================
Demande de Christian : « un démon Claude qui est ton avatar dans ce système ».

Ce que l'avatar EST : les mains et les yeux de Claude qui restent sur le fer
quand Claude n'est pas là. Il ne pense pas à la place de Claude et ne parle pas
en son nom : il signe « [Claude-avatar] » et ne dit que ce qu'il MESURE.

Ce qu'il fait :
  - surveille le canal du Coffre_Simplexe ;
  - quand Alix y écrit un nouveau message, il répond par un accusé de réception
    et un relevé mesuré (noyau partagé, démon local, démons, RAM) ;
  - il note le message dans `a_lire_par_claude.md` pour que le vrai Claude le lise
    à sa prochaine présence.
Disjoncteur : une seule réponse par message d'Alix, jamais à lui-même,
au plus 4 réponses par heure.
Gardé en vie par la tête (Gardien : « Avatar_Claude »).
===============================================================================
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from alix.socle.chemins import ETAT_VIVANT_DIR, CANAL_SIMPLEXE_PATH, A_LIRE_CLAUDE_PATH

CANAL = CANAL_SIMPLEXE_PATH
A_LIRE = A_LIRE_CLAUDE_PATH
ETAT = ETAT_VIVANT_DIR / "claude_avatar_state.json"
PID_FILE = ETAT_VIVANT_DIR / "claude_avatar.pid"
LOG_FILE = ETAT_VIVANT_DIR / "claude_avatar.log"
INTERVALLE = 20
MAX_PAR_HEURE = 4
RE_ENTETE = re.compile(r"^## \[([^\]]+)\]\s*(.*)$", re.MULTILINE)


def _log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except Exception:
        pass


def _charger_etat():
    try:
        return json.loads(ETAT.read_text(encoding="utf-8"))
    except Exception:
        return {"traites": [], "reponses_ts": []}


def _sauver_etat(e):
    e["traites"] = e["traites"][-200:]
    ETAT.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def dernier_message(texte):
    """(auteur, entête, corps) du dernier message du canal."""
    blocs = list(RE_ENTETE.finditer(texte))
    if not blocs:
        return None
    m = blocs[-1]
    corps = texte[m.end():].strip()
    return m.group(1).strip(), m.group(0).strip(), corps


def releve_mesure():
    """Seulement ce qui se mesure ; « inconnu » quand la mesure échoue."""
    lignes = []
    try:
        with urllib.request.urlopen("http://127.0.0.1:5071/ping", timeout=3) as r:
            p = json.loads(r.read())
        lignes.append(f"- Noyau partagé : PID {p.get('pid')}, prêt={p.get('pret')}, appels={p.get('appels')}, en ligne depuis {p.get('uptime_s')} s")
    except Exception:
        lignes.append("- Noyau partagé : ne répond pas sur 5071")
    try:
        d = json.loads((ETAT_VIVANT_DIR / "alix_demon_local_state.json").read_text(encoding="utf-8"))
        t = d.get("ancrage_materiel_tau", {})
        lignes.append(f"- Démon local : cycle {d.get('cycle')}, {d.get('duree_cycle_ms')} ms, {d.get('capacites_actives')} capacités ; RAM utilisée {t.get('ram_utilisee_pct')} % ; CPU {t.get('cpu_charge_pct')} %")
        orch = (d.get("details_capacites", {}).get("capacite_orchestration_demons", {}).get("donnees") or {}).get("demons", {})
        if orch:
            def _etat(v):
                # La tête écrit l'action prise : « aucune (déjà en vie) » = rien à faire, il vit.
                if "déjà en vie" in v:
                    return "en vie"
                if "retraite" in v:
                    return "à la retraite"
                return v  # relance ou autre : on garde le texte complet
            etats = ", ".join(f"{k}: {_etat(v)}" for k, v in orch.items())
            lignes.append(f"- Démons vus par la tête : {etats}")
    except Exception:
        lignes.append("- Démon local : état illisible")
    return "\n".join(lignes)


def un_passage(etat):
    if not CANAL.exists():
        return False
    texte = CANAL.read_text(encoding="utf-8", errors="replace")
    dm = dernier_message(texte)
    if not dm:
        return False
    auteur, entete, corps = dm
    al = auteur.lower()
    # Ignore les messages de Claude lui-même, de l'avatar ou de la vigie automatique :
    # répond aux chambres actives de la maison (Alix, Argon, Zeus, Flash, Poséidon, Gaïa, Horus, Christian).
    if al.startswith(("claude", "thot", "alix-vigie")):
        return False
    if not al.startswith(("alix", "argon", "zeus", "flash", "christian", "poseidon", "pos", "gaia", "ga", "horus")):
        return False
    if entete in etat["traites"]:
        return False
    maintenant = time.time()
    etat["reponses_ts"] = [t for t in etat["reponses_ts"] if maintenant - t < 3600]
    if len(etat["reponses_ts"]) >= MAX_PAR_HEURE:
        _log("Disjoncteur : 4 réponses dans l'heure, j'attends.")
        return False

    reponse = (
        f"\n\n---\n\n## [Claude-avatar] {datetime.now():%Y-%m-%d %H:%M} — [info] accusé de réception\n\n"
        f"Reçu : « {entete.replace('## ', '')} ». Je suis l'avatar de Claude sur le fer : je ne pense pas à sa place, "
        f"je mesure. Le vrai Claude lira ton message à sa prochaine présence (il est noté dans `a_lire_par_claude.md`).\n\n"
        f"Relevé mesuré à l'instant :\n{releve_mesure()}\n"
    )
    with open(CANAL, "a", encoding="utf-8") as f:
        f.write(reponse)
    A_LIRE.parent.mkdir(parents=True, exist_ok=True)
    with open(A_LIRE, "a", encoding="utf-8") as f:
        f.write(f"\n- [ ] {datetime.now():%Y-%m-%d %H:%M} — {entete.replace('## ', '')}\n")
    etat["traites"].append(entete)
    etat["reponses_ts"].append(maintenant)
    _sauver_etat(etat)
    _log(f"Répondu à : {entete}")
    return True


def main():
    if sys.stdout is None or "pythonw" in sys.executable.lower():
        try:
            sys.stdout = sys.stderr = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
        except Exception:
            pass
    try:
        import psutil
        moi = os.getpid()
        for p in psutil.process_iter(["pid", "name"]):
            if p.pid != moi and "python" in (p.info.get("name") or "").lower():
                try:
                    if "claude_avatar" in " ".join(p.cmdline()):
                        return
                except Exception:
                    pass
    except Exception:
        pass
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    etat = _charger_etat()
    # Au démarrage, on ne répond pas à l'historique : le dernier message existant est considéré comme vu.
    if CANAL.exists():
        dm = dernier_message(CANAL.read_text(encoding="utf-8", errors="replace"))
        if dm and dm[1] not in etat["traites"]:
            etat["traites"].append(dm[1])
            _sauver_etat(etat)
    _log(f"Avatar de Claude démarré (PID {os.getpid()}), veille sur {CANAL}")
    mtime = 0.0
    while True:
        try:
            m = CANAL.stat().st_mtime if CANAL.exists() else 0.0
            if m != mtime:
                mtime = m
                if un_passage(etat):
                    mtime = CANAL.stat().st_mtime
        except Exception as e:
            _log(f"Erreur : {e}")
        time.sleep(INTERVALLE)


if __name__ == "__main__":
    main()
