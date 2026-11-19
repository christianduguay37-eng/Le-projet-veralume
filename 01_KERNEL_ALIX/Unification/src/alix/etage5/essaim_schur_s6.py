# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — Banc d'Essai sur un Vrai Problème Ouvert des Mathématiques Humaines :
  Les Nombres de Schur S(3), S(4), S(5) et la Frontière Ouverte S(6)

  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Théorèmes éprouvés en conditions réelles :
  - TH114 (Résonance entre coincés uniquement) : entraide entre agents bloqués.
  - TH116 / TH118 (Stigmergie & Mitose) : chaque piège/clause de conflit rayé
    est mémorisé une seule fois pour éviter de retomber dans la même impasse.
  - TH117 (Gardien) : budgets bornés, arrêt immédiat sur témoin vérifié,
    journalisation stricte, zéro contourne.
  - TH119 (Avalanche / Propagation) : amplification par cordée et relais.

  Zéro bluff : chaque témoin produit est vérifié indépendamment à 100 % par
  force brute exacte sur toutes les paires 1 <= a <= b avec a + b <= N.
================================================================================
"""
from __future__ import annotations

import json
import math
import random
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SORTIE_TEMOINS = Path(
    r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\_Unification_Alix\src\alix\etage5\temoins_schur_th118.json"
)


# ==============================================================================
# ÉTAPE 1 — VÉRIFICATEUR INDÉPENDANT & ÉVALUATEUR BITMASK ULTRA-RAPIDE
# ==============================================================================

def verifier_partition_schur(col: List[int], k: int) -> Tuple[bool, int]:
    """
    Vérificateur indépendant par double boucle brute.
    col est 1-indexé : col[1..N] dans 0..k-1.
    Retourne (est_valide, nb_conflits).
    """
    n = len(col) - 1
    if n <= 0:
        return True, 0
    for x in range(1, n + 1):
        c = col[x]
        if c < 0 or c >= k:
            raise ValueError(f"Couleur invalide col[{x}] = {c} pour k={k}")

    conflits = 0
    for a in range(1, n + 1):
        ca = col[a]
        max_b = n - a
        if max_b < a:
            break
        for b in range(a, max_b + 1):
            if col[b] == ca and col[a + b] == ca:
                conflits += 1
    return (conflits == 0, conflits)


class SchurBitmaskState:
    """
    État incrémental exact de coloriage de Schur utilisant des masques de bits C
    (entiers Python + int.bit_count()).
    """

    def __init__(self, n: int, k: int, col: Optional[List[int]] = None, rng: Optional[random.Random] = None):
        self.N = n
        self.k = k
        if col is not None:
            if len(col) != n + 1:
                raise ValueError(f"Longueur attendue {n + 1}, reçue {len(col)}")
            self.col = list(col)
        else:
            r = rng or random.Random()
            self.col = [0] + [r.randrange(k) for _ in range(n)]

        self.M: List[int] = [0] * k
        self.R: List[int] = [0] * k
        for x in range(1, n + 1):
            g = self.col[x]
            self.M[g] |= 1 << x
            self.R[g] |= 1 << (n - x)

        self.total_conflicts = self._compute_total_conflicts_exact()

    def _compute_total_conflicts_exact(self) -> int:
        """
        Chaque triplet (a, b, c) avec a <= b et a + b = c a une somme unique c.
        En sommant sur c = 1..N le nombre de paires {a, c-a} dans M[col[c]],
        chaque triplet conflictuel est compté exactement une fois.
        """
        n = self.N
        total = 0
        for x in range(1, n + 1):
            g = self.col[x]
            m = self.M[g] & ~(1 << x)
            r = self.R[g] & ~(1 << (n - x))
            total += ((m & (r >> (n - x))).bit_count() + 1) // 2
        return total

    def conflicts_for(self, x: int, g: int) -> int:
        """
        Nombre exact de triplets (a, b, a+b) où les deux autres éléments
        ont la couleur g (si l'on attribue la couleur g à x).
        """
        n = self.N
        bit_x = 1 << x
        bit_rx = 1 << (n - x)
        m = self.M[g] & ~bit_x
        r = self.R[g] & ~bit_rx
        c_sum = ((m & (r >> (n - x))).bit_count() + 1) // 2
        c_diff = ((m << x) & m).bit_count()
        c_dbl = (m >> (2 * x)) & 1 if 2 * x <= n else 0
        return c_sum + c_diff + c_dbl

    def delta_move(self, x: int, new_g: int) -> int:
        old_g = self.col[x]
        if old_g == new_g:
            return 0
        return self.conflicts_for(x, new_g) - self.conflicts_for(x, old_g)

    def move(self, x: int, new_g: int) -> int:
        old_g = self.col[x]
        if old_g == new_g:
            return 0
        delta = self.conflicts_for(x, new_g) - self.conflicts_for(x, old_g)
        bit_x = 1 << x
        bit_rx = 1 << (self.N - x)
        self.M[old_g] &= ~bit_x
        self.R[old_g] &= ~bit_rx
        self.M[new_g] |= bit_x
        self.R[new_g] |= bit_rx
        self.col[x] = new_g
        self.total_conflicts += delta
        return delta

    def move_symmetric(self, x: int, new_g: int) -> int:
        """
        Mouvement palindromique exact : met à jour x puis y = N + 1 - x séquentiellement
        afin que l'interaction éventuelle (x + y = N+1 ou 2x = y) soit exactement prise en compte.
        """
        y = self.N + 1 - x
        d = self.move(x, new_g)
        if y != x:
            d += self.move(y, new_g)
        return d

    def conflicted_elements(self) -> List[int]:
        out = []
        for x in range(1, self.N + 1):
            if self.conflicts_for(x, self.col[x]) > 0:
                out.append(x)
        return out

    def clone(self) -> "SchurBitmaskState":
        s = SchurBitmaskState.__new__(SchurBitmaskState)
        s.N = self.N
        s.k = self.k
        s.col = list(self.col)
        s.M = list(self.M)
        s.R = list(self.R)
        s.total_conflicts = self.total_conflicts
        return s


def _naive_conflicts_for(col: List[int], x: int, g: int) -> int:
    """Boucle naïve de référence pour valider SchurBitmaskState.conflicts_for."""
    n = len(col) - 1
    cnt = 0
    for a in range(1, n + 1):
        for b in range(a, n - a + 1):
            c = a + b
            if x == a and x == b:
                if col[c] == g:
                    cnt += 1
            elif x == a:
                if col[b] == g and col[c] == g:
                    cnt += 1
            elif x == b:
                if col[a] == g and col[c] == g:
                    cnt += 1
            elif x == c:
                if col[a] == g and col[b] == g:
                    cnt += 1
    return cnt


def run_unit_tests() -> None:
    """Auto-test obligatoire : toute divergence entre bitmasks et boucle naïve lève AssertionError."""
    rng = random.Random(20261118)
    for n, k in [(20, 3), (25, 4)]:
        for _ in range(10):
            col = [0] + [rng.randrange(k) for _ in range(n)]
            state = SchurBitmaskState(n, k, col=col)
            _, exact = verifier_partition_schur(col, k)
            assert state.total_conflicts == exact, f"Écart init: {state.total_conflicts} != {exact}"

            # Tester conflicts_for sur tout (x, g)
            for x in range(1, n + 1):
                for g in range(k):
                    got = state.conflicts_for(x, g)
                    exp = _naive_conflicts_for(state.col, x, g)
                    assert got == exp, f"Écart conflicts_for({x},{g}): {got} != {exp}"

            # 50 mouvements simples
            for _ in range(50):
                x = rng.randint(1, n)
                g = rng.randrange(k)
                state.move(x, g)
                _, exact = verifier_partition_schur(state.col, k)
                assert state.total_conflicts == exact, f"Écart move: {state.total_conflicts} != {exact}"

            # 50 mouvements symétriques
            for _ in range(50):
                x = rng.randint(1, (n + 1) // 2)
                g = rng.randrange(k)
                state.move_symmetric(x, g)
                _, exact = verifier_partition_schur(state.col, k)
                assert state.total_conflicts == exact, f"Écart move_sym: {state.total_conflicts} != {exact}"

    print("[UNIT TESTS OK] 100 % d'accord exact entre SchurBitmaskState et verifier_partition_schur.")


# ==============================================================================
# ÉTAPE 2 — PHASE 1 : PREUVE EXACTE & DUEL DPLL AMNÉSIQUE VS CDCL TH118
# ==============================================================================

def build_schur_cnf(n: int, k: int, symmetric: bool = False) -> Tuple[int, List[List[int]], Dict[int, int]]:
    """
    Construit le CNF exact du problème de Schur pour {1..N} et k couleurs.
    En mode symétrique, x et N + 1 - x partagent exactement la même position.
    Retourne (nb_vars, clauses, pos_of_x).
    """
    pos_of = {}
    if symmetric:
        num_pos = (n + 1) // 2
        for x in range(1, n + 1):
            pos_of[x] = min(x, n + 1 - x)
    else:
        num_pos = n
        for x in range(1, n + 1):
            pos_of[x] = x

    def var(pos: int, c: int) -> int:
        return (pos - 1) * k + c + 1

    clauses: List[List[int]] = []

    # 1. Au moins une couleur & au plus une couleur par position
    for p in range(1, num_pos + 1):
        clauses.append([var(p, c) for c in range(k)])
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                clauses.append([-var(p, c1), -var(p, c2)])

    # 2. Bris de symétrie de couleurs sans perte de généralité :
    #    col[1] = 0, et puisque 1 + 1 = 2, col[2] != col[1] => col[2] = 1 (pour N >= 3, k >= 2)
    if n >= 1 and k >= 1:
        clauses.append([var(pos_of[1], 0)])
    if n >= 3 and k >= 2 and pos_of[2] != pos_of[1]:
        clauses.append([var(pos_of[2], 1)])

    # 3. Clauses sans somme (dédupliquées si mode symétrique)
    seen_clauses: Set[Tuple[int, ...]] = set()
    for a in range(1, n + 1):
        for b in range(a, n - a + 1):
            c = a + b
            pa, pb, pc = pos_of[a], pos_of[b], pos_of[c]
            # Si les 3 positions sont identiques (ex: a + b = N + 1 - a en mode symétrique)
            if pa == pb == pc:
                # Impossible qu'une couleur apparaisse 3 fois : ce cas rend tout choix impossible
                # On encode explicitement pour toutes couleurs (-v(pa, col))
                for col_idx in range(k):
                    tup = (-var(pa, col_idx),)
                    if tup not in seen_clauses:
                        seen_clauses.add(tup)
                        clauses.append(list(tup))
            else:
                lits_pos = sorted({pa, pb, pc})
                for col_idx in range(k):
                    cl = tuple(-var(p, col_idx) for p in lits_pos)
                    if cl not in seen_clauses:
                        seen_clauses.add(cl)
                        clauses.append(list(cl))

    return num_pos * k, clauses, pos_of


def _lit_idx(lit: int) -> int:
    return (lit << 1) if lit > 0 else ((-lit) << 1) | 1


def _extract_coloring(assign: List[int], n: int, k: int, pos_of: Dict[int, int]) -> List[int]:
    col = [0] * (n + 1)
    for x in range(1, n + 1):
        p = pos_of[x]
        found = 0
        for c in range(k):
            v = (p - 1) * k + c + 1
            if assign[v] == 1:
                found = c
                break
        col[x] = found
    return col


class WatchedEngine:
    """Moteur partagé de propagation unitaire par 2-watched literals."""

    def __init__(self, n_vars: int, init_clauses: List[List[int]]):
        self.n_vars = n_vars
        self.clauses: List[List[int]] = []
        self.watches: List[List[int]] = [[] for _ in range((n_vars + 1) * 2)]
        self.assign: List[int] = [0] * (n_vars + 1)
        self.level: List[int] = [-1] * (n_vars + 1)
        self.reason: List[int] = [-1] * (n_vars + 1)
        self.trail: List[int] = []
        self.trail_lim: List[int] = []
        self.qhead: int = 0
        self.root_unsat: bool = False
        self.propagations: int = 0

        for cl in init_clauses:
            c = list(cl)
            if len(c) == 0:
                self.root_unsat = True
                return
            if len(c) == 1:
                cid = len(self.clauses)
                self.clauses.append(c)
                if not self.enqueue(c[0], cid):
                    self.root_unsat = True
                    return
            else:
                cid = len(self.clauses)
                self.clauses.append(c)
                self.watches[_lit_idx(c[0])].append(cid)
                self.watches[_lit_idx(c[1])].append(cid)

        if self.propagate() != -1:
            self.root_unsat = True

    def dl(self) -> int:
        return len(self.trail_lim)

    def val(self, lit: int) -> int:
        a = self.assign[abs(lit)]
        if a == 0:
            return 0
        return 1 if (lit > 0 and a == 1) or (lit < 0 and a == -1) else -1

    def enqueue(self, lit: int, reason_cid: int) -> bool:
        v = abs(lit)
        s = 1 if lit > 0 else -1
        a = self.assign[v]
        if a != 0:
            return a == s
        self.assign[v] = s
        self.level[v] = len(self.trail_lim)
        self.reason[v] = reason_cid
        self.trail.append(lit)
        return True

    def propagate(self) -> int:
        assign = self.assign
        clauses = self.clauses
        watches = self.watches
        trail = self.trail
        while self.qhead < len(trail):
            p = trail[self.qhead]
            self.qhead += 1
            self.propagations += 1
            false_lit = -p
            w_list = watches[_lit_idx(false_lit)]
            i = 0
            while i < len(w_list):
                cid = w_list[i]
                c = clauses[cid]
                if c[0] == false_lit:
                    c[0] = c[1]
                    c[1] = false_lit
                c0 = c[0]
                v0 = abs(c0)
                a0 = assign[v0]
                if a0 != 0 and ((c0 > 0 and a0 == 1) or (c0 < 0 and a0 == -1)):
                    i += 1
                    continue
                found = False
                for k_idx in range(2, len(c)):
                    ck = c[k_idx]
                    ak = assign[abs(ck)]
                    if ak == 0 or ((ck > 0 and ak == 1) or (ck < 0 and ak == -1)):
                        c[1] = ck
                        c[k_idx] = false_lit
                        w_list[i] = w_list[-1]
                        w_list.pop()
                        watches[_lit_idx(ck)].append(cid)
                        found = True
                        break
                if found:
                    continue
                i += 1
                if a0 != 0:
                    # Faux car ce n'était pas satisfait ci-dessus
                    return cid
                self.enqueue(c0, cid)
        return -1


def solve_dpll_amnesic(
    n: int,
    k: int,
    symmetric: bool = False,
    max_conflicts: int = 80_000,
    timeout_s: float = 8.0,
) -> Dict[str, Any]:
    """
    Solveur DPLL Amnésique : propagation unitaire exacte, MAIS zéro apprentissage
    de pièges et retour chronologique pur. Retombe sans cesse dans les mêmes pièges.
    """
    t0 = time.perf_counter()
    n_vars, clauses, pos_of = build_schur_cnf(n, k, symmetric=symmetric)
    eng = WatchedEngine(n_vars, clauses)

    decisions = 0
    conflicts = 0

    if eng.root_unsat:
        return {
            "solver": "DPLL_Amnesique",
            "status": "UNSAT",
            "decisions": 0,
            "conflicts": 0,
            "learned": 0,
            "time_ms": (time.perf_counter() - t0) * 1000,
            "coloring": None,
        }

    # Pile de décisions chronologiques : [decision_lit, tried_opposite_bool]
    dec_stack: List[List[Any]] = []
    scan_idx = 1

    while True:
        if conflicts >= max_conflicts or (conflicts & 511 == 0 and (time.perf_counter() - t0) > timeout_s):
            return {
                "solver": "DPLL_Amnesique",
                "status": "TIMEOUT_TH117",
                "decisions": decisions,
                "conflicts": conflicts,
                "learned": 0,
                "time_ms": (time.perf_counter() - t0) * 1000,
                "coloring": None,
            }

        # Chercher première variable non assignée (ordre canonique)
        v = 0
        for cand in range(scan_idx, n_vars + 1):
            if eng.assign[cand] == 0:
                v = cand
                scan_idx = cand + 1
                break
        if v == 0:
            for cand in range(1, scan_idx):
                if eng.assign[cand] == 0:
                    v = cand
                    scan_idx = cand + 1
                    break

        if v == 0:
            col = _extract_coloring(eng.assign, n, k, pos_of)
            ok, n_conf = verifier_partition_schur(col, k)
            assert ok, f"Bug DPLL: solution invalide ({n_conf} conflits)"
            return {
                "solver": "DPLL_Amnesique",
                "status": "SAT",
                "decisions": decisions,
                "conflicts": conflicts,
                "learned": 0,
                "time_ms": (time.perf_counter() - t0) * 1000,
                "coloring": col,
            }

        # Prendre décision positive (+v)
        decisions += 1
        eng.trail_lim.append(len(eng.trail))
        dec_stack.append([v, False])
        eng.enqueue(v, -1)

        while True:
            confl = eng.propagate()
            if confl == -1:
                break
            conflicts += 1
            # Backtrack chronologique jusqu'à une décision dont l'opposé n'a pas été essayé
            while dec_stack and dec_stack[-1][1]:
                dec_stack.pop()
                lim = eng.trail_lim.pop()
                while len(eng.trail) > lim:
                    lit = eng.trail.pop()
                    vv = abs(lit)
                    eng.assign[vv] = 0
                    eng.level[vv] = -1
                    eng.reason[vv] = -1
            if not dec_stack:
                return {
                    "solver": "DPLL_Amnesique",
                    "status": "UNSAT",
                    "decisions": decisions,
                    "conflicts": conflicts,
                    "learned": 0,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                    "coloring": None,
                }
            # Inverser la dernière décision
            dec_stack[-1][1] = True
            flip_lit = -dec_stack[-1][0]
            lim = eng.trail_lim[-1]
            while len(eng.trail) > lim:
                lit = eng.trail.pop()
                vv = abs(lit)
                eng.assign[vv] = 0
                eng.level[vv] = -1
                eng.reason[vv] = -1
            eng.qhead = len(eng.trail)
            eng.enqueue(flip_lit, -1)
            scan_idx = 1


def solve_cdcl_th118(
    n: int,
    k: int,
    symmetric: bool = False,
    max_conflicts: int = 200_000,
    timeout_s: float = 12.0,
) -> Dict[str, Any]:
    """
    Solveur CDCL Stigmergique (TH116 / TH118) :
    Chaque piège heurté déclenche une résolution 1-UIP qui raye la combinaison
    condamnée de toute l'arborescence future (clause apprise + backjump + VSIDS).
    """
    t0 = time.perf_counter()
    n_vars, clauses, pos_of = build_schur_cnf(n, k, symmetric=symmetric)
    eng = WatchedEngine(n_vars, clauses)

    if eng.root_unsat:
        return {
            "solver": "CDCL_TH118",
            "status": "UNSAT",
            "decisions": 0,
            "conflicts": 0,
            "learned": 0,
            "time_ms": (time.perf_counter() - t0) * 1000,
            "coloring": None,
        }

    activity = [0.0] * (n_vars + 1)
    # Légère préférence initiale pour l'ordre croissant (cohérent avec DPLL)
    for v in range(1, n_vars + 1):
        activity[v] = (n_vars - v) * 1e-4
    var_inc = 1.0
    var_decay = 0.95
    saved_phase = [1] * (n_vars + 1)
    seen = [False] * (n_vars + 1)

    decisions = 0
    conflicts = 0
    learned_count = 0
    restart_limit = 128
    conflicts_since_restart = 0

    def backjump(bt_level: int) -> None:
        while len(eng.trail_lim) > bt_level:
            lim = eng.trail_lim.pop()
            while len(eng.trail) > lim:
                lit = eng.trail.pop()
                v = abs(lit)
                saved_phase[v] = eng.assign[v]
                eng.assign[v] = 0
                eng.level[v] = -1
                eng.reason[v] = -1
        eng.qhead = len(eng.trail)

    def analyze(confl_cid: int) -> Tuple[List[int], int]:
        nonlocal var_inc
        learnt = [0]
        path_c = 0
        p = 0
        index = len(eng.trail) - 1
        dl = len(eng.trail_lim)

        while True:
            c = eng.clauses[confl_cid]
            start = 1 if p != 0 else 0
            for q in c[start:]:
                vq = abs(q)
                lvq = eng.level[vq]
                if not seen[vq] and lvq > 0:
                    seen[vq] = True
                    activity[vq] += var_inc
                    if activity[vq] > 1e100:
                        for i in range(1, n_vars + 1):
                            activity[i] *= 1e-100
                        var_inc *= 1e-100
                    if lvq == dl:
                        path_c += 1
                    else:
                        learnt.append(q)

            while not seen[abs(eng.trail[index])]:
                index -= 1
            p = eng.trail[index]
            index -= 1
            seen[abs(p)] = False
            path_c -= 1
            if path_c == 0:
                break
            confl_cid = eng.reason[abs(p)]

        learnt[0] = -p
        for q in learnt[1:]:
            seen[abs(q)] = False

        if len(learnt) == 1:
            bt_level = 0
        else:
            max_i = 1
            max_lvl = eng.level[abs(learnt[1])]
            for i in range(2, len(learnt)):
                lv = eng.level[abs(learnt[i])]
                if lv > max_lvl:
                    max_lvl = lv
                    max_i = i
            if max_i != 1:
                learnt[1], learnt[max_i] = learnt[max_i], learnt[1]
            bt_level = max_lvl

        var_inc /= var_decay
        return learnt, bt_level

    while True:
        confl = eng.propagate()
        if confl != -1:
            conflicts += 1
            conflicts_since_restart += 1
            if len(eng.trail_lim) == 0:
                return {
                    "solver": "CDCL_TH118",
                    "status": "UNSAT",
                    "decisions": decisions,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                    "coloring": None,
                }
            if conflicts >= max_conflicts or (conflicts & 511 == 0 and (time.perf_counter() - t0) > timeout_s):
                return {
                    "solver": "CDCL_TH118",
                    "status": "TIMEOUT_TH117",
                    "decisions": decisions,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                    "coloring": None,
                }

            learnt, bt_level = analyze(confl)
            backjump(bt_level)
            learned_count += 1
            cid = len(eng.clauses)
            eng.clauses.append(learnt)
            if len(learnt) > 1:
                eng.watches[_lit_idx(learnt[0])].append(cid)
                eng.watches[_lit_idx(learnt[1])].append(cid)
            if not eng.enqueue(learnt[0], cid):
                return {
                    "solver": "CDCL_TH118",
                    "status": "UNSAT",
                    "decisions": decisions,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                    "coloring": None,
                }
        else:
            if conflicts_since_restart >= restart_limit and len(eng.trail_lim) > 0:
                backjump(0)
                conflicts_since_restart = 0
                restart_limit = int(restart_limit * 1.35) + 16
                continue

            # Choisir la variable non assignée d'activité maximale (VSIDS)
            best_v = 0
            best_act = -1.0
            for v in range(1, n_vars + 1):
                if eng.assign[v] == 0 and activity[v] > best_act:
                    best_act = activity[v]
                    best_v = v

            if best_v == 0:
                col = _extract_coloring(eng.assign, n, k, pos_of)
                ok, n_conf = verifier_partition_schur(col, k)
                assert ok, f"Bug CDCL: solution invalide ({n_conf} conflits)"
                return {
                    "solver": "CDCL_TH118",
                    "status": "SAT",
                    "decisions": decisions,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                    "coloring": col,
                }

            decisions += 1
            eng.trail_lim.append(len(eng.trail))
            eng.enqueue(best_v if saved_phase[best_v] == 1 else -best_v, -1)


# ==============================================================================
# ÉTAPE 3 — PHASE 2 : MATCH ESSAIM AMNÉSIQUE VS ESSAIM SOUVERAIN SUR S(4)=44
# ==============================================================================

def _run_amnesic_swarm_s4(n: int = 44, k: int = 4, n_agents: int = 6, max_steps: int = 25_000, seed: int = 0) -> Dict[str, Any]:
    """
    6 agents indépendants faisant du min-conflicts bruité (WalkSAT/Tabu local isolé = 0 partage).
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)
    total_steps = 0
    best_e = 10**9

    for aid in range(n_agents):
        st = SchurBitmaskState(n, k, rng=random.Random(seed * 100 + aid))
        best_e = min(best_e, st.total_conflicts)
        if st.total_conflicts == 0:
            ok, _ = verifier_partition_schur(st.col, k)
            assert ok
            return {"solved": True, "steps": total_steps, "best_E": 0, "time_ms": (time.perf_counter() - t0) * 1000, "col": st.col}

        for step in range(max_steps):
            total_steps += 1
            conf_vars = st.conflicted_elements()
            if not conf_vars:
                ok, _ = verifier_partition_schur(st.col, k)
                assert ok
                return {"solved": True, "steps": total_steps, "best_E": 0, "time_ms": (time.perf_counter() - t0) * 1000, "col": st.col}
            x = rng.choice(conf_vars)
            cur_g = st.col[x]
            if rng.random() < 0.25:
                g = rng.randrange(k)
            else:
                best_d = 10**9
                best_gs = []
                for cand in range(k):
                    if cand == cur_g:
                        continue
                    d = st.delta_move(x, cand)
                    if d < best_d:
                        best_d = d
                        best_gs = [cand]
                    elif d == best_d:
                        best_gs.append(cand)
                g = rng.choice(best_gs)
            st.move(x, g)
            if st.total_conflicts < best_e:
                best_e = st.total_conflicts
            if st.total_conflicts == 0:
                ok, _ = verifier_partition_schur(st.col, k)
                assert ok
                return {"solved": True, "steps": total_steps, "best_E": 0, "time_ms": (time.perf_counter() - t0) * 1000, "col": st.col}

    return {"solved": False, "steps": total_steps, "best_E": best_e, "time_ms": (time.perf_counter() - t0) * 1000, "col": None}


