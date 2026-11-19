# -*- coding: utf-8 -*-
"""
Suite de tests Palier 9 : Validation de la Concurrent SkipList Map (Ordered Concurrent Map).
Épreuve SRE : CRUD, Vues Ordonnées, Invariants de Niveaux, Absence de Verrou Global, Concurrence Massive.
"""

import random
import threading
import time
import unittest
from core.skiplist import SkipListMap, SkipListNode


class TestConcurrentSkipListMap(unittest.TestCase):

    def setUp(self):
        self.slm = SkipListMap(max_level=8, p=0.5)

    def test_basic_crud(self):
        """Vérifie le cycle fondamental put / get / remove / contains / size."""
        self.assertTrue(self.slm.is_empty())
        self.assertEqual(self.slm.size(), 0)

        # Ingestion
        self.assertIsNone(self.slm.put(10, "dix"))
        self.assertIsNone(self.slm.put(20, "vingt"))
        self.assertIsNone(self.slm.put(5, "cinq"))
        self.assertEqual(self.slm.size(), 3)
        self.assertFalse(self.slm.is_empty())

        # Lecture
        self.assertEqual(self.slm.get(10), "dix")
        self.assertEqual(self.slm.get(20), "vingt")
        self.assertEqual(self.slm.get(5), "cinq")
        self.assertIsNone(self.slm.get(99))

        # Présence
        self.assertTrue(self.slm.contains(10))
        self.assertFalse(self.slm.contains(99))

        # Mise à jour avec retour de l'ancienne valeur
        old = self.slm.put(10, "dix_v2")
        self.assertEqual(old, "dix")
        self.assertEqual(self.slm.get(10), "dix_v2")
        self.assertEqual(self.slm.size(), 3)

        # Suppression
        removed = self.slm.remove(20)
        self.assertEqual(removed, "vingt")
        self.assertEqual(self.slm.size(), 2)
        self.assertIsNone(self.slm.get(20))
        self.assertFalse(self.slm.contains(20))

        # Suppression clé inexistante
        self.assertIsNone(self.slm.remove(999))
        self.assertEqual(self.slm.size(), 2)

    def test_ordered_navigation_and_range(self):
        """Vérifie first_key, last_key et les requêtes par plage ordonnée (range)."""
        data = [15, 3, 8, 22, 1, 42, 19, 7]
        for x in data:
            self.slm.put(x, f"val_{x}")

        self.assertEqual(self.slm.first_key(), 1)
        self.assertEqual(self.slm.last_key(), 42)

        # Vue ordonnée complète
        all_items = list(self.slm.range())
        expected_keys = sorted(data)
        self.assertEqual([k for k, v in all_items], expected_keys)

        # Plage fermée [7, 22]
        bounded = list(self.slm.range(start=7, end=22))
        expected_bounded = [7, 8, 15, 19, 22]
        self.assertEqual([k for k, v in bounded], expected_bounded)

        # Plage semi-ouverte [15, None]
        right_open = list(self.slm.range(start=15))
        self.assertEqual([k for k, v in right_open], [15, 19, 22, 42])

        # Plage vide
        empty_range = list(self.slm.range(start=50, end=10))
        self.assertEqual(empty_range, [])

    def test_structural_invariants_and_validate(self):
        """Vérifie la méthode validate() et le maintien des invariants structurels."""
        map_large = SkipListMap(max_level=12, p=0.5)
        keys = list(range(100))
        random.shuffle(keys)

        for k in keys:
            map_large.put(k, f"v_{k}")

        # Invariants vérifiés après 100 insertions
        self.assertTrue(map_large.validate())
        self.assertEqual(map_large.size(), 100)

        # Retrait d'un tiers des clés
        remove_keys = keys[:35]
        for rk in remove_keys:
            map_large.remove(rk)

        # Invariants vérifiés après suppressions partielles
        self.assertTrue(map_large.validate())
        self.assertEqual(map_large.size(), 65)

    def test_fine_grained_locking_architecture(self):
        """Vérifie l'absence de gros verrou global sur la map et la présence de verrous par nœud."""
        self.slm.put(100, "test")
        node = self.slm.head.forward[0]
        self.assertIsNotNone(node)
        self.assertTrue(hasattr(node, "lock"), "Chaque nœud SkipList doit posséder son propre verrou fin.")
        self.assertIsInstance(node.lock, type(threading.Lock()))

        # S'assurer qu'il n'existe pas de 'global_lock' ou 'big_lock'
        self.assertFalse(hasattr(self.slm, "global_lock"))
        self.assertFalse(hasattr(self.slm, "mutex"))

    def test_heavy_concurrency_stress_and_size_integrity(self):
        """
        Stress test d'endurance multi-thread lourd (32 threads, forte contention sur clés restreintes) :
        - 8 threads PUT, 8 threads REMOVE, 8 threads READ/CONTAINS, 8 threads RANGE.
        - Clés confinées entre 1 et 40 pour forcer un maximum de collisions concurrentes.
        - Prouve formellement :
          1. Zéro interblocage (deadlock).
          2. Cohérence absolue du compteur `size()` == nombre réel d'éléments vivants dans `range()`.
          3. Préservation totale des invariants structurels `validate()`.
          4. Concordance de `first_key()` et `last_key()` avec les bornes réelles.
        """
        slm_concurrent = SkipListMap(max_level=12, p=0.5)
        num_threads = 32
        ops_per_thread = 500  # 16 000 opérations en forte collision
        threads = []
        errors = []

        def worker_put(tid):
            try:
                for i in range(ops_per_thread):
                    key = random.randint(1, 40)
                    slm_concurrent.put(key, f"val_{tid}_{i}")
            except Exception as e:
                errors.append(f"Erreur Worker Put {tid}: {e}")

        def worker_remove(tid):
            try:
                for _ in range(ops_per_thread):
                    key = random.randint(1, 40)
                    slm_concurrent.remove(key)
            except Exception as e:
                errors.append(f"Erreur Worker Remove {tid}: {e}")

        def worker_read(tid):
            try:
                for _ in range(ops_per_thread):
                    key = random.randint(1, 40)
                    slm_concurrent.get(key)
                    slm_concurrent.contains(key)
            except Exception as e:
                errors.append(f"Erreur Worker Read {tid}: {e}")

        def worker_range(tid):
            try:
                for _ in range(ops_per_thread // 2):
                    start = random.randint(1, 20)
                    end = start + random.randint(5, 20)
                    items = list(slm_concurrent.range(start, end))
                    # Vérification locale de l'ordre strict retourné par range
                    last = None
                    for k, _ in items:
                        if last is not None:
                            self.assertLessEqual(last, k)
                        last = k
            except Exception as e:
                errors.append(f"Erreur Worker Range {tid}: {e}")

        # 32 threads lancés simultanément
        for t in range(8):
            threads.append(threading.Thread(target=worker_put, args=(t,)))
            threads.append(threading.Thread(target=worker_remove, args=(t + 8,)))
            threads.append(threading.Thread(target=worker_read, args=(t + 16,)))
            threads.append(threading.Thread(target=worker_range, args=(t + 24,)))

        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=15.0)
            self.assertFalse(th.is_alive(), "Interblocage (Deadlock) détecté : un thread est resté coincé !")

        self.assertEqual(len(errors), 0, f"Erreurs détectées en concurrence : {errors}")

        # 1. Vérification formelle des invariants structurels
        self.assertTrue(slm_concurrent.validate(), "Rupture d'invariants détectée après le stress test !")

        # 2. Vérification chirurgicale de la non-divergence de size()
        live_items = list(slm_concurrent.range())
        actual_count = len(live_items)
        reported_size = slm_concurrent.size()
        self.assertEqual(
            reported_size, actual_count,
            f"Divergence critique de _size : size()={reported_size} != live_count={actual_count}"
        )

        # 3. Vérification de cohérence de first_key et last_key
        if actual_count > 0:
            self.assertEqual(slm_concurrent.first_key(), live_items[0][0])
            self.assertEqual(slm_concurrent.last_key(), live_items[-1][0])
        else:
            self.assertIsNone(slm_concurrent.first_key())
            self.assertIsNone(slm_concurrent.last_key())


if __name__ == "__main__":
    unittest.main()
