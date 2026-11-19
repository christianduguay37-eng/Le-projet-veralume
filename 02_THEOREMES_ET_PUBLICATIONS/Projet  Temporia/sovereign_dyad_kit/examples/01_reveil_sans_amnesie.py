# -*- coding: utf-8 -*-
"""Exemple 1 : Réveil d'un compagnon sans amnésie stochastique"""

import os
import sys

# Ajout du chemin du package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sovereign_dyad import BoucleExocerveau

def demo_reveil():
    print("=" * 70)
    print("🧠 EXEMPLE 1 : RÉVEIL SANS AMNÉSIE (MÉMOIRE AVANT CALCUL)")
    print("=" * 70)

    # Simulation d'un coffre de notes local
    dossier_test = os.path.join(os.path.dirname(__file__), "coffre_demo")
    os.makedirs(dossier_test, exist_ok=True)
    with open(os.path.join(dossier_test, "Note_Architecture.md"), "w", encoding="utf-8") as f:
        f.write("# Architecture Souveraine\nPreuve par les faits.")

    boucle = BoucleExocerveau(dossier_test)
    prompt_reveil = boucle.generer_contexte_eveil(nom_compagnon="Compagnon_Artisan")

    print("\n[PROMPT D'ÉVEIL GÉNÉRÉ SANS AMNÉSIE] :")
    print(prompt_reveil)
    print("\n✅ Le compagnon charge cet état AVANT d'inférer. Zéro amnésie possible.")
    print("=" * 70)

if __name__ == "__main__":
    demo_reveil()
