# -*- coding: utf-8 -*-
"""Tests de l'étage 5 (bibliothèque standard : python -m unittest alix.etage5.tests.test_etage5)."""
import unittest

from alix.etage5.noyau import Interpretation, derouler, classer
from alix.etage5.explorateur import explorer
from alix.etage5 import hades_pont


class TestNoyau(unittest.TestCase):
    def test_sature_pur_libere(self):
        t = derouler((0,) * 10, Interpretation())
        self.assertEqual(t.signature, (0, 0, 10))
        self.assertEqual(classer(t), "A")

    def test_secours_pur_periode_2(self):
        t = derouler((1,) * 10, Interpretation(n_lambda=None))
        self.assertEqual(t.periode_finale(), 2)
        self.assertEqual(classer(t), "D")

    def test_periode_2k(self):
        t = derouler((1,) * 14, Interpretation(n_lambda=None, nb_attracteurs=3))
        self.assertEqual(t.periode_finale(), 6)

    def test_B0_excursion_d_un_pas(self):
        t = derouler((0, 0, 1, 0, 0), Interpretation(n_lambda=3))
        self.assertEqual((t.T_R, t.R), (1, 0))
        self.assertEqual(classer(t), "B0")

    def test_loquet_borne_excursion(self):
        t = derouler((1,) * 12, Interpretation(n_lambda=3))
        self.assertTrue(all(len(run) <= 3 for run in "".join(
            "s" if p.regime == "secours" else "." for p in t.pas).split(".") if run))

    def test_univers_fini_repete(self):
        t = derouler((0,) * 8, Interpretation(n_lambda=None, taille_univers=3))
        self.assertGreater(t.R, 0)


class TestExplorateur(unittest.TestCase):
    def test_verdicts_stables(self):
        v = {x["th"]: x["verdict"] for x in explorer(6)}
        self.assertEqual(v["TH3"], "tient")
        self.assertEqual(v["TH9"], "tient")
        self.assertEqual(v["TH21"], "contre_exemple")
        self.assertEqual(v["TH41"], "contre_exemple")


class TestHades(unittest.TestCase):
    def test_B0_sat_et_TH9_unsat(self):
        self.assertTrue(hades_pont.chercher_B0(6, 2)["sat"])
        self.assertFalse(hades_pont.verifier_TH9(6, 2)["sat"])


if __name__ == "__main__":
    unittest.main()
