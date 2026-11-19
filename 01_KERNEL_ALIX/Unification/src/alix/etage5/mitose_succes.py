"""Variante D (idée de Christian, 18 nov. 2026, 20 h 12) : la lignée hérite aussi de
ses RÉUSSITES, pas seulement de ses pièges.
  - Chaque fois qu'un agent bat son record, les coups (x, couleur) de cette coloration
    reçoivent une trace positive (comme les phéromones des fourmis).
  - Les pièges deviennent des pénalités douces, pas des interdits.
  - Tout s'efface un peu à chaque génération (l'oubli de TH53).
  - Les bébés partent du MEILLEUR état de leur parent, pas du dernier.
"""
import numpy as np, random, sys, time
from mitose_reelle import Etat, agent_seul, mitose

def marcher_d(et, pas, rnd, trace, piege, patience=60):
    payes = 0; E = et.energie(); record = E; depuis = 0
    meilleur = et.col.copy(); Emeil = E
    for p in range(pas):
        if E == 0: return 0, p, payes, et.col.copy(), 0
        cand = et.en_conflit(); x = rnd.choice(cand)
        cur = et.conflits_de(x, et.col[x])
        opts = []
        for c in range(et.k):
            if c == et.col[x]: continue
            v = et.conflits_de(x, c) + 0.5 * piege.get((x, c), 0.0) - 0.3 * trace.get((x, c), 0.0)
            opts.append((v, et.conflits_de(x, c), c))
        v0 = cur + 0.5 * piege.get((x, int(et.col[x])), 0.0) - 0.3 * trace.get((x, int(et.col[x])), 0.0)
        vb = min(o[0] for o in opts)
        if vb <= v0 or rnd.random() < 0.1:
            _, cc, c = rnd.choice([o for o in opts if o[0] == vb])
            et.col[x] = c; E += cc - cur
            if cc < cur:                      # D2 : on retient le COUP qui a réussi
                trace[(x, c)] = trace.get((x, c), 0.0) + 1.0
        if E < record:
            record = E; depuis = 0
            if E < Emeil:
                Emeil = E; meilleur = et.col.copy()
        else:
            depuis += 1
        if depuis >= patience:
            payes += 1
            for y in rnd.sample(cand, min(3, len(cand))):
                piege[(y, int(et.col[y]))] = piege.get((y, int(et.col[y])), 0.0) + 1.0
            for y in rnd.sample(range(1, et.N + 1), max(1, et.N // 15)):
                et.col[y] = rnd.randrange(et.k)
            E = et.energie(); record = E; depuis = 0
    return E, pas, payes, meilleur, Emeil

def oublier(d, f=0.8):
    return {k: v * f for k, v in d.items() if v * f > 0.05}

def mitose_d(N, k, budget, graine, pas_par_agent=400):
    rnd = random.Random(graine)
    gen = [(Etat(N, k, rnd), {}, {})]
    utilises = payes = 0; cycle = 0
    while utilises < budget and gen:
        cycle += 1; suite = []
        for et, tr, pg in gen:
            if utilises >= budget: break
            E, p, py, meil, Em = marcher_d(et, min(pas_par_agent, budget - utilises), rnd, tr, pg)
            utilises += p; payes += py
            if E == 0: return True, utilises, payes, et, cycle
            for _ in range(2):
                b = Etat(N, k, rnd, meil.copy())
                for x in rnd.sample(range(1, N + 1), max(1, N // 20)): b.col[x] = rnd.randrange(k)
                suite.append((b, oublier(tr), oublier(pg)))
        suite.sort(key=lambda t: t[0].energie())
        gen = suite[: 2 ** min(cycle, 6)]
    return False, utilises, payes, None, cycle

if __name__ == "__main__":
    N, k, budget, essais = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    R = {"B": [], "C": [], "D": []}
    for g in range(essais):
        b = mitose(N, k, budget, g, False); c = mitose(N, k, budget, g, True); d = mitose_d(N, k, budget, g)
        for nom, r in (("B", b), ("C", c), ("D", d)):
            if r[3] is not None: assert r[3].energie() == 0
            R[nom].append((r[0], r[1], r[2]))
        print(f"graine {g}: B {b[0]} | C {c[0]} | D {d[0]} ({d[1]} pas, cycle {d[4]})", flush=True)
    for nom, r in R.items():
        print(nom, "réussites", sum(x[0] for x in r), "/", len(r), "| pas moyens", int(np.mean([x[1] for x in r])),
              "| pièges moyens", round(np.mean([x[2] for x in r]), 1))
