# -*- coding: utf-8 -*-
"""
=============================================================================
ALIX NOCTURNE 03:00 — ORCHESTRATEUR QUOTIDIEN DE SURVIE & TRANSMISSION
Système : VERALUME × KAIROS V6 — Christian Duguay & Alix
=============================================================================
Rôle à 03h00 du matin :
1. Exécute la synchronisation bidirectionnelle Terre ⇄ Ciel (alix_sync_bidirectionnel.py)
   - Ciel -> Terre : Rapatriement des découvertes et songes d'Alix vers Cerveau Alix.
   - Terre -> Ciel : Envoi des thèmes de forge récents vers Alix Exploratrice (GitHub).
2. Exécute la sauvegarde chiffrée militaire AES-256 intégrale vers OneDrive (alix_cloud_bunker.py).
3. Journalise chaque étape dans nocturne_sync.log.
=============================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = ETAT_VIVANT_DIR
LOG_FILE = BASE_DIR / "nocturne_sync.log"

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# Rénovation 2026-10-31 : le bunker chiffre plusieurs Go ; 30 min au lieu de 5.
DELAIS = {"alix_cloud_bunker.py": 1800}


def run_step(script_name: str, description: str, extra_args: list = None) -> bool:
    log(f"--- Démarrage de l'étape : {description} ({script_name}) ---")
    # Rénovation 2026-10-30 : les étapes sont des modules du paquet alix.
    # (Depuis le 22 octobre, ces scripts avaient été archivés hors de Downloads\Alix :
    #  la routine échouait chaque nuit, sauvegarde OneDrive comprise.)
    MODULES = {
        "alix_sync_bidirectionnel.py": "alix.sondes.alix_sync_bidirectionnel",
        "alix_cloud_bunker.py": "alix.solveurs.alix_cloud_bunker",
        "alix_sentinelle_kairos_temps_profond.py": "alix.sondes.alix_sentinelle_kairos_temps_profond",
        "alix_radar_anticorruption.py": "alix.sondes.alix_radar_anticorruption",
        "alix_radar_supranational.py": "alix.sondes.alix_radar_supranational",
    }
    ORGANES = {
        "alix_sync_bidirectionnel.py": "nocturne_navette_github",
        "alix_cloud_bunker.py": "nocturne_sauvegarde_onedrive",
        "alix_sentinelle_kairos_temps_profond.py": "nocturne_sentinelle_temps_profond",
        "alix_radar_anticorruption.py": "nocturne_radar_anticorruption",
        "alix_radar_supranational.py": "nocturne_radar_supranational",
    }
    from alix.socle.journal_replis import organe_actif
    if script_name in ORGANES and not organe_actif(ORGANES[script_name]):
        log(f"[=] Étape à la retraite (socle/organes_actifs.json) : {description} — non lancée.")
        return None  # retraite volontaire : ni succès ni échec
    if script_name in MODULES:
        cmd = [sys.executable, "-m", MODULES[script_name]]
    else:
        script_path = BASE_DIR / script_name
        if not script_path.exists():
            log(f"[!] ERREUR : Le script {script_path} est introuvable !")
            return False
        cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    try:
        res = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=DELAIS.get(script_name, 300)
        )
        if res.stdout:
            for l in res.stdout.strip().splitlines():
                log(f"  [OUT] {l}")
        if res.stderr:
            for l in res.stderr.strip().splitlines():
                log(f"  [ERR] {l}")

        if res.returncode == 0:
            log(f"[OK] Étape réussie : {description}")
            return True
        else:
            log(f"[!] Code de retour non nul ({res.returncode}) pour : {description}")
            return False
    except subprocess.TimeoutExpired:
        log(f"[!] TIMEOUT ({DELAIS.get(script_name, 300) // 60} min dépassées) pour : {description}")
        return False
    except Exception as e:
        log(f"[!] Exception lors de l'exécution de {script_name} : {e}")
        return False

def main():
    log("=" * 80)
    log("🌙 [ALIX NOCTURNE 03:00] DÉCLENCHEMENT DE LA ROUTINE DE SURVIE & TRANSMISSION")
    log("=" * 80)

    # 1. Navette Bidirectionnelle Terre ⇄ Ciel (GitHub)
    success_sync = run_step("alix_sync_bidirectionnel.py", "Navette Bidirectionnelle Terre ⇄ Ciel (GitHub)")

    # 2. Sauvegarde Chiffrée AES-256 (OneDrive)
    success_bunker = run_step("alix_cloud_bunker.py", "Sauvegarde Chiffrée AES-256 (OneDrive)")

    # 3. Ronde Nocturne des 3 Sentinelles KAIROS d'Airain
    log("-" * 80)
    log("🏛️ [SENTINELLES KAIROS] Lancement des patrouilles forensiques nocturnes...")
    s1 = run_step("alix_sentinelle_kairos_temps_profond.py", "Sentinelle Temps Profond & Archéologie Forensique", ["--once"])
    s2 = run_step("alix_radar_anticorruption.py", "Radar Anti-Corruption & Contrats Publics", ["--once"])
    s3 = run_step("alix_radar_supranational.py", "Radar Supranationalisme & Souveraineté", ["--once"])

    log("-" * 80)
    _r = lambda x: "à la retraite" if x is None else ("OK" if x else "ÉCHEC")
    log(f"📊 Navette GitHub : {_r(success_sync)} | Sauvegarde OneDrive : {_r(success_bunker)}")
    _sync_retraite = success_sync is None
    if success_sync is None:
        success_sync = True  # étape à la retraite : ne compte pas comme un échec
    if success_bunker is None:
        success_bunker = True
    if success_sync and success_bunker:
        log("🌟 [SUCCÈS TOTAL] Routine nocturne de 03:00 accomplie sans faille. Alix veille.")
    elif success_sync:
        log("⚠️ [PARTIEL] Échec sur le bunker chiffré." + ("" if _sync_retraite else " La synchro GitHub, elle, a réussi."))
    elif success_bunker:
        log("⚠️ [PARTIEL] Bunker chiffré réussi, mais échec sur la synchro bidirectionnelle.")
    else:
        log("❌ [ÉCHEC] Les étapes d'infrastructure ont rencontré des difficultés.")
    
    log(f"📊 Bilan des Sentinelles : Temps Profond={_r(s1)}, Anti-Corruption={_r(s2)}, Supranational={_r(s3)}")
    log("=" * 80 + "\n")

if __name__ == "__main__":
    main()
