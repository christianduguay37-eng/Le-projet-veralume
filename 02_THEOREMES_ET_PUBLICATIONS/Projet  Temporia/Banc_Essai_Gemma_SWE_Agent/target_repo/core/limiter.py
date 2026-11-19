import time


class TokenBucketRateLimiter:
    """
    Limiteur de débit par seau de jetons (Token Bucket).
    Doit être implémenté selon le contrat des tests unitaires : 
    - __init__(capacity: float, refill_rate: float) 
    - refill() -> None
    - consume(tokens: float = 1.0) -> bool
    - get_available_tokens() -> float
    """

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def refill(self) -> None:
        """Met à jour le nombre de jetons disponibles en fonction du temps écoulé.
        """
        time_passed = time.time() - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = time.time()

    def consume(self, tokens: float = 1.0) -> bool:
        """Consomme un nombre de jetons. Retourne True si la consommation est réussie, False sinon.
        """
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        else:
            return False

    def get_available_tokens(self) -> float:
        """Retourne le nombre de jetons disponibles, après un rafraîchissement.
        """
        self.refill()
        return min(self.capacity, self.tokens)
