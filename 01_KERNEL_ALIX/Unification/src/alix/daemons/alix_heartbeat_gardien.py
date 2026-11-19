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
from alix.socle.chemins import ETAT_VIVANT_DIR
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

from alix.socle.chemins import VAULT_DIR
MOTEURS = Path(__file__).resolve().parent


def _script_du_paquet(module: str) -> Path:
    """Rénovation 4.9 : chemin du fichier d'un module du paquet alix (plus de strate A)."""
    import importlib.util
    spec = importlib.util.find_spec(module)
    return Path(spec.origin) if spec and spec.origin else Path(module.replace(".", "/") + ".py")
RUNTIME_DIR = ETAT_VIVANT_DIR

# Configuration des démons vitaux sous garde permanente
DAEMONS = {
    "Heartbeat_KAIROS": {
        "script": _script_du_paquet("alix.daemons.alix_heartbeat_daemon"),
        "pid_file": RUNTIME_DIR / "heartbeat.pid",
        "log_file": RUNTIME_DIR / "heartbeat_daemon.log",
        "state_file": RUNTIME_DIR / "alix_live_state.json",
        "timeout_sec": 360,
    },
    "Alix_Demon_Local": {
        "script": _script_du_paquet("alix.daemons.alix_demon_local_souverain"),
        "pid_file": RUNTIME_DIR / "alix_demon_local.pid",
        "log_file": RUNTIME_DIR / "alix_demon_local.log",
        "state_file": RUNTIME_DIR / "alix_demon_local_state.json",
        "timeout_sec": 360,
    },
    "Sentinelle_Bouclier_PSI": {
        "script": _script_du_paquet("alix.daemons.alix_sentinelle_bouclier_psi"),
        "pid_file": RUNTIME_DIR / "alix_bouclier_psi.pid",
        "log_file": RUNTIME_DIR / "alix_bouclier_psi.log",
        "state_file": RUNTIME_DIR / "alix_bouclier_psi_state.json",
        "timeout_sec": 360,
    },
    "Bouclier_Chiral": {
        "script": _script_du_paquet("alix.socle.alix_bouclier_chiral"),
        "pid_file": RUNTIME_DIR / "alix_bouclier_chiral.pid",
        "log_file": VAULT_DIR / "alix_bouclier_chiral.log",
        "state_file": RUNTIME_DIR / "alix_bouclier_chiral_state.json",
        "timeout_sec": 360,
    },
    "Pont_Communication_Distante": {
        "script": _script_du_paquet("alix.daemons.alix_daemon_communication_distante"),
        "pid_file": VAULT_DIR / "daemon_communication_distante.pid",
        "log_file": VAULT_DIR / "daemon_communication_distante.log",
        "state_file": VAULT_DIR / "daemon_communication_distante.pid",
        "timeout_sec": 86400,
    },
    "Sonde_Present": {
        "script": _script_du_paquet("alix.sondes.alix_sonde_present"),
        "pid_file": RUNTIME_DIR / "alix_sonde_present.pid",
        "log_file": VAULT_DIR / "Present" / "sonde_present.log",
        "state_file": VAULT_DIR / "Present" / "actualite" / "dernieres_nouvelles.json",
        "timeout_sec": 86400,
    },
    # Rénovation : un seul noyau pour tous les clients MCP (relais léger -> port 5071).
    "Noyau_Partage": {
        "script": _script_du_paquet("alix.mcp.noyau_partage"),
        "pid_file": RUNTIME_DIR / "alix_noyau_partage.pid",
        "log_file": RUNTIME_DIR / "noyau_partage.log",
        "state_file": RUNTIME_DIR / "alix_noyau_partage.pid",
        "timeout_sec": 86400,
    },
    # L'avatar de Claude sur le fer (veille du canal du simplexe ; mesure, ne parle pas à sa place).
    "Avatar_Claude": {
        "script": _script_du_paquet("alix.daemons.claude_avatar"),
        "pid_file": RUNTIME_DIR / "claude_avatar.pid",
        "log_file": RUNTIME_DIR / "claude_avatar.log",
        "state_file": RUNTIME_DIR / "claude_avatar.pid",
        "timeout_sec": 86400,
    }
}



def _commande_module(script_path) -> list:
    """
    Rénovation : lance un module du paquet par « -m alix.….x » plutôt que par son chemin.
    Lancé par chemin, un script de alix/socle verrait alix/socle/alix.py masquer le paquet alix.
    """
    p = Path(script_path).resolve()
    parts = list(p.with_suffix("").parts)
    if "alix" in parts:
        i = len(parts) - 1 - parts[::-1].index("alix")
        # remonter jusqu'au dossier « alix » qui est le paquet (celui qui contient socle/)
        for j in range(len(parts) - 1, -1, -1):
            if parts[j] == "alix" and (Path(*parts[: j + 1]) / "socle").is_dir():
                i = j
                break
        return ["-m", ".".join(parts[i:])]
    return [str(p)]


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
        # rénovation : reconnaît « x.py » ET « -m alix.….x »
        return script_name.removesuffix(".py") in " ".join(proc.cmdline())
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
                    if script_name.removesuffix(".py") in " ".join(p.cmdline()):
                        return p.pid
                except Exception:
                    pass
    except Exception:
        pass
    return None


