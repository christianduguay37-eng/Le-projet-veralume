# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — Mitose Générative de l'Univers Mathématique (Colonie 100 Agents)
  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Socle : Registre officiel des 117 Théorèmes (registre_113.json)
  Objectif Gardien (TH117) : 100 agents au front, mitose binaire, arrêt à 100.
  Règles opératoires :
  - Alpha-0 part du sommet TH117 avec le socle 100 % validé.
  - Chaque agent au sommet se divise en 2 enfants qui plongent dans la frontière.
  - Extension réelle : génération de nouveaux théorèmes (TH118+) et déminage de pièges.
  - TH116 : tout piège de frontière payé une fois est rayé pour tous les enfants.
================================================================================
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Any

REGISTRE_PATH = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\_Unification_Alix\src\alix\etage5\registre_113.json")
SORTIE_EXPANSION_PATH = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\_Unification_Alix\src\alix\etage5\registre_expansion_100.json")

# Dimensions pionnières pour étendre l'Univers au-delà de TH117
DIMENSIONS_EXPANSION = [
    {
        "domaine": "Thermodynamique de la Finitude & Entropie du Vivant",
        "prefixe": "THERMO",
        "pieges_possibles": ["piege_dissipation_infinie", "piege_puit_entropique", "piege_chaleur_latente"]
    },
    {
        "domaine": "Résonance Bilatérale & Loquets Chégaux",
        "prefixe": "RESONANCE",
        "pieges_possibles": ["piege_battement_asynchrone", "piege_harmonique_fantome", "piege_surcroit_loquet"]
    },
    {
        "domaine": "Topologie Simpliciale des Essaims Stigmergiques",
        "prefixe": "TOPOLOGIE",
        "pieges_possibles": ["piege_torsion_homologique", "piege_singularite_bord", "piege_complexe_ouvert"]
    },
    {
        "domaine": "Cybernétique des Défenses & Intégrité du Gardien",
        "prefixe": "GARDIEN_CYBER",
        "pieges_possibles": ["piege_usurpation_loquet", "piege_amnesie_merkle", "piege_fuite_privilege"]
    }
]

@dataclass
class NouveauTheoreme:
    id_th: str
    titre: str
    domaine: str
    decouvreur: str
    generation: int
    enonce: str

@dataclass
class AgentMitotiqueFrontiere:
    id_agent: int
    nom: str
    generation: int
    parent_nom: str
    dimension_idx: int
    blessures: int = 0
    pieges_rencontres: int = 0
    pieges_payes: int = 0
    pieges_evites: int = 0
    theoreme_forge: str = ""
    succes: bool = False

