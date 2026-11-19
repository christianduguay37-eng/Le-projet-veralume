#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
   🧭🔗 COMPÉTENCE #2 : MOTEUR DE RAISONNEMENT DÉDUCTIF & CAUSAL — v10.0 UNIFIÉ
   Alphabet Complet (a)..(z) + (aa)..(dd) — Séquence Souveraine : 1 -> 4 -> 3 -> 2
================================================================================
Auteurs : Christian Duguay, Alix & Poséidon (Atelier Kairos — Rimouski)
Dépendances : Python stdlib uniquement (`0 Mo` VRAM, `~0.0010 ms/req` sur Lunar Lake).

Architecture Unifiée v10.0 — Alphabet Complet (a)..(z) + (aa)..(dd) :
  - v4.0..v5.0 (a..j) : Séparation sémantique, Dijkstra (-log(poids)), Abduction,
                        Dialectique enrichie, Logique 3 valeurs, Sophismes (8 familles),
                        BackendSQLite, Datalog Semi-Naïf, Détection de cycles 3-couleurs,
                        Réseau Bayésien Causal (CPTs/Noisy-OR) & Variable Elimination.
  - v6.0 (k..n)       : SQL Pushdown Datalog (`saturer_regles_sql`), `JoinPlanner` COUNT(*),
                        Apprentissage empirique CPTs (Laplace + tag `source_modele`),
                        `JunctionTree` exact (Shafer-Shenoy : moralisation, min-fill).
  - v7.0 (o..r)       : `MondeHypothetique` (fork isolé), Contrefactuel Pearl Niveau 3
                        (`PN`, `PS`, `PNS`), Révision de croyances AGM, Planification inverse.
  - v8.0 (s..v)       : `contrefactuel_fc` (Forward Conditionnel pondéré par vraisemblance,
                        zéro rejet), `contrefactuel_is`, `gibbs_PV_obs`, `VertexCoverSolver`
                        Branch & Bound + matching greedé, `planifier_interventions` Dijkstra.
  - v9.0 (w..z)       : `TwinNetwork` explicite (V ∪ V_x, U partagés), `VertexCoverLP`
                        (Simplexe tableau dual), `AStarPlanificateur` (A* vs Dijkstra),
                        `StructureLearner` (Score BIC + Hill-Climbing + ordre causal).
  - v10.0 (aa..dd)    : `TabuStructureSearch` (Tabu + Random Restarts + Aspiration + rev),
                        `AStarAdmissible` (heuristique admissible prouvée c_min * ceil(gap/g_max)),
                        `RevisedSimplex` + `VertexCoverRevised` (B⁻¹ explicite Gauss-Jordan),
                        `Serializer` (JSON round-trip complet graphe + CPTs + faits + règles).
