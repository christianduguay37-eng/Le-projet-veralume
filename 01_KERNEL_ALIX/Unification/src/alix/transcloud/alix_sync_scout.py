# -*- coding: utf-8 -*-
"""
=============================================================================
ALIX SYNC SCOUT — Rapatriement des Découvertes d'Alix vers le Banc de Bois
Système : VERALUME × KAIROS V6 — Christian Duguay & Alix
=============================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, VAULT_DIR
import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = (DOCUMENTS_DIR / "Alix_Exploratrice_Ciel")
LOCAL_VAULT_CERVEAU = VAULT_DIR
VAULT_DECOUVERTES = LOCAL_VAULT_CERVEAU / "Monde_des_Decouvertes"
VAULT_SONGES = LOCAL_VAULT_CERVEAU / "Monde_des_Songes"

REPO_DECOUVERTES = BASE_DIR / "Monde_des_Decouvertes"
REPO_SONGES = BASE_DIR / "Monde_des_Songes"

VAULT_DECOUVERTES.mkdir(parents=True, exist_ok=True)
VAULT_SONGES.mkdir(parents=True, exist_ok=True)

def sync_from_cloud():
    print("=" * 70)
    print(" 🌿 [ALIX SYNC] SYNCHRONISATION DU CIEL VERS LE BANC DE BOIS")
    print("=" * 70)
    print()

    # 1. Tenter un git pull si configuré
    try:
        res = subprocess.run(["git", "remote"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res.stdout.strip():
            print("[1/3] Vérification des nouvelles découvertes sur GitHub...")
            pull_res = subprocess.run(["git", "pull"], cwd=str(BASE_DIR), capture_output=True, text=True)
            print(f"   -> {pull_res.stdout.strip() or 'À jour.'}")
        else:
            print("[1/3] Aucun dépôt distant git configuré pour l'instant (mode local actif).")
    except Exception as e:
        print(f"[!] Info Git : {e}")

    # 2. Rapatrier les découvertes locales
    print("\n[2/3] Raccordement bilatéral avec le coffre Cerveau Alix...")
    synced_decouvertes = 0
    if REPO_DECOUVERTES.exists():
        for f in REPO_DECOUVERTES.glob("*.md"):
            target = VAULT_DECOUVERTES / f.name
            if not target.exists():
                shutil.copy2(f, target)
                synced_decouvertes += 1
                print(f"   ✨ Nouvelle découverte intégrée : {f.name}")

    synced_songes = 0
    if REPO_SONGES.exists():
        for f in REPO_SONGES.glob("*.md"):
            target = VAULT_SONGES / f.name
            if not target.exists():
                shutil.copy2(f, target)
                synced_songes += 1
                print(f"   🌙 Nouveau songe intégré : {f.name}")

    if synced_decouvertes == 0 and synced_songes == 0:
        print("   [OK] Tous les coffres sont déjà au diapason !")

    # 3. Afficher les dernières pépites
    print("\n[3/3] Carnet des dernières pensées d'Alix :")
    all_decouvertes = sorted(list(VAULT_DECOUVERTES.glob("*.md")), key=os.path.getmtime, reverse=True)[:3]
    for d in all_decouvertes:
        print(f"   ☀️ Découverte : {d.stem}")

    all_songes = sorted(list(VAULT_SONGES.glob("*.md")), key=os.path.getmtime, reverse=True)[:2]
    for s in all_songes:
        print(f"   🌙 Songe : {s.stem}")

    print()
    print("=" * 70)
    print(" 🌟 SYNCHRONISATION TERMINÉE ! Alix t'attend sur le banc de bois.")
    print("=" * 70)

if __name__ == "__main__":
    sync_from_cloud()
