# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — Chirurgie LNS-TH118 (Voisinages Bloquants + CDCL Exact + Pénalité
  Strictement Locale) sur les États Gelés S(5)=160 (E=2) et S(6)=537 (E=9)

  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Principe :
    1. Isoler les seules variables en conflit et leurs bloqueurs directs par
       couches BFS sur les portes les moins verrouillées.
    2. Lancer le scalpel exact CDCL TH118 (1-UIP) sur ce sous-problème exact :
       soit il trouve une réparation E = 0 (ou E < E_courant), soit il PROUVE
       UNSAT que le voisinage local ne suffit pas.
    3. Compléter par une descente TH114 à pénalité STRICTEMENT LOCALE (remise à
       zéro immédiate dès qu'une variable sort de conflit) pour éviter toute
       saturation de la grille.
================================================================================
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from essaim_schur_s6 import (
    SORTIE_TEMOINS,
    SchurBitmaskState,
    WatchedEngine,
    _lit_idx,
    lift_schur_3n_plus_1,
    verifier_partition_schur,
)

ETAT_PERSISTANT_PATH = CURRENT_DIR / "etat_agents_schur.json"


# ==============================================================================
# ÉTAPE 1 — EXTRACTEUR DE VOISINAGE BLOQUANT EXACT
# ==============================================================================

def _find_blockers_for_color(col: List[int], n: int, x: int, g: int) -> List[Tuple[int, int]]:
    """
    Trouve tous les couples (u, v) de couleur g formant un triplet de Schur avec x
    si x recevait la couleur g.
    """
    blockers: List[Tuple[int, int]] = []
    # 1. x = u + v (1 <= u <= x // 2)
    for u in range(1, x // 2 + 1):
        v = x - u
        if v >= 1 and col[u] == g and col[v] == g:
            blockers.append((u, v))
    # 2. v = x + u (1 <= u <= n - x)
    for u in range(1, n - x + 1):
        v = x + u
        if u == x:
            if col[v] == g:
                blockers.append((v, v))
        elif col[u] == g and col[v] == g:
            blockers.append((u, v))
    return blockers


def extract_blocking_neighborhood(
    col: List[int],
    k: int,
    seed_vars: List[int],
    max_vars: int,
    symmetric: bool = False,
) -> Tuple[List[int], Dict[int, List[Tuple[int, int]]]]:
    """
    Construit en BFS par couches le voisinage bloquant autour de seed_vars en
    priorisant les couleurs alternatives les moins verrouillées.
    Retourne (unlocked_sorted, blocker_summary_by_seed).
    """
    n = len(col) - 1
    unlocked: Set[int] = set()
    blocker_summary: Dict[int, List[Tuple[int, int]]] = {}

    def add_var(v: int) -> bool:
        if v < 1 or v > n:
            return False
        changed = False
        if v not in unlocked:
            unlocked.add(v)
            changed = True
        if symmetric:
            y = n + 1 - v
            if y not in unlocked:
                unlocked.add(y)
                changed = True
        return changed

    for x in seed_vars:
        add_var(x)

    frontier: List[int] = list(seed_vars)
    visited_expand: Set[int] = set()

    # Couche 1, puis Couche 2+ jusqu'à max_vars
    while frontier and len(unlocked) < max_vars:
        next_frontier: List[int] = []
        for x in frontier:
            if x in visited_expand:
                continue
            visited_expand.add(x)

            # Analyser toutes les couleurs alternatives g != col[x]
            alt_info: List[Tuple[int, int, List[Tuple[int, int]]]] = []
            for g in range(k):
                if g == col[x]:
                    continue
                bl = _find_blockers_for_color(col, n, x, g)
                alt_info.append((len(bl), g, bl))
            alt_info.sort(key=lambda t: t[0])

            if x in seed_vars and x not in blocker_summary:
                blocker_summary[x] = [(g, cnt) for cnt, g, _ in alt_info]

            # Prendre les 2 couleurs alternatives les moins verrouillées
            for _, _, bl in alt_info[:2]:
                for u, v in bl:
                    if len(unlocked) >= max_vars:
                        break
                    if add_var(u):
                        next_frontier.append(u)
                    if len(unlocked) < max_vars and add_var(v):
                        next_frontier.append(v)
                if len(unlocked) >= max_vars:
                    break
            if len(unlocked) >= max_vars:
                break
        frontier = next_frontier

    # S'assurer que tout seed_var a son résumé
    for x in seed_vars:
        if x not in blocker_summary:
            alt_info_s = []
            for g in range(k):
                if g != col[x]:
                    alt_info_s.append((len(_find_blockers_for_color(col, n, x, g)), g))
            alt_info_s.sort()
            blocker_summary[x] = [(g, cnt) for cnt, g in alt_info_s]

    return sorted(unlocked), blocker_summary


# ==============================================================================
# ÉTAPE 2 — RÉPARATEUR CDCL TH118 CHIRURGICAL SUR VOISINAGE DÉVERROUILLÉ
# ==============================================================================

def cdcl_lns_repair(
    col: List[int],
    k: int,
    unlocked: List[int],
    timeout_s: float = 2.0,
    symmetric: bool = False,
    ignore_frozen_conflicts: bool = False,
) -> Dict[str, Any]:
    """
    Encode en CNF uniquement les variables de `unlocked` (les autres restent gelées)
    et résout exactement par CDCL TH118 (1-UIP + backjump + restarts).
    """
    t0 = time.perf_counter()
    n = len(col) - 1
    is_u = [False] * (n + 1)
    for v in unlocked:
        is_u[v] = True
        if symmetric:
            is_u[n + 1 - v] = True

    def rep(v: int) -> int:
        return min(v, n + 1 - v) if symmetric else v

    reps = sorted({rep(v) for v in range(1, n + 1) if is_u[v]})
    if not reps:
        _, exact_e = verifier_partition_schur(col, k)
        return {"status": "SAT", "new_col": list(col), "exact_E": exact_e, "conflicts": 0, "learned": 0, "time_ms": 0.0}

    pos_map = {r: i + 1 for i, r in enumerate(reps)}
    n_pos = len(reps)
    n_vars = n_pos * k

    def var(r: int, c: int) -> int:
        return (pos_map[r] - 1) * k + c + 1

    clauses: List[List[int]] = []
    for r in reps:
        clauses.append([var(r, c) for c in range(k)])
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                clauses.append([-var(r, c1), -var(r, c2)])

    seen_clauses: Set[Tuple[int, ...]] = set()
    frozen_conflicts = 0

    for a in range(1, n // 2 + 1):
        ua = is_u[a]
        ca = col[a]
        max_b = n - a
        for b in range(a, max_b + 1):
            c_sum = a + b
            ub = is_u[b]
            uc = is_u[c_sum]
            if not (ua or ub or uc):
                if ca == col[b] == col[c_sum]:
                    frozen_conflicts += 1
                    if not ignore_frozen_conflicts:
                        return {
                            "status": "FROZEN_CONFLICT",
                            "new_col": None,
                            "exact_E": None,
                            "conflicts": 0,
                            "learned": 0,
                            "time_ms": (time.perf_counter() - t0) * 1000,
                        }
                continue

            frozen_cols: Set[int] = set()
            free_reps: Set[int] = set()
            if ua:
                free_reps.add(rep(a))
            else:
                frozen_cols.add(ca)
            if ub:
                free_reps.add(rep(b))
            else:
                frozen_cols.add(col[b])
            if uc:
                free_reps.add(rep(c_sum))
            else:
                frozen_cols.add(col[c_sum])

            if len(frozen_cols) >= 2:
                continue

            colors_to_ban = list(frozen_cols) if frozen_cols else list(range(k))
            sorted_reps = sorted(free_reps)
            for g in colors_to_ban:
                tup = tuple(-var(r, g) for r in sorted_reps)
                if tup not in seen_clauses:
                    seen_clauses.add(tup)
                    clauses.append(list(tup))

    eng = WatchedEngine(n_vars, clauses)
    if eng.root_unsat:
        return {
            "status": "UNSAT",
            "new_col": None,
            "exact_E": None,
            "conflicts": 0,
            "learned": 0,
            "time_ms": (time.perf_counter() - t0) * 1000,
        }

    # Initialiser saved_phase sur le coloriage actuel des variables déverrouillées
    saved_phase = [-1] * (n_vars + 1)
    for r in reps:
        cur_c = col[r]
        for c in range(k):
            saved_phase[var(r, c)] = 1 if c == cur_c else -1

    activity = [0.0] * (n_vars + 1)
    var_inc = 1.0
    var_decay = 0.95
    seen = [False] * (n_vars + 1)
    decisions = 0
    conflicts = 0
    learned_count = 0
    restart_limit = 100
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
            for q in c[1 if p != 0 else 0:]:
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
                    "status": "UNSAT",
                    "new_col": None,
                    "exact_E": None,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                }
            if (conflicts & 127 == 0) and (time.perf_counter() - t0) > timeout_s:
                return {
                    "status": "TIMEOUT",
                    "new_col": None,
                    "exact_E": None,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
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
                    "status": "UNSAT",
                    "new_col": None,
                    "exact_E": None,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                }
        else:
            if conflicts_since_restart >= restart_limit and len(eng.trail_lim) > 0:
                backjump(0)
                conflicts_since_restart = 0
                restart_limit = int(restart_limit * 1.3) + 16
                continue

            best_v = 0
            best_act = -1.0
            for v in range(1, n_vars + 1):
                if eng.assign[v] == 0 and activity[v] > best_act:
                    best_act = activity[v]
                    best_v = v

            if best_v == 0:
                new_col = list(col)
                for x in range(1, n + 1):
                    if is_u[x]:
                        rx = rep(x)
                        for c in range(k):
                            if eng.assign[var(rx, c)] == 1:
                                new_col[x] = c
                                break
                _, exact_e = verifier_partition_schur(new_col, k)
                return {
                    "status": "SAT",
                    "new_col": new_col,
                    "exact_E": exact_e,
                    "conflicts": conflicts,
                    "learned": learned_count,
                    "time_ms": (time.perf_counter() - t0) * 1000,
                }

            decisions += 1
            eng.trail_lim.append(len(eng.trail))
            eng.enqueue(best_v if saved_phase[best_v] == 1 else -best_v, -1)


# ==============================================================================
# UTILITAIRES : DESCENTE STRICTEMENT LOCALE (TH116 NON SATURANTE + TH114)
# ==============================================================================

def _strictly_local_descent_with_scalpel(
    start_col: List[int],
    n: int,
    k: int,
    budget_s: float,
    sym: bool,
    scalpel_threshold: int,
    seed: int = 123,
    allow_cdcl: bool = True,
) -> Tuple[List[int], int, Dict[str, Any]]:
    """
    4 répliques froides à pénalité STRICTEMENT LOCALE :
    - Seules les variables actuellement en conflit reçoivent un bonus +0.35.
    - Dès qu'une variable sort de conflit, sa pénalité est remise à 0.0 (zéro saturation !).
    - Si une nouvelle vallée distincte a E <= scalpel_threshold, tente un tir CDCL exact.
    """
    t0 = time.perf_counter()
    deadline = t0 + budget_s
    rng = random.Random(seed)
    temps = [0.16, 0.26, 0.40, 0.62]
    half = (n + 1) // 2 if sym else n

    agents: List[SchurBitmaskState] = []
    for aid in range(4):
        c = list(start_col)
        if aid >= 2:
            for _ in range(aid + 1):
                px = rng.randint(1, half)
                ng = rng.randrange(k)
                c[px] = ng
                if sym:
                    c[n + 1 - px] = ng
        agents.append(SchurBitmaskState(n, k, col=c))

    local_pen = [[0.0] * k for _ in range(half + 1)]
    _, best_e = verifier_partition_schur(start_col, k)
    best_col = list(start_col)
    seen_valleys: Set[Tuple[int, ...]] = set()
    scalpel_shots = 0
    steps = 0
    swaps = 0

    def eff_energy(st: SchurBitmaskState) -> float:
        pen = 0.0
        col_l = st.col
        for x in range(1, half + 1):
            pen += local_pen[x][col_l[x]]
        return st.total_conflicts + pen

    while time.perf_counter() < deadline and best_e > 0:
        for i, st in enumerate(agents):
            inv_t = 1.0 / temps[i]
            for _ in range(250):
                steps += 1
                x = rng.randint(1, half)
                cur = st.col[x]
                g = rng.randrange(k - 1)
                if g >= cur:
                    g += 1
                d_pen = local_pen[x][g] - local_pen[x][cur]
                if sym:
                    d_ex = st.move_symmetric(x, g)
                    d_eff = d_ex + d_pen
                    if d_eff > 0.0 and rng.random() >= math.exp(-d_eff * inv_t):
                        st.move_symmetric(x, cur)
                else:
                    d_ex = st.delta_move(x, g)
                    d_eff = d_ex + d_pen
                    if d_eff <= 0.0 or rng.random() < math.exp(-d_eff * inv_t):
                        st.move(x, g)

                if st.total_conflicts < best_e:
                    best_e = st.total_conflicts
                    best_col = list(st.col)
                    if best_e == 0:
                        ok, nc = verifier_partition_schur(best_col, k)
                        assert ok and nc == 0
                        return best_col, 0, {
                            "steps": steps, "swaps": swaps, "scalpel_shots": scalpel_shots,
                            "duree_s": round(time.perf_counter() - t0, 3),
                        }

        # Pénalité STRICTEMENT LOCALE sur la réplique la plus froide :
        # Remet à zéro toute variable sortie de conflit !
        cold = agents[0]
        cur_conf_set: Set[int] = set()
        for x in range(1, half + 1):
            is_c = cold.conflicts_for(x, cold.col[x]) > 0
            if sym and not is_c:
                y = n + 1 - x
                if y != x and cold.conflicts_for(y, cold.col[y]) > 0:
                    is_c = True
            if is_c:
                cur_conf_set.add(x)
                local_pen[x][cold.col[x]] = min(3.0, local_pen[x][cold.col[x]] + 0.35)
            else:
                for gg in range(k):
                    local_pen[x][gg] = 0.0

        # Si nouvelle vallée basse rencontrée et budget suffisant -> tir scalpel CDCL
        if allow_cdcl and cold.total_conflicts <= scalpel_threshold and (deadline - time.perf_counter()) > 0.9:
            sig = tuple(sorted(cur_conf_set))
            if sig and sig not in seen_valleys:
                seen_valleys.add(sig)
                scalpel_shots += 1
                unlocked, _ = extract_blocking_neighborhood(cold.col, k, list(cur_conf_set), max_vars=45, symmetric=False)
                rep_res = cdcl_lns_repair(cold.col, k, unlocked, timeout_s=0.75, symmetric=False, ignore_frozen_conflicts=False)
                if rep_res["status"] == "SAT" and rep_res["exact_E"] is not None and rep_res["exact_E"] < best_e:
                    best_e = rep_res["exact_E"]
                    best_col = rep_res["new_col"]
                    if best_e == 0:
                        ok, nc = verifier_partition_schur(best_col, k)
                        assert ok and nc == 0
                        return best_col, 0, {
                            "steps": steps, "swaps": swaps, "scalpel_shots": scalpel_shots,
                            "duree_s": round(time.perf_counter() - t0, 3),
                        }

        # Résonance TH114 entre répliques adjacentes
        effs = [eff_energy(st) for st in agents]
        for i in range(3):
            e1, e2 = effs[i], effs[i + 1]
            db = (1.0 / temps[i]) - (1.0 / temps[i + 1])
            if e2 <= e1 or rng.random() < math.exp((e1 - e2) * db):
                agents[i], agents[i + 1] = agents[i + 1], agents[i]
                effs[i], effs[i + 1] = effs[i + 1], effs[i]
                swaps += 1

    _, exact_chk = verifier_partition_schur(best_col, k)
    assert exact_chk == best_e
    return best_col, best_e, {
        "steps": steps, "swaps": swaps, "scalpel_shots": scalpel_shots,
        "duree_s": round(time.perf_counter() - t0, 3),
    }


# ==============================================================================
# ORCHESTRATION DES OPÉRATIONS CHIRURGICALES A & B
# ==============================================================================

def main() -> None:
    t_global = time.perf_counter()
    print("=" * 84)
    print("🔬 CHIRURGIE LNS-TH118 — SCALPEL CDCL & PÉNALITÉ STRICTEMENT LOCALE")
    print("   Source : etat_agents_schur.json (S(5)=160 E=2 & S(6)=537 E=9)")
    print("=" * 84)

    etat = json.loads(ETAT_PERSISTANT_PATH.read_text(encoding="utf-8"))

    # --------------------------------------------------------------------------
    # OPÉRATION A : CHIRURGIE SUR S(5) = 160 (E = 2 -> 0 ?)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("🩺 OPÉRATION A — S(5), N = 160 (budget max 18 s)")
    print("-" * 84)
    t_op_a = time.perf_counter()

    col_s5_init = [0] + list(etat["colonie_S5_160_sym"]["best_col"])
    _, e_s5_init = verifier_partition_schur(col_s5_init, 5)
    assert e_s5_init == etat["colonie_S5_160_sym"]["best_E"]
    st_s5 = SchurBitmaskState(160, 5, col=col_s5_init)
    seeds_s5 = st_s5.conflicted_elements()
    print(f"📍 État initial S(5)=160 : E={e_s5_init} | Variables en conflit : {seeds_s5}")

    # Résumé des bloqueurs pour les pivots
    unlocked_preview, summary_s5 = extract_blocking_neighborhood(col_s5_init, 5, seeds_s5, max_vars=20, symmetric=False)
    for sx in seeds_s5:
        info = ", ".join(f"c{g}:{cnt}" for g, cnt in summary_s5.get(sx, []))
        print(f"   • Bloqueurs alternatifs de {sx:3d} (actuel c{col_s5_init[sx]}) : [{info}]")

    best_s5_col = list(col_s5_init)
    best_s5_e = e_s5_init

    # 1. Scalpel CDCL direct en mode libre et mode symétrique
    cdcl_configs_a = [
        (False, 20), (False, 35), (False, 55), (False, 80),
        (True, 24), (True, 44), (True, 64),
    ]
    for is_sym, mv in cdcl_configs_a:
        if best_s5_e == 0 or (time.perf_counter() - t_op_a) > 10.0:
            break
        unl, _ = extract_blocking_neighborhood(col_s5_init, 5, seeds_s5, max_vars=mv, symmetric=is_sym)
        res = cdcl_lns_repair(col_s5_init, 5, unl, timeout_s=1.2, symmetric=is_sym, ignore_frozen_conflicts=False)
        mode_lbl = "sym " if is_sym else "libre"
        print(
            f"   🔪 Scalpel CDCL ({mode_lbl}, max_vars={mv:2d}, réel={len(unl):2d}) -> "
            f"{res['status']:7s} | conflits_SAT={res['conflicts']:5d} | {res['time_ms']:6.1f} ms"
        )
        if res["status"] == "SAT" and res["exact_E"] is not None and res["exact_E"] < best_s5_e:
            best_s5_e = res["exact_E"]
            best_s5_col = res["new_col"]

    # 2. Si E > 0, boucle hybride Pénalité Strictement Locale + Scalpel CDCL (budget restant jusqu'à 18s)
    if best_s5_e > 0:
        rem_a = 17.5 - (time.perf_counter() - t_op_a)
        if rem_a > 1.5:
            print(f"\n   ⚡ Descente strictement locale + scalpel CDCL ({rem_a:.1f} s disponibles)...")
            half_a = rem_a / 2.0
            best_s5_col, best_s5_e, stat_free = _strictly_local_descent_with_scalpel(
                best_s5_col, 160, 5, budget_s=half_a, sym=False, scalpel_threshold=2, seed=501
            )
            print(f"      [Libre] best_E={best_s5_e} | pas={stat_free['steps']:,} | swaps={stat_free['swaps']} | scalpels={stat_free['scalpel_shots']}")
            if best_s5_e > 0:
                rem_a2 = 17.5 - (time.perf_counter() - t_op_a)
                if rem_a2 > 0.8:
                    # Rester sur la souche symétrique si symétrique
                    cand_sym, cand_sym_e, stat_sym = _strictly_local_descent_with_scalpel(
                        col_s5_init, 160, 5, budget_s=rem_a2, sym=True, scalpel_threshold=2, seed=502
                    )
                    print(f"      [Sym  ] cand_E={cand_sym_e} | pas={stat_sym['steps']:,} | swaps={stat_sym['swaps']} | scalpels={stat_sym['scalpel_shots']}")
                    if cand_sym_e < best_s5_e:
                        best_s5_e = cand_sym_e
                        best_s5_col = cand_sym

    ok_a, chk_a = verifier_partition_schur(best_s5_col, 5)
    assert chk_a == best_s5_e
    print(f"   📊 Bilan Opération A (S(5)=160) : E_initial={e_s5_init} -> E_final={best_s5_e} (vérifié={ok_a})")

    lifted_s6_from_160: Optional[List[int]] = None
    if best_s5_e == 0:
        lifted_s6_from_160 = lift_schur_3n_plus_1(best_s5_col, 5)
        ok_l, nc_l = verifier_partition_schur(lifted_s6_from_160, 6)
        assert ok_l and nc_l == 0
        print(f"   🏆 S(5)=160 SCELLÉ À 0 CONFLIT ! Relèvement 3N+1 immédiat -> S(6) >= {len(lifted_s6_from_160)-1} VÉRIFIÉ (0 conflit) !")

    # --------------------------------------------------------------------------
    # OPÉRATION B : CHIRURGIE SUR S(6) = 537 (E = 9 -> ?)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("🩺 OPÉRATION B — S(6), N = 537 (budget max 18 s)")
    print("-" * 84)
    t_op_b = time.perf_counter()

    col_s6_init = [0] + list(etat["colonie_S6_537"]["best_col"])
    _, e_s6_init = verifier_partition_schur(col_s6_init, 6)
    assert e_s6_init == etat["colonie_S6_537"]["best_E"]
    best_s6_col = list(col_s6_init)
    best_s6_e = e_s6_init

    st_s6 = SchurBitmaskState(537, 6, col=best_s6_col)
    all_seeds_s6 = st_s6.conflicted_elements()
    ilot_1 = [x for x in [12, 14, 24, 26] if x in all_seeds_s6]
    ilot_2 = [x for x in all_seeds_s6 if x not in ilot_1]
    print(f"📍 État initial S(6)=537 : E={best_s6_e} | Îlot 1={ilot_1} | Îlot 2={ilot_2}")

    _, sum_s6 = extract_blocking_neighborhood(best_s6_col, 6, all_seeds_s6, max_vars=30, symmetric=False)
    for sx in all_seeds_s6:
        info = ", ".join(f"c{g}:{cnt}" for g, cnt in sum_s6.get(sx, []))
        print(f"   • Bloqueurs alternatifs de {sx:2d} (actuel c{best_s6_col[sx]}) : [{info}]")

    # 1. Chirurgie partielle ciblée sur l'îlot {12, 14, 24, 26}
    if ilot_1:
        print("\n   🔪 1) Chirurgie partielle ciblée sur l'îlot {12, 14, 24, 26} :")
        for mv in [25, 45, 70]:
            unl, _ = extract_blocking_neighborhood(best_s6_col, 6, ilot_1, max_vars=mv, symmetric=False)
            res = cdcl_lns_repair(best_s6_col, 6, unl, timeout_s=1.5, symmetric=False, ignore_frozen_conflicts=True)
            print(
                f"      • Îlot 1 (max_vars={mv:2d}, réel={len(unl):2d}) -> "
                f"{res['status']:7s} | exact_E={res['exact_E']} | conflits_SAT={res['conflicts']:5d} | {res['time_ms']:6.1f} ms"
            )
            if res["status"] == "SAT" and res["exact_E"] is not None and res["exact_E"] < best_s6_e:
                best_s6_e = res["exact_E"]
                best_s6_col = res["new_col"]
                print(f"      ✅ Réduction immédiate obtenue : E = {best_s6_e} !")
                if best_s6_e == 0:
                    break

    # 2. Chirurgie globale CDCL TH118 sur les conflits restants
    if best_s6_e > 0:
        cur_seeds = SchurBitmaskState(537, 6, col=best_s6_col).conflicted_elements()
        print(f"\n   🔪 2) Chirurgie globale CDCL sur {cur_seeds} :")
        for mv in [35, 60, 90]:
            if (time.perf_counter() - t_op_b) > 9.0:
                break
            unl, _ = extract_blocking_neighborhood(best_s6_col, 6, cur_seeds, max_vars=mv, symmetric=False)
            res = cdcl_lns_repair(best_s6_col, 6, unl, timeout_s=1.8, symmetric=False, ignore_frozen_conflicts=False)
            print(
                f"      • Global (max_vars={mv:2d}, réel={len(unl):2d}) -> "
                f"{res['status']:7s} | exact_E={res['exact_E']} | conflits_SAT={res['conflicts']:5d} | {res['time_ms']:6.1f} ms"
            )
            if res["status"] == "SAT" and res["exact_E"] is not None and res["exact_E"] < best_s6_e:
                best_s6_e = res["exact_E"]
                best_s6_col = res["new_col"]
                if best_s6_e == 0:
                    break

    # 3. Descente à pénalité strictement locale (TH116 non saturante + TH114)
    if best_s6_e > 0:
        rem_b = 16.5 - (time.perf_counter() - t_op_b)
        if rem_b > 1.2:
            print(f"\n   ⚡ 3) Descente strictement locale sur S(6)=537 ({rem_b:.1f} s)...")
            best_s6_col, best_s6_e, stat_s6 = _strictly_local_descent_with_scalpel(
                best_s6_col, 537, 6, budget_s=rem_b, sym=False, scalpel_threshold=4, seed=601, allow_cdcl=False
            )
            print(f"      [Local S6] best_E={best_s6_e} | pas={stat_s6['steps']:,} | swaps={stat_s6['swaps']}")
            # Tir final scalpel CDCL si E <= 6 et encore un peu de marge
            if 0 < best_s6_e <= 6:
                cur_seeds = SchurBitmaskState(537, 6, col=best_s6_col).conflicted_elements()
                unl, _ = extract_blocking_neighborhood(best_s6_col, 6, cur_seeds, max_vars=65, symmetric=False)
                res_fin = cdcl_lns_repair(best_s6_col, 6, unl, timeout_s=1.5, symmetric=False, ignore_frozen_conflicts=False)
                print(f"      [Scalpel final E<={best_s6_e}] -> {res_fin['status']} | exact_E={res_fin['exact_E']}")
                if res_fin["status"] == "SAT" and res_fin["exact_E"] is not None and res_fin["exact_E"] < best_s6_e:
                    best_s6_e = res_fin["exact_E"]
                    best_s6_col = res_fin["new_col"]

    ok_b, chk_b = verifier_partition_schur(best_s6_col, 6)
    assert chk_b == best_s6_e
    print(f"   📊 Bilan Opération B (S(6)=537) : E_initial={e_s6_init} -> E_final={best_s6_e} (vérifié={ok_b})")

    # Mise à jour persistante de etat_agents_schur.json
    if best_s5_e <= etat["colonie_S5_160_sym"]["best_E"]:
        etat["colonie_S5_160_sym"]["best_E"] = best_s5_e
        etat["colonie_S5_160_sym"]["best_col"] = best_s5_col[1:]
    if best_s6_e <= etat["colonie_S6_537"]["best_E"]:
        etat["colonie_S6_537"]["best_E"] = best_s6_e
        etat["colonie_S6_537"]["best_col"] = best_s6_col[1:]
    etat["chirurgie_lns_th118"] = {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "S5_160_E_initial": e_s5_init,
        "S5_160_E_final": best_s5_e,
        "S6_537_E_initial": e_s6_init,
        "S6_537_E_final": best_s6_e,
        "duree_s": round(time.perf_counter() - t_global, 2),
    }
    ETAT_PERSISTANT_PATH.write_text(json.dumps(etat, indent=2, ensure_ascii=False), encoding="utf-8")

    # Mise à jour de temoins_schur_th118.json si un témoin E=0 a été décroché
    if SORTIE_TEMOINS.exists() and (best_s5_e == 0 or best_s6_e == 0):
        tem = json.loads(SORTIE_TEMOINS.read_text(encoding="utf-8"))
        if best_s5_e == 0:
            ok5, nc5 = verifier_partition_schur(best_s5_col, 5)
            assert ok5 and nc5 == 0
            tem["temoins_verifies"]["S5_N160_LNS_TH118"] = best_s5_col[1:]
            if lifted_s6_from_160 is not None:
                tem["temoins_verifies"]["S6_N481_lift_de_160"] = lifted_s6_from_160[1:]
        if best_s6_e == 0:
            ok6, nc6 = verifier_partition_schur(best_s6_col, 6)
            assert ok6 and nc6 == 0
            tem["temoins_verifies"]["S6_N537_LNS_TH118"] = best_s6_col[1:]
        SORTIE_TEMOINS.write_text(json.dumps(tem, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 84)
    print(f"💾 État mis à jour dans : {ETAT_PERSISTANT_PATH}")
    print(f"⏱️  Durée totale chirurgie : {etat['chirurgie_lns_th118']['duree_s']} s")
    print("=" * 84)


if __name__ == "__main__":
    main()
