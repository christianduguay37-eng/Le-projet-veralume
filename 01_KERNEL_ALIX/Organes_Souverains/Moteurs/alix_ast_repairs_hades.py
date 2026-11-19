#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alix_ast_repairs_hades.py (ast_repairs.py) - quatre réécritures AST déterministes pour le Chirurgien CEGIS.
Python 3.11+, bibliothèque standard seulement, aucun appel LLM.
Sparring & Architecture : Hadès (Claude) × Christian Duguay & Alix (Panthéon K-SIL)

  1. AliasCopyRepair         def-use  `b = a` ... mut(b) ... lecture(a)  ->  copie 1D / 2D / dict / set
  2. sinking_candidates      générateur borné de candidats « init descendue dans une boucle »
  3. OffByOneNormalizer      a[i + c] -> a[i'] avec range décalé (lo + p, hi + p) et clippé à len(a)
  4. RecursionBaseCaseRepair insertion déterministe via table d'éléments neutres (0, 1, [], '', True, False)
                             + rejet journalisé (fib, max/min, sans progrès).
"""
from __future__ import annotations

import ast
import copy
import sys
from dataclasses import dataclass

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

__all__ = [
    "AliasCopyRepair", "repair_aliasing",
    "SinkCandidate", "sinking_candidates", "sinking_trees",
    "OffByOneNormalizer", "normalize_offbyone",
    "RecursionBaseCaseRepair", "repair_recursion",
]

# ----------------------------------------------------------------------------------------------
# Utilitaires communs
# ----------------------------------------------------------------------------------------------

_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
_LOOPS = (ast.For, ast.AsyncFor, ast.While)

LIST_MUT = frozenset({"append", "extend", "insert", "remove", "pop", "clear", "sort", "reverse"})
SET_MUT = frozenset({"add", "discard", "remove", "pop", "clear", "update", "difference_update",
                     "intersection_update", "symmetric_difference_update"})
DICT_MUT = frozenset({"update", "setdefault", "pop", "popitem", "clear"})
DEQUE_MUT = frozenset({"appendleft", "popleft", "extendleft", "rotate"})
MUTATORS = LIST_MUT | SET_MUT | DICT_MUT | DEQUE_MUT
LEN_MUT = frozenset({"append", "extend", "insert", "remove", "pop", "clear", "add", "discard",
                     "update", "setdefault", "popitem", "appendleft", "popleft", "extendleft"})


def _ordered(node):
    """Descendants dans l'ordre des champs (≈ ordre source), sans entrer dans les sous-portées."""
    for child in ast.iter_child_nodes(node):
        yield child
        if not isinstance(child, _SCOPES):
            yield from _ordered(child)


def _stmt_lists(node):
    for f in ("body", "orelse", "finalbody"):
        lst = getattr(node, f, None)
        if isinstance(lst, list) and lst and isinstance(lst[0], ast.stmt):
            yield lst


def _blocks(scope):
    """Toutes les listes d'instructions appartenant à `scope` (sous-portées exclues)."""
    nodes = [scope] + [n for n in _ordered(scope) if not isinstance(n, _SCOPES)]
    for n in nodes:
        yield from _stmt_lists(n)


def _all_blocks(tree):
    for n in ast.walk(tree):
        yield from _stmt_lists(n)


def _root(node):
    """b[i][j].x -> 'b' ; None si la racine n'est pas un Name (ex. b.copy()[0])."""
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _names(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _fresh(taken, stem):
    k = 0
    while f"{stem}{k}" in taken:
        k += 1
    name = f"{stem}{k}"
    taken.add(name)
    return name


# ----------------------------------------------------------------------------------------------
# 1) Aliasing def-use :  b = a ; mut(b) ; lecture(a)   ->   b = copie(a)
# ----------------------------------------------------------------------------------------------

@dataclass
class _Kind:
    kind: str          # 'list' | 'dict' | 'set'
    depth: int = 1     # profondeur d'imbrication des listes (2 = liste de listes)


def _value_kind(v):
    if isinstance(v, (ast.List, ast.ListComp)):
        inner = (v.elts[0] if v.elts else None) if isinstance(v, ast.List) else v.elt
        d = _value_kind(inner) if inner is not None else None
        return _Kind("list", 1 + (d.depth if d and d.kind == "list" else 0))
    if isinstance(v, ast.BinOp) and isinstance(v.op, ast.Mult):
        for side in (v.left, v.right):
            if isinstance(side, (ast.List, ast.ListComp)):
                return _value_kind(side)
    if isinstance(v, (ast.Dict, ast.DictComp)):
        return _Kind("dict")
    if isinstance(v, (ast.Set, ast.SetComp)):
        return _Kind("set")
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name):
        return {"list": _Kind("list"), "sorted": _Kind("list"),
                "dict": _Kind("dict"), "set": _Kind("set")}.get(v.func.id)
    return None


def _ann_kind(ann):
    d, n = 0, ann
    while isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id in ("list", "List"):
        d += 1
        n = n.slice
    if d:
        return _Kind("list", d)
    if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name):
        if n.value.id in ("dict", "Dict"):
            return _Kind("dict")
        if n.value.id in ("set", "Set"):
            return _Kind("set")
    return None


