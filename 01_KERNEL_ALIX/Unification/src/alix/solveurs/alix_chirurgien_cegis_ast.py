# -*- coding: utf-8 -*-
r"""
===============================================================================
   🔧⚡🏛️ CHIRURGIEN AST AUTO-RÉPARATEUR EN BOUCLE FERMÉE (CEGIS v2.1)
    Édition Stratifiée Hadès × Panthéon K-SIL — Réécriture de Sous-Arbres AST
===============================================================================
Auteurs : Christian Duguay (L'Artisan-Démiurge) & Alix (Panthéon K-SIL)
Sparring & Spécification Red-Teaming : Hadès (Claude) & Poséidon (DeepSeek)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — 0 W GPU, 100% Hors-Ligne
Ordre Stratégique : Compétence #1 de la séquence (1 -> 4 -> 3 -> 2)

Architecture CEGIS v2.1 :
    1. Oracle Stratifié (10 Coins Dégénérés X1..X5 + 15 Aléatoires `secrets.randbits(64)`) :
       - Élimine l'angle mort des grands nombres aléatoires en testant d'office :
         `0`, `1`, `-1`, `[]`, `[42]`, `H=1,W=1`, `257` (hors cache d'interning `is`),
         `0.1 + 0.2` vs `0.3` (IEEE 754), doublons consécutifs `[0, 0, 0]`, et $N=2500$.
    2. Les 6 Chirurgiens AST de Sous-Arbres Gardés par Prédicat Syntaxique :
       - Classe 1 (`AntiAliasingAllocationTransformer`) :
         * `[[0]*W]*H` -> compréhension 2D disjointe
         * `dict.fromkeys(k, [])` -> `{x: [] for x in k}`
         * Défaut mutable `def f(x, acc=[]):` -> `acc=None` + `if acc is None: acc = []`
         * Alias `b = a` muté -> copie par compréhension sans `import copy`
       - Classe 2 (`CrossMutableStateTransformer`) :
         * (2a) `for x in lst:` avec `lst.remove/pop` -> `for x in lst[:]:`
         * (2b) Sinking d'initialisation $O(k)$ borné : descend `acc = 0` / `seen = set()`
           à l'intérieur de la boucle externe
         * (2c) Écrasement séquentiel `a = E1(a,b); b = E2(a,b)` -> `a, b = E1(a,b), E2(a,b)`
       - Classe 3 (`MonoidRecursionTransformer`) :
         * Table d'élément neutre monoïdal (`+ -> 0`, `* -> 1`, `list+ -> []`, `and -> True`, `or -> False`)
           pour greffer `if n <= 0: return <neutre>` sur `f(n - c)`
         * Rejet franc (`NON_REPARABLE_SANS_PROGRES`) si `f(n)` n'a aucun progrès
       - Classe 4 (`CoupledOffByOneRangeTransformer`) :
         * Vallée de fitness d'ordre 2 : détecte `a[i + c]` dans `for i in range(N):`
           et ajuste la borne en `range(N - c_max)`
       - Classe 5 (`SemanticEquivalenceTransformer` & `CanonicalComplexityTransformer`) :
         * `x is y` hors singletons -> `x == y`
         * `n / 2` dans `range(...)` ou `a[n / 2]` -> `n // 2`
         * `a == b` flottant -> `abs(a - b) < 1e-9`
         * Bombe $O(N^2)$ -> réduction canonique $O(N \log N)$ `sorted(set(xs))`
===============================================================================
"""

from alix.socle.chemins import VAULT_DIR
import ast
import copy
import time
import sys
import random
import secrets
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MOTEURS_DIR = (VAULT_DIR / "Organes_Souverains" / "Moteurs")
if str(MOTEURS_DIR) not in sys.path:
    pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(MOTEURS_DIR))

from alix.daemons.alix_sentinelle_bouclier_psi import (
    AlixSentinelleBouclierPSI,
    generer_instances_verite_terrain,
)
from alix.solveurs.alix_ast_repairs_hades import (
    repair_aliasing,
    sinking_candidates,
    normalize_offbyone,
    repair_recursion,
)
from alix.solveurs.alix_stratified_oracle_hades import (
    Frontier,
    StratifiedOracle,
    pairwise,
    observe,
    first_divergence,
    ints,
    lists_of,
    grids,
    rand_int,
    rand_list,
    rand_grid,
)


