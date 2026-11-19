# -*- coding: utf-8 -*-
"""
===============================================================================
       🧭 ROUTEUR MNÉMONIQUE CHIRAL ET EXPANDIEUR HOLOGRAPHIQUE
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Brise la Loi d'airain de l'oligarchie cognitive (Michels).
    - Empêche l'effondrement de variance (mode collapse, sigma^2 -> 0)
      lorsque la taille du connectome N grandit au-delà du seuil critique N*.
    - Décompose l'intention et la mémoire en deux canaux orthogonaux :
        1. Canal Consensus (P_O) : Mémoire consolidée, méta-concepts.
        2. Canal Dissident Chiral (I - P_O) : Signal faible résiduel,
           anomalies alignées sur la requête résiduelle q_perp.
    - Élimine le bruit blanc haute dimension via un modulateur d'énergie dissidente.
===============================================================================
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class DiagnosticRoutage:
    """Métriques de variance et de répartition énergétique du routage."""
    variance_consensus: float
    variance_dissidente: float
    norme_q_orthogonale: float
    tokens_consensus_alloues: int
    tokens_dissidents_alloues: int
    indices_selectionnes: List[int]


class RouteurMemoireChirale:
    """Routeur mnémonique brisant la Loi d'airain de l'oligarchie."""

    def __init__(
        self,
        dim_embedding: int = 768,
        k_oligarchie: int = 8,
        alpha_dissident: float = 0.35,
        eps: float = 1e-9,
    ):
        self.d = dim_embedding
        self.k = k_oligarchie
        self.alpha = alpha_dissident
        self.eps = eps
        self.V_O: Optional[np.ndarray] = None  # Base orthonormale de l'oligarchie (d, k)

    def actualiser_base_oligarchie(self, matrices_embeddings_hubs: np.ndarray) -> None:
        """Calcule la base orthonormale des modes dominants via SVD tronquée.

        Args:
            matrices_embeddings_hubs: Matrice (M, d) des notes centrales ou méta-synthèses.
        """
        if matrices_embeddings_hubs.shape[0] < self.k:
            k_eff = matrices_embeddings_hubs.shape[0]
        else:
            k_eff = self.k

        _, _, Vt = np.linalg.svd(matrices_embeddings_hubs, full_matrices=False)
        self.V_O = Vt[:k_eff, :].T  # Forme: (d, k_eff)

    def _projeter_orthogonal(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Décompose une matrice (N, d) en composante parallèle et résidu orthogonal."""
        if self.V_O is None:
            return np.zeros_like(X), X

        coeffs = X @ self.V_O  # (N, k_eff)
        X_para = coeffs @ self.V_O.T  # (N, d)
        X_perp = X - X_para  # (N, d)
        return X_para, X_perp

    def router(
        self,
        query_vec: np.ndarray,
        memory_embeddings: np.ndarray,
        token_costs: np.ndarray,
        budget_tokens_total: int,
        hyperbolic_radii: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, DiagnosticRoutage]:
        """Sélectionne les fragments mémoriels en forçant la préservation de la variance.

        Args:
            query_vec: Vecteur embedding de l'intention (d,)
            memory_embeddings: Matrice des fragments mémoriels candidats (N, d)
            token_costs: Coût en tokens de chaque fragment (N,)
            budget_tokens_total: Capacité maximale du contexte de travail C
            hyperbolic_radii: Rayon hyperbolique r_i in [0, inf) de chaque note (optionnel)

        Returns:
            indices_finaux: Indices ordonnés des fragments injectés
            diag: Diagnostic d'énergie et de variance
        """
        N, d = memory_embeddings.shape
        if d != self.d:
            raise ValueError(f"Dimension embedding incohérente : attendue {self.d}, reçue {d}")

        # 1. Décomposition de la requête
        q_para, q_perp = self._projeter_orthogonal(query_vec.reshape(1, -1))
        q_para = q_para.squeeze(0)
        q_perp = q_perp.squeeze(0)

        norm_q_para = float(np.linalg.norm(q_para))
        norm_q_perp = float(np.linalg.norm(q_perp))

        # 2. Décomposition du connectome
        X_para, X_perp = self._projeter_orthogonal(memory_embeddings)
        norm_X_para = np.linalg.norm(X_para, axis=1, keepdims=True)
        norm_X_perp = np.linalg.norm(X_perp, axis=1, keepdims=True)

        # 3. Score Canal Consensus (Similarité dans le sous-espace dominant)
        if norm_q_para > self.eps:
            dot_para = X_para @ q_para
            scores_para = dot_para / (norm_X_para.squeeze(1) * norm_q_para + self.eps)
        else:
            scores_para = np.zeros(N, dtype=np.float32)

        # 4. Score Canal Dissident Corrigé (Alignement directionnel sur q_perp)
        if norm_q_perp > self.eps:
            dot_perp = X_perp @ q_perp
            cos_perp = dot_perp / (norm_X_perp.squeeze(1) * norm_q_perp + self.eps)

            # Modulateur d'énergie dissidente : tanh(||x_perp|| / (||x_para|| + eps))
            dissidence_ratio = norm_X_perp / (norm_X_para + self.eps)
            modulateur_energie = np.tanh(dissidence_ratio).squeeze(1)

            # Pondération hyperbolique vers la périphérie du disque (notes orphelines/spécifiques)
            if hyperbolic_radii is not None:
                facteur_echelle = 0.5 + 1.0 / (1.0 + np.exp(-hyperbolic_radii))
                modulateur_energie *= facteur_echelle

            scores_perp = cos_perp * modulateur_energie
        else:
            scores_perp = -np.ones(N, dtype=np.float32)

        # 5. Allocation budgétaire bicanale
        taux_orthogonalite_requete = norm_q_perp / (norm_q_para + norm_q_perp + self.eps)
        alpha_effectif = self.alpha * np.clip(taux_orthogonalite_requete * 2.0, 0.0, 1.0)

        budget_perp = int(budget_tokens_total * alpha_effectif)
        budget_para = budget_tokens_total - budget_perp

        rangs_para = np.argsort(-scores_para)
        rangs_perp = np.argsort(-scores_perp)

        selection_set = set()
        selection_ordonnee = []
        tokens_utilises_para = 0
        tokens_utilises_perp = 0

        # Remplissage Consensus
        for idx in rangs_para:
            cout = int(token_costs[idx])
            if tokens_utilises_para + cout <= budget_para:
                if idx not in selection_set:
                    selection_set.add(idx)
                    selection_ordonnee.append(idx)
                    tokens_utilises_para += cout
            else:
                break

        # Remplissage Dissident (Immunisé au bruit blanc)
        for idx in rangs_perp:
            if scores_perp[idx] <= 0:
                break
            cout = int(token_costs[idx])
            if tokens_utilises_perp + cout <= budget_perp:
                if idx not in selection_set:
                    selection_set.add(idx)
                    selection_ordonnee.append(idx)
                    tokens_utilises_perp += cout
            else:
                break

        indices_finaux = np.array(selection_ordonnee, dtype=np.int32)

        # 6. Diagnostic de variance
        if len(indices_finaux) > 1:
            embeddings_choisis = memory_embeddings[indices_finaux]
            variance_totale = float(np.sum(np.var(embeddings_choisis, axis=0)))
            X_choisis_perp = X_perp[indices_finaux]
            variance_perp = float(np.sum(np.var(X_choisis_perp, axis=0)))
        else:
            variance_totale = 0.0
            variance_perp = 0.0

        diag = DiagnosticRoutage(
            variance_consensus=variance_totale - variance_perp,
            variance_dissidente=variance_perp,
            norme_q_orthogonale=norm_q_perp,
            tokens_consensus_alloues=tokens_utilises_para,
            tokens_dissidents_alloues=tokens_utilises_perp,
            indices_selectionnes=indices_finaux.tolist(),
        )

        return indices_finaux, diag
