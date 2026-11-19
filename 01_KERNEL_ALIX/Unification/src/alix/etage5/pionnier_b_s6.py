# -*- coding: utf-8 -*-
"""
Pionnier Schur-B — Explorateur Frontière S(6)
Stratégies combinatoires + SAT CDCL natif (Cadical153) pour repousser S(6) > 400 -> 481 -> 537+.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from pysat.solvers import Cadical153

ETAGE5_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\_Unification_Alix\src\alix\etage5")
if str(ETAGE5_DIR) not in sys.path:
    sys.path.insert(0, str(ETAGE5_DIR))

from essaim_schur_s6 import lift_schur_3n_plus_1, verifier_partition_schur

OUT_S6 = ETAGE5_DIR / "temoin_S6_pionnier.json"
OUT_S5_A = ETAGE5_DIR / "temoin_S5_pionnier.json"
TEMOINS_BASE = ETAGE5_DIR / "temoins_schur_th118.json"


def build_schur_sat(
    n: int,
    k: int,
    sym_mode: str = "N+1",
    full_sym_break: bool = True,
    fixed: Optional[Dict[int, int]] = None,
    forbidden: Optional[Dict[int, Set[int]]] = None,
    allowed_colors: Optional[Dict[int, Set[int]]] = None,
) -> Tuple[int, List[List[int]], Dict[int, int]]:
    """
    Construit le CNF pour Schur(k, N).
    sym_mode:
      - "none": pas de symétrie
      - "N+1": C(x) = C(N+1-x) pour x=1..N  (requiert (N+1) % 3 != 0)
      - "N":   C(x) = C(N-x) pour x=1..N-1, et N libre (requiert N % 3 != 0)
    full_sym_break:
      - Bris de symétrie lexicographique exact par première occurrence (élimine les k! permutations).
    """
    pos_of: Dict[int, int] = {}
    if sym_mode == "N+1":
        num_pos = (n + 1) // 2
        for x in range(1, n + 1):
            pos_of[x] = min(x, n + 1 - x)
    elif sym_mode == "N":
        half = n // 2
        for x in range(1, n):
            pos_of[x] = min(x, n - x)
        pos_of[n] = half + 1
        num_pos = half + 1
    else:
        num_pos = n
        for x in range(1, n + 1):
            pos_of[x] = x

    def var(p: int, c: int) -> int:
        return (p - 1) * k + c + 1

    clauses: List[List[int]] = []

    # 1. Exactement une couleur par position
    for p in range(1, num_pos + 1):
        clauses.append([var(p, c) for c in range(k)])
        for c1 in range(k):
            v1 = var(p, c1)
            for c2 in range(c1 + 1, k):
                clauses.append([-v1, -var(p, c2)])

    # 2. Clauses sans somme (dédupliquées)
    seen: Set[Tuple[int, ...]] = set()
    for a in range(1, n + 1):
        pa = pos_of[a]
        max_b = n - a
        if max_b < a:
            break
        for b in range(a, max_b + 1):
            pb = pos_of[b]
            pc = pos_of[a + b]
            if pa == pb == pc:
                for c in range(k):
                    tup = (-var(pa, c),)
                    if tup not in seen:
                        seen.add(tup)
                        clauses.append([tup[0]])
            else:
                if pa == pb:
                    ps = (pa, pc) if pa < pc else (pc, pa)
                elif pa == pc:
                    ps = (pa, pb) if pa < pb else (pb, pa)
                elif pb == pc:
                    ps = (pa, pb) if pa < pb else (pb, pa)
                else:
                    # 3 distincts
                    if pa > pb:
                        pa_, pb_ = pb, pa
                    else:
                        pa_, pb_ = pa, pb
                    if pc < pa_:
                        ps = (pc, pa_, pb_)
                    elif pc < pb_:
                        ps = (pa_, pc, pb_)
                    else:
                        ps = (pa_, pb_, pc)
                for c in range(k):
                    cl = tuple(-var(p, c) for p in ps)
                    if cl not in seen:
                        seen.add(cl)
                        clauses.append(list(cl))

    next_var = num_pos * k + 1

    # 3. Bris de symétrie lexicographique exact (si aucun fixed ne l'invalide)
    if full_sym_break and not fixed:
        # col[1] = 0, col[2] = 1
        clauses.append([var(pos_of[1], 0)])
        if n >= 3 and k >= 2 and pos_of[2] != pos_of[1]:
            clauses.append([var(pos_of[2], 1)])
        # Auxiliary variables used[p][c] for p=1..num_pos, c=0..k-1
        # Only need c in 1..k-2 since c=0 is already used at p=1, and c=k-1 doesn't guard c+1
        used_id: Dict[Tuple[int, int], int] = {}
        for p in range(1, num_pos + 1):
            for c in range(1, k - 1):
                used_id[(p, c)] = next_var
                next_var += 1
        # Base p=1: used(1, c) = False for c >= 1 (since col[1] = 0)
        for c in range(1, k - 1):
            clauses.append([-used_id[(1, c)]])
        # Inductive step
        for p in range(2, num_pos + 1):
            for c in range(1, k - 1):
                u_cur = used_id[(p, c)]
                u_prev = used_id[(p - 1, c)]
                x_pc = var(p, c)
                # u_cur <-> u_prev OR x_pc
                clauses.append([-u_prev, u_cur])
                clauses.append([-x_pc, u_cur])
                clauses.append([-u_cur, u_prev, x_pc])
            # Ordering: if position p takes color c (c >= 2), then color c-1 must be used before p
            for c in range(2, k):
                clauses.append([-var(p, c), used_id[(p - 1, c - 1)]])
    elif not fixed:
        clauses.append([var(pos_of[1], 0)])
        if n >= 3 and k >= 2 and pos_of[2] != pos_of[1]:
            clauses.append([var(pos_of[2], 1)])

    # 4. Contraintes additionnelles (fixed / forbidden / allowed_colors)
    if fixed:
        for x, c in fixed.items():
            if 1 <= x <= n:
                clauses.append([var(pos_of[x], c)])
    if forbidden:
        for x, bad_cs in forbidden.items():
            if 1 <= x <= n:
                for c in bad_cs:
                    clauses.append([-var(pos_of[x], c)])
    if allowed_colors:
        for x, good_cs in allowed_colors.items():
            if 1 <= x <= n:
                for c in range(k):
                    if c not in good_cs:
                        clauses.append([-var(pos_of[x], c)])

    return next_var - 1, clauses, pos_of


def solve_cadical(
    n: int,
    k: int,
    sym_mode: str = "N+1",
    full_sym_break: bool = True,
    fixed: Optional[Dict[int, int]] = None,
    forbidden: Optional[Dict[int, Set[int]]] = None,
    allowed_colors: Optional[Dict[int, Set[int]]] = None,
    phases: Optional[List[int]] = None,
    timeout_s: float = 10.0,
) -> Tuple[str, Optional[List[int]], float]:
    t0 = time.perf_counter()
    _, clauses, pos_of = build_schur_sat(
        n, k,
        sym_mode=sym_mode,
        full_sym_break=full_sym_break,
        fixed=fixed,
        forbidden=forbidden,
        allowed_colors=allowed_colors,
    )
    with Cadical153(bootstrap_with=clauses) as solver:
        if phases:
            solver.set_phases(phases)
        timer = threading.Timer(timeout_s, solver.interrupt)
        timer.start()
        try:
            res = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        dt = time.perf_counter() - t0
        if res is True:
            model = set(solver.get_model())
            col = [0] * (n + 1)
            for x in range(1, n + 1):
                p = pos_of[x]
                for c in range(k):
                    v = (p - 1) * k + c + 1
                    if v in model:
                        col[x] = c
                        break
            ok, n_conf = verifier_partition_schur(col, k)
            assert ok, f"ERREUR INTERNE: modèle SAT invalide ({n_conf} conflits)!"
            return "SAT", col, dt
        elif res is False:
            return "UNSAT", None, dt
        else:
            return "TIMEOUT", None, dt


def save_best_s6(col: List[int], method: str) -> None:
    n = len(col) - 1
    ok, conf = verifier_partition_schur(col, 6)
    assert ok and conf == 0, f"Refus de sauvegarde: conflits={conf}"
    if OUT_S6.exists():
        try:
            old = json.loads(OUT_S6.read_text(encoding="utf-8"))
            if old.get("N", 0) >= n:
                return
        except Exception:
            pass
    payload = {
        "N": n,
        "k": 6,
        "methode": method,
        "verifie_E0": True,
        "coloration": col,
    }
    OUT_S6.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  [SAUVEGARDÉ] {OUT_S6.name} -> S(6) >= {n} (E=0 vérifié, méthode={method})", flush=True)


def analyze_color(col: List[int], c: int) -> List[int]:
    return [x for x in range(1, len(col)) if col[x] == c]


def main() -> None:
    print("=== PIONNIER SCHUR-B : STAGE 1 (S(5) -> S(6) + Symétrie Cadical153) ===", flush=True)

    # 1. Vérifier si Pionnier A a déjà posé temoin_S5_pionnier.json
    best_s5: Optional[List[int]] = None
    if OUT_S5_A.exists():
        data = json.loads(OUT_S5_A.read_text(encoding="utf-8"))
        c5 = data.get("coloration")
        if c5:
            ok, conf = verifier_partition_schur(c5, 5)
            if ok:
                best_s5 = c5
                print(f"[INFO] Témoin S(5) chargé depuis Pionnier A : N={len(c5)-1}", flush=True)

    # 2. Tester Cadical153 sur S(5) symétrique avec bris de symétrie lexicographique complet
    if best_s5 is None or (len(best_s5) - 1) < 160:
        for n5, smode, tlim in [(150, "N+1", 3.0), (156, "N+1", 4.0), (160, "N+1", 8.0)]:
            st, col5, dt = solve_cadical(n5, 5, sym_mode=smode, full_sym_break=True, timeout_s=tlim)
            print(f"[S(5) sym={smode} N={n5}] {st} en {dt:.3f}s", flush=True)
            if st == "SAT" and col5 is not None:
                best_s5 = col5
                # Immediately lift to S(6)!
                col6_lift = lift_schur_3n_plus_1(col5, 5)
                print(f"  -> Lift 3*N+1 immédiat : S(6) >= {len(col6_lift)-1} (E=0 vérifié!)", flush=True)
                save_best_s6(col6_lift, f"lift_3N+1_depuis_S5_{n5}")

    if best_s5 is not None:
        n5 = len(best_s5) - 1
        print(f"\n[ANATOMIE S(5) N={n5}] Tailles par couleur:", flush=True)
        for c in range(5):
            els = analyze_color(best_s5, c)
            small = [x for x in els if x <= n5 // 3]
            print(f"  Couleur {c}: {len(els)} éléments | <= N/3: {len(small)} ({small[:15]})", flush=True)


if __name__ == "__main__":
    main()