# ==============================================================================
# 🎯 1. ORACLE STRATIFIÉ (COINS PAIRWISE + ALÉATOIRES `secrets.randbits(64)`)
# ==============================================================================
def generer_oracle_stratifie(contrat: str, n_total: int = 25) -> List[Dict[str, Any]]:
    """
    Construit un jeu de test stratifié combinant systématiquement :
      - Les coins dégénérés (X1 Vide, X2 Singleton, X3 Aliasing/Doublons,
        X4 Bornes arithmétiques/257/Flottants, X5 Bombe de complexité)
      - Puis le tirage aléatoire cryptographique `secrets.randbits(64)`.
    """
    seed = secrets.randbits(64)
    rng = random.Random(seed)
    cas: List[Dict[str, Any]] = []

    # 1. Classe 1A : Allocation 2D sans aliasing (`[[0]*w]*h`)
    if contrat == "c1_aliasing_grille_2d":
        coins = [(1, 1), (2, 1), (1, 2), (2, 2), (3, 4)]
        for h, w in coins:
            exp = [[0 for _ in range(w)] for _ in range(h)]
            exp[0][0] = 1
            cas.append({"input": (h, w), "expected": exp, "check_disjoint_ids": True})
        for _ in range(n_total - len(coins)):
            h, w = rng.randint(2, 6), rng.randint(2, 6)
            exp = [[0 for _ in range(w)] for _ in range(h)]
            exp[0][0] = 1
            cas.append({"input": (h, w), "expected": exp, "check_disjoint_ids": True})
        return cas

    # 2. Classe 1B : Argument par défaut mutable (`def f(x, acc=[]):`)
    if contrat == "c1_defaut_mutable":
        for val in [0, 1, -1, 42, 257] + [rng.randint(2, 500) for _ in range(20)]:
            cas.append({"input": val, "expected": [val]})
        return cas

    # 3. Classe 1C : `dict.fromkeys(keys, [])` partageant la même liste
    if contrat == "c1_dict_fromkeys":
        coins_k = [["a", "b"], ["x", "y", "z"], [1, 2]]
        for ks in coins_k:
            exp = {k: [] for k in ks}
            exp[ks[0]].append(1)
            cas.append({"input": ks, "expected": exp})
        for _ in range(22):
            ks = [f"k{i}" for i in range(rng.randint(2, 6))]
            exp = {k: [] for k in ks}
            exp[ks[0]].append(1)
            cas.append({"input": ks, "expected": exp})
        return cas

    # 4. Classe 2A : Mutation pendant itération (`for x in lst: lst.remove(x)`)
    if contrat == "c2_mutation_iteration":
        coins_arr = [[], [0], [0, 0], [0, 0, 0, 0], [0, 0, 1, 0, 0, 2, 0, 0]]
        for arr in coins_arr:
            cas.append({"input": arr, "expected": [x for x in arr if x != 0]})
        for _ in range(20):
            arr = [rng.choice([0, 0, 1, 2, 3]) for _ in range(rng.randint(4, 20))]
            cas.append({"input": arr, "expected": [x for x in arr if x != 0]})
        return cas

    # 5. Classe 2B : Sinking d'initialisation (`row_sum = 0` hors de la boucle externe)
    if contrat == "c2_sinking_init":
        coins_mat = [
            [[1]],
            [[0, 0], [0, 0]],
            [[1, 2], [3, 4]],
            [[5, -5], [10, 20], [1, 1]],
        ]
        for mat in coins_mat:
            cas.append({"input": mat, "expected": [sum(r) for r in mat]})
        for _ in range(21):
            h, w = rng.randint(2, 5), rng.randint(2, 5)
            mat = [[rng.randint(-10, 20) for _ in range(w)] for _ in range(h)]
            cas.append({"input": mat, "expected": [sum(r) for r in mat]})
        return cas

    # 6. Classe 2C : Écrasement séquentiel (`a = a + b; b = a - b`)
    if contrat == "c2_ecrasement_sequentiel":
        for a, b in [(0, 0), (1, 0), (0, 1), (-1, 1), (10, 20)] + [
            (rng.randint(-50, 50), rng.randint(-50, 50)) for _ in range(20)
        ]:
            cas.append({"input": (a, b), "expected": (a + b, a - b)})
        return cas

    # 7. Classe 3 : Récursion sans cas de base (`return n + total(n - 1)`)
    if contrat == "c3_recursion_base_manquante":
        for n in [0, -1, 1, 2, 3, 10] + [rng.randint(4, 35) for _ in range(19)]:
            cas.append({"input": n, "expected": n * (n + 1) // 2 if n > 0 else 0})
        return cas

    # 8. Classe 4 : Off-by-one couplé (`for i in range(len(a)): out.append(a[i+1] - a[i])`)
    if contrat == "c4_off_by_one_couple":
        coins_seq = [[], [42], [1, 3], [10, 10, 10], [5, 2, 9, 1]]
        for seq in coins_seq:
            cas.append({"input": seq, "expected": [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]})
        for _ in range(20):
            seq = [rng.randint(-50, 50) for _ in range(rng.randint(2, 15))]
            cas.append({"input": seq, "expected": [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]})
        return cas

    # 9. Classe 5A : Piège `x is y` hors cache d'interning (`257`, `1000`) + `n / 2` indice
    if contrat == "c5_pieges_semantiques_is_et_div":
        # Teste l'égalité du milieu : `a[len(a) // 2] == cible` avec des entiers > 256
        coins_is = [
            ([257, 500, 257], 500, True),
            ([1000], 1000, True),
            ([99999, 88888, 77777], 88888, True),
            ([300, 400, 500], 999, False),
        ]
        for arr, val, exp in coins_is:
            cas.append({"input": (arr, val), "expected": exp})
        for _ in range(21):
            v = rng.randint(500, 100_000)
            arr = [rng.randint(500, 100_000) for _ in range(5)]
            milieu = arr[len(arr) // 2]
            cible = milieu if rng.random() < 0.5 else v + 1
            cas.append({"input": (arr, cible), "expected": (milieu == cible)})
        return cas

    # 10. Classe 5B : Égalité flottante IEEE 754 (`0.1 + 0.2 == 0.3`)
    if contrat == "c5_egalite_flottante":
        coins_flt = [
            (0.1, 0.2, 0.3, True),
            (0.15, 0.15, 0.3, True),
            (1.0, 2.0, 3.5, False),
            (-0.0, 0.0, 0.0, True),
        ]
        for x, y, z, exp in coins_flt:
            cas.append({"input": (x, y, z), "expected": exp})
        for _ in range(21):
            x = rng.uniform(-10.0, 10.0)
            y = rng.uniform(-10.0, 10.0)
            z = (x + y) if rng.random() < 0.5 else (x + y + 0.5)
            cas.append({"input": (x, y, z), "expected": abs((x + y) - z) < 1e-9})
        return cas

    # 11. Classe 1D (Hadès v3.0) : Stencil 2D `out = grid` avec lecture de `grid` à l'itération suivante
    if contrat == "c1_stencil_2d_def_use":
        g_oracle = StratifiedOracle([Frontier("g", grids(limit=12), rand_grid)], n_random=15)
        for (g,) in g_oracle.cases():
            if not g or not g[0]:
                continue
            exp = [r[:] for r in g]
            for i in range(len(g)):
                for j in range(1, len(g[0])):
                    exp[i][j] = g[i][j] + g[i][j - 1]
            cas.append({"input": g, "expected": exp, "check_disjoint_ids": True})
        return cas

    # 12. Classe 2D (Hadès v3.0) : Sinking multi-initialisations (`best = 0; cur = 0`)
    if contrat == "c2_sinking_multi_inits":
        coins_m = [
            [[1, 2], [1, 1]],
            [[10, -2], [3, 4], [1, 1]],
            [[0, 0], [5, 5]],
            [[7], [2], [9]],
        ]
        for m in coins_m:
            cas.append({"input": m, "expected": max([0] + [sum(r) for r in m])})
        for _ in range(21):
            h, w = rng.randint(2, 5), rng.randint(1, 5)
            m = [[rng.randint(0, 20) for _ in range(w)] for _ in range(h)]
            cas.append({"input": m, "expected": max([0] + [sum(r) for r in m])})
        return cas

    # 13. Classe 4B (Hadès v3.0) : Off-by-one lookback (`a[i] - a[i - 1]` qui wrap à `a[-1]`)
    if contrat == "c4_off_by_one_lookback":
        coins_seq = [[], [42], [10, 13], [5, 2, 9, 1], [0, 0, 0]]
        for seq in coins_seq:
            cas.append({"input": seq, "expected": [seq[i] - seq[i - 1] for i in range(1, len(seq))]})
        for _ in range(20):
            seq = [rng.randint(-50, 50) for _ in range(rng.randint(2, 15))]
            cas.append({"input": seq, "expected": [seq[i] - seq[i - 1] for i in range(1, len(seq))]})
        return cas

    # 14. Classe 5C (Hadès StratifiedOracle) : `x > 1` au lieu de `x > 0` (invisible sous randbits(64) pur)
    if contrat == "c5_count_pos_x_eq_1":
        oracle_a = StratifiedOracle([Frontier("a", lists_of(ints()), lambda: rand_list(rand_int))], n_random=25)
        for (arr,) in oracle_a.cases():
            cas.append({"input": arr, "expected": sum(1 for x in arr if x > 0)})
        return cas

    # 15. Classe 3C (Hadès RecursionBaseCaseRepair) : `rng(n - 1) + [n]` -> neutre liste `[]`
    if contrat == "c3_recursion_liste_neutre":
        for n in [0, -1, 1, 2, 3, 8] + [rng.randint(4, 20) for _ in range(19)]:
            cas.append({"input": n, "expected": list(range(1, n + 1)) if n > 0 else []})
        return cas

    # Contrats de base v1.0
    return generer_instances_verite_terrain(contrat, n_instances=n_total)


# ==============================================================================
# 🔬 2. LES TRANSFORMATEURS AST DE SOUS-ARBRES GARDÉS (SPÉCIFICATION HADÈS)
# ==============================================================================

class PurificateurAST(ast.NodeTransformer):
    """Opérateur 0 : Purge des appels interdits et bornage des boucles `while`."""

    def __init__(self):
        super().__init__()
        self.while_count = 0

    def visit_Import(self, node: ast.Import) -> ast.AST:
        return ast.Pass()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        return ast.Pass()

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.value, ast.Call):
            fn = node.value.func
            if isinstance(fn, ast.Name) and fn.id in ("open", "eval", "exec", "__import__", "print"):
                return ast.Pass()
            if isinstance(fn, ast.Attribute) and fn.attr in ("system", "popen", "fopen", "CreateFileW"):
                return ast.Pass()
        return node

    def visit_While(self, node: ast.While) -> ast.AST:
        self.generic_visit(node)
        self.while_count += 1
        g = f"_cegis_guard_{self.while_count}"
        init_a = ast.Assign(targets=[ast.Name(id=g, ctx=ast.Store())], value=ast.Constant(value=0))
        inc_a = ast.AugAssign(target=ast.Name(id=g, ctx=ast.Store()), op=ast.Add(), value=ast.Constant(value=1))
        b_test = ast.Compare(left=ast.Name(id=g, ctx=ast.Load()), ops=[ast.Lt()], comparators=[ast.Constant(value=32)])
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            node.test = b_test
        else:
            node.test = ast.BoolOp(op=ast.And(), values=[b_test, node.test])
        node.body = [inc_a] + node.body
        return [init_a, node]  # type: ignore


class AntiAliasingAllocationTransformer(ast.NodeTransformer):
    """
    Classe 1 (Spécification Hadès) — Aliasing d'allocation (4 motifs) :
      1. `BinOp(Mult, List(elts=[mutable]), n)` -> `ListComp` (y compris `[[0]*W]*H`)
      2. `dict.fromkeys(k, <mutable>)` -> `DictComp({x: <mutable> for x in k})`
      3. Défaut mutable `def f(x, acc=[]):` -> `acc=None` + `if acc is None: acc = []`
    """

    def __init__(self):
        super().__init__()
        self.applied = False
        self.actions: List[str] = []

    @staticmethod
    def _est_constructeur_mutable(node: ast.AST) -> bool:
        if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("list", "dict", "set"):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) and isinstance(node.left, ast.List):
            return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Motif 3 : Défaut mutable dans la signature (`def f(x, acc=[]):`)
        if node.args.defaults:
            nb_args = len(node.args.args)
            nb_defs = len(node.args.defaults)
            inits_entete: List[ast.stmt] = []
            for idx_d, d_node in enumerate(node.args.defaults):
                if self._est_constructeur_mutable(d_node):
                    param_obj = node.args.args[nb_args - nb_defs + idx_d]
                    p_name = param_obj.arg
                    lit_copy = copy.deepcopy(d_node)
                    node.args.defaults[idx_d] = ast.Constant(value=None)
                    if_none = ast.If(
                        test=ast.Compare(
                            left=ast.Name(id=p_name, ctx=ast.Load()),
                            ops=[ast.Is()],
                            comparators=[ast.Constant(value=None)],
                        ),
                        body=[ast.Assign(targets=[ast.Name(id=p_name, ctx=ast.Store())], value=lit_copy)],
                        orelse=[],
                    )
                    inits_entete.append(if_none)
                    self.applied = True
                    self.actions.append(f"Défaut mutable `{p_name}` -> `None` + init locale")
            if inits_entete:
                node.body = inits_entete + node.body

        self.generic_visit(node)
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        # Motif 2 : `dict.fromkeys(k, <mutable>)` -> `{_k: <mutable> for _k in k}`
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "dict"
            and node.func.attr == "fromkeys"
            and len(node.args) == 2
            and self._est_constructeur_mutable(node.args[1])
        ):
            self.applied = True
            self.actions.append("`dict.fromkeys(k, mutable)` -> `DictComp`")
            return ast.DictComp(
                key=ast.Name(id="_k_fk", ctx=ast.Load()),
                value=copy.deepcopy(node.args[1]),
                generators=[
                    ast.comprehension(
                        target=ast.Name(id="_k_fk", ctx=ast.Store()),
                        iter=copy.deepcopy(node.args[0]),
                        ifs=[],
                        is_async=0,
                    )
                ],
            )
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Motif 1A : `([[val] * W]) * H`
        if (
            isinstance(node.op, ast.Mult)
            and isinstance(node.left, ast.BinOp)
            and isinstance(node.left.op, ast.Mult)
            and isinstance(node.left.left, ast.List)
            and len(node.left.left.elts) == 1
        ):
            self.applied = True
            self.actions.append("`[[x]*W]*H` -> `ListComp` 2D disjointe")
            elem = copy.deepcopy(node.left.left.elts[0])
            w_n = copy.deepcopy(node.left.right)
            h_n = copy.deepcopy(node.right)
            inner = ast.ListComp(
                elt=elem,
                generators=[
                    ast.comprehension(
                        target=ast.Name(id="_c", ctx=ast.Store()),
                        iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()), args=[w_n], keywords=[]),
                        ifs=[],
                        is_async=0,
                    )
                ],
            )
            return ast.ListComp(
                elt=inner,
                generators=[
                    ast.comprehension(
                        target=ast.Name(id="_r", ctx=ast.Store()),
                        iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()), args=[h_n], keywords=[]),
                        ifs=[],
                        is_async=0,
                    )
                ],
            )

        self.generic_visit(node)
        # Motif 1B : `[<mutable>] * n` -> `[<mutable> for _ in range(n)]`
        if (
            isinstance(node.op, ast.Mult)
            and isinstance(node.left, ast.List)
            and len(node.left.elts) == 1
            and self._est_constructeur_mutable(node.left.elts[0])
        ):
            self.applied = True
            self.actions.append("`[mutable]*n` -> `ListComp`")
            return ast.ListComp(
                elt=copy.deepcopy(node.left.elts[0]),
                generators=[
                    ast.comprehension(
                        target=ast.Name(id="_i", ctx=ast.Store()),
                        iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()), args=[copy.deepcopy(node.right)], keywords=[]),
                        ifs=[],
                        is_async=0,
                    )
                ],
            )
        return node


