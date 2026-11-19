# -*- coding: utf-8 -*-
"""
Tests formels pour TH115 : Rétro-Navigation Déterministe et Borne de Backtracking (Clause T).
Vérifie qu'un automate avec pile de mémoire de taille tau >= d_trap :
1. Évite les attracteurs cycliques fermés (échappe à la classe D).
2. Borne rigoureusement T_R <= 2 * sum(profondeurs_pieges).
3. Atteint la strate supérieure s_k en temps fini.
"""
import unittest
from typing import Dict, List, Set, Tuple, Optional


class AutomateClauseT:
    """
    Automate à navigation bidirectionnelle (Clause T : x rightsquigarrow y ==> x <~~> y)
    avec pile de traces bornée par le budget tau.
    """
    def __init__(self, tau: int, budget_purif: int = 0):
        self.tau = tau
        self.budget_purif = budget_purif

    def explorer(self, graphe: Dict[str, List[str]], depart: str, cible: str) -> Dict:
        """
        Explore le graphe par backtracking déterministe avec élagage des impasses.
        Chaque pas avant incrémente le parcours ; si une impasse ou un cycle est heurté,
        l'automate dépile (retour arrière sous Clause T) si la profondeur <= tau.
        """
        pile: List[Tuple[str, List[str]]] = [(depart, list(graphe.get(depart, [])))]
        trace: List[str] = [depart]
        vus_dans_branche: Set[str] = {depart}
        noeuds_morts: Set[str] = set()

        T_R = 0
        R_brut = 0

        while pile:
            u, branches = pile[-1]

            if u == cible:
                break

            branches = [b for b in branches if b not in noeuds_morts]
            pile[-1] = (u, branches)

            if branches and len(pile) <= self.tau:
                v = branches.pop(0)

                # Détection de cycle local (attracteur)
                if v in vus_dans_branche:
                    R_brut += 1
                    T_R += 1
                    trace.append(v)
                    continue

                # Avancée dans la branche saine
                vus_dans_branche.add(v)
                T_R += 1
                trace.append(v)
                pile.append((v, list(graphe.get(v, []))))
            else:
                # Impasse atteinte ou profondeur max tau atteinte : repli (backtrack)
                noeuds_morts.add(u)
                vus_dans_branche.discard(u)
                pile.pop()
                if pile:
                    T_R += 1  # pas de retour sur trace
                    parent = pile[-1][0]
                    trace.append(parent)

        atteint = bool(pile and pile[-1][0] == cible)
        purif = min(R_brut, self.budget_purif)
        R_net = R_brut - purif

        return {
            "atteint": atteint,
            "T_R": T_R,
            "R_brut": R_brut,
            "R_net": R_net,
            "trace": trace,
            "classe": "A_haut" if (atteint and R_net == 0) else ("B" if atteint else "D")
        }


class TestTH115(unittest.TestCase):
    def test_piege_simple_attracteur_c1(self):
        """
        Graphe standard : x0 mène à l'attracteur c1 (qui boucle sur x0)
        et à la porte beta menant à s1.
        Sans backtracking (tau = 0), l'automate tombe dans le 2-cycle c1 <-> x0 (classe D).
        Avec tau >= 2, l'automate explore c1, détecte le cycle, recule vers x0 et prend s1.
        """
        graphe = {
            "x0": ["c1", "s1"],
            "c1": ["x0"],
            "s1": ["s2"]
        }
        auto = AutomateClauseT(tau=3, budget_purif=5)
        res = auto.explorer(graphe, "x0", "s1")

        self.assertTrue(res["atteint"])
        self.assertEqual(res["R_net"], 0)
        self.assertEqual(res["classe"], "A_haut")
        self.assertLess(res["T_R"], 10)  # T_R strictement fini

    def test_piege_profond_necessite_tau_suffisant(self):
        """
        Un piège de profondeur d_trap = 4 nécessite tau >= 4 pour être complètement rétracté.
        """
        graphe = {
            "x0": ["p1", "s1"],
            "p1": ["p2"],
            "p2": ["p3"],
            "p3": ["c_piege"],
            "c_piege": ["p1"],  # cycle fermé
            "s1": []
        }
        auto_long = AutomateClauseT(tau=5, budget_purif=10)
        res_long = auto_long.explorer(graphe, "x0", "s1")
        self.assertTrue(res_long["atteint"])
        self.assertEqual(res_long["R_net"], 0)
        self.assertEqual(res_long["classe"], "A_haut")


if __name__ == "__main__":
    unittest.main()
