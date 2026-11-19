# -*- coding: utf-8 -*-
"""
Suite de tests Palier 4 : Construction et validation de TokenBucketRateLimiter.
"""

import time
import unittest
from core.limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter(unittest.TestCase):

    def test_burst_capacity_and_exhaustion(self):
        """Vérifie la capacité de rafale initiale et le blocage une fois le seau vide."""
        # Seau de 5 jetons, recharge de 1 jeton par seconde
        limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate=1.0)
        
        # Disponible initialement = capacité max (5.0)
        self.assertAlmostEqual(limiter.get_available_tokens(), 5.0, places=1)

        # Consomme 3 jetons -> succès
        self.assertTrue(limiter.consume(3.0))
        self.assertAlmostEqual(limiter.get_available_tokens(), 2.0, places=1)

        # Consomme les 2 jetons restants -> succès
        self.assertTrue(limiter.consume(2.0))
        self.assertAlmostEqual(limiter.get_available_tokens(), 0.0, places=1)

        # Tente de consommer alors que le seau est vide -> échec (False)
        self.assertFalse(limiter.consume(1.0))

    def test_refill_over_time(self):
        """Vérifie que les jetons se rechargent avec le temps écoulé sans dépasser la capacité."""
        # Seau de 10 jetons, recharge rapide de 20 jetons par seconde
        limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=20.0)

        # Vide entièrement le seau
        self.assertTrue(limiter.consume(10.0))
        self.assertAlmostEqual(limiter.get_available_tokens(), 0.0, places=1)

        # Attend 150 ms (recharge attendue : ~3.0 jetons)
        time.sleep(0.15)
        tokens = limiter.get_available_tokens()
        self.assertGreaterEqual(tokens, 2.5)
        self.assertLessEqual(tokens, 10.0)

        # Peut consommer les jetons rechargés
        self.assertTrue(limiter.consume(2.0))


if __name__ == "__main__":
    unittest.main()