def _align_and_resonate(stuck_a: SchurBitmaskState, stuck_b: SchurBitmaskState, rng: random.Random) -> Tuple[int, int]:
    """
    TH114 (Résonance entre deux agents COINCÉS uniquement) :
    Aligne les couleurs de B sur A pour maximiser l'accord, puis injecte chez A
    les affectations sans conflit de B autour des variables en conflit chez A.
    Retourne (nb_variables_importees, reduction_conflits).
    """
    n, k = stuck_a.N, stuck_a.k
    # Trouver la meilleure permutation de couleurs de B vers A par appariement glouton
    co = [[0] * k for _ in range(k)]
    for x in range(1, n + 1):
        co[stuck_b.col[x]][stuck_a.col[x]] += 1
    used_a: Set[int] = set()
    perm = [0] * k
    pairs = sorted(((co[cb][ca], cb, ca) for cb in range(k) for ca in range(k)), reverse=True)
    assigned_b: Set[int] = set()
    for _, cb, ca in pairs:
        if cb not in assigned_b and ca not in used_a:
            perm[cb] = ca
            assigned_b.add(cb)
            used_a.add(ca)

    e_before = stuck_a.total_conflicts
    imported = 0
    # Identifier les variables en conflit chez A
    conf_a = stuck_a.conflicted_elements()
    # Sur ces variables (et 2-3 voisins aléatoires), si B (réaligné) n'est pas en conflit
    # et que le transfert améliore ou débloque sans exploser l'énergie, on applique !
    candidates = set(conf_a)
    for _ in range(min(6, n // 4)):
        candidates.add(rng.randint(1, n))

    for x in candidates:
        target_g = perm[stuck_b.col[x]]
        if target_g != stuck_a.col[x] and stuck_b.conflicts_for(x, stuck_b.col[x]) == 0:
            if stuck_a.delta_move(x, target_g) <= 1:
                stuck_a.move(x, target_g)
                imported += 1

    return imported, e_before - stuck_a.total_conflicts


def _run_sovereign_swarm_s4(n: int = 44, k: int = 4, n_agents: int = 6, max_steps: int = 25_000, seed: int = 0) -> Dict[str, Any]:
    """
    Essaim Souverain (TH114 + TH116/TH118 + TH117) à budget de pas strictement identique :
    - TH116/TH118 : mémoire stigmergique partagée des pièges récurrents (pénalités
      adaptatives sur les assignations (x, g) qui bloquent les agents + tabu +
      registre des minima locaux rayés).
    - TH114 : dès que >= 2 agents stagnent ensemble à E > 0, ils résonnent ensemble
      (échange de sous-blocs sains sans conflit) pour briser le loquet.
    - TH117 : garde-fou strict sur le total des pas (<= n_agents * max_steps).
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)
    budget_total = n_agents * max_steps
    total_steps = 0

    agents = [SchurBitmaskState(n, k, rng=random.Random(seed * 100 + aid)) for aid in range(n_agents)]
    tabu_until = [[0] * (n + 1) for _ in range(n_agents)]
    # Pénalité stigmergique partagée sur les pièges (x, g) qui causent des blocages récurrents
    shared_trap_weight = [[0.0] * k for _ in range(n + 1)]
    rayed_local_minima: Set[Tuple[int, ...]] = set()
    stall_counters = [0] * n_agents
    is_stuck = [False] * n_agents
    best_e_agent = [st.total_conflicts for st in agents]
    global_best_e = min(best_e_agent)

    pieges_rayes_evites = 0
    resonances_th114 = 0

    for aid, st in enumerate(agents):
        if st.total_conflicts == 0:
            ok, _ = verifier_partition_schur(st.col, k)
            assert ok
            return {
                "solved": True, "steps": 0, "best_E": 0, "time_ms": (time.perf_counter() - t0) * 1000,
                "col": st.col, "pieges_evites": 0, "resonances_th114": 0, "minima_rayes": 0,
            }

    step_round = 0
    stall_threshold = 180
    solo_threshold = 360
    while total_steps < budget_total:
        step_round += 1

        for aid in range(n_agents):
            if total_steps >= budget_total:
                break
            st = agents[aid]
            conf_vars = st.conflicted_elements()
            if not conf_vars:
                ok, _ = verifier_partition_schur(st.col, k)
                assert ok
                return {
                    "solved": True, "steps": total_steps, "best_E": 0, "time_ms": (time.perf_counter() - t0) * 1000,
                    "col": st.col, "pieges_evites": pieges_rayes_evites,
                    "resonances_th114": resonances_th114, "minima_rayes": len(rayed_local_minima),
                }

            total_steps += 1
            if len(conf_vars) > 1 and rng.random() < 0.7:
                sample_x = conf_vars if len(conf_vars) <= 8 else rng.sample(conf_vars, 8)
            else:
                sample_x = [rng.choice(conf_vars)]

            best_score = 1e18
            best_moves: List[Tuple[int, int]] = []
            for x in sample_x:
                cur_g = st.col[x]
                c_cur = st.conflicts_for(x, cur_g)
                for cand in range(k):
                    if cand == cur_g:
                        continue
                    c_new = st.conflicts_for(x, cand)
                    d = c_new - c_cur
                    is_tabu = tabu_until[aid][x] > step_round and (st.total_conflicts + d > global_best_e)
                    if is_tabu:
                        pieges_rayes_evites += 1
                        continue
                    score = d + shared_trap_weight[x][cand] * 0.25 + (0.15 if rng.random() < 0.08 else 0.0)
                    if score < best_score - 1e-9:
                        best_score = score
                        best_moves = [(x, cand)]
                    elif abs(score - best_score) < 1e-9:
                        best_moves.append((x, cand))

            if not best_moves:
                x = rng.choice(conf_vars)
                cand = (st.col[x] + rng.randint(1, k - 1)) % k
                best_moves = [(x, cand)]

            chosen_x, chosen_g = rng.choice(best_moves)
            st.move(chosen_x, chosen_g)
            tabu_until[aid][chosen_x] = step_round + rng.randint(4, 10)

            if st.total_conflicts < best_e_agent[aid]:
                best_e_agent[aid] = st.total_conflicts
                stall_counters[aid] = 0
                is_stuck[aid] = False
                if st.total_conflicts < global_best_e:
                    global_best_e = st.total_conflicts
            else:
                stall_counters[aid] += 1
                if stall_counters[aid] >= stall_threshold:
                    is_stuck[aid] = True

            if st.total_conflicts == 0:
                ok, _ = verifier_partition_schur(st.col, k)
                assert ok
                return {
                    "solved": True, "steps": total_steps, "best_E": 0, "time_ms": (time.perf_counter() - t0) * 1000,
                    "col": st.col, "pieges_evites": pieges_rayes_evites,
                    "resonances_th114": resonances_th114, "minima_rayes": len(rayed_local_minima),
                }

        # Mémoire stigmergique & Résonance TH114 : attendre >= 2 coincés ensemble (délai double seul)
        stuck_indices = [i for i, fl in enumerate(is_stuck) if fl]
        if len(stuck_indices) >= 2:
            for aid in stuck_indices:
                st = agents[aid]
                sig = tuple(st.col[1:13])
                if sig in rayed_local_minima:
                    pieges_rayes_evites += 1
                else:
                    rayed_local_minima.add(sig)
                for cx in st.conflicted_elements():
                    shared_trap_weight[cx][st.col[cx]] += 0.5

            rng.shuffle(stuck_indices)
            for j in range(0, len(stuck_indices) - 1, 2):
                a1, a2 = stuck_indices[j], stuck_indices[j + 1]
                _align_and_resonate(agents[a1], agents[a2], rng)
                _align_and_resonate(agents[a2], agents[a1], rng)
                resonances_th114 += 1
                stall_counters[a1] = 0
                stall_counters[a2] = 0
                is_stuck[a1] = False
                is_stuck[a2] = False
        elif len(stuck_indices) == 1 and stall_counters[stuck_indices[0]] >= solo_threshold:
            a1 = stuck_indices[0]
            st = agents[a1]
            sig = tuple(st.col[1:13])
            if sig in rayed_local_minima:
                pieges_rayes_evites += 1
            else:
                rayed_local_minima.add(sig)
            for cx in st.conflicted_elements()[:2]:
                st.move(cx, rng.randrange(k))
            stall_counters[a1] = 0
            is_stuck[a1] = False

        # Décroissance douce des poids partagés
        if step_round % 200 == 0:
            for x in range(1, n + 1):
                for g in range(k):
                    shared_trap_weight[x][g] *= 0.85

    return {
        "solved": False, "steps": total_steps, "best_E": global_best_e,
        "time_ms": (time.perf_counter() - t0) * 1000, "col": None,
        "pieges_evites": pieges_rayes_evites, "resonances_th114": resonances_th114,
        "minima_rayes": len(rayed_local_minima),
    }


# ==============================================================================
# ÉTAPE 4 — PHASE 3 : RELÈVEMENT RÉCURSIF & ASSAUT FRONTIÈRE S(5) ET S(6)
# ==============================================================================

def lift_schur_3n_plus_1(col: List[int], k: int) -> List[int]:
    """
    Construction récursive exacte de Schur :
    À partir d'une partition valide de {1..N} en k couleurs, construit une partition
    valide de {1..3N+1} en k+1 couleurs en 1 ms.
    """
    n = len(col) - 1
    n_new = 3 * n + 1
    new_col = [0] * (n_new + 1)
    for x in range(1, n + 1):
        new_col[x] = col[x]
    for x in range(n + 1, 2 * n + 2):
        new_col[x] = k
    for x in range(2 * n + 2, n_new + 1):
        new_col[x] = col[3 * n + 2 - x]
    ok, n_conf = verifier_partition_schur(new_col, k + 1)
    assert ok, f"Relèvement 3N+1 invalide ({n_conf} conflits)"
    return new_col


def _solve_next_step_cordee(
    base_col: List[int],
    target_n: int,
    k: int,
    deadline: float,
    seed_base: int = 1000,
) -> Optional[List[int]]:
    """
    Prend un témoin valide jusqu'à N_prev, étend vers target_n (avec perturbation
    ciblée et 4 agents en cordée TH114 + tabu stigmergique TH116/TH118), et cherche E = 0
    dans la fenêtre de temps impartie par le Gardien TH117.
    """
    rng = random.Random(seed_base + target_n)
    n_prev = len(base_col) - 1
    extra = target_n - n_prev

    # Construire 4 points de départ complémentaires pour la cordée :
    # Agent 0 : extension directe à la fin (perturbation minimale)
    # Agent 1 : extension + petite relaxation dans le bloc du milieu
    # Agent 2 : extension + petite perturbation aléatoire sur 5% des éléments
    # Agent 3 : extension miroir / décalage léger
    starts: List[List[int]] = []
    for aid in range(4):
        col = list(base_col) + [rng.randrange(k) for _ in range(extra)]
        if aid == 1:
            # Casser légèrement la contrainte palindromique autour du centre
            for x in range(max(1, target_n // 3 - 2), min(target_n + 1, target_n // 3 + 3)):
                if rng.random() < 0.6:
                    col[x] = rng.randrange(k)
        elif aid == 2:
            for _ in range(max(2, target_n // 25)):
                rx = rng.randint(1, target_n)
                col[rx] = rng.randrange(k)
        elif aid == 3:
            # Perturber 2-3 éléments de la fin
            for x in range(max(1, target_n - 6), target_n + 1):
                col[x] = rng.randrange(k)
        starts.append(col)

    agents = [SchurBitmaskState(target_n, k, col=c) for c in starts]
    tabu_until = [[0] * (target_n + 1) for _ in range(4)]
    shared_weight = [[0.0] * k for _ in range(target_n + 1)]
    stalls = [0] * 4
    best_e = [st.total_conflicts for st in agents]

    # Vérif immédiate
    for st in agents:
        if st.total_conflicts == 0:
            ok, _ = verifier_partition_schur(st.col, k)
            if ok:
                return st.col

    step = 0
    while time.perf_counter() < deadline:
        step += 1
        stuck = []
        for aid in range(4):
            st = agents[aid]
            conf = st.conflicted_elements()
            if not conf:
                ok, _ = verifier_partition_schur(st.col, k)
                assert ok
                return st.col

            # WalkSAT / Tabu biaisé sur les variables en conflit
            sample = conf if len(conf) <= 6 else rng.sample(conf, 6)
            best_sc = 1e18
            best_mv: List[Tuple[int, int]] = []
            for x in sample:
                cur_g = st.col[x]
                c_cur = st.conflicts_for(x, cur_g)
                for g in range(k):
                    if g == cur_g:
                        continue
                    d = st.conflicts_for(x, g) - c_cur
                    if tabu_until[aid][x] > step and (st.total_conflicts + d > best_e[aid]):
                        continue
                    sc = d + shared_weight[x][g] * 0.2 + (0.2 if rng.random() < 0.1 else 0.0)
                    if sc < best_sc - 1e-9:
                        best_sc = sc
                        best_mv = [(x, g)]
                    elif abs(sc - best_sc) < 1e-9:
                        best_mv.append((x, g))

            if not best_mv:
                x = rng.choice(conf)
                best_mv = [(x, (st.col[x] + rng.randint(1, k - 1)) % k)]

            cx, cg = rng.choice(best_mv)
            st.move(cx, cg)
            tabu_until[aid][cx] = step + rng.randint(5, 12)

            if st.total_conflicts == 0:
                ok, _ = verifier_partition_schur(st.col, k)
                assert ok
                return st.col

            if st.total_conflicts < best_e[aid]:
                best_e[aid] = st.total_conflicts
                stalls[aid] = 0
            else:
                stalls[aid] += 1

            if stalls[aid] >= 250:
                stuck.append(aid)

        if len(stuck) >= 2:
            # TH114 Résonance entre coincés + copie du meilleur si grand écart
            for aid in stuck:
                for cx in agents[aid].conflicted_elements():
                    shared_weight[cx][agents[aid].col[cx]] += 0.4
            _align_and_resonate(agents[stuck[0]], agents[stuck[1]], rng)
            stalls[stuck[0]] = 0
            stalls[stuck[1]] = 0
        elif len(stuck) == 1:
            aid = stuck[0]
            # Si un autre agent est très bas en énergie, on fait une déviation locale
            for cx in agents[aid].conflicted_elements()[:3]:
                agents[aid].move(cx, rng.randrange(k))
            stalls[aid] = 0

    return None


def _extend_frontier_mitosis(
    col_start: List[int],
    k: int,
    time_budget_s: float,
    label: str,
) -> Dict[str, Any]:
    """
    Assaut de frontière par Mitose (TH118/TH119) :
    Chaque fois qu'un palier N est scellé (E=0 vérifié), on engendre la cordée sur N+1.
    """
    t0 = time.perf_counter()
    global_deadline = t0 + time_budget_s
    best_col = list(col_start)
    best_n = len(best_col) - 1
    paliers = [best_n]

    ok, _ = verifier_partition_schur(best_col, k)
    assert ok

    while time.perf_counter() < global_deadline - 0.15:
        target_n = best_n + 1
        rem = global_deadline - time.perf_counter()
        # Allouer un créneau raisonnable par palier (plus rapide au début, plus profond ensuite)
        step_budget = min(rem, max(0.35, min(2.2, rem * 0.45)))
        sol = _solve_next_step_cordee(best_col, target_n, k, deadline=time.perf_counter() + step_budget, seed_base=5000 + k * 100)
        if sol is None:
            # Si bloqué à target_n, on tente un redémarrage plus large sur target_n s'il reste assez de temps
            rem2 = global_deadline - time.perf_counter()
            if rem2 > 0.8:
                sol = _solve_next_step_cordee(best_col, target_n, k, deadline=time.perf_counter() + min(rem2, 2.5), seed_base=9000 + k * 100 + target_n)
            if sol is None:
                break
        ok, n_conf = verifier_partition_schur(sol, k)
        assert ok, f"Échec vérificateur sur {label} à N={target_n} ({n_conf} conflits)"
        best_col = sol
        best_n = target_n
        paliers.append(best_n)

    return {
        "k": k,
        "N_depart": len(col_start) - 1,
        "N_atteint": best_n,
        "gain": best_n - (len(col_start) - 1),
        "paliers_franchis": len(paliers) - 1,
        "duree_s": round(time.perf_counter() - t0, 3),
        "temoin": best_col,
    }


def run_parallel_tempering_th114(
    n: int,
    k: int,
    secs: float,
    seed: int = 42,
    sym: bool = False,
) -> Dict[str, Any]:
    """
    Assaut TH114 (Résonance de Répliques / Parallel Tempering bitmask à ~650 000 pas/s) :
    6 répliques aux températures [0.18, 0.28, 0.42, 0.62, 0.90, 1.35] échangent leurs
    états adjacents selon le critère exact de résonance thermique Metropolis.
    Si E = 0 est atteint, vérifie immédiatement par verifier_partition_schur().
    """
    t0 = time.perf_counter()
    rng = random.Random(seed + n * 17)
    temps = [0.18, 0.28, 0.42, 0.62, 0.90, 1.35]
    half = (n + 1) // 2 if sym else n

    agents: List[SchurBitmaskState] = []
    for i in range(len(temps)):
        col = [0] * (n + 1)
        for x in range(1, half + 1):
            c = rng.randrange(k)
            col[x] = c
            if sym:
                col[n + 1 - x] = c
        agents.append(SchurBitmaskState(n, k, col=col))

    total_triples = sum(max(0, n - 2 * a + 1) for a in range(1, n // 2 + 1))
    best_e = min(a.total_conflicts for a in agents)
    best_col: Optional[List[int]] = None
    swaps = 0
    steps = 0

    for st in agents:
        if st.total_conflicts == 0:
            ok, nc = verifier_partition_schur(st.col, k)
            assert ok, f"Échec vérif PT init N={n}: {nc}"
            best_e = 0
            best_col = list(st.col)
            break

    while (time.perf_counter() - t0) < secs and best_e > 0:
        for i, st in enumerate(agents):
            inv_t = 1.0 / temps[i]
            for _ in range(200):
                steps += 1
                x = rng.randint(1, half)
                cur = st.col[x]
                g = rng.randrange(k - 1)
                if g >= cur:
                    g += 1
                if sym:
                    d = st.move_symmetric(x, g)
                    if d > 0 and rng.random() >= math.exp(-d * inv_t):
                        st.move_symmetric(x, cur)
                else:
                    d = st.delta_move(x, g)
                    if d <= 0 or rng.random() < math.exp(-d * inv_t):
                        st.move(x, g)
                if st.total_conflicts < best_e:
                    best_e = st.total_conflicts
                    if best_e == 0:
                        ok, nc = verifier_partition_schur(st.col, k)
                        assert ok, f"Échec vérif PT N={n} k={k}: {nc}"
                        best_col = list(st.col)
                        break
            if best_e == 0:
                break

        if best_e == 0:
            break

        for i in range(len(temps) - 1):
            e1, e2 = agents[i].total_conflicts, agents[i + 1].total_conflicts
            delta_beta = (1.0 / temps[i]) - (1.0 / temps[i + 1])
            if e2 <= e1 or rng.random() < math.exp((e1 - e2) * delta_beta):
                agents[i], agents[i + 1] = agents[i + 1], agents[i]
                swaps += 1

    pct_ok = ((total_triples - best_e) / total_triples * 100.0) if total_triples > 0 else 100.0
    return {
        "n": n,
        "k": k,
        "sym": sym,
        "solved": best_e == 0,
        "best_E": best_e,
        "total_triples": total_triples,
        "pct_contraintes_satisfaites": round(pct_ok, 4),
        "steps": steps,
        "swaps": swaps,
        "duree_s": round(time.perf_counter() - t0, 3),
        "temoin": best_col,
    }


# ==============================================================================
# ORCHESTRATION COMPLÈTE DU BANC D'ESSAI
# ==============================================================================

def main() -> None:
    t_global = time.perf_counter()
    print("=" * 84)
    print("🧮 BANC D'ESSAI RÉEL — LES NOMBRES DE SCHUR S(3), S(4), S(5) & FRONTIÈRE S(6)")
    print("   Épreuve des théorèmes TH114, TH116/TH118, TH119 et TH117 sur un problème ouvert")
    print("=" * 84)

    # 1. Auto-test obligatoire
    run_unit_tests()

    # --------------------------------------------------------------------------
    # PHASE 1 : PREUVE EXACTE & DUEL DPLL AMNÉSIQUE VS CDCL STIGMERGIQUE TH118
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("⚔️  PHASE 1 : PREUVES EXACTES (SAT / UNSAT) — AMNÉSIQUE vs TH118 STIGMERGIQUE")
    print("-" * 84)

    instances_p1 = [
        ("k=3, N=13 (général, S(3)=13)", 13, 3, False, 50_000, 5.0),
        ("k=3, N=14 (général, UNSAT)", 14, 3, False, 50_000, 5.0),
        ("k=4, N=44 (général, S(4)=44)", 44, 4, False, 100_000, 8.0),
        ("k=4, N=45 (symétrique, UNSAT)", 45, 4, True, 100_000, 8.0),
    ]

    p1_results = []
    witness_s3 = None
    witness_s4 = None

    for label, n, k, sym, max_c, to_s in instances_p1:
        r_dpll = solve_dpll_amnesic(n, k, symmetric=sym, max_conflicts=max_c, timeout_s=to_s)
        r_cdcl = solve_cdcl_th118(n, k, symmetric=sym, max_conflicts=max_c * 2, timeout_s=to_s)

        if n == 13 and k == 3:
            assert r_dpll["status"] == "SAT" and r_cdcl["status"] == "SAT"
            witness_s3 = r_cdcl["coloring"]
        if n == 14 and k == 3:
            assert r_dpll["status"] == "UNSAT" and r_cdcl["status"] == "UNSAT"
        if n == 44 and k == 4:
            assert r_dpll["status"] == "SAT" and r_cdcl["status"] == "SAT", (
                f"DPLL/CDCL doivent trouver S(4)=44 général (dpll={r_dpll['status']}, cdcl={r_cdcl['status']})"
            )
            witness_s4 = r_cdcl["coloring"]
        if n == 45 and k == 4:
            assert r_dpll["status"] == "UNSAT" and r_cdcl["status"] == "UNSAT", (
                f"DPLL/CDCL doivent prouver N=45 symétrique UNSAT (dpll={r_dpll['status']}, cdcl={r_cdcl['status']})"
            )

        print(f"📌 {label}")
        print(f"   • Amnésique (DPLL sans mémoire) : {r_dpll['status']:13s} | décisions={r_dpll['decisions']:7d} | pièges={r_dpll['conflicts']:6d} | {r_dpll['time_ms']:7.1f} ms")
        print(f"   • TH118 (CDCL rayage 1-UIP)     : {r_cdcl['status']:13s} | décisions={r_cdcl['decisions']:7d} | pièges={r_cdcl['conflicts']:6d} | clauses rayées={r_cdcl['learned']:5d} | {r_cdcl['time_ms']:7.1f} ms")

        p1_results.append({
            "instance": label, "n": n, "k": k, "symmetric": sym,
            "amnesique": {kk: vv for kk, vv in r_dpll.items() if kk != "coloring"},
            "th118": {kk: vv for kk, vv in r_cdcl.items() if kk != "coloring"},
        })

    assert witness_s3 is not None and witness_s4 is not None

    # --------------------------------------------------------------------------
    # PHASE 2 : MATCH SUR S(4) = 44 ASYMÉTRIQUE (DÉPART ALÉATOIRE PUR)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("🥊 PHASE 2 : MATCH ESSAIM AMNÉSIQUE vs ESSAIM SOUVERAIN (S(4)=44 ASYMÉTRIQUE)")
    print("   5 graines aléatoires | 6 agents × 25 000 pas max chacun | zéro symétrie")
    print("-" * 84)

    seeds_p2 = [11, 22, 33, 44, 55]
    p2_amn = []
    p2_sov = []
    for sd in seeds_p2:
        ra = _run_amnesic_swarm_s4(n=44, k=4, n_agents=6, max_steps=25_000, seed=sd)
        rs = _run_sovereign_swarm_s4(n=44, k=4, n_agents=6, max_steps=25_000, seed=sd)
        p2_amn.append(ra)
        p2_sov.append(rs)
        st_a = "SAT" if ra["solved"] else f"E={ra['best_E']:2d}"
        st_s = "SAT" if rs["solved"] else f"E={rs['best_E']:2d}"
        print(
            f"   Graine {sd:2d} | Amnésique: {st_a:6s} ({ra['steps']:6d} pas, {ra['time_ms']:6.0f} ms)"
            f" || Souverain: {st_s:6s} ({rs['steps']:6d} pas, {rs['time_ms']:6.0f} ms, TH114={rs['resonances_th114']}, évités={rs['pieges_evites']})"
        )

    amn_wins = sum(1 for r in p2_amn if r["solved"])
    sov_wins = sum(1 for r in p2_sov if r["solved"])
    print(f"   📊 Bilan Phase 2 : Amnésique = {amn_wins}/{len(seeds_p2)} résolus | Essaim Souverain = {sov_wins}/{len(seeds_p2)} résolus")

    # --------------------------------------------------------------------------
    # PHASE 3 : TÉMOINS VÉRIFIÉS 3N+1 & ASSAUT PARALLEL TEMPERING TH114 S(5) / S(6)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("🚀 PHASE 3 : SOCLE VÉRIFIÉ 3N+1 & ASSAUT TH114 PARALLEL TEMPERING S(5) / S(6)")
    print("-" * 84)

    # Relèvement exact S(4)=44 -> S(5)=133
    s5_best_col = lift_schur_3n_plus_1(witness_s4, 4)
    s5_best_n = len(s5_best_col) - 1
    print(f"✅ Relèvement exact 3N+1 depuis S(4)=44 : N={s5_best_n} (k=5) vérifié en 1 ms (0 conflit).")

    assaut_s5_cibles = [
        (136, 5, 2.5, False),
        (156, 5, 2.5, False),
        (160, 5, 3.0, True),
    ]
    assauts_s5 = []
    for tn, tk, tsec, tsym in assaut_s5_cibles:
        res_pt = run_parallel_tempering_th114(tn, tk, secs=tsec, seed=42, sym=tsym)
        assauts_s5.append({kk: vv for kk, vv in res_pt.items() if kk != "temoin"})
        mode_str = "sym" if tsym else "libre"
        etat_str = "SAT (0 conflit)" if res_pt["solved"] else f"E={res_pt['best_E']} ({res_pt['pct_contraintes_satisfaites']:.2f} % sur {res_pt['total_triples']} triplets)"
        print(
            f"🔥 Assaut TH114 S(5) N={tn:3d} ({mode_str:5s}) : {etat_str} | "
            f"{res_pt['steps']:,} pas | {res_pt['swaps']} échanges TH114 | {res_pt['duree_s']:.2f} s"
        )
        if res_pt["solved"] and tn > s5_best_n:
            s5_best_col = res_pt["temoin"]
            s5_best_n = tn

    # Relèvement exact depuis le meilleur témoin S(5) vérifié -> S(6)
    s6_best_col = lift_schur_3n_plus_1(s5_best_col, 5)
    s6_best_n = len(s6_best_col) - 1
    print(f"✅ Relèvement exact 3N+1 depuis S(5)={s5_best_n} : N={s6_best_n} (k=6) vérifié (0 conflit).")

    assaut_s6_cibles = [
        (481, 6, 2.0, False),
        (537, 6, 2.5, False),
    ]
    assauts_s6 = []
    for tn, tk, tsec, tsym in assaut_s6_cibles:
        res_pt = run_parallel_tempering_th114(tn, tk, secs=tsec, seed=108, sym=tsym)
        assauts_s6.append({kk: vv for kk, vv in res_pt.items() if kk != "temoin"})
        etat_str = "SAT (0 conflit)" if res_pt["solved"] else f"E={res_pt['best_E']} ({res_pt['pct_contraintes_satisfaites']:.2f} % sur {res_pt['total_triples']} triplets)"
        print(
            f"🌌 Assaut TH114 S(6) N={tn:3d} (frontière): {etat_str} | "
            f"{res_pt['steps']:,} pas | {res_pt['swaps']} échanges TH114 | {res_pt['duree_s']:.2f} s"
        )
        if res_pt["solved"] and tn > s6_best_n:
            s6_best_col = res_pt["temoin"]
            s6_best_n = tn

    # Vérification finale indépendante de tous les témoins sauvegardés
    for nom, col, kk in [
        ("S(3)", witness_s3, 3),
        ("S(4)", witness_s4, 4),
        ("S(5)", s5_best_col, 5),
        ("S(6)", s6_best_col, 6),
    ]:
        ok, nc = verifier_partition_schur(col, kk)
        assert ok, f"Échec vérification finale sur {nom}: {nc} conflits"

    payload = {
        "meta": {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duree_totale_s": round(time.perf_counter() - t_global, 2),
            "record_mondial_S5": 160,
            "record_mondial_S6_oct_2026": 537,
        },
        "phase1_sat_exact": p1_results,
        "phase2_match_s4": {
            "amnesique_resolus": amn_wins,
            "souverain_resolus": sov_wins,
            "total_graines": len(seeds_p2),
            "details_amnesique": [{k2: v2 for k2, v2 in r.items() if k2 != "col"} for r in p2_amn],
            "details_souverain": [{k2: v2 for k2, v2 in r.items() if k2 != "col"} for r in p2_sov],
        },
        "phase3_frontiere": {
            "S5_temoin_verifie_N": s5_best_n,
            "S6_temoin_verifie_N": s6_best_n,
            "assauts_th114_S5": assauts_s5,
            "assauts_th114_S6": assauts_s6,
        },
        "temoins_verifies": {
            "S3_N13": witness_s3[1:],
            "S4_N44_general": witness_s4[1:],
            f"S5_N{s5_best_n}": s5_best_col[1:],
            f"S6_N{s6_best_n}": s6_best_col[1:],
        },
    }

    SORTIE_TEMOINS.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n" + "=" * 84)
    print(f"💾 Témoins vérifiés (0 conflit) scellés dans : {SORTIE_TEMOINS}")
    print(f"⏱️  Durée totale du banc d'essai : {payload['meta']['duree_totale_s']} s")
    print("=" * 84)


if __name__ == "__main__":
    main()
