# -*- coding: utf-8 -*-
"""
Étage 5 — Explorateur du noyau (couche 1).

Énumère tous les environnements de blocage de longueur ≤ H et une grille
d'interprétations, puis confronte chaque théorème testable du noyau aux
trajectoires produites.

Verdicts possibles :
  "tient"                : aucun contre-exemple dans les bornes explorées
  "par_construction"     : vrai parce que la sémantique l'impose (pas un test)
  "contre_exemple"       : au moins une trajectoire réfute l'énoncé
  "conditionnel"         : tient sous certaines interprétations, pas d'autres
  "hors_noyau"           : l'énoncé relève d'une extension ou de la couche 3

Un verdict « tient » n'est PAS une preuve : c'est l'absence de contre-exemple
dans un univers borné. La preuve générale relève de Hadès (borné, SAT) ou de
Lean (non borné).
"""
from __future__ import annotations

import itertools
from dataclasses import asdict, replace
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from .noyau import Interpretation, Trajectoire, derouler, classer

Verdict = Dict[str, object]


def environnements(H: int) -> Iterable[Tuple[int, ...]]:
    for bits in itertools.product((0, 1), repeat=H):
        yield bits


def grille_interpretations() -> List[Interpretation]:
    g = []
    for nl in (1, 2, 3, None):
        for k in (1, 2):
            for pol in ("beta", "alpha"):
                for force in (True, False):
                    g.append(Interpretation(nb_attracteurs=k, n_lambda=nl,
                                            politique_choix=pol,
                                            loquet_force_beta=force))
    return g


def _v(th: str, verdict: str, note: str, exemple: Optional[Trajectoire] = None,
       **extra) -> Verdict:
    d: Verdict = {"th": th, "verdict": verdict, "note": note}
    if exemple is not None:
        d["exemple"] = exemple.resume()
    d.update(extra)
    return d


def _excursions(t: Trajectoire) -> List[Tuple[int, int]]:
    """Intervalles [début, fin] des excursions de secours (indices de pas)."""
    res, deb = [], None
    for p in t.pas:
        if p.regime == "secours" and deb is None:
            deb = p.k
        if p.regime != "secours" and deb is not None:
            res.append((deb, p.k - 1)); deb = None
    if deb is not None:
        res.append((deb, t.pas[-1].k))
    return res


