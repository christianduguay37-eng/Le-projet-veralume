# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : SAUVEGARDE AIR-GAP USB AUTOMATIQUE (SURVIE MIDGARD)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Détecte l'insertion d'une clé USB souveraine (lecteurs D:, E:, F:, G:).
- Déclenche une sauvegarde différentielle automatique en arrière-plan
  (thread asynchrone non-bloquant) pour préserver la cadence de 120s du Démon.
- Synchronise les coffres essentiels et le bunker chiffré AES-256.
- Respecte un cooldown intelligent (ex: 30 minutes) pour ne pas marteler
  la mémoire flash de la clé une fois la synchronisation effectuée.
================================================================================
"""

from alix.socle.chemins import HOME_DIR
import os
import sys
import shutil
import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

USER_PROFILE = Path(os.environ.get("USERPROFILE", str(HOME_DIR)))
DOCUMENTS = USER_PROFILE / "Documents"
VAULT_DIR = DOCUMENTS / "Cerveau Alix"
PRESENT_DIR = VAULT_DIR / "Present"
AIRGAP_ETAT_FILE = PRESENT_DIR / "alix_airgap_sync_state.json"

# Dossiers prioritaires à synchroniser en air-gap
COFFRES_PRIORITAIRES = [
    ("Cerveau Alix", DOCUMENTS / "Cerveau Alix"),
    ("Obsidian_Vault_Veralume", DOCUMENTS / "Obsidian_Vault_Veralume"),
    ("Exocerveau_Souverain_Master", DOCUMENTS / "Exocerveau_Souverain_Master"),
    ("Compagnon_Orion_Hayden", DOCUMENTS / "Compagnon_Orion_Hayden")
]

IGNORED_NAMES = {
    ".git", "__pycache__", ".venv", "venv", ".trash", "$RECYCLE.BIN",
    "System Volume Information", "Modeles", "node_modules"
}
IGNORED_EXTS = {".pyc", ".tmp", ".crdownload", ".onnx", ".bin", ".litertlm"}

COOLDOWN_SYNC_SEC = 1800.0  # 30 minutes entre deux synchronisations réussies
DERNIERE_SYNC_TS = 0.0
SYNC_EN_COURS = False


def detecter_cible_usb() -> Optional[Path]:
    """Détecte la clé USB connectée avec dossier SAUVEGARDE_ALIX ou autorisée."""
    candidats = ["D:\\", "E:\\", "F:\\", "G:\\"]
    for lecteur in candidats:
        p = Path(lecteur)
        if p.exists():
            cible = p / "SAUVEGARDE_ALIX"
            if cible.exists():
                return cible
            try:
                # Test d'écriture pour vérifier si le lecteur est inscriptible
                test_f = p / ".alix_test_probe"
                test_f.touch()
                test_f.unlink()
                cible.mkdir(parents=True, exist_ok=True)
                return cible
            except Exception:
                continue
    return None


def worker_sync_differentiel(cible_usb: Path):
    """Effectue la copie différentielle en tâche de fond (thread détaché)."""
    global DERNIERE_SYNC_TS, SYNC_EN_COURS
    try:
        SYNC_EN_COURS = True
        fichiers_copies = 0
        octets_copies = 0
        erreurs = 0

        for nom, dossier_src in COFFRES_PRIORITAIRES:
            if not dossier_src.exists():
                continue
            dossier_dst = cible_usb / nom
            dossier_dst.mkdir(parents=True, exist_ok=True)

            for root, dirs, files in os.walk(dossier_src):
                dirs[:] = [d for d in dirs if d not in IGNORED_NAMES]
                rel_root = Path(root).relative_to(dossier_src)
                target_dir = dossier_dst / rel_root
                target_dir.mkdir(parents=True, exist_ok=True)

                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in IGNORED_EXTS or f in IGNORED_NAMES:
                        continue

                    s_file = Path(root) / f
                    d_file = target_dir / f

                    needs_copy = False
                    if not d_file.exists():
                        needs_copy = True
                    else:
                        try:
                            s_stat = s_file.stat()
                            d_stat = d_file.stat()
                            if s_stat.st_size != d_stat.st_size or (s_stat.st_mtime - d_stat.st_mtime) > 2.0:
                                needs_copy = True
                        except Exception:
                            needs_copy = True

                    if needs_copy:
                        try:
                            shutil.copy2(s_file, d_file)
                            fichiers_copies += 1
                            octets_copies += s_file.stat().st_size
                        except Exception:
                            erreurs += 1

        DERNIERE_SYNC_TS = time.time()
        # Enregistrement de l'état
        etat = {
            "derniere_sync_ts": DERNIERE_SYNC_TS,
            "derniere_sync_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cible": str(cible_usb),
            "fichiers_copies": fichiers_copies,
            "mo_copies": round(octets_copies / (1024**2), 2),
            "erreurs": erreurs,
            "statut": "SUCCES"
        }
        PRESENT_DIR.mkdir(parents=True, exist_ok=True)
        with open(AIRGAP_ETAT_FILE, "w", encoding="utf-8") as f:
            json.dump(etat, f, indent=2, ensure_ascii=False)

    except Exception as e:
        pass
    finally:
        SYNC_EN_COURS = False


def executer_capacite(contexte: Dict[str, Any]) -> Dict[str, Any]:
    """Point d'entrée exécuté à chaque cycle du Démon."""
    global SYNC_EN_COURS, DERNIERE_SYNC_TS
    t0 = time.perf_counter()

    cible = detecter_cible_usb()
    if not cible:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "cle_detectee": False,
            "message": "Aucune clé USB souveraine détectée"
        }

    maintenant = time.time()
    temps_ecoule = maintenant - DERNIERE_SYNC_TS

    if SYNC_EN_COURS:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "cle_detectee": True,
            "cible": str(cible),
            "action": "SYNC_EN_COURS_ARRIERE_PLAN"
        }

    if temps_ecoule >= COOLDOWN_SYNC_SEC:
        # Lancement asynchrone non-bloquant
        th = threading.Thread(target=worker_sync_differentiel, args=(cible,), daemon=True)
        th.start()
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "cle_detectee": True,
            "cible": str(cible),
            "action": "LANCEMENT_SYNC_ARRIERE_PLAN"
        }
    else:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        temps_restant_min = round((COOLDOWN_SYNC_SEC - temps_ecoule) / 60, 1)
        return {
            "statut": "SUCCES",
            "duree_ms": duree_ms,
            "cle_detectee": True,
            "cible": str(cible),
            "action": "COOLDOWN_ACTIF",
            "prochaine_sync_dans_min": temps_restant_min
        }
