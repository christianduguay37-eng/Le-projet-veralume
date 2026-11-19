"""
Lignée qui voyage dans son passé (Christian, 18 nov. 2026, 20 h 18-21) — test réel.
Départ : la coloration gelée des agents (E = 2 sur S(5)=160 symétrique).
Chaque agent « suppose » des couleurs (hypothèses). Le solveur exact dit :
  - soit « ça marche » (E = 0) ;
  - soit « impossible, et voici la PLUS PETITE combinaison d'hypothèses qui coince »
    (le noyau). C'est le piège AVEC son contexte.
Voyage en arrière : les bébés retirent ces hypothèses fautives (on revient avant
ces décisions) et réessaient. Bébé 1 retire le noyau ; bébé 2 retire aussi un peu
plus autour. Avec mémoire : la lignée hérite des noyaux (« ne plus jamais refaire
cette combinaison »). Sans mémoire : les bébés oublient.
"""
import json, sys, time, random
from pysat.solvers import Cadical153

def base(N, k, sym):
    v = lambda i, c: (i - 1) * k + c + 1
    cl = []
    for i in range(1, N + 1):
        cl.append([v(i, c) for c in range(k)])
        for a in range(k):
            for b in range(a + 1, k): cl.append([-v(i, a), -v(i, b)])
    for x in range(1, N + 1):
        for y in range(x, N + 1 - x):
            for c in range(k): cl.append(list({-v(x, c), -v(y, c), -v(x + y, c)}))
    if sym:
        for i in range(1, N // 2 + 1):
            for c in range(k): cl += [[-v(i, c), v(N + 1 - i, c)], [v(i, c), -v(N + 1 - i, c)]]
    return cl, v

def lignee(N, k, sym, col, memoire, budget_s, conf=20000, graine=0, largeur=8):
    rnd = random.Random(graine)
    cl, v = base(N, k, sym)
    hyp0 = frozenset(v(i, col[i]) for i in range(1, N + 1))
    gen = [(hyp0, [])]                         # (hypothèses, noyaux hérités)
    t0 = time.time(); appels = 0; cycle = 0; noyaux_payes = 0
    while time.time() - t0 < budget_s and gen:
        cycle += 1; suite = []
        for hyp, herite in gen:
            if time.time() - t0 >= budget_s: break
            s = Cadical153(bootstrap_with=cl + herite)
            s.conf_budget(conf)
            r = s.solve_limited(assumptions=sorted(hyp)); appels += 1
            if r:
                m = set(l for l in s.get_model() if l > 0); s.delete()
                sol = [None] + [next(c for c in range(k) if v(i, c) in m) for i in range(1, N + 1)]
                return True, sol, appels, cycle, noyaux_payes, time.time() - t0
            noyau = set(s.get_core() or []) if r is False else set()
            s.delete()
            if r is None:                      # budget épuisé : on relâche au hasard
                noyau = set(rnd.sample(sorted(hyp), max(1, len(hyp) // 20)))
            else:
                noyaux_payes += 1
            nouveau = herite + ([[-l for l in noyau]] if (memoire and r is False and noyau) else [])
            # voyage en arrière : retirer les hypothèses fautives (et un peu plus pour le 2e bébé)
            b1 = hyp - noyau
            autour = set(rnd.sample(sorted(b1), min(len(b1), max(2, len(noyau)))))
            b2 = b1 - autour
            suite += [(frozenset(b1), nouveau), (frozenset(b2), nouveau)]
        rnd.shuffle(suite)
        suite.sort(key=lambda t: -len(t[0]))   # garder ceux qui ont le moins reculé
        gen = suite[:largeur]
    return False, None, appels, cycle, noyaux_payes, time.time() - t0

if __name__ == "__main__":
    etat = json.load(open(sys.argv[1])); nom = sys.argv[2]; budget = float(sys.argv[3])
    c = etat[nom]; N, k, sym = c["N"], c["k"], c["sym"]; col = [None] + list(c["best_col"])
    for memoire in (False, True):
        for g in range(int(sys.argv[4])):
            ok, sol, ap, cy, nk, dt = lignee(N, k, sym, col, memoire, budget, graine=g)
            if ok:
                from lns_schur import verifier; assert verifier(sol, N, k)
                json.dump({"N": N, "k": k, "coloration": sol[1:]}, open(f"temoin_retro_{nom}.json", "w"))
            print(f"{'AVEC' if memoire else 'SANS'} mémoire, graine {g} : {'E = 0 !' if ok else 'pas trouvé'} "
                  f"| {ap} essais, cycle {cy}, {nk} noyaux, {dt:.0f}s", flush=True)