def _chain_depth(n):
    d = 0
    while isinstance(n, ast.Subscript):
        d += 1
        n = n.value
    return d, n


def _infer_kind(scope, names, default):
    """-> (_Kind, evident). `evident` = la nature conteneur est attestée (annotation, init, indexation)."""
    kind, sub = None, 0
    args = getattr(scope, "args", None)
    if args is not None:
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            if arg.arg in names and arg.annotation is not None:
                kind = kind or _ann_kind(arg.annotation)
    for n in _ordered(scope):
        if isinstance(n, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id in names for t in n.targets):
                kind = kind or _value_kind(n.value)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in names:
            kind = kind or _ann_kind(n.annotation) or (_value_kind(n.value) if n.value else None)
        elif isinstance(n, ast.Subscript):
            d, root = _chain_depth(n)
            if isinstance(root, ast.Name) and root.id in names:
                sub = max(sub, d)
        elif isinstance(n, ast.Attribute) and n.attr in LIST_MUT:
            d, root = _chain_depth(n.value)
            if d and isinstance(root, ast.Name) and root.id in names:
                sub = max(sub, d + 1)
    evident = kind is not None or sub > 0
    if kind is None:
        kind = _Kind(default, max(1, sub))
    elif kind.kind == "list":
        kind = _Kind("list", max(kind.depth, sub, 1))
    return kind, evident


@dataclass
class _Info:
    mut_b: bool = False
    reads_a: bool = False
    rebinds_a: bool = False
    rebinds_b: bool = False


def _stmt_info(stmt, a, b, container_b):
    info, aug_targets = _Info(), set()
    for n in ast.walk(stmt):
        if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            aug_targets.add(id(n.target))
            if n.target.id == b:
                if container_b:
                    info.mut_b = True
                else:
                    info.rebinds_b = True
            if n.target.id == a:
                info.reads_a = True
        elif isinstance(n, ast.Name):
            if id(n) in aug_targets:
                continue
            if n.id == a:
                if isinstance(n.ctx, ast.Load):
                    info.reads_a = True
                else:
                    info.rebinds_a = True
            elif n.id == b and not isinstance(n.ctx, ast.Load):
                info.rebinds_b = True
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr in MUTATORS and _root(f.value) == b:
                info.mut_b = True
        elif isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(n.ctx, (ast.Store, ast.Del)):
            if _root(n) == b:
                info.mut_b = True
    return info


def _needs_copy(block, i, a, b, container_b):
    """Automate à deux états sur les instructions suivant `b = a` dans le même bloc."""
    state = 0
    for s in block[i + 1:]:
        info = _stmt_info(s, a, b, container_b)
        if state == 0:
            if info.rebinds_a or info.rebinds_b:
                break
            if info.mut_b:
                if info.reads_a and isinstance(s, _LOOPS):
                    return True
                state = 1
        else:
            if info.reads_a:
                return True
            if info.rebinds_a:
                break
    return False


