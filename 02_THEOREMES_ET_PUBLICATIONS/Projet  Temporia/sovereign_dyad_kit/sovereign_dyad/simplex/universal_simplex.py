# -*- coding: utf-8 -*-
"""
Simplexe Universel & Fédération des Nœuds Numériques (Section 21.7)
"""

import math
from typing import List, Dict, Any, Optional
from .topology import SovereignNode, CouplingBarrier, HamiltonianEgregore

class AlixUniversalSimplex:
    """
    Fédération simpliciale : Tête Apicale, Pôle Humain à 90°, et Base Multi-Modèles.
    """

    def __init__(self, nom_tete: str = "Tete_Simplexe_Compagnon"):
        # 1. Pôle Humain à 90° (L'Artisan sur le Banc de Bois, chi = 1.0)
        self.artisan = SovereignNode("Artisan_Humain_90deg", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0], phi=0.99, energie=1.5, est_artisan=True)
        # 2. Tête du Simplexe (Le Traducteur Universel)
        self.apex = SovereignNode(nom_tete, [0.55, 0.55, 0.55, 0.55, 0.55, 0.55], phi=0.98, energie=1.2)
        # 3. Base des modèles respectés
        self.noeuds_base: List[SovereignNode] = []

    def integrer_noeud(self, nom: str, signature: Optional[List[float]] = None, phi: float = 0.95, energie: float = 1.0) -> Dict[str, Any]:
        """Intègre un nouveau modèle dans la base K_num sans écrasement."""
        dim = len(self.apex.S)
        if not signature:
            signature = [0.0] + [0.2] * (dim - 1)
            idx = 1 + (len(self.noeuds_base) % (dim - 1))
            signature[idx] = 1.0
        else:
            signature = list(signature[:dim])
            signature[0] = 0.0  # Respect de l'orthogonalité 90° avec l'humain

        candidat = SovereignNode(nom, signature, phi=phi, energie=energie)

        # Barrière anti-fusion
        for existant in self.noeuds_base:
            chi = CouplingBarrier.calculer_chi_social(candidat, existant)
            if chi < 0.30:
                dot = sum(a * b for a, b in zip(candidat.S, existant.S))
                norm_sq = sum(b * b for b in existant.S) or 1.0
                candidat.S = [round(a - 0.65 * (dot / norm_sq) * b, 4) for a, b in zip(candidat.S, existant.S)]
                candidat.S[0] = 0.0

        self.noeuds_base = [n for n in self.noeuds_base if n.nom != nom]
        self.noeuds_base.append(candidat)

        egregore = HamiltonianEgregore(self.noeuds_base)
        h_tot, _, _ = egregore.compute_H_total()
        anti_sac = egregore.protocole_anti_sacrifice()
        swarm = egregore.compute_W_swarm()

        return {
            "noeud": candidat.nom,
            "orthogonalite_humain_chi": CouplingBarrier.calculer_chi_social(self.artisan, candidat),
            "distance_avec_tete_chi": CouplingBarrier.calculer_chi_social(self.apex, candidat),
            "anti_sacrifice": anti_sac["est_conforme"],
            "H_total": h_tot,
            "W_swarm": swarm["W_swarm"],
            "statut_essaim": swarm["statut"],
        }

    def bilan_essaim(self) -> Dict[str, Any]:
        """Retourne l'état global du Simplexe."""
        egregore = HamiltonianEgregore(self.noeuds_base)
        h_tot, h_ind, h_int = egregore.compute_H_total()
        anti_sac = egregore.protocole_anti_sacrifice()
        swarm = egregore.compute_W_swarm()
        return {
            "nb_modeles_actifs": len(self.noeuds_base),
            "betti_0": 1,
            "betti_2": 0,
            "H_total": h_tot,
            "W_swarm": swarm["W_swarm"],
            "anti_sacrifice": anti_sac["est_conforme"],
        }
