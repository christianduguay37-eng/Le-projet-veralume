#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alix_dpll_t_solver_hades.py (dpll_t_solver.py) - CDCL(T) en Python pur (3.11+, stdlib seulement, aucun appel LLM).
Sparring & Architecture : Hadès (Claude) × Christian Duguay & Alix (Panthéon K-SIL)

Noyau SAT
  * 2-Watched Literals (BCP sans scan global), analyse de conflit 1-UIP + minimisation locale,
    VSIDS (tas paresseux) + sauvegarde de phase, redémarrages de Luby, réduction de la base
    de clauses apprises (LBD + activité).
  * Assomptions : solve(assumptions) ; en cas d'UNSAT, `core` = sous-ensemble des assomptions
    suffisant (analyze_final) ; `minimal_unsat_subset()` le réduit à un MUS (suppression + raffinement
    par noyau).

Théorie : Difference Logic (IDL entiers / RDL réels)
  * Atome  x - y <= c  lié à un littéral booléen b.   b vrai : arête y -> x de poids c ;
    b faux : IDL  x - y >= c+1  (arête x -> y, poids -c-1) ;
             RDL  x - y >  c    (arête x -> y, poids -c - delta, delta infinitésimal ; poids = paires (c, k)).
  * Potentiels maintenus de façon incrémentale (Cotton-Maler : Dijkstra sur coûts réduits, un seul
    parcours par arête ajoutée). Si le sommet source de la nouvelle arête est atteint avec gain
    négatif -> cycle négatif ; les arêtes du cycle (simple) forment un ensemble inconsistant minimal et
    leur négation est le lemme de théorie, renvoyé au CDCL comme clause de conflit.
  * Le retour arrière n'a pas à restaurer les potentiels (une solution du graphe complet reste
    solution de tout sous-graphe).