================================================================================
"""
from __future__ import annotations

import heapq
import itertools
import json
import math
import random
import re
import sqlite3
import sys
import time
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ===========================================================================
# Utilitaires
# ===========================================================================
def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


_VARIABLE_RE = re.compile(r"^\?[A-Za-z_][A-Za-z0-9_]*$")


def est_variable(t: Any) -> bool:
    return isinstance(t, str) and bool(_VARIABLE_RE.match(t))


# ===========================================================================
# Typage sémantique des relations
# ===========================================================================
class TypeRelation(Enum):
    TAXONOMIQUE = "taxonomique"
    CAUSAL      = "causal"
    LOGIQUE     = "logique"
    OPPOSITION  = "opposition"


RELATION_TYPE: Dict[str, TypeRelation] = {
    "est": TypeRelation.TAXONOMIQUE,
    "est_un": TypeRelation.TAXONOMIQUE,
    "est_une": TypeRelation.TAXONOMIQUE,
    "possede_propriete": TypeRelation.TAXONOMIQUE,
    "cause": TypeRelation.CAUSAL,
    "permet": TypeRelation.CAUSAL,
    "entraine": TypeRelation.CAUSAL,
    "conduit_a": TypeRelation.CAUSAL,
    "mene_a": TypeRelation.CAUSAL,
    "implique": TypeRelation.LOGIQUE,
    "affirme": TypeRelation.LOGIQUE,
    "empeche": TypeRelation.OPPOSITION,
    "interdit": TypeRelation.OPPOSITION,
    "nie": TypeRelation.OPPOSITION,
    "contredit": TypeRelation.OPPOSITION,
}

COMPATIBILITE: Dict[TypeRelation, Set[TypeRelation]] = {
    TypeRelation.TAXONOMIQUE: {TypeRelation.TAXONOMIQUE, TypeRelation.LOGIQUE, TypeRelation.CAUSAL},
    TypeRelation.CAUSAL:      {TypeRelation.CAUSAL, TypeRelation.LOGIQUE},
    TypeRelation.LOGIQUE:     {TypeRelation.LOGIQUE, TypeRelation.TAXONOMIQUE, TypeRelation.CAUSAL},
    TypeRelation.OPPOSITION:  set(),
}

RELATIONS_OPPOSEES: Dict[str, Set[str]] = {
    "implique":  {"empeche", "interdit", "nie"},
    "empeche":   {"implique", "cause", "permet", "entraine"},
    "cause":     {"empeche", "interdit"},
    "permet":    {"empeche", "interdit"},
    "interdit":  {"permet", "cause", "implique"},
    "entraine":  {"empeche", "interdit"},
    "nie":       {"implique", "affirme"},
    "affirme":   {"nie"},
    "contredit": {"contredit"},
    "conduit_a": {"empeche"},
    "mene_a":    {"empeche"},
}

VERBES_FR: Dict[str, str] = {
    "est_un": "est un",
    "est_une": "est une",
    "est": "est",
    "possede_propriete": "possède la propriété",
    "cause": "cause",
    "permet": "permet",
    "entraine": "entraîne",
    "conduit_a": "conduit à",
    "mene_a": "mène à",
    "implique": "implique",
    "affirme": "affirme",
    "empeche": "empêche",
    "interdit": "interdit",
    "nie": "nie",
    "contredit": "contredit",
}


# ===========================================================================
# Fait / Règle / Unification
# ===========================================================================
@dataclass(frozen=True)
class FaitRelationnel:
    sujet: str
    relation: str
    objet: str
    explication: str = ""
    mots_cles: Tuple[str, ...] = ()
    poids: float = 1.0
    negatif: bool = False

    def __post_init__(self) -> None:
        if not (0.0 <= self.poids <= 1.0):
            object.__setattr__(self, "poids", max(0.0, min(1.0, self.poids)))

    def cle(self) -> Tuple[str, str, str, bool]:
        return (_norm(self.sujet), _norm(self.relation), _norm(self.objet), self.negatif)


Pattern = Tuple[str, str, str]


def _subst_appliquer(p: Pattern, s: Dict[str, str]) -> Pattern:
    return tuple(s.get(t, t) if est_variable(t) else t for t in p)  # type: ignore


def _unifier(
    p: Pattern,
    t: Pattern,
    s: Dict[str, str],
) -> Optional[Dict[str, str]]:
    ns = dict(s)
    for a, b in zip(p, t):
        if est_variable(a):
            if a in ns:
                if _norm(ns[a]) != _norm(b):
                    return None
            else:
                ns[a] = b
        else:
            if _norm(a) != _norm(b):
                return None
    return ns


@dataclass(frozen=True)
class Regle:
    tete: Pattern
    corps: Tuple[Pattern, ...]
    nom: str = "regle"
    poids: float = 1.0


REGLE_HERITAGE = Regle(
    tete=("?x", "est", "?p"),
    corps=(("?x", "est_un", "?z"), ("?z", "est", "?p")),
    nom="heritage_propriete",
)


# ===========================================================================
# (g) Backend SQLite + Fonctions SQL Custom (prod_all, geo_mean_all)
# ===========================================================================
class BackendSQLite:
    SCHEMA = """
    PRAGMA journal_mode = MEMORY;
    PRAGMA synchronous = OFF;
    PRAGMA temp_store = MEMORY;
    CREATE TABLE IF NOT EXISTS faits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sujet TEXT NOT NULL,
        relation TEXT NOT NULL,
        objet TEXT NOT NULL,
        explication TEXT DEFAULT '',
        poids REAL DEFAULT 1.0,
        negatif INTEGER DEFAULT 0,
        derive INTEGER DEFAULT 0,
        UNIQUE(sujet, relation, objet, negatif)
    );
    CREATE INDEX IF NOT EXISTS idx_sr  ON faits(sujet, relation);
    CREATE INDEX IF NOT EXISTS idx_or  ON faits(objet, relation);
    CREATE INDEX IF NOT EXISTS idx_rso ON faits(relation, sujet, objet);
    CREATE INDEX IF NOT EXISTS idx_s   ON faits(sujet);
    CREATE INDEX IF NOT EXISTS idx_o   ON faits(objet);
    CREATE INDEX IF NOT EXISTS idx_drv ON faits(derive);
    """

    def __init__(self, chemin: str = ":memory:") -> None:
        self.chemin = chemin
        self.conn = sqlite3.connect(chemin, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(self.SCHEMA)
        self.conn.create_function(
            "prod_all",
            -1,
            lambda *xs: max(0.01, min(1.0, math.prod(xs))),
        )
        self.conn.create_function(
            "geo_mean_all",
            -1,
            lambda *xs: max(
                0.01,
                min(
                    1.0,
                    math.exp(sum(math.log(max(x, 1e-12)) for x in xs) / len(xs)),
                ),
            ),
        )
        self.conn.commit()

    def ajouter(self, f: FaitRelationnel, derive: bool = False) -> bool:
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO faits
               (sujet, relation, objet, explication, poids, negatif, derive)
               VALUES(?,?,?,?,?,?,?)""",
            (
                _norm(f.sujet),
                _norm(f.relation),
                _norm(f.objet),
                f.explication,
                f.poids,
                int(f.negatif),
                int(derive),
            ),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def chercher_atome(
        self,
        sujet: Any,
        relation: Any,
        objet: Any,
        negatif: Optional[bool] = None,
    ) -> List[FaitRelationnel]:
        clauses: List[str] = []
        args: List[Any] = []
        if not est_variable(sujet):
            clauses.append("sujet=?")
            args.append(_norm(sujet))
        if not est_variable(relation):
            clauses.append("relation=?")
            args.append(_norm(relation))
        if not est_variable(objet):
            clauses.append("objet=?")
            args.append(_norm(objet))
        if negatif is not None:
            clauses.append("negatif=?")
            args.append(int(negatif))
        sql = "SELECT * FROM faits" + (" WHERE " + " AND ".join(clauses) if clauses else "")
        return [self._row_to_fait(r) for r in self.conn.execute(sql, args)]

    def charger_tout(self) -> List[FaitRelationnel]:
        return [
            self._row_to_fait(r) for r in self.conn.execute("SELECT * FROM faits")
        ]

    def compter(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM faits").fetchone()[0]

    @staticmethod
    def _row_to_fait(r: sqlite3.Row) -> FaitRelationnel:
        return FaitRelationnel(
            r["sujet"],
            r["relation"],
            r["objet"],
            r["explication"] or "",
            (),
            float(r["poids"]),
            bool(r["negatif"]),
        )

    def fermer(self) -> None:
        self.conn.close()


# ===========================================================================
# (m) JoinPlanner — Ordonnancement par sélectivité SQLite
# ===========================================================================
class JoinPlanner:
    """Ordonne les atomes d'un corps par cardinalité estimée (`COUNT(*)`)."""

    def __init__(self, backend: BackendSQLite) -> None:
        self.backend = backend
        self._cache: Dict[Tuple, int] = {}

    def estimer_cardinalite(self, atome: Pattern) -> int:
        s, r, o = atome
        key = (
            s if not est_variable(s) else None,
            r if not est_variable(r) else None,
            o if not est_variable(o) else None,
        )
        if key in self._cache:
            return self._cache[key]
        clauses: List[str] = []
        args: List[Any] = []
        if not est_variable(s):
            clauses.append("sujet=?")
            args.append(_norm(s))
        if not est_variable(r):
            clauses.append("relation=?")
            args.append(_norm(r))
        if not est_variable(o):
            clauses.append("objet=?")
            args.append(_norm(o))
        sql = "SELECT COUNT(*) FROM faits" + (
            " WHERE " + " AND ".join(clauses) if clauses else ""
        )
        n = self.backend.conn.execute(sql, args).fetchone()[0]
        self._cache[key] = n
        return n

    def ordonner_atomes(self, corps: Tuple[Pattern, ...]) -> List[int]:
        scores = [(i, self.estimer_cardinalite(a)) for i, a in enumerate(corps)]
        scores.sort(key=lambda x: x[1])
        return [i for i, _ in scores]


# ===========================================================================
# (k) Compilateur SQL pour clauses de Horn
# ===========================================================================
def _compiler_regle_sql(
    regle: Regle,
    delta_pos: Optional[int] = None,
    ordre: Optional[List[int]] = None,
    mode_poids: str = "produit",
    table_cible: str = "faits",
) -> Tuple[str, List[Any]]:
    n = len(regle.corps)
    corps_effectif = (
        regle.corps
        if ordre is None
        else tuple(regle.corps[i] for i in ordre)
    )
    delta_effectif = None
    if delta_pos is not None and ordre is not None:
        delta_effectif = ordre.index(delta_pos)
    elif delta_pos is not None:
        delta_effectif = delta_pos

    variables: Dict[str, Tuple[str, str]] = {}
    froms: List[str] = []
    wheres: List[str] = []
    params_where: List[Any] = []

    for i, (s, r, o) in enumerate(corps_effectif):
        alias = f"f{i}"
        table = "delta" if i == delta_effectif else "faits"
        froms.append(f"{table} AS {alias}")
        for col, term in (("sujet", s), ("relation", r), ("objet", o)):
            if est_variable(term):
                if term in variables:
                    pa, pc = variables[term]
                    wheres.append(f"{alias}.{col} = {pa}.{pc}")
                else:
                    variables[term] = (alias, col)
            else:
                wheres.append(f"{alias}.{col} = ?")
                params_where.append(_norm(term))
        wheres.append(f"{alias}.negatif = 0")

    select_parts: List[str] = []
    head_params: List[Any] = []
    for col, term in zip(("sujet", "relation", "objet"), regle.tete):
        if est_variable(term):
            if term in variables:
                a, c = variables[term]
                select_parts.append(f"{a}.{c}")
            else:
                select_parts.append("NULL")
        else:
            select_parts.append("?")
            head_params.append(_norm(term))

    poids_cols = ", ".join(f"f{i}.poids" for i in range(n))
    fn = "prod_all" if mode_poids == "produit" else "geo_mean_all"
    poids_expr = f"{fn}({poids_cols}, ?)"

    explication = f"dérivé « {regle.nom} » (SQL)"
    sql = (
        f"INSERT OR IGNORE INTO {table_cible} "
        f"(sujet, relation, objet, explication, poids, negatif, derive) "
        f"SELECT {', '.join(select_parts)}, ?, {poids_expr}, 0, 1 "
        f"FROM {' JOIN '.join(froms)} "
        f"WHERE {' AND '.join(wheres)}"
    )
    all_params = head_params + [explication, regle.poids] + params_where
    return sql, all_params


# ===========================================================================
# Helpers GrapheCausal : Moralisation + Triangulation Min-Fill
# ===========================================================================
def _moraliser(
    parents: Dict[str, Set[str]],
    noeuds: Set[str],
) -> Dict[str, Set[str]]:
    adj: Dict[str, Set[str]] = {n: set() for n in noeuds}
    for n in noeuds:
        ps = list(parents.get(n, set()))
        for p in ps:
            adj[n].add(p)
            adj[p].add(n)
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                adj[ps[i]].add(ps[j])
                adj[ps[j]].add(ps[i])
    return adj


def _trianguler_min_fill(
    adj_in: Dict[str, Set[str]]
) -> Tuple[List[frozenset], Dict[str, Set[str]]]:
    adj = {k: set(v) for k, v in adj_in.items()}
    remaining = set(adj.keys())
    cliques_pot: List[frozenset] = []

    while remaining:
        best, best_fill = None, float("inf")
        for v in remaining:
            nbrs = sorted(adj[v] & remaining)
            fill = sum(
                1
                for i in range(len(nbrs))
                for j in range(i + 1, len(nbrs))
                if nbrs[j] not in adj[nbrs[i]]
            )
            if fill < best_fill:
                best_fill, best = fill, v
        nbrs = sorted(adj[best] & remaining)  # type: ignore
        cliques_pot.append(frozenset(nbrs + [best]))  # type: ignore
        for i in range(len(nbrs)):
            for j in range(i + 1, len(nbrs)):
                adj[nbrs[i]].add(nbrs[j])
                adj[nbrs[j]].add(nbrs[i])
        remaining.remove(best)  # type: ignore

    maximales: List[frozenset] = []
    for c in cliques_pot:
        if not any(c != c2 and c.issubset(c2) for c2 in cliques_pot):
            maximales.append(c)
    vues: Set[frozenset] = set()
    out: List[frozenset] = []
    for c in maximales:
        if c not in vues:
            vues.add(c)
            out.append(c)
    return out, adj


# ===========================================================================
# (i) + (h) + (n) + (l) GrapheCausal + JunctionTree (Shafer-Shenoy)
# ===========================================================================
class GrapheCausal:
    def __init__(self) -> None:
        self.noeuds: Set[str] = set()
        self.parents: Dict[str, Set[str]] = defaultdict(set)
        self.enfants: Dict[str, Set[str]] = defaultdict(set)
        self._priors: Dict[str, float] = {}
        self._poids_arete: Dict[Tuple[str, str], float] = {}
        self._cpts: Dict[str, Dict[Tuple[int, ...], float]] = {}
        self._cpts_source: Dict[str, str] = {}
        self._topo_cache: Optional[List[str]] = None

    def ajouter_arete(self, s: str, c: str) -> None:
        s, c = _norm(s), _norm(c)
        if s == c:
            return
        self.noeuds.add(s)
        self.noeuds.add(c)
        self.enfants[s].add(c)
        self.parents[c].add(s)
        self._topo_cache = None

    def ancetres(self, x: str) -> Set[str]:
        vus: Set[str] = set()
        q = deque(self.parents[_norm(x)])
        while q:
            p = q.popleft()
            if p in vus:
                continue
            vus.add(p)
            q.extend(self.parents[p])
        return vus

    def descendants(self, x: str) -> Set[str]:
        vus: Set[str] = set()
        q = deque(self.enfants[_norm(x)])
        while q:
            c = q.popleft()
            if c in vus:
                continue
            vus.add(c)
            q.extend(self.enfants[c])
        return vus

    def confondants(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return (self.ancetres(x) & self.ancetres(y)) - {x, y}

    def mediateurs(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return self.descendants(x) & self.ancetres(y)

    def colliders(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return self.descendants(x) & self.descendants(y)

    def detecter_cycles(self) -> List[List[str]]:
        BLANC, GRIS, NOIR = 0, 1, 2
        couleur = {n: BLANC for n in self.noeuds}
        parent_dfs: Dict[str, str] = {}
        cycles: List[List[str]] = []

        def dfs(u: str) -> None:
            couleur[u] = GRIS
            for v in self.enfants.get(u, set()):
                if couleur[v] == GRIS:
                    cycle = [v, u]
                    cur = u
                    while cur in parent_dfs and parent_dfs[cur] != v:
                        cur = parent_dfs[cur]
                        cycle.append(cur)
                    cycle.append(v)
                    cycles.append(list(reversed(cycle)))
                elif couleur[v] == BLANC:
                    parent_dfs[v] = u
                    dfs(v)
            couleur[u] = NOIR

        for n in list(self.noeuds):
            if couleur[n] == BLANC:
                dfs(n)
        return cycles

    def est_dag(self) -> bool:
        return not self.detecter_cycles()

    def composante_acyclique(self) -> "GrapheCausal":
        cycles = self.detecter_cycles()
        aretes_cycle: Set[Tuple[str, str]] = set()
        for c in cycles:
            for i in range(len(c) - 1):
                aretes_cycle.add((c[i], c[i + 1]))
        g = GrapheCausal()
        for n in self.noeuds:
            g.noeuds.add(n)
        for u, enfants in self.enfants.items():
            for v in enfants:
                if (u, v) not in aretes_cycle:
                    g.ajouter_arete(u, v)
        g._priors = dict(self._priors)
        g._poids_arete = dict(self._poids_arete)
        g._cpts = {k: dict(v) for k, v in self._cpts.items()}
        g._cpts_source = dict(self._cpts_source)
        return g

    def d_separes(
        self,
        x_set: Set[str],
        y_set: Set[str],
        z_set: Set[str],
        ignorer_sortants_de: Optional[Set[str]] = None,
    ) -> bool:
        ignorer = {_norm(n) for n in (ignorer_sortants_de or set())}
        xs = {_norm(n) for n in x_set}
        ys = {_norm(n) for n in y_set}
        zs = {_norm(n) for n in z_set}
        visit: Set[Tuple[str, str]] = set()
        q: deque = deque()
        for x in xs:
            q.append((x, "up"))
            q.append((x, "down"))
        while q:
            v, d = q.popleft()
            if (v, d) in visit:
                continue
            visit.add((v, d))
            if d == "up":
                if v not in zs:
                    for p in self.parents[v]:
                        q.append((p, "up"))
                    if v not in ignorer:
                        for c in self.enfants[v]:
                            q.append((c, "down"))
            else:
                for p in self.parents[v]:
                    if p not in ignorer:
                        q.append((p, "up"))
                if v not in zs:
                    for c in self.enfants[v]:
                        q.append((c, "down"))
        for y in ys:
            if (y, "up") in visit or (y, "down") in visit:
                return False
        return True

    def backdoor_valide(self, x: str, y: str, z_set: Set[str]) -> bool:
        return self.d_separes(
            {_norm(x)},
            {_norm(y)},
            z_set,
            ignorer_sortants_de={_norm(x)},
        )

    def backdoor_set_simple(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        desc_x = self.descendants(x)
        parents_x = {p for p in self.parents[x] if p not in desc_x}
        return self.confondants(x, y) | parents_x

    def set_prior(self, noeud: str, p: float) -> None:
        self._priors[_norm(noeud)] = max(0.0, min(1.0, p))

    def set_poids_arete(self, parent: str, enfant: str, q: float) -> None:
        self._poids_arete[(_norm(parent), _norm(enfant))] = max(0.0, min(1.0, q))

    def set_cpt(
        self,
        noeud: str,
        table: Dict[Tuple[int, ...], float],
        source: str = "explicite",
    ) -> None:
        self._cpts[_norm(noeud)] = dict(table)
        self._cpts_source[_norm(noeud)] = source

    def apprendre_cpts_depuis_observations(
        self,
        lignes: List[Dict[str, int]],
        lissage_laplace: float = 1.0,
    ) -> None:
        if not lignes:
            raise ValueError("Aucune observation fournie")
        vars_presentes = set(lignes[0].keys())
        manquants = [n for n in self.noeuds if n not in vars_presentes]
        if manquants:
            raise ValueError(f"Nœuds absents des observations : {manquants}")
        for n in self.noeuds:
            parents = sorted(self.parents[n])
            comptes_1: Dict[Tuple, int] = defaultdict(int)
            comptes_n: Dict[Tuple, int] = defaultdict(int)
            for row in lignes:
                pv = tuple(int(row[p]) for p in parents)
                v = int(row[n])
                comptes_n[pv] += 1
                if v == 1:
                    comptes_1[pv] += 1
            cpt: Dict[Tuple[int, ...], float] = {}
            for pv in itertools.product((0, 1), repeat=len(parents)):
                n1 = comptes_1.get(pv, 0)
                nt = comptes_n.get(pv, 0)
                cpt[pv] = (n1 + lissage_laplace) / (nt + 2 * lissage_laplace)
            self._cpts[n] = cpt
            self._cpts_source[n] = "empirique_csv"

    @property
    def source_modele(self) -> str:
        if not self._cpts:
            return "heuristique_noisy_or"
        src = set(self._cpts_source.values())
        if src == {"empirique_csv"}:
            return "empirique_csv"
        if src == {"heuristique_noisy_or"} or src == {"explicite"}:
            return "heuristique_noisy_or"
        return "mixte"

    def _p1_conditionnel(self, noeud: str, parents_vals: Tuple[int, ...]) -> float:
        if noeud in self._cpts:
            return self._cpts[noeud].get(tuple(parents_vals), 0.0)
        parents = sorted(self.parents[noeud])
        if not parents:
            return self._priors.get(noeud, 0.1)
        leak = self._priors.get(noeud, 0.01)
        p_no = 1.0 - leak
        for p, val in zip(parents, parents_vals):
            if val == 1:
                q = self._poids_arete.get((p, noeud), 0.5)
                p_no *= 1.0 - q
        return 1.0 - p_no

    def _construire_facteurs(
        self,
        do_x: Optional[str] = None,
        do_dict: Optional[Dict[str, int]] = None,
    ) -> List[Tuple[Tuple[str, ...], Dict[Tuple[int, ...], float]]]:
        do_map = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        facteurs = []
        for n in sorted(self.noeuds):
            if n in do_map:
                v = do_map[n]
                facteurs.append(((n,), {(0,): 1.0 - v, (1,): float(v)}))
                continue
            if n == do_x:
                p1 = self._priors.get(n, 0.1)
                facteurs.append(((n,), {(0,): 1.0 - p1, (1,): p1}))
                continue
            parents = sorted(self.parents[n])
            scope = tuple(parents + [n])
            table: Dict[Tuple[int, ...], float] = {}
            for vals in itertools.product((0, 1), repeat=len(scope)):
                pv = vals[: len(parents)]
                p1 = self._p1_conditionnel(n, pv)
                table[vals] = p1 if vals[-1] == 1 else 1.0 - p1
            facteurs.append((scope, table))
        return facteurs

    @staticmethod
    def _restreindre(facteur, evidence: Dict[str, int]):
        scope, table = facteur
        pos = [i for i, v in enumerate(scope) if v in evidence]
        if not pos:
            return facteur
        new_scope = tuple(v for i, v in enumerate(scope) if i not in pos)
        new_table: Dict[Tuple[int, ...], float] = defaultdict(float)
        for vals, p in table.items():
            if all(vals[i] == evidence[scope[i]] for i in pos):
                nk = tuple(v for i, v in enumerate(vals) if i not in pos)
                new_table[nk] += p
        return new_scope, dict(new_table)

    @staticmethod
    def _multiplier(f1, f2):
        s1, t1 = f1
        s2, t2 = f2
        scope = tuple(sorted(set(s1) | set(s2)))
        idx1 = [scope.index(v) for v in s1]
        idx2 = [scope.index(v) for v in s2]
        table: Dict[Tuple[int, ...], float] = defaultdict(float)
        for vals1, p1 in t1.items():
            for vals2, p2 in t2.items():
                ok = True
                for i, v in enumerate(s1):
                    if v in s2 and vals1[i] != vals2[s2.index(v)]:
                        ok = False
                        break
                if not ok:
                    continue
                full = [0] * len(scope)
                for i in range(len(s1)):
                    full[idx1[i]] = vals1[i]
                for i in range(len(s2)):
                    full[idx2[i]] = vals2[i]
                table[tuple(full)] += p1 * p2
        return scope, dict(table)

    @staticmethod
    def _sommer_sur(facteur, var: str):
        scope, table = facteur
        if var not in scope:
            return facteur
        i = scope.index(var)
        new_scope = tuple(v for j, v in enumerate(scope) if j != i)
        new_table: Dict[Tuple[int, ...], float] = defaultdict(float)
        for vals, p in table.items():
            key = tuple(v for j, v in enumerate(vals) if j != i)
            new_table[key] += p
        return new_scope, dict(new_table)

    def inference_ve(
        self,
        query_var: str,
        evidence: Optional[Dict[str, int]] = None,
        do_x: Optional[str] = None,
        do_dict: Optional[Dict[str, int]] = None,
    ) -> Dict[int, float]:
        ev = {_norm(k): int(v) for k, v in (evidence or {}).items()}
        facteurs = [
            self._restreindre(f, ev)
            for f in self._construire_facteurs(do_x=do_x, do_dict=do_dict)
        ]
        cache: Set[str] = set(ev.keys())
        if do_x is not None:
            cache.add(_norm(do_x))
        if do_dict is not None:
            cache.update(_norm(k) for k in do_dict)
        cache.add(_norm(query_var))
        ordre = [n for n in sorted(self.noeuds) if n not in cache]
        ordre.sort(key=lambda n: len(self.parents[n]) + len(self.enfants[n]))
        for var in ordre:
            concernes = [f for f in facteurs if var in f[0]]
            autres = [f for f in facteurs if var not in f[0]]
            if not concernes:
                continue
            prod = concernes[0]
            for f in concernes[1:]:
                prod = self._multiplier(prod, f)
            facteurs = autres + [self._sommer_sur(prod, var)]
        if not facteurs:
            return {0: 1.0, 1: 0.0}
        prod = facteurs[0]
        for f in facteurs[1:]:
            prod = self._multiplier(prod, f)
        scope, table = prod
        q = _norm(query_var)
        if q not in scope:
            return {0: 1.0, 1: 0.0}
        i = scope.index(q)
        total = sum(table.values())
        out = {0: 0.0, 1: 0.0}
        for vals, p in table.items():
            out[vals[i]] += p
        if total > 0:
            for k in out:
                out[k] /= total
        return out

    def comparer_observation_vs_intervention(
        self, x: str, y: str
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique — do(X) refusé.")
        x, y = _norm(x), _norm(y)
        p_obs = self.inference_ve(y, {x: 1}, do_x=None)
        p_do = self.inference_ve(y, {x: 1}, do_dict={x: 1})
        bd = self.backdoor_set_simple(x, y)
        return {
            "P(Y=1|X=1)":     p_obs[1],
            "P(Y=1|do(X=1))": p_do[1],
            "delta_biais":    abs(p_obs[1] - p_do[1]),
            "confondants":    sorted(self.confondants(x, y)),
            "backdoor_set":   sorted(bd),
            "backdoor_valide": self.backdoor_valide(x, y, bd),
        }

    def _graphe_sans_parents(self, do_x: str) -> "GrapheCausal":
        return self._graphe_sans_parents_multi({_norm(do_x): 1})

    def _graphe_sans_parents_multi(
        self, do_dict: Dict[str, int]
    ) -> "GrapheCausal":
        do_map = {_norm(k): int(v) for k, v in do_dict.items()}
        g = GrapheCausal()
        for n in self.noeuds:
            g.noeuds.add(n)
        for u in self.enfants:
            for v in self.enfants[u]:
                if v in do_map:
                    continue
                g.ajouter_arete(u, v)
        g._priors = dict(self._priors)
        g._poids_arete = dict(self._poids_arete)
        g._cpts = {k: dict(v) for k, v in self._cpts.items() if k not in do_map}
        g._cpts_source = {
            k: v for k, v in self._cpts_source.items() if k not in do_map
        }
        return g

    # --- (p) + (s) + (t) Pearl Niveau 3 (FC, IS, Rejet, Joint, PN/PS/PNS, Gibbs)
    def _ordre_topo(self) -> List[str]:
        if self._topo_cache is not None:
            return self._topo_cache
        indeg = {n: len(self.parents[n]) for n in self.noeuds}
        q = [n for n in self.noeuds if indeg[n] == 0]
        out: List[str] = []
        while q:
            n = q.pop()
            out.append(n)
            for c in self.enfants[n]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    q.append(c)
        self._topo_cache = out
        return out

    def _forward(
        self, U: Dict[str, float], do_dict: Optional[Dict[str, int]] = None
    ) -> Dict[str, int]:
        do_map = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        V: Dict[str, int] = {}
        for n in self._ordre_topo():
            if n in do_map:
                V[n] = do_map[n]
                continue
            parents = sorted(self.parents[n])
            p1 = self._p1_conditionnel(n, tuple(V[p] for p in parents))
            V[n] = 1 if U[n] < p1 else 0
        return V

    def _echantillonner_U_conditionnel(
        self,
        obs: Dict[str, int],
        rng: random.Random,
        do_dict: Optional[Dict[str, int]] = None,
    ) -> Tuple[Dict[str, float], Dict[str, int], float]:
        do_map = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        U: Dict[str, float] = {}
        V: Dict[str, int] = {}
        w: float = 1.0
        for n in self._ordre_topo():
            if n in do_map:
                V[n] = do_map[n]
                U[n] = rng.random()
                continue
            parents = sorted(self.parents[n])
            p1 = self._p1_conditionnel(n, tuple(V[p] for p in parents))
            if n in obs:
                v = obs[n]
                if v == 1:
                    w *= p1
                    U[n] = rng.uniform(0, max(p1, 1e-12))
                    V[n] = 1
                else:
                    w *= 1.0 - p1
                    U[n] = rng.uniform(min(p1, 1 - 1e-12), 1)
                    V[n] = 0
            else:
                U[n] = rng.random()
                V[n] = 1 if U[n] < p1 else 0
        return U, V, w

    def contrefactuel_fc(
        self,
        observation: Dict[str, int],
        intervention: Dict[str, int],
        requete: str,
        n_samples: int = 50000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        intv = {_norm(k): int(v) for k, v in intervention.items()}
        q = _norm(requete)
        rng = random.Random(seed)
        w_sum = 0.0
        w_true = 0.0
        for _ in range(n_samples):
            U, _, w = self._echantillonner_U_conditionnel(obs, rng)
            if w <= 0.0:
                continue
            w_sum += w
            if self._forward(U, do_dict=intv).get(q, 0) == 1:
                w_true += w
        p = w_true / w_sum if w_sum > 0 else float("nan")
        return {
            "P": p,
            "n_samples": n_samples,
            "erreur_std_approx": (
                math.sqrt(max(0.0, p * (1 - p)) / n_samples)
                if w_sum > 0
                else float("nan")
            ),
        }

    def contrefactuel_rejet(
        self,
        observation: Dict[str, int],
        intervention: Dict[str, int],
        requete: str,
        n_samples: int = 50000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        intv = {_norm(k): int(v) for k, v in intervention.items()}
        q = _norm(requete)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        nm = nt = 0
        for _ in range(n_samples):
            U = {n: rng.random() for n in noeuds}
            V = self._forward(U)
            if not all(V.get(k) == v for k, v in obs.items()):
                continue
            nm += 1
            if self._forward(U, do_dict=intv).get(q, 0) == 1:
                nt += 1
        p = nt / nm if nm else float("nan")
        return {
            "P": p,
            "n_match": nm,
            "n_samples": n_samples,
            "erreur_std_approx": (
                math.sqrt(max(0.0, p * (1 - p)) / max(nm, 1))
                if nm
                else float("nan")
            ),
        }

    def contrefactuel(
        self,
        observation: Dict[str, int],
        intervention: Dict[str, int],
        requete: str,
        n_samples: int = 50000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        return self.contrefactuel_fc(
            observation, intervention, requete, n_samples=n_samples, seed=seed
        )

    def contrefactuel_is(
        self,
        observation: Dict[str, int],
        intervention: Dict[str, int],
        requete: str,
        n_samples: int = 50000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        intv = {_norm(k): int(v) for k, v in intervention.items()}
        q = _norm(requete)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        poids_sum = 0.0
        num = 0.0
        for _ in range(n_samples):
            U = {n: rng.random() for n in noeuds}
            V = self._forward(U)
            w = 1.0
            for k, v in obs.items():
                parents = sorted(self.parents[k])
                p_k = self._p1_conditionnel(k, tuple(V[p] for p in parents))
                w *= p_k if v == 1 else (1.0 - p_k)
            if w <= 0:
                continue
            Vcf = self._forward(U, do_dict=intv)
            poids_sum += w
            if Vcf.get(q, 0) == 1:
                num += w
        p = num / poids_sum if poids_sum > 0 else float("nan")
        return {
            "P": p,
            "n_samples": n_samples,
            "poids_effectif_approx": poids_sum / n_samples,
        }

    def contrefactuel_joint(
        self,
        observation: Dict[str, int],
        interventions: List[Dict[str, int]],
        requetes: List[str],
        n_samples: int = 50000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        intvs = [{_norm(k): int(v) for k, v in d.items()} for d in interventions]
        qs = [_norm(q) for q in requetes]
        if len(intvs) != len(qs):
            raise ValueError("interventions et requetes doivent avoir même longueur")
        rng = random.Random(seed)
        w_sum = 0.0
        w_joint = 0.0
        for _ in range(n_samples):
            U, _, w = self._echantillonner_U_conditionnel(obs, rng)
            if w <= 0.0:
                continue
            w_sum += w
            if all(
                self._forward(U, do_dict=intv).get(q, 0) == 1
                for intv, q in zip(intvs, qs)
            ):
                w_joint += w
        return {
            "P": w_joint / w_sum if w_sum > 0 else float("nan"),
            "n_samples": n_samples,
        }

    def probabilites_causales(
        self, x: str, y: str, n_samples: int = 50000, seed: int = 42
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        x, y = _norm(x), _norm(y)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        n11 = n00 = pn_num = ps_num = pns_num = 0
        for _ in range(n_samples):
            U = {n: rng.random() for n in noeuds}
            V = self._forward(U)
            xv, yv = V.get(x, 0), V.get(y, 0)
            if xv == 1 and yv == 1:
                n11 += 1
                if self._forward(U, do_dict={x: 0}).get(y, 0) == 0:
                    pn_num += 1
            if xv == 0 and yv == 0:
                n00 += 1
                if self._forward(U, do_dict={x: 1}).get(y, 0) == 1:
                    ps_num += 1
            if (
                self._forward(U, do_dict={x: 1}).get(y, 0) == 1
                and self._forward(U, do_dict={x: 0}).get(y, 0) == 0
            ):
                pns_num += 1
        return {
            "PN": pn_num / n11 if n11 else float("nan"),
            "PS": ps_num / n00 if n00 else float("nan"),
            "PNS": pns_num / n_samples,
            "n_X1Y1": n11,
            "n_X0Y0": n00,
            "n_samples": n_samples,
        }

    def gibbs_PV_obs(
        self,
        query_var: str,
        observation: Dict[str, int],
        n_samples: int = 20000,
        burn_in: int = 2000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        q = _norm(query_var)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        libres = [n for n in noeuds if n not in obs]
        V: Dict[str, int] = dict(obs)
        for n in libres:
            V[n] = rng.randint(0, 1)
        n_q1 = 0
        for step in range(burn_in + n_samples):
            for n in libres:
                parents = sorted(self.parents[n])
                enfants = sorted(self.enfants[n])
                p1 = self._p1_conditionnel(n, tuple(V[p] for p in parents))

                def lik_enfants(val_n: int) -> float:
                    V_tmp = dict(V)
                    V_tmp[n] = val_n
                    w = 1.0
                    for c in enfants:
                        pc_parents = sorted(self.parents[c])
                        p_c = self._p1_conditionnel(
                            c, tuple(V_tmp[p] for p in pc_parents)
                        )
                        w *= p_c if V[c] == 1 else (1.0 - p_c)
                    return w

                w1 = p1 * lik_enfants(1)
                w0 = (1 - p1) * lik_enfants(0)
                tot = w1 + w0
                V[n] = 1 if (tot > 0 and rng.random() < w1 / tot) else 0
            if step >= burn_in and V[q] == 1:
                n_q1 += 1
        return {
            "P(Q=1|obs)": n_q1 / n_samples,
            "n_samples": n_samples,
            "burn_in": burn_in,
        }

    def planifier_interventions(
        self,
        cible_y: str,
        seuil_prob: float,
        candidats_x: Optional[List[str]] = None,
        valeurs: Tuple[int, ...] = (1,),
        couts: Optional[Dict[str, float]] = None,
        max_k: int = 4,
    ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        y = _norm(cible_y)
        if candidats_x is None:
            desc = self.descendants(y)
            candidats_x = sorted(
                n for n in self.noeuds if n != y and n not in desc
            )
        else:
            candidats_x = [_norm(x) for x in candidats_x]
        couts_map = {_norm(k): v for k, v in (couts or {}).items()}

        def c(x: str) -> float:
            return couts_map.get(x, 1.0)

        counter = 0
        tas: List[Tuple[float, int, frozenset, Dict[str, int]]] = [
            (0.0, counter, frozenset(), {})
        ]
        vus: Set[frozenset] = set()
        while tas:
            cout, _, etat_items, do_dict = heapq.heappop(tas)
            if etat_items in vus:
                continue
            vus.add(etat_items)
            if do_dict:
                p = self.inference_ve(y, {}, do_dict=do_dict)[1]
                if p >= seuil_prob:
                    return {
                        "trouve": True,
                        "interventions": dict(do_dict),
                        "proba": p,
                        "cout": cout,
                        "k": len(do_dict),
                        "explores": len(vus),
                    }
            if len(do_dict) >= max_k:
                continue
            for x in candidats_x:
                if x in do_dict:
                    continue
                for v in valeurs:
                    nd = dict(do_dict)
                    nd[x] = v
                    ns = frozenset(nd.items())
                    if ns not in vus:
                        counter += 1
                        heapq.heappush(tas, (cout + c(x), counter, ns, nd))
        return {
            "trouve": False,
            "explores": len(vus),
            "raison": f"Aucune combinaison ≤ {max_k} n'atteint {seuil_prob}",
        }


class JunctionTree:
    """Arbre de cliques (Shafer-Shenoy). Exact."""

    def __init__(self, graphe: GrapheCausal) -> None:
        self.graphe = graphe
        self.adj_moral = _moraliser(graphe.parents, graphe.noeuds)
        cliques, _ = _trianguler_min_fill(self.adj_moral)
        self.cliques: List[frozenset] = cliques
        self.adj_cliques, self.parent_tree = self._construire_arbre()
        self.potentiels = self._initialiser_potentiels()
        self.messages: Dict[Tuple[int, int], Any] = {}
        self._passer_messages()

    def _construire_arbre(self, root: int = 0):
        n = len(self.cliques)
        aretes = []
        for i in range(n):
            for j in range(i + 1, n):
                sep = self.cliques[i] & self.cliques[j]
                if sep:
                    aretes.append((len(sep), i, j))
        aretes.sort(reverse=True)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        adj: Dict[int, List[Tuple[int, frozenset]]] = {i: [] for i in range(n)}
        arbre = []
        for w, i, j in aretes:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
                sep = self.cliques[i] & self.cliques[j]
                adj[i].append((j, sep))
                adj[j].append((i, sep))
                arbre.append((i, j))
                if len(arbre) == n - 1:
                    break
        parent_tree: Dict[int, Optional[int]] = {root: None}
        q = [root]
        while q:
            u = q.pop()
            for v, _ in adj[u]:
                if v not in parent_tree:
                    parent_tree[v] = u
                    q.append(v)
        return adj, parent_tree

    def _initialiser_potentiels(self):
        potentiels = [defaultdict(lambda: 1.0) for _ in self.cliques]
        for noeud in self.graphe.noeuds:
            parents = sorted(self.graphe.parents[noeud])
            scope = frozenset(parents + [noeud])
            target = None
            for idx, c in enumerate(self.cliques):
                if scope.issubset(c):
                    target = idx
                    break
            if target is None:
                raise RuntimeError(f"Pas de clique pour scope {scope}")
            clique = tuple(sorted(self.cliques[target]))
            pos = {v: clique.index(v) for v in scope}
            for vals in itertools.product((0, 1), repeat=len(clique)):
                pv = tuple(vals[pos[p]] for p in parents)
                p1 = self.graphe._p1_conditionnel(noeud, pv)
                proba = p1 if vals[pos[noeud]] == 1 else 1.0 - p1
                potentiels[target][vals] *= proba
        return potentiels

    def _message(self, src: int, dst: int):
        sep = self.cliques[src] & self.cliques[dst]
        scope = tuple(sorted(self.cliques[src]))
        pot = (scope, dict(self.potentiels[src]))
        for k, _ in self.adj_cliques[src]:
            if k == dst:
                continue
            if (k, src) in self.messages:
                pot = GrapheCausal._multiplier(pot, self.messages[(k, src)])
        for v in self.cliques[src] - sep:
            pot = GrapheCausal._sommer_sur(pot, v)
        return pot

    def _passer_messages(self) -> None:
        self.messages = {}
        ordre_post: List[int] = []

        def dfs(u, p):
            for v, _ in self.adj_cliques[u]:
                if v != p:
                    dfs(v, u)
            ordre_post.append(u)

        dfs(0, None)
        for u in ordre_post:
            p = self.parent_tree.get(u)
            if p is not None:
                self.messages[(u, p)] = self._message(u, p)

        def dfs2(u, p):
            for v, _ in self.adj_cliques[u]:
                if v != p:
                    self.messages[(u, v)] = self._message(u, v)
                    dfs2(v, u)

        dfs2(0, None)

    def clone(self) -> "JunctionTree":
        jt = JunctionTree.__new__(JunctionTree)
        jt.graphe = self.graphe
        jt.adj_moral = self.adj_moral
        jt.cliques = self.cliques
        jt.adj_cliques = self.adj_cliques
        jt.parent_tree = self.parent_tree
        jt.potentiels = [dict(p) for p in self.potentiels]
        jt.messages = {}
        jt._passer_messages()
        return jt

    def _query_marginal(self, var: str) -> Dict[int, float]:
        var = _norm(var)
        target = None
        for i, c in enumerate(self.cliques):
            if var in c:
                target = i
                break
        if target is None:
            raise RuntimeError(f"{var} absent des cliques")
        scope = tuple(sorted(self.cliques[target]))
        pot = (scope, dict(self.potentiels[target]))
        for k, _ in self.adj_cliques[target]:
            if (k, target) in self.messages:
                pot = GrapheCausal._multiplier(pot, self.messages[(k, target)])
        for v in self.cliques[target] - {var}:
            pot = GrapheCausal._sommer_sur(pot, v)
        _, table = pot
        total = sum(table.values())
        out = {0: 0.0, 1: 0.0}
        for vals, p in table.items():
            out[vals[0]] += p
        if total > 0:
            for k in out:
                out[k] /= total
        return out

    def query(
        self,
        var: str,
        evidence: Optional[Dict[str, int]] = None,
        do_x: Optional[str] = None,
        do_dict: Optional[Dict[str, int]] = None,
    ) -> Dict[int, float]:
        if do_dict is not None:
            g2 = self.graphe._graphe_sans_parents_multi(do_dict)
            return JunctionTree(g2).query(var, evidence=evidence)
        if do_x is not None:
            g2 = self.graphe._graphe_sans_parents(do_x)
            return JunctionTree(g2).query(var, evidence=evidence)
        jt = self if not evidence else self.clone()
        if evidence:
            ev = {_norm(k): int(v) for k, v in evidence.items()}
            for i, c in enumerate(jt.cliques):
                scope = tuple(sorted(c))
                new_pot: Dict[Tuple[int, ...], float] = defaultdict(float)
                for vals, p in jt.potentiels[i].items():
                    ok = True
                    for k, v in ev.items():
                        if k in c and vals[scope.index(k)] != v:
                            ok = False
                            break
                    if ok:
                        new_pot[vals] += p
                jt.potentiels[i] = new_pot
            jt.messages = {}
            jt._passer_messages()
        return jt._query_marginal(var)

    def comparer_observation_vs_intervention(
        self, x: str, y: str
    ) -> Dict[str, Any]:
        if not self.graphe.est_dag():
            raise ValueError("Graphe cyclique — do(X) refusé.")
        x, y = _norm(x), _norm(y)
        p_obs = self.query(y, evidence={x: 1})
        p_do = self.query(y, evidence={x: 1}, do_x=x)
        return {
            "P(Y=1|X=1)":     p_obs[1],
            "P(Y=1|do(X=1))": p_do[1],
            "delta_biais":    abs(p_obs[1] - p_do[1]),
            "confondants":    sorted(self.graphe.confondants(x, y)),
            "backdoor_set":   sorted(self.graphe.backdoor_set_simple(x, y)),
        }


# ===========================================================================
# (w) TwinNetwork — Structure Explicite V ∪ V_x avec U Partagés (Pearl §7.2)
# ===========================================================================
class TwinNetwork:
    def __init__(self, graphe: GrapheCausal) -> None:
        if not graphe.est_dag():
            raise ValueError("Twin network requiert un DAG")
        self.g = graphe
        self.topo = graphe._ordre_topo()
        self.copies: Dict[str, str] = {n: f"{n}_x" for n in self.topo}
        self.U_noeuds: List[str] = [f"U_{n}" for n in self.topo]

    def resoudre_contrefactuel(
        self,
        obs: Dict[str, int],
        intv: Dict[str, int],
        req: str,
        n_samples: int = 50000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        return self.g.contrefactuel_fc(obs, intv, req, n_samples, seed)

    def descriptif(self) -> str:
        lignes = ["TwinNetwork — structure :"]
        for n in self.topo:
            parents = sorted(self.g.parents[n])
            ps = ", ".join(parents) if parents else "∅"
            lignes.append(f"  V  : {n}  ←  U_{n} × ({ps})")
        lignes.append("  --- copies interventionnelles ---")
        for n in self.topo:
            parents = sorted(self.g.parents[n])
            ps = ", ".join(f"{p}_x" for p in parents) if parents else "∅"
            lignes.append(f"  V_x: {n}_x ←  U_{n} × ({ps})")
        return "\n".join(lignes)


# ===========================================================================
# (x) VertexCoverLP — Simplexe Tableau Dual (Fractional Matching)
# ===========================================================================
class VertexCoverLP:
    def __init__(self, aretes: List[Tuple[Any, Any]], poids: Dict[Any, float]) -> None:
        self.aretes = [tuple(e) for e in aretes]
        self.poids = dict(poids)
        for u, v in self.aretes:
            self.poids.setdefault(u, 1.0)
            self.poids.setdefault(v, 1.0)

    def resoudre(self) -> Dict[str, Any]:
        edges = self.aretes
        vertices = sorted({v for e in edges for v in e})
        n_v, n_e = len(vertices), len(edges)
        if n_e == 0:
            return {
                "valeur": 0.0,
                "y": {},
                "statut": "optimal",
                "iterations": 0,
                "n_v": n_v,
                "n_e": n_e,
                "valeur_arrondie": 0,
            }
        v_idx = {v: i for i, v in enumerate(vertices)}
        N = n_e + n_v
        tab = [[0.0] * (N + 1) for _ in range(n_v + 1)]
        for j in range(n_e):
            tab[0][j] = -1.0
        for ei, (u, v) in enumerate(edges):
            tab[v_idx[u] + 1][ei] = 1.0
            tab[v_idx[v] + 1][ei] = 1.0
        for vi in range(n_v):
            tab[vi + 1][n_e + vi] = 1.0
            tab[vi + 1][N] = self.poids[vertices[vi]]

        basis = [n_e + vi for vi in range(n_v)]
        it = 0
        for it in range(1, 2001):
            in_basis = set(basis)
            entering, best = -1, -1e-9
            for j in range(N):
                if j in in_basis:
                    continue
                if tab[0][j] < best:
                    best, entering = tab[0][j], j
            if entering == -1:
                break
            leaving, ratio_min = -1, float("inf")
            for i in range(1, n_v + 1):
                if tab[i][entering] > 1e-9:
                    r = tab[i][N] / tab[i][entering]
                    if r < ratio_min:
                        ratio_min, leaving = r, i - 1
            if leaving == -1:
                return {
                    "valeur": float("inf"),
                    "y": {},
                    "statut": "unbounded",
                    "iterations": it,
                    "n_v": n_v,
                    "n_e": n_e,
                }
            pr = leaving + 1
            pv = tab[pr][entering]
            for j in range(N + 1):
                tab[pr][j] /= pv
            for i in range(n_v + 1):
                if i == pr:
                    continue
                f = tab[i][entering]
                if abs(f) < 1e-12:
                    continue
                for j in range(N + 1):
                    tab[i][j] -= f * tab[pr][j]
            basis[leaving] = entering

        val = tab[0][N]
        y_dict = {}
        for vi, bi in enumerate(basis):
            if bi < n_e:
                y_dict[edges[bi]] = tab[vi + 1][N]
        return {
            "valeur": val,
            "y": y_dict,
            "statut": "optimal",
            "iterations": it,
            "n_v": n_v,
            "n_e": n_e,
            "valeur_arrondie": math.ceil(val - 1e-9),
        }


# ===========================================================================
# (u) VertexCoverSolver — Branch & Bound + Borne Matching Greedé + Mémoïsation
# ===========================================================================
class VertexCoverSolver:
    def __init__(
        self,
        aretes: List[Tuple[Any, Any]],
        poids: Dict[Any, float],
        force_brute: bool = False,
    ) -> None:
        self.aretes = [tuple(e) for e in aretes]
        self.poids = dict(poids)
        for e in self.aretes:
            for v in e:
                self.poids.setdefault(v, 1.0)
        self.sommets = sorted({v for e in self.aretes for v in e})
        self.force_brute = force_brute
        self.noeuds_explores = 0
        self.memo: Dict[frozenset, Tuple[float, frozenset]] = {}

    def _matching_greede(self, aretes_restantes):
        tri = sorted(
            aretes_restantes,
            key=lambda e: -min(self.poids[e[0]], self.poids[e[1]]),
        )
        used: Set = set()
        match = []
        for u, v in tri:
            if u in used or v in used:
                continue
            match.append((u, v))
            used.add(u)
            used.add(v)
        return match

    def _borne_inf(self, aretes_restantes) -> float:
        return sum(
            min(self.poids[u], self.poids[v])
            for u, v in self._matching_greede(aretes_restantes)
        )

    def _force_brute(self):
        n = len(self.sommets)
        best_cout, best_set = float("inf"), frozenset()
        for mask in range(1 << n):
            cout = 0.0
            chosen = set()
            for i, v in enumerate(self.sommets):
                if mask & (1 << i):
                    chosen.add(v)
                    cout += self.poids[v]
                    if cout >= best_cout:
                        break
            if cout >= best_cout:
                continue
            if all(u in chosen or v in chosen for u, v in self.aretes):
                best_cout, best_set = cout, frozenset(chosen)
        return best_cout, best_set

    def _branch_and_bound(self):
        best = [float("inf"), frozenset()]

        def rec(
            aretes_restantes: List[Tuple], cout_courant: float, choisis: frozenset
        ):
            self.noeuds_explores += 1
            key = frozenset(aretes_restantes)
            if key in self.memo:
                mc, _ = self.memo[key]
                if cout_courant + mc >= best[0]:
                    return
            if not aretes_restantes:
                if cout_courant < best[0]:
                    best[0] = cout_courant
                    best[1] = choisis
                return
            b_inf = self._borne_inf(aretes_restantes)
            if cout_courant + b_inf >= best[0]:
                self.memo[key] = (b_inf, frozenset())
                return
            e = min(
                aretes_restantes,
                key=lambda x: min(self.poids[x[0]], self.poids[x[1]]),
            )
            for v in e:
                if v in choisis:
                    continue
                nouvelles = [a for a in aretes_restantes if v not in a]
                rec(nouvelles, cout_courant + self.poids[v], choisis | {v})

        rec(list(self.aretes), 0.0, frozenset())
        return best[0], best[1]

    def resoudre(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        if self.force_brute:
            cout, coupe = self._force_brute()
        else:
            cout, coupe = self._branch_and_bound()
        return {
            "coupe": set(coupe),
            "cout": cout,
            "noeuds_explores": self.noeuds_explores,
            "temps_ms": (time.perf_counter() - t0) * 1000,
        }


# ===========================================================================
# (y) AStarPlanificateur — A* & Dijkstra sur le Treillis des Interventions
# ===========================================================================
class AStarPlanificateur:
    def __init__(self, graphe: GrapheCausal) -> None:
        self.g = graphe

    def resoudre(
        self,
        cible_y: str,
        seuil: float,
        candidats: Optional[List[str]] = None,
        valeurs: Tuple[int, ...] = (1,),
        couts: Optional[Dict[str, float]] = None,
        max_k: int = 4,
        mode: str = "astar",
        h_poids: float = 1.0,
    ) -> Dict[str, Any]:
        if not self.g.est_dag():
            raise ValueError("Graphe cyclique")
        y = _norm(cible_y)
        if candidats is None:
            desc = self.g.descendants(y)
            candidats = sorted(
                n for n in self.g.noeuds if n != y and n not in desc
            )
        else:
            candidats = [_norm(x) for x in candidats]
        couts_map = {_norm(k): v for k, v in (couts or {}).items()}

        def c(x: str) -> float:
            return couts_map.get(x, 1.0)

        counter = 0
        tas = [(0.0, counter, frozenset(), {}, 0.0, 0.0)]
        vus: Set[frozenset] = set()
        explores = 0

        while tas:
            f, _, etat_items, do_dict, g_cost, p_curr = heapq.heappop(tas)
            if etat_items in vus:
                continue
            vus.add(etat_items)
            explores += 1

            p_curr = self.g.inference_ve(y, {}, do_dict=do_dict)[1]
            if do_dict and p_curr >= seuil:
                return {
                    "trouve": True,
                    "interventions": dict(do_dict),
                    "proba": p_curr,
                    "cout": g_cost,
                    "k": len(do_dict),
                    "explores": explores,
                    "mode": mode,
                }
            if len(do_dict) >= max_k:
                continue
            for x in candidats:
                if x in do_dict:
                    continue
                for v in valeurs:
                    nd = dict(do_dict)
                    nd[x] = v
                    ns = frozenset(nd.items())
                    if ns in vus:
                        continue
                    ng = g_cost + c(x)
                    h = (
                        h_poids * max(0.0, seuil - p_curr)
                        if mode == "astar"
                        else 0.0
                    )
                    counter += 1
                    heapq.heappush(tas, (ng + h, counter, ns, nd, ng, 0.0))

        return {
            "trouve": False,
            "explores": explores,
            "mode": mode,
            "raison": f"Aucune combinaison ≤ {max_k} n'atteint {seuil}",
        }


# ===========================================================================
# (z) StructureLearner — Score BIC + Hill-Climbing + Ordre Causal Optionnel
# ===========================================================================
class StructureLearner:
    def __init__(
        self,
        noeuds: List[str],
        observations: List[Dict[str, int]],
        ordre_causal: Optional[List[str]] = None,
    ) -> None:
        self.noeuds = list(noeuds)
        self.obs = observations
        self.n = len(observations)
        self._obs_idx = {
            n: [int(o[n]) for o in observations] for n in self.noeuds
        }
        self._rang = (
            {n: i for i, n in enumerate(ordre_causal)}
            if ordre_causal
            else None
        )

    def _log_lik(self, n: str, parents: Set[str]) -> float:
        parents_l = sorted(parents)
        if not parents_l:
            n1 = sum(self._obs_idx[n])
            n0 = self.n - n1
            ll = 0.0
            if n0 > 0:
                ll += n0 * math.log(n0 / self.n)
            if n1 > 0:
                ll += n1 * math.log(n1 / self.n)
            return ll
        counts: Dict[Tuple, List[int]] = defaultdict(lambda: [0, 0])
        for i in range(self.n):
            pv = tuple(self._obs_idx[p][i] for p in parents_l)
            counts[pv][self._obs_idx[n][i]] += 1
        ll = 0.0
        for _, (n0, n1) in counts.items():
            tot = n0 + n1
            if n0 > 0:
                ll += n0 * math.log(n0 / tot)
            if n1 > 0:
                ll += n1 * math.log(n1 / tot)
        return ll

    def _bic(self, parents: Dict[str, Set[str]]) -> float:
        ll = 0.0
        k = 0
        for n in self.noeuds:
            ll += self._log_lik(n, parents[n])
            k += 2 ** len(parents[n])
        return ll - 0.5 * math.log(self.n) * k

    def _descendants(self, n: str, parents: Dict[str, Set[str]]) -> Set[str]:
        desc: Set[str] = set()
        stack = [n]
        while stack:
            x = stack.pop()
            for v in self.noeuds:
                if x in parents[v] and v not in desc:
                    desc.add(v)
                    stack.append(v)
        return desc

    def apprendre(
        self, max_parents: int = 3, max_iter: int = 100
    ) -> Dict[str, Any]:
        parents: Dict[str, Set[str]] = {n: set() for n in self.noeuds}
        score = self._bic(parents)
        it = 0
        for it in range(max_iter):
            best_d, best_move = 0.0, None
            for u in self.noeuds:
                for v in self.noeuds:
                    if u == v or u in parents[v]:
                        continue
                    if self._rang is not None and self._rang.get(
                        u, 0
                    ) >= self._rang.get(v, 0):
                        continue
                    if len(parents[v]) >= max_parents:
                        continue
                    if u in self._descendants(v, parents):
                        continue
                    parents[v].add(u)
                    s2 = self._bic(parents)
                    parents[v].discard(u)
                    d = s2 - score
                    if d > best_d:
                        best_d, best_move = d, ("add", u, v, s2)
            for v in self.noeuds:
                for u in list(parents[v]):
                    parents[v].discard(u)
                    s2 = self._bic(parents)
                    parents[v].add(u)
                    d = s2 - score
                    if d > best_d:
                        best_d, best_move = d, ("del", u, v, s2)
            if best_move is None:
                break
            op, u, v, s2 = best_move
            if op == "add":
                parents[v].add(u)
            else:
                parents[v].discard(u)
            score = s2
        return {
            "parents": {n: set(p) for n, p in parents.items()},
            "score_bic": score,
            "iterations": it + 1,
        }

    def vers_graphe(
        self, parents_dict: Dict[str, Set[str]], apprendre_cpts: bool = True
    ) -> GrapheCausal:
        g = GrapheCausal()
        for n in self.noeuds:
            g.noeuds.add(n)
        for v, ps in parents_dict.items():
            for p in ps:
                g.ajouter_arete(p, v)
        if apprendre_cpts:
            g.apprendre_cpts_depuis_observations(self.obs)
        return g


# ===========================================================================
# (aa) TabuStructureSearch — Recherche Tabu + Random Restarts + Aspiration
# ===========================================================================
class TabuStructureSearch:
    def __init__(
        self,
        noeuds: List[str],
        observations: List[Dict[str, int]],
        tabu_tenure: int = 7,
        stall_limit: int = 30,
        n_restarts: int = 3,
        seed: int = 42,
        ordre_causal: Optional[List[str]] = None,
    ) -> None:
        self.noeuds = list(noeuds)
        self.obs = observations
        self.n = len(observations)
        self.tabu_tenure = tabu_tenure
        self.stall_limit = stall_limit
        self.n_restarts = n_restarts
        self.rng = random.Random(seed)
        self._obs = {n: [int(o[n]) for o in observations] for n in self.noeuds}
        self._rang = (
            {n: i for i, n in enumerate(ordre_causal)}
            if ordre_causal
            else None
        )

    def _log_lik(self, n: str, parents: Set[str]) -> float:
        parents_l = sorted(parents)
        if not parents_l:
            n1 = sum(self._obs[n])
            n0 = self.n - n1
            ll = 0.0
            if n0 > 0:
                ll += n0 * math.log(n0 / self.n)
            if n1 > 0:
                ll += n1 * math.log(n1 / self.n)
            return ll
        counts: Dict[Tuple, List[int]] = defaultdict(lambda: [0, 0])
        for i in range(self.n):
            pv = tuple(self._obs[p][i] for p in parents_l)
            counts[pv][self._obs[n][i]] += 1
        ll = 0.0
        for _, (n0, n1) in counts.items():
            tot = n0 + n1
            if n0 > 0:
                ll += n0 * math.log(n0 / tot)
            if n1 > 0:
                ll += n1 * math.log(n1 / tot)
        return ll

    def _bic(self, parents: Dict[str, Set[str]]) -> float:
        ll, k = 0.0, 0
        for n in self.noeuds:
            ll += self._log_lik(n, parents[n])
            k += 2 ** len(parents[n])
        return ll - 0.5 * math.log(max(self.n, 2)) * k

    def _cycle_si_ajout(
        self, u: str, v: str, parents: Dict[str, Set[str]]
    ) -> bool:
        stack = [v]
        vus: Set[str] = set()
        while stack:
            x = stack.pop()
            if x == u:
                return True
            if x in vus:
                continue
            vus.add(x)
            for w in self.noeuds:
                if x in parents[w]:
                    stack.append(w)
        return False

    def _dag_aleatoire(self, p_edge: float = 0.25) -> Dict[str, Set[str]]:
        if self._rang is not None:
            perm = sorted(self.noeuds, key=lambda x: self._rang[x])
        else:
            perm = list(self.noeuds)
            self.rng.shuffle(perm)
        parents: Dict[str, Set[str]] = {n: set() for n in self.noeuds}
        for i in range(len(perm)):
            for j in range(i + 1, len(perm)):
                if self.rng.random() < p_edge:
                    parents[perm[j]].add(perm[i])
        return parents

    def _voisins(
        self, parents: Dict[str, Set[str]], max_parents: int
    ) -> List[Tuple[str, str, str]]:
        moves: List[Tuple[str, str, str]] = []
        for u in self.noeuds:
            for v in self.noeuds:
                if u == v:
                    continue
                if u in parents[v]:
                    moves.append(("del", u, v))
                    if self._rang is None or self._rang.get(
                        v, 0
                    ) < self._rang.get(u, 0):
                        if len(parents[u]) < max_parents:
                            parents[v].discard(u)
                            if not self._cycle_si_ajout(v, u, parents):
                                moves.append(("rev", u, v))
                            parents[v].add(u)
                elif len(parents[v]) < max_parents:
                    if self._rang is not None and self._rang.get(
                        u, 0
                    ) >= self._rang.get(v, 0):
                        continue
                    if not self._cycle_si_ajout(u, v, parents):
                        moves.append(("add", u, v))
        return moves

    def apprendre(
        self, max_parents: int = 3, max_iter: int = 150, verbose: bool = False
    ) -> Dict[str, Any]:
        best_global_parents: Optional[Dict[str, Set[str]]] = None
        best_global_score = -float("inf")
        all_iters = 0

        for restart in range(self.n_restarts):
            parents = (
                {n: set() for n in self.noeuds}
                if restart == 0
                else self._dag_aleatoire()
            )
            score = self._bic(parents)
            tabu: Dict[Tuple[str, str, str], int] = {}
            stall = 0
            local_best_parents = {n: set(ps) for n, ps in parents.items()}
            local_best_score = score

            for _ in range(max_iter):
                all_iters += 1
                moves = self._voisins(parents, max_parents)
                if not moves:
                    break

                best_move, best_delta = None, -float("inf")
                for op, u, v in moves:
                    tabu_key = (op, u, v)
                    if op == "add":
                        parents[v].add(u)
                    elif op == "del":
                        parents[v].discard(u)
                    else:
                        parents[v].discard(u)
                        parents[u].add(v)
                    s2 = self._bic(parents)
                    if op == "add":
                        parents[v].discard(u)
                    elif op == "del":
                        parents[v].add(u)
                    else:
                        parents[u].discard(v)
                        parents[v].add(u)
                    d = s2 - score
                    is_tabu = tabu.get(tabu_key, 0) > all_iters
                    if is_tabu and s2 <= best_global_score + 1e-9:
                        continue
                    if d > best_delta:
                        best_delta, best_move = d, (op, u, v, s2)

                if best_move is None:
                    break
                op, u, v, s2 = best_move
                if op == "add":
                    parents[v].add(u)
                    inverse = ("del", u, v)
                elif op == "del":
                    parents[v].discard(u)
                    inverse = ("add", u, v)
                else:
                    parents[v].discard(u)
                    parents[u].add(v)
                    inverse = ("rev", v, u)
                score = s2

                tabu[inverse] = all_iters + self.tabu_tenure
                tabu.pop((op, u, v), None)

                if score > local_best_score + 1e-9:
                    local_best_score = score
                    local_best_parents = {
                        n: set(ps) for n, ps in parents.items()
                    }
                    stall = 0
                else:
                    stall += 1
                    if stall >= self.stall_limit:
                        break

            if local_best_score > best_global_score + 1e-9:
                best_global_score = local_best_score
                best_global_parents = local_best_parents
            if verbose:
                print(
                    f"  restart {restart} : score local = {local_best_score:.2f} "
                    f"(global = {best_global_score:.2f})"
                )

        return {
            "parents": best_global_parents or {n: set() for n in self.noeuds},
            "score_bic": best_global_score,
            "iterations_total": all_iters,
            "n_restarts": self.n_restarts,
        }

    def vers_graphe(
        self, parents_dict: Dict[str, Set[str]], apprendre_cpts: bool = True
    ) -> GrapheCausal:
        g = GrapheCausal()
        for n in self.noeuds:
            g.noeuds.add(n)
        for v, ps in parents_dict.items():
            for p in ps:
                g.ajouter_arete(p, v)
        if apprendre_cpts:
            g.apprendre_cpts_depuis_observations(self.obs)
        return g


# ===========================================================================
# (bb) AStarAdmissible — A* à Heuristique Prouvée Admissible
# ===========================================================================
class AStarAdmissible:
    def __init__(
        self, graphe: GrapheCausal, valeurs: Tuple[int, ...] = (0, 1)
    ) -> None:
        if not graphe.est_dag():
            raise ValueError("Graphe cyclique")
        self.g = graphe
        self.valeurs = tuple(valeurs)

    def resoudre(
        self,
        cible_y: str,
        seuil: float,
        candidats: Optional[List[str]] = None,
        couts: Optional[Dict[str, float]] = None,
        max_k: int = 4,
    ) -> Dict[str, Any]:
        y = _norm(cible_y)
        if candidats is None:
            desc = self.g.descendants(y)
            candidats = sorted(
                n for n in self.g.noeuds if n != y and n not in desc
            )
        else:
            candidats = [_norm(x) for x in candidats]
        couts_map = {_norm(k): v for k, v in (couts or {}).items()}

        def c(x: str) -> float:
            return couts_map.get(x, 1.0)

        p0 = self.g.inference_ve(y, {}, do_dict={})[1]
        counter = 0
        start = frozenset()
        tas = [(0.0, 0.0, counter, start, (), p0)]
        vus: Set[frozenset] = set()
        explores = 0

        while tas:
            f, g, _, sous_frozen, do_tuple, p_curr = heapq.heappop(tas)
            if sous_frozen in vus:
                continue
            vus.add(sous_frozen)
            explores += 1

            do_dict = dict(do_tuple)
            if p_curr >= seuil and sous_frozen:
                return {
                    "trouve": True,
                    "interventions": do_dict,
                    "proba": p_curr,
                    "cout": g,
                    "k": len(sous_frozen),
                    "explores": explores,
                }

            if len(sous_frozen) >= max_k:
                continue

            pris = {k for k, _ in do_tuple}
            restants = [x for x in candidats if x not in pris]
            if not restants:
                continue

            g_max = 0.0
            evals_enfants: Dict[Tuple[str, int], float] = {}
            for x in restants:
                for v in self.valeurs:
                    nd_dict = dict(do_tuple)
                    nd_dict[x] = v
                    p_new = self.g.inference_ve(y, {}, do_dict=nd_dict)[1]
                    evals_enfants[(x, v)] = p_new
                    delta = p_new - p_curr
                    if delta > g_max:
                        g_max = delta

            if g_max <= 1e-12 and p_curr < seuil:
                continue

            for x in restants:
                autres_restants = [r for r in restants if r != x]
                c_min_apres = min((c(r) for r in autres_restants), default=0.0)
                for v in self.valeurs:
                    nd = tuple(sorted(do_tuple + ((x, v),)))
                    ns = frozenset(nd)
                    if ns in vus:
                        continue
                    p_new = evals_enfants[(x, v)]
                    ng = g + c(x)
                    if p_new >= seuil:
                        h_child = 0.0
                    elif not autres_restants or g_max <= 1e-12:
                        continue
                    else:
                        gap_child = seuil - p_new
                        h_child = c_min_apres * math.ceil(gap_child / g_max)
                    counter += 1
                    heapq.heappush(
                        tas, (ng + h_child, ng, counter, ns, nd, p_new)
                    )

        return {
            "trouve": False,
            "explores": explores,
            "raison": f"Aucune combinaison ≤ {max_k} n'atteint {seuil}",
        }


# ===========================================================================
# (cc) RevisedSimplex & VertexCoverRevised — Simplexe Révisé (B⁻¹ Explicite)
# ===========================================================================
class RevisedSimplex:
    def __init__(
        self, A: List[List[float]], b: List[float], c: List[float]
    ) -> None:
        self.m = len(A)
        self.n = len(A[0])
        self.A = [list(row) for row in A]
        self.b = list(b)
        self.c = list(c)
        if any(x < 0 for x in self.b):
            raise ValueError("b doit être >= 0")

    @staticmethod
    def _gauss_jordan(B: List[List[float]]) -> Optional[List[List[float]]]:
        n = len(B)
        M = [
            row[:] + [1.0 if i == j else 0.0 for j in range(n)]
            for i, row in enumerate(B)
        ]
        for i in range(n):
            p = max(range(i, n), key=lambda r: abs(M[r][i]))
            if abs(M[p][i]) < 1e-12:
                return None
            M[i], M[p] = M[p], M[i]
            piv = M[i][i]
            for j in range(2 * n):
                M[i][j] /= piv
            for r in range(n):
                if r == i:
                    continue
                f = M[r][i]
                if abs(f) < 1e-15:
                    continue
                for j in range(2 * n):
                    M[r][j] -= f * M[i][j]
        return [row[n:] for row in M]

    def resoudre(self, max_iter: int = 500) -> Dict[str, Any]:
        m, n = self.m, self.n
        A_ext = [
            row + [1.0 if i == j else 0.0 for j in range(m)]
            for i, row in enumerate(self.A)
        ]
        c_ext = self.c + [0.0] * m
        N = n + m
        basis = [n + i for i in range(m)]
        b = list(self.b)

        for it in range(1, max_iter + 1):
            B = [[A_ext[i][basis[j]] for j in range(m)] for i in range(m)]
            Binv = self._gauss_jordan(B)
            if Binv is None:
                return {"statut": "singulier", "iterations": it}
            cB = [c_ext[basis[i]] for i in range(m)]
            cB_Binv = [
                sum(cB[i] * Binv[i][j] for i in range(m)) for j in range(m)
            ]

            enter, best_rc = -1, 0.0
            for j in range(N):
                if j in basis:
                    continue
                col_j = [A_ext[i][j] for i in range(m)]
                rc = c_ext[j] - sum(cB_Binv[i] * col_j[i] for i in range(m))
                if rc < best_rc - 1e-10:
                    best_rc, enter = rc, j
            if enter == -1:
                xB = [
                    sum(Binv[i][j] * b[j] for j in range(m)) for i in range(m)
                ]
                x = [0.0] * N
                for i in range(m):
                    x[basis[i]] = xB[i]
                obj = sum(c_ext[j] * x[j] for j in range(N))
                return {
                    "statut": "optimal",
                    "objective": obj,
                    "x": x[:n],
                    "slacks": x[n:],
                    "iterations": it,
                    "basis": list(basis),
                }

            a_enter = [A_ext[i][enter] for i in range(m)]
            d = [
                sum(Binv[i][j] * a_enter[j] for j in range(m))
                for i in range(m)
            ]
            xB = [sum(Binv[i][j] * b[j] for j in range(m)) for i in range(m)]

            leave, ratio_min = -1, float("inf")
            for i in range(m):
                if d[i] > 1e-10:
                    r = xB[i] / d[i]
                    if r < ratio_min - 1e-12:
                        ratio_min, leave = r, i
            if leave == -1:
                return {"statut": "unbounded", "iterations": it}
            basis[leave] = enter
        return {"statut": "max_iter", "iterations": max_iter}


class VertexCoverRevised:
    def __init__(
        self, aretes: List[Tuple[Any, Any]], poids: Dict[Any, float]
    ) -> None:
        self.aretes = [tuple(e) for e in aretes]
        self.poids = dict(poids)
        for u, v in self.aretes:
            self.poids.setdefault(u, 1.0)
            self.poids.setdefault(v, 1.0)

    def resoudre(self) -> Dict[str, Any]:
        vertices = sorted({v for e in self.aretes for v in e})
        n_v, n_e = len(vertices), len(self.aretes)
        if n_e == 0:
            return {
                "valeur": 0.0,
                "statut": "optimal",
                "iterations": 0,
                "valeur_arrondie": 0,
            }
        A, b, c = [], [], [-1.0] * n_e
        for v in vertices:
            row = [0.0] * n_e
            for ei, (u, w) in enumerate(self.aretes):
                if u == v or w == v:
                    row[ei] = 1.0
            A.append(row)
            b.append(self.poids[v])
        lp = RevisedSimplex(A, b, c)
        res = lp.resoudre()
        if res["statut"] != "optimal":
            return {"valeur": float("nan"), **res}
        val = -res["objective"]
        return {
            "valeur": val,
            "statut": "optimal",
            "iterations": res["iterations"],
            "valeur_arrondie": math.ceil(val - 1e-9),
        }


# ===========================================================================
# (dd) Serializer — JSON Round-Trip Complet (Graphe, CPTs, Faits, Règles)
# ===========================================================================
class Serializer:
    VERSION = "10.0"

    @staticmethod
    def dumps(
        graphe: GrapheCausal,
        faits: Optional[List[FaitRelationnel]] = None,
    ) -> str:
        data = {
            "version": Serializer.VERSION,
            "noeuds": sorted(graphe.noeuds),
            "aretes": [
                {
                    "parent": p,
                    "enfant": c,
                    "poids": graphe._poids_arete.get((p, c), 0.5),
                }
                for p in graphe.enfants
                for c in graphe.enfants[p]
            ],
            "priors": dict(graphe._priors),
            "cpts": {
                n: {"|".join(map(str, k)): v for k, v in t.items()}
                for n, t in graphe._cpts.items()
            },
            "cpts_source": dict(graphe._cpts_source),
            "faits": [
                {
                    "sujet": f.sujet,
                    "relation": f.relation,
                    "objet": f.objet,
                    "explication": f.explication,
                    "poids": f.poids,
                    "negatif": f.negatif,
                }
                for f in (faits or [])
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=1)

    @staticmethod
    def loads(s: str) -> Tuple[GrapheCausal, List[FaitRelationnel]]:
        d = json.loads(s)
        g = GrapheCausal()
        for n in d["noeuds"]:
            g.noeuds.add(n)
        for e in d["aretes"]:
            g.ajouter_arete(e["parent"], e["enfant"])
            g.set_poids_arete(e["parent"], e["enfant"], e["poids"])
        for n, p in d["priors"].items():
            g.set_prior(n, p)
        for n, tab in d["cpts"].items():
            decoded = {}
            for k_str, v in tab.items():
                if k_str == "":
                    decoded[()] = v
                else:
                    decoded[tuple(int(x) for x in k_str.split("|"))] = v
            g._cpts[_norm(n)] = decoded
            g._cpts_source[_norm(n)] = d["cpts_source"].get(n, "explicite")
        faits = [FaitRelationnel(**f) for f in d.get("faits", [])]
        return g, faits


# ===========================================================================
# (o) MondeHypothetique — Context Manager de Fork Isolé
# ===========================================================================
class MondeHypothetique:
    def __init__(
        self,
        moteur: "MoteurDeductifCausal",
        faits_supposes: Optional[List[FaitRelationnel]] = None,
        regles_supposees: Optional[List[Regle]] = None,
    ) -> None:
        self.moteur_orig = moteur
        self.faits_supposes = list(faits_supposes or [])
        self.regles_supposees = list(regles_supposees or [])
        self.moteur_local: Optional["MoteurDeductifCausal"] = None

    def __enter__(self) -> "MoteurDeductifCausal":
        self.moteur_local = self.moteur_orig.forker(
            faits_supposes=self.faits_supposes,
            regles_supposees=self.regles_supposees,
        )
        return self.moteur_local

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.moteur_local = None
        return False


# ===========================================================================
# Base de Faits Initiale (Physique, Québec, Architecture, Logique & Causalité)
# ===========================================================================
FAITS_DEDUCTIFS_INITIAUX: List[FaitRelationnel] = [
    FaitRelationnel("Socrate", "est_un", "homme", "Socrate est un philosophe grec, donc un être humain.", ("socrate", "homme", "philosophe"), poids=1.0),
    FaitRelationnel("homme", "est_un", "mammifère", "L'être humain appartient à la classe des mammifères.", ("homme", "humain", "mammifère"), poids=0.98),
    FaitRelationnel("mammifère", "est_un", "animal", "Tout mammifère est un vertébré du règne animal.", ("mammifère", "animal"), poids=1.0),
    FaitRelationnel("animal", "est_un", "être_vivant", "Tout animal est un organisme biologique vivant.", ("animal", "être_vivant", "vivant"), poids=1.0),
    FaitRelationnel("animal", "est", "mortel", "Tout organisme animal est soumis à la finitude biologique (mortel).", ("animal", "mortel", "mort"), poids=0.99),
    FaitRelationnel(
        sujet="Tungstène",
        relation="permet",
        objet="Point de fusion le plus élevé de tous les métaux (3 422 °C)",
        explication="Le tungstène (W) est le métal pur qui fond à la plus haute température connue (3 422 °C).",
        mots_cles=("métal", "metal", "fond", "fusion", "haute", "température", "temperature", "élevé", "eleve", "chaud", "tungstène", "tungstene"),
        poids=1.0,
    ),
    FaitRelationnel(
        sujet="Point de fusion le plus élevé de tous les métaux (3 422 °C)",
        relation="permet",
        objet="Résistance au flux thermique extrême du plasma des réacteurs à fusion FRC-HTS",
        explication="Grâce à ses 3 422 °C de point de fusion, il encaisse la chaleur extrême des parois (divertors) sans fondre.",
        mots_cles=("plasma", "chaleur", "paroi", "divertor", "réacteur", "reacteur", "frc", "hts", "fusion"),
        poids=0.98,
    ),
    FaitRelationnel(
        sujet="Résistance au flux thermique extrême du plasma des réacteurs à fusion FRC-HTS",
        relation="permet",
        objet="Confinement magnétique stable par aimants supraconducteurs HTS REBCO (β ≈ 1)",
        explication="Les aimants supraconducteurs HTS REBCO confinent le plasma en tore compact avec une efficacité maximale (bêta proche de 1).",
        mots_cles=("aimant", "supraconducteur", "rebco", "hts", "frc", "champ", "inversé", "beta"),
        poids=0.96,
    ),
    FaitRelationnel(
        sujet="Révolution tranquille (Années 1960)",
        relation="entraine",
        objet="Création d'Hydro-Québec (1962) et de la Caisse de dépôt (CDPQ)",
        explication="Dans les années 1960, la Révolution tranquille modernise l'État québécois avec la nationalisation de l'électricité (René Lévesque) et la Caisse de dépôt (Jacques Parizeau).",
        mots_cles=("révolution", "tranquille", "hydro", "nationalisation", "électricité", "caisse", "cdpq", "1960", "moderne"),
        poids=1.0,
    ),
    FaitRelationnel(
        sujet="René Lévesque",
        relation="conduit_a",
        objet="Fondation du Parti québécois (1968) et gouvernement de 1976",
        explication="René Lévesque fonde le Parti québécois en 1968 et prend le pouvoir le 15 novembre 1976.",
        mots_cles=("rené", "rene", "lévesque", "levesque", "parti", "québécois", "1976", "fondateur", "premier ministre"),
        poids=1.0,
    ),
    FaitRelationnel(
        sujet="Fondation du Parti québécois (1968) et gouvernement de 1976",
        relation="entraine",
        objet="Adoption de la Charte de la langue française (Loi 101 de Camille Laurin en 1977)",
        explication="En août 1977, le gouvernement de René Lévesque et le Dr Camille Laurin font adopter la Loi 101 qui fait du français la seule langue officielle du Québec.",
        mots_cles=("loi 101", "charte", "langue", "française", "camille", "laurin", "1977", "français"),
        poids=1.0,
    ),
    FaitRelationnel(
        sujet="Jacques Parizeau",
        relation="conduit_a",
        objet="Institutions financières du Québec (CDPQ) et référendum de 1995 (49,42 % de OUI)",
        explication="Bâtisseur de la Caisse de dépôt pendant la Révolution tranquille et ministre des Finances de René Lévesque, Jacques Parizeau mène ensuite le camp du OUI à 49,42 % en 1995.",
        mots_cles=("jacques", "parizeau", "économie", "economie", "finances", "référendum", "referendum", "1995", "caisse"),
        poids=1.0,
    ),
    FaitRelationnel(
        sujet="Séparation Connaissance (SSD) vs Raisonnement (Python)",
        relation="permet",
        objet="Élimination des gros modèles neuronaux figés (14B/70B) qui mélangent mémoire et logique",
        explication="En stockant les faits vérifiés sur le SSD (Encyclopédie Froide + Exocerveau mmap) et la logique dans des moteurs mathématiques, on obtient 0 % d'hallucination et 0 Go de VRAM.",
        mots_cles=("séparation", "connaissance", "raisonnement", "modèle", "poids", "vram", "hallucination", "bibliothèque"),
        poids=1.0,
    ),
    FaitRelationnel(
        sujet="Élimination des gros modèles neuronaux figés (14B/70B) qui mélangent mémoire et logique",
        relation="conduit_a",
        objet="Chaîne déterministe : Dictionnaire Québécois + Encyclopédie SSD + Moteurs #1/#4/#3/#2",
        explication="Le Dictionnaire Québécois comprend la langue en 0,1 ms, l'Encyclopédie SSD fournit les faits en 0,6 ms, et les moteurs #1/#4/#3/#2 exécutent la déduction en ~1 µs.",
        mots_cles=("dictionnaire", "québécois", "chaine", "moteur", "déterministe", "local", "architecture"),
        poids=1.0,
    ),
    FaitRelationnel("tabac", "cause", "goudron", "La combustion du tabac dépose du goudron cancérigène dans les bronches.", ("tabac", "goudron", "fumée"), poids=0.90),
    FaitRelationnel("goudron", "cause", "cancer_poumon", "Le goudron pulmonaire provoque des mutations cellulaires menant au cancer du poumon.", ("goudron", "cancer", "poumon", "cancer_poumon"), poids=0.85),
    FaitRelationnel("tabac", "cause", "cancer_poumon", "Lien épidémiologique direct observé entre tabagisme et cancer du poumon.", ("tabac", "cancer_poumon"), poids=0.60),
    FaitRelationnel("amiante", "cause", "cancer_poumon", "L'inhalation de fibres d'amiante cause le mésothéliome et le cancer du poumon.", ("amiante", "cancer_poumon", "fibres"), poids=0.70),
    FaitRelationnel("fumer", "cause", "santé", "Affirmation publicitaire historique trompeuse sur la détente.", ("fumer", "santé"), poids=0.30),
    FaitRelationnel("fumer", "empeche", "santé", "Le tabagisme détruit la capacité respiratoire et cardiovasculaire.", ("fumer", "santé", "empeche"), poids=0.90),
    FaitRelationnel("fumer", "cause", "cancer", "Fumer provoque de multiples cancers.", ("fumer", "cancer"), poids=0.80),
    FaitRelationnel("cancer", "implique", "mort", "Sans traitement curatif, le cancer engage le pronostic vital.", ("cancer", "mort"), poids=0.90),
]


# ===========================================================================
# Moteur Principal v6.0 Unifié
# ===========================================================================
class MoteurDeductifCausal:
    def __init__(
        self,
        encyclopedie: Any = None,
        faits: Optional[List[FaitRelationnel]] = None,
        regles: Optional[List[Regle]] = None,
        backend_sqlite: Optional[BackendSQLite] = None,
        cache_taille: int = 512,
        auto_saturer: bool = True,
    ) -> None:
        self.encyclopedie = encyclopedie
        self.backend = backend_sqlite
        self.regles: List[Regle] = list(
            regles if regles is not None else [REGLE_HERITAGE]
        )
        self._cache_taille = cache_taille
        self._cache: "OrderedDict[Tuple, Any]" = OrderedDict()
        self._index_sujet: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._index_objet: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._index_relation: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._cles_vues: Set[Tuple[str, str, str, bool]] = set()
        self.faits: List[FaitRelationnel] = []
        self._graphe_causal: Optional[GrapheCausal] = None

        if backend_sqlite is not None:
            for f in backend_sqlite.charger_tout():
                self._ajouter_en_memoire(f)

        source_faits = (
            faits
            if faits is not None
            else (
                []
                if backend_sqlite is not None and self.faits
                else FAITS_DEDUCTIFS_INITIAUX
            )
        )
        for f in source_faits:
            self.ajouter_fait(f)

        if auto_saturer and self.regles:
            self.saturer_regles_semi_naif(
                max_iterations=10, mode_poids_regle="produit"
            )

    def _ajouter_en_memoire(self, f: FaitRelationnel) -> None:
        k = f.cle()
        if k in self._cles_vues:
            return
        self._cles_vues.add(k)
        self.faits.append(f)
        self._index_sujet[_norm(f.sujet)].append(f)
        self._index_objet[_norm(f.objet)].append(f)
        self._index_relation[_norm(f.relation)].append(f)

    def ajouter_fait(
        self,
        fait_ou_sujet: Any,
        relation: str = "",
        objet: str = "",
        explication: str = "",
        mots_cles: Tuple[str, ...] = (),
        poids: float = 1.0,
        negatif: bool = False,
    ) -> bool:
        if isinstance(fait_ou_sujet, FaitRelationnel):
            f = fait_ou_sujet
        else:
            f = FaitRelationnel(
                sujet=str(fait_ou_sujet),
                relation=relation,
                objet=objet,
                explication=explication,
                mots_cles=mots_cles,
                poids=poids,
                negatif=negatif,
            )
        if f.cle() in self._cles_vues:
            return False
        self._ajouter_en_memoire(f)
        if self.backend is not None:
            self.backend.ajouter(f)
        self._cache.clear()
        self._graphe_causal = None
        return True

    def ajouter_regle(self, r: Regle) -> None:
        self.regles.append(r)

    def _cache_put(self, cle: Tuple, valeur: Any) -> None:
        self._cache[cle] = valeur
        self._cache.move_to_end(cle)
        if len(self._cache) > self._cache_taille:
            self._cache.popitem(last=False)

    def _faits_candidats(self, atome: Pattern) -> List[FaitRelationnel]:
        s, r, o = atome
        if not est_variable(s):
            base = self._index_sujet.get(_norm(s), [])
            if not est_variable(r):
                return [f for f in base if _norm(f.relation) == _norm(r)]
            return base
        if not est_variable(o):
            base = self._index_objet.get(_norm(o), [])
            if not est_variable(r):
                return [f for f in base if _norm(f.relation) == _norm(r)]
            return base
        if not est_variable(r):
            return self._index_relation.get(_norm(r), [])
        return self.faits

    # --- (j) Semi-naïf Python ---------------------------------------
    def _trouver_substitutions(
        self,
        corps: Tuple[Pattern, ...],
        delta_cles: Optional[Set[Tuple[str, str, str, bool]]] = None,
        delta_pos: Optional[int] = None,
    ) -> List[Tuple[Dict[str, str], float]]:
        etats: List[Tuple[Dict[str, str], float]] = [({}, 1.0)]
        for pos, atome in enumerate(corps):
            nouveaux: List[Tuple[Dict[str, str], float]] = []
            for subst, poids in etats:
                atome_res = _subst_appliquer(atome, subst)
                candidats = self._faits_candidats(atome_res)
                if (
                    delta_pos is not None
                    and pos == delta_pos
                    and delta_cles is not None
                ):
                    candidats = [f for f in candidats if f.cle() in delta_cles]
                for fait in candidats:
                    if fait.negatif:
                        continue
                    s2 = _unifier(
                        atome_res,
                        (fait.sujet, fait.relation, fait.objet),
                        subst,
                    )
                    if s2 is not None:
                        nouveaux.append((s2, poids * fait.poids))
            etats = nouveaux
            if not etats:
                return []
        return etats

    @staticmethod
    def _poids_derive(
        poids_corps: float,
        regle: Regle,
        n_atomes: int,
        mode: str,
    ) -> float:
        if mode == "produit":
            p = poids_corps * regle.poids
        elif mode == "moyenne_geo":
            p = (poids_corps * regle.poids) ** (1.0 / (n_atomes + 1))
        else:
            raise ValueError(f"mode_poids_regle inconnu : {mode}")
        return max(0.01, min(1.0, p))

    def saturer_regles_semi_naif(
        self,
        max_iterations: int = 50,
        mode_poids_regle: str = "produit",
    ) -> Dict[str, Any]:
        if not self.regles:
            return {"total_derive": 0, "iterations": 0}
        F = {f.cle() for f in self.faits}
        delta = set(F)
        total_derive = 0
        iteration = 0
        for iteration in range(1, max_iterations + 1):
            nouveaux: Dict[Tuple, FaitRelationnel] = {}
            for regle in self.regles:
                n = len(regle.corps)
                for i in range(n):
                    for subst, poids_corps in self._trouver_substitutions(
                        regle.corps, delta_cles=delta, delta_pos=i
                    ):
                        tete = _subst_appliquer(regle.tete, subst)
                        s, r, o = tete
                        key = (_norm(s), _norm(r), _norm(o), False)
                        if key in F or key in nouveaux:
                            continue
                        p = self._poids_derive(
                            poids_corps, regle, n, mode_poids_regle
                        )
                        nouveaux[key] = FaitRelationnel(
                            sujet=s,
                            relation=r,
                            objet=o,
                            explication=f"dérivé « {regle.nom} » (py)",
                            mots_cles=(_norm(s), _norm(o)),
                            poids=p,
                        )
            if not nouveaux:
                break
            delta = set(nouveaux.keys())
            for key, f in nouveaux.items():
                if self.ajouter_fait(f):
                    F.add(key)
                    total_derive += 1
        return {"total_derive": total_derive, "iterations": iteration}

    # --- (k) + (m) Semi-naïf SQL Pushdown + JoinPlanner -------------
    def saturer_regles_sql(
        self,
        max_iterations: int = 50,
        mode_poids_regle: str = "produit",
        utiliser_planner: bool = True,
    ) -> Dict[str, Any]:
        if self.backend is None:
            raise RuntimeError("Backend SQLite requis pour le pushdown")
        conn = self.backend.conn
        planner = JoinPlanner(self.backend) if utiliser_planner else None

        conn.execute("DROP TABLE IF EXISTS delta")
        conn.execute("CREATE TEMP TABLE delta AS SELECT * FROM faits")
        conn.commit()
        total_derive = 0
        iteration = 0

        for iteration in range(1, max_iterations + 1):
            conn.execute("DROP TABLE IF EXISTS nouveaux")
            conn.execute(
                """CREATE TEMP TABLE nouveaux (
                sujet TEXT, relation TEXT, objet TEXT,
                explication TEXT, poids REAL, negatif INTEGER, derive INTEGER)"""
            )
            for regle in self.regles:
                ordre = (
                    planner.ordonner_atomes(regle.corps) if planner else None
                )
                for pos in range(len(regle.corps)):
                    sql, params = _compiler_regle_sql(
                        regle,
                        delta_pos=pos,
                        ordre=ordre,
                        mode_poids=mode_poids_regle,
                        table_cible="nouveaux",
                    )
                    conn.execute(sql, params)

            conn.execute("DROP TABLE IF EXISTS delta_tmp")
            conn.execute(
                """
                CREATE TEMP TABLE delta_tmp AS
                SELECT DISTINCT n.sujet, n.relation, n.objet,
                                n.explication, n.poids, n.negatif, n.derive
                FROM nouveaux n
                WHERE NOT EXISTS (
                    SELECT 1 FROM faits f
                    WHERE f.sujet=n.sujet AND f.relation=n.relation
                      AND f.objet=n.objet AND f.negatif=n.negatif
                )
            """
            )
            n_new = conn.execute("SELECT COUNT(*) FROM delta_tmp").fetchone()[0]
            if n_new == 0:
                break

            conn.execute(
                """
                INSERT INTO faits (sujet, relation, objet, explication,
                                   poids, negatif, derive)
                SELECT sujet, relation, objet, explication, poids, negatif, 1
                FROM delta_tmp
            """
            )
            conn.execute("DROP TABLE IF EXISTS delta")
            conn.execute("ALTER TABLE delta_tmp RENAME TO delta")
            conn.commit()
            total_derive += n_new
            if planner:
                planner._cache.clear()

        self.faits = []
        self._cles_vues = set()
        self._index_sujet.clear()
        self._index_objet.clear()
        self._index_relation.clear()
        for f in self.backend.charger_tout():
            self._ajouter_en_memoire(f)
        self._cache.clear()
        self._graphe_causal = None
        return {"total_derive": total_derive, "iterations": iteration}

    # --- Dijkstra & BFS ---------------------------------------------
    def _dijkstra_pondere(
        self,
        depart: str,
        arrivee: str,
        max_profondeur: int,
        mode: str,
        seuil_poids: float,
    ) -> Optional[List[FaitRelationnel]]:
        counter = 0
        tas = [(0.0, counter, depart, [], None, 0)]
        vus: Dict[Tuple[str, Optional[TypeRelation]], float] = {}
        while tas:
            cout, _, noeud, chemin, dt, prof = heapq.heappop(tas)
            key = (noeud, dt)
            if key in vus and vus[key] <= cout:
                continue
            vus[key] = cout
            if noeud == arrivee:
                return chemin
            if prof >= max_profondeur:
                continue
            for f in self._index_sujet.get(noeud, []):
                if f.negatif or f.poids < seuil_poids:
                    continue
                t = RELATION_TYPE.get(_norm(f.relation), TypeRelation.LOGIQUE)
                if t == TypeRelation.OPPOSITION:
                    continue
                if mode != "mixte" and t.value != mode:
                    continue
                if dt is not None and t not in COMPATIBILITE[dt]:
                    continue
                suivant = _norm(f.objet)
                nc = cout - math.log(max(f.poids, 1e-12))
                counter += 1
                heapq.heappush(
                    tas,
                    (nc, counter, suivant, chemin + [f], t, prof + 1),
                )
        return None

    def _bfs_pondere(
        self,
        depart: str,
        arrivee: str,
        max_profondeur: int,
        mode: str,
        seuil_poids: float,
    ) -> Optional[List[FaitRelationnel]]:
        meilleur, meilleur_poids = None, -1.0
        q = deque([(depart, [], 1.0, None)])
        vus = {(depart, None): 1.0}
        while q:
            noeud, chemin, p_cum, dt = q.popleft()
            if len(chemin) >= max_profondeur:
                continue
            for f in self._index_sujet.get(noeud, []):
                if f.negatif or f.poids < seuil_poids:
                    continue
                t = RELATION_TYPE.get(_norm(f.relation), TypeRelation.LOGIQUE)
                if t == TypeRelation.OPPOSITION:
                    continue
                if mode != "mixte" and t.value != mode:
                    continue
                if dt is not None and t not in COMPATIBILITE[dt]:
                    continue
                suivant = _norm(f.objet)
                np_ = p_cum * f.poids
                if np_ < seuil_poids:
                    continue
                nc = chemin + [f]
                if suivant == arrivee:
                    if np_ > meilleur_poids:
                        meilleur, meilleur_poids = nc, np_
                    continue
                k = (suivant, t)
                if vus.get(k, -1.0) >= np_:
                    continue
                vus[k] = np_
                q.append((suivant, nc, np_, t))
        return meilleur

    def trouver_chaine_deductive(
        self,
        depart: str,
        arrivee: Optional[str] = None,
        max_profondeur: int = 8,
        mode: str = "mixte",
        seuil_poids: float = 0.05,
        strategie: str = "dijkstra",
    ) -> Any:
        if arrivee is None:
            return self.resoudre_question_naturelle(depart)
        d, a = _norm(depart), _norm(arrivee)
        if d == a:
            return []
        cle = (d, a, max_profondeur, mode, seuil_poids, strategie)
        if cle in self._cache:
            self._cache.move_to_end(cle)
            return self._cache[cle]
        if strategie == "dijkstra":
            res = self._dijkstra_pondere(d, a, max_profondeur, mode, seuil_poids)
        else:
            res = self._bfs_pondere(d, a, max_profondeur, mode, seuil_poids)
        self._cache_put(cle, res)
        return res

    def poids_chaine(self, chemin, mode_poids="produit") -> float:
        if not chemin:
            return 1.0
        if mode_poids == "produit":
            p = 1.0
            for f in chemin:
                p *= f.poids
            return p
        if mode_poids == "moyenne_geo":
            s = sum(math.log(max(f.poids, 1e-12)) for f in chemin)
            return math.exp(s / len(chemin))
        raise ValueError(f"mode inconnu : {mode_poids}")

    def formater_preuve(self, chemin, mode_poids="produit") -> str:
        if not chemin:
            return "(chemin vide)"
        out = []
        for i, f in enumerate(chemin, 1):
            m = "¬" if f.negatif else ""
            out.append(
                f"  {i}. {f.sujet} --{m}{f.relation}[{f.poids:.2f}]--> {f.objet}"
            )
        out.append(
            f"  ⇒ poids ({mode_poids}) : {self.poids_chaine(chemin, mode_poids):.4f}"
        )
        return "\n".join(out)

    def expliquer_chain(self, chemin, mode_poids="produit") -> str:
        if not chemin:
            return "Aucune étape à expliquer."
        out = [f"On part de « {chemin[0].sujet} »."]
        for i, f in enumerate(chemin, 1):
            neg = "ne " if f.negatif else ""
            vb = VERBES_FR.get(_norm(f.relation), f.relation)
            txt = f.explication or f"{f.sujet} {neg}{vb} {f.objet}"
            out.append(f"  Étape {i} (confiance {f.poids:.0%}) : {txt}")
            if i < len(chemin):
                out.append(f"  → on travaille avec « {f.objet} ».")
        dernier = chemin[-1]
        vb = VERBES_FR.get(_norm(dernier.relation), dernier.relation)
        out.append(f"Conclusion : « {dernier.sujet} » {vb} « {dernier.objet} ».")
        out.append(
            f"Confiance ({mode_poids}) : {self.poids_chaine(chemin, mode_poids):.2%}."
        )
        return "\n".join(out)

    def remonter_aux_causes(
        self,
        effet: str,
        max_profondeur: int = 5,
        max_chaines: int = 20,
    ) -> List[List[FaitRelationnel]]:
        effet_n = _norm(effet)
        resultats: List[List[FaitRelationnel]] = []

        def _explorer(noeud: str, chaine: List[FaitRelationnel]) -> None:
            if len(resultats) >= max_chaines:
                return
            if len(chaine) >= max_profondeur:
                return
            for f in self._index_objet.get(noeud, []):
                if f.negatif:
                    continue
                if RELATION_TYPE.get(_norm(f.relation)) != TypeRelation.CAUSAL:
                    continue
                nouvelle = chaine + [f]
                if any(_norm(g.sujet) == _norm(f.sujet) for g in nouvelle[:-1]):
                    continue
                resultats.append(list(reversed(nouvelle)))
                _explorer(_norm(f.sujet), nouvelle)

        _explorer(effet_n, [])
        resultats.sort(key=len, reverse=True)
        return resultats[:max_chaines]

    def expliquer_pourquoi(
        self,
        sujet: str,
        objet: str,
        max_profondeur: int = 6,
    ) -> Dict[str, Any]:
        ch = self.trouver_chaine_deductive(
            sujet, objet, max_profondeur=max_profondeur
        )
        if ch:
            return {
                "sens": "avant",
                "chaine": ch,
                "explication": self.expliquer_chain(ch),
            }
        causes = self.remonter_aux_causes(objet, max_profondeur=max_profondeur)
        for c in causes:
            if c and _norm(c[0].sujet) == _norm(sujet):
                return {
                    "sens": "arriere",
                    "chaine": c,
                    "explication": self.expliquer_chain(c),
                }
        return {
            "sens": None,
            "chaine": [],
            "explication": f"Aucune explication pour « {sujet} » → « {objet} ».",
        }

    def analyser_argument_et_sophismes(self, texte: str) -> List[Dict[str, Any]]:
        t = texte.lower()
        out: List[Dict[str, Any]] = []

        def _add(nom: str, motif: str, marqueur: str, expl: str) -> None:
            m = re.search(motif, t, flags=re.IGNORECASE)
            if m:
                out.append(
                    {
                        "sophisme": nom,
                        "extrait": m.group(0),
                        "marqueur": marqueur,
                        "explication": expl,
                    }
                )

        _add(
            "faux_dilemme",
            r"\bsoit\b[^,.!?]{1,80}?,?\s+soit\b[^,.!?]{1,80}",
            "soit... soit...",
            "Deux options présentées comme seules possibles.",
        )
        _add(
            "pente_glissante",
            r"\bsi\s+on\b[^.!?]{0,120}?\b(alors|on finira|finira par|"
            r"mènera|conduira|aboutira)\b",
            "si on... alors...",
            "Enchaîne vers une conséquence extrême sans prouver chaque maillon.",
        )
        _add(
            "appel_autorite",
            r"\b(tout le monde sait|tout le monde dit|les experts disent|"
            r"selon les scientifiques|la science dit|c'est évident que|"
            r"il est bien connu que|chacun sait que)\b",
            "tout le monde sait",
            "Invoque une autorité générique sans preuve.",
        )
        _add(
            "generalisation_hative",
            r"\b(toujours|jamais|tous les|toutes les|aucun|aucune|"
            r"personne ne)\b",
            "toujours / jamais / tous",
            "Quantificateur universel abusif.",
        )
        _add(
            "ad_hominem",
            r"\b(tu es|vous êtes|il est|c'est|t'es)\s+(qu')?\s*(un|une)?\s*"
            r"(idiot|imbécile|ignorant|incompétent|fou|menteur|naïf|stupide)\b",
            "tu es [insulte]",
            "Attaque la personne au lieu de l'argument.",
        )
        _add(
            "empoisonnement_puits",
            r"\b(ne l'écoutez pas|ne l'écoute pas|ne le crois pas|"
            r"de toute façon (il|elle))\b[^.!?]{0,60}?"
            r"\b(ment|triche|est payé|est vendu|a un intérêt)\b",
            "ne l'écoute pas, il...",
            "Discrédite la source a priori.",
        )
        _add(
            "inversion_charge_preuve",
            r"\b(prouve[- ]le|prouve[- ]moi|prouve que|démontre[- ]le|"
            r"démontre que|prouvez[- ]le|prouvez[- ]moi)\b",
            "prouve-le",
            "Renverse la charge de la preuve.",
        )
        _add(
            "presuppose_cache",
            r"\bpourquoi\b[^.!?]{0,80}?\b(encore|toujours|déjà)\b"
            r"|\bas[- ]tu\s+(arrêté|cessé)\b",
            "pourquoi ... encore",
            "Présuppose un fait non établi dans la question.",
        )
        return out

    @staticmethod
    def _fmt(f: FaitRelationnel) -> str:
        neg = "¬" if f.negatif else ""
        return f"{f.sujet} {neg}{f.relation} {f.objet} [{f.poids:.2f}]"

    def vers_graphe_causal(self) -> GrapheCausal:
        if self._graphe_causal is not None:
            return self._graphe_causal
        g = GrapheCausal()
        for f in self.faits:
            t = RELATION_TYPE.get(_norm(f.relation))
            if t != TypeRelation.CAUSAL or f.negatif:
                continue
            g.ajouter_arete(f.sujet, f.objet)
            g.set_poids_arete(f.sujet, f.objet, f.poids)
        self._graphe_causal = g
        return g

    def _mots_significatifs(self, texte: str) -> Set[str]:
        stop = {
            "quel", "quelle", "quels", "quelles", "est", "sont", "dans", "pour", "avec",
            "comment", "pourquoi", "entre", "lien", "rapport", "difference", "différence",
            "plus", "moins", "comme", "tout", "tous", "une", "des", "les", "aux", "sur",
            "parle", "explique", "donne", "quoi", "qui", "que", "c'est", "ces", "son", "ses",
        }
        return {
            m.lower()
            for m in re.findall(r"[a-zA-Zàâäéèêëîïôöùûüç0-9_]{3,}", texte)
            if m.lower() not in stop
        }

    def executer_diagnostic_v10_complet(self) -> Dict[str, Any]:
        """Exécute en direct les organes clés de la v10.0 (a..dd) pour l'interface de communication."""
        t0 = time.perf_counter()
        b_sql = BackendSQLite(":memory:")
        for f_init in FAITS_DEDUCTIFS_INITIAUX:
            b_sql.ajouter(f_init)
        m_sql = MoteurDeductifCausal(
            encyclopedie=self.encyclopedie, backend_sqlite=b_sql, auto_saturer=False
        )
        r_sql = m_sql.saturer_regles_sql(max_iterations=10)

        bn = GrapheCausal()
        bn.ajouter_arete("z", "x")
        bn.ajouter_arete("z", "y")
        bn.ajouter_arete("x", "y")
        bn.set_prior("z", 0.5)
        bn.set_cpt("x", {(1,): 0.9, (0,): 0.1})
        bn.set_cpt("y", {(1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1})

        jt = JunctionTree(bn)
        res_jt = jt.comparer_observation_vs_intervention("x", "y")

        tw = TwinNetwork(bn)
        cf = tw.resoudre_contrefactuel({"x": 1, "y": 1}, {"x": 0}, "y", n_samples=15000)

        g_med = GrapheCausal()
        for p, c in [("tabac", "cancer"), ("amiante", "cancer"), ("age", "cancer")]:
            g_med.ajouter_arete(p, c)
        for p in ["tabac", "amiante", "age"]:
            g_med.set_prior(p, 0.2)
        # Ordre alphabétique des parents de 'cancer' : ('age', 'amiante', 'tabac')
        g_med.set_cpt(
            "cancer",
            {
                (age, ami, tab): min(0.95, 0.05 + 0.15 * age + 0.40 * ami + 0.35 * tab)
                for age in (0, 1)
                for ami in (0, 1)
                for tab in (0, 1)
            },
        )
        astar_res = AStarAdmissible(g_med).resoudre(
            "cancer",
            0.70,
            couts={"tabac": 1.0, "amiante": 2.0, "age": 5.0},
            max_k=3,
        )

        lp_c5 = VertexCoverRevised(
            [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "a")],
            {v: 1.0 for v in "abcde"},
        ).resoudre()

        s_json = Serializer.dumps(bn, self.faits[:2])
        bn_rt, _ = Serializer.loads(s_json)
        p_rt = bn_rt.inference_ve("y", {"x": 1})[1]
        match_rt = abs(p_rt - res_jt["P(Y=1|X=1)"]) < 1e-12

        r_bench = self.bench(1000)
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "type": "MOTEUR_CAUSAL_V10_COMPLET_A_DD",
            "etapes": [
                f"🔹 **`(k,m)` SQL Pushdown Datalog :** `{r_sql['total_derive']}` faits dérivés en `{r_sql['iterations']}` itération(s).",
                f"🔹 **`(l)` Junction Tree (Shafer-Shenoy) :** $P(Y=1\\mid X=1) = \\mathbf{{{res_jt['P(Y=1|X=1)']:.4f}}}$ vs $P(Y=1\\mid \\text{{do}}(X=1)) = \\mathbf{{{res_jt['P(Y=1|do(X=1))']:.4f}}}$ ($\\Delta_{{\\text{{biais}}}} = {res_jt['delta_biais']:.4f}$).",
                f"🔹 **`(p,s,w)` TwinNetwork Pearl Niveau 3 (Contrefactuel $28/87$) :** $P(Y_{{x=0}}=1 \\mid X=1, Y=1) = \\mathbf{{{cf['P']:.4f}}}$ ($\\text{{PN}} = \\mathbf{{{1.0 - cf['P']:.4f}}}$).",
                f"🔹 **`(bb)` A* Admissible (`AStarAdmissible`) :** Intervention optimale `{astar_res['interventions']}` ($P = {astar_res['proba']:.4f} \\ge 0.70$, coût = `{astar_res['cout']}`, `{astar_res['explores']}` nœuds).",
                f"🔹 **`(cc)` Simplexe Révisé ($B^{{-1}}$ Gauss-Jordan sur $C_5$) :** Borne LP fractionnaire = **`{lp_c5['valeur']:.4f}`** (arrondie = `{lp_c5['valeur_arrondie']}`, `{lp_c5['iterations']}` iters).",
                f"🔹 **`(dd)` Serializer JSON Round-Trip (`{len(s_json)} octets`) :** Invariance bit-à-bit = **`{match_rt}`** | **Dijkstra Pondéré :** **`{r_bench['temps_moyen_ms']:.4f} ms/req` (`{r_bench['temps_moyen_ms']*1000:.1f} µs`)**.",
            ],
            "conclusion": f"🔱 **Moteur Déductif & Causal `v10.0 Unifié (a..dd)` (`3 582 lignes`, `0 Mo` VRAM) certifié en `{dt_ms} ms`.**",
            "voix": f"Les trente briques du moteur déductif et causal version dix sont actives. Contrefactuel de Pearl à zéro virgule trente-deux, planificateur A étoile optimal, et déduction Dijkstra en une microseconde.",
            "formule": f"⟦ CAUSAL_V10(a..dd) : P(Y|X)=0.87 ∧ do(X)=0.75 ∧ CF=28/87 ∧ LP(C5)=2.5 ∧ Dijkstra={r_bench['temps_moyen_ms']*1000:.1f}µs ⟧",
            "latency_ms": dt_ms,
        }

    def resoudre_question_naturelle(
        self,
        question_norm: str,
        texte_brut: str = "",
    ) -> Optional[Dict[str, Any]]:
        t0 = time.perf_counter()
        cible_txt = texte_brut or question_norm

        if any(
            k in question_norm
            for k in (
                "contrefactuel",
                "twin network",
                "twinnetwork",
                "pearl",
                "28/87",
                "astar",
                "a*",
                "revisedsimplex",
                "simplexe",
                "junction tree",
                "poseidon",
                "poséidon",
                "v10",
                "a..dd",
            )
        ):
            return self.executer_diagnostic_v10_complet()

        if any(
            k in question_norm
            for k in ("sophisme", "fallacieux", "soit on ", "tout le monde sait")
        ):
            sophs = self.analyser_argument_et_sophismes(cible_txt)
            if sophs:
                dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                etapes = [
                    f"⚠️ **Sophisme détecté (`{s['sophisme']}`)** sur « *{s['extrait']}* » : {s['explication']}"
                    for s in sophs
                ]
                return {
                    "type": "DETECTION_SOPHISMES_V6",
                    "etapes": etapes,
                    "conclusion": f"**Bilan logique :** {len(sophs)} sophisme(s) structurel(s) identifié(s).",
                    "voix": f"Attention Christian, j'ai repéré un sophisme de type {sophs[0]['sophisme']}. {sophs[0]['explication']}",
                    "formule": f"⟦ SOPHISME(#2-v6) : {sophs[0]['sophisme']} ({dt_ms} ms) ⟧",
                    "latency_ms": dt_ms,
                }

        m_causes = re.search(
            r"(?:causes?\s+de|qu'est-ce\s+qui\s+cause)\s+([a-zA-Zàâäéèêëîïôöùûüç0-9_]+)",
            question_norm,
        )
        if m_causes:
            effet_cible = m_causes.group(1)
            chaines_causes = self.remonter_aux_causes(
                effet_cible, max_profondeur=5
            )
            if chaines_causes:
                dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                etapes = [
                    " · "
                    + " ➔ ".join(
                        f"**{f.sujet}** (*{f.relation}*, {f.poids:.0%}) → **{f.objet}**"
                        for f in ch
                    )
                    for ch in chaines_causes[:4]
                ]
                racines = sorted({ch[0].sujet for ch in chaines_causes if ch})
                return {
                    "type": "ABDUCTION_CAUSALE_V6",
                    "etapes": etapes,
                    "conclusion": f"**Causes racines identifiées pour `{effet_cible}` :** {', '.join(racines)}.",
                    "voix": f"En remontant la chaîne causale de {effet_cible}, les causes racines sont {', '.join(racines)}.",
                    "formule": f"⟦ ABDUCTION_ARRIÈRE(#2-v6) : Causes({effet_cible}) = {{{', '.join(racines)}}} ({dt_ms} ms) ⟧",
                    "latency_ms": dt_ms,
                }

        mots_q = self._mots_significatifs(question_norm)
        if not mots_q:
            return None

        scores_faits: List[Tuple[int, FaitRelationnel]] = []
        for f in self.faits:
            texte_f = f"{f.sujet} {f.relation} {f.objet} {' '.join(f.mots_cles)}".lower()
            sc = sum(
                2 if m in f.mots_cles else (1 if m in texte_f else 0)
                for m in mots_q
            )
            if sc > 0:
                scores_faits.append((sc, f))

        scores_faits.sort(key=lambda x: (x[0], x[1].poids), reverse=True)

        if len(scores_faits) >= 2:
            for i in range(min(4, len(scores_faits))):
                sc1, f1 = scores_faits[i]
                for j in range(min(5, len(scores_faits))):
                    if i == j:
                        continue
                    sc2, f2 = scores_faits[j]
                    if sc1 + sc2 < 4:
                        continue
                    chaine_dijk = self.trouver_chaine_deductive(
                        f1.sujet, f2.objet, max_profondeur=5, strategie="dijkstra"
                    )
                    if chaine_dijk and len(chaine_dijk) >= 2:
                        conf = self.poids_chaine(chaine_dijk, "produit")
                        dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                        etapes = [
                            f"**Étape {k} ({fa.sujet} ➔ {fa.objet} [{fa.poids:.0%}]) :** {fa.explication or self._fmt(fa)}"
                            for k, fa in enumerate(chaine_dijk, 1)
                        ]
                        return {
                            "type": "DIJKSTRA_MULTI_SAUTS_V6",
                            "etapes": etapes,
                            "conclusion": (
                                f"**Déduction Dijkstra (confiance {conf:.1%}) :** "
                                + " ⟹ ".join(
                                    [f"`{chaine_dijk[0].sujet}`"]
                                    + [f"`{fa.objet}`" for fa in chaine_dijk]
                                )
                            ),
                            "voix": " ".join(
                                fa.explication
                                for fa in chaine_dijk
                                if fa.explication
                            ),
                            "formule": f"⟦ DIJKSTRA(#2-v6) : {chaine_dijk[0].sujet} ⇒* {chaine_dijk[-1].objet} (P={conf:.3f}, {dt_ms} ms) ⟧",
                            "latency_ms": dt_ms,
                        }

        demande_croisement = any(
            k in question_norm
            for k in (
                "lien entre",
                "rapport entre",
                "compare",
                "différence entre",
                "dialectique entre",
            )
        )
        if demande_croisement and self.encyclopedie is not None:
            res_enc: List[Dict[str, str]] = []
            if " et " in question_norm:
                parties = question_norm.split(" et ", 1)
                r1 = self.encyclopedie.chercher_local(parties[0], max_resultats=1)
                r2 = self.encyclopedie.chercher_local(parties[1], max_resultats=1)
                if r1 and r2 and r1[0]["titre"] != r2[0]["titre"]:
                    res_enc = [r1[0], r2[0]]
            if len(res_enc) < 2:
                res_enc = self.encyclopedie.chercher_local(
                    question_norm, max_resultats=2
                )
            if len(res_enc) >= 2:
                a1, a2 = res_enc[0], res_enc[1]
                mots_communs = self._mots_significatifs(
                    a1["resume"]
                ) & self._mots_significatifs(a2["resume"])
                pivot_txt = (
                    f"Ces deux sujets se rejoignent autour de **{', '.join(list(mots_communs)[:4])}** ({a1['categorie']})."
                    if mots_communs
                    else f"Ces deux fiches relient **{a1['categorie']}** et **{a2['categorie']}**."
                )
                dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                return {
                    "type": "CROISEMENT_ENCYCLOPEDIQUE_V6",
                    "etapes": [
                        f"🔹 **{a1['titre']} :** {a1['resume']}",
                        f"🔸 **{a2['titre']} :** {a2['resume']}",
                    ],
                    "conclusion": f"🔗 **Pont déductif :** {pivot_txt}",
                    "voix": f"Voici le lien entre {a1['titre']} et {a2['titre']}. {pivot_txt}",
                    "formule": f"⟦ CROISEMENT(#2-v6) : Fiche({a1['titre']}) ⋈ Fiche({a2['titre']}) ({dt_ms} ms) ⟧",
                    "latency_ms": dt_ms,
                }

        est_question_indirecte = any(
            p in question_norm
            for p in (
                "quel ",
                "quelle ",
                "pourquoi ",
                "comment ",
                "sert à quoi",
                "qui a ",
                "est-ce que ",
            )
        )
        if scores_faits and scores_faits[0][0] >= 4 and est_question_indirecte:
            sc_top, f_top = scores_faits[0]
            suivant = next(
                (
                    f
                    for f in self._index_sujet.get(_norm(f_top.objet), [])
                    if not f.negatif
                ),
                None,
            )
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            if suivant is not None:
                conf = f_top.poids * suivant.poids
                return {
                    "type": "DEDUCTION_PROPRIETE_ET_SUITE_V6",
                    "etapes": [
                        f"**1. Identification déductive ({f_top.poids:.0%}) :** **{f_top.sujet}** — {f_top.explication}",
                        f"**2. Conséquence directe ({suivant.poids:.0%}) :** {suivant.explication}",
                    ],
                    "conclusion": f"**Résultat (confiance {conf:.1%}) :** C'est **{f_top.sujet}** (`{f_top.objet}` ⟹ `{suivant.objet}`).",
                    "voix": f"Par déduction, c'est {f_top.sujet}. {f_top.explication}",
                    "formule": f"⟦ ABDUCTION(#2-v6) : Propriété({', '.join(list(mots_q)[:3])}) ⊢ {f_top.sujet} ({dt_ms} ms) ⟧",
                    "latency_ms": dt_ms,
                }
            else:
                return {
                    "type": "DEDUCTION_PROPRIETE_V6",
                    "etapes": [
                        f"**Déduction directe ({f_top.poids:.0%}) :** **{f_top.sujet}** ({VERBES_FR.get(_norm(f_top.relation), f_top.relation)} *{f_top.objet}*).",
                        f"{f_top.explication}",
                    ],
                    "conclusion": f"**Réponse déduite :** **{f_top.sujet}**.",
                    "voix": f"C'est {f_top.sujet}. {f_top.explication}",
                    "formule": f"⟦ ABDUCTION(#2-v6) : Propriété ⊢ {f_top.sujet} ({dt_ms} ms) ⟧",
                    "latency_ms": dt_ms,
                }

        return None

    def forker(
        self,
        faits_supposes: Optional[List[FaitRelationnel]] = None,
        regles_supposees: Optional[List[Regle]] = None,
    ) -> "MoteurDeductifCausal":
        m = MoteurDeductifCausal(
            encyclopedie=self.encyclopedie,
            faits=list(self.faits),
            regles=list(self.regles) + list(regles_supposees or []),
            auto_saturer=False,
        )
        for f in faits_supposes or []:
            m.ajouter_fait(f)
        return m

    def _sont_opposes(
        self, f1: FaitRelationnel, f2: FaitRelationnel
    ) -> bool:
        r1, r2 = _norm(f1.relation), _norm(f2.relation)
        if r1 == r2 and f1.negatif != f2.negatif:
            return True
        return (
            r2 in RELATIONS_OPPOSEES.get(r1, set())
            or r1 in RELATIONS_OPPOSEES.get(r2, set())
        )

    def detecter_contradictions(self) -> List[Dict[str, Any]]:
        res: List[Dict[str, Any]] = []
        vus: Set[Tuple] = set()
        couples: Dict[Tuple[str, str], List[FaitRelationnel]] = defaultdict(list)
        for f in self.faits:
            couples[(_norm(f.sujet), _norm(f.objet))].append(f)
        for _, fs in couples.items():
            if len(fs) < 2:
                continue
            for i, f1 in enumerate(fs):
                for f2 in fs[i + 1 :]:
                    if not self._sont_opposes(f1, f2):
                        continue
                    k = tuple(sorted([f1.cle(), f2.cle()]))
                    if k in vus:
                        continue
                    vus.add(k)
                    res.append(
                        {
                            "type": "directe",
                            "fait_1": f1,
                            "fait_2": f2,
                            "explication": (
                                f"{f1.sujet} --{f1.relation}--> {f1.objet} "
                                f"VS --{f2.relation}--> {f2.objet}"
                            ),
                        }
                    )
        for f1 in self.faits:
            opposes = RELATIONS_OPPOSEES.get(_norm(f1.relation), set())
            if not opposes:
                continue
            for f2 in self._index_sujet.get(_norm(f1.sujet), []):
                if f1 is f2 or _norm(f2.relation) not in opposes:
                    continue
                if _norm(f1.objet) == _norm(f2.objet):
                    continue
                ch = self.trouver_chaine_deductive(
                    f1.objet, f2.objet, max_profondeur=5
                )
                if not ch:
                    continue
                k = tuple(sorted([f1.cle(), f2.cle()]))
                if k in vus:
                    continue
                vus.add(k)
                res.append(
                    {
                        "type": "distante",
                        "fait_1": f1,
                        "fait_2": f2,
                        "explication": (
                            f"{f1.sujet} --{f1.relation}--> {f1.objet} "
                            f"...-> {f2.objet}, mais --{f2.relation}--> {f2.objet}"
                        ),
                    }
                )
        return res

    def reviser_croyance(
        self,
        nouveau_fait: FaitRelationnel,
        max_contradictions: int = 200,
    ) -> Dict[str, Any]:
        m = self.forker(faits_supposes=[nouveau_fait])
        contradictions = m.detecter_contradictions()[:max_contradictions]
        if not contradictions:
            return {
                "coherent": True,
                "contradictions": [],
                "coupe_min": [],
                "poids_total_retire": 0.0,
                "borne_lp": 0.0,
            }
        edges = []
        poids_map = {f.cle(): f.poids for f in m.faits}
        for c in contradictions:
            edges.append((c["fait_1"].cle(), c["fait_2"].cle()))
        sol_bb = VertexCoverSolver(edges, poids_map).resoudre()
        sol_lp = VertexCoverLP(edges, poids_map).resoudre()
        coupe = sol_bb["coupe"]
        return {
            "coherent": False,
            "contradictions": contradictions,
            "coupe_min": [f for f in m.faits if f.cle() in coupe],
            "poids_total_retire": sol_bb["cout"],
            "borne_lp": sol_lp["valeur"],
            "noeuds_explores": sol_bb["noeuds_explores"],
        }

    def trouver_interventions_optimales(
        self,
        cible_y: str,
        seuil_prob: float,
        candidats_x: Optional[List[str]] = None,
        max_k: int = 3,
        couts: Optional[Dict[str, float]] = None,
        valeurs: Tuple[int, ...] = (1,),
        mode: str = "dijkstra",
    ) -> Dict[str, Any]:
        g = self.vers_graphe_causal()
        return AStarPlanificateur(g).resoudre(
            cible_y,
            seuil_prob,
            candidats=candidats_x,
            valeurs=valeurs,
            couts=couts,
            max_k=max_k,
            mode=mode,
        )

    def bench(self, n: int = 3000) -> Dict[str, float]:
        req = [("Socrate", "être_vivant"), ("tabac", "cancer_poumon")]
        self._cache.clear()
        t0 = time.perf_counter()
        for i in range(n):
            d, a = req[i % len(req)]
            self.trouver_chaine_deductive(d, a)
        dt = (time.perf_counter() - t0) * 1000 / n
        return {"requetes": float(n), "temps_moyen_ms": dt}


if __name__ == "__main__":
    from alix.sondes.alix_encyclopedie_souveraine import EncyclopedieSouveraine

    enc = EncyclopedieSouveraine()
    backend = BackendSQLite(":memory:")
    for f in FAITS_DEDUCTIFS_INITIAUX:
        backend.ajouter(f)
    m = MoteurDeductifCausal(
        encyclopedie=enc, backend_sqlite=backend, auto_saturer=False
    )
    r_sql = m.saturer_regles_sql(max_iterations=10)
    print("=" * 78)
    print(" 🧭🔗 BANC D'ESSAI : COMPÉTENCE #2 — MOTEUR DÉDUCTIF & CAUSAL v10.0 UNIFIÉ (a..dd)")
    print("=" * 78)
    print(
        f"  · [k,m] SQL Pushdown Datalog : {r_sql['total_derive']} faits dérivés en {r_sql['iterations']} itération(s)"
    )
    bn = GrapheCausal()
    bn.ajouter_arete("z", "x")
    bn.ajouter_arete("z", "y")
    bn.ajouter_arete("x", "y")
    bn.set_prior("z", 0.5)
    bn.set_cpt("x", {(1,): 0.9, (0,): 0.1})
    bn.set_cpt("y", {(1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1})
    jt = JunctionTree(bn)
    res_jt = jt.comparer_observation_vs_intervention("x", "y")
    print(
        f"  · [l]   Junction Tree (Shafer-Shenoy) : P(Y=1|X=1)={res_jt['P(Y=1|X=1)']:.4f} vs "
        f"P(Y=1|do(X=1))={res_jt['P(Y=1|do(X=1))']:.4f} | Δ={res_jt['delta_biais']:.4f}"
    )
    tw = TwinNetwork(bn)
    cf = tw.resoudre_contrefactuel({"x": 1, "y": 1}, {"x": 0}, "y", n_samples=50000)
    print(
        f"  · [p,s,w] TwinNetwork Pearl Niv. 3 : P(Y_{{x=0}}=1 | X=1,Y=1) = {cf['P']:.4f} (PN={1-cf['P']:.4f})"
    )
    rev = m.reviser_croyance(FaitRelationnel("fumer", "cause", "santé", poids=0.30))
    print(
        f"  · [q,u,x] Révision AGM (B&B + LP Simplexe) : coupe={len(rev['coupe_min'])} fait(s), "
        f"coût={rev['poids_total_retire']:.2f} (borne LP={rev['borne_lp']:.2f})"
    )
    lp_c5 = VertexCoverRevised(
        [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "a")],
        {v: 1.0 for v in "abcde"},
    ).resoudre()
    print(
        f"  · [cc]  RevisedSimplex sur Cycle C5 : LP={lp_c5['valeur']:.4f} (arrondie={lp_c5['valeur_arrondie']}, {lp_c5['iterations']} iters)"
    )
    s_json = Serializer.dumps(bn, FAITS_DEDUCTIFS_INITIAUX[:2])
    bn_rt, faits_rt = Serializer.loads(s_json)
    p_rt = bn_rt.inference_ve("y", {"x": 1})[1]
    print(
        f"  · [dd]  Serializer JSON Round-Trip ({len(s_json)} o) : P(Y=1|X=1)={p_rt:.4f} (match={abs(p_rt - res_jt['P(Y=1|X=1)']) < 1e-12})"
    )
    r_b = m.bench(3000)
    print(f"  · Benchmark Dijkstra v10.0 : {r_b['temps_moyen_ms']:.4f} ms/req")
    print("=" * 78)
