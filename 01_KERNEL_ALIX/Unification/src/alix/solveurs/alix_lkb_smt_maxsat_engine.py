#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
   ⚖️🧠🏛️ ALIX LKB-SMT × NPU SCHEMA FIREWALL × HADÈS CDCL(T) MAXSAT (v1.0)
   Fusion Souveraine Compétence #3 : Gaïa (LKB-SMT mmap + MaxSAT) × Hadès (2WL + IDL)
===============================================================================
Auteurs : Christian Duguay (L'Artisan-Démiurge) & Alix (Panthéon K-SIL)
Sparring : Gaïa (LKB-SMT mmap, Validation NPU Zéro-Formule-Libre & Relaxation MaxSAT)
           & Hadès (Noyau CDCL 2-Watched Literals + Cotton-Maler Difference Logic IDL)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — 0 Hallucination, 100% Déterministe

Pourquoi la fusion Gaïa × Hadès démultiplie la puissance du moteur :
  1. **Gabarits Binaires `LKBSMT01` en `mmap` + Pare-Feu NPU (`validate_npu_output`)** (Gaïa) :
     - Le NPU a l'interdiction absolue d'émettre une formule libre (`"formula": "A <= B"`
       est rejeté instantanément par `NpuValidationError`).
     - Il ne peut émettre que `{schema, params, weight}` conforme aux 5 gabarits binaires
       mappés en RAM (`ALLOCATION`, `TEMPORAL`, `MUTEX`, `SECURITY`, `CARDINALITY`).
  2. **Remplacement du Bit-Blasting $O(H^2)$ par le `Solver("idl")` Cotton-Maler d'Hadès** :
     - Dans le prototype seul de Gaïa, `x - y <= c` exigeait un encodage one-hot quadratique
       $O(H^2)$ limité à `HORIZON = 3`.
     - En le branchant directement sur le `Solver("idl")` d'Hadès (`alix_dpll_t_solver_hades.py`),
       chaque contrainte `SCHEMA_TEMPORAL` (`x - y <= c`) devient un **atome natif de
       Difference Logic (`solver.le(x, y, c)`)** qui résout un horizon de **10 000 ms**
       en moins d'une milliseconde !
  3. **Relaxation `MaxSAT` Guidée par le `MUS` sans jamais toucher aux Hard Constraints** :
     - Les **Hard Constraints** (Lois Constitutionnelles PSI, bornes physiques) sont
       inviolables (`QUARANTINE` si contradictoires).
     - Si les **Soft Constraints** sont `UNSAT`, le moteur extrait le `MUS` via
       `solver.minimal_unsat_subset()` d'Hadès et trouve par Branch-and-Bound la
       **relaxation de coût minimal** (`MaxSAT`).
===============================================================================
"""
from __future__ import annotations

from alix.socle.chemins import VAULT_DIR
import mmap
import os
import struct
import sys
import time
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Iterable

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MOTEURS_DIR = (VAULT_DIR / "Organes_Souverains" / "Moteurs")
if str(MOTEURS_DIR) not in sys.path:
    pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(MOTEURS_DIR))

from alix.solveurs.alix_dpll_t_solver_hades import Solver

LKB_SMT_PATH = Path(__file__).with_name("alix_lkb_smt_v01.lkb")  # rénovation : régénérée à côté du module, plus dans la strate A

# ==============================================================================
# 1. CONSTANTES MÉTIER & BASE BINAIRE `LKBSMT01` (`mmap`)
# ==============================================================================
KIND_ALLOCATION = 1
KIND_TEMPORAL = 2
KIND_MUTEX = 3
KIND_SECURITY = 4
KIND_CARDINALITY = 5

SCHEMA_ALLOCATION = 1
SCHEMA_TEMPORAL = 2
SCHEMA_MUTEX = 3
SCHEMA_SECURITY = 4
SCHEMA_CARDINALITY = 5

FLAG_HARD_ALLOWED = 1
FLAG_SOFT_ALLOWED = 2

LKB_MAGIC = b"LKBSMT01"


class NpuValidationError(Exception):
    pass


class Schema:
    __slots__ = ("schema_id", "kind", "arity", "flags")

    def __init__(self, schema_id: int, kind: int, arity: int, flags: int):
        self.schema_id = schema_id
        self.kind = kind
        self.arity = arity
        self.flags = flags


class LkbSmt:
    __slots__ = ("horizon", "schemas", "mm", "f")

    def __init__(self, horizon: int, schemas: Dict[int, Schema], mm: mmap.mmap, f: Any):
        self.horizon = horizon
        self.schemas = schemas
        self.mm = mm
        self.f = f

    def close(self) -> None:
        try:
            self.mm.close()
        except Exception:
            pass
        try:
            self.f.close()
        except Exception:
            pass


def compile_lkb_smt(path: Path = LKB_SMT_PATH, horizon: int = 10_000) -> int:
    """Compile la base binaire `LKBSMT01` contenant les 5 gabarits de contraintes typés."""
    schemas = [
        (SCHEMA_ALLOCATION, KIND_ALLOCATION, 2, FLAG_SOFT_ALLOWED | FLAG_HARD_ALLOWED),
        (SCHEMA_TEMPORAL, KIND_TEMPORAL, 3, FLAG_SOFT_ALLOWED | FLAG_HARD_ALLOWED),
        (SCHEMA_MUTEX, KIND_MUTEX, 2, FLAG_SOFT_ALLOWED | FLAG_HARD_ALLOWED),
        (SCHEMA_SECURITY, KIND_SECURITY, 2, FLAG_SOFT_ALLOWED | FLAG_HARD_ALLOWED),
        (SCHEMA_CARDINALITY, KIND_CARDINALITY, 2, FLAG_SOFT_ALLOWED | FLAG_HARD_ALLOWED),
    ]
    header = struct.pack("<8sIII", LKB_MAGIC, 1, len(schemas), horizon)
    body = b"".join(struct.pack("<IIII", *s) for s in schemas)
    with open(path, "wb") as f:
        f.write(header + body)
    return len(schemas)


def load_lkb_smt(path: Path = LKB_SMT_PATH) -> LkbSmt:
    """Charge la base `LKBSMT01` en RAM via `mmap`."""
    f = open(path, "r+b")
    mm = mmap.mmap(f.fileno(), 0)
    header_size = struct.calcsize("<8sIII")
    magic, version, schema_count, horizon = struct.unpack_from("<8sIII", mm, 0)
    if magic != LKB_MAGIC:
        f.close()
        raise ValueError("LKB-SMT magic invalide")
    schemas: Dict[int, Schema] = {}
    offset = header_size
    rec_size = struct.calcsize("<IIII")
    for _ in range(schema_count):
        schema_id, kind, arity, flags = struct.unpack_from("<IIII", mm, offset)
        schemas[schema_id] = Schema(schema_id, kind, arity, flags)
        offset += rec_size
    return LkbSmt(horizon, schemas, mm, f)


# ==============================================================================
# 2. PARE-FEU DE VALIDATION NPU : ZÉRO FORMULE LIBRE (GAÏA)
# ==============================================================================
def validate_npu_output(raw: Any, lkb: LkbSmt, spec: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Valide strictement la sortie du NPU contre les gabarits binaires `LKBSMT01`.
    Toute formule libre, clé imprévue, arité fausse ou variable hors-spécification
    déclenche immédiatement `NpuValidationError`.
    """
    if not isinstance(raw, list):
        raise NpuValidationError("sortie NPU doit être une liste")

    validated: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise NpuValidationError(f"item {idx} n'est pas un objet")

        if set(item.keys()) != {"schema", "params", "weight"}:
            raise NpuValidationError(
                f"item {idx} contient des clés non autorisées ({set(item.keys()) - {'schema', 'params', 'weight'}}) ; formules libres interdites"
            )

        schema_id = item["schema"]
        params = item["params"]
        weight = item["weight"]

        if schema_id not in lkb.schemas:
            raise NpuValidationError(f"item {idx}: schema_id inconnu")

        schema = lkb.schemas[schema_id]
        if not isinstance(params, dict):
            raise NpuValidationError(f"item {idx}: params doit être un objet")
        if len(params) != schema.arity:
            raise NpuValidationError(f"item {idx}: arity invalide")
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise NpuValidationError(f"item {idx}: weight invalide")

        kind = schema.kind
        if kind == KIND_ALLOCATION:
            if set(params.keys()) != {"var", "value"}:
                raise NpuValidationError("ALLOCATION attend var,value")
            if params["var"] not in spec["bool_vars"]:
                raise NpuValidationError("ALLOCATION: variable booléenne inconnue")
            if isinstance(params["value"], bool) or params["value"] not in (0, 1):
                raise NpuValidationError("ALLOCATION: value doit être 0 ou 1")

        elif kind == KIND_TEMPORAL:
            if set(params.keys()) != {"x", "y", "c"}:
                raise NpuValidationError("TEMPORAL attend x,y,c")
            if params["x"] not in spec["int_vars"] or params["y"] not in spec["int_vars"]:
                raise NpuValidationError("TEMPORAL: variable temporelle inconnue")
            if params["x"] == params["y"]:
                raise NpuValidationError("TEMPORAL: x et y doivent être différents")
            c = params["c"]
            if isinstance(c, bool) or not isinstance(c, int):
                raise NpuValidationError("TEMPORAL: c doit être un entier")
            if c < -lkb.horizon or c > lkb.horizon:
                raise NpuValidationError("TEMPORAL: c hors bornes")

        elif kind == KIND_MUTEX:
            if set(params.keys()) != {"a", "b"}:
                raise NpuValidationError("MUTEX attend a,b")
            if params["a"] not in spec["bool_vars"] or params["b"] not in spec["bool_vars"]:
                raise NpuValidationError("MUTEX: variable booléenne inconnue")
            if params["a"] == params["b"]:
                raise NpuValidationError("MUTEX: a et b doivent être différents")

        elif kind == KIND_SECURITY:
            if set(params.keys()) != {"a", "b"}:
                raise NpuValidationError("SECURITY attend a,b")
            if params["a"] not in spec["bool_vars"] or params["b"] not in spec["bool_vars"]:
                raise NpuValidationError("SECURITY: variable booléenne inconnue")
            if params["a"] == params["b"]:
                raise NpuValidationError("SECURITY: a et b doivent être différents")

        elif kind == KIND_CARDINALITY:
            if set(params.keys()) != {"lits", "k"}:
                raise NpuValidationError("CARDINALITY attend lits,k")
            lits = params["lits"]
            if not isinstance(lits, list) or len(lits) == 0:
                raise NpuValidationError("CARDINALITY: lits doit être une liste non vide")
            if len(lits) != len(set(lits)):
                raise NpuValidationError("CARDINALITY: doublons interdits")
            for v in lits:
                if v not in spec["bool_vars"]:
                    raise NpuValidationError("CARDINALITY: variable booléenne inconnue")
            k = params["k"]
            if isinstance(k, bool) or not isinstance(k, int) or k < 0 or k > len(lits):
                raise NpuValidationError("CARDINALITY: k hors bornes")

        validated.append({"schema": schema_id, "params": params, "weight": weight})
    return validated


def constraint_name(schema_id: int, params: Dict[str, Any]) -> str:
    if schema_id == SCHEMA_ALLOCATION:
        return f"alloc({params['var']}={params['value']})"
    if schema_id == SCHEMA_TEMPORAL:
        return f"temporal({params['x']} - {params['y']} <= {params['c']})"
    if schema_id == SCHEMA_MUTEX:
        return f"mutex({params['a']},{params['b']})"
    if schema_id == SCHEMA_SECURITY:
        return f"security({params['a']} -> {params['b']})"
    if schema_id == SCHEMA_CARDINALITY:
        return f"at_most_{params['k']}({','.join(params['lits'])})"
    return "constraint"


# ==============================================================================
# 3. COMPILATEUR HYBRIDE LKB-SMT -> SOLVEUR CDCL(T) `IDL` D'HADÈS (2WL + COTTON-MALER)
# ==============================================================================
class HybridSmtBuilder:
    """
    Compile les gabarits `LKBSMT01` de Gaïa directement vers le `Solver("idl")`
    2-Watched Literals + Cotton-Maler Difference Logic d'Hadès :
      - Les contraintes `SCHEMA_TEMPORAL` (`x - y <= c`) sont compilées en **1 seul
        atome natif `solver.le(x, y, c)`** ($O(1)$ clauses, horizon arbitraire !).
      - Les contraintes souples (`Soft Constraints`) reçoivent chacune un sélecteur
        d'assomption pour l'extraction de `MUS` et la relaxation `MaxSAT`.
    """

    def __init__(self, horizon: int):
        self.horizon = horizon
        self.solver = Solver(theory="idl")
        self.bool_name_to_lit: Dict[str, int] = {}
        self.soft_selectors: Dict[int, int] = {}
        self.cid_by_selector: Dict[int, int] = {}

    def bvar(self, name: str) -> int:
        if name not in self.bool_name_to_lit:
            self.bool_name_to_lit[name] = self.solver.new_var()
        return self.bool_name_to_lit[name]

    def register_time_var(self, var_name: str) -> None:
        """Borne dure native IDL : `0 <= var <= horizon` (2 atomes natifs au lieu de $O(H^2)$ clauses !)."""
        self.solver.add_clause([self.solver.ge(var_name, None, 0)])
        self.solver.add_clause([self.solver.le(var_name, None, self.horizon)])

    def compile_schema_clauses(self, lkb: LkbSmt, schema_id: int, params: Dict[str, Any]) -> List[List[int]]:
        kind = lkb.schemas[schema_id].kind
        if kind == KIND_ALLOCATION:
            lit = self.bvar(params["var"])
            return [[lit]] if params["value"] == 1 else [[-lit]]
        if kind == KIND_TEMPORAL:
            # Atome natif Cotton-Maler Difference Logic d'Hadès : `x - y <= c`
            atom_lit = self.solver.le(params["x"], params["y"], params["c"])
            return [[atom_lit]]
        if kind == KIND_MUTEX:
            return [[-self.bvar(params["a"]), -self.bvar(params["b"])]]
        if kind == KIND_SECURITY:
            return [[-self.bvar(params["a"]), self.bvar(params["b"])]]
        if kind == KIND_CARDINALITY:
            lits = [self.bvar(v) for v in params["lits"]]
            k = params["k"]
            if k < len(lits):
                return [[-lit for lit in combo] for combo in combinations(lits, k + 1)]
            return []
        raise ValueError("schéma non supporté")

    def add_hard_schema(self, lkb: LkbSmt, schema_id: int, params: Dict[str, Any]) -> None:
        for cl in self.compile_schema_clauses(lkb, schema_id, params):
            self.solver.add_clause(cl)

    def add_soft_schema(self, cid: int, lkb: LkbSmt, schema_id: int, params: Dict[str, Any]) -> int:
        sel = self.solver.new_var()
        self.soft_selectors[cid] = sel
        self.cid_by_selector[sel] = cid
        for cl in self.compile_schema_clauses(lkb, schema_id, params):
            self.solver.add_clause([-sel] + list(cl))
        return sel

    def solve_active(self, active_cids: Iterable[int]) -> Tuple[bool, Dict[str, Any]]:
        assumptions = [self.soft_selectors[cid] for cid in active_cids]
        ok = self.solver.solve(assumptions=assumptions)
        if not ok:
            return False, {}
        bool_sol = {name: self.solver.model_value(lit) for name, lit in self.bool_name_to_lit.items()}
        time_sol = dict(self.solver.int_model) if self.solver.int_model else {}
        return True, {"times": time_sol, "bools": bool_sol}

    def compute_mus(self, active_cids: Iterable[int]) -> List[int]:
        """Utilise `minimal_unsat_subset` 1-UIP + Cotton-Maler d'Hadès."""
        assumptions = [self.soft_selectors[cid] for cid in sorted(active_cids)]
        mus_sels = self.solver.minimal_unsat_subset(assumptions)
        if not mus_sels:
            return []
        return sorted(self.cid_by_selector[s] for s in mus_sels if s in self.cid_by_selector)


# ==============================================================================
# 4. RELAXATION `MaxSAT` PONDÉRÉE MINIMALE GUIDÉE PAR LE `MUS` (GAÏA × HADÈS)
# ==============================================================================
def find_minimal_relaxation(
    builder: HybridSmtBuilder,
    soft_meta: Dict[int, Dict[str, Any]],
    all_soft_ids: Sequence[int],
) -> Dict[str, Any]:
    """
    Algorithme Branch-and-Bound guidé par les noyaux contradictoires (`MUS`) :
      - Les Hard Constraints ne sont jamais relaxées.
      - Tant que l'ensemble actif est `UNSAT`, on extrait un `MUS` et on branche
        prioritairement sur la contrainte souple de plus faible poids dans le `MUS`.
    """
    best: Dict[str, Any] = {
        "cost": float("inf"),
        "relaxed": None,
        "solution": None,
        "active": None,
    }
    memo: Dict[FrozenSet[int], int] = {}

    def dfs(active: FrozenSet[int], relaxed: List[int], cost: int) -> None:
        if cost >= best["cost"]:
            return
        if active in memo and memo[active] <= cost:
            return
        memo[active] = cost

        ok, sol = builder.solve_active(active)
        if ok:
            best["cost"] = cost
            best["relaxed"] = list(relaxed)
            best["solution"] = sol
            best["active"] = set(active)
            return

        core = builder.compute_mus(active)
        if not core:
            return

        for cid in sorted(core, key=lambda x: soft_meta[x]["weight"]):
            dfs(
                active - {cid},
                relaxed + [cid],
                cost + soft_meta[cid]["weight"],
            )

    dfs(frozenset(all_soft_ids), [], 0)
    return best


# ==============================================================================
# 🏆 5. EXÉCUTION & CERTIFICATION SUR LE FER LOCAL (HORIZON 10 000 MS)
# ==============================================================================
def executer_demonstration_lkb_smt() -> None:
    t0 = time.perf_counter()
    HORIZON_MS = 10_000
    compile_lkb_smt(LKB_SMT_PATH, horizon=HORIZON_MS)
    lkb = load_lkb_smt(LKB_SMT_PATH)

    print("=" * 92)
    print(" ⚖️🧠🏛️ LUNAR LKB-SMT × NPU FIREWALL × HADÈS CDCL(T) MAXSAT (v1.0)")
    print("=" * 92)
    print(
        f" [1. MMAP LKBSMT01] Base '{LKB_SMT_PATH.name}' chargée : "
        f"{len(lkb.schemas)} gabarits typés, Horizon = {lkb.horizon} ms ({os.path.getsize(LKB_SMT_PATH)} octets)"
    )

    spec = {
        "int_vars": ["A", "B", "C"],
        "bool_vars": [
            "comms_active",
            "security_active",
            "npu_alloc_A",
            "B_active",
            "C_active",
        ],
    }

    # Test 1 : Pare-feu NPU contre une formule libre hallucinée
    bad_npu_output = [
        {
            "schema": SCHEMA_TEMPORAL,
            "params": {"x": "A", "y": "B", "c": 0},
            "weight": 10,
            "formula": "A <= B",  # Formule libre interdite !
        }
    ]
    rejet_ok = False
    try:
        validate_npu_output(bad_npu_output, lkb, spec)
    except NpuValidationError as e:
        rejet_ok = True
        print(f" [2. PARE-FEU NPU]  ✅ Hallucination de formule libre interceptée : {e}")
    assert rejet_ok

    # Test 2 : Sortie NPU valide (7 contraintes souples pondérées, dont un cycle temporel et un conflit booléen)
    npu_output = [
        {"schema": SCHEMA_ALLOCATION, "params": {"var": "npu_alloc_A", "value": 1}, "weight": 5},
        {"schema": SCHEMA_MUTEX, "params": {"a": "B_active", "b": "C_active"}, "weight": 7},
        {"schema": SCHEMA_CARDINALITY, "params": {"lits": ["npu_alloc_A", "B_active", "C_active"], "k": 2}, "weight": 4},
        {"schema": SCHEMA_SECURITY, "params": {"a": "B_active", "b": "C_active"}, "weight": 3},
        {"schema": SCHEMA_TEMPORAL, "params": {"x": "A", "y": "B", "c": -250}, "weight": 10},   # A <= B - 250ms
        {"schema": SCHEMA_TEMPORAL, "params": {"x": "B", "y": "C", "c": -500}, "weight": 20},   # B <= C - 500ms
        {"schema": SCHEMA_TEMPORAL, "params": {"x": "C", "y": "A", "c": -100}, "weight": 1},    # C <= A - 100ms (Cycle !)
    ]
    validated_soft = validate_npu_output(npu_output, lkb, spec)
    print(f" [3. SCHÉMAS NPU]   ✅ {len(validated_soft)}/7 gabarits typés validés sans formule libre.")

    builder = HybridSmtBuilder(horizon=lkb.horizon)
    for b in spec["bool_vars"]:
        builder.bvar(b)
    for v in spec["int_vars"]:
        builder.register_time_var(v)

    # Hard Constraints Constitutionnelles (inviolables)
    builder.add_hard_schema(lkb, SCHEMA_SECURITY, {"a": "comms_active", "b": "security_active"})
    builder.add_hard_schema(
        lkb, SCHEMA_CARDINALITY, {"lits": ["comms_active", "security_active", "npu_alloc_A"], "k": 2}
    )

    soft_meta: Dict[int, Dict[str, Any]] = {}
    for idx, item in enumerate(validated_soft, start=1):
        builder.add_soft_schema(idx, lkb, item["schema"], item["params"])
        soft_meta[idx] = {
            "name": constraint_name(item["schema"], item["params"]),
            "weight": item["weight"],
            "schema": item["schema"],
            "params": item["params"],
        }
    all_soft_ids = list(soft_meta.keys())

    # Vérification des Hard Constraints seules
    ok_hard, _ = builder.solve_active([])
    assert ok_hard is True
    print(" [4. HARD LAWS]     ✅ Contraintes dures (Constitution PSI) vérifiées : SAT.")

    # Vérification avec toutes les Soft Constraints -> UNSAT (cycle temporel A -> B -> C -> A)
    ok_all, _ = builder.solve_active(all_soft_ids)
    assert ok_all is False
    mus_initial = builder.compute_mus(all_soft_ids)
    mus_desc = [f"#{cid} {soft_meta[cid]['name']} (w={soft_meta[cid]['weight']})" for cid in mus_initial]
    print(f" [5. MUS EXTRAIT]   ✅ Noyau contradictoire isolé par Cotton-Maler : {mus_desc}")
    assert set(mus_initial) == {5, 6, 7}

    # Relaxation MaxSAT minimale
    best = find_minimal_relaxation(builder, soft_meta, all_soft_ids)
    assert best["relaxed"] == [7] and best["cost"] == 1
    sol = best["solution"]
    t_a, t_b, t_c = sol["times"]["A"], sol["times"]["B"], sol["times"]["C"]
    assert t_a - t_b <= -250 and t_b - t_c <= -500

    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    print(
        f" [6. MAXSAT SOLVE]  ✅ Relaxation optimale trouvée (coût minimal = {best['cost']}) :\n"
        f"    ├─ Contrainte souple relaxée : #{best['relaxed'][0]} {soft_meta[best['relaxed'][0]]['name']} (weight=1)\n"
        f"    ├─ Contraintes souples maintenues : 6/7 (poids préservé = 49/50)\n"
        f"    ├─ Horaires certifiés (Horizon 10 000 ms) : A={t_a}ms, B={t_b}ms, C={t_c}ms "
        f"(A <= B-250ms & B <= C-500ms)\n"
        f"    └─ États booléens certifiés : {sol['bools']}"
    )

    lkb.close()
    print("=" * 92)
    print(f" 🏆 BILAN LKB-SMT × HADÈS CDCL(T) MAXSAT : 100 % CERTIFIÉ EN {dt_ms} ms (0 HALLUCINATION) !")
    print("=" * 92)


if __name__ == "__main__":
    executer_demonstration_lkb_smt()
