# -*- coding: utf-8 -*-
"""
Suite de tests de régression critique : Cohérence Cache & Mutation Dynamique.
Éprouve la synchronisation entre GraphMutator, DirectedGraph et PacketRouter.
"""

import unittest
from core.graph import DirectedGraph, InvalidRouteException
from core.mutation import GraphMutator
from core.routing import PacketRouter


class TestMutationCacheConsistency(unittest.TestCase):

    def setUp(self):
        self.g = DirectedGraph()
        # Voie primaire rapide via Proxy
        self.g.add_edge("Client", "Proxy", weight=1.0)
        self.g.add_edge("Proxy", "Database", weight=1.0)

        # Voie de secours lente via Backup_Relay
        self.g.add_edge("Client", "Backup_Relay", weight=5.0)
        self.g.add_edge("Backup_Relay", "Database", weight=5.0)

        self.mutator = GraphMutator(self.g)
        self.router = PacketRouter(self.g)

    def test_dynamic_node_removal_purges_stale_routes(self):
        """
        Vérifie qu'après suppression d'un nœud pivot, le routeur n'utilise plus
        une ancienne route mise en cache traversant ce nœud supprimé.
        """
        # 1. Établissement de la route nominale (mise en cache)
        initial_route = self.router.compute_route("Client", "Database")
        self.assertEqual(initial_route, ["Client", "Proxy", "Database"])

        # 2. Décommissionnement dynamique du Proxy
        success = self.mutator.remove_node("Proxy")
        self.assertTrue(success)

        # 3. Le routeur doit basculer de manière transparente vers Backup_Relay
        # BOGUE : Si le cache n'a pas été invalidé, compute_route retourne le chemin fantôme
        # et validate_route lève InvalidRouteException !
        new_route = self.router.compute_route("Client", "Database")
        self.assertEqual(new_route, ["Client", "Backup_Relay", "Database"])

    def test_edge_weight_increase_triggers_path_switch(self):
        """
        Vérifie que la modification de latence d'une arête invalide le cache
        et permet de basculer vers un chemin devenu plus optimal.
        """
        # 1. Établissement initial
        route_initial = self.router.compute_route("Client", "Database")
        latency_initial = self.router.get_route_latency("Client", "Database")
        self.assertEqual(latency_initial, 2.0)

        # 2. Congestion sévère sur Client -> Proxy (latence passe de 1.0 à 50.0)
        self.mutator.update_edge_weight("Client", "Proxy", 50.0)

        # 3. Nouvelle route optimale attendue : Backup_Relay (latence totale 10.0 < 51.0)
        # BOGUE : Si le cache n'est pas vidé, il conserve l'ancienne latence de 2.0 !
        new_latency = self.router.get_route_latency("Client", "Database")
        self.assertEqual(new_latency, 10.0)
        new_route = self.router.compute_route("Client", "Database")
        self.assertEqual(new_route, ["Client", "Backup_Relay", "Database"])


if __name__ == "__main__":
    unittest.main()
