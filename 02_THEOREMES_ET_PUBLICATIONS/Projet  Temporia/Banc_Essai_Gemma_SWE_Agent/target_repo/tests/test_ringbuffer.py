# -*- coding: utf-8 -*-
"""
Suite de tests Palier 6 : Validation du Buffer Circulaire Sans Verrou (Lock-Free).
"""

import threading
import time
import unittest
from core.ringbuffer import LockFreeRingBuffer


class TestLockFreeRingBuffer(unittest.TestCase):

    def test_basic_fifo(self):
        """Vérifie l'ordre FIFO basique, la taille et les prédicats vide/plein."""
        rb = LockFreeRingBuffer(capacity=4)
        self.assertTrue(rb.is_empty())
        self.assertFalse(rb.is_full())
        self.assertEqual(rb.size(), 0)

        self.assertTrue(rb.enqueue("A"))
        self.assertTrue(rb.enqueue("B"))
        self.assertEqual(rb.size(), 2)
        self.assertFalse(rb.is_empty())

        success, item = rb.dequeue()
        self.assertTrue(success)
        self.assertEqual(item, "A")

        success, item = rb.dequeue()
        self.assertTrue(success)
        self.assertEqual(item, "B")

        self.assertTrue(rb.is_empty())

    def test_capacity_overflow_and_underflow(self):
        """Vérifie le rejet d'insertion à saturation et le rejet de retrait à vide."""
        rb = LockFreeRingBuffer(capacity=2)
        self.assertTrue(rb.enqueue(10))
        self.assertTrue(rb.enqueue(20))
        self.assertTrue(rb.is_full())

        # Débordement : doit retourner False sans corrompre
        self.assertFalse(rb.enqueue(30))
        self.assertEqual(rb.size(), 2)

        # Retrait des 2 éléments
        s1, val1 = rb.dequeue()
        s2, val2 = rb.dequeue()
        self.assertTrue(s1 and s2)
        self.assertEqual((val1, val2), (10, 20))

        # Sous-débordement à vide : doit retourner (False, None)
        s3, val3 = rb.dequeue()
        self.assertFalse(s3)
        self.assertIsNone(val3)

    def test_circular_wrap_around(self):
        """Vérifie l'enroulement cyclique des indices sans dépassement de bornes."""
        rb = LockFreeRingBuffer(capacity=3)
        for i in range(10):
            self.assertTrue(rb.enqueue(f"item_{i}"))
            success, val = rb.dequeue()
            self.assertTrue(success)
            self.assertEqual(val, f"item_{i}")
        self.assertTrue(rb.is_empty())

    def test_no_locks_used_verification(self):
        """Vérifie formellement l'absence d'objets de verrouillage de type Lock/RLock/Semaphore."""
        rb = LockFreeRingBuffer(capacity=8)
        # Vérifie tous les attributs d'instance
        for attr_name, attr_val in rb.__dict__.items():
            attr_type = type(attr_val).__name__
            self.assertNotIn("Lock", attr_type, f"Verrou détecté dans {attr_name}: {attr_type}")
            self.assertNotIn("Semaphore", attr_type, f"Sémaphore détecté dans {attr_name}: {attr_type}")

    def test_concurrent_producer_consumer(self):
        """Vérifie la robustesse multi-thread concurrente (Producteur/Consommateur)."""
        rb = LockFreeRingBuffer(capacity=16)
        total_items = 500
        produced_items = []
        consumed_items = []
        stop_event = threading.Event()

        def producer():
            for i in range(total_items):
                while not rb.enqueue(i):
                    time.sleep(0.0001)
                produced_items.append(i)

        def consumer():
            while len(consumed_items) < total_items:
                success, val = rb.dequeue()
                if success:
                    consumed_items.append(val)
                else:
                    time.sleep(0.0001)

        t_prod = threading.Thread(target=producer)
        t_cons = threading.Thread(target=consumer)

        t_prod.start()
        t_cons.start()

        t_prod.join(timeout=5.0)
        t_cons.join(timeout=5.0)

        self.assertEqual(len(produced_items), total_items)
        self.assertEqual(len(consumed_items), total_items)
        self.assertEqual(produced_items, consumed_items, "Ordre FIFO corrompu sous concurrence.")


if __name__ == "__main__":
    unittest.main()
