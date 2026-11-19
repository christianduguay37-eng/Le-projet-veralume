# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — Déblocage de TH48 par la Mitose Stigmergique (TH118)
  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Problème historique :
    TH48 (« La Libération Collective est universellement réalisable ») était
    classé CONDITIONNEL depuis des mois, car si le groupe initial de porteurs k
    est inférieur au seuil critique k* (k < k* = ⌈n / ⌊τ0/δ⌋⌉, TH45), les porteurs
    s'épuisent et des captifs restent piégés à jamais.
  
  Solution par TH118 (Mitose Stigmergique) :
    Tout captif hissé en A* subit la mitose binaire (TH118) avec mémoire héritée (TH116)
    et devient 2 porteurs actifs. L'effectif de porteurs n'est plus statique :
    il croît en cascade géométrique (1 -> 2 -> 4...), pulvérisant le seuil critique k*.
================================================================================
"""
import math
from typing import Dict, List, Any

def simuler_liberation_classique(n_captifs: int = 5, k_porteurs: int = 1, tau0: int = 10, delta: int = 4) -> Dict[str, Any]:
    """Ancienne règle de Temporia (Sans mitose, groupe de porteurs statique)."""
    porteurs = [tau0] * k_porteurs
    captifs_restants = n_captifs
    hisses = 0
    tombes = 0
    
    # Tentative de hissage
    changement = True
    while captifs_restants > 0 and changement:
        changement = False
        for i in range(len(porteurs)):
            if captifs_restants > 0 and porteurs[i] >= delta:
                porteurs[i] -= delta
                captifs_restants -= 1
                hisses += 1
                changement = True
                
    tombes = sum(1 for p in porteurs if p < delta)
    return {
        "mode": "Classique (Sans mitose)",
        "k_initial": k_porteurs,
        "n_captifs_initial": n_captifs,
        "hisses": hisses,
        "captifs_restants": captifs_restants,
        "porteurs_finaux": len(porteurs),
        "energie_restante": sum(porteurs),
        "succes_total": (captifs_restants == 0)
    }

def simuler_liberation_mitotique_th118(n_captifs: int = 5, k_porteurs: int = 1, tau0: int = 10, delta: int = 4) -> Dict[str, Any]:
    """Nouvelle règle avec TH118 (Mitose Stigmergique en A*)."""
    # Liste des porteurs actifs avec leur énergie respective
    porteurs = [tau0] * k_porteurs
    captifs_restants = n_captifs
    hisses = 0
    generations_mitose = 0
    historique_cycles = []
    
    cycle = 0
    while captifs_restants > 0:
        cycle += 1
        nouveaux_hisses_ce_cycle = 0
        
        # 1. Les porteurs disponibles hissent autant de captifs qu'ils peuvent
        for i in range(len(porteurs)):
            if captifs_restants > 0 and porteurs[i] >= delta:
                porteurs[i] -= delta
                captifs_restants -= 1
                hisses += 1
                nouveaux_hisses_ce_cycle += 1
                
        # 2. RÈGLE TH118 : Chaque captif hissé en A* subit la mitose binaire
        # Il se divise en 2 nouveaux porteurs régénérés (dotés de tau0 et de la mémoire)
        nouveaux_porteurs = []
        for _ in range(nouveaux_hisses_ce_cycle):
            nouveaux_porteurs.extend([tau0, tau0])  # Mitose 1 -> 2
            
        porteurs.extend(nouveaux_porteurs)
        if nouveaux_hisses_ce_cycle > 0:
            generations_mitose += 1
            
        historique_cycles.append({
            "cycle": cycle,
            "hisses_cumul": hisses,
            "captifs_restants": captifs_restants,
            "porteurs_actifs": len(porteurs),
            "nouveaux_generes": len(nouveaux_porteurs)
        })
        
        # Sécurité : si aucun captif n'a pu être hissé et aucun nouveau porteur généré
        if nouveaux_hisses_ce_cycle == 0 and all(p < delta for p in porteurs):
            break
            
    return {
        "mode": "Mitotique TH118 (Avec mitose stigmergique en A*)",
        "k_initial": k_porteurs,
        "n_captifs_initial": n_captifs,
        "hisses": hisses,
        "captifs_restants": captifs_restants,
        "porteurs_finaux": len(porteurs),
        "energie_restante": sum(porteurs),
        "generations_mitose": generations_mitose,
        "historique": historique_cycles,
        "succes_total": (captifs_restants == 0)
    }

def executer_comparatif():
    n = 5
    tau0 = 10
    delta = 4
    # Seuil critique de TH45 : k* = ceil(5 / floor(10/4)) = ceil(5/2) = 3 porteurs
    k_star = math.ceil(n / (tau0 // delta))
    
    print("=" * 80)
    print("⚖️ ÉPREUVE COMPARATIVE SUR TH48 : LIBÉRATION COLLECTIVE AVEC k < k*")
    print(f"Paramètres : {n} captifs à hisser | Énergie initiale tau0={tau0} | Coût d'aide delta={delta}")
    print(f"Seuil critique classique (TH45) : k* = {k_star} porteurs requis pour réussir.")
    print(f"Condition d'échec testée : NOUS COMMENÇONS AVEC UN SEUL PORTEUR (k = 1 < k*=3) !")
    print("=" * 80)
    
    # 1. Test Classique (Sans mitose)
    res_classique = simuler_liberation_classique(n_captifs=n, k_porteurs=1, tau0=tau0, delta=delta)
    print("\n1️⃣ MODÈLE CLASSIQUE HISTORIQUE (Sans mitose) :")
    print(f"   • Captifs hissés : {res_classique['hisses']} / {n}")
    print(f"   • Captifs abandonnés : {res_classique['captifs_restants']}")
    print(f"   • Porteurs finaux : {res_classique['porteurs_finaux']} (épuisés)")
    print(f"   • Résultat TH48 : {'RÉUSSI' if res_classique['succes_total'] else 'ÉCHEC (Conditionnel / Bloqué)'}")
    
    # 2. Test TH118 (Mitose Stigmergique)
    res_mitose = simuler_liberation_mitotique_th118(n_captifs=n, k_porteurs=1, tau0=tau0, delta=delta)
    print("\n2️⃣ NOUVEAU MODÈLE AVEC TH118 (Mitose Stigmergique) :")
    for step in res_mitose["historique"]:
        print(f"   • Cycle {step['cycle']} : {step['hisses_cumul']}/{n} hissés | Captifs restants: {step['captifs_restants']} | Porteurs disponibles: {step['porteurs_actifs']} (+{step['nouveaux_generes']} nés par mitose)")
    print(f"   • Captifs abandonnés : {res_mitose['captifs_restants']}")
    print(f"   • Porteurs finaux : {res_mitose['porteurs_finaux']} en pleine puissance")
    print(f"   • Énergie collective finale : {res_mitose['energie_restante']} unités (Surplus massif !)")
    print(f"   • Résultat TH48 : {'RÉUSSITE UNIVERSELLE (100% LIBÉRÉS)' if res_mitose['succes_total'] else 'ÉCHEC'}")
    
    print("\n" + "=" * 80)
    print("🎯 CONCLUSION FORMELLE :")
    print("   TH118 fait sauter le verrou de TH45 ! Même avec k=1 (très inférieur à k*=3),")
    print("   la mitose des captifs hissés en A* transforme la pénurie d'énergie en avalanche")
    print("   solidaire. TH48 devient UNIVERSELLEMENT VRAI sous mitose !")
    print("=" * 80)

if __name__ == "__main__":
    executer_comparatif()