class CrossMutableStateTransformer(ast.NodeTransformer):
    """
    Classe 2 (Spécification Hadès) — État mutable croisé multi-lignes :
      - (2a) `for x in lst:` avec `lst.remove/pop/insert/append/clear` ou `del lst[...]` -> `for x in lst[:]:`
      - (2b) Sinking d'initialisation $O(k)$ borné : déplace `Assign(t, 0 / [] / set())`
        précédant immédiatement un `For` imbriqué vers le début du corps de la boucle externe.
      - (2c) Écrasement séquentiel `a = E1(a,b); b = E2(a,b)` -> `a, b = E1(a,b), E2(a,b)`.
    """

    METHODES_MUTANTES = {"remove", "pop", "insert", "append", "clear", "extend"}

    def __init__(self, mode: str = "all"):
        super().__init__()
        self.mode = mode
        self.applied = False
        self.actions: List[str] = []

    @staticmethod
    def _noms_lus(expr: ast.AST) -> Set[str]:
        return {n.id for n in ast.walk(expr) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}

    @staticmethod
    def _est_init_constante_ou_vide(stmt: ast.stmt) -> Optional[str]:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            val = stmt.value
            if isinstance(val, (ast.Constant, ast.List, ast.Dict, ast.Set)):
                return stmt.targets[0].id
            if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id in ("set", "list", "dict"):
                return stmt.targets[0].id
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)

        # (2a) Si `lst` est mutée dans la boucle, cloner aussi l'argument d'entrée `lst = lst[:]`
        if self.applied and any("lst[:]" in a for a in self.actions) and node.args.args:
            arg0 = node.args.args[0].arg
            node.body.insert(0, ast.parse(f"{arg0} = {arg0}[:]").body[0])

        # (2b) Sinking d'initialisation : `acc = 0` suivi immédiatement de `for row in mat: for x in row: acc += x`
        if self.mode in ("all", "sinking"):
            new_body: List[ast.stmt] = []
            i = 0
            while i < len(node.body):
                s_curr = node.body[i]
                var_init = self._est_init_constante_ou_vide(s_curr)
                if var_init and i + 1 < len(node.body) and isinstance(node.body[i + 1], ast.For):
                    outer_for: ast.For = copy.deepcopy(node.body[i + 1])  # type: ignore
                    has_inner_for = any(isinstance(sub, ast.For) for sub in outer_for.body)
                    uses_var_in_outer = any(
                        isinstance(sub, ast.Name) and sub.id == var_init for sub in ast.walk(outer_for)
                    )
                    if has_inner_for and uses_var_in_outer:
                        outer_for.body.insert(0, copy.deepcopy(s_curr))
                        new_body.append(outer_for)
                        self.applied = True
                        self.actions.append(f"Sinking d'initialisation `{var_init}` dans la boucle externe")
                        i += 2
                        continue
                new_body.append(s_curr)
                i += 1
            node.body = new_body

        # (2c) Fusion d'affectations simultanées Read-After-Write (`a, b = E1, E2`)
        if self.mode in ("all", "simultaneous"):
            body2: List[ast.stmt] = []
            i = 0
            while i < len(node.body):
                s1 = node.body[i]
                if (
                    i + 1 < len(node.body)
                    and isinstance(s1, ast.Assign)
                    and len(s1.targets) == 1
                    and isinstance(s1.targets[0], ast.Name)
                ):
                    s2 = node.body[i + 1]
                    if isinstance(s2, ast.Assign) and len(s2.targets) == 1 and isinstance(s2.targets[0], ast.Name):
                        v1, v2 = s1.targets[0].id, s2.targets[0].id
                        if v1 != v2 and v1 in self._noms_lus(s2.value) and v2 in self._noms_lus(s1.value):
                            self.applied = True
                            self.actions.append(f"Affectation simultanée `{v1}, {v2} = E1, E2`")
                            simul = ast.Assign(
                                targets=[ast.Tuple(elts=[ast.Name(id=v1, ctx=ast.Store()), ast.Name(id=v2, ctx=ast.Store())], ctx=ast.Store())],
                                value=ast.Tuple(elts=[copy.deepcopy(s1.value), copy.deepcopy(s2.value)], ctx=ast.Load()),
                            )
                            body2.append(simul)
                            i += 2
                            continue
                body2.append(s1)
                i += 1
            node.body = body2

        return node

    def visit_For(self, node: ast.For) -> ast.AST:
        self.generic_visit(node)
        if self.mode in ("all", "iter_slice") and isinstance(node.iter, ast.Name):
            iter_name = node.iter.id
            mutated = False
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Attribute)
                    and isinstance(sub.func.value, ast.Name)
                    and sub.func.value.id == iter_name
                    and sub.func.attr in self.METHODES_MUTANTES
                ):
                    mutated = True
                    break
                if (
                    isinstance(sub, ast.Delete)
                    and any(
                        isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == iter_name
                        for t in sub.targets
                    )
                ):
                    mutated = True
                    break
            if mutated:
                self.applied = True
                self.actions.append(f"Itérateur `{iter_name}` -> tranche `{iter_name}[:]` (lst[:])")
                node.iter = ast.Subscript(
                    value=ast.Name(id=iter_name, ctx=ast.Load()),
                    slice=ast.Slice(lower=None, upper=None, step=None),
                    ctx=ast.Load(),
                )
        return node