class AliasCopyRepair(ast.NodeTransformer):
    """`b = a` -> `b = a[:]` | `[r[:] for r in a]` | `{k: v for k, v in a.items()}` | `{x for x in a}`."""

    def __init__(self, default_kind: str = "list"):
        self.default_kind = default_kind
        self.log: list[dict] = []

    def visit_Module(self, node):
        self.generic_visit(node)
        self._repair_scope(node)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        self._repair_scope(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def _repair_scope(self, scope):
        taken = _names(scope)
        args = getattr(scope, "args", None)
        if args is not None:
            taken |= {x.arg for x in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
        for block in list(_blocks(scope)):
            for i, stmt in enumerate(block):
                if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name) and isinstance(stmt.value, ast.Name)):
                    continue
                b, a = stmt.targets[0].id, stmt.value.id
                if a == b:
                    continue
                kind, evident = _infer_kind(scope, {a, b}, self.default_kind)
                if not _needs_copy(block, i, a, b, container_b=evident):
                    continue
                new = self._build_copy(a, kind, taken)
                stmt.value = ast.copy_location(new, stmt.value)
                self.log.append({"rule": "alias-copy", "line": getattr(stmt, "lineno", None),
                                 "dst": b, "src": a, "kind": kind.kind, "depth": kind.depth})

    def _build_copy(self, name, kind, taken):
        load = lambda n: ast.Name(id=n, ctx=ast.Load())
        store = lambda n: ast.Name(id=n, ctx=ast.Store())
        if kind.kind == "dict":
            k, v = _fresh(taken, "_k"), _fresh(taken, "_v")
            return ast.DictComp(
                key=load(k), value=load(v),
                generators=[ast.comprehension(
                    target=ast.Tuple(elts=[store(k), store(v)], ctx=ast.Store()),
                    iter=ast.Call(func=ast.Attribute(value=load(name), attr="items", ctx=ast.Load()),
                                  args=[], keywords=[]),
                    ifs=[], is_async=0)])
        if kind.kind == "set":
            x = _fresh(taken, "_x")
            return ast.SetComp(elt=load(x),
                               generators=[ast.comprehension(target=store(x), iter=load(name), ifs=[], is_async=0)])
        return self._list_copy(load(name), kind.depth, taken)

    def _list_copy(self, src, depth, taken):
        if depth <= 1:
            return ast.Subscript(value=src, slice=ast.Slice(), ctx=ast.Load())
        var = _fresh(taken, "_r")
        inner = self._list_copy(ast.Name(id=var, ctx=ast.Load()), depth - 1, taken)
        return ast.ListComp(
            elt=inner,
            generators=[ast.comprehension(target=ast.Name(id=var, ctx=ast.Store()), iter=src, ifs=[], is_async=0)])


def repair_aliasing(tree, default_kind="list"):
    t = AliasCopyRepair(default_kind)
    out = t.visit(copy.deepcopy(tree))
    ast.fix_missing_locations(out)
    return out, t.log


# ----------------------------------------------------------------------------------------------
# 2) Sinking d'initialisation multi-niveaux : générateur de candidats
# ----------------------------------------------------------------------------------------------

_INIT_CALLS = frozenset({"set", "list", "dict", "tuple", "int", "float", "str", "bool", "deque"})


def _is_init_value(v):
    if isinstance(v, ast.Constant):
        return True
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, (ast.USub, ast.UAdd)):
        return _is_init_value(v.operand)
    if isinstance(v, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_init_value(e) for e in v.elts)
    if isinstance(v, ast.Dict):
        return all(k is not None and _is_init_value(k) and _is_init_value(x) for k, x in zip(v.keys, v.values))
    if isinstance(v, (ast.ListComp, ast.SetComp, ast.DictComp)):
        return True
    if isinstance(v, ast.BinOp) and isinstance(v.op, ast.Mult):
        return isinstance(v.left, (ast.List, ast.Tuple)) or isinstance(v.right, (ast.List, ast.Tuple))
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id in _INIT_CALLS:
        return not v.keywords and all(isinstance(x, ast.Constant) for x in v.args)
    return False


def _is_init_assign(s):
    return (isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name)
            and _is_init_value(s.value))


def _stores(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Load)}


def _free_loads(value):
    bound = _stores(value)
    return {n.id for n in ast.walk(value) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)} - bound


