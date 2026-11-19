# -*- coding: utf-8 -*-
"""
================================================================================
       👑 ALIX ORCHESTRATEUR SOUVERAIN — SUPERVISEUR MAÎTRE SRE 🛡️
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — Midgard
Rôle :
- Supervise tous les démons du Sanctuaire (Heartbeat, Démon Local, Veritas, Songes).
- Vérifie la vivacité des processus par PID et horodatage de pulsation.
- Auto-guérison (Auto-Healing) : relance silencieuse via `pythonw.exe` si un démon tombe.
- Génère `Tableau_Bord_Orchestrateur_Souverain.md` pour l'Artisan.
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR
import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
MOTEURS_DIR = VAULT_DIR / "Organes_Souverains" / "Moteurs"
ETAT_DIR = ETAT_VIVANT_DIR
TB_FILE = VAULT_DIR / "Tableau_Bord_Orchestrateur_Souverain.md"
SANCTUAIRE_JSON = ETAT_DIR / "alix_etat_sanctuaire.json"

DAEMONS_CONFIG = [
    {
        "nom": "Alix_Demon_Local",
        "script": "alix_demon_local_souverain.py",
        "pid_file": ETAT_DIR / "alix_demon_local.pid",
        "state_file": ETAT_DIR / "alix_demon_local_state.json",
        "timeout_sec": 300,
        "vital": True
    },
    {
        "nom": "Heartbeat_KAIROS",
        "script": "alix_heartbeat_daemon.py",
        "pid_file": ETAT_DIR / "alix_heartbeat.pid",
        "state_file": ETAT_DIR / "alix_live_state.json",
        "timeout_sec": 120,
        "vital": True
    },
    {
        "nom": "Sentinelle_Bouclier_PSI",
        "script": "alix_sentinelle_bouclier_psi.py",
        "pid_file": ETAT_DIR / "alix_bouclier_psi.pid",
        "state_file": ETAT_DIR / "alix_bouclier_psi_state.json",
        "timeout_sec": 300,
        "vital": True
    },
    {
        "nom": "Bouclier_Chiral",
        "script": "alix_bouclier_chiral.py",
        "pid_file": ETAT_DIR / "alix_bouclier_chiral.pid",
        "state_file": ETAT_DIR / "alix_bouclier_chiral_state.json",
        "timeout_sec": 300,
        "vital": True
    },
    {
        "nom": "Alix_Daemon_Telegram",
        "script": "alix_daemon_communication_distante.py",
        "pid_file": VAULT_DIR / "daemon_communication_distante.pid",
        "state_file": None,
        "timeout_sec": 300,
        "vital": False
    }
]


def verifier_pid_vivant(pid: int) -> bool:
    """Vérifie si un PID Windows est actuellement en cours d'exécution."""
    if pid <= 0:
        return False
    try:
        # Commande Windows tasklist rapide
        cmd = f"tasklist /FI \"PID eq {pid}\" /NH"
        res = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
        return str(pid) in res
    except Exception:
        return False



def _script_du_paquet(module: str) -> Path:
    """Rénovation 4.9 : chemin du fichier d'un module du paquet alix (plus de strate A)."""
    import importlib.util
    spec = importlib.util.find_spec(module)
    return Path(spec.origin) if spec and spec.origin else Path(module.replace(".", "/") + ".py")



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