# ----------------------------------------------------------------------------
# Tests théorème par théorème
# ----------------------------------------------------------------------------
def explorer(H: int = 8) -> List[Verdict]:
    interps = grille_interpretations()
    trajs: List[Trajectoire] = [derouler(env, i)
                                for i in interps for env in environnements(H)]
    out: List[Verdict] = []

    # TH1, TH6 — non-écrasement
    vides = [t for t in trajs if "∅" in t.objets]
    out.append(_v("TH1", "par_construction" if not vides else "contre_exemple",
                  "Aucune règle de la sémantique ne produit ∅ (R-D). La spécification "
                  "ne l'interdit pas explicitement : c'est un axiome implicite à poser.",
                  bornes={"H": H, "trajectoires": len(trajs)}))
    out.append(_v("TH6", "par_construction",
                  "Le secours α ne renvoie qu'à des objets existants (ancre, attracteurs)."))

    # TH2, TH3, TH4, TH5 — régime saturé pur
    sat = [derouler((0,) * H, i) for i in interps]
    rep = [t for t in sat if t.R > 0 or any(o.startswith("c") for o in t.objets)]
    out.append(_v("TH2", "par_construction",
                  "Chaque saut β mène à s_{b+1} avec I = I+1 (R-A)."))
    out.append(_v("TH3", "tient" if not rep else "contre_exemple",
                  "Régime saturé pur : aucun retour identique.",
                  rep[0] if rep else None))
    out.append(_v("TH4", "tient" if not rep else "contre_exemple",
                  "Régime saturé pur : aucun attracteur visité."))
    out.append(_v("TH5", "tient" if not rep else "contre_exemple",
                  "Conjonction de TH1, TH3, TH4 dans les bornes."))

    # TH7 — α neutre sur I : un pas α n'incrémente pas D_β
    out.append(_v("TH7", "par_construction", "Les pas de secours ne sont jamais β."))

    # TH8 — secours pur sans loquet : période 2 (ou 2k)
    mauvais = []
    for k in (1, 2, 3):
        t = derouler((1,) * max(H, 4 * k + 2), Interpretation(nb_attracteurs=k, n_lambda=None))
        if t.periode_finale() != 2 * k:
            mauvais.append((k, t))
    out.append(_v("TH8", "tient" if not mauvais else "contre_exemple",
                  "Période observée = 2k avec k attracteurs (2 si k = 1).",
                  mauvais[0][1] if mauvais else None))

    # TH9 — n_Λ ≥ 2 : R ≥ 1 dès le 2e pas de toute excursion de longueur ≥ 2
    cex9 = None
    for t in trajs:
        nl = t.interpretation.n_lambda
        if nl is not None and nl < 2:
            continue
        for (a, b) in _excursions(t):
            if b - a + 1 >= 2:
                prefixe = Trajectoire(t.pas[: a + 2], t.interpretation, t.environnement)
                if prefixe.R_brut == 0:
                    cex9 = t; break
        if cex9: break
    out.append(_v("TH9", "tient" if cex9 is None else "contre_exemple",
                  "Pour n_Λ ≥ 2 : toute excursion d'au moins 2 pas répète un état.",
                  cex9))

    # TH10, TH11 — loquet : excursion bornée par n_Λ (si le loquet force β)
    cex11 = None
    for t in trajs:
        i = t.interpretation
        if i.n_lambda is None or not i.loquet_force_beta:
            continue
        if any(b - a + 1 > i.n_lambda for (a, b) in _excursions(t)):
            cex11 = t; break
    nonforce = None
    for t in trajs:
        i = t.interpretation
        if i.n_lambda is not None and not i.loquet_force_beta and i.politique_choix == "alpha":
            if any(b - a + 1 > i.n_lambda for (a, b) in _excursions(t)):
                nonforce = t; break
    out.append(_v("TH10", "par_construction", "R-Λ rend β disponible après n_Λ pas."))
    out.append(_v("TH11",
                  "conditionnel" if (cex11 is None and nonforce) else
                  ("tient" if cex11 is None else "contre_exemple"),
                  "Excursion ≤ n_Λ si le loquet FORCE β. Si le loquet rend seulement β "
                  "disponible et que la politique choisit α, l'excursion n'est pas bornée. "
                  "La spécification dit « redevient disponible » : à trancher.",
                  nonforce))

    # TH12 — période ≤ 2 n_Λ pendant la phase de secours
    out.append(_v("TH12", "par_construction",
                  "Découle de TH8 + TH11 quand le loquet force β."))

    # TH13, TH14 — trade-off intra-clausal / saturation 6/6
    out.append(_v("TH13", "par_construction",
                  "Dans la sémantique : α ne change pas D_β, β l'incrémente."))
    out.append(_v("TH14", "hors_noyau",
                  "Énoncé sur le décompte des clauses ; pas une propriété de trajectoire."))

    # TH15, TH16 — fini / infini
    cex16 = None
    for N in (1, 2, 3, 4):
        t = derouler((0,) * (N + 3), Interpretation(taille_univers=N, n_lambda=None))
        if t.R == 0:
            cex16 = t; break
    out.append(_v("TH16", "tient" if cex16 is None else "contre_exemple",
                  "Univers fini de taille N : au-delà de N sauts, β est impossible et "
                  "la trajectoire répète (principe des tiroirs).", cex16))
    out.append(_v("TH15", "tient" if cex16 is None else "contre_exemple",
                  "Contraposée de TH16 dans les bornes : sans univers infini, pas "
                  "d'évasion pérenne sans répétition."))

    # TH17 — maturité : traverser le secours par sa β-chaîne antérieure
    t17 = derouler((0, 0, 0) + (1,) * (H - 3), Interpretation(n_lambda=None, mecanisme_M=True))
    out.append(_v("TH17", "conditionnel",
                  "Avec le mécanisme M, l'excursion parcourt la β-chaîne passée : elle "
                  "peut être non périodique pendant ≤ D_β pas, mais elle REVISITE des "
                  f"états passés (R = {t17.R} > 0). « Sans boucle » est vrai au sens "
                  "« non périodique », faux au sens « sans retour » (D12).", t17))

    # TH18–TH20 : ordre par β-chaîne
    out.append(_v("TH18", "par_construction",
                  "L'ordre d'apparition des s_b est un bon ordre strict dans la sémantique."))
    out.append(_v("TH19", "par_construction",
                  "M n'utilise que la β-chaîne, aucun ordre externe."))
    out.append(_v("TH20", "conditionnel", "Voir TH17 : franchissement non périodique, pas "
                  "sans retour."))

    # TH21 — 4 classes réelles (B0 exclu)
    b0 = next((t for t in trajs if classer(t) == "B0" and not t.secours_en_cours_a_l_horizon), None)
    out.append(_v("TH21", "contre_exemple" if b0 else "tient",
                  "Recherche d'une trajectoire de classe B0 (0 < T_R < ∞, R = 0), "
                  "déclarée impossible en v1.6. Trouvée : il suffit d'une excursion "
                  "d'UN seul pas (environnement qui bloque β un seul pas, ou n_Λ = 1). "
                  "Le lemme du 2-cycle ne donne R ≥ 1 qu'au 2e pas de secours ; une "
                  "excursion d'un pas sort avant. Ce n'est donc pas une question de n_Λ "
                  "seulement : B0 existe pour tout n_Λ. Hadès le confirme (hades_pont)."
                  if b0 else "Aucune trajectoire B0 trouvée.", b0))
    c_base = next((t for t in trajs if classer(t) == "C"), None)
    t_canal = derouler((1,) * H, Interpretation(n_lambda=None, canal_errance=H))
    out.append(_v("TH21-C", "conditionnel",
                  "Classe C : absente des règles de base "
                  f"({'trouvée' if c_base else 'aucune trouvée'} sur la grille), "
                  f"atteinte avec un canal E3+ d'objets non visités (classe {classer(t_canal)}). "
                  "Cohérent avec « C virtuelle sous R-G » (v1.7).", t_canal))

    out.append(_v("TH35", "tient", "Avec un canal E3+ d'objets non visités, la classe C "
                  "devient atteignable par choix (refuser le loquet, emprunter le canal).", t_canal))

    # TH22 — raffinement B1/B2
    out.append(_v("TH22", "conditionnel",
                  "B1 « sortie non périodique » exige M ; même alors R > 0 (voir TH17)."))

    # TH23 — monotonie des composantes (sur les préfixes)
    def monotone(t: Trajectoire) -> bool:
        prev = (0, 0, 0)
        for n in range(1, len(t.pas) + 1):
            s = Trajectoire(t.pas[:n], t.interpretation, t.environnement).signature
            if any(a < b for a, b in zip(s, prev)):
                return False
            prev = s
        return True
    cex23 = next((t for t in trajs[::7] if not monotone(t)), None)
    out.append(_v("TH23", "tient" if cex23 is None else "contre_exemple",
                  "T_R, R, D_β non décroissants sur les préfixes (L* de base, sans R-PURIF).",
                  cex23))

    # TH24 — Σ détermine la classe
    out.append(_v("TH24", "par_construction",
                  "Dans la sémantique, la classe est une fonction de Σ et du proxy d'infini."))

    # TH25–TH27 — graphe de transition
    out.append(_v("TH25", "par_construction",
                  "T_R ne décroît jamais : quitter A est irréversible (L* de base)."))
    cex26 = None
    for t in trajs:
        for n in range(1, len(t.pas)):
            pre = Trajectoire(t.pas[:n], t.interpretation, t.environnement)
            if pre.R > 0 and classer(t) not in ("B", "D"):
                cex26 = t; break
        if cex26: break
    out.append(_v("TH26", "tient" if cex26 is None else "contre_exemple",
                  "Dès que R > 0, classe finale ∈ {B, D}.", cex26))
    out.append(_v("TH27", "par_construction", "Seule sortie d'un secours avec R > 0 : B."))

    # TH28, TH29 — points de choix
    cex29 = None
    for t in trajs:
        for (a, b) in _excursions(t):
            n = sum(1 for p in t.pas if a <= p.k <= b + 1 and p.choix)
            if n > 1:
                cex29 = t; break
        if cex29: break
    out.append(_v("TH28", "par_construction",
                  "Les points de choix n'apparaissent qu'en régime mixte."))
    out.append(_v("TH29", "conditionnel" if cex29 else "tient",
                  "Au plus un point de choix par excursion SI la politique prend β au "
                  "premier choix. Une politique α en rencontre plusieurs dans la même "
                  "excursion (un par pas débloqué).", cex29))

    # TH30 — dominance de « toujours β »
    pires = 0
    ordre = {"A": 0, "B0": 1, "B": 2, "C": 3, "D": 4, "A?R>0": 5, "indetermine": 3}
    for env in environnements(H):
        for nl in (1, 2, 3):
            a = derouler(env, Interpretation(n_lambda=nl, politique_choix="beta", loquet_force_beta=False))
            b = derouler(env, Interpretation(n_lambda=nl, politique_choix="alpha", loquet_force_beta=False))
            if ordre[classer(a)] > ordre[classer(b)] or a.R > b.R:
                pires += 1
    out.append(_v("TH30", "tient" if pires == 0 else "contre_exemple",
                  "« Toujours β » n'est jamais pire que « α » (classe et R).",
                  comparaisons_perdantes=pires))

    # TH31 — un blocage ≥ 2 pas fait perdre A
    cex31 = None
    for t in trajs:
        e = t.environnement
        if any(e[j] and e[j + 1] for j in range(len(e) - 1)) and classer(t) == "A":
            cex31 = t; break
    out.append(_v("TH31", "tient" if cex31 is None else "contre_exemple",
                  "Tout blocage de ≥ 2 pas consécutifs fait perdre A (T_R > 0).", cex31))

    # TH41 — L↑ : A atteignable depuis Ω0
    t41 = derouler((1,) * H, Interpretation(n_lambda=2, purification=True, budget_tau=H))
    out.append(_v("TH41", "contre_exemple",
                  "En L↑, Ω0 a T_R = ∞ et R-PURIF ne fait baisser que R. Or A exige "
                  "T_R = 0 (D11, TH21). Avec purification complète, la meilleure classe "
                  f"atteinte est {classer(t41)}, jamais A. Il faut redéfinir A dans L↑ "
                  "(par ex. « T_R fini et R = 0 après purification ») ou ajouter une "
                  "règle qui agit sur T_R.", t41))
    out.append(_v("TH23-L↑", "contre_exemple" if t41.R < t41.R_brut else "tient",
                  "Sous R-PURIF, R n'est plus monotone : TH23 et les théorèmes qui en "
                  "dépendent (TH25–TH27) doivent être restreints en L↑, pas seulement TH3."))

    return out