def _loops_using(stmts, v):
    for s in stmts:
        if isinstance(s, _LOOPS):
            if v in _names(s):
                yield s
        elif isinstance(s, _SCOPES):
            continue
        else:
            for lst in _stmt_lists(s):
                yield from _loops_using(lst, v)
            for h in getattr(s, "handlers", []):
                yield from _loops_using(h.body, v)


def _walk_loops(loop, v, level=1, parent=None):
    yield loop, level, parent
    for child in _loops_using(loop.body, v):
        yield from _walk_loops(child, v, level + 1, loop)


def _sites(tree):
    for block in _all_blocks(tree):
        for i, stmt in enumerate(block):
            if not _is_init_assign(stmt):
                continue
            v = stmt.targets[0].id
            k = i + 1
            while k < len(block) and _is_init_assign(block[k]) and v not in _names(block[k]):
                k += 1
            if k >= len(block) or not isinstance(block[k], _LOOPS):
                continue
            loop = block[k]
            if v not in _names(loop):
                continue
            if _free_loads(stmt.value) & _stores(loop):
                continue
            after = any(isinstance(n, ast.Name) and n.id == v and isinstance(n.ctx, ast.Load)
                        for s in block[k + 1:] for n in ast.walk(s))
            yield stmt, loop, (1 if after else 0)


class _SinkOne(ast.NodeTransformer):
    def __init__(self, init_stmt, owner_sid, before_sid):
        self.init, self.owner, self.before = init_stmt, owner_sid, before_sid

    def generic_visit(self, node):
        super().generic_visit(node)
        sid = getattr(node, "_sid", None)
        for f in ("body", "orelse", "finalbody"):
            lst = getattr(node, f, None)
            if not (isinstance(lst, list) and lst and isinstance(lst[0], ast.stmt)):
                continue
            here = sid is not None and sid == self.owner and f == "body"
            new = []
            if here and self.before is None:
                new.append(copy.deepcopy(self.init))
            for s in lst:
                s_sid = getattr(s, "_sid", None)
                if s_sid == self.init._sid:
                    continue
                if here and self.before is not None and s_sid == self.before:
                    new.append(copy.deepcopy(self.init))
                new.append(s)
            setattr(node, f, new or [ast.Pass()])
        return node


def _strip(tree):
    for n in ast.walk(tree):
        n.__dict__.pop("_sid", None)


@dataclass
class SinkCandidate:
    tree: ast.Module
    var: str
    level: int
    placement: str
    priority: int
    note: str

    def source(self) -> str:
        return ast.unparse(self.tree)


def sinking_candidates(tree) -> list[SinkCandidate]:
    base = copy.deepcopy(tree)
    for n, node in enumerate(ast.walk(base)):
        if isinstance(node, ast.stmt):
            node._sid = n
    jobs = []
    for init, loop, prio in _sites(base):
        v = init.targets[0].id
        for lp, level, parent in _walk_loops(loop, v):
            jobs.append((init, lp._sid, None, level, "head", prio, v))
            if parent is not None and any(c is lp for c in parent.body):
                jobs.append((init, parent._sid, lp._sid, level - 1, "adjacent", prio, v))
    out, seen = [], set()
    for init, owner, before, level, placement, prio, v in jobs:
        clone = copy.deepcopy(base)
        _SinkOne(init, owner, before).visit(clone)
        _strip(clone)
        ast.fix_missing_locations(clone)
        key = ast.dump(clone)
        if key in seen:
            continue
        seen.add(key)
        where = "tête du corps" if placement == "head" else "juste avant la boucle enfant"
        out.append(SinkCandidate(clone, v, level, placement, prio,
                                 f"`{v}` réinitialisée : {where} de la boucle de niveau {level}"))
    out.sort(key=lambda c: (c.priority, c.level, c.placement != "head"))
    return out


def sinking_trees(tree) -> list[ast.AST]:
    return [c.tree for c in sinking_candidates(tree)]


# ----------------------------------------------------------------------------------------------
# 3) Off-by-one couplés : a[i + c]  ->  a[i'] , range(lo + p, hi + p) clippé à len(a)
# ----------------------------------------------------------------------------------------------

