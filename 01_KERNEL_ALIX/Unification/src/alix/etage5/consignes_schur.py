"""
Consignes de Thot aux agents qui ont appris (Schur), 18 nov. 2026.

Les colorations gelées dans etat_agents_schur.json servent de point de départ
(l'héritage de TH116) à un solveur exact compilé (CaDiCaL via pysat, TH118 industriel).

Deux modes :
  lns   : garde les nombres en conflit + une fraction au hasard des autres LIBRES,
          fige le reste, résout ; recommence avec un autre tirage. (grand voisinage)
  plein : problème complet, la coloration apprise sert de « phases » (démarrage à chaud).

Installation : pip install python-sat
Exemples :
  python consignes_schur.py etat_agents_schur.json colonie_S5_160_sym lns sym 0.5 20000 3600
  python consignes_schur.py etat_agents_schur.json colonie_S6_537 plein libre 0 0 0
Un témoin E = 0 est écrit dans temoin_<colonie>_E0.json et revérifié par force brute.
"""

import json, sys, time, random
from pysat.solvers import Cadical153


def conflits(col, N):
    return [(x, y, x + y) for x in range(1, N + 1) for y in range(x, N + 1 - x)
            if col[x] == col[y] == col[x + y]]


def verifier(col, N, k):
    return all(0 <= col[i] < k for i in range(1, N + 1)) and not conflits(col, N)



def essai(col, N, k, libres, sym, budget):
    var = lambda i, c: (i - 1) * k + c + 1
    s = Cadical153()
    for i in range(1, N + 1):
        if i in libres:
            s.add_clause([var(i, c) for c in range(k)])
            for a in range(k):
                for b in range(a + 1, k): s.add_clause([-var(i, a), -var(i, b)])
        else:
            for c in range(k):
                s.add_clause([var(i, c) if c == col[i] else -var(i, c)])
    for x in range(1, N + 1):
        for y in range(x, N + 1 - x):
            z = x + y
            if x in libres or y in libres or z in libres:
                for c in range(k): s.add_clause(list({-var(x, c), -var(y, c), -var(z, c)}))
    if sym:
        for i in libres:
            j = N + 1 - i
            for c in range(k):
                s.add_clause([-var(i, c), var(j, c)]); s.add_clause([var(i, c), -var(j, c)])
    s.set_phases([var(i, col[i]) for i in libres])
    if budget > 0:
        s.conf_budget(budget); r = s.solve_limited()
    else:
        r = s.solve()
    sol = None
    if r:
        ms = set(l for l in s.get_model() if l > 0)
        sol = [None] + [next(c for c in range(k) if var(i, c) in ms) for i in range(1, N + 1)]
    s.delete(); return r, sol

def lns(col, N, k, sym, frac, budget, temps, graine=0):
    rnd = random.Random(graine); t0 = time.time(); it = 0
    while time.time() - t0 < temps:
        E = conflits(col, N)
        if not E: return col, it
        S = {v for t in E for v in t}
        if sym: S |= {N + 1 - v for v in S}
        autres = [i for i in range(1, N + 1) if i not in S]
        lib = set(rnd.sample(autres, int(frac * len(autres)))) | S
        if sym: lib |= {N + 1 - v for v in lib}
        r, sol = essai(col, N, k, lib, sym, budget); it += 1
        if r: return sol, it
    return col, it


def plein(col, N, k, sym, budget_conf):
    var = lambda i, c: (i - 1) * k + c + 1
    s = Cadical153()
    for i in range(1, N + 1):
        s.add_clause([var(i, c) for c in range(k)])
        for a in range(k):
            for b in range(a + 1, k): s.add_clause([-var(i, a), -var(i, b)])
    for x in range(1, N + 1):
        for y in range(x, N + 1 - x):
            for c in range(k): s.add_clause(list({-var(x, c), -var(y, c), -var(x + y, c)}))
    if sym:
        for i in range(1, N // 2 + 1):
            for c in range(k):
                s.add_clause([-var(i, c), var(N + 1 - i, c)]); s.add_clause([var(i, c), -var(N + 1 - i, c)])
    if col:
        s.set_phases([var(i, col[i]) if True else 0 for i in range(1, N + 1)])
    if budget_conf > 0:
        s.conf_budget(budget_conf)
        r = s.solve_limited()
    else:
        r = s.solve()
    m = s.get_model() if r else None
    st = s.accum_stats(); s.delete()
    if not r: return r, None, st
    ms = set(l for l in m if l > 0)
    return r, [None] + [next(c for c in range(k) if var(i, c) in ms) for i in range(1, N + 1)], st


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f_in:
        etat = json.load(f_in)
    nom, mode, sym = sys.argv[2], sys.argv[3], sys.argv[4] == "sym"
    frac, budget, temps = float(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7])
    c = etat[nom]; N, k = c["N"], c["k"]; col = [None] + list(c["best_col"])
    print(f"{nom} : N={N}, k={k}, conflits au départ = {len(conflits(col, N))}", flush=True)
    t = time.time()
    if mode == "lns":
        sol, it = lns(col, N, k, sym, frac, budget, temps)
    else:
        r, s2, st = plein(col, N, k, sym, budget)
        sol = s2 or col
    E = conflits(sol, N)
    print(f"fin : {time.time()-t:.1f}s, E = {len(E)}, valide = {verifier(sol, N, k)}")
    if not E:
        with open(f"temoin_{nom}_E0.json", "w", encoding="utf-8") as f_out:
            json.dump({"N": N, "k": k, "coloration": sol[1:]}, f_out)
        print("TÉMOIN ÉCRIT")
