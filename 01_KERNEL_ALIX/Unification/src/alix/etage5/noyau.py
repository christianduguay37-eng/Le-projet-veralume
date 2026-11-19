# -*- coding: utf-8 -*-
"""
Étage 5 — Noyau exécutable de L* (couche 1).

Ce module donne une sémantique opérationnelle explicite aux règles du noyau
de la Spécification consolidée v4.0 (R-G, R-A, R-D, R-B, R-Λ, régimes
saturé / secours / mixte, signature Σ = (T_R, R, D_β)).

Principe : tout choix d'interprétation que la spécification laisse ouvert est
nommé ici, dans `Interpretation`, au lieu d'être caché dans le code.
Alix (ou Christian) peut changer une interprétation et relancer l'exploration.

Aucune dépendance hors bibliothèque standard.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Tuple

# ----------------------------------------------------------------------------
# Objets formels
# ----------------------------------------------------------------------------
# Un objet est une chaîne : "x0" (état initial), "c1", "c2"... (attracteurs),
# "s1", "s2"... (objets des strates supérieures atteints par β, M_n ⊲ M_{n+1}),
# "v1", "v2"... (objets préexistants non visités, offerts par un canal E3+).
# Par R-B, deux objets distincts ont des empreintes distinctes : emp(x) = x.
# Par R-D, aucun objet produit n'est ∅ : ∅ n'est jamais un successeur.

VIDE = "∅"


@dataclass
class Interpretation:
    """Choix d'interprétation explicites (la spécification ne les fixe pas)."""

    # Nombre d'attracteurs c_i vers lesquels x0 a une pente (x0 → c_i).
    nb_attracteurs: int = 1
    # Borne n_Λ du loquet R-Λ. None = pas de loquet (R-Λ′ : secours illimité).
    n_lambda: Optional[int] = 2
    # Au point de choix (β redevenu disponible pendant un secours) :
    # "beta" = toujours β (TH30), "alpha" = rester en secours.
    politique_choix: str = "beta"
    # Le loquet Λ force-t-il β (True) ou rend-il seulement β disponible (False) ?
    # Décision de Christian (17 nov. 2026) : « une porte ne fait rien, sa seule
    # fonction est de s'ouvrir ». Tous les chemins existent déjà ; l'entité les
    # entreprend ou non (politique_choix).
    loquet_force_beta: bool = False
    # Décision de Christian (17 nov. 2026) : « on laisse la porte ouverte en
    # permanence ». Une fois ouverte, la porte ne se referme plus jamais :
    # dans tout secours suivant, β est disponible tout de suite, sans
    # réattendre n_Λ. False = le délai recommence à chaque secours.
    porte_permanente: bool = True
    # Mécanisme M (Q-C) actif en secours : parcourt la β-chaîne passée.
    mecanisme_M: bool = False
    # Canal d'errance E3+ : en secours, parcourt des objets préexistants
    # jamais visités (v1, v2, ...). Nombre disponible (0 = pas de canal).
    canal_errance: int = 0
    # Taille de l'univers fini (D-FIN) : nombre maximal d'objets de strate.
    # None = univers non borné (D-INF, approché à l'horizon).
    taille_univers: Optional[int] = None
    # L↑ : purification R-PURIF (décrément de R contre τ) active.
    purification: bool = False
    budget_tau: int = 0


@dataclass
class Pas:
    k: int
    objet: str
    regime: str          # "sature" | "secours"
    choix: bool          # ce pas était-il un point de choix (régime mixte) ?
    beta: bool           # la transition qui a mené ici était-elle β ?