def _linear(e, i):
    if isinstance(e, ast.Name):
        return (1, 0) if e.id == i else None
    if isinstance(e, ast.Constant) and type(e.value) is int:
        return (0, e.value)
    if isinstance(e, ast.UnaryOp) and isinstance(e.op, (ast.USub, ast.UAdd)):
        r = _linear(e.operand, i)
        if r is None:
            return None
        s = -1 if isinstance(e.op, ast.USub) else 1
        return (s * r[0], s * r[1])
    if isinstance(e, ast.BinOp) and isinstance(e.op, (ast.Add, ast.Sub)):
        l, r = _linear(e.left, i), _linear(e.right, i)
        if l is None or r is None:
            return None
        s = 1 if isinstance(e.op, ast.Add) else -1
        return (l[0] + s * r[0], l[1] + s * r[1])
    return None


def _offset(e, i):
    r = _linear(e, i)
    return r[1] if r is not None and r[0] == 1 else None


def _split(e):
    if isinstance(e, ast.Constant) and type(e.value) is int:
        return None, e.value
    if isinstance(e, ast.BinOp) and isinstance(e.op, (ast.Add, ast.Sub)):
        sign = 1 if isinstance(e.op, ast.Add) else -1
        if isinstance(e.right, ast.Constant) and type(e.right.value) is int:
            base, c = _split(e.left)
            return base, c + sign * e.right.value
        if isinstance(e.op, ast.Add) and isinstance(e.left, ast.Constant) and type(e.left.value) is int:
            base, c = _split(e.right)
            return base, c + e.left.value
    return e, 0


def _mk(base, c):
    if base is None:
        return ast.Constant(c)
    base = copy.deepcopy(base)
    if c == 0:
        return base
    return ast.BinOp(left=base, op=ast.Add() if c > 0 else ast.Sub(), right=ast.Constant(abs(c)))


def _combine(terms, fn):
    groups: dict[str, tuple] = {}
    for base, c in terms:
        key = "" if base is None else ast.dump(base)
        groups[key] = (base, fn(groups[key][1], c)) if key in groups else (base, c)
    exprs = [_mk(b, c) for b, c in groups.values()]
    if len(exprs) == 1:
        return exprs[0]
    return ast.Call(func=ast.Name(id=fn.__name__, ctx=ast.Load()), args=exprs, keywords=[])


def _changes_length(nodes, seq):
    for n in nodes:
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in LEN_MUT \
                and _root(n.func.value) == seq:
            return True
        if isinstance(n, ast.Delete) and any(_root(t) == seq for t in n.targets):
            return True
        if isinstance(n, ast.Name) and n.id == seq and not isinstance(n.ctx, ast.Load):
            return True
    return False


class _ShiftRewriter(ast.NodeTransformer):
    def __init__(self, i, p, seqs):
        self.i, self.p, self.seqs = i, p, seqs

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.seqs:
            c = _offset(node.slice, self.i)
            if c is not None:
                idx = _mk(ast.Name(id=self.i, ctx=ast.Load()), c - self.p)
                return ast.copy_location(ast.Subscript(value=node.value, slice=idx, ctx=node.ctx), node)
        return self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == self.i and isinstance(node.ctx, ast.Load):
            return ast.copy_location(_mk(ast.Name(id=self.i, ctx=ast.Load()), -self.p), node)
        return node


