"""
Simulation de reference pour le papier :
« Consensus ancre sur un complexe simplicial — analyse critique et correction
  d'une architecture de consensus distribue sans maitre (SGTD) »

Christian Duguay — Atelier Kairos, Rimouski — 2026-10-20

Quatre experiences, toutes deterministes (graine fixe), numpy pur :
  E1  Dynamique de consensus : Laplacien pur / + ancrage / + repulsion « cross-talk » (SGTD tel que propose)
  E2  Partition (split-brain) : surveillance de lambda_2 et reecriture longue portee
  E3  Detection d'hallucination : beta_2 (deux variantes) vs beta_0 reduit du complexe conifie
  E4  Arbitrage : fonction de cout telle qu'ecrite (signe -), signe corrige non borne, forme bornee verifiee

Sorties : resultats.json + fig1..fig4 (PNG) dans le dossier du script.
Usage :  python simulation_simplexe.py
"""

import itertools
import json
import os
import time
from math import comb

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 20261020
ICI = os.path.dirname(os.path.abspath(__file__))
D = 8  # dimension de l'etat latent partage


# ---------------------------------------------------------------- outils graphe

def graphe_geometrique(n, rayon, rng, essais=500):
    """Graphe geometrique aleatoire connexe dans [0,1]^2."""
    for _ in range(essais):
        p = rng.random((n, 2))
        dist = np.linalg.norm(p[:, None, :] - p[None, :, :], axis=-1)
        A = ((dist < rayon) & (dist > 0)).astype(float)
        if fiedler(A) > 1e-9:
            return A
    raise RuntimeError("graphe connexe introuvable")


def laplacien(A):
    return np.diag(A.sum(1)) - A


def fiedler(A):
    return float(np.linalg.eigvalsh(laplacien(A))[1])


def composantes(A):
    n = len(A)
    vu, comps = np.zeros(n, bool), []
    for s in range(n):
        if vu[s]:
            continue
        pile, comp = [s], []
        vu[s] = True
        while pile:
            u = pile.pop()
            comp.append(u)
            for v in np.nonzero(A[u])[0]:
                if not vu[v]:
                    vu[v] = True
                    pile.append(v)
        comps.append(comp)
    return comps


# ---------------------------------------------------------------- E1 dynamique

