#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alix_stratified_oracle_hades.py (stratified_oracle.py) - générateur de cas stratifié pour l'oracle CEGIS.
Sparring & Architecture : Hadès (Claude) × Christian Duguay & Alix (Panthéon K-SIL)

Ordre d'évaluation : coins déterministes (couverture pairwise entre arguments) PUIS aléatoire
secrets.randbits. Les bugs de bord (n=1, liste vide, H=W=1, x == 1, négatifs) ont une probabilité
~2^-64 sous randbits(64) pur ; ici ils sont testés d'office.

Les « frontières » sont décrites par un `Frontier(name, corners, rand)`.
`observe()` compare aussi les arguments APRÈS appel : c'est ce qui détecte les réparations d'aliasing
(entrée mutée vs entrée intacte), invisible si on ne compare que la valeur de retour.
"""
from __future__ import annotations

import copy
import itertools
import math
import secrets
import sys
from dataclasses import dataclass
from typing import Any, Callable, Sequence

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ------------------------------------------------------------------ domaines de coins

_INT_PRIORITY = (0, 1, -1, 2, -2, 10, 63, 64, 2**31 - 1, 2**63 - 1, 255, 256, 257, -2**31, -2**63)


def ints(limit: int = 11) -> list[int]:
    return list(_INT_PRIORITY[:limit])


def sizes(limit: int = 6) -> list[int]:
    return [0, 1, 2, 3, 5, 8][:limit]


def floats(limit: int = 9) -> list[float]:
    return [0.0, -0.0, 1.0, -1.0, 0.5, 1e-9, 1e9, math.inf, -math.inf][:limit]


def strs(limit: int = 7) -> list[str]:
    return ["", "a", "aa", "ab", " ", "A1", "é"][:limit]


def lists_of(elems: Sequence, limit: int = 12) -> list[list]:
    e = list(elems)
    base = [[]]
    base += [[x] for x in e[:3]]
    if e:
        base.append([e[0], e[0]])                          # doublons
    distinct = [x for i, x in enumerate(e) if x not in e[:i]][:3]
    if len(distinct) >= 2:
        base.append(sorted(distinct))                      # croissante
        base.append(sorted(distinct, reverse=True))        # décroissante
    if len(distinct) >= 3:
        base.append([distinct[1], distinct[0], distinct[2]])
    return base[:limit]


def grids(elems: Sequence | None = None, limit: int = 24) -> list[list[list]]:
    """Grilles H x W incluant 1x1, bandes, non-carrées ; remplissages 0 / 1 / distinct / damier."""
    shapes = [(1, 1), (1, 2), (2, 1), (2, 2), (1, 4), (4, 1), (3, 3), (2, 5)]
    fills: list[Callable[[int, int, int, int], Any]] = [
        lambda r, c, h, w: 0,
        lambda r, c, h, w: 1,
        lambda r, c, h, w: r * w + c + 1,
        lambda r, c, h, w: (r + c) % 2,
    ]
    out = [[[f(r, c, h, w) for c in range(w)] for r in range(h)] for (h, w) in shapes for f in fills]
    return out[:limit]


# ------------------------------------------------------------------ générateurs aléatoires

def rand_int(bits: int = 64) -> int:
    v = secrets.randbits(bits)
    return -v if secrets.randbits(1) else v


def rand_small(span: int = 20) -> int:
    return secrets.randbelow(2 * span + 1) - span


def rand_list(elem: Callable[[], Any] = rand_small, max_len: int = 8) -> list:
    return [elem() for _ in range(secrets.randbelow(max_len + 1))]


def rand_grid(elem: Callable[[], Any] = rand_small, max_dim: int = 6) -> list[list]:
    h, w = 1 + secrets.randbelow(max_dim), 1 + secrets.randbelow(max_dim)
    return [[elem() for _ in range(w)] for _ in range(h)]


@dataclass
class Frontier:
    name: str
    corners: list
    rand: Callable[[], Any]


# ------------------------------------------------------------------ pairwise (all-pairs) glouton

def pairwise(domains: Sequence[Sequence]) -> list[tuple]:
    n = len(domains)
    if n == 0:
        return [()]
    if n == 1:
        return [(v,) for v in domains[0]]
    uncovered = {(i, a, j, b) for i in range(n) for j in range(i + 1, n)
                 for a in range(len(domains[i])) for b in range(len(domains[j]))}
    rows: list[tuple] = []
    while uncovered:
        i, a, j, b = min(uncovered)                        # déterministe
        row: list[int | None] = [None] * n
        row[i], row[j] = a, b
        for k in range(n):
            if row[k] is not None:
                continue

            def gain(v, k=k):
                g = 0
                for m in range(n):
                    if row[m] is None:
                        continue
                    key = (m, row[m], k, v) if m < k else (k, v, m, row[m])
                    g += key in uncovered
                return g

            row[k] = max(range(len(domains[k])), key=gain)
        for x in range(n):
            for y in range(x + 1, n):
                uncovered.discard((x, row[x], y, row[y]))
        rows.append(tuple(domains[k][row[k]] for k in range(n)))
    return rows


class StratifiedOracle:
    def __init__(self, frontiers: Sequence[Frontier], n_random: int = 25):
        self.frontiers = list(frontiers)
        self.n_random = n_random

    def corner_cases(self) -> list[tuple]:
        return pairwise([f.corners for f in self.frontiers])

    def random_cases(self) -> list[tuple]:
        return [tuple(f.rand() for f in self.frontiers) for _ in range(self.n_random)]

    def cases(self) -> list[tuple]:
        return self.corner_cases() + self.random_cases()


# ------------------------------------------------------------------ comparaison de comportements

def observe(fn: Callable, args: tuple):
    """(résultat | exception, arguments après appel). Les args sont copiés : l'oracle ne mute jamais ses cas."""
    a = copy.deepcopy(args)
    try:
        r: Any = ("ok", fn(*a))
    except RecursionError:
        r = ("exc", "RecursionError")
    except Exception as e:                                 # noqa: BLE001 - on compare des comportements
        r = ("exc", type(e).__name__)
    return r, a