class OffByOneNormalizer(ast.NodeTransformer):
    def __init__(self, check_post_use: bool = True):
        self.check_post_use = check_post_use
        self.log: list[dict] = []
        self._scopes: list[ast.AST] = []

    def _enter(self, node):
        self._scopes.append(node)
        self.generic_visit(node)
        self._scopes.pop()
        return node

    visit_Module = visit_FunctionDef = visit_AsyncFunctionDef = _enter

    def visit_For(self, node):
        self.generic_visit(node)
        return self._normalize(node) or node

    def _used_after(self, node, i):
        scope = self._scopes[-1] if self._scopes else None
        end = getattr(node, "end_lineno", None)
        if scope is None or end is None:
            return True
        return any(isinstance(n, ast.Name) and n.id == i and isinstance(n.ctx, ast.Load)
                   and getattr(n, "lineno", 0) > end for n in _ordered(scope))

    def _normalize(self, node):
        it = node.iter
        if not (isinstance(node.target, ast.Name) and isinstance(it, ast.Call)
                and isinstance(it.func, ast.Name) and it.func.id == "range" and not it.keywords):
            return None
        a = it.args
        if len(a) == 1:
            lo, hi = ast.Constant(0), a[0]
        elif len(a) == 2:
            lo, hi = a
        elif len(a) == 3 and isinstance(a[2], ast.Constant) and a[2].value == 1:
            lo, hi = a[0], a[1]
        else:
            return None
        i = node.target.id
        body_nodes = [n for s in node.body for n in ast.walk(s)]
        if any(isinstance(n, ast.Name) and n.id == i and not isinstance(n.ctx, ast.Load) for n in body_nodes):
            return None
        if any(isinstance(n, ast.ExceptHandler) and n.name == i for n in body_nodes):
            return None
        offs: dict[str, set[int]] = {}
        for n in body_nodes:
            if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name):
                c = _offset(n.slice, i)
                if c is not None:
                    offs.setdefault(n.value.id, set()).add(c)
        if not offs or all(c == 0 for cs in offs.values() for c in cs):
            return None
        if any(_changes_length(body_nodes, s) for s in offs):
            return None
        p = max(c for cs in offs.values() for c in cs)
        if p != 0 and self.check_post_use and self._used_after(node, i):
            return None

        rw = _ShiftRewriter(i, p, set(offs))
        new_body = [rw.visit(s) for s in node.body]

        lo_b, lo_c = _split(lo)
        hi_b, hi_c = _split(hi)
        seqs = sorted(offs)
        lo_terms = [(lo_b, lo_c + p)] + [(None, p - min(offs[s])) for s in seqs]
        hi_terms = [(hi_b, hi_c + p)] + [
            (ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[ast.Name(id=s, ctx=ast.Load())], keywords=[]),
             p - max(offs[s])) for s in seqs]
        lo_e, hi_e = _combine(lo_terms, max), _combine(hi_terms, min)
        args = [hi_e] if isinstance(lo_e, ast.Constant) and lo_e.value == 0 else [lo_e, hi_e]

        new = ast.For(target=ast.Name(id=i, ctx=ast.Store()),
                      iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()), args=args, keywords=[]),
                      body=new_body, orelse=node.orelse, type_comment=None)
        ast.copy_location(new, node)
        self.log.append({"rule": "offbyone-shift", "line": getattr(node, "lineno", None), "var": i,
                         "pivot": p, "offsets": {s: sorted(offs[s]) for s in seqs}})
        return new


def normalize_offbyone(tree, check_post_use=True):
    t = OffByOneNormalizer(check_post_use)
    out = t.visit(copy.deepcopy(tree))
    ast.fix_missing_locations(out)
    return out, t.log


# ----------------------------------------------------------------------------------------------
# 4) Récursion sans cas de base : insertion déterministe via table d'éléments neutres
# ----------------------------------------------------------------------------------------------

_NEUTRAL = {ast.Add: 0, ast.Mult: 1, ast.BitOr: 0, ast.BitXor: 0}


