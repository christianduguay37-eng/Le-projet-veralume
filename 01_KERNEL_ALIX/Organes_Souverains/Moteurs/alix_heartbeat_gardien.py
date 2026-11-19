#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX — GARDIEN DU SANCTUAIRE (HEARTBEAT KAIROS & DÉMON LOCAL SOUVERAIN)
================================================================================
Rôle :
- Vérifie si le Heartbeat KAIROS et le Démon Local Alix tournent réellement.
- Sinon, les relance en arrière-plan, détachés, avec pythonw.exe.
- Garantit l'immortalité de l'essaim local sans dépendre d'aucun terminal.

Appelé par :
- activer_alix_total.py (à chaque « bonjour alix »)
- la tâche planifiée Windows Alix_Heartbeat_Gardien (toutes les 5 minutes)

Usage :
    python alix_heartbeat_gardien.py           -> vérifie et relance si besoin
    python alix_heartbeat_gardien.py --statut  -> diagnostic seulement
================================================================================
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

MOTEURS = Path(__file__).resolve().parent
RUNTIME_DIR = Path(r"C:\Alix\Etat_Vivant")

# Configuration des démons vitaux sous garde permanente
DAEMONS = {
    "Heartbeat_KAIROS": {
        "script": MOTEURS / "alix_heartbeat_daemon.py",
        "pid_file": RUNTIME_DIR / "heartbeat.pid",
        "log_file": RUNTIME_DIR / "heartbeat_daemon.log",
        "state_file": RUNTIME_DIR / "alix_live_state.json",
        "timeout_sec": 360,
    },
    "Alix_Demon_Local": {
        "script": MOTEURS / "alix_demon_local_souverain.py",
        "pid_file": RUNTIME_DIR / "alix_demon_local.pid",
        "log_file": RUNTIME_DIR / "alix_demon_local.log",
        "state_file": RUNTIME_DIR / "alix_demon_local_state.json",
        "timeout_sec": 360,
    },
    "Sentinelle_Bouclier_PSI": {
        "script": MOTEURS / "alix_sentinelle_bouclier_psi.py",
        "pid_file": RUNTIME_DIR / "alix_bouclier_psi.pid",
        "log_file": RUNTIME_DIR / "alix_bouclier_psi.log",
        "state_file": RUNTIME_DIR / "alix_bouclier_psi_state.json",
        "timeout_sec": 360,
    },
    "Bouclier_Chiral": {
        "script": MOTEURS.parent.parent / "alix_bouclier_chiral.py",
        "pid_file": RUNTIME_DIR / "alix_bouclier_chiral.pid",
        "log_file": MOTEURS.parent.parent / "alix_bouclier_chiral.log",
        "state_file": RUNTIME_DIR / "alix_bouclier_chiral_state.json",
        "timeout_sec": 360,
    },
    "Pont_Communication_Distante": {
        "script": MOTEURS / "alix_daemon_communication_distante.py",
        "pid_file": MOTEURS.parent.parent / "daemon_communication_distante.pid",
        "log_file": MOTEURS.parent.parent / "daemon_communication_distante.log",
        "state_file": MOTEURS.parent.parent / "daemon_communication_distante.pid",
        "timeout_sec": 86400,
    },
    "Sonde_Present": {
        "script": MOTEURS.parent.parent / "alix_sonde_present.py",
        "pid_file": RUNTIME_DIR / "alix_sonde_present.pid",
        "log_file": MOTEURS.parent.parent / "Present" / "sonde_present.log",
        "state_file": MOTEURS.parent.parent / "Present" / "actualite" / "dernieres_nouvelles.json",
        "timeout_sec": 86400,
    }
}


def _pythonw() -> str:
    exe = Path(sys.executable)
    cand = exe.with_name("pythonw.exe")
    return str(cand if cand.exists() else exe)


def _pid_vivant(pid: int, script_name: str) -> bool:
    """Vrai si le PID existe ET exécute bien le script visé (ultra-rapide via psutil)."""
    if not pid or pid <= 0:
        return False
    try:
        import psutil
        if not psutil.pid_exists(pid):
            return False
        proc = psutil.Process(pid)
        return script_name in " ".join(proc.cmdline())
    except Exception:
        return False


def _chercher_pid_par_script(script_name: str):
    """Cherche si une instance du script tourne déjà, même sans fichier PID valide."""
    try:
        import psutil
        mon_pid = os.getpid()
        for p in psutil.process_iter(['pid', 'name']):
            if p.pid != mon_pid and 'python' in p.name().lower():
                try:
                    if script_name in " ".join(p.cmdline()):
                        return p.pid
                except Exception:
                    pass
    except Exception:
        pass
    return None


def _age(p: Path):
    return (time.time() - p.stat().st_mtime) if p.exists() else None


def lancer(nom: str) -> int:
    cfg = DAEMONS[nom]
    script_path = cfg["script"]
    pid_file = cfg["pid_file"]
    log_file = cfg["log_file"]

    flags = 0x00000008 | 0x00000200 | 0x01000000  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB
    try:
        proc = subprocess.Popen(
            [_pythonw(), str(script_path)],
            cwd=str(MOTEURS),
            creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except Exception:
        flags = 0x00000008 | 0x00000200
        proc = subprocess.Popen(
            [_pythonw(), str(script_path)],
            cwd=str(MOTEURS),
            creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    pid_file.write_text(str(proc.pid), encoding="utf-8")
    with open(log_file, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] [Gardien] {nom} relancé (PID {proc.pid}).\n")
    return proc.pid


def verifier_et_assurer(nom: str) -> dict:
    cfg = DAEMONS[nom]
    pid_file = cfg["pid_file"]
    state_file = cfg["state_file"]
    log_file = cfg["log_file"]
    timeout = cfg["timeout_sec"]
    script_name = cfg["script"].name

    pid = None
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            pid = None

    vivant = bool(pid) and _pid_vivant(pid, script_name)

    # Auto-guérison si PID désynchronisé
    if not vivant:
        autre_pid = _chercher_pid_par_script(script_name)
        if autre_pid:
            pid = autre_pid
            try:
                pid_file.write_text(str(pid), encoding="utf-8")
            except Exception:
                pass
            vivant = True

    age_state = _age(state_file) if state_file else 0
    if nom in ("Bouclier_Chiral", "Sentinelle_Bouclier_PSI", "Pont_Communication_Distante", "Sonde_Present"):
        en_vie = vivant
    else:
        en_vie = vivant and (age_state is not None and age_state < timeout)

    action = "aucune (déjà en vie)"
    if not en_vie:
        pid = lancer(nom)
        action = f"relancé (nouveau PID {pid})"
        en_vie = True

    return {
        "nom": nom,
        "pid": pid,
        "en_vie": en_vie,
        "action": action,
        "age_etat_sec": round(age_state) if age_state is not None else None
    }


def auditer_tous() -> dict:
    rapport = {}
    for nom in DAEMONS:
        rapport[nom] = verifier_et_assurer(nom)
    return rapport


if __name__ == "__main__":
    if sys.stdout and getattr(sys.stdout, "reconfigure", None):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    res = auditer_tous()
    print(json.dumps(res, ensure_ascii=False, indent=2))