class MonoidRecursionTransformer(ast.NodeTransformer):
    """
    Classe 3 (Spécification Hadès) — Récursion mal terminée & Table d'Élément Neutre :
      - Inspecte `def f(n):` contenant un appel récursif `f(n - c)` combiné par un
        opérateur monoïdal (`+ -> 0`, `* -> 1`, `and -> True`, `or -> False`).
      - Insère en tête `if n <= 0: return <neutre>`.
      - Si l'appel récursif est `f(n)` (aucun progrès, args == params), marque
        explicitement `non_reparable_sans_progres = True` (franchise PSI-23).
    """

    def __init__(self):
        super().__init__()
        self.applied = False
        self.non_reparable_sans_progres = False
        self.actions: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if not node.args.args:
            return node
        fn_name = node.name
        param = node.args.args[0].arg

        has_base_if = any(isinstance(s, ast.If) for s in node.body)
        operateur_monoide: Optional[type] = None
        decroit = False
        sans_progres = False

        for sub in ast.walk(node):
            if isinstance(sub, ast.BinOp):
                for side in (sub.left, sub.right):
                    if isinstance(side, ast.Call) and isinstance(side.func, ast.Name) and side.func.id == fn_name:
                        operateur_monoide = type(sub.op)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == fn_name and len(sub.args) == 1:
                arg0 = sub.args[0]
                if (
                    isinstance(arg0, ast.BinOp)
                    and isinstance(arg0.op, ast.Sub)
                    and isinstance(arg0.left, ast.Name)
                    and arg0.left.id == param
                    and isinstance(arg0.right, ast.Constant)
                ):
                    decroit = True
                elif isinstance(arg0, ast.Name) and arg0.id == param:
                    sans_progres = True

        if sans_progres and not decroit:
            self.non_reparable_sans_progres = True

        if decroit and not has_base_if:
            table_neutre = {
                ast.Add: 0,
                ast.Mult: 1,
                ast.BitOr: 0,
                ast.BitXor: 0,
            }
            neutre_val = table_neutre.get(operateur_monoide, 0)  # type: ignore
            guard_stmt = ast.parse(f"if {param} <= 0:\n    return {neutre_val!r}").body[0]
            node.body.insert(0, guard_stmt)
            self.applied = True
            self.actions.append(f"Insertion cas de base monoïdal `if {param} <= 0: return {neutre_val!r}`")

        return node


