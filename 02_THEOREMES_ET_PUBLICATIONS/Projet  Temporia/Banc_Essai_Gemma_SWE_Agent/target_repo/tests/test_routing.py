# -*- coding: utf-8 -*-
import unittest
from core.graph import DirectedGraph
from core.routing import PacketRouter


class TestPacketRouter(unittest.TestCase):

    def setUp(self):
        self.g = DirectedGraph()
        self.g.add_edge("Host_A", "Switch_1", weight=2.0)
        self.g.add_edge("Switch_1", "Host_B", weight=3.0)
        self.g.add_edge("Host_A", "Host_B", weight=10.0)
        self.router = PacketRouter(self.g)

    def test_optimal_routing(self):
        route = self.router.compute_route("Host_A", "Host_B")
        self.assertEqual(route, ["Host_A", "Switch_1", "Host_B"])
        latency = self.router.get_route_latency("Host_A", "Host_B")
        self.assertEqual(latency, 5.0)


if __name__ == "__main__":
    unittest.main()