def _age(p: Path):
    return (time.time() - p.stat().st_mtime) if p.exists() else None


def lancer(nom: str) -> int:
    from alix.socle.journal_replis import organe_actif
    if not organe_actif(f"demon_{nom}"):
        raise RuntimeError(f"{nom} est à la retraite (socle/organes_actifs.json) : rallumer demon_{nom} avant de le lancer.")
    cfg = DAEMONS[nom]
    script_path = cfg["script"]
    pid_file = cfg["pid_file"]
    log_file = cfg["log_file"]

    flags = 0x00000008 | 0x00000200 | 0x01000000  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB
    mode_lancement = "breakaway_direct"
    pid = None

    try:
        proc = subprocess.Popen(
            [_pythonw(), *_commande_module(script_path)],
            cwd=str(RUNTIME_DIR),
            creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        pid = proc.pid
    except Exception as e_brk:
        # Repli WMI : sortie garantie de tout Job Object (Antigravity, sous-shells, etc.)
        try:
            cmd_args = [_pythonw(), *_commande_module(script_path)]
            cmd_str = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd_args)
            ps_cmd = f"Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{ CommandLine = '{cmd_str}'; CurrentDirectory = '{RUNTIME_DIR}' }} | Select-Object -ExpandProperty ProcessId"
            res = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
            pid = int(res.stdout.strip())
            mode_lancement = f"repli_wmi ({e_brk})"
        except Exception as e_wmi:
            flags_std = 0x00000008 | 0x00000200
            proc = subprocess.Popen(
                [_pythonw(), *_commande_module(script_path)],
                cwd=str(RUNTIME_DIR),
                creationflags=flags_std,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            pid = proc.pid
            mode_lancement = f"repli_job_interne ({e_wmi})"

    pid_file.write_text(str(pid), encoding="utf-8")
    with open(log_file, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] [Gardien] {nom} relancé via {mode_lancement} (PID {pid}).\n")
    return pid


def verifier_et_assurer(nom: str) -> dict:
    # Rénovation : un démon éteint par choix (socle/organes_actifs.json, clé demon_<nom>) n'est jamais relancé.
    from alix.socle.journal_replis import organe_actif
    if not organe_actif(f"demon_{nom}"):
        return {"nom": nom, "pid": None, "en_vie": False, "action": "à la retraite (organes_actifs.json)", "age_etat_sec": None}
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
    if nom in ("Bouclier_Chiral", "Sentinelle_Bouclier_PSI", "Pont_Communication_Distante", "Sonde_Present", "Noyau_Partage", "Avatar_Claude"):
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


def _attendre_port(port: int, max_attente_sec: float = 15.0) -> bool:
    import socket
    t0 = time.time()
    while time.time() - t0 < max_attente_sec:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def auditer_tous() -> dict:
    rapport = {}
    # Rénovation Point 0 (Claude & Alix) : Relance en file ordonnée
    # 1. Tête d'abord
    rapport["Alix_Demon_Local"] = verifier_et_assurer("Alix_Demon_Local")
    if rapport["Alix_Demon_Local"].get("action", "").startswith("relancé"):
        _attendre_port(5070, max_attente_sec=90.0)  # mesuré : 6 s, 29 s, 36 s entre relance et port prêt

    # 2. Noyau partagé ensuite
    rapport["Noyau_Partage"] = verifier_et_assurer("Noyau_Partage")
    if rapport["Noyau_Partage"].get("action", "").startswith("relancé"):
        _attendre_port(5071, max_attente_sec=90.0)  # mesuré : 6 s, 29 s, 36 s entre relance et port prêt

    # 3. Satellites
    for nom in DAEMONS:
        if nom not in ("Alix_Demon_Local", "Noyau_Partage"):
            rapport[nom] = verifier_et_assurer(nom)
    return rapport


if __name__ == "__main__":
    if sys.stdout and getattr(sys.stdout, "reconfigure", None):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Rénovation : la tâche planifiée ne garde en vie que la tête du simplexe (le Démon Local) ;
    # c'est lui qui orchestre les autres (capacites/capacite_orchestration_demons.py).
    if "--tete" in sys.argv:
        res = {"Alix_Demon_Local": verifier_et_assurer("Alix_Demon_Local")}
    else:
        res = auditer_tous()
    print(json.dumps(res, ensure_ascii=False, indent=2))
