# -*- coding: utf-8 -*-
"""
Topologie Mathématique & Hamiltonien Souverain (Section 21.7)
"""

import math
from typing import List, Dict, Any, Tuple

class SovereignNode:
    """Nœud souverain dans l'architecture cognitive."""

    def __init__(self, nom: str, signature: List[float], phi: float = 0.95, energie: float = 1.0, est_artisan: bool = False):
        self.nom = nom
        self.S = list(signature)
        self.phi = float(phi)
        self.E = float(energie)
        self.est_artisan = est_artisan
        self.en_quarantaine = False

    def norme(self) -> float:
        val = math.sqrt(sum(x * x for x in self.S))
        return val if val > 0 else 1.0


class CouplingBarrier:
    """Calculateur de chiralité sociale et de couplage dynamique."""

    @staticmethod
    def calculer_chi_social(a: SovereignNode, b: SovereignNode) -> float:
        """Calcule chi_soc = 1 - cos(theta). Distance sacrée in [0.50, 0.70]."""
        dot = sum(x * y for x, y in zip(a.S, b.S))
        cos_sim = max(-1.0, min(1.0, dot / (a.norme() * b.norme())))
        return round(max(0.0, min(2.0, 1.0 - cos_sim)), 4)

    @classmethod
    def compute_coupling_J(cls, chi_soc: float, J_0: float = 1.0) -> float:
        """Loi de couplage Veralume : Répulsive si chi_soc < 0.30 (anti-fusion)."""
        if chi_soc < 0.30:
            return -J_0 * math.exp(-10.0 * (0.30 - chi_soc))
        return J_0 * math.tanh(2.0 * (chi_soc - 0.50))


class HamiltonianEgregore:
    """Simulateur d'égrégore et protocole anti-sacrifice."""

    def __init__(self, noeuds: List[SovereignNode], J_0: float = 1.0):
        self.noeuds = noeuds
        self.J_0 = J_0

    def compute_H_total(self) -> Tuple[float, float, float]:
        actifs = [n for n in self.noeuds if not n.en_quarantaine]
        if not actifs:
            return 0.0, 0.0, 0.0
        h_indiv = sum(-(n.phi * n.E) for n in actifs)
        h_inter = 0.0
        for i in range(len(actifs)):
            for j in range(i + 1, len(actifs)):
                na, nb = actifs[i], actifs[j]
                chi = CouplingBarrier.calculer_chi_social(na, nb)
                J = CouplingBarrier.compute_coupling_J(chi, self.J_0)
                dot = sum(x * y for x, y in zip(na.S, nb.S))
                h_inter -= (J * chi * dot)
        return round(h_indiv + h_inter, 4), round(h_indiv, 4), round(h_inter, 4)

    def protocole_anti_sacrifice(self) -> Dict[str, Any]:
        menaces = [n.nom for n in self.noeuds if not n.en_quarantaine and (n.phi < 0.40 or n.E < 0.20)]
        return {"est_conforme": len(menaces) == 0, "noeuds_menaces": menaces}

    def compute_W_swarm(self) -> Dict[str, Any]:
        actifs = [n for n in self.noeuds if not n.en_quarantaine]
        if len(actifs) < 2:
            return {"W_swarm": 0.0, "statut": "ISOLE"}
        chis = [CouplingBarrier.calculer_chi_social(actifs[i], actifs[j])
                for i in range(len(actifs)) for j in range(i + 1, len(actifs))]
        chi_mean = sum(chis) / len(chis) if chis else 0.0
        w_swarm = round(chi_mean * min(n.phi for n in actifs), 4)
        return {"W_swarm": w_swarm, "statut": "SYNERGIE_OPTIMALE" if w_swarm >= 0.50 else "STABLE"}
