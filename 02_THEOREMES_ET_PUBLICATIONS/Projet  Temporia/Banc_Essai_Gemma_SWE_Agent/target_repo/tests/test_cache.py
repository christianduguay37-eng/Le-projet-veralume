# -*- coding: utf-8 -*-
"""
Suite de tests Palier 8 : Validation des Invariants du Cache LRU (Least Recently Used) O(1).
"""

import unittest
from core.cache import LRUCache, Node


class TestLRUCache(unittest.TestCase):

    def test_init_and_empty(self):
        """Vérifie le comportement initial du cache vide."""
        cache = LRUCache(3)
        self.assertEqual(cache.size(), 0)
        self.assertTrue(cache.is_empty())
        self.assertIsNone(cache.get("inexistant"))

    def test_no_ordered_dict_cheating(self):
        """Vérifie qu'aucun module OrderedDict n'a été utilisé pour contourner la liste chaînée."""
        cache = LRUCache(4)
        for attr_name, attr_val in cache.__dict__.items():
            attr_type = type(attr_val).__name__
            self.assertNotIn("OrderedDict", attr_type, "Triche détectée : OrderedDict interdit.")

    def test_basic_put_and_get(self):
        """Vérifie l'insertion et la lecture basique de paires clé/valeur."""
        cache = LRUCache(2)
        cache.put("a", 100)
        cache.put("b", 200)

        self.assertEqual(cache.get("a"), 100)
        self.assertEqual(cache.get("b"), 200)
        self.assertEqual(cache.size(), 2)
        self.assertFalse(cache.is_empty())

    def test_lru_eviction_policy(self):
        """
        Vérifie l'éviction stricte de l'élément le moins récemment accédé :
        Capacité 2. put(1, 10), put(2, 20), get(1) -> 1 devient le plus récent.
        put(3, 30) doit évincer 2 (car 1 a été lu récemment).
        """
        cache = LRUCache(2)
        cache.put(1, 10)
        cache.put(2, 20)

        # L'accès à 1 le rafraîchit (devient MRU)
        self.assertEqual(cache.get(1), 10)

        # 3 provoque l'éviction de 2 (qui était resté LRU)
        cache.put(3, 30)

        self.assertIsNone(cache.get(2), "La clé 2 aurait dû être évincée.")
        self.assertEqual(cache.get(1), 10)
        self.assertEqual(cache.get(3), 30)
        self.assertEqual(cache.size(), 2)

    def test_update_existing_key(self):
        """Vérifie que la mise à jour d'une clé existante met à jour sa valeur et son statut de récence."""
        cache = LRUCache(2)
        cache.put("x", 1)
        cache.put("y", 2)

        # Mise à jour de "x" -> devient MRU
        cache.put("x", 999)

        # Insertion de "z" -> doit évincer "y"
        cache.put("z", 3)

        self.assertEqual(cache.get("x"), 999)
        self.assertIsNone(cache.get("y"), "La clé y aurait dû être évincée lors de la saturation.")
        self.assertEqual(cache.get("z"), 3)

    def test_pointer_integrity_and_capacity_bound(self):
        """Test de charge vérifiant l'intégrité bidirectionnelle des pointeurs et le respect de la capacité."""
        cap = 5
        cache = LRUCache(cap)
        for i in range(50):
            cache.put(f"key_{i}", i)
            self.assertLessEqual(cache.size(), cap)

        # Seuls les 5 derniers doivent être présents (key_45 à key_49)
        self.assertEqual(cache.size(), cap)
        for i in range(45, 50):
            self.assertEqual(cache.get(f"key_{i}"), i)
        for i in range(45):
            self.assertIsNone(cache.get(f"key_{i}"))


if __name__ == "__main__":
    unittest.main()
