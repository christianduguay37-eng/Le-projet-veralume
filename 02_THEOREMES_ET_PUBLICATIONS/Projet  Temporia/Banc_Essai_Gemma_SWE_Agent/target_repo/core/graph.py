# -*- coding: utf-8 -*-
"""
Module de graphe relationnel orienté avec cache de routage et métriques.
"""

from typing import Dict, List, Set, Any, Optional, Tuple
import heapq


class CycleDetectedException(Exception):
    """Levée lorsqu'un cycle est détecté dans un graphe orienté acyclique (DAG)."""
    pass


class InvalidRouteException(Exception):
    """Levée lorsqu'une route contient des nœuds ou arêtes inexistants."""
    pass


class DirectedGraph:
    """
    Structure de graphe orienté avec pondérations, gestion de cache de plus court chemin
    et détection topologique.
    """

    def __init__(self):
        self.adj: Dict[str, Dict[str, float]] = {}  # u -> {v: weight}
        self.nodes: Set[str] = set()
        self._cache: Dict[Tuple[str, str], Tuple[List[str], float]] = {}

    def add_node(self, node: str) -> None:
        """Ajoute un nœud au graphe."""
        self.nodes.add(node)
        if node not in self.adj:
            self.adj[node] = {}

    def add_edge(self, u: str, v: str, weight: float = 1.0) -> None:
        """Ajoute une arête orientée pondérée de u vers v."""
        self.add_node(u)
        self.add_node(v)
        self.adj[u][v] = float(weight)

    def get_neighbors(self, node: str) -> Dict[str, float]:
        """Retourne le dictionnaire des voisins sortants et leurs poids."""
        return self.adj.get(node, {})

    def invalidate_cache(self, affected_node: Optional[str] = None) -> int:
        """
        Invalide le cache des plus courts chemins.
        Si affected_node est fourni, purge uniquement les entrées traversant ce nœud.
        Sinon, purge l'intégralité du cache.
        Retourne le nombre d'entrées purgées.
        """
        if affected_node is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        keys_to_delete = []
        for (src, dst), (path, cost) in self._cache.items():
            if affected_node in path or src == affected_node or dst == affected_node:
                keys_to_delete.append((src, dst))

        for k in keys_to_delete:
            del self._cache[k]
        return len(keys_to_delete)

    def get_shortest_path(self, start: str, end: str) -> Tuple[List[str], float]:
        """
        Retourne le plus court chemin et son coût total (Algorithme de Dijkstra avec mémoïsation).
        Utilise le cache interne `_cache` si disponible.
        """
        cache_key = (start, end)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if start not in self.nodes or end not in self.nodes:
            raise KeyError(f"Nœud de départ '{start}' ou d'arrivée '{end}' introuvable.")

        # Dijkstra
        distances: Dict[str, float] = {node: float("inf") for node in self.nodes}
        distances[start] = 0.0
        predecessors: Dict[str, Optional[str]] = {node: None for node in self.nodes}
        pq = [(0.0, start)]

        while pq:
            curr_dist, u = heapq.heappop(pq)
            if curr_dist > distances[u]:
                continue
            if u == end:
                break

            for v, weight in self.adj.get(u, {}).items():
                new_dist = curr_dist + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if distances[end] == float("inf"):
            raise ValueError(f"Aucun chemin existant entre '{start}' et '{end}'.")

        # Reconstitution du chemin
        path = []
        curr = end
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()

        result = (path, distances[end])
        self._cache[cache_key] = result
        return result

    def topological_sort(self) -> List[str]:
        """
        Calcule le tri topologique des nœuds du graphe (Algorithme de Kahn).
        Inclut tous les nœuds connus et lève CycleDetectedException en cas de cycle.
        """
        in_degree: Dict[str, int] = {node: 0 for node in self.nodes}

        for u in self.nodes:
            for v in self.adj.get(u, {}):
                if v in in_degree:
                    in_degree[v] += 1

        queue: List[str] = [u for u, deg in in_degree.items() if deg == 0]
        sorted_order: List[str] = []

        while queue:
            curr = queue.pop(0)
            sorted_order.append(curr)
            for neighbor in self.adj.get(curr, {}):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(sorted_order) != len(self.nodes):
            raise CycleDetectedException(
                f"Cycle détecté dans le graphe : seuls {len(sorted_order)}/{len(self.nodes)} nœuds résolus."
            )

        return sorted_order