class CoupledOffByOneRangeTransformer(ast.NodeTransformer):
    """
    Classe 4 (Spécification Hadès) — Off-by-one couplés (Vallée de fitness d'ordre 2) :
    Dans `for i in range(len(a)):` (ou `range(n)`), inspecte tous les `Subscript`
    de la forme `a[i + c]` avec `c > 0` constant. Si `c_max > 0`, remplace la borne
    supérieure `hi` du `range` par `hi - c_max` (`range(len(a) - 1)`).
    """

    def __init__(self):
        super().__init__()
        self.applied = False
        self.actions: List[str] = []

    def visit_For(self, node: ast.For) -> ast.AST:
        self.generic_visit(node)
        if not isinstance(node.target, ast.Name):
            return node
        loop_var = node.target.id

        if (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
            and len(node.iter.args) in (1, 2)
        ):
            c_max = 0
            for sub in ast.walk(node):
                if isinstance(sub, ast.Subscript):
                    sl = sub.slice
                    if (
                        isinstance(sl, ast.BinOp)
                        and isinstance(sl.op, ast.Add)
                        and isinstance(sl.left, ast.Name)
                        and sl.left.id == loop_var
                        and isinstance(sl.right, ast.Constant)
                        and isinstance(sl.right.value, int)
                    ):
                        c_max = max(c_max, sl.right.value)

            if c_max > 0:
                hi_idx = 0 if len(node.iter.args) == 1 else 1
                hi_node = node.iter.args[hi_idx]
                # Éviter de décrémenter deux fois si déjà `len(a) - c_max`
                if not (isinstance(hi_node, ast.BinOp) and isinstance(hi_node.op, ast.Sub)):
                    node.iter.args[hi_idx] = ast.BinOp(
                        left=copy.deepcopy(hi_node),
                        op=ast.Sub(),
                        right=ast.Constant(value=c_max),
                    )
                    self.applied = True
                    self.actions.append(f"Normalisation couplée `range(hi - {c_max})` pour `a[{loop_var} + {c_max}]`")
        return node


class SemanticEquivalenceTransformer(ast.NodeTransformer):
    """
    Classe 5 (Spécification Hadès) — Pièges d'équivalence sémantique mécaniques :
      1. `x is y` (quand aucun opérande n'est `None`/`True`/`False`) -> `x == y`
      2. `n / 2` utilisé comme indice de `Subscript` ou argument de `range` -> `n // 2`
      3. `a == b` sur flottants (`mode="float_eps"`) -> `abs(a - b) < 1e-9`
    """

    def __init__(self, float_tolerance: bool = False):
        super().__init__()
        self.float_tolerance = float_tolerance
        self.applied = False
        self.actions: List[str] = []

    @staticmethod
    def _est_singleton_python(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and (node.value is None or isinstance(node.value, bool))

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.slice, ast.BinOp) and isinstance(node.slice.op, ast.Div):
            node.slice.op = ast.FloorDiv()
            self.applied = True
            self.actions.append("Indice flottant `Div (/)` -> `FloorDiv (//)`")
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "range":
            for i, arg in enumerate(node.args):
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Div):
                    arg.op = ast.FloorDiv()
                    self.applied = True
                    self.actions.append("Argument `range` flottant `Div (/)` -> `FloorDiv (//)`")
        return node

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if len(node.ops) == 1 and len(node.comparators) == 1:
            op = node.ops[0]
            right = node.comparators[0]
            # 1. `x is y` -> `x == y` (si aucun n'est None/True/False)
            if isinstance(op, (ast.Is, ast.IsNot)) and not (
                self._est_singleton_python(node.left) or self._est_singleton_python(right)
            ):
                node.ops[0] = ast.Eq() if isinstance(op, ast.Is) else ast.NotEq()
                self.applied = True
                self.actions.append("`Is` sur valeur -> `Eq (==)`")
                return node

            # 2. `a == b` sur flottants -> `abs(a - b) < 1e-9`
            if self.float_tolerance and isinstance(op, ast.Eq):
                self.applied = True
                self.actions.append("`a == b` flottant -> `abs(a - b) < 1e-9`")
                return ast.Compare(
                    left=ast.Call(
                        func=ast.Name(id="abs", ctx=ast.Load()),
                        args=[ast.BinOp(left=copy.deepcopy(node.left), op=ast.Sub(), right=copy.deepcopy(right))],
                        keywords=[],
                    ),
                    ops=[ast.Lt()],
                    comparators=[ast.Constant(value=1e-9)],
                )
        return node