def consensus(A, x0, capteurs, x_vrai, rng, T=300, kappa=0.0, repulsion=False,
              theta=0.9, sigma=0.1):
    """
    x_i <- x_i + eta * sum_j W_ij (x_j - x_i) + kappa * a_i (y_i - x_i)
    W_ij = A_ij, ou -A_ij si repulsion et cos(dx_i, dx_j) > theta au pas precedent
    (lecture litterale de la regle « cross-talk » de la proposition SGTD).
    """
    n = len(A)
    eta = 0.5 / A.sum(1).max()
    x = x0.copy()
    dx_prec = np.zeros_like(x)
    rmse, desaccord, actives = [], [], []
    diverge = False
    for _ in range(T):
        W = A.copy()
        n_act = 0
        if repulsion:
            nrm = np.linalg.norm(dx_prec, axis=1, keepdims=True)
            u = np.divide(dx_prec, nrm, out=np.zeros_like(dx_prec), where=nrm > 1e-12)
            C = u @ u.T
            masque = (C > theta) & (A > 0)
            W[masque] = -A[masque]
            n_act = int(masque.sum() // 2)
        lap = W @ x - W.sum(1)[:, None] * x
        y = x_vrai + sigma * rng.standard_normal(x.shape)
        dx = eta * lap + kappa * capteurs[:, None] * (y - x)
        x = x + dx
        dx_prec = dx
        if not np.isfinite(x).all() or np.abs(x).max() > 1e6:
            diverge = True
            break
        rmse.append(float(np.sqrt(((x - x_vrai) ** 2).sum(1).mean())))
        desaccord.append(float(np.sqrt(((x - x.mean(0)) ** 2).sum(1).mean())))
        actives.append(n_act)
    return dict(rmse=rmse, desaccord=desaccord, liens_repulsifs=actives, diverge=diverge)


def experience_1(rng):
    n = 30
    A = graphe_geometrique(n, 0.35, rng)
    x_vrai = rng.standard_normal(D)
    biais = rng.standard_normal(D)
    biais *= 1.0 / np.linalg.norm(biais)  # biais a priori partage, norme 1
    x0 = x_vrai + biais + 0.5 * rng.standard_normal((n, D))
    capteurs = np.zeros(n)
    capteurs[rng.choice(n, 9, replace=False)] = 1.0  # 30 % de noeuds ancres

    variantes = {
        "laplacien_pur": dict(kappa=0.0, repulsion=False),
        "sgtd_repulsion_sans_ancre": dict(kappa=0.0, repulsion=True),
        "laplacien_ancre": dict(kappa=0.2, repulsion=False),
        "sgtd_repulsion_ancre": dict(kappa=0.2, repulsion=True),
    }
    res = {}
    for nom, kw in variantes.items():
        r = consensus(A, x0, capteurs, x_vrai, np.random.default_rng(SEED + 1), **kw)
        res[nom] = r
    # balayage du seuil theta pour la repulsion
    balayage = {}
    for theta in [0.5, 0.7, 0.9, 0.95, 0.99]:
        r = consensus(A, x0, capteurs, x_vrai, np.random.default_rng(SEED + 1),
                      kappa=0.2, repulsion=True, theta=theta)
        balayage[str(theta)] = dict(
            rmse_final=r["rmse"][-1] if r["rmse"] else None,
            desaccord_final=r["desaccord"][-1] if r["desaccord"] else None,
            diverge=r["diverge"],
            pas_executes=len(r["rmse"]),
            liens_repulsifs_moyens_50_derniers=float(np.mean(r["liens_repulsifs"][-50:])) if r["liens_repulsifs"] else None,
        )
    res["balayage_theta"] = balayage
    res["meta"] = dict(n=n, d=D, capteurs=int(capteurs.sum()), aretes=int(A.sum() // 2),
                       lambda2=fiedler(A), norme_biais=1.0)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for nom in variantes:
        ax[0].semilogy(res[nom]["rmse"], label=nom)
        ax[1].semilogy(np.maximum(res[nom]["desaccord"], 1e-6), label=nom)
    ax[0].set_title("Erreur a la verite (RMSE)")
    ax[1].set_title("Desaccord inter-noeuds")
    for a in ax:
        a.set_xlabel("iteration")
        a.legend(fontsize=8)
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(ICI, "fig1_consensus.png"), dpi=130)
    plt.close(fig)
    return res


# ---------------------------------------------------------------- E2 partition

def experience_2(rng):
    nA = nB = 15
    A1 = graphe_geometrique(nA, 0.45, rng)
    A2 = graphe_geometrique(nB, 0.45, rng)
    n = nA + nB
    A = np.zeros((n, n))
    A[:nA, :nA] = A1
    A[nA:, nA:] = A2
    ponts = [(0, nA), (1, nA + 1)]
    for i, j in ponts:
        A[i, j] = A[j, i] = 1
    x_vrai = rng.standard_normal(D)
    biais = rng.standard_normal(D)
    biais /= np.linalg.norm(biais)
    x0 = x_vrai + 0.3 * rng.standard_normal((n, D))
    x0[nA:] += 1.5 * biais  # le cluster B demarre biaise et n'a aucun capteur
    capteurs = np.zeros(n)
    capteurs[rng.choice(nA, 5, replace=False)] = 1.0

    T, t_coupure, eps = 400, 30, 1e-3
    sorties = {}
    for reecriture in (False, True):
        r = np.random.default_rng(SEED + 2)
        Ad = A.copy()
        x = x0.copy()
        l2, errB = [], []
        evenements = []
        for t in range(T):
            if t == t_coupure:
                for i, j in ponts:
                    Ad[i, j] = Ad[j, i] = 0
            lam2 = fiedler(Ad)
            if reecriture and lam2 < eps:
                comps = composantes(Ad)
                for c1, c2 in zip(comps[:-1], comps[1:]):
                    i, j = int(r.choice(c1)), int(r.choice(c2))
                    Ad[i, j] = Ad[j, i] = 1  # lien longue portee (canal cloud)
                    evenements.append(dict(t=t, lien=[i, j]))
                lam2 = fiedler(Ad)
            l2.append(lam2)
            eta = 0.5 / Ad.sum(1).max()
            lap = Ad @ x - Ad.sum(1)[:, None] * x
            y = x_vrai + 0.1 * r.standard_normal(x.shape)
            x = x + eta * lap + 0.2 * capteurs[:, None] * (y - x)
            errB.append(float(np.sqrt(((x[nA:] - x_vrai) ** 2).sum(1).mean())))
        sorties["avec_reecriture" if reecriture else "sans_reecriture"] = dict(
            lambda2=l2, rmse_cluster_B=errB, evenements=evenements,
            rmse_B_final=errB[-1], lambda2_final=l2[-1])

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for k, v in sorties.items():
        ax[0].plot(v["lambda2"], label=k)
        ax[1].semilogy(v["rmse_cluster_B"], label=k)
    for a in ax:
        a.axvline(t_coupure, color="k", ls=":", lw=1)
        a.set_xlabel("iteration")
        a.legend(fontsize=8)
        a.grid(alpha=0.3)
    ax[0].set_title("Valeur de Fiedler lambda_2")
    ax[1].set_title("RMSE du cluster B (sans capteur)")
    fig.tight_layout()
    fig.savefig(os.path.join(ICI, "fig2_partition.png"), dpi=130)
    plt.close(fig)
    sorties["meta"] = dict(nA=nA, nB=nB, capteurs_A=5, capteurs_B=0, t_coupure=t_coupure, eps=eps)
    return sorties


# ---------------------------------------------------------------- E3 topologie

def bord(faces_k, index_km1):
    """Matrice de bord orientee (reels) des k-faces vers les (k-1)-faces."""
    M = np.zeros((len(index_km1), len(faces_k)))
    for c, f in enumerate(faces_k):
        for i in range(len(f)):
            sous = f[:i] + f[i + 1:]
            M[index_km1[sous], c] = (-1) ** i
    return M


def betti(simplexes, kmax=3):
    """simplexes : dict k -> liste de tuples tries. Retourne beta_0..beta_{kmax-1}."""
    rangs = {}
    for k in range(1, kmax + 1):
        if simplexes.get(k) and simplexes.get(k - 1):
            idx = {f: i for i, f in enumerate(simplexes[k - 1])}
            rangs[k] = np.linalg.matrix_rank(bord(simplexes[k], idx)) if simplexes[k] else 0
        else:
            rangs[k] = 0
    b = []
    for k in range(kmax):
        b.append(int(len(simplexes.get(k, [])) - rangs.get(k, 0) - rangs.get(k + 1, 0)))
    return b


def complexe_conifie(accord, ancre, variante):
    """
    Sommets 0..n-1 = agents, n = G (sommet « verite materielle »).
    Aretes agent-agent : accord. Triangles agent : triades en accord.
    Variante 'litterale' : aucun tetraedre agent-agent (seule la validation materielle remplit) .
    Variante 'clique'    : complexe de cliques complet jusqu'a la dim 3.
    Cone : G relie a chaque agent ancre ; toute face d'agents ancres est conifiee.
    """
    n = len(accord)
    G = n
    S = {0: [(i,) for i in range(n + 1)], 1: [], 2: [], 3: []}
    ar = [(i, j) for i, j in itertools.combinations(range(n), 2) if accord[i, j]]
    S[1] = ar + [(i, G) for i in range(n) if ancre[i]]
    tri = [t for t in itertools.combinations(range(n), 3)
           if accord[t[0], t[1]] and accord[t[0], t[2]] and accord[t[1], t[2]]]
    S[2] = tri + [(i, j, G) for (i, j) in ar if ancre[i] and ancre[j]]
    tet = [t + (G,) for t in tri if all(ancre[v] for v in t)]
    if variante == "clique":
        tet += [q for q in itertools.combinations(range(n), 4)
                if all(accord[a, b] for a, b in itertools.combinations(q, 2))]
    S[3] = sorted(tet)
    S[1] = sorted(S[1])
    S[2] = sorted(S[2])
    return S


def experience_3(rng):
    n_h, n_capt = 12, 5
    tau_accord, tau_ancre = 0.6, 0.6
    essais = 30
    x_vrai = np.zeros(D)
    x_faux = np.zeros(D)
    x_faux[0] = 3.0
    res = {}
    t0 = time.time()
    for ecart in (0.05, 0.12):
        for m in range(0, 6):
            det = dict(beta2_litterale=0, beta2_clique=0, beta0_reduit=0)
            valeurs_b2 = []
            for _ in range(essais):
                n = n_h + m
                X = np.vstack([x_vrai + ecart * rng.standard_normal((n_h, D)),
                               x_faux + ecart * rng.standard_normal((m, D))])
                capt = np.zeros(n, bool)
                capt[:n_capt] = True
                y = x_vrai + 0.05 * rng.standard_normal((n, D))
                ancre = capt & (np.linalg.norm(X - y, axis=1) < tau_ancre)
                dist = np.linalg.norm(X[:, None] - X[None], axis=-1)
                accord = (dist < tau_accord) & ~np.eye(n, dtype=bool)
                # beta_0 reduit du complexe conifie = composantes d'accord sans sommet ancre
                comps = composantes(accord.astype(float))
                b0r = sum(1 for c in comps if not ancre[c].any())
                det["beta0_reduit"] += int(b0r > 0)
                for var in ("litterale", "clique"):
                    b = betti(complexe_conifie(accord, ancre, var))
                    det["beta2_" + var] += int(b[2] > 0)
                    assert b[0] - 1 == b0r, "Proposition 1 violee"
                    if var == "litterale":
                        valeurs_b2.append(b[2])
            res[f"ecart_{ecart}_m_{m}"] = dict(
                ecart=ecart, colluders=m,
                taux_beta2_litterale=det["beta2_litterale"] / essais,
                taux_beta2_clique=det["beta2_clique"] / essais,
                taux_beta0_reduit=det["beta0_reduit"] / essais,
                beta2_litterale_median=float(np.median(valeurs_b2)))
    res["meta"] = dict(honnetes=n_h, capteurs=n_capt, tau_accord=tau_accord,
                       tau_ancre=tau_ancre, essais_par_case=essais,
                       duree_s=round(time.time() - t0, 1),
                       note="m=0 : taux = faux positifs ; m>0 : taux = detection")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for a, ecart in zip(ax, (0.05, 0.12)):
        ms = list(range(0, 6))
        for cle, lab in (("taux_beta2_litterale", "beta_2 (litterale)"),
                         ("taux_beta2_clique", "beta_2 (clique)"),
                         ("taux_beta0_reduit", "beta_0 reduit (cone)")):
            a.plot(ms, [res[f"ecart_{ecart}_m_{m}"][cle] for m in ms], "o-", label=lab)
        a.set_title(f"Dispersion honnete = {ecart}")
        a.set_xlabel("noeuds colludants m (m=0 : faux positifs)")
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    ax[0].set_ylabel("taux d'alerte")
    fig.tight_layout()
    fig.savefig(os.path.join(ICI, "fig3_detection.png"), dpi=130)
    plt.close(fig)
    return res


# ---------------------------------------------------------------- E4 arbitrage

def arbitrage(X, pi):
    """argmin_x sum_k pi_k ||x - x_k||^2 ; None si l'objectif n'est pas borne inferieurement."""
    s = pi.sum()
    # Hessien = 2 s I : convexe ssi s > 0 ; si s <= 0 l'objectif n'est pas borne (ou degenere)
    if s <= 0:
        return None
    return (pi[:, None] * X).sum(0) / s


def experience_4(rng):
    x_vrai = rng.standard_normal(D)
    biais = rng.standard_normal(D)
    biais /= np.linalg.norm(biais)
    n_cloud = 8
    sigma_faible = 0.05
    X_cloud = x_vrai + 1.0 * biais + 0.05 * rng.standard_normal((n_cloud, D))
    x_faible_honnete = x_vrai + sigma_faible * rng.standard_normal(D)
    x_byz = x_vrai + 3.0 * (-biais)
    X = np.vstack([X_cloud, x_faible_honnete, x_byz])
    c_cloud = 100.0

    I_verif = np.array([0.0] * n_cloud + [1 / sigma_faible ** 2, 0.0])      # audite
    I_declare = np.array([0.0] * n_cloud + [1 / sigma_faible ** 2, 1 / sigma_faible ** 2])  # le byzantin ment
    alpha, lam, delta, c0 = 1.0, 1.0, 1.0, 0.1

    def schemas(c_faible):
        c = np.array([c_cloud] * n_cloud + [c_faible, c_faible])
        return {
            "uniforme": np.ones(len(c)),
            "pondere_capacite": c.copy(),
            "qwen_signe_moins": alpha - lam * I_declare / c ** delta,
            "signe_plus_non_borne_declare": alpha + lam * I_declare / c ** delta,
            "borne_verifie": alpha + lam * I_verif / (c + c0) ** delta,
            "variance_inverse_verifiee": alpha + I_verif,
        }

    res = {}
    for nom, pi in schemas(0.01).items():
        x = arbitrage(X, pi)
        res[nom] = dict(
            poids=[float(v) for v in pi],
            borne=x is not None,
            erreur=None if x is None else float(np.linalg.norm(x - x_vrai)),
            somme_poids=float(pi.sum()))
    # balayage de la capacite du noeud faible
    cs = np.logspace(-4, 1, 26)
    bal = {}
    for nom in schemas(1.0):
        errs = []
        for cf in cs:
            x = arbitrage(X, schemas(cf)[nom])
            errs.append(None if x is None else float(np.linalg.norm(x - x_vrai)))
        bal[nom] = errs
    res["balayage_c_faible"] = dict(c=[float(v) for v in cs], erreurs=bal)
    res["references"] = dict(
        erreur_si_on_suit_le_cloud=float(np.linalg.norm(X_cloud.mean(0) - x_vrai)),
        erreur_noeud_faible_seul=float(np.linalg.norm(x_faible_honnete - x_vrai)),
        erreur_byzantin=float(np.linalg.norm(x_byz - x_vrai)))
    res["meta"] = dict(n_cloud=n_cloud, c_cloud=c_cloud, sigma_faible=sigma_faible,
                       alpha=alpha, lam=lam, delta=delta, c0=c0)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    for nom, errs in bal.items():
        e = np.array([np.nan if v is None else v for v in errs])
        ax.loglog(cs, e, "o-", ms=3, label=nom)
    ax.set_xlabel("capacite c du noeud faible (et du byzantin)")
    ax.set_ylabel("||x* - x_vrai|| (absent = objectif non borne)")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(ICI, "fig4_arbitrage.png"), dpi=130)
    plt.close(fig)
    return res


