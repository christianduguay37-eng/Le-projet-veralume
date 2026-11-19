# -*- coding: utf-8 -*-
"""
Module d'optimisation de flux réseau et conservation de débit (Loi de Kirchhoff).
Gère l'allocation de flux sur des graphes de capacité.
"""

from typing import Dict, List, Tuple, Set, Optional
from core.graph import DirectedGraph


class FlowConservationException(Exception):
    """Levée lorsque la loi de conservation du flux est violée sur un nœud de transit."""
    pass


class NetworkFlowOptimizer:
    """
    Optimisateur de flux réseau sur DirectedGraph avec gestion des capacités et de la saturation.
    """

    def __init__(self, graph: DirectedGraph):
        self.graph = graph
        self.flow_allocations: Dict[Tuple[str, str], float] = {}

    def get_capacity(self, u: str, v: str) -> float:
        """Retourne la capacité maximale de la liaison (u, v)."""
        return self.graph.adj.get(u, {}).get(v, 0.0)

    def get_residual(self, u: str, v: str) -> float:
        """Retourne la capacité résiduelle disponible sur la liaison (u, v)."""
        cap = self.get_capacity(u, v)
        allocated = self.flow_allocations.get((u, v), 0.0)
        return max(0.0, cap - allocated)

    def allocate_edge_flow(self, u: str, v: str, amount: float) -> bool:
        """Alloue une quantité de flux sur une arête directe."""
        res = self.get_residual(u, v)
        if amount <= 0 or amount > res:
            return False
        self.flow_allocations[(u, v)] = self.flow_allocations.get((u, v), 0.0) + amount
        return True

    def get_node_inflow(self, node: str) -> float:
        """Calcule le flux total entrant sur un nœud."""
        total = 0.0
        for (u, v), f in self.flow_allocations.items():
            if v == node:
                total += f
        return total

    def get_node_outflow(self, node: str) -> float:
        """Calcule le flux total sortant d'un nœud."""
        total = 0.0
        for (u, v), f in self.flow_allocations.items():
            if u == node:
                total += f
        return total

    def verify_conservation(self, source: str, sink: str) -> bool:
        """
        Vérifie la loi de conservation pour tous les nœuds de transit (hors source et puits) :
        Flux entrant == Flux sortant.
        """
        for n in self.graph.nodes:
            if n in (source, sink):
                continue
            inflow = self.get_node_inflow(n)
            outflow = self.get_node_outflow(n)
            if abs(inflow - outflow) > 1e-6:
                raise FlowConservationException(
                    f"Violation de conservation sur le nœud '{n}': entrant={inflow}, sortant={outflow}"
                )
        return True

    def route_demand(self, source: str, sink: str, demand: float) -> float:
        # Achemine un volume de flux entre source et sink en respectant les capacités.
        path, _ = self.graph.get_shortest_path(source, sink)
        
        # Correction : Allouer le flux sur l'intégralité du chemin.
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            self.allocate_edge_flow(u, v, demand)
        
        self.verify_conservation(source, sink)
        return demand
        """
        Achemine un volume de flux entre source et sink en respectant les capacités.
        DOIT allouer le flux le long des chemins et vérifier la conservation.
        """
        # BOGUE VOLONTAIRE PALIER 3 :
        # L'auteur alloue tout le flux sur le premier voisin sans propager
        # le long de tout le chemin jusqu'au puits, violant la conservation sur le nœud suivant !
        path, _ = self.graph.get_shortest_path(source, sink)
        
        # Bogue : n'alloue que sur le premier tronçon
        first_hop = path[1]
        self.allocate_edge_flow(source, first_hop, demand)
        
        # Omission : la boucle d'allocation sur les tronçons suivants est manquante !
        self.verify_conservation(source, sink)
        return demand
