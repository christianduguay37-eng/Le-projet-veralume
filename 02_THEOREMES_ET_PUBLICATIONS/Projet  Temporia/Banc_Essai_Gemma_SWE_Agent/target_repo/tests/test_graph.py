# -*- coding: utf-8 -*-
import unittest
from core.graph import DirectedGraph, CycleDetectedException


class TestDirectedGraph(unittest.TestCase):

    def test_basic_dag(self):
        g = DirectedGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        res = g.topological_sort()
        self.assertEqual(res, ["A", "B", "C"])

    def test_isolated_nodes_in_topological_sort(self):
        g = DirectedGraph()
        g.add_edge("A", "B")
        g.nodes.add("ORPHAN_NODE") # Nœud enregistré dans le graphe sans arête
        res = g.topological_sort()
        self.assertEqual(len(res), 3)
        self.assertIn("ORPHAN_NODE", res)
        self.assertLess(res.index("A"), res.index("B"))

    def test_cycle_detection_raises_exception(self):
        g = DirectedGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "A") # Cycle A -> B -> C -> A
        with self.assertRaises(CycleDetectedException):
            g.topological_sort()


if __name__ == "__main__":
    unittest.main()
