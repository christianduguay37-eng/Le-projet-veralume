# -*- coding: utf-8 -*-
"""
Pionnier Schur-A ("Architecte Algébrique & SAT")
Objectif : Trouver une coloration sans conflit (E = 0 vérifié) pour S(5) = 160.
Utilise python-sat (CaDiCaL153 / autres solveurs CDCL) avec bris de symétrie fort,
symétrie palindromique / quasi-palindromique, et gabarits structurels.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

ETAGE5_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\_Unification_Alix\src\alix\etage5")
if str(ETAGE5_DIR) not in sys.path:
    sys.path.insert(0, str(ETAGE5_DIR))

from essaim_schur_s6 import verifier_partition_schur
from pysat.solvers import Cadical153, Solver

TEMOIN_OUT = ETAGE5_DIR / "temoin_S5_pionnier.json"


def build_schur_cnf(
    n: int,
    k: int = 5,
    mode: str = "sym",
    use_amo: bool = True,
    sym_break: bool = True,
    fixed_colors: Optional[Dict[int, int]] = None,
    forbidden_colors: Optional[Dict[int, Sequence[int]]] = None,
) -> Tuple[List[List[int]], Callable[[List[int]], List[int]], int]:
    """
    Construit le CNF pour S(k) à taille N.
    mode:
      - "sym": col[x] = col[N+1-x] (variables sur 1..ceil(N/2))
      - "quasisym": col[x] = col[N-x] sur 1..N-1, et N libre
      - "free": 1..N indépendants
    Retourne (clauses, decode_fn, num_vars).
    """
    if mode == "sym":
        def rep(x: int) -> int:
            return min(x, n + 1 - x)
        m = (n + 1) // 2
    elif mode == "quasisym":
        def rep(x: int) -> int:
            if x == n:
                return (n // 2) + 1
            return min(x, n - x)
        m = (n // 2) + 1
    elif mode == "free":
        def rep(x: int) -> int:
            return x
        m = n
    else:
        raise ValueError(f"Mode inconnu: {mode}")

    def vid(r: int, c: int) -> int:
        # r in 1..m, c in 0..k-1
        return (r - 1) * k + c + 1

    clauses: List[List[int]] = []

    # 1. At-least-one (ALO) et At-most-one (AMO)
    for r in range(1, m + 1):
        clauses.append([vid(r, c) for c in range(k)])
        if use_amo:
            for c1 in range(k):
                for c2 in range(c1 + 1, k):
                    clauses.append([-vid(r, c1), -vid(r, c2)])

    # 2. Contraintes sum-free : a + b = c, 1 <= a <= b, c <= n
    seen_triplets = set()
    for a in range(1, n // 2 + 1):
        ra = rep(a)
        for b in range(a, n - a + 1):
            c_val = a + b
            rb = rep(b)
            rc = rep(c_val)
            # Déduplication des représentants dans le triplet
            reps = tuple(sorted({ra, rb, rc}))
            if reps in seen_triplets:
                continue
            seen_triplets.add(reps)
            if len(reps) == 1:
                # Impossible pour toute couleur -> UNSAT immédiat
                r0 = reps[0]
                for col_idx in range(k):
                    clauses.append([-vid(r0, col_idx)])
            elif len(reps) == 2:
                r0, r1 = reps
                for col_idx in range(k):
                    clauses.append([-vid(r0, col_idx), -vid(r1, col_idx)])
            else:
                r0, r1, r2 = reps
                for col_idx in range(k):
                    clauses.append([-vid(r0, col_idx), -vid(r1, col_idx), -vid(r2, col_idx)])

    # 3. Bris de symétrie fort (ordre canonique d'apparition des couleurs)
    next_var = m * k + 1
    if sym_break and n >= 2:
        # col[1] = 0
        clauses.append([vid(rep(1), 0)])
        # col[2] = 1 (car 1+1=2 interdit col[2]=0)
        clauses.append([vid(rep(2), 1)])
        # Ordre d'apparition pour c = 2..k-1 sur r = 1..min(m, 35)
        # Pour tout r >= 3, v(r, c) => OR_{y < r} v(y, c-1)
        # Encodage compact avec variables auxiliaires seen(r, c) pour c in 1..k-2
        # seen(r, c) <=> OR_{y=1..r} v(y, c)
        limit_r = min(m, 40)
        seen_var: Dict[Tuple[int, int], int] = {}
        for c in range(1, k - 1):
            for r in range(1, limit_r + 1):
                sv = next_var
                next_var += 1
                seen_var[(r, c)] = sv
                if r == 1:
                    # seen(1, c) <=> v(1, c)
                    clauses.append([-sv, vid(1, c)])
                    clauses.append([-vid(1, c), sv])
                else:
                    prev = seen_var[(r - 1, c)]
                    # sv => prev OR v(r, c)
                    clauses.append([-sv, prev, vid(r, c)])
                    # prev => sv
                    clauses.append([-prev, sv])
                    # v(r, c) => sv
                    clauses.append([-vid(r, c), sv])
        for c in range(2, k):
            # Avant r = c+1, impossible d'utiliser couleur c
            for r in range(1, min(c + 1, m + 1)):
                clauses.append([-vid(r, c)])
            for r in range(c + 1, limit_r + 1):
                # v(r, c) => seen(r-1, c-1)
                clauses.append([-vid(r, c), seen_var[(r - 1, c - 1)]])

    # 4. Couleurs fixées / interdites optionnelles
    if fixed_colors:
        for x, c in fixed_colors.items():
            clauses.append([vid(rep(x), c)])
    if forbidden_colors:
        for x, cols in forbidden_colors.items():
            rx = rep(x)
            for c in cols:
                clauses.append([-vid(rx, c)])

    def decode(model: List[int]) -> List[int]:
        pos = {lit for lit in model if lit > 0}
        col = [0] * (n + 1)
        for x in range(1, n + 1):
            rx = rep(x)
            found = -1
            for c in range(k):
                if vid(rx, c) in pos:
                    found = c
                    break
            col[x] = found
        return col

    return clauses, decode, next_var - 1


def solve_with_timeout(
    clauses: List[List[int]],
    decode: Callable[[List[int]], List[int]],
    n: int,
    k: int = 5,
    timeout_s: float = 15.0,
    solver_name: str = "cadical153",
    label: str = "",
) -> Tuple[str, Optional[List[int]], float]:
    """
    Exécute le solveur SAT avec timeout strict via solver.interrupt().
    Retourne (status, col_or_None, elapsed_s) où status in {"SAT", "UNSAT", "TIMEOUT"}.
    """
    t0 = time.perf_counter()
    with Solver(name=solver_name, bootstrap_with=clauses) as solver:
        timer = threading.Timer(timeout_s, solver.interrupt)
        timer.start()
        try:
            res = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        elapsed = time.perf_counter() - t0
        if res is True:
            model = solver.get_model()
            col = decode(model)
            ok, conf = verifier_partition_schur(col, k)
            print(f"[{label}] SAT en {elapsed:.3f}s | verif=({ok}, E={conf})")
            if not ok:
                raise RuntimeError(f"ALERTE: modèle SAT invalide ! E={conf}")
            return "SAT", col, elapsed
        elif res is False:
            print(f"[{label}] UNSAT prouvé en {elapsed:.3f}s")
            return "UNSAT", None, elapsed
        else:
            print(f"[{label}] TIMEOUT après {elapsed:.3f}s")
            return "TIMEOUT", None, elapsed


def save_witness(n: int, k: int, col: List[int], source: str) -> None:
    payload = {
        "N": n,
        "k": k,
        "coloration": col,
        "source": source,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    TEMOIN_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f">>> TÉMOIN SAUVEGARDÉ dans {TEMOIN_OUT} (N={n}, k={k}, E=0)")


def run_salve_1() -> Optional[Tuple[int, List[int]]]:
    print("=== SALVE 1 : CaDiCaL153 symétrique & quasi-symétrique avec bris de symétrie fort ===")
    best_n = 0
    best_col: Optional[List[int]] = None

    # 1. Test direct N=160 symétrique (80 variables !) - 15s
    clauses, decode, nvars = build_schur_cnf(160, 5, mode="sym", use_amo=True, sym_break=True)
    print(f"N=160 sym (AMO+SB): {nvars} vars, {len(clauses)} clauses")
    status, col, _ = solve_with_timeout(clauses, decode, 160, 5, timeout_s=15.0, label="160_sym_AMO_SB")
    if status == "SAT" and col is not None:
        save_witness(160, 5, col, "cadical153_160_sym_AMO_SB")
        return 160, col

    # 2. Test direct N=160 symétrique sans AMO (clauses plus légères) - 10s
    clauses, decode, nvars = build_schur_cnf(160, 5, mode="sym", use_amo=False, sym_break=True)
    print(f"N=160 sym (noAMO+SB): {nvars} vars, {len(clauses)} clauses")
    status, col, _ = solve_with_timeout(clauses, decode, 160, 5, timeout_s=10.0, label="160_sym_noAMO_SB")
    if status == "SAT" and col is not None:
        save_witness(160, 5, col, "cadical153_160_sym_noAMO_SB")
        return 160, col

    # 3. Test paliers en mode symétrique pour mesurer la transition de phase
    for n_test in [140, 148, 154, 157, 159]:
        if (n_test + 1) % 3 == 0:
            # Palindrome strict impossible quand N+1 = 3m (piège #1)
            continue
        clauses, decode, nvars = build_schur_cnf(n_test, 5, mode="sym", use_amo=True, sym_break=True)
        status, col, _ = solve_with_timeout(clauses, decode, n_test, 5, timeout_s=8.0, label=f"{n_test}_sym_SB")
        if status == "SAT" and col is not None:
            if n_test > best_n:
                best_n = n_test
                best_col = col
                save_witness(n_test, 5, col, f"cadical153_{n_test}_sym_SB")

    if best_col is not None:
        return best_n, best_col
    return None


if __name__ == "__main__":
    run_salve_1()