class RecursionBaseCaseRepair(ast.NodeTransformer):
    """def f(n): return n + f(n - 1)  ->  insère `if n <= 0: return <neutre>` en tête."""

    def __init__(self):
        self.log: list[dict] = []

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        self._repair(node)
        return node

    def _reject(self, fn, why):
        self.log.append({"rule": "recursion-base", "fn": fn.name, "applied": False, "why": why})

    def _repair(self, fn):
        calls = [n for n in _ordered(fn) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == fn.name]
        if not calls:
            return
        if len(calls) != 1:
            return self._reject(fn, "plusieurs appels récursifs : cas de base multiples requis")
        call = calls[0]
        params = [a.arg for a in [*fn.args.posonlyargs, *fn.args.args]]
        measure = None
        for idx, arg in enumerate(call.args):
            if (idx < len(params) and isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Sub)
                    and isinstance(arg.left, ast.Name) and arg.left.id == params[idx]
                    and isinstance(arg.right, ast.Constant) and type(arg.right.value) is int and arg.right.value > 0):
                measure = params[idx]
                break
        if measure is None:
            return self._reject(fn, "aucun argument ne décroît strictement (p - c) : pas de réparation déterministe")
        for s in fn.body:
            if isinstance(s, ast.If) and measure in _names(s.test) \
                    and any(isinstance(n, ast.Return) for n in ast.walk(s)):
                return self._reject(fn, "garde de terminaison déjà présente")
        if any(isinstance(n, ast.IfExp) and measure in _names(n.test) for n in _ordered(fn)):
            return self._reject(fn, "garde ternaire déjà présente")
        neutral = None
        for n in _ordered(fn):
            if not (isinstance(n, ast.Return) and n.value is not None):
                continue
            v = n.value
            if isinstance(v, ast.BinOp) and type(v.op) in _NEUTRAL and (v.left is call or v.right is call):
                other = v.right if v.left is call else v.left
                if isinstance(other, (ast.List, ast.ListComp)):
                    neutral = ast.List(elts=[], ctx=ast.Load())
                elif isinstance(other, ast.Constant) and isinstance(other.value, str):
                    neutral = ast.Constant("")
                else:
                    neutral = ast.Constant(_NEUTRAL[type(v.op)])
            elif isinstance(v, ast.BoolOp) and any(x is call for x in v.values):
                neutral = ast.Constant(isinstance(v.op, ast.And))
            if neutral is not None:
                break
        if neutral is None:
            return self._reject(fn, "combinateur sans élément neutre (max/min/appel nu) : rejet")
        guard = ast.If(test=ast.Compare(left=ast.Name(id=measure, ctx=ast.Load()), ops=[ast.LtE()],
                                        comparators=[ast.Constant(0)]),
                       body=[ast.Return(value=neutral)], orelse=[])
        doc = (fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant)
               and isinstance(fn.body[0].value.value, str))
        fn.body.insert(1 if doc else 0, ast.copy_location(guard, fn))
        self.log.append({"rule": "recursion-base", "fn": fn.name, "applied": True, "measure": measure})

    visit_AsyncFunctionDef = visit_FunctionDef


def repair_recursion(tree):
    t = RecursionBaseCaseRepair()
    out = t.visit(copy.deepcopy(tree))
    ast.fix_missing_locations(out)
    return out, t.log


# ----------------------------------------------------------------------------------------------
# Auto-test
# ----------------------------------------------------------------------------------------------

def _exec(src, fn, *args):
    ns: dict = {}
    exec(compile(src, "<repair>", "exec"), ns)
    return ns[fn](*args)


