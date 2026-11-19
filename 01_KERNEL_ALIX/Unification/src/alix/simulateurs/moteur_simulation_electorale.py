# -*- coding: utf-8 -*-
"""
================================================================================
     MOTEUR DE SIMULATION ÉLECTORALE SOUVERAIN (QC-125 CALIBRÉ) v1.6
                 « LES VRAIS CHIFFRES » (AUDIT SRE HORUS)
================================================================================
Auteurs : Christian Duguay & Alix (Horus SRE)
Cadre   : Scrutin Général du Québec (Scénario d'Octobre 2026)
Règles  :
  1. ZÉRO DOUBLE COMPTABILISATION des transfuges (le sondage reflète déjà l'état net).
  2. Swing mixte (50% proportionnel, 50% additif) borné et équilibré.
  3. Bruit régional corrélé (grappe macro-régionale) + bruit local.
  4. Modulation démographique DGEQ (aînés 55+ à forte participation vs jeunes).
  5. Primes d'ancrage réelles des députés sortants solides (Jolin-Barrette, Poulin, etc.).
================================================================================
"""

import sys
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Import de la base de données des 125 comtés
from alix.simulateurs.donnees_125_circonscriptions import CIRCONSCRIPTIONS_125


class SimulateurElectoralSouverainV16:
    """Moteur de simulation v1.6 corrigé : Réalisme politique strict sans biais de saturation."""

    # Primes d'ancrage local réelles (effet candidat mesuré historiquement : 2% à 8%)
    PRIMES_LOCALES = {
        # CAQ : Piliers solidement enracinés qui sauvent les meubles
        "Borduas": {"CAQ": 6.5},           # Simon Jolin-Barrette (fief personnel très fort)
        "Beauce-Sud": {"CAQ": 7.0},         # Samuel Poulin (réseau d'affaires local puissant)
        "Sanguinet": {"CAQ": 4.5},          # Christine Fréchette (cheffe / Première ministre)
        "Vachon": {"CAQ": 3.5},             # Ian Lafrenière (visibilité médiatique)

        # Chefs & Vedettes
        "Bellechasse": {"PCQ": 8.5},        # Éric Duhaime (campagne hyper-ciblée)
        "Chauveau": {"PCQ": 5.0},           # Bastion conservateur historique
        "Camille-Laurin": {"PQ": 7.0},      # Paul St-Pierre Plamondon
        "Mercier": {"QS": 8.0},             # Ruba Ghazal
        "Gouin": {"QS": 6.5},               # Alexandre Boulerice (ancrage militant)
        "LaFontaine": {"PLQ": 6.0},         # Marc Tanguay

        # Députés d'opposition incontournables
        "Matane-Matapédia": {"PQ": 20.0},   # Pascal Bérubé (fief imprenable)
        "Arthabaska": {"PQ": 9.0},          # Alex Boissonneault (vainqueur partielle août 2025)
        "Jean-Talon": {"PQ": 6.5},          # Pascal Paradis
        "Îles-de-la-Madeleine": {"PQ": 10.0}, # Joël Arseneau
        "Pontiac": {"PLQ": 8.0},            # André Fortin
        "Laurier-Dorion": {"QS": 5.0},      # Andrés Fontecilla
        "Sainte-Marie-Saint-Jacques": {"QS": 6.0},
    }

    # Circonscriptions où la CAQ subit un malus d'abandon (démission du ministre sortant sans relève connue)
    ABANDONS_CAQ = [
        "Granby", "L'Assomption", "La Prairie", "Champlain", "Louis-Hébert",
        "Deux-Montagnes", "Terrebonne", "Trois-Rivières", "Mirabel", "Iberville"
    ]

    def __init__(self, sondage_brut: Dict[str, float]):
        self.sondage_brut = sondage_brut
        self.circonscriptions = CIRCONSCRIPTIONS_125
        self.regions_uniques = sorted(list(set(c["region"] for c in self.circonscriptions)))

    def simuler_mode_brut_qc125(self, nb_simulations: int = 5000) -> Dict[str, Any]:
        """Modèle brut Qc125 : swing proportionnel pur sans correction démographique."""
        baseline_2022 = {"CAQ": 41.0, "QS": 15.4, "PQ": 14.6, "PLQ": 14.4, "PCQ": 12.9}
        swings = {p: self.sondage_brut[p] / baseline_2022[p] for p in self.sondage_brut}

        siege_counts = {p: [0] * nb_simulations for p in self.sondage_brut}
        gagnants_comte = {c["nom"]: {p: 0 for p in self.sondage_brut} for c in self.circonscriptions}

        for sim in range(nb_simulations):
            for c in self.circonscriptions:
                scores_comte = {}
                for p in self.sondage_brut:
                    base_p = c["res_2022"].get(p, 5.0)
                    proj_p = base_p * swings[p]
                    if c["region"] == "Capitale_Nationale" and p == "PCQ":
                        proj_p *= 1.25
                    if c["region"] == "Montreal" and p == "PLQ" and c["pct_franco"] < 50:
                        proj_p *= 1.20
                    bruit = random.gauss(0, 2.2)
                    scores_comte[p] = max(0.5, proj_p + bruit)
                
                vainqueur = max(scores_comte, key=scores_comte.get)
                siege_counts[vainqueur][sim] += 1
                gagnants_comte[c["nom"]][vainqueur] += 1

        stats = {}
        for p in self.sondage_brut:
            vals = sorted(siege_counts[p])
            stats[p] = {
                "mediane": vals[nb_simulations // 2],
                "min": vals[int(nb_simulations * 0.05)],
                "max": vals[int(nb_simulations * 0.95)],
                "moyenne": round(sum(vals) / nb_simulations, 1)
            }
        return {"stats": stats, "details_comtes": gagnants_comte}

    def simuler_vrais_chiffres_v16(self, nb_simulations: int = 5000) -> Dict[str, Any]:
        """
        Modèle v1.6 Réaliste (Zéro double comptabilisation) :
        - Swing mixte 50/50 calibré sur le vote provincial.
        - Distribution régionale réaliste (PCQ fort à Québec/Beauce, PLQ fort dans l'Ouest/Laval, PQ fort en région/450).
        - Effet d'âge DGEQ équilibré (les aînés votent à 78%, les jeunes à 54%).
        - Primes de comté raisonnables.
        """
        baseline_2022 = {"CAQ": 41.0, "QS": 15.4, "PQ": 14.6, "PLQ": 14.4, "PCQ": 12.9}
        swings_prop = {p: self.sondage_brut[p] / baseline_2022[p] for p in self.sondage_brut}
        deltas_add = {p: self.sondage_brut[p] - baseline_2022[p] for p in self.sondage_brut}

        siege_counts = {p: [0] * nb_simulations for p in self.sondage_brut}
        gagnants_comte = {c["nom"]: {p: 0 for p in self.sondage_brut} for c in self.circonscriptions}
        scores_moyens = {c["nom"]: {p: 0.0 for p in self.sondage_brut} for c in self.circonscriptions}
        toss_ups_count = {c["nom"]: 0 for c in self.circonscriptions}

        for sim in range(nb_simulations):
            # 1. Bruit régional corrélé (erreur de grappe de sondage) : sigma = 1.3
            bruits_regionaux = {
                reg: {p: random.gauss(0, 1.3) for p in self.sondage_brut}
                for reg in self.regions_uniques
            }

            for c in self.circonscriptions:
                pct_55 = c["pct_55_plus"]
                pct_franco = c["pct_franco"]
                milieu = c["milieu"]
                reg = c["region"]
                nom = c["nom"]

                # Poids démographique d'urne (Likely Voter)
                poids_urne_55 = (pct_55 * 0.76) / ((pct_55 * 0.76) + ((100 - pct_55) * 0.54))
                poids_urne_jeunes = 1.0 - poids_urne_55

                scores_comte = {}
                for p in self.sondage_brut:
                    base_p = c["res_2022"].get(p, 4.0)

                    # Swing mixte 50% proportionnel, 50% additif
                    proj_prop = base_p * swings_prop[p]
                    proj_add = base_p + deltas_add[p]
                    proj_p = max(0.8, 0.50 * proj_prop + 0.50 * proj_add)

                    # Ajustements régionaux & sociologiques réalistes (SANS double comptabilisation)
                    if p == "PQ":
                        # Bonus dans les comtés francophones aînés
                        bonus_age = 1.0 + (poids_urne_55 - 0.50) * 0.20
                        bonus_fr = 1.05 if pct_franco > 85 else (0.80 if pct_franco < 50 else 1.0)
                        proj_p *= bonus_age * bonus_fr
                        if reg in ["Est_du_Quebec", "Saguenay_Lac_St_Jean", "Mauricie_Centre_du_Quebec"]:
                            proj_p *= 1.06

                    elif p == "PLQ":
                        if pct_franco < 50:
                            proj_p *= 1.25 # Forteresse anglophone/allophone étanche
                        elif pct_franco > 85:
                            proj_p *= 0.75 # Déclin sévère en région francophone

                    elif p == "PCQ":
                        # Fort à Québec et Chaudière-Appalaches, plus faible ailleurs
                        if reg in ["Capitale_Nationale", "Chaudiere_Appalaches"]:
                            proj_p *= 1.15
                        else:
                            proj_p *= 0.92
                        # Facteur âge (pression à la baisse chez les 55+)
                        proj_p *= (1.0 - (poids_urne_55 - 0.50) * 0.15)

                    elif p == "CAQ":
                        # Baisse générale de la CAQ, mais résistance des comtés d'aînés de banlieue
                        if nom in self.ABANDONS_CAQ:
                            proj_p *= 0.88 # Siège orphelin sans député vedette
                        else:
                            # Les sortants résistent mieux chez les aînés
                            proj_p *= (1.0 + (poids_urne_55 - 0.50) * 0.12)

                    elif p == "QS":
                        # Concentration métropolitaine
                        if reg == "Montreal" and nom in ["Gouin", "Mercier", "Laurier-Dorion", "Sainte-Marie-Saint-Jacques", "Rosemont"]:
                            proj_p *= 1.20
                        elif pct_55 > 50:
                            proj_p *= 0.80 # Très faible dans les comtés âgés

                    # Ajout des primes locales mesurées
                    if nom in self.PRIMES_LOCALES and p in self.PRIMES_LOCALES[nom]:
                        proj_p += self.PRIMES_LOCALES[nom][p]
                    elif p == c["vainqueur_2022"] and nom not in self.ABANDONS_CAQ:
                        proj_p += 1.5 # Prime sortant standard modeste

                    # Bruit combiné : Régional (1.3) + Local (1.0)
                    bruit_r = bruits_regionaux[reg][p]
                    bruit_l = random.gauss(0, 1.0)
                    scores_comte[p] = max(0.5, proj_p + bruit_r + bruit_l)

                # Normalisation stricte à 100%
                total_s = sum(scores_comte.values())
                for p in scores_comte:
                    scores_comte[p] = (scores_comte[p] / total_s) * 100.0
                    scores_moyens[nom][p] += scores_comte[p]

                # Détection de toss-up (< 3% d'écart entre 1er et 2e)
                tries = sorted(scores_comte.values(), reverse=True)
                if (tries[0] - tries[1]) < 3.0:
                    toss_ups_count[nom] += 1

                vainqueur = max(scores_comte, key=scores_comte.get)
                siege_counts[vainqueur][sim] += 1
                gagnants_comte[nom][vainqueur] += 1

        # Moyennes des scores
        for nom in scores_moyens:
            for p in scores_moyens[nom]:
                scores_moyens[nom][p] = round(scores_moyens[nom][p] / nb_simulations, 2)

        stats = {}
        for p in self.sondage_brut:
            vals = sorted(siege_counts[p])
            stats[p] = {
                "mediane": vals[nb_simulations // 2],
                "min": vals[int(nb_simulations * 0.05)],
                "max": vals[int(nb_simulations * 0.95)],
                "moyenne": round(sum(vals) / nb_simulations, 1)
            }

        return {
            "stats": stats,
            "details_comtes": gagnants_comte,
            "scores_moyens": scores_moyens,
            "toss_ups_pct": {k: round((v / nb_simulations) * 100, 1) for k, v in toss_ups_count.items()}
        }


def executer_les_vrais_chiffres():
    # Intentions brutes réelles (PQ 30%, PLQ 25%, PCQ 19%, CAQ 16%, QS 10%)
    sondage_test = {
        "PQ": 30.0,
        "PLQ": 25.0,
        "PCQ": 19.0,
        "CAQ": 16.0,
        "QS": 10.0
    }

    print("==========================================================================")
    print("   🏛️ LES VRAIS CHIFFRES : SIMULATION ÉLECTORALE SOUVERAINE v1.6 🗳️")
    print("==========================================================================")
    print(f"📊 Intentions : PQ {sondage_test['PQ']}% | PLQ {sondage_test['PLQ']}% | PCQ {sondage_test['PCQ']}% | CAQ {sondage_test['CAQ']}% | QS {sondage_test['QS']}%")
    print("⚡ Exécution de 10 000 simulations Monte Carlo (Zéro double comptabilisation)...")
    print("--------------------------------------------------------------------------")

    sim = SimulateurElectoralSouverainV16(sondage_test)
    res_qc = sim.simuler_mode_brut_qc125(nb_simulations=10000)
    res_v16 = sim.simuler_vrais_chiffres_v16(nb_simulations=10000)

    print("\n📋 PROJECTION COMPARATIVE DES 125 SIÈGES :\n")
    print(f"{'Parti':<10} | {'Mode Brut Qc125':<22} | {'Les Vrais Chiffres v1.6':<24} | {'Écart':<12}")
    print("-" * 75)

    for p in ["PQ", "PLQ", "PCQ", "CAQ", "QS"]:
        m_qc = res_qc["stats"][p]
        m_v16 = res_v16["stats"][p]
        str_qc = f"{m_qc['mediane']} sièges ({m_qc['min']}-{m_qc['max']})"
        str_v16 = f"{m_v16['mediane']} sièges ({m_v16['min']}-{m_v16['max']})"
        diff = m_v16['mediane'] - m_qc['mediane']
        signe = f"+{diff}" if diff > 0 else f"{diff}"
        print(f"{p:<10} | {str_qc:<22} | {str_v16:<24} | {signe:<12}")

    print("=" * 75)
    print("\n🔍 AUTOPSIE DES COMTÉS PIVOTS (PROBABILITÉS DE VICTOIRE EN %)")
    print("-" * 85)
    comtes_cles = [
        "Borduas", "Beauce-Sud", "Beauce-Nord", "Bellechasse", "Chauveau",
        "Granby", "Arthabaska", "Jean-Talon", "Rosemont", "Gouin", "Mercier",
        "Laurier-Dorion", "Sherbrooke", "Saint-Jérôme", "Montarville"
    ]
    print(f"{'Circonscription':<25} | {'Gagnant Qc125':<15} | {'Vainqueur v1.6':<18} | {'Probabilité':<15}")
    print("-" * 85)

    for nom in comtes_cles:
        g_qc = max(res_qc["details_comtes"][nom], key=res_qc["details_comtes"][nom].get)
        g_v16 = max(res_v16["details_comtes"][nom], key=res_v16["details_comtes"][nom].get)
        proba_v16 = res_v16["details_comtes"][nom][g_v16] / 100.0
        print(f"{nom:<25} | {g_qc:<15} | {g_v16:<18} | {proba_v16:<15.1f}%")

    print("==========================================================================")
    return res_v16


if __name__ == "__main__":
    executer_les_vrais_chiffres()
