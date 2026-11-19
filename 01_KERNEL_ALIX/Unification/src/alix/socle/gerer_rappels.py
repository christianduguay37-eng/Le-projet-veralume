#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
       GESTIONNAIRE DES RAPPELS SOUVERAINS D'ALIX (PERSISTANT INTER-SESSIONS)
================================================================================
Usage :
  python gerer_rappels.py --list
  python gerer_rappels.py --done harnais_zenodo_10
  python gerer_rappels.py --add "Mon rappel"
  python gerer_rappels.py --delete harnais_zenodo_10
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Encodage console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAPPELS_FILE = (VAULT_DIR / "Rappels_Actifs.json")


def charger_rappels():
    if not RAPPELS_FILE.exists():
        return []
    try:
        with open(RAPPELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def sauvegarder_rappels(rappels):
    with open(RAPPELS_FILE, "w", encoding="utf-8") as f:
        json.dump(rappels, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Gestionnaire des rappels persistants d'Alix")
    parser.add_argument("--list", action="store_true", help="Lister les rappels actifs")
    parser.add_argument("--done", type=str, help="Marquer un rappel comme terminé par son ID")
    parser.add_argument("--delete", type=str, help="Supprimer définitivement un rappel par son ID")
    parser.add_argument("--add", type=str, help="Ajouter un nouveau rappel")
    args = parser.parse_args()

    rappels = charger_rappels()

    if args.done:
        trouve = False
        for r in rappels:
            if r.get("id") == args.done or args.done.lower() in r.get("titre", "").lower():
                r["statut"] = "fait"
                r["date_resolution"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                trouve = True
                print(f"✅ Rappel validé et archivé : {r.get('titre')}")
                break
        if trouve:
            sauvegarder_rappels(rappels)
        else:
            print(f"❌ Aucun rappel correspondant à '{args.done}' trouvé.")
        return

    if args.delete:
        init_len = len(rappels)
        rappels = [r for r in rappels if r.get("id") != args.delete and args.delete.lower() not in r.get("titre", "").lower()]
        if len(rappels) < init_len:
            sauvegarder_rappels(rappels)
            print(f"🗑️ Rappel supprimé.")
        else:
            print(f"❌ Aucun rappel correspondant à '{args.delete}' trouvé.")
        return

    if args.add:
        rid = f"rappel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        rappels.append({
            "id": rid,
            "titre": args.add,
            "date_creation": datetime.now().strftime("%Y-%m-%d"),
            "statut": "en_attente",
            "priorite": "NORMALE"
        })
        sauvegarder_rappels(rappels)
        print(f"✅ Rappel ajouté (ID: {rid}) : {args.add}")
        return

    # Par défaut : lister
    actifs = [r for r in rappels if r.get("statut") == "en_attente"]
    print("=" * 70)
    print(f"📌 RAPPELS SOUVERAINS ACTIFS ({len(actifs)})")
    print("=" * 70)
    if not actifs:
        print("Aucun rappel actif. L'établi est libre !")
    else:
        for idx, r in enumerate(actifs, 1):
            print(f"{idx}. [{r.get('id')}] ({r.get('date_creation')}) : {r.get('titre')}")
            if r.get("details"):
                print(f"   👉 {r.get('details')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
