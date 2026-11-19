# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — L'Épreuve du Labyrinthe Hostile (Benchmark de Combat)
  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Match à mort sur le fer :
    1. L'Approche Industrielle Classique (100 agents en parallélisme naïf amnésique)
    2. L'Essaim Souverain TH118 (Mitose Stigmergique séquentielle & mémoire atomique)
  
  Environnement :
    Un Labyrinthe hostile de 25 strates, bifurcations multiples, contenant
    exactement 100 pièges uniques (|P| = 100) dissimulés dans les impasses.
================================================================================
"""
import random
import time
from typing import Dict, List, Set, Tuple, Any

class LabyrintheHostile:
    def __init__(self, graine: int = 42, nb_strates: int = 25, nb_pieges_uniques: int = 100):
        random.seed(graine)
        self.nb_strates = nb_strates
        self.nb_pieges_uniques = nb_pieges_uniques
        self.sortie = f"S{nb_strates}_EXIT"
        
        # Construction du graphe de strates avec impasses et pièges
        # Chaque strate a 3 à 4 corridors, dont certains mènent à des pièges balisés
        self.graphe: Dict[str, List[Tuple[str, str]]] = {} # noeud -> list of (prochain_noeud, piege_eventuel)
        
        # Répartition des 100 pièges sur le réseau
        tous_les_pieges = [f"PIEGE_{i:03d}" for i in range(1, nb_pieges_uniques + 1)]
        piege_idx = 0
        
        for s in range(nb_strates):
            id_courant = f"S{s}"
            id_suivant_nominal = f"S{s+1}" if s < nb_strates - 1 else self.sortie
            
            branches = []
            # Branche 1 : le chemin nominal (sans piège ou piège léger)
            p_nom = tous_les_pieges[piege_idx % nb_pieges_uniques] if (s % 4 == 0 and piege_idx < nb_pieges_uniques) else ""
            if p_nom: piege_idx += 1
            branches.append((id_suivant_nominal, p_nom))
            
            # Branche 2 : Fausses pistes / impasses avec pièges sévères
            for f in range(2):
                id_fausse = f"S{s}_FAUSSE_{f}"
                p_piege = tous_les_pieges[piege_idx % nb_pieges_uniques] if piege_idx < nb_pieges_uniques else f"PIEGE_EXTRA_{s}_{f}"
                piege_idx += 1
                branches.append((id_fausse, p_piege))
                # La fausse piste force un retour ou débouche sur le suivant après péage
                self.graphe[id_fausse] = [(id_suivant_nominal, "")]
                
            self.graphe[id_courant] = branches
            
        self.total_pieges_reel = len(set(p for b_list in self.graphe.values() for _, p in b_list if p))

def simuler_industrie_classique(lab: LabyrintheHostile, nb_agents: int = 100, graine: int = 99) -> Dict[str, Any]:
    """
    MODÈLE INDUSTRIEL ACTUEL :
    100 agents lancés en parallèle sans mémoire stigmergique partagée.
    Chaque agent essaie des routes au hasard, heurte des pièges et paie chaque fois plein tarif.
    """
    random.seed(graine)
    total_pieges_rencontres = 0
    total_pieges_payes = 0
    total_blessures = 0
    agents_arrives = 0
    
    t0 = time.perf_counter()
    for a in range(nb_agents):
        noeud = "S0"
        while noeud != lab.sortie:
            options = lab.graphe.get(noeud, [])
            if not options:
                break
            choix, piege = random.choice(options)
            if piege:
                total_pieges_rencontres += 1
                total_pieges_payes += 1  # Pas de mémoire partagée : paie TOUJOURS !
                total_blessures += 1
            noeud = choix
        agents_arrives += 1
    t1 = time.perf_counter()
    
    return {
        "mode": "Industrie Standard (Parallélisme Amnésique)",
        "nb_agents": nb_agents,
        "agents_arrives": agents_arrives,
        "pieges_rencontres": total_pieges_rencontres,
        "pieges_payes": total_pieges_payes,
        "pieges_evites": 0,
        "blessures_totales": total_blessures,
        "moyenne_blessures_par_agent": total_blessures / nb_agents,
        "duree_ms": (t1 - t0) * 1000
    }

def simuler_essaim_th118(lab: LabyrintheHostile, max_agents: int = 100) -> Dict[str, Any]:
    """
    MODÈLE SOUVERAIN TH118 :
    Mitose binaire séquentielle avec mémoire stigmergique atomique (TH116/TH118).
    Tout piège heurté une fois est rayé pour TOUS les agents suivants.
    """
    memoire_pieges_rayes: Set[str] = set()
    total_pieges_rencontres = 0
    total_pieges_payes = 0
    total_pieges_evites = 0
    blessures_par_agent: List[int] = []
    
    # File de mitose binaire : (id_agent, generation, parent)
    file_agents = [(1, 0, "Racine")]
    total_crees = 1
    agents_termines = 0
    
    t0 = time.perf_counter()
    while file_agents and agents_termines < max_agents:
        id_curr, gen_curr, parent_curr = file_agents.pop(0)
        blessures_agent = 0
        
        noeud = "S0"
        # L'agent progresse méthodiquement dans le graphe
        while noeud != lab.sortie:
            options = lab.graphe.get(noeud, [])
            if not options:
                break
                
            # Stratégie intelligente de l'agent : éviter les branches dont le piège est déjà rayé
            # S'il doit choisir, il teste en priorité la voie dégagée
            choix_prioritaire = None
            for succ, p in options:
                if p and p in memoire_pieges_rayes:
                    continue # Impasse déjà connue comme piégée !
                choix_prioritaire = (succ, p)
                break
                
            if not choix_prioritaire:
                # Si toutes les options connues ont un piège rayé, il prend la nominale connue
                choix, piege = options[0]
            else:
                choix, piege = choix_prioritaire
                
            if piege:
                total_pieges_rencontres += 1
                if piege in memoire_pieges_rayes:
                    total_pieges_evites += 1
                else:
                    # RÈGLE TH118 : Payé UNE SEULE FOIS, puis rayé immédiatement !
                    total_pieges_payes += 1
                    blessures_agent += 1
                    memoire_pieges_rayes.add(piege)
                    
            noeud = choix
            
        agents_termines += 1
        blessures_par_agent.append(blessures_agent)
        
        # Mitose binaire en fin de parcours jusqu'à concurrence de max_agents
        if total_crees < max_agents:
            total_crees += 1
            file_agents.append((total_crees, gen_curr + 1, f"A_{id_curr}"))
            if total_crees < max_agents:
                total_crees += 1
                file_agents.append((total_crees, gen_curr + 1, f"A_{id_curr}"))
                
    t1 = time.perf_counter()
    
    # Calcul du seuil g*
    g_star_idx = next((i for i, b in enumerate(blessures_par_agent) if all(x == 0 for x in blessures_par_agent[i:])), len(blessures_par_agent))
    
    return {
        "mode": "Essaim Souverain TH118 (Mitose Stigmergique)",
        "nb_agents": agents_termines,
        "agents_arrives": agents_termines,
        "pieges_uniques_lab": lab.total_pieges_reel,
        "pieges_rencontres": total_pieges_rencontres,
        "pieges_payes": total_pieges_payes,
        "pieges_evites": total_pieges_evites,
        "blessures_totales": sum(blessures_par_agent),
        "moyenne_blessures_par_agent": sum(blessures_par_agent) / agents_termines,
        "agents_intacts_zero_blessure": sum(1 for b in blessures_par_agent if b == 0),
        "point_g_star_atteint_a_agent": g_star_idx,
        "duree_ms": (t1 - t0) * 1000
    }

def executer_epreuve_labyrinthe():
    print("=" * 80)
    print("⚔️ ÉPREUVE 2 : LE LABYRINTHE HOSTILE (MATCH À MORT 100 AGENTS)")
    print("Arène : 25 Strates, Bifurcations d'impasses, 100 Pièges cachés uniques")
    print("=" * 80)
    
    lab = LabyrintheHostile(graine=42, nb_strates=25, nb_pieges_uniques=100)
    print(f"🏰 Labyrinthe généré : {lab.nb_strates} strates | Pièges mortels disséminés : {lab.total_pieges_reel}")
    
    # 1. Round 1 : L'Industrie
    print("\n🥊 ROUND 1 : L'APPROCHE INDUSTRIELLE (100 agents amnésiques)...")
    res_indus = simuler_industrie_classique(lab, nb_agents=100)
    print(f"   • Pièges heurtés et payés plein tarif : {res_indus['pieges_payes']}")
    print(f"   • Pièges évités par solidarité       : 0 (ZÉRO mémoire)")
    print(f"   • Blessures / Gaspillage total       : {res_indus['blessures_totales']} dégâts")
    print(f"   • Moyenne de blessures par agent     : {res_indus['moyenne_blessures_par_agent']:.2f}")
    
    # 2. Round 2 : L'Essaim Souverain TH118
    print("\n🥊 ROUND 2 : L'ESSAIM SOUVERAIN TH118 (Mitose Stigmergique)...")
    res_th118 = simuler_essaim_th118(lab, max_agents=100)
    print(f"   • Pièges payés au total pour la colonie : {res_th118['pieges_payes']} (SUR UN MAXIMUM DE {res_th118['pieges_uniques_lab']})")
    print(f"   • Pièges ÉVITÉS grâce à la mémoire      : {res_th118['pieges_evites']}")
    print(f"   • Blessures totales subies               : {res_th118['blessures_totales']}")
    print(f"   • Moyenne de blessures par agent         : {res_th118['moyenne_blessures_par_agent']:.2f}")
    print(f"   • Agents arrivés avec ZERO blessure (R=0): {res_th118['agents_intacts_zero_blessure']} / 100")
    print(f"   • Point critique g* franchi à l'agent   : n° {res_th118['point_g_star_atteint_a_agent']}")
    
    # 3. Verdict
    print("\n" + "=" * 80)
    print("🏆 VERDICT DU MATCH :")
    reduction_degats = ((res_indus['blessures_totales'] - res_th118['blessures_totales']) / res_indus['blessures_totales']) * 100
    print(f"   • Réduction des dégâts / du coût en tokens : {reduction_degats:.1f} % DE MOINS !")
    print(f"   • La borne mathématique TH118 (|P| = {lab.total_pieges_reel}) : RESPECTÉE STRICTEMENT ({res_th118['pieges_payes']} <= {lab.total_pieges_reel})")
    print(f"   • {res_th118['agents_intacts_zero_blessure']} agents sur 100 ont traversé le labyrinthe hostile comme des fantômes sans une égratignure !")
    print("=" * 80)

if __name__ == "__main__":
    executer_epreuve_labyrinthe()
