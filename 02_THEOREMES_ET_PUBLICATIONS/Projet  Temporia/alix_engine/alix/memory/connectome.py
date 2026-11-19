# -*- coding: utf-8 -*-
"""
===============================================================================
       🪢 LE CONNECTOME SYNAPTIQUE SOUVERAIN (GRAPHE DES CONNAISSANCES)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Graphe en mémoire vive pur, rapide et autonome (zéro Neo4j, zéro dépendance).
    - Cartographie des nœuds (concepts, notes, DOIs) et arêtes (liens wikilinks).
    - Navigation topologique et identification des nœuds orphelins.
===============================================================================
"""

from typing import Dict, Any, List, Set, Tuple, Optional

class SynapticConnectome:
    """Graphe relationnel léger des connaissances de l'exocerveau."""

    def __init__(self):
        self.noeuds: Dict[str, Dict[str, Any]] = {}
        self.adjacence: Dict[str, Set[str]] = {}
        self.ponts_trans_coffres: int = 0

    def ajouter_noeud(self, nom: str, coffre: str = "Cerveau Alix", tags: Optional[List[str]] = None) -> None:
        """Ajoute ou met à jour un nœud dans le connectome."""
        if nom not in self.noeuds:
            self.noeuds[nom] = {
                "coffre": coffre,
                "tags": tags or [],
                "degre_entrant": 0,
                "degre_sortant": 0
            }
            self.adjacence[nom] = set()

    def ajouter_lien(self, source: str, cible: str) -> None:
        """Ajoute une arête orientée entre deux concepts."""
        self.ajouter_noeud(source)
        self.ajouter_noeud(cible)

        if cible not in self.adjacence[source]:
            self.adjacence[source].add(cible)
            self.noeuds[source]["degre_sortant"] += 1
            self.noeuds[cible]["degre_entrant"] += 1

            if self.noeuds[source]["coffre"] != self.noeuds[cible]["coffre"]:
                self.ponts_trans_coffres += 1

    def voisins(self, noeud: str) -> List[str]:
        """Retourne la liste des voisins directs d'un nœud."""
        return list(self.adjacence.get(noeud, set()))

    def noeuds_orphelins(self) -> List[str]:
        """Identifie les concepts isolés n'ayant aucun lien entrant ni sortant."""
        orphelins = []
        for n, meta in self.noeuds.items():
            if meta["degre_entrant"] == 0 and meta["degre_sortant"] == 0:
                orphelins.append(n)
        return orphelins

    def densite_synaptique(self) -> float:
        """Calcule le ratio de connectivité du connectome."""
        n = len(self.noeuds)
        if n <= 1:
            return 1.0
        nb_liens = sum(len(v) for v in self.adjacence.values())
        max_liens = n * (n - 1)
        return round(nb_liens / max_liens, 4)

    def stats(self) -> Dict[str, Any]:
        """Retourne un bilan chiffré du connectome."""
        return {
            "total_noeuds": len(self.noeuds),
            "total_liens": sum(len(v) for v in self.adjacence.values()),
            "ponts_trans_coffres": self.ponts_trans_coffres,
            "orphelins": len(self.noeuds_orphelins()),
            "densite": self.densite_synaptique()
        }
