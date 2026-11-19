# -*- coding: utf-8 -*-
"""
Module de routage de paquets et calcul de métriques réseau.
"""

from typing import List, Tuple
from core.graph import DirectedGraph, InvalidRouteException


class PacketRouter:
    """
    Gestionnaire de routage réseau exploitant le graphe orienté.
    """

    def __init__(self, graph: DirectedGraph):
        self.graph = graph

    def compute_route(self, source: str, destination: str) -> List[str]:
        """
        Calcule la route optimale et valide sa cohérence matérielle.
        Lève InvalidRouteException si un nœud sur le chemin n'existe plus.
        """
        path, _ = self.graph.get_shortest_path(source, destination)
        self.validate_route(path)
        return path

    def get_route_latency(self, source: str, destination: str) -> float:
        """Retourne la latence totale cumulée le long du chemin optimal."""
        _, cost = self.graph.get_shortest_path(source, destination)
        return cost

    def validate_route(self, route: List[str]) -> bool:
        """
        Vérifie qu'aucun nœud ou lien fantôme n'apparaît dans la route calculée.
        """
        if not route:
            raise InvalidRouteException("Route vide.")

        for node in route:
            if node not in self.graph.nodes:
                raise InvalidRouteException(
                    f"Route invalide : le nœud '{node}' n'existe pas ou a été décommissionné."
                )

        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if v not in self.graph.adj.get(u, {}):
                raise InvalidRouteException(
                    f"Route invalide : la liaison de '{u}' vers '{v}' n'existe pas."
                )

        return True
