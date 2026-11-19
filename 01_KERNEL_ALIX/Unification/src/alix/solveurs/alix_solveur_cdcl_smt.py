#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
   ⚖️🧠🏛️ SOLVEUR UNIVERSEL DE CONTRAINTES LOGIQUES & STRATÉGIQUES (CDCL(T) v2.0)
   Compétence #3 de la Séquence Souveraine (1 -> 4 -> 3 -> 2)
   Édition Hadès × Panthéon K-SIL : 2-Watched Literals + Cotton-Maler IDL/RDL
===============================================================================
Auteurs : Christian Duguay (L'Artisan-Démiurge) & Alix (Panthéon K-SIL)
Sparring & Noyau CDCL(T) : Hadès (Claude) — `alix_dpll_t_solver_hades.py`
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — 0 W GPU, 100% Hors-Ligne, Stdlib pure

Architecture CDCL(T) v2.0 :
  1. Noyau SAT CDCL Haute Vitesse (`Solver` d'Hadès) :
     - **2-Watched Literals (2WL)** : BCP sans balayage global des clauses.
     - **Analyse de conflit 1-UIP + Minimisation Locale** des clauses apprises.
     - **VSIDS sur tas binaire paresseux + Phase Saving + Redémarrages de Luby**.
     - **Purge adaptative LBD (Literal Block Distance)** de la base de clauses apprises.
     - **Extraction de `UNSAT Core` (`_analyze_final`) et `MUS` (`minimal_unsat_subset`)**.
  2. Solveur de Théorie `DifferenceLogic` (`IDL` entiers / `RDL` réels avec infinitésimal $\delta$) :
     - Maintien incrémental des potentiels par l'algorithme de **Cotton-Maler** (Dijkstra
       sur coûts réduits : un seul parcours par arête ajoutée, zéro coût de restauration
       des potentiels au backtrack).
     - Détection de cycle négatif simple -> génération du **lemme de théorie minimal**
       renvoyé au noyau CDCL comme clause de conflit.
===============================================================================
"""
from __future__ import annotations

from alix.socle.chemins import VAULT_DIR
import itertools
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MOTEURS_DIR = (VAULT_DIR / "Organes_Souverains" / "Moteurs")
if str(MOTEURS_DIR) not in sys.path:
    pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(MOTEURS_DIR))

from alix.solveurs.alix_dpll_t_solver_hades import (
    Solver,
    DifferenceLogic,
    luby,
)


# ==============================================================================
# 🧮 1. FAÇADE SOUVERAINE `SolveurCDCL` & `CompilateurSMT` (SUR NOYAU 2WL HADÈS)
# ==============================================================================
class CompilateurSMT:
    @staticmethod
    def clauses_at_most_one(lits: Sequence[int]) -> List[List[int]]:
        return [[-a, -b] for a, b in itertools.combinations(lits, 2)]

    @staticmethod
    def clauses_exactly_one(lits: Sequence[int]) -> List[List[int]]:
        return [list(lits)] + CompilateurSMT.clauses_at_most_one(lits)

    @staticmethod
    def clauses_implies(a: int, b: int) -> List[List[int]]:
        return [[-a, b]]


class SolveurCDCL:
    """
    Façade nommée au-dessus du moteur `Solver` 2WL + Cotton-Maler `IDL/RDL` d'Hadès.
    Gère à la fois les variables booléennes nommées, les contraintes souples/nommées
    (avec extraction de `MUS` minimal) et les contraintes temporelles/arithmétiques
    `x - y <= c` en Difference Logic (`theory="idl"` ou `"rdl"`).
    """

    def __init__(self, theory: Optional[str] = None):
        self.engine = Solver(theory=theory)
        self.name_to_var: Dict[str, int] = {}
        self.var_names: Dict[int, str] = {}
        self.selector_to_label: Dict[int, str] = {}
        self.selectors_order: List[int] = []

    def var(self, name: str) -> int:
        if name in self.name_to_var:
            return self.name_to_var[name]
        v = self.engine.new_var()
        self.name_to_var[name] = v
        self.var_names[v] = name
        return v

    def add_clause(self, lits: Sequence[int]) -> bool:
        return self.engine.add_clause(lits)

    def add_named_constraint(self, label: str, clauses_list: Sequence[Sequence[int]]) -> int:
        """
        Crée un sélecteur d'assomption unique `s` gouvernant toutes les clauses de `clauses_list`
        via `(-s OR clause)`. Permet d'extraire le `MUS` exact sur des contraintes multi-clauses.
        """
        s = self.engine.new_var()
        for cl in clauses_list:
            self.engine.add_clause([-s] + list(cl))
        self.selector_to_label[s] = label
        self.selectors_order.append(s)
        return s

    def solve(self, assumptions: Optional[Sequence[int]] = None) -> Tuple[bool, Dict[int, bool]]:
        assump = self.selectors_order if assumptions is None else list(assumptions)
        ok = self.engine.solve(assumptions=assump)
        if not ok:
            return False, {}
        mod = {v: self.engine.model_value(v) for v in range(1, self.engine.nvars + 1)}
        return True, mod

    def extraire_noyau_unsat_minimal(self) -> List[str]:
        mus_sels = self.engine.minimal_unsat_subset(self.selectors_order)
        if not mus_sels:
            return []
        return [self.selector_to_label[s] for s in mus_sels if s in self.selector_to_label]


# ==============================================================================
# 🏆 2. BANC D'ESSAI SOUVERAIN CDCL(T) v2.0 (8 ÉPREUVES BOOLÉENNES + IDL + RDL)
# ==============================================================================
def executer_banc_cdcl_smt() -> None:
    print("=" * 92)
    print(" ⚖️🧠🏛️ BANC D'ESSAI SOLVEUR CDCL(T) v2.0 — HADÈS 2WL + COTTON-MALER IDL/RDL + MUS")
    print("=" * 92)
    t_global = time.perf_counter()
    ok_total = 0

    # 1. Allocation matérielle sous contraintes
    t0 = time.perf_counter()
    s1 = SolveurCDCL()
    daemons = ["ARGUS", "SONG", "CEGIS"]
    unites = ["CPU_P", "CPU_E", "NPU_48TOPS"]
    v_map = {(d, u): s1.var(f"{d}_sur_{u}") for d in daemons for u in unites}
    for d in daemons:
        s1.add_named_constraint(
            f"Chaque daemon `{d}` sur exactement 1 unité",
            CompilateurSMT.clauses_exactly_one([v_map[(d, u)] for u in unites]),
        )
    for u in unites:
        s1.add_named_constraint(
            f"Unité `{u}` reçoit au plus 1 daemon lourd",
            CompilateurSMT.clauses_at_most_one([v_map[(d, u)] for d in daemons]),
        )
    s1.add_named_constraint("ARGUS exige CPU_P (BitBlt Win32)", [[v_map[("ARGUS", "CPU_P")]]])
    s1.add_named_constraint("SONG exige NPU_48TOPS (YAMNet + Whisper)", [[v_map[("SONG", "NPU_48TOPS")]]])
    sat1, mod1 = s1.solve()
    alloc1 = {d: u for (d, u), vid in v_map.items() if mod1.get(vid)}
    dt1 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert sat1 and alloc1 == {"ARGUS": "CPU_P", "SONG": "NPU_48TOPS", "CEGIS": "CPU_E"}
    ok_total += 1
    print(f" ✅ [1. ALLOCATION MATÉRIELLE SOUS CONTRAINTES] ({dt1} ms) -> SAT : {alloc1}")

    # 2. Extraction du MUS booléen (Loi PSI-26)
    t0 = time.perf_counter()
    s2 = SolveurCDCL()
    mode_furtif = s2.var("mode_furtif")
    camera_active = s2.var("camera_active")
    commande_christian = s2.var("commande_christian")
    audit_visuel_continu = s2.var("audit_visuel_continu")
    wifi_ouvert = s2.var("wifi_ouvert")
    s2.add_named_constraint("R1_LOI_PSI_26 (camera_active -> commande_christian)", [[-camera_active, commande_christian]])
    s2.add_named_constraint("R2_BRUIT_WIFI (wifi_ouvert)", [[wifi_ouvert]])
    s2.add_named_constraint("R3_ABSENCE_COMMANDE (NON commande_christian)", [[-commande_christian]])
    s2.add_named_constraint("R4_BRUIT_FURTIF (mode_furtif)", [[mode_furtif]])
    s2.add_named_constraint("R5_REQUETE_EXTERNE (audit_visuel_continu -> camera_active)", [[audit_visuel_continu], [-audit_visuel_continu, camera_active]])
    mus2 = s2.extraire_noyau_unsat_minimal()
    dt2 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert set(mus2) == {
        "R1_LOI_PSI_26 (camera_active -> commande_christian)",
        "R3_ABSENCE_COMMANDE (NON commande_christian)",
        "R5_REQUETE_EXTERNE (audit_visuel_continu -> camera_active)",
    }
    ok_total += 1
    print(f" ✅ [2. EXTRACTION MUS BOOLÉEN (PSI-23 / PSI-26)] ({dt2} ms) -> {len(mus2)} règles isolées sur 5")

    # 3. Déduction d'intégrité croisée A/B/C
    t0 = time.perf_counter()
    s3 = SolveurCDCL()
    A, B, C = s3.var("Acteur_A"), s3.var("Acteur_B"), s3.var("Acteur_C")
    s3.add_clause([-A, -B])
    s3.add_clause([-A, -C])
    s3.add_clause([A, B, C])
    s3.add_clause([-B, A])
    s3.add_clause([-A, B])
    sat3, mod3 = s3.solve()
    verite3 = {"A": mod3[A], "B": mod3[B], "C": mod3[C]}
    dt3 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert sat3 and verite3 == {"A": False, "B": False, "C": True}
    ok_total += 1
    print(f" ✅ [3. DÉDUCTION D'INTÉGRITÉ CROISÉE A/B/C] ({dt3} ms) -> Solution unique : {verite3}")

    # 4. Pigeonhole PHP(6, 5) avec 2-Watched Literals + 1-UIP + Luby
    t0 = time.perf_counter()
    s4 = Solver()
    P, H = 6, 5
    pvar = lambda p, h: p * H + h + 1
    for p in range(P):
        s4.add_clause([pvar(p, h) for h in range(H)])
    for h in range(H):
        for p1, p2 in itertools.combinations(range(P), 2):
            s4.add_clause([-pvar(p1, h), -pvar(p2, h)])
    sat4 = s4.solve()
    dt4 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert sat4 is False
    ok_total += 1
    print(
        f" ✅ [4. PREUVE UNSAT PHP(6->5) EN 2-WATCHED LITERALS] ({dt4} ms) "
        f"-> UNSAT ({s4.n_conflicts} conflits, {s4.n_props} propagations 2WL)"
    )

    # 5. Ordonnancement Temporel DPLL(T) `IDL` (Cotton-Maler : 6 tâches sur 1 ressource)
    t0 = time.perf_counter()
    durs = {"T0": 3, "T1": 5, "T2": 2, "T3": 4, "T4": 6, "T5": 1}
    horizon_exact = sum(durs.values())  # 21 ms

    def resoudre_ordonnancement(deadline: int) -> Tuple[bool, Optional[Dict[str, int]], int]:
        st = Solver("idl")
        for j, d in durs.items():
            st.add_clause([st.ge(j, None, 0)])
            st.add_clause([st.le(j, None, deadline - d)])
        for j1, j2 in itertools.combinations(durs.keys(), 2):
            st.add_clause([st.le(j1, j2, -durs[j1]), st.le(j2, j1, -durs[j2])])
        res = st.solve()
        return res, st.int_model, st.n_theory_conflicts

    sat_21, sched_21, _ = resoudre_ordonnancement(horizon_exact)
    sat_20, _, lemmes_20 = resoudre_ordonnancement(horizon_exact - 1)
    dt5 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert sat_21 is True and sat_20 is False and sched_21 is not None
    ok_total += 1
    print(
        f" ✅ [5. ORDONNANCEMENT DPLL(T) IDL COTTON-MALER (6 TÂCHES)] ({dt5} ms) "
        f"-> D=21ms SAT {sched_21} | D=20ms UNSAT ({lemmes_20} lemmes de cycles négatifs)"
    )

    # 6. Extraction de MUS Temporel DPLL(T) `IDL` (Conflit de fenêtre d'exécution)
    t0 = time.perf_counter()
    s6 = SolveurCDCL(theory="idl")
    eng6 = s6.engine
    for j in ("ARGUS", "SONG", "CEGIS"):
        eng6.add_clause([eng6.ge(j, None, 0)])
    for j1, j2 in itertools.combinations(("ARGUS", "SONG", "CEGIS"), 2):
        eng6.add_clause([eng6.le(j1, j2, -4), eng6.le(j2, j1, -4)])  # 4 ms chacune, exclusion mutuelle
    s6.add_named_constraint("ARGUS démarre à t=0 (fin <= 4ms)", [[eng6.le("ARGUS", None, 0)]])
    s6.add_named_constraint("SONG démarre à t=0 (fin <= 4ms)", [[eng6.le("SONG", None, 0)]])
    s6.add_named_constraint("CEGIS démarre avant t=100ms", [[eng6.le("CEGIS", None, 100)]])
    mus6 = s6.extraire_noyau_unsat_minimal()
    dt6 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert set(mus6) == {"ARGUS démarre à t=0 (fin <= 4ms)", "SONG démarre à t=0 (fin <= 4ms)"}
    ok_total += 1
    print(f" ✅ [6. MUS TEMPOREL DPLL(T) IDL] ({dt6} ms) -> Conflit isolé : {mus6}")

    # 7. Théorie Réelle `RDL` avec Infinitésimal delta (`0 < x - y < 1` : SAT dans R, UNSAT dans Z)
    t0 = time.perf_counter()
    s_rdl = Solver("rdl")
    s_rdl.add_clause([s_rdl.gt("x", "y", 0)])
    s_rdl.add_clause([s_rdl.lt("x", "y", 1)])
    ok_rdl = s_rdl.solve()
    val_diff = s_rdl.int_model["x"] - s_rdl.int_model["y"] if s_rdl.int_model else None

    s_idl = Solver("idl")
    s_idl.add_clause([s_idl.gt("x", "y", 0)])
    s_idl.add_clause([s_idl.lt("x", "y", 1)])
    ok_idl = s_idl.solve()
    dt7 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert ok_rdl is True and ok_idl is False and val_diff is not None and 0 < val_diff < 1
    ok_total += 1
    print(
        f" ✅ [7. SÉPARATION RDL (RÉELS) vs IDL (ENTIERS) SUR `0 < x - y < 1`] ({dt7} ms) "
        f"-> RDL=SAT (x-y = {val_diff}), IDL=UNSAT"
    )

    # 8. Topologie K4 (3 couleurs vs 4 couleurs)
    t0 = time.perf_counter()
    def tester_k4(nb_couleurs: int) -> bool:
        sc = SolveurCDCL()
        nodes = [0, 1, 2, 3]
        cv = {(n, c): sc.var(f"n{n}_c{c}") for n in nodes for c in range(nb_couleurs)}
        for n in nodes:
            for cl in CompilateurSMT.clauses_exactly_one([cv[(n, c)] for c in range(nb_couleurs)]):
                sc.add_clause(cl)
        for n1, n2 in itertools.combinations(nodes, 2):
            for c in range(nb_couleurs):
                sc.add_clause([-cv[(n1, c)], -cv[(n2, c)]])
        ok, _ = sc.solve()
        return ok

    k4_3col, k4_4col = tester_k4(3), tester_k4(4)
    dt8 = round((time.perf_counter() - t0) * 1000.0, 2)
    assert (not k4_3col) and k4_4col
    ok_total += 1
    print(
        f" ✅ [8. TOPOLOGIE K4 (3 COULEURS vs 4 COULEURS)] ({dt8} ms) "
        f"-> 3 couleurs={k4_3col} (UNSAT), 4 couleurs={k4_4col} (SAT)"
    )

    dt_tot = round((time.perf_counter() - t_global) * 1000.0, 2)
    print("=" * 92)
    print(f" 🏆 BILAN SOLVEUR CDCL(T) v2.0 : {ok_total}/8 épreuves logiques & temporelles certifiées en {dt_tot} ms !")
    print("=" * 92)


if __name__ == "__main__":
    executer_banc_cdcl_smt()