def first_divergence(ref: Callable, cand: Callable, cases: Sequence[tuple]):
    """Premier cas où cand diffère de ref (valeur, type d'exception ou mutation des entrées)."""
    for c in cases:
        if observe(ref, c) != observe(cand, c):
            return c
    return None


# ------------------------------------------------------------------ démonstration

def _demo():
    ref_src = "def count_pos(a):\n    return sum(1 for x in a if x > 0)\n"
    bug_src = "def count_pos(a):\n    return sum(1 for x in a if x > 1)\n"      # rate x == 1
    ns_ref: dict = {}
    ns_bug: dict = {}
    exec(ref_src, ns_ref)
    exec(bug_src, ns_bug)
    ref, bug = ns_ref["count_pos"], ns_bug["count_pos"]

    oracle = StratifiedOracle([Frontier("a", lists_of(ints()), lambda: rand_list(rand_int))], n_random=25)
    corners, rnd = oracle.corner_cases(), oracle.random_cases()
    print(f"coins : {len(corners)} cas ; aléatoires randbits(64) : {len(rnd)} cas")
    print("aléatoire seul  ->", first_divergence(ref, bug, rnd))
    print("coins d'abord   ->", first_divergence(ref, bug, corners))
    assert first_divergence(ref, bug, corners) is not None

    # pairwise : 3 arguments, couverture de toutes les paires de coins
    rows = pairwise([ints(10), sizes(6), strs(7)])
    print(f"pairwise 10x6x7 : {len(rows)} lignes au lieu de {10 * 6 * 7}")
    assert len(rows) < 10 * 6 * 7

    # aliasing : seule la comparaison des entrées après appel voit la différence
    ref_a = "def smooth(g):\n    o = [r[:] for r in g]\n    for i in range(len(g)):\n        for j in range(1, len(g[0])):\n            o[i][j] = g[i][j] + g[i][j - 1]\n    return o\n"
    bug_a = ref_a.replace("o = [r[:] for r in g]", "o = g")
    n1: dict = {}
    n2: dict = {}
    exec(ref_a, n1)
    exec(bug_a, n2)
    g_oracle = StratifiedOracle([Frontier("g", grids(), rand_grid)], n_random=10)
    print("alias (grilles) ->", first_divergence(n1["smooth"], n2["smooth"], g_oracle.corner_cases()))
    assert first_divergence(n1["smooth"], n2["smooth"], g_oracle.corner_cases()) is not None
    print("✅ OK : StratifiedOracle + Pairwise All-Pairs + observe(args_after_call) certifiés !")


if __name__ == "__main__":
    _demo()