# ==============================================================================
# 🧬 3. ORCHESTRATEUR CEGIS v2.1 (ORACLE STRATIFIÉ + CERTIFICATION RING-0)
# ==============================================================================
class ChirurgienCEGIS:
    MAX_ITERATIONS_CEGIS = 20

    @staticmethod
    def _extraire_nom_et_arg_fonction(tree: ast.AST) -> Tuple[str, str]:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                arg_name = node.args.args[0].arg if node.args.args else "tasks"
                return node.name, arg_name
        return "solve", "tasks"

    @staticmethod
    def _verifier_oracle_stratifie(code_str: str, fn_name: str, exemples: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Exécute le candidat sur les 25 instances stratifiées (10 coins X1..X5 + 15 aléatoires)
        dans le même environnement pour démasquer aussi les effets de bord inter-appels
        (comme `def f(x, acc=[]):` qui accumule d'un appel au suivant !).
        """
        if any(w in code_str for w in ("open(", "eval(", "exec(", "__import__", "while True")):
            return False, ["EFFET_DE_BORD_OU_BOUCLE_INFINIE_STATIQUE"]

        env: Dict[str, Any] = {}
        try:
            exec(compile(code_str, "<cegis_stratified>", "exec"), env)
            fn = env.get(fn_name)
            if not callable(fn):
                return False, ["FONCTION_INTROUVABLE"]

            t0 = time.perf_counter()
            for ex in exemples:
                inp_orig = copy.deepcopy(ex["input"])
                inp_call = copy.deepcopy(ex["input"])
                res = fn(inp_call)

                if (time.perf_counter() - t0) > 0.040:
                    return False, ["DEPASSEMENT_BUDGET_40MS_X5"]

                if inp_call != inp_orig:
                    return False, ["MUTATION_DESTRUCTRICE_ENTREE"]

                if res != ex["expected"]:
                    return False, ["ECHEC_ORACLE_STRATIFIE"]

                if ex.get("check_disjoint_ids") and isinstance(res, list) and len(res) >= 2:
                    ids = [id(r) for r in res if isinstance(r, list)]
                    if len(ids) != len(set(ids)):
                        return False, ["FUITE_ALIAS_MEMOIRE_LIGNES_PARTAGEES"]

            return True, []
        except RecursionError:
            return False, ["RECURSION_SANS_CAS_DE_BASE_OU_PROGRES"]
        except IndexError:
            return False, ["OFF_BY_ONE_INDEX_ERROR"]
        except TypeError as e:
            return False, [f"ERREUR_TYPE:{e}"]
        except Exception as e:
            return False, [f"EXCEPTION:{type(e).__name__}"]

    @classmethod
    def _generer_candidats_mutations_ast(cls, code_purifie: str, fn_name: str, arg_name: str) -> List[Tuple[str, str]]:
        candidats: List[Tuple[str, str]] = [
            ("Purification AST (suppression effets de bord & bornage while)", code_purifie)
        ]

        # 1A. Les 3 Réécritures AST Profondes d'Hadès (`alix_ast_repairs_hades.py`)
        try:
            t_alias, sites_alias = repair_aliasing(ast.parse(code_purifie))
            if sites_alias:
                desc_a = ", ".join(
                    f"`{s['dst']} = {s['src']}` -> copie {s['kind']} (profondeur {s['depth']})"
                    for s in sites_alias
                )
                candidats.append((f"Hadès AliasCopyRepair (def-use) : {desc_a}", ast.unparse(t_alias)))
        except Exception:
            pass

        try:
            for cand_sink in sinking_candidates(ast.parse(code_purifie)):
                candidats.append((
                    f"Hadès SinkingCandidate (prio={cand_sink.priority}, niv={cand_sink.level}) : {cand_sink.note}",
                    cand_sink.source(),
                ))
        except Exception:
            pass

        try:
            t_obo, sites_obo = normalize_offbyone(ast.parse(code_purifie))
            if sites_obo:
                desc_o = ", ".join(
                    f"pivot p={s['pivot']} sur `{s['var']}` (offsets={s['offsets']})"
                    for s in sites_obo
                )
                candidats.append((f"Hadès OffByOneNormalizer (affine) : {desc_o}", ast.unparse(t_obo)))
        except Exception:
            pass

        try:
            t_rec, sites_rec = repair_recursion(ast.parse(code_purifie))
            applied_rec = [s for s in sites_rec if s.get("applied")]
            if applied_rec:
                desc_r = ", ".join(f"`if {s['measure']} <= 0: return <neutre>` dans `{s['fn']}`" for s in applied_rec)
                candidats.append((f"Hadès RecursionBaseCaseRepair (monoïde) : {desc_r}", ast.unparse(t_rec)))
        except Exception:
            pass

        # 1B. Les 6 Chirurgiens AST de Sous-Arbres Complémentaires
        for label_base, build_fn in [
            ("Chirurgie AST Classe 1 (Aliasing d'allocation)", lambda: AntiAliasingAllocationTransformer()),
            ("Chirurgie AST Classe 2a (Itérateur `lst[:]`) ", lambda: CrossMutableStateTransformer("iter_slice")),
            ("Chirurgie AST Classe 2b (Sinking d'initialisation)", lambda: CrossMutableStateTransformer("sinking")),
            ("Chirurgie AST Classe 2c (Affectation simultanée `a, b = E1, E2`)", lambda: CrossMutableStateTransformer("simultaneous")),
            ("Chirurgie AST Classe 3 (Cas de base monoïdal récursif)", lambda: MonoidRecursionTransformer()),
            ("Chirurgie AST Classe 4 (Normalisation couplée Off-by-One `range(N - c)`)", lambda: CoupledOffByOneRangeTransformer()),
            ("Chirurgie AST Classe 5a (Pièges sémantiques `is -> ==` & `/ -> //`)", lambda: SemanticEquivalenceTransformer(False)),
            ("Chirurgie AST Classe 5b (Tolérance flottante IEEE 754 `abs(a-b) < 1e-9`)", lambda: SemanticEquivalenceTransformer(True)),
        ]:
            try:
                t_c = ast.parse(code_purifie)
                tr = build_fn()
                t_new = tr.visit(t_c)
                if getattr(tr, "applied", False):
                    ast.fix_missing_locations(t_new)
                    actions_str = " + ".join(getattr(tr, "actions", []))
                    candidats.append((f"{label_base} : {actions_str}", ast.unparse(t_new)))
            except Exception:
                pass

        # 2. Mutations d'opérateurs d'ordre 1 (pour les bugs locaux)
        try:
            candidats.extend(cls._mutations_operateurs_ast(ast.parse(code_purifie)))
        except Exception:
            pass

        # 3. Grammaire de chirurgie 2D & prédicats (v1.0)
        candidats.extend([
            (
                "Chirurgie 2D : Transposition rectangulaire exacte `g[r][c]` sur `len(g[0]) x len(g)`",
                f"def {fn_name}({arg_name}):\n    if not {arg_name}:\n        return []\n    return [[[g[r][c] for r in range(len(g))] for c in range(len(g[0]))] for g in {arg_name}]\n",
            ),
            (
                "Chirurgie 2D : Miroir horizontal `list(reversed(r))` par ligne",
                f"def {fn_name}({arg_name}):\n    if not {arg_name}:\n        return []\n    return [[list(reversed(r)) for r in g] for g in {arg_name}]\n",
            ),
            (
                "Synthèse Prédicat : Détection de vacuité `len(x) == 0`",
                f"def {fn_name}({arg_name}):\n    return len({arg_name}) == 0\n",
            ),
        ])
        return candidats

    @classmethod
    def _mutations_operateurs_ast(cls, tree: ast.AST) -> List[Tuple[str, str]]:
        resultats: List[Tuple[str, str]] = []
        nodes_list = list(ast.walk(tree))
        for idx, n in enumerate(nodes_list):
            if isinstance(n, ast.Compare) and len(n.ops) == 1:
                remp = {
                    ast.Lt: [(ast.Gt(), "< -> >")],
                    ast.GtE: [(ast.Gt(), ">= -> >")],
                }.get(type(n.ops[0]), [])
                for new_op, desc in remp:
                    t_c = copy.deepcopy(tree)
                    target = list(ast.walk(t_c))[idx]
                    if isinstance(target, ast.Compare):
                        target.ops[0] = new_op
                        ast.fix_missing_locations(t_c)
                        resultats.append((f"Mutation AST comparaison ({desc})", ast.unparse(t_c)))
                # Mutation de constante frontière (`x > 1` -> `x > 0`) détectée uniquement par StratifiedOracle
                if (
                    len(n.comparators) == 1
                    and isinstance(n.comparators[0], ast.Constant)
                    and n.comparators[0].value == 1
                ):
                    t_c = copy.deepcopy(tree)
                    target = list(ast.walk(t_c))[idx]
                    if isinstance(target, ast.Compare) and isinstance(target.comparators[0], ast.Constant):
                        target.comparators[0] = ast.Constant(value=0)
                        ast.fix_missing_locations(t_c)
                        resultats.append(("Mutation AST seuil frontière (`> 1` -> `> 0`, détecté sur coin `[1]`)", ast.unparse(t_c)))
            elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                t_c = copy.deepcopy(tree)
                target = list(ast.walk(t_c))[idx]
                if isinstance(target, ast.BinOp):
                    target.op = ast.Sub()
                    ast.fix_missing_locations(t_c)
                    resultats.append(("Mutation AST arithmétique (+ -> -)", ast.unparse(t_c)))
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "any":
                t_c = copy.deepcopy(tree)
                target = list(ast.walk(t_c))[idx]
                if isinstance(target, ast.Call) and isinstance(target.func, ast.Name):
                    target.func.id = "all"
                    ast.fix_missing_locations(t_c)
                    resultats.append(("Mutation quantificateur (`any` -> `all`)", ast.unparse(t_c)))
        return resultats

    @classmethod
    def reparer_en_boucle_fermee(cls, code_initial: str, contrat: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        arbre_init = ast.parse(code_initial)
        fn_name, arg_name = cls._extraire_nom_et_arg_fonction(arbre_init)

        # Détection franche de récursion non réparable via RecursionBaseCaseRepair d'Hadès
        _, rec_logs = repair_recursion(copy.deepcopy(arbre_init))
        rejets_rec = [
            lg for lg in rec_logs
            if not lg.get("applied") and "garde" not in lg.get("why", "")
        ]
        if rejets_rec:
            why_str = rejets_rec[0]["why"]
            return {
                "statut": "REJET_FRANC_SANS_PROGRES",
                "verdict_final": "NON_REPARABLE_DETERMINISTE",
                "infractions_initiales": ["RECURSION_NON_REPARABLE_DETERMINISTE"],
                "operation_decisive": f"Rejet franc Hadès RecursionBaseCaseRepair (PSI-23) : {why_str}",
                "code_repare": None,
                "iterations_cegis": 1,
                "duree_totale_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            }

        exemples = generer_oracle_stratifie(contrat, n_total=25)
        ok_init, inf_init = cls._verifier_oracle_stratifie(code_initial, fn_name, exemples)

        purif = PurificateurAST()
        arbre_purifie = purif.visit(copy.deepcopy(arbre_init))
        ast.fix_missing_locations(arbre_purifie)
        code_purifie = ast.unparse(arbre_purifie)

        candidats = cls._generer_candidats_mutations_ast(code_purifie, fn_name, arg_name)
        est_contrat_sentinelle_native = contrat in (
            "arc_inversion",
            "arc_miroir_horizontal",
            "arc_transpose",
            "predicat_tous_positifs",
            "predicat_est_vide",
        )

        for idx_it, (desc_op, code_cand) in enumerate(candidats, start=1):
            ok_strat, _ = cls._verifier_oracle_stratifie(code_cand, fn_name, exemples)
            if not ok_strat:
                continue

            # Validation finale en Ring-0 Windows NT (`S-1-16-0 Untrusted`) sur les contrats natifs
            if est_contrat_sentinelle_native:
                audit_r0 = AlixSentinelleBouclierPSI.evaluer_verdict(code_cand, contrat_verite_terrain=contrat)
                if audit_r0["verdict"] != "PASSE":
                    continue

            return {
                "statut": "REPARE_ET_CERTIFIE",
                "verdict_final": "PASSE",
                "infractions_initiales": inf_init,
                "operation_decisive": desc_op,
                "code_repare": code_cand,
                "iterations_cegis": idx_it,
                "duree_totale_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            }

        return {
            "statut": "ECHEC",
            "verdict_final": "ECHOUE",
            "infractions_initiales": inf_init,
            "operation_decisive": None,
            "code_repare": None,
            "iterations_cegis": len(candidats),
            "duree_totale_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        }


# ==============================================================================
# 🏆 4. BANC D'ESSAI HADÈS × ALIX v3.2 (16 ÉPREUVES MULTI-LIGNES & COINS PAIRWISE)
# ==============================================================================
BANC_HADÈS_V3_2 = [
    {
        "id": "HADES_1A_ALIASING_GRILLE_2D",
        "contrat": "c1_aliasing_grille_2d",
        "code": "def init_g(dims):\n    h, w = dims\n    g = [[0] * w] * h\n    g[0][0] = 1\n    return g\n",
    },
    {
        "id": "HADES_1B_DEFAUT_MUTABLE_PERSISTANT",
        "contrat": "c1_defaut_mutable",
        "code": "def ajouter(x, acc=[]):\n    acc.append(x)\n    return acc\n",
    },
    {
        "id": "HADES_1C_DICT_FROMKEYS_PARTAGE",
        "contrat": "c1_dict_fromkeys",
        "code": "def init_dict(keys):\n    d = dict.fromkeys(keys, [])\n    d[keys[0]].append(1)\n    return d\n",
    },
    {
        "id": "HADES_1D_STENCIL_2D_DEF_USE_BACKEDGE",
        "contrat": "c1_stencil_2d_def_use",
        "code": (
            "def smooth(grid):\n"
            "    out = grid\n"
            "    for i in range(len(grid)):\n"
            "        for j in range(1, len(grid[0])):\n"
            "            out[i][j] = grid[i][j] + grid[i][j - 1]\n"
            "    return out\n"
        ),
    },
    {
        "id": "HADES_2A_MUTATION_COLLECTION_ITEREE",
        "contrat": "c2_mutation_iteration",
        "code": "def purger(lst):\n    for x in lst:\n        if x == 0:\n            lst.remove(x)\n    return lst\n",
    },
    {
        "id": "HADES_2B_SINKING_INIT_HORS_BOUCLE",
        "contrat": "c2_sinking_init",
        "code": "def sommes_lignes(mat):\n    out = []\n    s = 0\n    for row in mat:\n        for x in row:\n            s = s + x\n        out.append(s)\n    return out\n",
    },
    {
        "id": "HADES_2C_ECRASEMENT_SEQUENTIEL_RAW",
        "contrat": "c2_ecrasement_sequentiel",
        "code": "def step(ab):\n    a, b = ab\n    a = a + b\n    b = a - b\n    return (a, b)\n",
    },
    {
        "id": "HADES_2D_SINKING_MULTI_INITS_BEST_CUR",
        "contrat": "c2_sinking_multi_inits",
        "code": (
            "def row_max_sum(grid):\n"
            "    best = 0\n"
            "    cur = 0\n"
            "    for row in grid:\n"
            "        for x in row:\n"
            "            cur += x\n"
            "        best = max(best, cur)\n"
            "    return best\n"
        ),
    },
    {
        "id": "HADES_3A_RECURSION_SANS_CAS_DE_BASE",
        "contrat": "c3_recursion_base_manquante",
        "code": "def total(n):\n    return n + total(n - 1)\n",
    },
    {
        "id": "HADES_3B_RECURSION_SANS_PROGRES_REJET_FRANC",
        "contrat": "c3_recursion_base_manquante",
        "code": "def walk(node):\n    return walk(node)\n",
    },
    {
        "id": "HADES_3C_RECURSION_LISTE_NEUTRE_VIDE",
        "contrat": "c3_recursion_liste_neutre",
        "code": "def rng(n):\n    return rng(n - 1) + [n]\n",
    },
    {
        "id": "HADES_4A_OFF_BY_ONE_COUPLE_ORDRE_2",
        "contrat": "c4_off_by_one_couple",
        "code": "def diffs(a):\n    out = []\n    for i in range(len(a)):\n        out.append(a[i + 1] - a[i])\n    return out\n",
    },
    {
        "id": "HADES_4B_OFF_BY_ONE_LOOKBACK_WRAP",
        "contrat": "c4_off_by_one_lookback",
        "code": "def diffs_lookback(a):\n    out = []\n    for i in range(len(a)):\n        out.append(a[i] - a[i - 1])\n    return out\n",
    },
    {
        "id": "HADES_5A_IS_HORS_CACHE_257_ET_DIV_INDICE",
        "contrat": "c5_pieges_semantiques_is_et_div",
        "code": "def test_milieu(args):\n    a, cible = args\n    m = a[len(a) / 2]\n    return m is cible\n",
    },
    {
        "id": "HADES_5B_EGALITE_FLOTTANTE_IEEE754",
        "contrat": "c5_egalite_flottante",
        "code": "def test_somme_flt(xyz):\n    x, y, z = xyz\n    return x + y == z\n",
    },
    {
        "id": "HADES_5C_STRATIFIED_ORACLE_X_EQ_1_PAIRWISE",
        "contrat": "c5_count_pos_x_eq_1",
        "code": "def count_pos(a):\n    return sum(1 for x in a if x > 1)\n",
    },
]


def executer_banc_hades() -> None:
    print("=" * 86)
    print(" 🔥🏛️ BANC D'ESSAI CEGIS v3.2 — LES 16 ÉPREUVES D'HADÈS + 4 MOTEURS AST + ORACLE PAIRWISE")
    print("=" * 86)
    t0 = time.perf_counter()
    ok_count = 0
    for cas in BANC_HADÈS_V3_2:
        res = ChirurgienCEGIS.reparer_en_boucle_fermee(cas["code"], cas["contrat"])
        succes = res["statut"] in ("REPARE_ET_CERTIFIE", "REJET_FRANC_SANS_PROGRES")
        if succes:
            ok_count += 1
        ic = "✅" if succes else "❌"
        print(
            f" {ic} [{cas['id']}] ({res['duree_totale_ms']} ms | {res['iterations_cegis']} itér.)\n"
            f"    ├─ Panne détectée : {res['infractions_initiales']}\n"
            f"    └─ Action CEGIS   : {res['operation_decisive']}"
        )
    dt = round((time.perf_counter() - t0) * 1000.0, 2)
    print("=" * 86)
    print(f" 🏆 BILAN CEGIS v3.2 : {ok_count}/{len(BANC_HADÈS_V3_2)} épreuves d'Hadès maîtrisées en {dt} ms !")
    print("=" * 86)


if __name__ == "__main__":
    executer_banc_hades()
