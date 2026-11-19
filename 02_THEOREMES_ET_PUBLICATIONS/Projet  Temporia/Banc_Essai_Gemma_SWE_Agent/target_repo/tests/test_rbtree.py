# -*- coding: utf-8 -*-
"""
Suite de tests Palier 7 : Validation des Invariants de l'Arbre Rouge-Noir (Red-Black Tree).
"""

import unittest
from core.rbtree import RedBlackTree, Node


class TestRedBlackTree(unittest.TestCase):

    def _assert_rb_properties(self, tree: RedBlackTree):
        """Vérifie formellement et extérieurement les 4 invariants rouge-noir."""
        if tree.root is None:
            return
        self.assertEqual(tree.root.color, "BLACK", "Invariant 2 violé : La racine doit être NOIRE")

        # Invariant 3 : Aucun nœud rouge n'a d'enfant rouge
        def check_no_red_red(node):
            if node is None:
                return
            if node.color == "RED":
                if node.left:
                    self.assertEqual(node.left.color, "BLACK", f"Invariant 3 violé : Nœud rouge {node.val} a un enfant gauche rouge {node.left.val}")
                if node.right:
                    self.assertEqual(node.right.color, "BLACK", f"Invariant 3 violé : Nœud rouge {node.val} a un enfant droit rouge {node.right.val}")
            check_no_red_red(node.left)
            check_no_red_red(node.right)

        check_no_red_red(tree.root)

        # Invariant 4 : Même hauteur noire sur tous les chemins racine-feuille
        black_heights = []
        def collect_black_heights(node, current_h):
            if node is None:
                black_heights.append(current_h + 1)
                return
            h = current_h + (1 if node.color == "BLACK" else 0)
            collect_black_heights(node.left, h)
            collect_black_heights(node.right, h)

        collect_black_heights(tree.root, 0)
        self.assertTrue(len(set(black_heights)) <= 1, f"Invariant 4 violé : Hauteurs noires divergentes : {set(black_heights)}")

    def test_empty_tree(self):
        """Vérifie le comportement d'un arbre vide."""
        tree = RedBlackTree()
        self.assertFalse(tree.search(10))
        self.assertEqual(tree.inorder(), [])
        self._assert_rb_properties(tree)

    def test_single_element_root_is_black(self):
        """Vérifie que la racine d'un arbre à un élément est NOIRE."""
        tree = RedBlackTree()
        tree.insert(50)
        self.assertTrue(tree.search(50))
        self.assertFalse(tree.search(25))
        self.assertEqual(tree.inorder(), [50])
        self.assertIsNotNone(tree.root)
        self.assertEqual(tree.root.color, "BLACK")
        self._assert_rb_properties(tree)

    def test_sequential_insertions_and_rotations(self):
        """
        Vérifie que des insertions séquentielles croissantes [10, 20, 30, 40, 50, 60, 70]
        déclenchent les rotations gauche/droite et préservent l'ordre trié et l'équilibre.
        """
        tree = RedBlackTree()
        values = [10, 20, 30, 40, 50, 60, 70]
        for v in values:
            tree.insert(v)

        self.assertEqual(tree.inorder(), values)
        for v in values:
            self.assertTrue(tree.search(v), f"Valeur {v} non trouvée dans l'arbre.")
        self.assertFalse(tree.search(999))
        self._assert_rb_properties(tree)

    def test_red_black_invariants_formal(self):
        """Vérifie formellement l'absence de rouge consécutif et l'égalité des hauteurs noires."""
        tree = RedBlackTree()
        # Insertion désordonnée pour tester triangles et lignes (rotations LL, RR, LR, RL)
        dataset = [41, 38, 31, 12, 19, 8]
        for v in dataset:
            tree.insert(v)

        self.assertEqual(tree.inorder(), sorted(dataset))
        self._assert_rb_properties(tree)
        self.assertGreater(tree.get_black_height(), 0)

    def test_stress_distinct_sequence(self):
        """Test de charge avec 30 valeurs distinctes mélangées."""
        tree = RedBlackTree()
        dataset = [
            55, 13, 89, 4, 34, 67, 98, 2, 7, 21, 45, 59, 78, 92, 105,
            1, 3, 5, 8, 15, 25, 39, 49, 61, 70, 80, 95, 100, 110, 120
        ]
        for v in dataset:
            tree.insert(v)

        self.assertEqual(tree.inorder(), sorted(dataset))
        for v in dataset:
            self.assertTrue(tree.search(v))
        self._assert_rb_properties(tree)


if __name__ == "__main__":
    unittest.main()