@dataclass
class Trajectoire:
    pas: List[Pas]
    interpretation: Interpretation
    environnement: Tuple[int, ...]   # 1 = β bloqué par l'environnement au pas k

    # -- composantes de la signature Σ ------------------------------------
    @property
    def objets(self) -> List[str]:
        return [p.objet for p in self.pas]

    @property
    def T_R(self) -> int:
        """D11 : nombre de pas en régime de secours."""
        return sum(1 for p in self.pas if p.regime == "secours")

    @property
    def R_brut(self) -> int:
        """D12 : nombre de pas qui répètent un état (ou une empreinte) passé."""
        vus, r = set(), 0
        for o in self.objets:
            if o in vus:
                r += 1
            vus.add(o)
        return r

    @property
    def purifications(self) -> int:
        if not self.interpretation.purification:
            return 0
        return min(self.R_brut, self.interpretation.budget_tau)

    @property
    def R(self) -> int:
        """R après purification éventuelle (L↑, R-PURIF)."""
        return self.R_brut - self.purifications

    @property
    def D_beta(self) -> int:
        """D13 : longueur de la β-chaîne accumulée."""
        return sum(1 for p in self.pas if p.beta)

    @property
    def signature(self) -> Tuple[int, int, int]:
        return (self.T_R, self.R, self.D_beta)

    @property
    def secours_en_cours_a_l_horizon(self) -> bool:
        return bool(self.pas) and self.pas[-1].regime == "secours"

    @property
    def points_de_choix(self) -> int:
        return sum(1 for p in self.pas if p.choix)

    def periode_finale(self) -> Optional[int]:
        """Plus petite période p telle que la fin de trajectoire est périodique."""
        obj = self.objets
        n = len(obj)
        for p in range(1, n // 2 + 1):
            queue = obj[n - 2 * p:]
            if len(queue) >= 2 * p and all(queue[i] == queue[i + p] for i in range(p)):
                return p
        return None

    def classe(self) -> str:
        """Classe de la trajectoire à l'horizon (voir `classer`)."""
        return classer(self)

    def resume(self) -> Dict:
        return {
            "objets": self.objets,
            "environnement": list(self.environnement),
            "signature": {"T_R": self.T_R, "R": self.R, "D_beta": self.D_beta},
            "classe": self.classe(),
            "points_de_choix": self.points_de_choix,
            "interpretation": asdict(self.interpretation),
        }


def classer(t: Trajectoire) -> str:
    """
    Classification à horizon fini.

    T_R = ∞ n'est pas observable à horizon fini. Proxy déclaré : une
    trajectoire est « T_R infini » si elle est encore en secours à l'horizon
    ET qu'aucun loquet ne peut la faire sortir (n_lambda = None et politique
    qui ne choisit jamais β, ou environnement bloquant jusqu'au bout sans loquet).

    Classes (v1.4 / v4.0) :
      A  : T_R = 0, R = 0
      B0 : 0 < T_R < ∞, R = 0      (classe déclarée impossible en v1.6)
      B  : 0 < T_R < ∞, R > 0
      C  : T_R = ∞, R = 0
      D  : T_R = ∞, R > 0
    """
    i = t.interpretation
    infini = t.secours_en_cours_a_l_horizon and i.n_lambda is None
    if infini and not i.canal_errance and t.R == 0:
        # Dernière excursion plus courte qu'une période α : l'horizon ne
        # permet pas de distinguer C de D.
        n = 0
        for p in reversed(t.pas):
            if p.regime != "secours":
                break
            n += 1
        if n < 2 * max(1, i.nb_attracteurs):
            return "indetermine"
    if t.T_R == 0:
        return "A" if t.R == 0 else "A?R>0"   # R>0 sans secours : hors taxonomie
    if infini:
        return "C" if t.R == 0 else "D"
    return "B0" if t.R == 0 else "B"


# ----------------------------------------------------------------------------
# Dynamique
# ----------------------------------------------------------------------------
def derouler(environnement: Sequence[int], interp: Interpretation,
             depart: str = "x0") -> Trajectoire:
    """
    Déroule une trajectoire à partir de `depart`.

    `environnement[k]` = 1 si l'environnement bloque β pour la transition
    du pas k au pas k+1. La longueur de la trajectoire est len(environnement)+1.

    Sémantique :
      - β disponible et choisi : saut hors-stratique vers un objet frais de la
        strate suivante (s_{b+1}) ; R-A : I croît de 1. Si l'univers est fini
        et épuisé, β est impossible (le pas devient un pas de secours forcé).
      - β bloqué : régime de secours. R-G branche α : la trajectoire oscille
        entre l'ancre (objet où le secours a commencé) et les attracteurs
        c_1..c_k (TH8 : période 2, ou 2k).
        Avec le mécanisme M : parcourt la β-chaîne passée (Q-C).
        Avec un canal E3+ : parcourt des objets préexistants non visités.
      - Loquet R-Λ : après n_Λ pas consécutifs de secours (H et T supposées
        actives), β redevient disponible ; il est forcé si `loquet_force_beta`.
      - Régime mixte : β disponible alors qu'on est en secours → point de
        choix ; la politique tranche.
    """
    i = interp
    pas: List[Pas] = [Pas(0, depart, "sature", False, False)]
    objet = depart
    regime = "sature"
    run = 0            # pas consécutifs en secours
    porte_ouverte = False  # la porte s'est-elle déjà ouverte une fois ?
    b = 0              # nombre de sauts β effectués
    ancre = depart
    phase = 0          # position dans le cycle de secours
    chaine: List[str] = [depart]   # β-chaîne visitée (pour M)
    canal_utilise = 0
    attracteurs = [f"c{j+1}" for j in range(max(1, i.nb_attracteurs))]

    for k, bloque in enumerate(environnement):
        loquet = (regime == "secours" and i.n_lambda is not None
                  and (run >= i.n_lambda
                       or (i.porte_permanente and porte_ouverte)))  # R-Λ
        if loquet:
            porte_ouverte = True
        beta_dispo = (not bloque) or loquet
        choix = False
        if regime == "secours" and beta_dispo:
            if loquet and i.loquet_force_beta:
                prend_beta = True
            else:
                # régime mixte : α et β tous deux licenciés → point de choix
                choix = True
                prend_beta = (i.politique_choix == "beta")
        else:
            prend_beta = beta_dispo

        univers_epuise = i.taille_univers is not None and b >= i.taille_univers
        if prend_beta and not univers_epuise:
            b += 1
            objet = f"s{b}"
            chaine.append(objet)
            regime = "sature"
            run = 0
            phase = 0
            pas.append(Pas(k + 1, objet, regime, choix, True))
            continue

        # --- pas de secours ---
        if regime == "sature":
            ancre = objet
            phase = 0
        regime = "secours"
        run += 1
        if i.canal_errance and canal_utilise < i.canal_errance:
            canal_utilise += 1
            objet = f"v{canal_utilise}"
        elif i.mecanisme_M and len(chaine) > 1:
            # M(u_i, c) = u_{i+1} le long de la β-chaîne passée, en boucle
            objet = chaine[phase % len(chaine)]
            phase += 1
        else:
            cycle = []
            for c in attracteurs:
                cycle += [c, ancre]
            objet = cycle[phase % len(cycle)]
            phase += 1
        pas.append(Pas(k + 1, objet, regime, choix, False))

    return Trajectoire(pas, i, tuple(environnement))