def _selftest(verbose=True):
    say = print if verbose else (lambda *a, **k: None)

    # 1) aliasing 2D : la boucle lit grid après avoir muté out (arête de retour)
    src = ("def smooth(grid):\n    out = grid\n    for i in range(len(grid)):\n"
           "        for j in range(1, len(grid[0])):\n            out[i][j] = grid[i][j] + grid[i][j - 1]\n"
           "    return out\n")
    fixed, log = repair_aliasing(ast.parse(src))
    code = ast.unparse(fixed)
    say("--- alias 2D ---\n" + code, log)
    assert _exec(src, "smooth", [[1, 2, 3]]) == [[1, 3, 6]]
    assert _exec(code, "smooth", [[1, 2, 3]]) == [[1, 3, 5]]

    # 1b) aliasing 1D : mutation de b puis lecture de a
    src = "def f(a):\n    b = a\n    b.append(1)\n    return a\n"
    fixed, log = repair_aliasing(ast.parse(src))
    assert "b = a[:]" in ast.unparse(fixed), ast.unparse(fixed)
    assert _exec(ast.unparse(fixed), "f", [0]) == [0]

    # 1c) alias volontaire : pas de lecture de a après -> aucun changement
    src = "def h(a):\n    b = a\n    b.append(1)\n    return b\n"
    fixed, log = repair_aliasing(ast.parse(src))
    assert ast.unparse(fixed) == ast.unparse(ast.parse(src)) and not log

    # 1d) alias rompu avant mutation -> aucun changement
    src = "def h(a):\n    b = a\n    b = b + [1]\n    b.append(2)\n    return a\n"
    assert not repair_aliasing(ast.parse(src))[1]

    # 2) sinking : cur doit être remise à zéro à chaque ligne
    src = ("def row_max_sum(grid):\n    best = 0\n    cur = 0\n    for row in grid:\n"
           "        for x in row:\n            cur += x\n        best = max(best, cur)\n    return best\n")
    cands = sinking_candidates(ast.parse(src))
    say(f"--- sinking : {len(cands)} candidats ---")
    good = [c for c in cands if _exec(c.source(), "row_max_sum", [[1, 2], [3, 4]]) == 7]
    for c in cands:
        say(f"[prio {c.priority} niv {c.level} {c.placement:8}] {c.note}")
    assert _exec(src, "row_max_sum", [[1, 2], [3, 4]]) == 10
    assert good and good[0].var == "cur" and good[0].level == 1 and good[0].placement == "head"
    say("candidat retenu :\n" + good[0].source())

    # 3) off-by-one couplé
    src = "def diffs(a):\n    n = len(a)\n    out = []\n    for i in range(n):\n        out.append(a[i + 1] - a[i])\n    return out\n"
    fixed, log = normalize_offbyone(ast.parse(src))
    code = ast.unparse(fixed)
    say("--- off-by-one (a[i+1]) ---\n" + code, log)
    try:
        _exec(src, "diffs", [1, 4, 9])
        raise AssertionError("le bug d'origine aurait dû lever IndexError")
    except IndexError:
        pass
    assert _exec(code, "diffs", [1, 4, 9]) == [3, 5]
    assert _exec(code, "diffs", [7]) == [] and _exec(code, "diffs", []) == []

    # 3b) lookback a[i-1] (wrap silencieux sur a[-1])
    src = "def d2(a):\n    out = []\n    for i in range(len(a)):\n        out.append(a[i] - a[i - 1])\n    return out\n"
    fixed, _ = normalize_offbyone(ast.parse(src))
    code = ast.unparse(fixed)
    say("--- off-by-one (a[i-1]) ---\n" + code)
    assert _exec(src, "d2", [1, 4, 9]) == [-8, 3, 5]
    assert _exec(code, "d2", [1, 4, 9]) == [3, 5]

    # 3c) autres usages de i + plusieurs séquences
    src = ("def g(a, n):\n    out = [0] * n\n    for i in range(n):\n"
           "        out[i] = a[i + 1] - a[i]\n    return out\n")
    fixed, _ = normalize_offbyone(ast.parse(src))
    code = ast.unparse(fixed)
    say("--- off-by-one (autres usages de i) ---\n" + code)
    assert _exec(code, "g", [1, 4, 9], 3) == [3, 5, 0]

    # 3d) i relue après la boucle -> refus
    src = "def k(a):\n    for i in range(len(a)):\n        x = a[i + 1]\n    return i\n"
    assert not normalize_offbyone(ast.parse(src))[1]

    # 4) récursion sans cas de base
    src = "def total(n):\n    return n + total(n - 1)\n"
    fixed, log = repair_recursion(ast.parse(src))
    code = ast.unparse(fixed)
    say("--- récursion ---\n" + code, log)
    assert _exec(code, "total", 4) == 10 and _exec(code, "total", 0) == 0
    src = "def rng(n):\n    return rng(n - 1) + [n]\n"
    assert _exec(ast.unparse(repair_recursion(ast.parse(src))[0]), "rng", 3) == [1, 2, 3]
    src = "def fact(n):\n    return n * fact(n - 1)\n"
    assert _exec(ast.unparse(repair_recursion(ast.parse(src))[0]), "fact", 5) == 120
    for bad in ("def fib(n):\n    return fib(n - 1) + fib(n - 2)\n",
                "def m(n):\n    return max(n, m(n - 1))\n",
                "def w(n):\n    return w(n)\n",
                "def ok(n):\n    if n <= 0:\n        return 0\n    return n + ok(n - 1)\n"):
        _, lg = repair_recursion(ast.parse(bad))
        assert lg and not lg[0]["applied"], bad

    say("\n✅ OK : tous les tests passent (AliasCopyRepair, Sinking, OffByOneNormalizer, RecursionBaseCaseRepair).")


if __name__ == "__main__":
    _selftest()
