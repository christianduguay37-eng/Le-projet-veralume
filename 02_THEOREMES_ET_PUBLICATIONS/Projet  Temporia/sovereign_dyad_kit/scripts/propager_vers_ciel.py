# -*- coding: utf-8 -*-
"""
🎛️ Pupitre de Commande Local : Déclencheur de Propagation vers le Ciel
Permet à Christian de déclencher la symphonie des 4 Vecteurs d'un seul mot d'ordre.

Usage :
    python scripts/propager_vers_ciel.py 1.0.0
"""

import os
import sys
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def lancer_propagation():
    version = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
    tag = f"v{version}"

    print("=" * 76)
    print(f"🚀 ATELIER SOUVERAIN : DÉCLENCHEMENT DU VOL VERS LE CIEL ({tag})")
    print("=" * 76)

    # 1. TEST LOCAL PRÉALABLE DU RADIATEUR
    print("\n[1/3] Validation locale des benchmarks...")
    res = subprocess.run([sys.executable, "scripts/radiateur_ether.py"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print("❌ Échec des tests locaux :")
        print(res.stderr or res.stdout)
        sys.exit(1)
    print("✅ Benchmarks locaux 100 % au vert (Bouclier PSI validé).")

    # 2. VÉRIFICATION DU REPO GIT
    print("\n[2/3] Préparation du Tag Git...")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"chore(release): armement de la version {tag} pour Asgard"], check=False)
    
    # Création du tag
    subprocess.run(["git", "tag", "-a", tag, "-m", f"Release {tag} Sovereign Dyad Kit"], check=False)
    print(f"✅ Tag {tag} créé localement.")

    # 3. CONSEIL D'ENVOI
    print("\n[3/3] Le détonateur est armé !")
    print("Pour lancer l'arrosage des 4 vecteurs dans le Ciel (PyPI, Hugging Face, Zenodo, Pages) :")
    print("\n👉 Tape la commande :")
    print(f"   git push origin master --tags")
    print("\nEt le Cloud Runner d'Asgard prendra le relais pour tout allumer là-haut !")
    print("=" * 76)

if __name__ == "__main__":
    lancer_propagation()