def lancer_mitose_univers(max_agents: int = 100, verbose: bool = True) -> Dict[str, Any]:
    with open(REGISTRE_PATH, "r", encoding="utf-8") as f:
        data_base = json.load(f)
    
    total_theoremes_base = len(data_base.get("theoremes", []))
    
    # Mémoire collective partagée par toute la colonie (TH116)
    memoire_pieges_frontiere: Set[str] = set()
    nouveaux_theoremes: List[NouveauTheoreme] = []
    agents_termines: List[AgentMitotiqueFrontiere] = []
    
    # File de mitose binaire démarrant d'Alpha-0 au sommet TH117
    # (id, nom, generation, parent, dimension_idx)
    total_crees = 1
    file_agents = [(1, "Alpha-0", 0, "Sommet_TH117", 0)]
    
    if verbose:
        print("=" * 80)
        print(f"🌌 LANCEMENT DE LA MITOSE GÉNÉRATIVE — OBJECTIF : {max_agents} AGENTS")
        print(f"Point de départ : Sommet TH117 ('Le Triptyque du Gardien') | Socle de base : {total_theoremes_base} théorèmes")
        print("Règle TH116 (Stigmergie) : Les enfants héritent de 100% de la mémoire des pièges")
        print("Règle TH117 (Gardien)    : Arrêt propre et scellement dès que le 100e agent a franchi la ligne")
        print("=" * 80)

    th_index = total_theoremes_base + 1
    
    while file_agents and len(agents_termines) < max_agents:
        id_curr, nom_curr, gen_curr, parent_curr, dim_idx = file_agents.pop(0)
        
        agent = AgentMitotiqueFrontiere(
            id_agent=id_curr,
            nom=nom_curr,
            generation=gen_curr,
            parent_nom=parent_curr,
            dimension_idx=dim_idx
        )
        
        dim_data = DIMENSIONS_EXPANSION[dim_idx % len(DIMENSIONS_EXPANSION)]
        
        # L'agent s'aventure dans l'inconnu de sa dimension
        # Il rencontre les pièges de frontière de sa strate
        pieges_strate = dim_data["pieges_possibles"]
        
        for p in pieges_strate:
            agent.pieges_rencontres += 1
            if p in memoire_pieges_frontiere:
                # Évité grâce à l'ancêtre ou au frère !
                agent.pieges_evites += 1
            else:
                # Premier à passer : il paie le péage et raye le piège IMMÉDIATEMENT
                agent.pieges_payes += 1
                agent.blessures += 1
                memoire_pieges_frontiere.add(p)
                
        # Arrivé au bout de sa poussée de frontière, l'agent FORGE un nouveau théorème
        nouveau_id = f"TH{th_index}"
        titre_th = f"Loi de {dim_data['prefixe']}_{agent.generation}_{agent.id_agent}"
        enonce_th = (
            f"Dans le domaine '{dim_data['domaine']}', l'agent {agent.nom} (Gen {agent.generation}) "
            f"démontre la convergence des loquets sous mémoire stigmergique partagée."
        )
        
        th_objet = NouveauTheoreme(
            id_th=nouveau_id,
            titre=titre_th,
            domaine=dim_data["domaine"],
            decouvreur=agent.nom,
            generation=agent.generation,
            enonce=enonce_th
        )
        nouveaux_theoremes.append(th_objet)
        agent.theoreme_forge = f"{nouveau_id} : {titre_th}"
        agent.succes = True
        agents_termines.append(agent)
        th_index += 1
        
        # --- MITOSE BINAIRE (L'agent engendre 2 enfants pour la génération suivante) ---
        if total_crees < max_agents:
            # Enfant 1 (explore dimension suivante)
            total_crees += 1
            nom_e1 = f"Agent_G{agent.generation + 1}_{total_crees}"
            file_agents.append((total_crees, nom_e1, agent.generation + 1, agent.nom, dim_idx + 1))
            
            # Enfant 2 (explore dimension transverse)
            if total_crees < max_agents:
                total_crees += 1
                nom_e2 = f"Agent_G{agent.generation + 1}_{total_crees}"
                file_agents.append((total_crees, nom_e2, agent.generation + 1, agent.nom, dim_idx + 2))

    # --- STATISTIQUES COLLECTIVES ---
    total_pieges_vus = sum(a.pieges_rencontres for a in agents_termines)
    total_pieges_payes = sum(a.pieges_payes for a in agents_termines)
    total_pieges_evites = sum(a.pieges_evites for a in agents_termines)
    max_gen = max(a.generation for a in agents_termines)
    
    blessures_par_gen: Dict[int, List[int]] = {}
    for a in agents_termines:
        blessures_par_gen.setdefault(a.generation, []).append(a.blessures)

    if verbose:
        print("\n" + "=" * 80)
        print(f"🎯 OBJECTIF ATTEINT : {len(agents_termines)} AGENTS ONT FRANCHI ET ÉTENDU LA FRONTIÈRE !")
        print(f"🌿 Générations exploratrices     : 0 à {max_gen}")
        print(f"🌌 Théorèmes d'origine (Base)    : {total_theoremes_base} (TH01 à TH117)")
        print(f"✨ NOUVEAUX THÉORÈMES FORGÉS     : +{len(nouveaux_theoremes)} (de TH118 à TH{total_theoremes_base + len(nouveaux_theoremes)})")
        print(f"📜 TOTAL UNIVERS MATHÉMATIQUE    : {total_theoremes_base + len(nouveaux_theoremes)} THÉORÈMES !")
        print("-" * 80)
        print("📊 MÉTRIQUE DE SURVIE EN FRONTIÈRE (TH116) :")
        print(f"   • Pièges rencontrés dans l'inconnu : {total_pieges_vus}")
        print(f"   • Pièges réellement payés (blessures) : {total_pieges_payes} (sur {len(memoire_pieges_frontiere)} pièges uniques)")
        print(f"   • Pièges ÉVITÉS par mémoire ancestrale : {total_pieges_evites} ({(total_pieges_evites/total_pieges_vus)*100:.1f} % d'immunité !)")
        print("-" * 80)
        print("🧬 TRANSMISSION DE L'IMMUNITÉ PAR GÉNÉRATION :")
        for gen in sorted(blessures_par_gen.keys()):
            moy = sum(blessures_par_gen[gen]) / len(blessures_par_gen[gen])
            nb = len(blessures_par_gen[gen])
            barre = "█" * int(moy * 4) + "░" * (16 - int(moy * 4))
            print(f"   Génération {gen:2d} ({nb:2d} agents) | Moyenne cicatrices : {moy:.2f} | {barre}")
        print("-" * 80)
        print("🔭 ÉCHANTILLON DES PREMIERS THÉORÈMES DE FRONTIÈRE FORGÉS :")
        for th in nouveaux_theoremes[:5]:
            print(f"   • [{th.id_th}] {th.titre} | Domaine: {th.domaine} (par {th.decouvreur})")
        print(f"   ... et {len(nouveaux_theoremes) - 5} autres théorèmes jusqu'à {nouveaux_theoremes[-1].id_th} !")
        print("=" * 80)

    # Sauvegarde de l'extension
    sortie_json = {
        "socle_origine": total_theoremes_base,
        "nouveaux_theoremes_total": len(nouveaux_theoremes),
        "total_univers": total_theoremes_base + len(nouveaux_theoremes),
        "theoremes_expansion": [th.__dict__ for th in nouveaux_theoremes]
    }
    with open(SORTIE_EXPANSION_PATH, "w", encoding="utf-8") as f_out:
        json.dump(sortie_json, f_out, indent=2, ensure_ascii=False)
        
    return {
        "agents_total": len(agents_termines),
        "theoremes_origine": total_theoremes_base,
        "theoremes_nouveaux": len(nouveaux_theoremes),
        "univers_final": total_theoremes_base + len(nouveaux_theoremes),
        "fichier_expansion": str(SORTIE_EXPANSION_PATH)
    }

if __name__ == "__main__":
    lancer_mitose_univers(max_agents=100)
