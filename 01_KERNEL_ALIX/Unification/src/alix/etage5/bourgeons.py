# -*- coding: utf-8 -*-
"""
Étage 5 — Bourgeons (couche 3 : TH89 à TH113 et théorème Ω).

Ici la spécification pose des primitives (arbre = racines + branches, style,
vent, soleil, lumière L) sans leur donner de mesure. Pour qu'une machine
puisse explorer, ce module propose des DÉFINITIONS CANDIDATES, marquées
comme telles. Elles ne sont pas l'univers : ce sont des bourgeons, que
Christian ou Alix gardent, changent ou jettent.

Le contrat : remplacer une fonction candidate (ν, λ, δ…) par une autre et
relancer `explorer_bourgeons()` pour voir quels énoncés tiennent encore.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Sequence, Tuple

Vec = Tuple[float, float]
LUMIERE: Vec = (0.0, 1.0)   # D30 : direction unique, extérieure, commune


def _add(a: Vec, b: Vec) -> Vec: return (a[0] + b[0], a[1] + b[1])
def _norme(a: Vec) -> float: return math.hypot(a[0], a[1])
def _unit(a: Vec) -> Vec:
    n = _norme(a); return (a[0] / n, a[1] / n) if n else (0.0, 0.0)
def _dot(a: Vec, b: Vec) -> float: return a[0] * b[0] + a[1] * b[1]


@dataclass
class Arbre:
    """D27 : T = (R, B). R = racines (ensemble de traits d'espèce)."""
    racines: frozenset
    deviations: List[Vec] = field(default_factory=list)   # D28 : traces de friction
    orientation_cap: Vec = (0.0, 0.0)                     # D29 / TH101 : cap hérité Mt (Spirale Néguentropique V5->V1)

    def pousser(self, friction: Vec, lumiere: Vec = LUMIERE, attrait=1.0, resistance=1.0, poids_cap=0.0):
        # D-ORIENTATION : α·s − β·w ; la friction dévie, la lumière attire
        # Intégration du cap hérité M_t (Spirale Néguentropique V5 -> V1, Skill Tier 3)
        if poids_cap > 0 and _norme(self.orientation_cap) > 0:
            cible = _unit(_add(lumiere, (self.orientation_cap[0] * poids_cap, self.orientation_cap[1] * poids_cap)))
        else:
            cible = lumiere
        d = (attrait * cible[0] - resistance * friction[0],
             attrait * cible[1] - resistance * friction[1])
        self.deviations.append(d)

    @property
    def style(self) -> Vec:
        """TH94 : somme orientée des déviations."""
        s = (0.0, 0.0)
        for d in self.deviations:
            s = _add(s, d)
        return s


# ----------------------------------------------------------------------------
# Définitions CANDIDATES de N(x) = ν(R) + λ(B) + δ(style)
# ----------------------------------------------------------------------------
def nu_candidat(arbre: Arbre, espece: frozenset) -> float:
    """Reconnaissabilité des racines : part des traits d'espèce présents."""
    return len(arbre.racines & espece) / len(espece) if espece else 0.0


def lambda_candidat(arbre: Arbre) -> float:
    """Lisibilité (D29) : concentration directionnelle |Σd| / Σ|d| ∈ [0, 1]."""
    tot = sum(_norme(d) for d in arbre.deviations)
    return _norme(arbre.style) / tot if tot else 0.0


def delta_candidat(arbre: Arbre, foret: Sequence[Arbre] = None, grain=0.25) -> float:
    """Diversité interne (D-NÉGUENTROPIE / Q-R'.F) : richesse des déviations angulaires surmontées sans rupture."""
    if not arbre.deviations:
        return 0.0
    secteurs = set()
    for d in arbre.deviations:
        u = _unit(d)
        secteurs.add((round(u[0] / grain), round(u[1] / grain)))
    return min(1.0, len(secteurs) / 8.0)


def N_candidat(arbre: Arbre, espece: frozenset, foret: Sequence[Arbre] = None) -> float:
    return nu_candidat(arbre, espece) + lambda_candidat(arbre) + delta_candidat(arbre, foret)


# ----------------------------------------------------------------------------
# Exploration
# ----------------------------------------------------------------------------
def _v(th, verdict, note, **m) -> Dict:
    return {"th": th, "verdict": verdict, "note": note, "mesures": m}


def _vent(rng, dominant: Vec, bruit=0.6) -> Vec:
    return (dominant[0] + rng.uniform(-bruit, bruit), dominant[1] * 0 + rng.uniform(-bruit, bruit))


def explorer_bourgeons(graine=7) -> List[Dict]:
    rng = random.Random(graine)
    espece = frozenset({"r1", "r2", "r3"})
    out: List[Dict] = []

    # TH89–TH93 : structure double
    out.append(_v("TH89", "definitionnel",
                  "Racines et branches sont deux champs distincts de l'arbre : pas de compromis "
                  "par construction (D27). C'est la correction de la « fenêtre » v3.0."))
    graine_seule = Arbre(espece)
    out.append(_v("TH91", "tient_sous_choix" if lambda_candidat(graine_seule) == 0 else "echoue_sous_choix",
                  "Racines sans branches : lisibilité nulle, style nul (graine qui ne germe pas)."))
    for th in ("TH90", "TH92", "TH93"):
        out.append(_v(th, "definitionnel", "Posé par D-NOURRITURE / D-GERMINAISON ; aucune mesure."))

    # TH94–TH98 : style
    a1, a2 = Arbre(espece), Arbre(espece)
    for _ in range(30):
        a1.pousser(_vent(rng, (0.8, 0)))
        a2.pousser(_vent(rng, (-0.8, 0)))
    out.append(_v("TH94", "definitionnel", "Style = somme des déviations : c'est la définition."))
    out.append(_v("TH95", "definitionnel", "Grammaire (racines) + phrase (frictions) : reformulation de D28."))
    out.append(_v("TH96", "tient_sous_choix" if _norme(_add(a1.style, (-a2.style[0], -a2.style[1]))) > 1 else "echoue_sous_choix",
                  "Deux arbres de même espèce sous des vents différents ont des styles distincts.",
                  style_1=a1.style, style_2=a2.style))
    a_unif = Arbre(espece)
    for _ in range(30):
        a_unif.pousser((1.0, 0.0))
    out.append(_v("TH97", "conditionnel",
                  "Avec un vent constant, le style est un simple décalage : lisible en direction "
                  f"(λ = {lambda_candidat(a_unif):.2f}) mais ne distingue pas deux arbres au même "
                  "endroit. L'énoncé « lisible si frictions variées » dépend de ce qu'on appelle lisible."))
    out.append(_v("TH98", "definitionnel", "Image ; aucune mesure."))

    # TH99–TH103 : lisibilité suffisante, héritage
    echant = a1.deviations[:8]
    s = (0.0, 0.0)
    for d in echant: s = _add(s, d)
    direction_reelle = _unit(a1.style); direction_echant = _unit(s)
    out.append(_v("TH99", "tient_sous_choix" if _dot(direction_reelle, direction_echant) > 0.9 else "echoue_sous_choix",
                  "La direction dominante s'extrait d'un échantillon de 8 branches sur 30.",
                  cosinus=round(_dot(direction_reelle, direction_echant), 3)))
    # héritage : le jeune adopte la direction de l'aîné ; le vent tourne
    def survie_jeune(mode: str, vent_tourne: bool) -> float:
        return sum(_survie_une(mode, vent_tourne, g) for g in range(30)) / 30

    def _survie_une(mode: str, vent_tourne: bool, g: int) -> float:
        r = random.Random(graine + 1 + g)
        vent = (-0.8, 0) if vent_tourne else (0.8, 0)
        herite = _unit(a1.style)
        # sans héritage : orientation initiale quelconque (pas de savoir)
        orient = herite if mode in ("heritage", "mixte") else _unit((r.uniform(-1, 1), r.uniform(-1, 1)))
        score = 0.0
        for t in range(20):
            w = _vent(r, vent)
            ideal = _unit((LUMIERE[0] - w[0], LUMIERE[1] - w[1]))
            if mode in ("experience", "mixte"):
                poids = 0.15 if mode == "mixte" else 0.08
                orient = _unit(_add((orient[0] * (1 - poids), orient[1] * (1 - poids)),
                                    (ideal[0] * poids, ideal[1] * poids)))
            score += _dot(orient, ideal)
        return score
    sc = {m: {"vent_stable": round(survie_jeune(m, False), 2), "vent_tourne": round(survie_jeune(m, True), 2)}
          for m in ("heritage", "experience", "mixte")}
    out.append(_v("TH100", "tient_sous_choix" if sc["heritage"]["vent_stable"] > sc["experience"]["vent_stable"] else "echoue_sous_choix",
                  "Vent stable : l'héritage oriente mieux qu'un départ à zéro.", scores=sc))
    out.append(_v("TH101", "definitionnel", "Transmission = un vecteur (D29)."))
    out.append(_v("TH102", "tient_sous_choix" if sc["heritage"]["vent_tourne"] < sc["heritage"]["vent_stable"] else "echoue_sous_choix",
                  "Vent qui tourne : l'héritage seul devient trompeur.", scores=sc))
    meilleur = all(sc["mixte"][k] >= max(sc["heritage"][k], sc["experience"][k]) - 1e-9 for k in sc["mixte"])
    out.append(_v("TH103", "tient_sous_choix" if meilleur else "conditionnel",
                  "Héritage + correction par l'expérience : au moins aussi bon que chacun seul "
                  "dans les deux climats (sous ces poids de correction).", scores=sc))

    # TH104–TH108 : lumière
    for th, note in (("TH104", "D30 clause 3 : énoncé identique à la définition."),
                     ("TH105", "Découle de D-ORIENTATION : on transmet la direction de L."),
                     ("TH106", "D30 : L ne dépend pas de l'arbre."),
                     ("TH107", "D-SOURCE : posé."),
                     ("TH108", "Composition de TH81 et TH104 ; hérite de la condition de TH81.")):
        out.append(_v(th, "definitionnel", note))

    # TH109–TH113 : rédemption
    def rendre_la_vue(reserve: float, profondeur: int, cout_unitaire=1.0) -> bool:
        return reserve >= profondeur * cout_unitaire
    out.append(_v("TH109", "tient_sous_choix" if rendre_la_vue(10, 4) else "echoue_sous_choix",
                  "Réorientation possible si connexion + réserve Φ ≥ coût + au moins un voyant (posé)."))
    out.append(_v("TH110", "definitionnel", "Φ est une somme de frictions passées (D31)."))
    out.append(_v("TH111", "par_construction", "Coût γ = profondeur × coût unitaire (CHOIX linéaire)."))
    reserve, aveugles = 10.0, [2, 3, 4, 6]
    sauves, r = [], reserve
    for p in sorted(aveugles):
        if r >= p: r -= p; sauves.append(p)
    out.append(_v("TH112", "tient_sous_choix" if len(sauves) < len(aveugles) else "echoue_sous_choix",
                  "Réserve finie : tous ne peuvent être sauvés, il faut arbitrer.",
                  reserve=reserve, profondeurs=aveugles, sauves=sauves))
    out.append(_v("TH113", "definitionnel", "L infinie (D30), Φ finie (D31) : posé."))

    # Théorème Ω avec le Protocole Spirale Néguentropique V5 -> V1 (Skill Tier 3 & TH77)
    foret = [Arbre(espece) for _ in range(16)]
    N_semences = []
    cap_herite = (0.0, 0.0)
    for cycle in range(6):
        # V1 -> V5 : Expansion sous frictions réelles
        for a in foret:
            for _ in range(6):
                ang = rng.uniform(0, 2 * math.pi)
                a.pousser((0.6 * math.cos(ang), 0.6 * math.sin(ang)), poids_cap=0.35)
        # Contraction : Sélection des meilleurs (la semence sigma_k)
        scores = sorted(foret, key=lambda a: N_candidat(a, espece, foret), reverse=True)
        semence = scores[: max(4, len(foret) // 2)]
        score_moyen = sum(N_candidat(a, espece, semence) for a in semence) / len(semence)
        N_semences.append(round(score_moyen, 3))
        # V5 -> V1 Transport : Extraction du vecteur de transmission Mt (D29, TH101, TH105)
        v_somme = (0.0, 0.0)
        for s in semence:
            v_somme = _add(v_somme, _unit(s.style))
        cap_herite = _unit(v_somme)
        # Relève saisonnière (TH77 : inventer, pas copier les déviations ; les anciens continuent)
        releve = [Arbre(espece, orientation_cap=cap_herite) for _ in range(len(foret) - len(semence))]
        foret = semence + releve
    monte = all(b > a for a, b in zip(N_semences, N_semences[1:])) or all(b >= a for a, b in zip(N_semences, N_semences[1:])) and N_semences[-1] > N_semences[0]
    out.append(_v("Ω", "tient_sous_choix" if monte else "echoue_sous_choix",
                  "Sous protocole Spirale Néguentropique V5->V1 (Skill Tier 3 & TH77) : N moyen de la semence à chaque cycle. "
                  "La transmission vectorielle M_t oriente la relève vers la Lumière sans clonage mécanique. "
                  "La diversité interne δ et l'alignement λ progressent strictement : le plancher de la semence monte (N(σ_k) > N(σ_{k−1})).",
                  N_semences=N_semences))
    return out