# ---------------------------------------------------------------- verification des formules

def verifications():
    """Petits controles analytiques (Proposition 2 : beta_2 du 2-squelette d'un m-simplexe)."""
    out = {}
    for m in range(3, 8):
        accord = ~np.eye(m, dtype=bool)
        ancre = np.zeros(m, bool)
        b = betti(complexe_conifie(accord, ancre, "litterale"))
        out[f"m={m}"] = dict(beta2_mesure=b[2], beta2_theorique=comb(m - 1, 3))
    return out


if __name__ == "__main__":
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    R = {"graine": SEED, "numpy": np.__version__}
    R["verifications"] = verifications()
    R["E1"] = experience_1(rng)
    R["E2"] = experience_2(rng)
    R["E3"] = experience_3(rng)
    R["E4"] = experience_4(rng)
    R["duree_totale_s"] = round(time.time() - t0, 1)

    # resume console (les series completes restent dans le JSON)
    print("== Verifications (Prop. 2)")
    for k, v in R["verifications"].items():
        print(f"  {k}: {v}")
    print("== E1")
    for k in ("laplacien_pur", "sgtd_repulsion_sans_ancre", "laplacien_ancre", "sgtd_repulsion_ancre"):
        r = R["E1"][k]
        print(f"  {k:24s} diverge={r['diverge']}  rmse_final={r['rmse'][-1] if r['rmse'] else None:.4f}"
              f"  desaccord_final={r['desaccord'][-1] if r['desaccord'] else None:.4f}")
    print("  balayage theta:", json.dumps(R["E1"]["balayage_theta"], indent=1))
    print("  meta:", R["E1"]["meta"])
    print("== E2")
    for k in ("sans_reecriture", "avec_reecriture"):
        r = R["E2"][k]
        print(f"  {k:18s} rmse_B_final={r['rmse_B_final']:.4f}  lambda2_final={r['lambda2_final']:.4f}"
              f"  evenements={r['evenements']}")
    print("== E3")
    for k, v in R["E3"].items():
        print(f"  {k}: {v}")
    print("== E4")
    for k, v in R["E4"].items():
        if k in ("balayage_c_faible",):
            continue
        if isinstance(v, dict) and "erreur" in v:
            print(f"  {k:30s} borne={v['borne']}  erreur={v['erreur']}  somme_poids={v['somme_poids']:.3g}")
        else:
            print(f"  {k}: {v}")
    print("duree totale (s):", R["duree_totale_s"])

    with open(os.path.join(ICI, "resultats.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
