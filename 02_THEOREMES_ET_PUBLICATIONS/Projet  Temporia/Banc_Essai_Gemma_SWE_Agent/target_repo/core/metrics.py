# -*- coding: utf-8 -*-
"""
Calcul de métriques sur graphes orientés.
"""

from .graph import DirectedGraph


class GraphMetrics:
    """Calculateur de densité et de connectivité."""

    @staticmethod
    def density(graph: DirectedGraph) -> float:
        n = len(graph.nodes)
        if n <= 1:
            return 0.0
        e = sum(len(neighbors) for neighbors in graph.adj.values())
        return e / (n * (n - 1))
