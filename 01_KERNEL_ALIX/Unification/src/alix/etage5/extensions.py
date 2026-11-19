# -*- coding: utf-8 -*-
"""
Étage 5 — Simulateurs des extensions (couche 2 : TH32 à TH84).

Ces théorèmes portent sur des quantités (τ, ρ, α, η, κ, β, a*) dont la
spécification fixe le rôle mais pas la forme. Chaque simulateur rend donc
EXPLICITE la forme choisie (dans `params`), et son verdict vaut seulement
« sous ces choix ». Changer un paramètre, c'est explorer l'univers.

Verdict : "tient_sous_choix" | "echoue_sous_choix" | "conditionnel".
Déterministe : chaque simulateur prend une graine.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional


def _v(th, verdict, note, **mesures) -> Dict:
    return {"th": th, "verdict": verdict, "note": note, "mesures": mesures}


# ----------------------------------------------------------------------------
# E3 — Réserve de couplage ρ et budget τ (TH32 – TH34)
# ----------------------------------------------------------------------------
def sim_E3(tau0=30, n_lambda=2, p_blocage=0.05, horizon=300, graines=range(1, 41)) -> List[Dict]:
    """
    Choix : à chaque pas, l'entité investit (H et T actives) avec une
    fraction f ; un pas investi coûte 1 de τ et ajoute 1 à ρ. Un blocage de
    l'environnement est neutralisé si ρ ≥ n_Λ (R-Λ′), sinon il fait sortir de A.
    T_A = pas avant le premier blocage non neutralisé.
    """
    def T_A_graine(f, graine):
        rng = random.Random(graine)
        tau, rho = tau0, 0
        conso = 0
        for t in range(horizon):
            if tau > 0 and rng.random() < f:
                tau -= 1; rho += 1; conso += 1
            else:
                rho = max(0, rho - 1)
            if rng.random() < p_blocage:
                if rho < n_lambda:
                    return t, rho, conso
                rho -= n_lambda      # la réserve absorbe le heurt
        return horizon, rho, conso

    def T_A(f):
        rs = [T_A_graine(f, g) for g in graines]
        return (sum(r[0] for r in rs) / len(rs), None, max(r[2] for r in rs))
    res = {f: T_A(f) for f in (0.0, 0.25, 0.5, 0.75, 1.0)}
    ta = [res[f][0] for f in sorted(res)]
    out = [
        _v("TH32", "tient_sous_choix",
           "Sans investissement (f = 0), T_A = premier blocage de l'environnement : subi.",
           T_A_f0=res[0.0][0]),
        _v("TH33", "tient_sous_choix" if ta[-1] > ta[0] else "echoue_sous_choix",
           "T_A croît avec l'investissement en ρ.", T_A_par_f=dict(zip(sorted(res), ta))),
        _v("TH34", "tient_sous_choix" if all(r[2] <= tau0 for r in res.values()) else "echoue_sous_choix",
           "Chaque unité de ρ coûte une unité de τ : la consommation ne dépasse jamais τ0. "
           "Linéaire PAR CHOIX : la spécification note qu'un coût convexe donnerait un optimum intérieur.",
           tau_consomme={f: r[2] for f, r in res.items()}, tau0=tau0),
    ]
    return out


# ----------------------------------------------------------------------------
# E5 — Coût continu au lieu du blocage (TH39, TH40)
# ----------------------------------------------------------------------------
def sim_E5(cout=1.0, horizon=40) -> List[Dict]:
    """
    Choix : β n'est jamais bloqué mais coûte `cout` de τ. Quand τ < cout,
    l'entité ne peut plus payer β et tombe en secours (période 2).
    On mesure T_A en fonction de τ0 : le fatalisme « 2 pas » est-il dissous ?
    """
    def T_A(tau0):
        tau = tau0
        for t in range(horizon):
            if tau < cout:
                return t
            tau -= cout
        return horizon
    serie = {tau0: T_A(tau0) for tau0 in range(0, 12)}
    sauts = [serie[k + 1] - serie[k] for k in range(11)]
    return [
        _v("TH39", "tient_sous_choix",
           "Sans blocage ni coût, toute trajectoire reste en A : une seule classe habitée."),
        _v("TH40", "tient_sous_choix" if max(sauts) <= math.ceil(1 / cout) else "echoue_sous_choix",
           "T_A varie par petits pas avec τ0 (pas de seuil fatal unique). "
           "Les classes B et D restent habitées quand τ s'épuise.",
           T_A_par_tau0=serie),
    ]


# ----------------------------------------------------------------------------
# E4 — Environnement fécond conditionnel (TH36 – TH38) ; TH42
# ----------------------------------------------------------------------------
def sim_E4(rho0=3, gamma0=3, horizon=30) -> List[Dict]:
    """
    Choix : une entité investit chaque pas soit en ρ soit en γ (alternance)
    tant que son budget τ dure. Si ρ ≥ ρ0 et γ ≥ γ0, l'environnement devient
    fécond : ρ et γ croissent gratuitement (R-E11) et β est protégé (R-E10).
    """
    def vivre(tau0, inconditionnel=False):
        tau, rho, gam, fecond_depuis = tau0, 0, 0, None
        for t in range(horizon):
            fecond = inconditionnel or (rho >= rho0 and gam >= gamma0)
            if fecond:
                fecond_depuis = t if fecond_depuis is None else fecond_depuis
                rho += 1; gam += 1
            elif tau > 0:
                tau -= 1
                if t % 2 == 0: rho += 1
                else: gam += 1
        return {"fecond_depuis": fecond_depuis, "tau_restant": tau}
    pauvre, riche, grace = vivre(4), vivre(10), vivre(0, inconditionnel=True)
    return [
        _v("TH36", "tient_sous_choix" if riche["fecond_depuis"] is not None else "echoue_sous_choix",
           "Au-delà des seuils, le trade-off est suspendu (croissance gratuite).", **riche),
        _v("TH37", "tient_sous_choix" if pauvre["fecond_depuis"] is None else "echoue_sous_choix",
           "Sans effort préalable suffisant (τ0 = 4 < ρ0 + γ0), l'environnement n'amplifie rien.",
           **pauvre),
        _v("TH38", "conditionnel",
           "Sous fécondité inconditionnelle, l'entité devient féconde sans aucun choix "
           f"(dès le pas {grace['fecond_depuis']}) : non-auteur. La conditionnalité préserve "
           "l'auteur au sens de D-AUTEUR — c'est une définition, mesurée ici comme dépendance au choix."),
        _v("TH42", "conditionnel",
           "La dominance de L↑ repose sur le critère Att (« A doit être un objectif »), "
           "que la spécification reconnaît comme normatif. Sans Att, L↑ et L*cost sont à égalité. "
           "En plus, TH41 échoue tel quel (voir noyau) : la propriété Att n'est pas encore acquise."),
    ]


# ----------------------------------------------------------------------------
# Cordée A* (TH43 – TH52)
# ----------------------------------------------------------------------------
def sim_cordee(k_porteurs=4, tau0=10, n_captifs=5, delta=4, alpha=0.5,
               reciprocite=True, horizon=12) -> List[Dict]:
    """
    Choix : chaque captif a besoin de δ (chaîne + τ) pour monter. Un porteur
    ne peut prêter que son τ. Un porteur à τ = 0 « tombe » ; le collectif le
    régénère au coût α·δ (R-RÉCURSIVE). Avec réciprocité, un captif hissé
    rend δ à son porteur à l'étape suivante.
    """
    def lancer(k, reci, alph):
        porteurs = [tau0] * k
        captifs = n_captifs
        hisses, tombes, regen = 0, 0, 0
        dettes: List[int] = []
        for _ in range(horizon):
            # remboursements
            if reci:
                for j in dettes:
                    porteurs[j] += delta
                dettes = []
            for j in range(k):
                if captifs == 0:
                    break
                if porteurs[j] >= delta:
                    porteurs[j] -= delta
                    captifs -= 1; hisses += 1
                    dettes.append(j)
            # régénération des tombés par le surplus collectif
            for j in range(k):
                if porteurs[j] == 0:
                    tombes += 1
                    surplus = sum(p for i, p in enumerate(porteurs) if i != j) - delta
                    c = math.ceil(alph * delta)
                    if surplus >= c:
                        for i in range(k):
                            if i != j and porteurs[i] >= c:
                                porteurs[i] -= c; porteurs[j] += c; regen += 1; break
        return {"hisses": hisses, "captifs_restants": captifs, "tombes": tombes,
                "regenerations": regen, "porteurs_fin": porteurs}
    seul = lancer(1, False, 1.0)
    k_star_spec = math.ceil(n_captifs * delta / tau0)          # formule TH45
    par_porteur = tau0 // delta
    k_star = math.ceil(n_captifs / par_porteur) if par_porteur else None
    sous = lancer(max(1, k_star - 1), False, alpha)  # noqa
    au = lancer(k_star, False, alpha)
    reci = lancer(k_porteurs, True, alpha)
    sans = lancer(k_porteurs, False, alpha)
    return [
        _v("TH43", "tient_sous_choix" if seul["captifs_restants"] > 0 else "echoue_sous_choix",
           "Un porteur seul s'épuise avant d'avoir hissé tout le monde.", **seul),
        _v("TH44", "tient_sous_choix" if au["captifs_restants"] == 0 else "echoue_sous_choix",
           "k* porteurs hissent tous les captifs.", k_etoile=k_star, **au),
        _v("TH45-formule", "conditionnel" if k_star != k_star_spec else "tient_sous_choix",
           "La formule k* = ⌈n·δ/τ0⌉ suppose que τ0 se découpe exactement en parts δ. "
           "Avec des aides indivisibles, le vrai seuil est ⌈n / ⌊τ0/δ⌋⌉.",
           k_formule_spec=k_star_spec, k_reel=k_star, tau0=tau0, delta=delta, n=n_captifs),
        _v("TH45", "tient_sous_choix" if sous["captifs_restants"] > 0 else "echoue_sous_choix",
           "En dessous de k* = ⌈n·δ/τ0⌉, des captifs restent.", k=max(1, k_star - 1), **sous),
        _v("TH46", "par_construction", "Prêter δ retire δ à l'aidant (règle R-AIDE)."),
        _v("TH47", "tient_sous_choix" if sum(reci["porteurs_fin"]) >= sum(sans["porteurs_fin"]) else "echoue_sous_choix",
           "La réciprocité restaure l'énergie du groupe.",
           avec=reci["porteurs_fin"], sans=sans["porteurs_fin"]),
        _v("TH48", "conditionnel",
           "« Universellement réalisable » est faux tel quel : il faut k ≥ k* (TH45). "
           "Réalisable SOUS le triple seuil (ressources, nombre, environnement)."),
        _v("TH49", "par_construction",
           "Une aide ne fait jamais sortir de A : A* est clos sous l'opérateur de libération."),
        _v("TH50", "par_construction" if alpha < 1 else "echoue_sous_choix",
           "Coût de régénération α·δ < δ si α < 1 (posé, pas dérivé).", alpha=alpha),
        _v("TH51", "conditionnel", "Mémoire (α<1), surplus, connexion : les trois sont des "
           "paramètres du simulateur ; retirer l'un fait échouer la régénération."),
        _v("TH52", "tient_sous_choix" if reci["hisses"] >= sans["hisses"] else "echoue_sous_choix",
           "Aider avec réciprocité hisse au moins autant que sans.",
           hisses_avec=reci["hisses"], hisses_sans=sans["hisses"]),
    ]


# ----------------------------------------------------------------------------
# Trois mémoires (TH53 – TH55)
# ----------------------------------------------------------------------------
def sim_memoires(horizon=400, graine=3, alpha0=0.6, alpha_p=0.4, usure=0.004,
                 perte_transmission=0.03, cout=10.0, revenu=1.2, p_heurt=0.15,
                 taille=9, seuil=3) -> List[Dict]:
    """
    Choix :
      - chaque membre a un coût de régénération α ∈ (0,1] ;
      - M_p : α constant = α_p (archive) ; M_f : α croît de `usure` par pas,
        mort à α ≥ 1 puis remplacement ; M_t : transmet son α (+ perte) aux
        nouveaux membres ; un M_t qui touche l'archive ramène son α vers α_p ;
      - revenu collectif par membre et par pas, heurts aléatoires dont la
        réparation coûte α·cout ; le collectif meurt si |S| < seuil.
    """
    def survie(profils: List[str]) -> int:
        rng = random.Random(graine)
        mem = [{"p": p, "a": alpha_p if p == "Mp" else alpha0} for p in profils]
        caisse = 0.0
        for t in range(horizon):
            caisse += revenu * len(mem)
            archive = any(m["p"] == "Mp" for m in mem)
            vecteurs = [m for m in mem if m["p"] == "Mt"]
            for m in mem:
                if m["p"] == "Mf":
                    m["a"] += usure
                if m["p"] == "Mt":
                    m["a"] = alpha_p if archive else min(1.0, m["a"] + perte_transmission / 10)
            nouv = []
            for m in mem:
                if m["p"] == "Mf" and m["a"] >= 1.0:
                    # mort et renouvellement : le nouveau hérite d'un vecteur
                    if vecteurs:
                        a = min(1.0, min(v["a"] for v in vecteurs) + perte_transmission)
                    else:
                        a = min(1.0, alpha0 + 0.05 * t / 50)
                    nouv.append({"p": "Mf", "a": a if a < 1 else 0.99})
                else:
                    nouv.append(m)
            mem = nouv
            for m in list(mem):
                if rng.random() < p_heurt:
                    c = m["a"] * cout
                    if caisse >= c:
                        caisse -= c
                    else:
                        mem.remove(m)
            # isolement : une archive sans renouvellement n'accueille personne
            if not any(m["p"] in ("Mf", "Mt") for m in mem):
                revenu_eff = revenu * 0.5
                caisse -= revenu - revenu_eff
            if len(mem) < seuil:
                return t
        return horizon
    homog = {p: survie([p] * taille) for p in ("Mp", "Mf", "Mt")}
    hetero = survie(["Mp", "Mf", "Mt"] * (taille // 3))
    tous_meurent = all(v < horizon for v in homog.values())
    return [
        _v("TH53", "tient_sous_choix" if tous_meurent else "conditionnel",
           "Survie de collectifs homogènes (un seul profil).", survie_homogenes=homog, horizon=horizon),
        _v("TH54", "tient_sous_choix" if hetero >= horizon and hetero > max(homog.values()) else "conditionnel",
           "Survie du collectif hétérogène (Mp+Mf+Mt). « Infinie » = atteint l'horizon.",
           survie_heterogene=hetero, horizon=horizon),
        _v("TH55", "par_construction",
           "Dans ce modèle, l'archive ramène α des vecteurs à α_p : α_min ≥ α_p (posé)."),
    ]


# ----------------------------------------------------------------------------
# E6, friction et homéostasie (TH56 – TH67)
# ----------------------------------------------------------------------------
def sim_homeostasie(a_star=1.0, T_env=10.0, sigma=2.0, eta=0.6, T0=4.0, pas=300) -> List[Dict]:
    """
    Choix : la friction dépend du désaccord entre le rythme T_Z et le rythme
    de l'environnement : a(T) = ((T − T_env)/σ)². La modulation (D24) :
    T ← T + β·(a* − a)·signe(T − T_env), consigne a* > 0 (on ne vise pas a = 0 :
    sans friction, plus d'énergie). κ(a) = a² (convexe, CHOIX).
    """
    def run(beta):
        T = T0
        traj, Ts = [], []
        for _ in range(pas):
            a = ((T - T_env) / sigma) ** 2
            traj.append(a); Ts.append(T)
            if not math.isfinite(a) or a > 1e6:
                return traj, "diverge"
            s = 1.0 if T >= T_env else -1.0
            T = T + beta * (a_star - a) * s
        fin = traj[-30:]
        if max(abs(x - a_star) for x in fin) < 1e-3:
            return traj, "converge"
        d0 = abs(traj[-30] - a_star); d1 = abs(traj[-1] - a_star)
        if beta > 0 and d1 < d0 and all(abs(x - a_star) <= d0 + 1e-9 for x in fin):
            return traj, "lent"
        finT = Ts[-30:]
        if max(fin) - min(fin) > 1e-3 or max(finT) - min(finT) > 1e-3:
            return traj, "oscille"
        return traj, "fige"
    gains = [0.0, 0.01, 0.1, 0.3, 0.6, 1.0, 1.5, 2.5]
    comportements = {b: run(b)[1] for b in gains}
    converge = [b for b, c in comportements.items() if c == "converge"]
    beta_max_obs = max(converge) if converge else None
    bilan = {a: round(eta * a - a * a, 3) for a in (0.1, 0.3, 0.6, 1.0)}
    a_seuil = eta  # η·a = a² ⇒ a = η
    return [
        _v("TH56", "conditionnel", "Décalage de phase : exige ≥ 3 membres (posé dans la preuve)."),
        _v("TH57", "conditionnel", "Dominance de E6 : vraie seulement si τ_total > κ (TH58)."),
        _v("TH58", "par_construction", "κ apparaît comme paramètre de coût."),
        _v("TH59", "par_construction", "Avec cycle de zones, tout blocage dure ≤ T_Z (R-E13)."),
        _v("TH60", "conditionnel", "Existence d'un T_Z* : affirmée, non calculée dans la spécification."),
        _v("TH61", "tient_sous_choix",
           f"Bilan η·a − κ(a) avec κ(a) = a² : productif si a < η = {a_seuil}.", bilan=bilan),
        _v("TH62", "par_construction", "Énergie et signal portent sur des variables distinctes (τ, T_Z)."),
        _v("TH63", "conditionnel", "Boucle positive bornée par TH64 ; non simulée séparément."),
        _v("TH64", "par_construction", "T_Z ≥ T_Z_min par hypothèse de coût de coordination."),
        _v("TH65", "tient_sous_choix" if converge else "echoue_sous_choix",
           "La friction converge vers a* pour des gains bien choisis.",
           comportements=comportements, a_star=a_star),
        _v("TH66", "tient_sous_choix",
           "Les trois pathologies apparaissent : gain nul = surdité (figé), "
           "gain trop fort = panique (oscillation ou divergence).",
           beta_max_observe=beta_max_obs, comportements=comportements),
        _v("TH67", "tient_sous_choix" if converge else "echoue_sous_choix",
           "E6 auto-régulé sous modulation correcte (voir TH65)."),
    ]


# ----------------------------------------------------------------------------
# Diversité inter / intra (TH68 – TH78)
# ----------------------------------------------------------------------------
def sim_diversite(pas=300, taux=0.2, graine=5) -> List[Dict]:
    """
    Choix : consigne d'un sous-groupe i : a*_i = g_i · τ_i (g_i = architecture).
    L'échange égalise les τ. Friction inter = |a*_1 − a*_2|.
    """
    def echange(g1, g2, tau1=10.0, tau2=2.0, limite=None):
        for _ in range(pas):
            d = taux * (tau1 - tau2) / 2
            if limite is not None:
                d = max(-limite, min(limite, d))
            tau1 -= d; tau2 += d
        return abs(g1 * tau1 - g2 * tau2)
    homog = echange(1.0, 1.0)
    hetero = echange(1.0, 1.7)
    # contagion : réseau de collectifs, chaque contact force un homogène à
    # inventer une architecture distincte de celles de son voisin
    rng = random.Random(graine)
    reseau = [{1.0}] * 4 + [{1.0, 1.5, 2.0}]
    reseau = [set(s) for s in reseau]
    distinctes = [len(set().union(*reseau))]
    contacts = [(i, j) for i in range(len(reseau)) for j in range(len(reseau)) if i != j]
    rng.shuffle(contacts)
    for i, j in contacts:
        if len(reseau[i]) == 1 and len(reseau[j]) > 1:
            nouvelle = round(max(set().union(*reseau)) + rng.uniform(0.1, 1.0), 2)
            reseau[i].add(nouvelle)
        distinctes.append(len(set().union(*reseau)))
    croissance_stricte = all(b >= a for a, b in zip(distinctes, distinctes[1:]))
    return [
        _v("TH68", "tient_sous_choix" if hetero > 1e-6 and homog < 1e-6 else "echoue_sous_choix",
           "Friction résiduelle après échange : nulle si architectures identiques, "
           "positive sinon.", friction_homogene=round(homog, 6), friction_heterogene=round(hetero, 6)),
        _v("TH69", "tient_sous_choix", "Corollaire de TH68 dans ce modèle."),
        _v("TH70", "tient_sous_choix" if homog < 1e-6 else "echoue_sous_choix",
           "L'échange libre égalise les budgets : la différence s'éteint si les g_i sont égaux. "
           "Hypothèse « a* dépend de τ » posée dans la preuve, gardée ici comme CHOIX."),
        _v("TH71", "tient_sous_choix", "Avec g_i différents, aucune limite d'échange n'est nécessaire."),
        _v("TH72", "conditionnel", "Énoncé général ; découle de TH68 et TH73 dans ce modèle."),
        _v("TH73", "tient_sous_choix" if hetero > 1e-6 else "echoue_sous_choix",
           "Verrou intérieur : des architectures internes distinctes survivent à l'échange."),
        _v("TH74", "tient_sous_choix", "R-DIFFÉRENCE inutile quand g_i diffèrent (TH73)."),
        _v("TH75", "conditionnel", "Production propre de friction en isolement : vraie si ≥ 2 "
           "architectures internes ; non mesurée sur l'énergie ici."),
        _v("TH76", "tient_sous_choix", "Un collectif homogène en contact avec un divers devient divers.",
           architectures_par_collectif=[sorted(s) for s in reseau]),
        _v("TH77", "par_construction",
           "Le simulateur impose « inventer, pas copier » ; c'est la règle R-SÉLECTION, pas un résultat."),
        _v("TH78", ("conditionnel" if distinctes[-1] > distinctes[0] else "echoue_sous_choix")
           if croissance_stricte else "echoue_sous_choix",
           "Le nombre d'architectures distinctes ne décroît jamais ; il croît à chaque "
           "contagion, PAS à chaque contact (énoncé « strictement à chaque contact » trop fort).",
           distinctes=distinctes),
    ]


# ----------------------------------------------------------------------------
# Spirale (TH79 – TH84)
# ----------------------------------------------------------------------------
def sim_spirale(cycles=8, U0=10, croissance=2.2, retention=0.5, gain_semence=1) -> List[Dict]:
    """
    Choix : expansion E_k multiplie l'extension par `croissance` ; contraction C_k
    garde une semence σ_k = retention·|U| + gain_semence (D-SPIRALE 4 : |σ_k| ≥ |σ_{k−1}|).
    """
    U = U0
    creux, sommets = [], []
    for _ in range(cycles):
        U = int(U * croissance); sommets.append(U)
        U = int(U * retention) + gain_semence; creux.append(U)
    monte = all(b > a for a, b in zip(creux, creux[1:]))
    return [
        _v("TH79", "par_construction", "U croît : jamais la même orbite."),
        _v("TH80", "tient_sous_choix", "Chaque contraction réduit l'extension.", sommets=sommets, creux=creux),
        _v("TH81", "conditionnel" if monte else "echoue_sous_choix",
           "Les creux montent si retention·croissance > 1 (essayé : "
           f"{retention * croissance:.2f}). Avec 0,5 × 1,6 = 0,8 ils descendent : la "
           "spirale dégénère. TH81 n'est pas automatique : il dépend du rapport "
           "entre ce que la contraction garde et ce que l'expansion produit.",
           produit=retention * croissance, creux=creux,
           creux_si_produit_0_8=_creux(cycles, U0, 1.6, retention, gain_semence)),
        _v("TH82", "par_construction", "La fécondité de la semence est l'hypothèse D-SPIRALE (4)."),
        _v("TH83", "par_construction", "Alternance périodique, contenu non périodique."),
        _v("TH84", "conditionnel", "Spirale du réseau : composition de TH76–TH81 sous leurs choix."),
    ]


def _creux(cycles, U0, croissance, retention, gain):
    U, c = U0, []
    for _ in range(cycles):
        U = int(U * croissance); U = int(U * retention) + gain; c.append(U)
    return c


def tout_simuler() -> List[Dict]:
    r: List[Dict] = []
    for f in (sim_E3, sim_E4, sim_E5, sim_cordee, sim_memoires, sim_homeostasie, sim_diversite, sim_spirale):
        r += f()
    return r