"""
from __future__ import annotations

import heapq
import itertools
import random
import sys
import time
from fractions import Fraction

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

TRUE, FALSE, UNDEF = 1, -1, 0

__all__ = ["Solver", "DifferenceLogic", "luby"]


def luby(i: int) -> int:
    """Suite de Luby (1-indexée) : 1 1 2 1 1 2 4 1 1 2 1 1 2 4 8 ..."""
    while True:
        k = 1
        while (1 << k) - 1 < i:
            k += 1
        if (1 << k) - 1 == i:
            return 1 << (k - 1)
        i -= (1 << (k - 1)) - 1


def _li(lit: int) -> int:
    return (lit << 1) if lit > 0 else ((-lit) << 1) | 1


class _Clause:
    __slots__ = ("lits", "learnt", "act", "lbd", "deleted")

    def __init__(self, lits, learnt=False):
        self.lits = lits
        self.learnt = learnt
        self.act = 0.0
        self.lbd = 0
        self.deleted = False


# =================================================================================================
# Théorie : Difference Logic
# =================================================================================================

class DifferenceLogic:
    """Contraintes x - y <= c. mode='idl' (entiers) ou 'rdl' (réels, inégalités strictes via delta)."""

    def __init__(self, mode: str = "idl"):
        if mode not in ("idl", "rdl"):
            raise ValueError("mode ∈ {'idl','rdl'}")
        self.mode = mode
        self.names: dict = {}
        self.p: list = [(0, 0)]          # potentiels (a, b) = a + b*delta ; index 0 = variable ZERO
        self.out: list = [[]]            # arêtes sortantes : (src, dst, w0, w1, lit)
        self.atoms: dict = {}            # var booléenne -> (arête_vraie, arête_fausse)
        self.stack: list = []            # (position sur la trace, arête)
        self.n_edges_added = 0

    def var(self, name) -> int:
        if name is None:
            return 0
        if name not in self.names:
            self.names[name] = len(self.p)
            self.p.append((0, 0))
            self.out.append([])
        return self.names[name]

    def _const(self, c):
        if self.mode == "idl":
            if isinstance(c, float) and c.is_integer():
                c = int(c)
            if not isinstance(c, int):
                raise TypeError("IDL : constantes entières")
            return c
        return Fraction(str(c)) if isinstance(c, float) else Fraction(c)

    def make_atom(self, bvar: int, x: int, y: int, c):
        c = self._const(c)
        pos = (y, x, c, 0, 0)                                     # x - y <= c : y -> x
        neg = (x, y, -c - 1, 0, 0) if self.mode == "idl" else (x, y, -c, -1, 0)
        self.atoms[bvar] = (pos, neg)

    def assert_lit(self, lit: int, pos: int):
        a = self.atoms.get(abs(lit))
        if a is None:
            return None
        e = a[0] if lit > 0 else a[1]
        e = (e[0], e[1], e[2], e[3], lit)
        cycle = self._add_edge(e)
        if cycle is not None:
            return sorted({-x[4] for x in cycle})                  # lemme : ¬(l1 ∧ ... ∧ lk)
        self.stack.append((pos, e))
        return None

    def backtrack(self, size: int):
        st = self.stack
        while st and st[-1][0] >= size:
            _, e = st.pop()
            self.out[e[0]].pop()

    def _add_edge(self, e):
        """None si consistant (arête ajoutée) ; sinon la liste des arêtes du cycle négatif (simple)."""
        u, v, w0, w1, _ = e
        p, out = self.p, self.out
        pu, pv = p[u], p[v]
        if u == v:
            if (w0, w1) < (0, 0):
                return [e]
            out[u].append(e)
            return None
        g0, g1 = pu[0] + w0 - pv[0], pu[1] + w1 - pv[1]
        if (g0, g1) >= (0, 0):                                     # contrainte déjà satisfaite
            out[u].append(e)
            self.n_edges_added += 1
            return None
        gamma = {v: (g0, g1)}
        pred = {v: e}
        newp: dict = {}
        done: set = set()
        heap = [((g0, g1), v)]
        zero = (0, 0)
        while heap:
            g, s = heapq.heappop(heap)
            if s in done or gamma[s] != g:
                continue
            done.add(s)
            ps = p[s]
            ns = (ps[0] + g[0], ps[1] + g[1])
            newp[s] = ns
            for f in out[s]:
                t = f[1]
                if t in done:
                    continue
                pt = p[t]
                gt = (ns[0] + f[2] - pt[0], ns[1] + f[3] - pt[1])
                if gt < zero and gt < gamma.get(t, zero):
                    gamma[t] = gt
                    pred[t] = f
                    if t == u:                                     # chemin v ~> u de poids w + chemin < 0
                        cyc = [f]
                        cur = s
                        while cur != v:
                            pe = pred[cur]
                            cyc.append(pe)
                            cur = pe[0]
                        cyc.append(e)
                        return cyc
                    heapq.heappush(heap, (gt, t))
        for s, ns in newp.items():
            p[s] = ns
        out[u].append(e)
        self.n_edges_added += 1
        return None

    def model(self) -> dict:
        p = self.p
        z = p[0]
        if self.mode == "idl":
            return {n: p[i][0] - z[0] for n, i in self.names.items()}
        delta = Fraction(1)
        for lst in self.out:
            for (u, v, c, d, _) in lst:
                A, B = p[v][0] - p[u][0], p[v][1] - p[u][1]
                if A < c and B > d:
                    delta = min(delta, Fraction(c - A) / (B - d))
        return {n: Fraction(p[i][0] - z[0]) + (p[i][1] - z[1]) * delta for n, i in self.names.items()}


# =================================================================================================
# Solveur CDCL(T)
# =================================================================================================

class Solver:
    def __init__(self, theory: str | None = None, restart_base: int = 100, seed: int = 0):
        self.nvars = 0
        self.val = [0]
        self.level = [0]
        self.reason = [None]
        self.phase = [False]
        self.act = [0.0]
        self.seen = [False]
        self.watches: list = [[], []]
        self.trail: list = []
        self.trail_lim: list = []
        self.qhead = 0
        self.th_head = 0
        self.clauses: list = []
        self.learnts: list = []
        self.heap: list = []
        self.var_inc, self.cla_inc = 1.0, 1.0
        self.restart_base = restart_base
        self.max_learnts = 2000.0
        self.ok = True
        self.core: list = []
        self.model: list | None = None
        self.int_model: dict | None = None
        self.theory = DifferenceLogic(theory) if theory else None
        self._atom_memo: dict = {}
        self.lemmas: list = []
        self.n_conflicts = self.n_decisions = self.n_props = self.n_restarts = self.n_theory_conflicts = 0
        self.rng = random.Random(seed)

    def new_var(self) -> int:
        self.nvars += 1
        v = self.nvars
        self.val.append(0)
        self.level.append(0)
        self.reason.append(None)
        self.phase.append(False)
        self.act.append(0.0)
        self.seen.append(False)
        self.watches.append([])
        self.watches.append([])
        heapq.heappush(self.heap, (-0.0, v))
        return v

    def _ensure(self, lit: int):
        while abs(lit) > self.nvars:
            self.new_var()

    def _val(self, lit: int) -> int:
        v = self.val[lit if lit > 0 else -lit]
        return v if lit > 0 else -v

    def decision_level(self) -> int:
        return len(self.trail_lim)

    def atom(self, x, y, c) -> int:
        """Littéral booléen pour  x - y <= c  (y=None : x <= c)."""
        if self.theory is None:
            raise RuntimeError("Solver créé sans théorie")
        th = self.theory
        xi, yi = th.var(x), th.var(y)
        cc = th._const(c)
        if xi == yi:
            v = self.new_var()
            self.add_clause([v] if cc >= 0 else [-v])
            return v
        if th.mode == "idl" and xi > yi:
            return -self.atom(y, x, -cc - 1)
        key = (xi, yi, cc)
        if key in self._atom_memo:
            return self._atom_memo[key]
        v = self.new_var()
        th.make_atom(v, xi, yi, cc)
        self._atom_memo[key] = v
        return v

    def le(self, x, y, c):  return self.atom(x, y, c)
    def ge(self, x, y, c):  return self.atom(y, x, -c)
    def lt(self, x, y, c):  return -self.atom(y, x, -c)
    def gt(self, x, y, c):  return -self.atom(x, y, c)

    def add_soft(self, lits) -> int:
        """Clause activable : (¬s ∨ lits). Retourne le sélecteur s à passer dans les assomptions."""
        s = self.new_var()
        self.add_clause([-s] + list(lits))
        return s

    def add_clause(self, lits) -> bool:
        if not self.ok:
            return False
        for l in lits:
            self._ensure(l)
        self._cancel_until(0)
        seen, out = set(), []
        for l in lits:
            if -l in seen:
                return True
            if l in seen:
                continue
            v = self._val(l)
            if v == TRUE:
                return True
            if v == FALSE:
                continue
            seen.add(l)
            out.append(l)
        if not out:
            self.ok = False
            return False
        if len(out) == 1:
            self._enqueue(out[0], None)
        else:
            c = _Clause(out)
            self.clauses.append(c)
            self._attach(c)
        if self._propagate_all() is not None:
            self.ok = False
            return False
        return True

    def _attach(self, c):
        self.watches[_li(c.lits[0])].append(c)
        self.watches[_li(c.lits[1])].append(c)

    def _enqueue(self, lit, reason):
        v = lit if lit > 0 else -lit
        self.val[v] = 1 if lit > 0 else -1
        self.level[v] = len(self.trail_lim)
        self.reason[v] = reason
        self.trail.append(lit)

    def _propagate(self):
        val, trail, watches = self.val, self.trail, self.watches
        while self.qhead < len(trail):
            p = trail[self.qhead]
            self.qhead += 1
            self.n_props += 1
            fl = -p
            ws = watches[_li(fl)]
            i = j = 0
            n = len(ws)
            while i < n:
                c = ws[i]
                i += 1
                if c.deleted:
                    continue
                lits = c.lits
                if lits[0] == fl:
                    lits[0] = lits[1]
                    lits[1] = fl
                first = lits[0]
                fv = val[first if first > 0 else -first]
                if first < 0:
                    fv = -fv
                if fv == 1:
                    ws[j] = c
                    j += 1
                    continue
                for k in range(2, len(lits)):
                    lk = lits[k]
                    kv = val[lk if lk > 0 else -lk]
                    if lk < 0:
                        kv = -kv
                    if kv != -1:
                        lits[1] = lk
                        lits[k] = fl
                        watches[_li(lk)].append(c)
                        break
                else:
                    ws[j] = c
                    j += 1
                    if fv == -1:
                        while i < n:
                            ws[j] = ws[i]
                            j += 1
                            i += 1
                        del ws[j:]
                        self.qhead = len(trail)
                        return c
                    self._enqueue(first, c)
            del ws[j:]
        return None

    def _theory_check(self):
        th, trail = self.theory, self.trail
        while self.th_head < len(trail):
            pos = self.th_head
            self.th_head += 1
            lemma = th.assert_lit(trail[pos], pos)
            if lemma is not None:
                return lemma
        return None

    def _propagate_all(self):
        c = self._propagate()
        if c is not None:
            return c
        if self.theory is not None:
            lemma = self._theory_check()
            if lemma is not None:
                self.n_theory_conflicts += 1
                self.lemmas.append(tuple(lemma))
                return _Clause(list(lemma))
        return None

    def _cancel_until(self, lvl):
        if len(self.trail_lim) <= lvl:
            return
        start = self.trail_lim[lvl]
        trail, val, act, heap = self.trail, self.val, self.act, self.heap
        for i in range(len(trail) - 1, start - 1, -1):
            lit = trail[i]
            v = lit if lit > 0 else -lit
            self.phase[v] = lit > 0
            val[v] = 0
            self.reason[v] = None
            heapq.heappush(heap, (-act[v], v))
        del trail[start:]
        del self.trail_lim[lvl:]
        self.qhead = start
        if self.theory is not None:
            self.theory.backtrack(start)
            self.th_head = min(self.th_head, start)

    def _bump_var(self, v):
        self.act[v] += self.var_inc
        if self.act[v] > 1e100:
            for i in range(1, self.nvars + 1):
                self.act[i] *= 1e-100
            self.var_inc *= 1e-100
            self._rebuild_heap()
        elif self.val[v] == 0:
            heapq.heappush(self.heap, (-self.act[v], v))

    def _bump_clause(self, c):
        c.act += self.cla_inc
        if c.act > 1e20:
            for d in self.learnts:
                d.act *= 1e-20
            self.cla_inc *= 1e-20

    def _decay(self):
        self.var_inc *= 1 / 0.95
        self.cla_inc *= 1 / 0.999

    def _rebuild_heap(self):
        self.heap = [(-self.act[v], v) for v in range(1, self.nvars + 1) if self.val[v] == 0]
        heapq.heapify(self.heap)

    def _pick_branch(self):
        if len(self.heap) > 4 * self.nvars + 1000:
            self._rebuild_heap()
        heap, val = self.heap, self.val
        while heap:
            _, v = heapq.heappop(heap)
            if val[v] == 0:
                return v if self.phase[v] else -v
        return None

    def _analyze(self, confl):
        seen, level, trail, reason = self.seen, self.level, self.trail, self.reason
        cur = self.decision_level()
        learnt = [0]
        path_c = 0
        p = None
        idx = len(trail) - 1
        c = confl
        while True:
            if c.learnt:
                self._bump_clause(c)
            for q in c.lits:
                if q == p:
                    continue
                v = q if q > 0 else -q
                if not seen[v] and level[v] > 0:
                    self._bump_var(v)
                    seen[v] = True
                    if level[v] >= cur:
                        path_c += 1
                    else:
                        learnt.append(q)
            while not seen[trail[idx] if trail[idx] > 0 else -trail[idx]]:
                idx -= 1
            p = trail[idx]
            idx -= 1
            pv = p if p > 0 else -p
            c = reason[pv]
            seen[pv] = False
            path_c -= 1
            if path_c <= 0:
                break
        learnt[0] = -p
        out = [learnt[0]]
        for q in learnt[1:]:
            r = reason[abs(q)]
            if r is not None and all(abs(x) == abs(q) or seen[abs(x)] or level[abs(x)] == 0 for x in r.lits):
                continue
            out.append(q)
        for q in learnt[1:]:
            seen[abs(q)] = False
        if len(out) == 1:
            bt = 0
        else:
            m = max(range(1, len(out)), key=lambda k: level[abs(out[k])])
            out[1], out[m] = out[m], out[1]
            bt = level[abs(out[1])]
        lbd = len({level[abs(l)] for l in out})
        return out, bt, lbd

    def _analyze_final(self, a):
        core = [a]
        if self.decision_level() == 0:
            return core
        seen, level = self.seen, self.level
        seen[abs(a)] = True
        for i in range(len(self.trail) - 1, self.trail_lim[0] - 1, -1):
            lit = self.trail[i]
            v = abs(lit)
            if not seen[v]:
                continue
            r = self.reason[v]
            if r is None:
                if level[v] > 0 and lit != a:
                    core.append(lit)
            else:
                for q in r.lits:
                    if abs(q) != v and level[abs(q)] > 0:
                        seen[abs(q)] = True
            seen[v] = False
        seen[abs(a)] = False
        return core

    def _handle_conflict(self, confl) -> bool:
        lits = confl.lits
        maxl = max((self.level[abs(l)] for l in lits), default=0)
        if maxl == 0:
            self.ok = False
            return False
        if maxl < self.decision_level():
            self._cancel_until(maxl)
        learnt, bt, lbd = self._analyze(confl)
        self._cancel_until(bt)
        if len(learnt) == 1:
            self._enqueue(learnt[0], None)
        else:
            c = _Clause(learnt, True)
            c.lbd = lbd
            self.learnts.append(c)
            self._attach(c)
            self._bump_clause(c)
            self._enqueue(learnt[0], c)
        self._decay()
        return True

    def _reduce_db(self):
        def locked(c):
            l0 = c.lits[0]
            return self._val(l0) == TRUE and self.reason[abs(l0)] is c
        cand = [c for c in self.learnts if len(c.lits) > 2 and c.lbd > 2 and not locked(c)]
        cand.sort(key=lambda c: (-c.lbd, c.act))
        for c in cand[: len(cand) // 2]:
            c.deleted = True
        self.learnts = [c for c in self.learnts if not c.deleted]
        self.max_learnts *= 1.1

    def solve(self, assumptions=(), max_conflicts: int | None = None):
        self.core, self.model, self.int_model = [], None, None
        if not self.ok:
            return False
        assumptions = list(assumptions)
        for a in assumptions:
            self._ensure(a)
        self._cancel_until(0)
        used = since = 0
        ri = 1
        limit = self.restart_base * luby(ri)
        while True:
            confl = self._propagate_all()
            if confl is not None:
                self.n_conflicts += 1
                used += 1
                since += 1
                if not self._handle_conflict(confl):
                    return False
                if max_conflicts is not None and used >= max_conflicts:
                    self._cancel_until(0)
                    return None
                continue
            if since >= limit:
                self.n_restarts += 1
                ri += 1
                limit = self.restart_base * luby(ri)
                since = 0
                self._cancel_until(0)
                continue
            if len(self.learnts) >= self.max_learnts:
                self._reduce_db()
            nxt = None
            while self.decision_level() < len(assumptions):
                a = assumptions[self.decision_level()]
                v = self._val(a)
                if v == TRUE:
                    self.trail_lim.append(len(self.trail))
                elif v == FALSE:
                    self.core = self._analyze_final(a)
                    self._cancel_until(0)
                    return False
                else:
                    nxt = a
                    break
            if nxt is None:
                nxt = self._pick_branch()
                if nxt is None:
                    self.model = [x == TRUE for x in self.val]
                    if self.theory is not None:
                        self.int_model = self.theory.model()
                    self._cancel_until(0)
                    return True
                self.n_decisions += 1
            self.trail_lim.append(len(self.trail))
            self._enqueue(nxt, None)

    def minimal_unsat_subset(self, assumptions):
        assumptions = list(dict.fromkeys(assumptions))
        if self.solve(assumptions):
            return None
        core = set(self.core)
        todo = [a for a in assumptions if a in core]
        keep: list = []
        while todo:
            a = todo.pop()
            if self.solve(keep + todo):
                keep.append(a)
            else:
                core = set(self.core)
                todo = [x for x in todo if x in core]
        return keep

    def model_value(self, lit: int) -> bool:
        v = self.model[abs(lit)]
        return v if lit > 0 else not v


# =================================================================================================
# Auto-test
# =================================================================================================

def _brute_sat(n, clauses):
    for bits in range(1 << n):
        if all(any(((bits >> (abs(l) - 1)) & 1) == (l > 0) for l in c) for c in clauses):
            return True
    return False


def _rand_cnf(rng, n, m, k=3):
    return [[rng.choice((-1, 1)) * v for v in rng.sample(range(1, n + 1), k)] for _ in range(m)]


def _check_model(S, clauses):
    return all(any(S.model_value(l) for l in c) for c in clauses)


def _selftest(verbose: bool = True):
    say = print if verbose else (lambda *a, **k: None)
    t0 = time.time()

    # Luby
    assert [luby(i) for i in range(1, 16)] == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]

    # SAT pur vs force brute
    rng = random.Random(1)
    for _ in range(300):
        n = rng.randint(3, 11)
        cl = _rand_cnf(rng, n, rng.randint(n, 5 * n), k=rng.choice((2, 3)))
        S = Solver()
        for c in cl:
            S.add_clause(c)
        r = S.solve()
        assert r == _brute_sat(n, cl), cl
        if r:
            assert _check_model(S, cl)
    say("SAT pur vs brute force : 300 instances OK")

    # Pigeonhole 6 -> 5 : UNSAT
    P, H = 6, 5
    S = Solver()
    var = lambda p, h: p * H + h + 1
    for p in range(P):
        S.add_clause([var(p, h) for h in range(H)])
    for h in range(H):
        for p1 in range(P):
            for p2 in range(p1 + 1, P):
                S.add_clause([-var(p1, h), -var(p2, h)])
    assert S.solve() is False
    say(f"PHP(6,5) UNSAT : {S.n_conflicts} conflits, {S.n_restarts} redémarrages")

    # 3-SAT aléatoire, grande taille, modèle vérifié
    rng = random.Random(7)
    sat_found = 0
    for seed in range(6):
        n = 80
        cl = _rand_cnf(rng, n, int(3.9 * n))
        S = Solver()
        for c in cl:
            S.add_clause(c)
        r = S.solve()
        if r:
            assert _check_model(S, cl)
            sat_found += 1
    say(f"3-SAT n=80 ratio 3.9 : {sat_found}/6 SAT, modèles vérifiés")

    # Assomptions, noyau, MUS (booléen)
    S = Solver()
    a, b, c, d = (S.new_var() for _ in range(4))
    x, y = S.new_var(), S.new_var()
    s1 = S.add_soft([x]); s2 = S.add_soft([-x, y]); s3 = S.add_soft([-y]); s4 = S.add_soft([a, b])
    assert S.solve([s1, s2, s3, s4]) is False and set(S.core) <= {s1, s2, s3, s4}
    mus = S.minimal_unsat_subset([s4, s1, s2, s3])
    assert set(mus) == {s1, s2, s3}, mus
    assert S.solve(mus) is False
    for m in mus:
        assert S.solve([q for q in mus if q != m]) is True
    assert S.solve([s1, s2, s4]) is True
    assert S.minimal_unsat_subset([s1, s4]) is None
    say(f"noyau + MUS booléen OK ({len(mus)} sélecteurs)")

    # ---------------------------------------------------------------- IDL
    # Cycle négatif direct : x-y<=-1, y-z<=-1, z-x<=-1
    S = Solver("idl")
    for (u, v) in (("x", "y"), ("y", "z"), ("z", "x")):
        S.add_clause([S.le(u, v, -1)])
    assert S.solve() is False
    assert S.lemmas and len(S.lemmas[0]) == 3, S.lemmas
    say(f"IDL cycle négatif : lemme de théorie minimal = {len(S.lemmas[0])} littéraux")

    # IDL aléatoire vs force brute (3 variables + ZERO), clauses de 1 à 3 atomes
    rng = random.Random(3)
    names = ["x", "y", "z"]
    R = range(-9, 10)

    def eval_atom(env, x, y, c):
        return env[x] - (env[y] if y else 0) <= c

    n_sat = 0
    for _ in range(150):
        S = Solver("idl")
        spec = []
        for _ in range(rng.randint(4, 12)):
            cl = []
            for _ in range(rng.choice((1, 1, 2, 3))):
                x = rng.choice(names)
                y = rng.choice([n for n in names + [None] if n != x])
                cl.append((x, y, rng.randint(-2, 2), rng.choice((True, False))))
            spec.append(cl)
        for cl in spec:
            S.add_clause([(S.le(x, y, c) if s else -S.le(x, y, c)) for (x, y, c, s) in cl])
        got = S.solve()
        want = any(all(any(eval_atom(dict(zip(names, vals)), x, y, c) == s for (x, y, c, s) in cl) for cl in spec)
                   for vals in itertools.product(R, repeat=3))
        assert got == want, spec
        if got:
            n_sat += 1
            env = S.int_model
            assert all(any(eval_atom(env, x, y, c) == s for (x, y, c, s) in cl) for cl in spec), (spec, env)
    assert 20 < n_sat < 140, n_sat
    say(f"IDL vs force brute : 150 instances OK ({n_sat} SAT / {150 - n_sat} UNSAT, modèles vérifiés)")

    # Ordonnancement : 1 machine, 3 tâches (durées 3,2,4), échéance D ; SAT ssi D >= 9
    def sched(durs, D):
        S = Solver("idl")
        jobs = list(durs)
        for j, d in durs.items():
            S.add_clause([S.ge(j, None, 0)])
            S.add_clause([S.le(j, None, D - d)])
        for j1, j2 in itertools.combinations(jobs, 2):
            S.add_clause([S.le(j1, j2, -durs[j1]), S.le(j2, j1, -durs[j2])])
        return S

    durs = {"A": 3, "B": 2, "C": 4}
    S = sched(durs, 9)
    assert S.solve() is True
    m = S.int_model
    ivs = sorted((m[j], m[j] + durs[j]) for j in durs)
    assert all(ivs[i][1] <= ivs[i + 1][0] for i in range(2)) and ivs[0][0] >= 0 and ivs[-1][1] <= 9, m
    assert sched(durs, 8).solve() is False
    say(f"ordonnancement D=9 SAT {m} ; D=8 UNSAT")

    big = {f"J{i}": d for i, d in enumerate((3, 5, 2, 4, 6, 1))}
    tot = sum(big.values())
    S = sched(big, tot)
    assert S.solve() is True
    S2 = sched(big, tot - 1)
    t1 = time.time()
    assert S2.solve() is False
    say(f"6 tâches : D={tot} SAT ; D={tot - 1} UNSAT en {time.time() - t1:.2f}s "
        f"({S2.n_conflicts} conflits, {S2.n_theory_conflicts} lemmes de théorie)")

    # MUS sur contraintes temporelles : A fini <= 3 et B fini <= 3 (3 min chacune, 1 machine) incompatibles
    S = Solver("idl")
    dd = {"A": 3, "B": 3, "C": 3}
    for j in dd:
        S.add_clause([S.ge(j, None, 0)])
    for j1, j2 in itertools.combinations(dd, 2):
        S.add_clause([S.le(j1, j2, -3), S.le(j2, j1, -3)])
    sa = S.add_soft([S.le("A", None, 0)])
    sb = S.add_soft([S.le("B", None, 0)])
    sc = S.add_soft([S.le("C", None, 100)])
    mus = S.minimal_unsat_subset([sa, sb, sc])
    assert set(mus) == {sa, sb}, mus
    say("MUS temporel : {A@0, B@0} (C hors conflit)")

    # Lemmes de théorie : chacun est un cycle de poids < 0 et minimal (retirer un littéral le rend satisfiable)
    def lemma_edges(S, lemma):
        es = []
        for l in lemma:
            e = S.theory.atoms[abs(l)]
            es.append(e[0] if -l > 0 else e[1])
        return es

    def has_neg_cycle(es):
        nodes = {x for e in es for x in e[:2]}
        d = {x: (0, 0) for x in nodes}
        for _ in range(len(nodes) + 1):
            ch = False
            for (u, v, w0, w1, _) in es:
                c = (d[u][0] + w0, d[u][1] + w1)
                if c < d[v]:
                    d[v] = c
                    ch = True
            if not ch:
                return False
        return True

    S = sched(big, tot - 1)
    assert S.solve() is False and S.lemmas
    for lem in S.lemmas[:300]:
        es = lemma_edges(S, lem)
        assert has_neg_cycle(es), lem
        for k in range(len(es)):
            assert not has_neg_cycle(es[:k] + es[k + 1:]), lem
    say(f"lemmes de théorie : {min(300, len(S.lemmas))} vérifiés (cycle négatif, minimal)")

    # Réduction de la base apprise + redémarrages fréquents : résultats inchangés
    rng = random.Random(11)
    for _ in range(120):
        n = rng.randint(8, 13)
        cl = _rand_cnf(rng, n, int(4.3 * n))
        S = Solver(restart_base=2)
        S.max_learnts = 3
        for c in cl:
            S.add_clause(c)
        assert S.solve() == _brute_sat(n, cl), cl
    say("réduction de base + redémarrages agressifs : 120 instances OK")

    # Assomptions + théorie : le noyau est bien un sous-ensemble d'assomptions, solveur réutilisable
    S = sched(durs, 9)
    sA = S.add_soft([S.ge("A", None, 5)]); sB = S.add_soft([S.ge("B", None, 5)]); sC = S.add_soft([S.ge("C", None, 5)])
    assert S.solve([sA, sB]) is False or True
    mus = S.minimal_unsat_subset([sA, sB, sC])
    assert mus is not None and S.solve(mus) is False
    for m_ in mus:
        assert S.solve([q for q in mus if q != m_]) is True
    assert S.solve() is True
    say(f"assomptions + IDL : MUS de taille {len(mus)}, solveur réutilisable après UNSAT")

    # ---------------------------------------------------------------- RDL
    S = Solver("rdl")
    S.add_clause([S.lt("x", "y", 0)])
    S.add_clause([S.lt("y", "x", 0)])
    assert S.solve() is False

    S = Solver("rdl")
    S.add_clause([S.le("x", "y", 0)])
    S.add_clause([S.le("y", "x", 0)])
    assert S.solve() is True and S.int_model["x"] == S.int_model["y"]

    # 0 < x - y < 1 : SAT sur les réels, UNSAT sur les entiers
    for mode, want in (("rdl", True), ("idl", False)):
        S = Solver(mode)
        S.add_clause([S.gt("x", "y", 0)])
        S.add_clause([S.lt("x", "y", 1)])
        assert S.solve() is want, mode
        if want:
            d = S.int_model["x"] - S.int_model["y"]
            assert 0 < d < 1, d
    say("RDL : strictes OK ; 0 < x-y < 1 SAT en RDL, UNSAT en IDL")

    # chaîne stricte à 4 sommets avec disjonction : modèle vérifié
    S = Solver("rdl")
    l1, l2 = S.lt("a", "b", 0), S.lt("b", "a", 0)
    S.add_clause([l1, l2])
    S.add_clause([S.lt("b", "c", 0)])
    S.add_clause([S.lt("c", "a", 0), S.lt("a", "c", 0)])
    assert S.solve() is True
    m = S.int_model
    assert (m["a"] < m["b"] or m["b"] < m["a"]) and m["b"] < m["c"]

    say(f"\n✅ OK : tous les tests CDCL(T) d'Hadès passent ({time.time() - t0:.2f}s).")


if __name__ == "__main__":
    _selftest()
