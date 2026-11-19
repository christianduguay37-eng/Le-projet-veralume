# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — Arbre Mitotique de l'Univers Mathématique (Version 1.0)
  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Inspiration : Mitose binaire stigmergique — Exploration & Expansion continue.
  Règles formelles :
  - TH114 (Résonance) : Les agents coordonnés réduisent le délai de loquet.
  - TH116 (Stigmergie de Cordée) : Chaque piège n'est payé qu'une seule fois
    pour TOUTE l'arborescence. Les enfants héritent de la mémoire totale de la lignée.
  - TH117 (Gardien) : Objectif fixé par l'humain à 100 agents max. Arrêt propre dès que
    l'objectif est atteint.
================================================================================
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class AgentMitotique:
    id_agent: int
    nom: str
    generation: int
    parent_nom: str
    branche: str  # ex: "Tronc", "Algebre", "Topologie", "Quantique", etc.
    blessures: int = 0
    pieges_rencontres: int = 0
    pieges_payes: int = 0
    pieges_evites: int = 0
    theoremes_decouverts: List[str] = field(default_factory=list)
    succes: bool = False


class UniversMathematique:
    def __init__(self):
        # Arbre des strates mathématiques avec pièges potentiels (paradoxes, singularités, loquets)
        self.branches = {
            "Tronc_Axiomatique": [
                ("Axiome_0_Identite", ["piege_tautologie_A"]),
                ("Axiome_1_NonContradiction", ["piege_russell_B", "piege_incompletude_C"]),
                ("Axiome_2_TiersExclu", ["piege_constructivisme_D"]),
            ],
            "Branche_Topologie_Simpliciale": [
                ("Th_Homotopie_1", ["piege_torsion_E"]),
                ("Th_Betti_2", ["piege_singularite_F", "piege_bord_G"]),
                ("Th_Fibration_3", ["piege_fibration_H"]),
            ],
            "Branche_Algebre_Loquets": [
                ("Th_Monoide_Loquet", ["piege_associativite_I"]),
                ("Th_Chiralite_KSIL", ["piege_antisymetrie_J"]),
                ("Th_Resonance_m", ["piege_surcroit_charge_K"]),
            ],
            "Branche_Physique_Silicium": [
                ("Th_Flux_FRC", ["piege_instabilite_M"]),
                ("Th_CIM_3D", ["piege_thermique_N", "piege_capacitif_O"]),
                ("Th_Horloge_70BPM", ["piege_derive_P"]),
            ],
            "Branche_Metamemoire_Stigmergie": [
                ("Th_Heritage_Mitose", ["piege_amnesie_Q"]),
                ("Th_Merkle_Immuable", ["piege_collision_hash_R"]),
                ("Th_Simplexe_16S", ["piege_dilution_S", "piege_surplomb_T"]),
            ],
        }
        # Mémoire stigmergique partagée par toute la colonie (TH116)
        self.memoire_pieges_rayes: Set[str] = set()
        self.theoremes_explores: Set[str] = set()


