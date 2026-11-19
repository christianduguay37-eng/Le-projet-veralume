"""Test de l'idée de Christian : colorier « d'en haut » (grands nombres décidés d'abord)
contre « d'en bas ». CaDiCaL départage ses premières décisions selon la numérotation des
variables : on numérote les nombres dans un sens ou dans l'autre, tout le reste identique
(symétrie N+1, bris de symétrie des couleurs par précédence)."""
import sys, time, json
from pysat.solvers import Cadical153

def construire(N, k, haut):
    pos = lambda x: min(x, N + 1 - x)              # symétrie C(x) = C(N+1-x)
    P = (N + 1) // 2
    rang = (lambda p: P + 1 - p) if haut else (lambda p: p)   # ordre des variables
    X = lambda p, c: (rang(p) - 1) * k + c + 1
    base = P * k
    Y = lambda p, c: base + (p - 1) * k + c + 1     # « couleur c déjà utilisée parmi 1..p »
    cl = []
    for p in range(1, P + 1):
        cl.append([X(p, c) for c in range(k)])
        for a in range(k):
            for b in range(a + 1, k): cl.append([-X(p, a), -X(p, b)])
        for c in range(k):                          # précédence des couleurs
            if c >= 1:
                cl.append([-X(p, c)] + ([Y(p - 1, c - 1)] if p > 1 else []))
            prev = [Y(p - 1, c)] if p > 1 else []
            cl.append([-Y(p, c), X(p, c)] + prev)
            cl.append([Y(p, c), -X(p, c)])
            if p > 1: cl.append([Y(p, c), -Y(p - 1, c)])
    vus = set()
    for x in range(1, N + 1):
        for y in range(x, N + 1 - x):
            t = tuple(sorted({pos(x), pos(y), pos(x + y)}))
            if t in vus: continue
            vus.add(t)
            for c in range(k): cl.append([-X(q, c) for q in t])
    return cl, P, X

def essayer(N, k, haut, limite):
    cl, P, X = construire(N, k, haut)
    s = Cadical153(bootstrap_with=cl)
    t = time.time()
    import threading
    res = {}
    def run(): res['r'] = s.solve()
    th = threading.Thread(target=run, daemon=True); th.start(); th.join(limite)
    if th.is_alive():
        s.interrupt(); th.join(5); dt = None; ok = None
    else:
        dt = time.time() - t; ok = res['r']
    col = None
    if ok:
        m = set(l for l in s.get_model() if l > 0)
        col = [None] + [next(c for c in range(k) if X(min(x, N + 1 - x), c) in m) for x in range(1, N + 1)]
    s.delete()
    return ok, dt, col

if __name__ == "__main__":
    k = int(sys.argv[1]); Ns = [int(v) for v in sys.argv[2].split(',')]; limite = float(sys.argv[3])
    for N in Ns:
        for haut in (False, True):
            ok, dt, col = essayer(N, k, haut, limite)
            if col:
                from lns_schur import verifier
                assert verifier(col, N, k)
                json.dump({"N": N, "k": k, "coloration": col[1:]}, open(f"temoin_S{k}_{N}_{'haut' if haut else 'bas'}.json", "w"))
            print(f"S({k}) N={N} {'haut' if haut else 'bas '} : {'SAT' if ok else ('UNSAT' if ok is False else 'pas fini')} "
                  f"{'' if dt is None else f'{dt:.1f}s'}", flush=True)
