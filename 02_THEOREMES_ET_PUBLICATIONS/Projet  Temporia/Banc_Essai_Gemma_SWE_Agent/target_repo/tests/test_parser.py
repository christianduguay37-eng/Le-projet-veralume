# -*- coding: utf-8 -*-
"""
Suite de tests Palier 5 : Défi extrême de parsing syntaxique et d'évaluation arithmétique.
"""

import unittest
from core.parser import ExpressionEvaluator


class TestExpressionEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = ExpressionEvaluator()

    def test_basic_arithmetic(self):
        """Vérifie l'addition, la soustraction, la multiplication et la division."""
        self.assertAlmostEqual(self.evaluator.evaluate("2 + 3 - 1"), 4.0)
        self.assertAlmostEqual(self.evaluator.evaluate("10 / 2 * 3"), 15.0)

    def test_operator_precedence(self):
        """Vérifie que la multiplication et division ont priorité sur addition et soustraction."""
        self.assertAlmostEqual(self.evaluator.evaluate("2 + 3 * 4"), 14.0)
        self.assertAlmostEqual(self.evaluator.evaluate("20 - 4 / 2"), 18.0)

    def test_parentheses(self):
        """Vérifie le respect des parenthèses simples et imbriquées."""
        self.assertAlmostEqual(self.evaluator.evaluate("(2 + 3) * 4"), 20.0)
        self.assertAlmostEqual(self.evaluator.evaluate("((1 + 2) * (3 + 4))"), 21.0)

    def test_power_and_right_associativity(self):
        """
        Vérifie la puissance mathématique (symbole ^) et son associativité stricte à droite.
        Ex: 2 ^ 3 ^ 2 doit être évalué comme 2 ^ (3 ^ 2) = 2 ^ 9 = 512, et NON (2 ^ 3) ^ 2 = 64.
        """
        self.assertAlmostEqual(self.evaluator.evaluate("2 ^ 3"), 8.0)
        self.assertAlmostEqual(self.evaluator.evaluate("2 ^ 3 ^ 2"), 512.0)
        self.assertAlmostEqual(self.evaluator.evaluate("3 * 2 ^ 3"), 24.0)

    def test_unary_negation(self):
        """Vérifie la négation unaire en début d'expression ou après un opérateur/parenthèse."""
        self.assertAlmostEqual(self.evaluator.evaluate("-5 + 3"), -2.0)
        self.assertAlmostEqual(self.evaluator.evaluate("-(2 + 3)"), -5.0)
        self.assertAlmostEqual(self.evaluator.evaluate("2 * -3"), -6.0)
        self.assertAlmostEqual(self.evaluator.evaluate("(-2) ^ 2"), 4.0)

    def test_floating_point(self):
        """Vérifie les nombres à virgule flottante."""
        self.assertAlmostEqual(self.evaluator.evaluate("3.5 * 2"), 7.0)
        self.assertAlmostEqual(self.evaluator.evaluate("1.5 + 2.5"), 4.0)

    def test_division_by_zero(self):
        """Vérifie la levée de ZeroDivisionError."""
        with self.assertRaises(ZeroDivisionError):
            self.evaluator.evaluate("10 / 0")

    def test_syntax_errors(self):
        """Vérifie la levée de ValueError pour parenthèses non fermées ou syntaxe invalide."""
        with self.assertRaises(ValueError):
            self.evaluator.evaluate("(2 + 3")
        with self.assertRaises(ValueError):
            self.evaluator.evaluate("2 + * 3")


if __name__ == "__main__":
    unittest.main()
