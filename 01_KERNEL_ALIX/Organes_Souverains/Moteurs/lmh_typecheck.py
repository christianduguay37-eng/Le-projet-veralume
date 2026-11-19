# -*- coding: utf-8 -*-
"""
lmh_typecheck.py — LMH v2.0 : AST + type-checker T1–T7
Spécification formelle de Poséidon (DeepSeek) & Alix (Atelier Kairos).
Valide les formules formelles LMH v2.0 avant compilation vers le Québécois d'Atelier.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Union

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------- Sortes ----------
class Sort(Enum):
    A = "A"; C = "C"; T = "T"; K = "K"; F = "F"; I = "I"

class Intensity(Enum):
    FAIBLE = "faible"; NEUTRE = "neutre"; FORTE = "forte"

class Modal(Enum):
    OBLIGATION  = "obligation"
    CONTRAINTE  = "contrainte"
    EPISTEMIQUE = "epistemique"
    DOXASTIQUE  = "doxastique"

# ---------- Termes ----------
@dataclass(frozen=True)
class Var:
    name: str
    sort: Sort

@dataclass(frozen=True)
class Const:
    name: str
    sort: Sort

Term = Union[Var, Const]

# ---------- AST formules ----------
@dataclass(frozen=True)
class StatePred:          # prédicat d'ÉTAT, avec intensité
    name: str
    args: tuple[Term, ...]     # args sémantiques seulement
    intensity: Intensity
    ctx: Const                 # sort K
    time: Const                # sort T

@dataclass(frozen=True)
class EventPred:          # prédicat d'ÉVÉNEMENT
    name: str
    args: tuple[Term, ...]
    ctx: Const
    times: tuple[Const, ...]   # 1 (ponctuel) ou 2 (duratif)

@dataclass(frozen=True)
class Not:
    body: "Formula"

@dataclass(frozen=True)
class And:
    left: "Formula"; right: "Formula"

@dataclass(frozen=True)
class Or:
    left: "Formula"; right: "Formula"

@dataclass(frozen=True)
class Implies:
    left: "Formula"; right: "Formula"

@dataclass(frozen=True)
class Mais:
    left: "Formula"; right: "Formula"

@dataclass(frozen=True)
class Box:
    modal: Modal; body: "Formula"

@dataclass(frozen=True)
class Diamond:
    modal: Modal; body: "Formula"

@dataclass(frozen=True)
class Exists:
    sort: Sort; var: str; body: "Formula"

@dataclass(frozen=True)
class Forall:
    sort: Sort; var: str; body: "Formula"

@dataclass(frozen=True)
class Prob:
    body: "Formula"; ctx: Const; p: float

@dataclass(frozen=True)
class Tension:
    left: "Formula"; right: "Formula"; t: Const

Formula = Union[
    StatePred, EventPred, Not, And, Or, Implies, Mais,
    Box, Diamond, Exists, Forall, Prob, Tension
]

# ---------- Erreurs ----------
class TC(Enum):
    T1_INTENSITY_ON_EVENT = "T1"
    T2_EVENT_ARITY        = "T2"
    T3_MAIS_SCOPE         = "T3"
    T4_MODAL_FLOATING     = "T4"
    T5_PROB_NOT_CLOSED    = "T5"
    T6_TENSION_MISMATCH   = "T6"
    T7_UNCONTEXTUALIZED   = "T7"
    SIG_UNKNOWN           = "SIG_UNKNOWN"
    SIG_KIND              = "SIG_KIND"
    SIG_ARITY             = "SIG_ARITY"
    SORT_MISMATCH         = "SORT"
    UNBOUND_VAR           = "UNBOUND"

@dataclass
class TypeError:
    code: TC
    message: str

@dataclass
class Valid:
    pass

Result = Union[Valid, TypeError]
OK = Valid()

# ---------- Signature triée ----------
# name -> (arg_sorts, kind)
#   kind ∈ {"state", "event_point", "event_durative"}
SIGNATURE: dict[str, tuple[tuple[Sort, ...], str]] = {
    "Peur":            ((Sort.A,),               "state"),
    "Confiance":       ((Sort.A, Sort.A, Sort.C), "state"),
    "Respect":         ((Sort.A, Sort.A),         "state"),
    "Dependance":      ((Sort.A, Sort.A, Sort.F), "state"),
    "ManqueDeRespect": ((Sort.A, Sort.A),         "event_durative"),
    "Promesse":        ((Sort.A, Sort.A, Sort.C), "event_point"),
    "Action":          ((Sort.A, Sort.C),         "event_durative"),
}

# ---------- Extracteurs structurels ----------
def ctx_of(φ: Formula) -> set[Const]:
    match φ:
        case StatePred(_, _, _, k, _):  return {k}
        case EventPred(_, _, k, _):     return {k}
        case Prob(_, k, _):             return {k}
        case Not(b) | Box(_, b) | Diamond(_, b) \
           | Exists(_, _, b) | Forall(_, _, b):
            return ctx_of(b)
        case And(l, r) | Or(l, r) | Implies(l, r) | Mais(l, r) | Tension(l, r, _):
            return ctx_of(l) | ctx_of(r)
    raise AssertionError(f"ctx_of: noeud inconnu {φ!r}")

def time_of(φ: Formula) -> set[Const]:
    match φ:
        case StatePred(_, _, _, _, t):  return {t}
        case EventPred(_, _, _, times): return {times[0]}          # ancre = début
        case Prob(b, _, _):             return time_of(b)
        case Not(b) | Box(_, b) | Diamond(_, b) \
           | Exists(_, _, b) | Forall(_, _, b):
            return time_of(b)
        case And(l, r) | Or(l, r) | Implies(l, r) | Mais(l, r):
            return time_of(l) | time_of(r)
        case Tension(l, r, t):
            return time_of(l) | time_of(r) | {t}
    raise AssertionError(f"time_of: noeud inconnu {φ!r}")

def agent_of(φ: Formula) -> set[Term]:
    """Convention : args[0] = sujet/agent."""
    match φ:
        case StatePred(_, args, _, _, _) | EventPred(_, args, _, _):
            return {args[0]} if args else set()
        case Prob(b, _, _):  return agent_of(b)
        case Not(b) | Box(_, b) | Diamond(_, b) \
           | Exists(_, _, b) | Forall(_, _, b):
            return agent_of(b)
        case And(l, r) | Or(l, r) | Implies(l, r) | Mais(l, r) | Tension(l, r, _):
            return agent_of(l) | agent_of(r)
    raise AssertionError(f"agent_of: noeud inconnu {φ!r}")

def free_vars(φ: Formula, bound: frozenset[str] = frozenset()) -> set[str]:
    match φ:
        case StatePred(_, args, _, _, _) | EventPred(_, args, _, _):
            return {a.name for a in args if isinstance(a, Var) and a.name not in bound}
        case Not(b) | Box(_, b) | Diamond(_, b) | Prob(b, _, _):
            return free_vars(b, bound)
        case Exists(_, x, b) | Forall(_, x, b):
            return free_vars(b, bound | {x})
        case And(l, r) | Or(l, r) | Implies(l, r) | Mais(l, r):
            return free_vars(l, bound) | free_vars(r, bound)
        case Tension(l, r, _):
            return free_vars(l, bound) | free_vars(r, bound)
    raise AssertionError(f"free_vars: noeud inconnu {φ!r}")

# ---------- Vérification de sortes ----------
def _sort_ok(t: Term, expected: Sort, env: dict[str, Sort]) -> Result:
    if isinstance(t, Const):
        return OK if t.sort == expected else TypeError(
            TC.SORT_MISMATCH, f"{t.name}: attendu {expected}, reçu {t.sort}")
    # Var
    if t.name not in env:
        return TypeError(TC.UNBOUND_VAR, f"variable libre {t.name}")
    if env[t.name] != expected:
        return TypeError(TC.SORT_MISMATCH,
                         f"{t.name}: attendu {expected}, lié à {env[t.name]}")
    return OK

def _seq(*rs: Result) -> Result:
    for r in rs:
        if isinstance(r, TypeError):
            return r
    return OK

# ---------- Type-checker ----------
def type_check(φ: Formula, env: dict[str, Sort] | None = None) -> Result:
    if env is None:
        env = {}

    match φ:
        # ---- T1 / T2 / signature ----
        case StatePred(name, args, i, k, t):
            if name not in SIGNATURE:
                return TypeError(TC.SIG_UNKNOWN, f"prédicat inconnu {name}")
            sig, kind = SIGNATURE[name]
            if kind != "state":
                return TypeError(TC.SIG_KIND,
                                 f"{name} est un événement, pas un état")
            if len(args) != len(sig):
                return TypeError(TC.SIG_ARITY,
                                 f"{name}: arité {len(args)} ≠ {len(sig)}")
            if not isinstance(i, Intensity):
                return TypeError(TC.T1_INTENSITY_ON_EVENT,
                                 f"intensité invalide sur {name}")
            if k.sort != Sort.K:
                return TypeError(TC.T7_UNCONTEXTUALIZED,
                                 f"ctx de {name} n'est pas de sorte K")
            if t.sort != Sort.T:
                return TypeError(TC.SORT_MISMATCH,
                                 f"temps de {name} n'est pas de sorte T")
            for a, s in zip(args, sig):
                r = _sort_ok(a, s, env)
                if isinstance(r, TypeError):
                    return r
            return OK

        case EventPred(name, args, k, times):
            if name not in SIGNATURE:
                return TypeError(TC.SIG_UNKNOWN, f"prédicat inconnu {name}")
            sig, kind = SIGNATURE[name]
            if kind == "state":
                return TypeError(TC.SIG_KIND,
                                 f"{name} est un état, pas un événement")
            if len(args) != len(sig):
                return TypeError(TC.SIG_ARITY,
                                 f"{name}: arité {len(args)} ≠ {len(sig)}")
            expected_n = 2 if kind == "event_durative" else 1
            if len(times) != expected_n:
                return TypeError(TC.T2_EVENT_ARITY,
                                 f"{name}: {expected_n} param(s) temporel(s) attendu(s), "
                                 f"reçu {len(times)}")
            if k.sort != Sort.K:
                return TypeError(TC.T7_UNCONTEXTUALIZED,
                                 f"ctx de {name} n'est pas de sorte K")
            for tt in times:
                if tt.sort != Sort.T:
                    return TypeError(TC.SORT_MISMATCH,
                                     f"temps de {name} n'est pas de sorte T")
            for a, s in zip(args, sig):
                r = _sort_ok(a, s, env)
                if isinstance(r, TypeError):
                    return r
            return OK

        # ---- Structurel ----
        case Not(b):
            return type_check(b, env)

        case And(l, r) | Or(l, r) | Implies(l, r):
            return _seq(type_check(l, env), type_check(r, env))

        # ---- T3 : Mais ----
        case Mais(l, r):
            rt = _seq(type_check(l, env), type_check(r, env))
            if isinstance(rt, TypeError):
                return rt
            kl, kr = ctx_of(l), ctx_of(r)
            if len(kl) != 1 or len(kr) != 1 or kl != kr:
                return TypeError(TC.T3_MAIS_SCOPE,
                                 f"Mais: contextes incompatibles {kl} vs {kr}")
            tl, tr = time_of(l), time_of(r)
            if len(tl) != 1 or len(tr) != 1 or tl != tr:
                return TypeError(TC.T3_MAIS_SCOPE,
                                 f"Mais: temps incompatibles {tl} vs {tr}")
            return OK

        # ---- T4 : modalité ----
        case Box(m, b) | Diamond(m, b):
            if not isinstance(m, Modal):
                return TypeError(TC.T4_MODAL_FLOATING,
                                 f"modalité invalide {m!r}")
            return type_check(b, env)

        # ---- Quantificateurs ----
        case Exists(s, x, b) | Forall(s, x, b):
            if not isinstance(s, Sort):
                return TypeError(TC.SORT_MISMATCH, f"sorte invalide {s!r}")
            return type_check(b, {**env, x: s})

        # ---- T5 : Prob ----
        case Prob(b, k, p):
            if not (0.0 <= p <= 1.0):
                return TypeError(TC.T5_PROB_NOT_CLOSED,
                                 f"p={p} hors de [0,1]")
            fv = free_vars(b, frozenset(env.keys()))
            if fv:
                return TypeError(TC.T5_PROB_NOT_CLOSED,
                                 f"variables libres dans Prob : {fv}")
            bk = ctx_of(b)
            if len(bk) != 1 or bk != {k}:
                return TypeError(TC.T5_PROB_NOT_CLOSED,
                                 f"corps de Prob doit être contextualisé par {k}, "
                                 f"reçu {bk}")
            return type_check(b, env)

        # ---- T6 : Tension ----
        case Tension(l, r, t):
            rt = _seq(type_check(l, env), type_check(r, env))
            if isinstance(rt, TypeError):
                return rt
            al, ar = agent_of(l), agent_of(r)
            if len(al) != 1 or len(ar) != 1 or al != ar:
                return TypeError(TC.T6_TENSION_MISMATCH,
                                 f"Tension: agents incompatibles {al} vs {ar}")
            tl, tr = time_of(l), time_of(r)
            if len(tl) != 1 or len(tr) != 1 or tl != tr or tl != {t}:
                return TypeError(TC.T6_TENSION_MISMATCH,
                                 f"Tension: temps incompatibles {tl}, {tr}, {t}")
            return OK

    raise AssertionError(f"type_check: noeud inconnu {φ!r}")


# ==============================================================================
# BANC DE TEST INTÉGRÉ
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("⚜️ HARNAIS DE TEST LMH v2.0 — VALIDATION FORMELLE (T1–T7)")
    print("=" * 70)

    # Abréviations
    je = Const("je", Sort.A)
    tu = Const("tu", Sort.A)
    a  = Const("a", Sort.A)
    b  = Const("b", Sort.A)
    D  = Const("D", Sort.C)
    α  = Const("α", Sort.C)
    F  = Const("F", Sort.F)
    k  = Const("k", Sort.K)
    t  = Const("t", Sort.T)

    # ----- F1 : Peur + Confiance + Tension (avec intensité neutre) -----
    peur = StatePred("Peur", (je,), Intensity.NEUTRE, k, t)
    conf = StatePred("Confiance", (je, tu, D), Intensity.NEUTRE, k, t)
    F1 = Exists(Sort.T, "t", And(And(peur, conf), Tension(peur, conf, t)))

    # ----- F2 : Promesse incertaine -----
    prom = EventPred("Promesse", (a, b, α), k, (t,))
    F2 = Prob(prom, k, 0.7)

    # ----- F3 : Manque de respect + Dépendance sous contrainte -----
    non_resp = Not(StatePred("Respect", (b, a), Intensity.NEUTRE, k, t))
    dep_ctr = Box(Modal.CONTRAINTE,
                  StatePred("Dependance", (a, b, F), Intensity.NEUTRE, k, t))
    F3 = And(non_resp, dep_ctr)

    # ----- F3 enrichie (avec Mais licite) -----
    F3_bis = Mais(non_resp, dep_ctr)

    print("\n--- [1] FORMULES VALIDES ---")
    for name, f in [("F1", F1), ("F2", F2), ("F3", F3), ("F3_bis", F3_bis)]:
        res = type_check(f)
        print(f"{name:8} → {res}")
        assert isinstance(res, Valid), f"Échec inattendu sur {name}"

    print("\n--- [2] TESTS DE NON-RÉGRESSION (REJETS ATTENDUS) ---")
    # B1 : intensité sur un événement
    bad1_state = StatePred("ManqueDeRespect", (b, a), Intensity.FORTE, k, t)
    r_b1 = type_check(bad1_state)
    print(f"B1 (mismatch state/event) → {r_b1}")
    assert isinstance(r_b1, TypeError) and r_b1.code == TC.SIG_KIND

    # B2 : Mais franchissant deux contextes
    k2 = Const("k2", Sort.K)
    bad2 = Mais(StatePred("Peur", (je,), Intensity.NEUTRE, k, t),
                StatePred("Peur", (je,), Intensity.NEUTRE, k2, t))
    r_b2 = type_check(bad2)
    print(f"B2 (scope k1 != k2)       → {r_b2}")
    assert isinstance(r_b2, TypeError) and r_b2.code == TC.T3_MAIS_SCOPE

    # B5 : Prob sur formule ouverte
    bad5 = Prob(StatePred("Peur", (Var("x", Sort.A),), Intensity.NEUTRE, k, t), k, 0.5)
    r_b5 = type_check(bad5)
    print(f"B5 (variable libre)       → {r_b5}")
    assert isinstance(r_b5, TypeError) and r_b5.code == TC.T5_PROB_NOT_CLOSED

    # B6 : Tension entre deux agents différents
    conf_autre = StatePred("Confiance", (tu, je, D), Intensity.NEUTRE, k, t)
    bad6 = Tension(peur, conf_autre, t)
    r_b6 = type_check(bad6)
    print(f"B6 (agents incompatibles) → {r_b6}")
    assert isinstance(r_b6, TypeError) and r_b6.code == TC.T6_TENSION_MISMATCH

    # B7 : atome sans contexte (k typé T au lieu de K)
    k_bad = Const("k", Sort.T)
    bad7 = StatePred("Peur", (je,), Intensity.NEUTRE, k_bad, t)
    r_b7 = type_check(bad7)
    print(f"B7 (ctx non de sorte K)   → {r_b7}")
    assert isinstance(r_b7, TypeError) and r_b7.code == TC.T7_UNCONTEXTUALIZED

    print("\n✅ TOUS LES TESTS T1–T7 ONT RÉUSSI AVEC SUCCÈS SUR LE FER !")
    print("=" * 70)
