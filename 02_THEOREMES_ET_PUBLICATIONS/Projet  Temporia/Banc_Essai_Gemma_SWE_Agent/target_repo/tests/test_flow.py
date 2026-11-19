# -*- coding: utf-8 -*-
"""
Suite de tests Palier 3 : Conservation de flux réseau & Lois de Kirchhoff.
"""

import unittest
from core.graph import DirectedGraph
from core.flow import NetworkFlowOptimizer, FlowConservationException


class TestNetworkFlow(unittest.TestCase):

    def setUp(self):
        self.g = DirectedGraph()
        # Pipeline séquentiel : Source -> R1 -> R2 -> Sink (capacité 10.0 chacune)
        self.g.add_edge("Source", "R1", weight=10.0)
        self.g.add_edge("R1", "R2", weight=10.0)
        self.g.add_edge("R2", "Sink", weight=10.0)
        self.flow_opt = NetworkFlowOptimizer(self.g)

    def test_flow_conservation_along_path(self):
        """
        Vérifie qu'un acheminement de 5.0 unités respecte la conservation
        sur R1 et R2 (flux entrant == flux sortant = 5.0).
        """
        allocated = self.flow_opt.route_demand("Source", "Sink", 5.0)
        self.assertEqual(allocated, 5.0)

        # Vérification sur R1
        self.assertEqual(self.flow_opt.get_node_inflow("R1"), 5.0)
        self.assertEqual(self.flow_opt.get_node_outflow("R1"), 5.0)

        # Vérification sur R2
        self.assertEqual(self.flow_opt.get_node_inflow("R2"), 5.0)
        self.assertEqual(self.flow_opt.get_node_outflow("R2"), 5.0)

        # Conservation globale
        self.assertTrue(self.flow_opt.verify_conservation("Source", "Sink"))


if __name__ == "__main__":
    unittest.main()
