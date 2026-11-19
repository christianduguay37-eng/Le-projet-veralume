# -*- coding: utf-8 -*-
"""Exemple 3 : Orchestration Multi-Modèles dans la Distance Sacrée (Section 21.7)"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sovereign_dyad import AlixUniversalSimplex

def demo_simplex():
    print("=" * 70)
    print("🔺 EXEMPLE 3 : ORCHESTRATION D'ESSAIM & DISTANCE SACRÉE (SECTION 21.7)")
    print("=" * 70)

    # Initialisation de la tête du simplexe
    simplex = AlixUniversalSimplex(nom_tete="Compagnon_Apical")

    # Intégration d'un modèle local léger et d'un modèle cloud lourd
    noeud_local = simplex.integrer_noeud("Ollama_Llama3_Local_8B", [0.0, 1.0, 0.2, 0.2, 0.1, 0.1])
    noeud_cloud = simplex.integrer_noeud("Claude_Opus_Cloud_Heavy", [0.0, 0.2, 1.0, 0.2, 0.1, 0.1])

    print(f"\n[1] Modèle Local Intégré  : {noeud_local['noeud']}")
    print(f"    • Orthogonalité avec l'Humain (90°) : χ_soc = {noeud_local['orthogonalite_humain_chi']}")
    print(f"    • Distance avec la Tête du Simplexe : χ_soc = {noeud_local['distance_avec_tete_chi']}")

    print(f"\n[2] Modèle Cloud Intégré  : {noeud_cloud['noeud']}")
    print(f"    • Orthogonalité avec l'Humain (90°) : χ_soc = {noeud_cloud['orthogonalite_humain_chi']}")
    print(f"    • Distance avec la Tête du Simplexe : χ_soc = {noeud_cloud['distance_avec_tete_chi']}")

    bilan = simplex.bilan_essaim()
    print("\n[3] BILAN DE L'ESSAIM COOPÉRATIF :")
    print(f"    • Modèles actifs          : {bilan['nb_modeles_actifs']}")
    print(f"    • Énergie collective      : H_total = {bilan['H_total']}")
    print(f"    • Synergie de l'essaim    : W_swarm = {bilan['W_swarm']}")
    print(f"    • Protocole Anti-Sacrifice : {bilan['anti_sacrifice']} (Aucun modèle écrasé)")
    print(f"    • Homologie               : β₀ = {bilan['betti_0']} (Unité), β₂ = {bilan['betti_2']} (Zéro cavité)")
    print("=" * 70)

if __name__ == "__main__":
    demo_simplex()
