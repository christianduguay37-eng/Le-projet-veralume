# -*- coding: utf-8 -*-
"""
===============================================================================
       ⚡ ATTENTION CHIRALE ORTHOGONALE (COA) À MÉMOIRE BORNÉE O(d²)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Résout le Trilemme de l'Attention des grands modèles :
        1. Élimine la dilution entropique Softmax (plus de division par Z(L) -> infini).
        2. Élimine l'écrasement spectral de la règle Delta / Linear Attention.
        3. Maintient un état borné strict O(d²) dans le cache silicium L3 (Lunar Lake).
    - Opérateur non-linéaire séquentiel rendu possible par l'absence de contrainte de batch (B=1).
    - Sanctuarisation chirale des aiguilles à décroissance nulle (gamma_perp = 1).
===============================================================================
"""

from typing import Dict, Tuple, Optional
import numpy as np


class ChiralOrthogonalAttention:
    """Opérateur d'attention à mémoire bornée O(d²) et immunité spectrale."""

    def __init__(
        self,
        dim: int = 64,
        eta: float = 0.5,
        decay_c: float = 0.02,
        theta_energy: float = 0.02,
        warmup_steps: int = 50,
        dtype=np.float64,
    ):
        self.d = dim
        self.eta = eta
        self.decay_c = decay_c
        self.theta_energy = theta_energy
        self.warmup_steps = warmup_steps
        self.dtype = dtype

        # État mnémonique borné O(d²) — Résident en Cache L3
        self.S_bulk = np.zeros((dim, dim), dtype=dtype)     # Mémoire associative de fond
        self.S_chiral = np.zeros((dim, dim), dtype=dtype)   # Sanctuaire des aiguilles rares (γ_⊥ = 1)
        self.C_k = np.zeros((dim, dim), dtype=dtype)        # Covariance running du sous-espace dominant

        self.pas_temps: int = 0
        self.compteur_aiguilles: int = 0

    def mettre_a_jour(self, k: np.ndarray, v: np.ndarray) -> bool:
        """Met à jour l'état mnémonique séquentiel Φ(S_{t-1}, k_t, v_t).

        Args:
            k: Vecteur clé (d,)
            v: Vecteur valeur (d,)

        Returns:
            est_aiguille: True si le token a été sanctuarisé dans S_chiral, False sinon.
        """
        self.pas_temps += 1
        energy = float(k @ self.C_k @ k)

        if self.pas_temps <= self.warmup_steps or energy > self.theta_energy:
            # Branche A : Token de fond redondant (compression amortie)
            self.C_k = (1.0 - self.decay_c) * self.C_k + self.decay_c * np.outer(k, k)
            self.S_bulk = self.S_bulk - self.eta * np.outer(self.S_bulk @ k, k) + self.eta * np.outer(v, k)
            # S_chiral reste strictement intact (zéro fuite)
            return False
        else:
            # Branche B : Anomalie / Aiguille chirale (sanctuaire à γ_⊥ = 1)
            self.S_chiral = self.S_chiral + np.outer(v, k)
            self.compteur_aiguilles += 1
            # C_k et S_bulk ne sont pas pollués par l'anomalie
            return True

    def lire(self, q: np.ndarray) -> np.ndarray:
        """Opérateur de lecture Ψ(S_L, q) découplé sans division de partition."""
        energy_q = float(q @ self.C_k @ q)

        if energy_q <= self.theta_energy:
            # Lecture chirale directe (Aiguille) : normalisation de norme unitaire
            norme_sq = float(np.dot(q, q)) + 1e-12
            return self.S_chiral @ q / norme_sq
        else:
            # Lecture sur la mémoire de fond consolidée
            return self.S_bulk @ q

    def empreinte_memoire_octets(self) -> int:
        """Retourne la taille mémoire exacte des tenseurs d'état en octets."""
        taille_unitaire = np.dtype(self.dtype).itemsize
        return 3 * self.d * self.d * taille_unitaire

    def reinitialiser(self) -> None:
        """Remet à zéro les tenseurs d'état."""
        self.S_bulk.fill(0)
        self.S_chiral.fill(0)
        self.C_k.fill(0)
        self.pas_temps = 0
        self.compteur_aiguilles = 0