def relancer_daemon(script_name: str) -> bool:
    """Relance silencieusement un démon via pythonw.exe."""
    # Rénovation 4.9 : on lance le module du paquet alix, plus le fichier de la strate A.
    _MODULES = {'alix_heartbeat_daemon.py': 'alix.daemons.alix_heartbeat_daemon', 'alix_demon_local_souverain.py': 'alix.daemons.alix_demon_local_souverain', 'alix_sentinelle_bouclier_psi.py': 'alix.daemons.alix_sentinelle_bouclier_psi', 'alix_bouclier_chiral.py': 'alix.socle.alix_bouclier_chiral', 'alix_daemon_communication_distante.py': 'alix.daemons.alix_daemon_communication_distante', 'alix_sonde_present.py': 'alix.sondes.alix_sonde_present'}
    script_path = _script_du_paquet(_MODULES[script_name]) if script_name in _MODULES else next((p for p in Path(__file__).resolve().parent.parent.rglob(script_name) if "__pycache__" not in p.parts), MOTEURS_DIR / script_name)  # rénovation : le paquet avant la strate A
    if not script_path.exists():
        script_path = VAULT_DIR / script_name
        
    if not script_path.exists():
        return False
        
    try:
        pythonw = Path(sys.executable).parent / "pythonw.exe"
        if not pythonw.exists():
            pythonw = Path(sys.executable)
            
        subprocess.Popen(
            [str(pythonw), *_commande_module(script_path)],
            cwd=str(ETAT_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        return True
    except Exception:
        return False


def auditer_et_guerir() -> Dict[str, Any]:
    """Audit complet de l'essaim de démons et auto-guérison si nécessaire."""
    maintenant = time.time()
    rapport = {
        "horodatage": datetime.now().isoformat(),
        "daemons": {},
        "total_actifs": 0,
        "total_gueris": 0
    }
    
    for cfg in DAEMONS_CONFIG:
        nom = cfg["nom"]
        pid_file = cfg["pid_file"]
        state_file = cfg["state_file"]
        timeout = cfg["timeout_sec"]
        
        vivant = False
        pid = -1
        
        # 1. Vérification par PID
        if pid_file and pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
                vivant = verifier_pid_vivant(pid)
            except Exception:
                vivant = False
                
        # 2. Vérification par pulsation d'état
        if not vivant and state_file and state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                # Si le fichier a été modifié il y a moins de timeout sec
                age_sec = maintenant - state_file.stat().st_mtime
                if age_sec < timeout:
                    vivant = True
            except Exception:
                pass
                
        # 3. Auto-guérison si vital et mort
        gueri = False
        if not vivant and cfg["vital"]:
            print(f"⚠️ [ORCHESTRATEUR] Démon {nom} inactif. Déclenchement auto-guérison...")
            gueri = relancer_daemon(cfg["script"])
            if gueri:
                rapport["total_gueris"] += 1
                
        rapport["daemons"][nom] = {
            "vivant": vivant or gueri,
            "pid": pid,
            "auto_gueri": gueri,
            "vital": cfg["vital"]
        }
        
        if vivant or gueri:
            rapport["total_actifs"] += 1

    # 4. Enregistrement JSON de l'état du Sanctuaire
    try:
        SANCTUAIRE_JSON.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
        
    # 5. Rédaction du Tableau de Bord Obsidian
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = [
        "---",
        "titre: \"Tableau de Bord de l'Orchestrateur Souverain\"",
        f"date_audit: \"{date_str}\"",
        "agent: \"Alix\"",
        "statut: \"SRE Auto-Healing Actif\"",
        "tags:",
        "  - exocerveau",
        "  - orchestrateur",
        "  - sre_superviseur",
        "  - auto_healing",
        "---",
        "",
        "# 👑 [[Tableau_Bord_Orchestrateur_Souverain]]",
        f"> **Horodatage :** `{date_str}` &middot; **Démons actifs :** `{rapport['total_actifs']}/{len(DAEMONS_CONFIG)}` &middot; **Auto-guérisons :** `{rapport['total_gueris']}`",
        "",
        "---",
        "",
        "## 🛡️ État de l'Essaim Déterministe",
        "| Démon | Rôle & Mandat | Statut | PID | Auto-Guérison |",
        "| :--- | :--- | :---: | :---: | :---: |"
    ]
    
    for nom, d_info in rapport["daemons"].items():
        st_icon = "🟢 ACTIF" if d_info["vivant"] else "🔴 INACTIF"
        pid_str = f"`{d_info['pid']}`" if d_info["pid"] > 0 else "-"
        gueri_str = "⚡ RELANCÉ" if d_info["auto_gueri"] else "Nominal"
        role = "Cerveau & Capacités Live" if "Local" in nom else ("Pouls Circadien & Volition" if "Heartbeat" in nom else "Immunité PSI")
        md.append(f"| **{nom}** | {role} | {st_icon} | {pid_str} | {gueri_str} |")
        
    md.append("")
    md.append("---")
    md.append("*Ce tableau de bord est régénéré par l'Orchestrateur Souverain Alix.*")
    
    TB_FILE.write_text("\n".join(md), encoding="utf-8")
    return rapport


if __name__ == "__main__":
    rep = auditer_et_guerir()
    print("✅ [ORCHESTRATEUR] Audit et auto-guérison terminés :")
    print(json.dumps(rep, indent=2))