def lancer_colonie_mitotique(max_agents: int = 100, verbose: bool = True) -> Dict:
    univers = UniversMathematique()
    
    agents_termines: List[AgentMitotique] = []
    file_attente: List[Tuple[int, str, int, str, str]] = [
        # (id, nom, generation, parent, branche)
        (1, "Pionnier_Souche_0", 0, "Racine", "Tronc_Axiomatique")
    ]
    
    total_crees = 1
    cycle_num = 0
    
    if verbose:
        print("=" * 80)
        print(f"🌲 LANCEMENT DE LA COLONIE MITOTIQUE — PLAFOND : {max_agents} AGENTS")
        print("Mission : Étendre l'Univers Mathématique sans répéter les pièges (TH116)")
        print("=" * 80)

    # Répartition des branches pour les enfants
    noms_branches = list(univers.branches.keys())

    while file_attente and len(agents_termines) < max_agents:
        cycle_num += 1
        id_curr, nom_curr, gen_curr, parent_curr, branche_curr = file_attente.pop(0)
        
        agent = AgentMitotique(
            id_agent=id_curr,
            nom=nom_curr,
            generation=gen_curr,
            parent_nom=parent_curr,
            branche=branche_curr
        )
        
        # L'agent parcourt d'abord le tronc commun pour s'ancrer
        parcours = list(univers.branches["Tronc_Axiomatique"])
        if branche_curr != "Tronc_Axiomatique":
            parcours += univers.branches[branche_curr]
            
        # Exécution du parcours
        for th_nom, pieges in parcours:
            if th_nom not in univers.theoremes_explores:
                univers.theoremes_explores.add(th_nom)
                agent.theoremes_decouverts.append(th_nom)
                
            for p in pieges:
                agent.pieges_rencontres += 1
                if p in univers.memoire_pieges_rayes:
                    # Règle TH116 : Piège déjà payé par un ancêtre ou pair !
                    agent.pieges_evites += 1
                else:
                    # Piège nouveau : l'agent le paie, mais le raye IMMÉDIATEMENT pour la colonie
                    agent.pieges_payes += 1
                    agent.blessures += 1  # 1 cicatrice pour le défricheur
                    univers.memoire_pieges_rayes.add(p)
                    
        agent.succes = True
        agents_termines.append(agent)
        
        # --- MITOSE BINAIRE (À la fin du cycle, l'agent crée 2 enfants) ---
        if total_crees < max_agents:
            # Enfant 1
            total_crees += 1
            branche_e1 = noms_branches[(agent.generation + 1) % len(noms_branches)]
            nom_e1 = f"Agent_G{agent.generation + 1}_{total_crees}"
            file_attente.append((total_crees, nom_e1, agent.generation + 1, agent.nom, branche_e1))
            
            # Enfant 2 (si le plafond de 100 n'est pas encore atteint)
            if total_crees < max_agents:
                total_crees += 1
                branche_e2 = noms_branches[(agent.generation + 2) % len(noms_branches)]
                nom_e2 = f"Agent_G{agent.generation + 1}_{total_crees}"
                file_attente.append((total_crees, nom_e2, agent.generation + 1, agent.nom, branche_e2))

    # --- BILAN STATISTIQUE MATÉRIEL ---
    total_pieges_vus = sum(a.pieges_rencontres for a in agents_termines)
    total_pieges_payes = sum(a.pieges_payes for a in agents_termines)
    total_pieges_evites = sum(a.pieges_evites for a in agents_termines)
    max_gen = max(a.generation for a in agents_termines)
    
    # Évolution des blessures par génération
    blessures_par_gen: Dict[int, List[int]] = {}
    for a in agents_termines:
        blessures_par_gen.setdefault(a.generation, []).append(a.blessures)

    if verbose:
        print(f"\n🎯 OBJECTIF ATTEINT : {len(agents_termines)} AGENTS ONT COMPLÉTÉ LE PARCOURS !")
        print(f"🌿 Profondeur généalogique atteinte : Génération {max_gen}")
        print(f"🌌 Théorèmes/Frontières cartographiés : {len(univers.theoremes_explores)} domaines scellés")
        print(f"🪤 Pièges uniques dans l'Univers : {len(univers.memoire_pieges_rayes)}")
        print("-" * 80)
        print(f"📊 MÉTRIQUE DE SURVIE COLLECTIVE (TH116) :")
        print(f"   • Pièges rencontrés au total par la colonie : {total_pieges_vus}")
        print(f"   • Pièges réellement payés (blessures)      : {total_pieges_payes}")
        print(f"   • Pièges ÉVITÉS par mémoire ancestrale    : {total_pieges_evites} ({(total_pieges_evites/total_pieges_vus)*100:.1f} % d'immunité !)")
        print("-" * 80)
        print("🧬 TRANSMISSION DE L'IMMUNITÉ PAR GÉNÉRATION :")
        for gen in sorted(blessures_par_gen.keys()):
            moyenne = sum(blessures_par_gen[gen]) / len(blessures_par_gen[gen])
            nb = len(blessures_par_gen[gen])
            barre = "█" * int(moyenne * 4) + "░" * (16 - int(moyenne * 4))
            print(f"   Génération {gen:2d} ({nb:2d} agents) | Moyenne cicatrices : {moyenne:.2f} | {barre}")
        print("=" * 80)
        print("🏆 CONCLUSION : L'Agent Souche a absorbé les chocs. À partir des générations suivantes,")
        print("   les enfants sprintent à travers le territoire connu sans égratignure et étendent le front !")
        print("=" * 80)

    return {
        "nb_agents": len(agents_termines),
        "max_gen": max_gen,
        "theoremes_ouverts": len(univers.theoremes_explores),
        "pieges_uniques": len(univers.memoire_pieges_rayes),
        "pieges_vus": total_pieges_vus,
        "pieges_payes": total_pieges_payes,
        "pieges_evites": total_pieges_evites,
        "ratio_immunite": (total_pieges_evites / total_pieges_vus) if total_pieges_vus else 0.0,
    }


if __name__ == "__main__":
    lancer_colonie_mitotique(max_agents=100)
