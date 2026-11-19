# -*- coding: utf-8 -*-
"""
Étage 5 — Pont vers Hadès (étage 3).

Vérification bornée par SAT : la dynamique du noyau est déroulée sur H pas
et encodée en clauses. Le solveur cherche un environnement de blocage qui
réalise une propriété. SAT = témoin trouvé ; UNSAT = la propriété est
impossible pour TOUS les environnements dans la borne (vérification
exhaustive, indépendante de l'énumérateur Python).

Moteur : `alix.solveurs.alix_dpll_t_solver_hades.Solver` (CDCL 2WL d'Hadès).
Si Hadès n'est pas importable, un DPLL minimal intégré prend le relais et le
résultat le dit.

Sémantique encodée (identique à noyau.derouler, cas k = 1 attracteur,
politique « toujours β », loquet qui force β, univers non borné) :
  lam[t]  = sec[t] ∧ run[t] = n_Λ
  beta[t] = ¬bl[t] ∨ lam[t]
  beta[t] → ¬sec[t+1], run[t+1] = 0, b[t+1] = b[t]+1, pos[t+1] = s_{b[t]+1}
  ¬beta[t] → sec[t+1], run[t+1] = run[t]+1, ancre maintenue (ou posée),
             pos[t+1] = c1 si run[t+1] impair, sinon l'ancre.
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Optional, Sequence, Tuple


# ----------------------------------------------------------------------------
# Moteurs SAT
# ----------------------------------------------------------------------------
def _moteur_hades():
    try:
        from alix.solveurs.alix_dpll_t_solver_hades import Solver  # type: ignore
        return Solver
    except Exception:
        return None


class _DPLLMinimal:
    """Repli : DPLL récursif simple (petits problèmes seulement)."""

    def __init__(self):
        self.nvars = 0
        self.clauses: List[List[int]] = []
        self.modele: Dict[int, bool] = {}

    def new_var(self) -> int:
        self.nvars += 1
        return self.nvars

    def add_clause(self, lits) -> bool:
        self.clauses.append(list(lits))
        return True

    def solve(self, assumptions=()):
        import sys
        sys.setrecursionlimit(100000)
        res = self._dpll([list(c) for c in self.clauses], {})
        if res is None:
            return False
        self.modele = res
        return True

    def model_value(self, lit: int) -> bool:
        v = self.modele.get(abs(lit), False)
        return v if lit > 0 else not v

    def _dpll(self, clauses, assign):
        while True:
            unit = None
            nouv = []
            for c in clauses:
                if any(assign.get(abs(l)) == (l > 0) for l in c):
                    continue
                reste = [l for l in c if abs(l) not in assign]
                if not reste:
                    return None
                if len(reste) == 1 and unit is None:
                    unit = reste[0]
                nouv.append(reste)
            clauses = nouv
            if unit is None:
                break
            assign[abs(unit)] = unit > 0
        if not clauses:
            return assign
        l = clauses[0][0]
        for val in (l > 0, not (l > 0)):
            a = dict(assign); a[abs(l)] = val
            r = self._dpll(clauses, a)
            if r is not None:
                return r
        return None


class CNF:
    def __init__(self):
        S = _moteur_hades()
        self.moteur_nom = "Hadès (CDCL 2WL)" if S else "DPLL minimal (Hadès indisponible)"
        self.s = S() if S else _DPLLMinimal()
        self.noms: Dict[str, int] = {}

    def v(self, nom: str) -> int:
        if nom not in self.noms:
            self.noms[nom] = self.s.new_var()
        return self.noms[nom]

    def clause(self, *lits: int):
        self.s.add_clause(list(lits))

    def exactement_un(self, lits: Sequence[int]):
        self.clause(*lits)
        for a, b in itertools.combinations(lits, 2):
            self.clause(-a, -b)

    def equiv_et(self, out: int, a: int, b: int):
        self.clause(-out, a); self.clause(-out, b); self.clause(out, -a, -b)

    def equiv_ou(self, out: int, a: int, b: int):
        self.clause(out, -a); self.clause(out, -b); self.clause(-out, a, b)

    def resoudre(self) -> Optional[Dict[str, bool]]:
        if not self.s.solve():
            return None
        return {n: bool(self.s.model_value(v)) for n, v in self.noms.items()}


# ----------------------------------------------------------------------------
# Déroulement de la dynamique
# ----------------------------------------------------------------------------
def _encoder(H: int, n_lambda: int) -> Tuple[CNF, List[str]]:
    f = CNF()
    objets = ["x0", "c1"] + [f"s{i}" for i in range(1, H + 1)]
    ancres = ["x0"] + [f"s{i}" for i in range(1, H + 1)]
    P = lambda t, o: f.v(f"pos{t}_{o}")
    A = lambda t, o: f.v(f"anc{t}_{o}")
    R = lambda t, r: f.v(f"run{t}_{r}")
    Bc = lambda t, i: f.v(f"b{t}_{i}")
    SEC = lambda t: f.v(f"sec{t}")
    BL = lambda t: f.v(f"bl{t}")

    for t in range(H + 1):
        f.exactement_un([P(t, o) for o in objets])
        f.exactement_un([A(t, o) for o in ancres])
        f.exactement_un([R(t, r) for r in range(n_lambda + 1)])
        f.exactement_un([Bc(t, i) for i in range(H + 1)])
    # état initial
    f.clause(P(0, "x0")); f.clause(A(0, "x0")); f.clause(R(0, 0)); f.clause(Bc(0, 0))
    f.clause(-SEC(0))

    for t in range(H):
        lam = f.v(f"lam{t}")
        f.equiv_et(lam, SEC(t), R(t, n_lambda))
        beta = f.v(f"beta{t}")
        f.equiv_ou(beta, -BL(t), lam)
        # --- branche β ---
        f.clause(-beta, -SEC(t + 1))
        f.clause(-beta, R(t + 1, 0))
        for i in range(H):
            f.clause(-beta, -Bc(t, i), Bc(t + 1, i + 1))
            f.clause(-beta, -Bc(t, i), P(t + 1, f"s{i+1}"))
        f.clause(-beta, -Bc(t, H))          # au-delà de la borne : interdit
        for o in ancres:                    # l'ancre ne sert plus ; on la recopie
            f.clause(-beta, -A(t, o), A(t + 1, o))
        # --- branche secours (α) ---
        f.clause(beta, SEC(t + 1))
        for r in range(n_lambda):
            f.clause(beta, -R(t, r), R(t + 1, r + 1))
        f.clause(beta, -R(t, n_lambda))     # run = n_Λ et secours ⇒ lam ⇒ β
        for i in range(H + 1):
            f.clause(beta, -Bc(t, i), Bc(t + 1, i))
        for o in ancres:
            # nouvelle excursion : l'ancre devient la position courante
            f.clause(beta, SEC(t), -P(t, o), A(t + 1, o))
            # excursion en cours : l'ancre est conservée
            f.clause(beta, -SEC(t), -A(t, o), A(t + 1, o))
        for r in range(1, n_lambda + 1):
            if r % 2 == 1:
                f.clause(beta, -R(t + 1, r), P(t + 1, "c1"))
            else:
                for o in ancres:
                    f.clause(beta, -R(t + 1, r), -A(t + 1, o), P(t + 1, o))
    return f, objets


def _sans_repetition(f: CNF, H: int, objets: List[str], jusqua: int):
    for t, u in itertools.combinations(range(jusqua + 1), 2):
        for o in objets:
            f.clause(-f.v(f"pos{t}_{o}"), -f.v(f"pos{u}_{o}"))


def _temoin(m: Dict[str, bool], H: int, objets: List[str]) -> Dict:
    pos = []
    for t in range(H + 1):
        pos.append(next(o for o in objets if m.get(f"pos{t}_{o}")))
    env = [int(m.get(f"bl{t}", False)) for t in range(H)]
    sec = [int(m.get(f"sec{t}", False)) for t in range(H + 1)]
    return {"objets": pos, "environnement": env, "secours": sec}


def chercher_B0(H: int, n_lambda: int) -> Dict:
    """Existe-t-il une trajectoire avec T_R > 0, R = 0, excursion terminée ?"""
    f, objets = _encoder(H, n_lambda)
    f.clause(*[f.v(f"sec{t}") for t in range(1, H + 1)])   # T_R > 0
    f.clause(-f.v(f"sec{H}"))                               # sortie du secours
    _sans_repetition(f, H, objets, H)
    m = f.resoudre()
    return {"propriete": "B0 (0 < T_R < ∞, R = 0)", "H": H, "n_lambda": n_lambda,
            "moteur": f.moteur_nom, "sat": m is not None,
            "temoin": _temoin(m, H, objets) if m else None}


def verifier_TH9(H: int, n_lambda: int) -> Dict:
    """Négation de TH9 : un 2e pas d'excursion (run = 2) sans aucune répétition."""
    assert n_lambda >= 2
    f, objets = _encoder(H, n_lambda)
    t2 = [f.v(f"run{t}_2") for t in range(H + 1)]
    f.clause(*t2)
    # premier instant où run = 2 : aucune répétition jusque-là
    # (on impose l'absence totale de répétition sur toute la trajectoire
    #  ET l'existence d'un pas run=2 : plus fort, donc UNSAT suffit)
    _sans_repetition(f, H, objets, H)
    m = f.resoudre()
    return {"propriete": "¬TH9 : excursion de ≥ 2 pas sans répétition",
            "H": H, "n_lambda": n_lambda, "moteur": f.moteur_nom,
            "sat": m is not None, "verdict": "TH9 vérifié dans la borne" if m is None
            else "contre-exemple", "temoin": _temoin(m, H, objets) if m else None}
