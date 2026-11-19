# -*- coding: utf-8 -*-
"""
Module de mutation dynamique de topologie réseau.
Gère l'ajout, le retrait et la modification d'éléments du graphe.
"""

from typing import Optional
from core.graph import DirectedGraph


class GraphMutator:
    """
    Opérateur de mutation sur le graphe de réseau.
    Permet de modifier dynamiquement les liens et les nœuds en cours d'exécution.
    """

    def __init__(self, graph: DirectedGraph):
        self.graph = graph

    def remove_node(self, node: str) -> bool:
        """
        Supprime un nœud du réseau ainsi que toutes ses arêtes incidentes et sortantes.
        """
        if node not in self.graph.nodes:
            return False

        # 1. Suppression du nœud dans l'ensemble des nœuds
        self.graph.nodes.remove(node)

        # 2. Suppression des arêtes sortantes
        if node in self.graph.adj:
            del self.graph.adj[node]

        # 3. Suppression des arêtes incidentes (vers ce nœud)
        for u in list(self.graph.adj.keys()):
            if node in self.graph.adj[u]:
                del self.graph.adj[u][node]

        return True

    def update_edge_weight(self, u: str, v: str, new_weight: float) -> bool:
        """
        Met à jour la pondération / latence d'une liaison réseau.
        """
        if u not in self.graph.adj or v not in self.graph.adj[u]:
            return False

        self.graph.adj[u][v] = float(new_weight)
        self.graph.invalidate_cache()
        return True
