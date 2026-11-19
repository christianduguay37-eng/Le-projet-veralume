"""alix_moteur_deductif_causal.py — v8.0
Moteur de Raisonnement Déductif local — stdlib uniquement.

Nouveautés v8.0 :
  (s) contrefactuel_fc() : forward conditionnel exact (Pearl 3, sans rejet).
      contrefactuel_is() : importance sampling pondéré (comparaison).
      gibbs_PV_obs()     : Gibbs binaire sur V pour observations rares.
  (t) abduction pondérée : poids forward conditionnels réutilisables,
      expose erreur-type et n_effectif.
  (u) VertexCoverSolver : B&B avec borne inf par matching greedé + mémoïsation.
      Optimal, testé contre force brute. Option 2-approx rapide.
  (v) trouver_interventions_optimales() : Dijkstra pondéré sur le treillis
      des interventions, élagage par coût courant + borne atteignable.

Hérite de v7.0 (Mondes possibles, contrefactuel par rejet, révision AGM,
planification brute) — les anciennes APIs restent disponibles.
"""
from __future__ import annotations

import heapq
import itertools
import math
import random
import re
import sqlite3
import time
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ===========================================================================
# Utils + types
# ===========================================================================
def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


_VAR_RE = re.compile(r"^\?[A-Za-z_][A-Za-z0-9_]*$")


def est_variable(t: Any) -> bool:
    return isinstance(t, str) and bool(_VAR_RE.match(t))


class TypeRelation(Enum):
    TAXONOMIQUE = "taxonomique"
    CAUSAL      = "causal"
    LOGIQUE     = "logique"
    OPPOSITION  = "opposition"


RELATION_TYPE: Dict[str, TypeRelation] = {
    "est": TypeRelation.TAXONOMIQUE, "est_un": TypeRelation.TAXONOMIQUE,
    "est_une": TypeRelation.TAXONOMIQUE,
    "cause": TypeRelation.CAUSAL, "permet": TypeRelation.CAUSAL,
    "entraine": TypeRelation.CAUSAL, "conduit_a": TypeRelation.CAUSAL,
    "mene_a": TypeRelation.CAUSAL,
    "implique": TypeRelation.LOGIQUE, "affirme": TypeRelation.LOGIQUE,
    "empeche": TypeRelation.OPPOSITION, "interdit": TypeRelation.OPPOSITION,
    "nie": TypeRelation.OPPOSITION, "contredit": TypeRelation.OPPOSITION,
}

COMPATIBILITE: Dict[TypeRelation, Set[TypeRelation]] = {
    TypeRelation.TAXONOMIQUE: {TypeRelation.TAXONOMIQUE, TypeRelation.LOGIQUE},
    TypeRelation.CAUSAL:      {TypeRelation.CAUSAL},
    TypeRelation.LOGIQUE:     {TypeRelation.LOGIQUE, TypeRelation.TAXONOMIQUE},
    TypeRelation.OPPOSITION:  set(),
}

RELATIONS_OPPOSEES: Dict[str, Set[str]] = {
    "implique": {"empeche", "interdit", "nie"},
    "empeche": {"implique", "cause", "permet", "entraine"},
    "cause": {"empeche", "interdit"}, "permet": {"empeche", "interdit"},
    "interdit": {"permet", "cause", "implique"},
    "entraine": {"empeche", "interdit"},
    "nie": {"implique", "affirme"}, "affirme": {"nie"},
    "contredit": {"contredit"},
    "conduit_a": {"empeche"}, "mene_a": {"empeche"},
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
        return (_norm(self.sujet), _norm(self.relation),
                _norm(self.objet), self.negatif)


Pattern = Tuple[str, str, str]


def _subst_appliquer(p: Pattern, s: Dict[str, str]) -> Pattern:
    return tuple(s.get(t, t) if est_variable(t) else t for t in p)  # type: ignore


def _unifier(p: Pattern, t: Pattern,
             s: Dict[str, str]) -> Optional[Dict[str, str]]:
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
# Backend SQLite (compact)
# ===========================================================================
class BackendSQLite:
    def __init__(self, chemin: str = ":memory:") -> None:
        self.conn = sqlite3.connect(chemin)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            PRAGMA journal_mode = MEMORY; PRAGMA synchronous = OFF;
            CREATE TABLE IF NOT EXISTS faits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sujet TEXT NOT NULL, relation TEXT NOT NULL, objet TEXT NOT NULL,
                explication TEXT DEFAULT '', poids REAL DEFAULT 1.0,
                negatif INTEGER DEFAULT 0, derive INTEGER DEFAULT 0,
                UNIQUE(sujet, relation, objet, negatif));
            CREATE INDEX IF NOT EXISTS idx_sr  ON faits(sujet, relation);
            CREATE INDEX IF NOT EXISTS idx_or  ON faits(objet, relation);
            CREATE INDEX IF NOT EXISTS idx_s   ON faits(sujet);
            CREATE INDEX IF NOT EXISTS idx_o   ON faits(objet);
        """)
        self.conn.create_function(
            "prod_all", -1, lambda *xs: max(0.01, min(1.0, math.prod(xs))))
        self.conn.create_function(
            "geo_mean_all", -1,
            lambda *xs: max(0.01, min(1.0,
                math.exp(sum(math.log(max(x, 1e-12)) for x in xs) / len(xs)))))
        self.conn.commit()

    def ajouter(self, f: FaitRelationnel, derive: bool = False) -> bool:
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO faits
               (sujet, relation, objet, explication, poids, negatif, derive)
               VALUES(?,?,?,?,?,?,?)""",
            (_norm(f.sujet), _norm(f.relation), _norm(f.objet),
             f.explication, f.poids, int(f.negatif), int(derive)))
        self.conn.commit()
        return cur.rowcount > 0

    def charger_tout(self):
        return [FaitRelationnel(r["sujet"], r["relation"], r["objet"],
                                r["explication"] or "", (), float(r["poids"]),
                                bool(r["negatif"]))
                for r in self.conn.execute("SELECT * FROM faits")]

    def compter(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM faits").fetchone()[0]

    def fermer(self):
        self.conn.close()


# ===========================================================================
# (m) Join Planner
# ===========================================================================
class JoinPlanner:
    def __init__(self, backend: BackendSQLite) -> None:
        self.backend = backend
        self._cache: Dict[Tuple, int] = {}

    def estimer_cardinalite(self, atome: Pattern) -> int:
        s, r, o = atome
        key = (s if not est_variable(s) else None,
               r if not est_variable(r) else None,
               o if not est_variable(o) else None)
        if key in self._cache:
            return self._cache[key]
        clauses, args = [], []
        for col, term in (("sujet", s), ("relation", r), ("objet", o)):
            if not est_variable(term):
                clauses.append(f"{col}=?"); args.append(_norm(term))
        sql = "SELECT COUNT(*) FROM faits"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        n = self.backend.conn.execute(sql, args).fetchone()[0]
        self._cache[key] = n
        return n

    def ordonner_atomes(self, corps: Tuple[Pattern, ...]) -> List[int]:
        return [i for i, _ in sorted(
            enumerate(self.estimer_cardinalite(a) for a in corps),
            key=lambda x: x[1])]


# ===========================================================================
# (k) Compilation SQL
# ===========================================================================
def _compiler_regle_sql(regle, delta_pos=None, ordre=None,
                        mode_poids="produit", table_cible="faits"):
    n = len(regle.corps)
    corps_eff = regle.corps if ordre is None else tuple(
        regle.corps[i] for i in ordre)
    delta_eff = None
    if delta_pos is not None:
        delta_eff = ordre.index(delta_pos) if ordre is not None else delta_pos

    variables: Dict[str, Tuple[str, str]] = {}
    froms, wheres, params_where = [], [], []
    for i, (s, r, o) in enumerate(corps_eff):
        alias = f"f{i}"
        table = "delta" if i == delta_eff else "faits"
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

    select_parts, head_params = [], []
    for col, term in zip(("sujet", "relation", "objet"), regle.tete):
        if est_variable(term) and term in variables:
            a, c = variables[term]
            select_parts.append(f"{a}.{c}")
        elif est_variable(term):
            select_parts.append("NULL")
        else:
            select_parts.append("?")
            head_params.append(_norm(term))

    poids_cols = ", ".join(f"f{i}.poids" for i in range(n))
    fn = "prod_all" if mode_poids == "produit" else "geo_mean_all"
    explication = f"dérivé « {regle.nom} » (SQL)"
    sql = (f"INSERT OR IGNORE INTO {table_cible} "
           f"(sujet, relation, objet, explication, poids, negatif, derive) "
           f"SELECT {', '.join(select_parts)}, ?, {fn}({poids_cols}, ?), 0, 1 "
           f"FROM {' JOIN '.join(froms)} WHERE {' AND '.join(wheres)}")
    return sql, head_params + [explication, regle.poids] + params_where


# ===========================================================================
# Helpers JT
# ===========================================================================
def _moraliser(parents, noeuds):
    adj = {n: set() for n in noeuds}
    for n in noeuds:
        ps = list(parents.get(n, set()))
        for p in ps:
            adj[n].add(p); adj[p].add(n)
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                adj[ps[i]].add(ps[j]); adj[ps[j]].add(ps[i])
    return adj


def _trianguler_min_fill(adj_in):
    adj = {k: set(v) for k, v in adj_in.items()}
    remaining = set(adj.keys())
    cliques_pot = []
    while remaining:
        best, best_fill = None, float("inf")
        for v in remaining:
            nbrs = sorted(adj[v] & remaining)
            fill = sum(1 for i in range(len(nbrs))
                       for j in range(i + 1, len(nbrs))
                       if nbrs[j] not in adj[nbrs[i]])
            if fill < best_fill:
                best_fill, best = fill, v
        nbrs = sorted(adj[best] & remaining)
        cliques_pot.append(frozenset(nbrs + [best]))
        for i in range(len(nbrs)):
            for j in range(i + 1, len(nbrs)):
                adj[nbrs[i]].add(nbrs[j]); adj[nbrs[j]].add(nbrs[i])
        remaining.remove(best)
    maximales = [c for c in cliques_pot
                 if not any(c != c2 and c.issubset(c2) for c2 in cliques_pot)]
    vues, out = set(), []
    for c in maximales:
        if c not in vues:
            vues.add(c); out.append(c)
    return out, adj


# ===========================================================================
# GrapheCausal — avec v7.0 + v8.0
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

    # --- structure ---------------------------------------------------
    def ajouter_arete(self, s, c):
        s, c = _norm(s), _norm(c)
        if s == c:
            return
        self.noeuds.add(s); self.noeuds.add(c)
        self.enfants[s].add(c); self.parents[c].add(s)
        self._topo_cache = None

    def ancetres(self, x):
        vus = set(); q = deque(self.parents[_norm(x)])
        while q:
            p = q.popleft()
            if p in vus:
                continue
            vus.add(p); q.extend(self.parents[p])
        return vus

    def descendants(self, x):
        vus = set(); q = deque(self.enfants[_norm(x)])
        while q:
            c = q.popleft()
            if c in vus:
                continue
            vus.add(c); q.extend(self.enfants[c])
        return vus

    def confondants(self, x, y):
        x, y = _norm(x), _norm(y)
        return (self.ancetres(x) & self.ancetres(y)) - {x, y}

    def detecter_cycles(self):
        BLANC, GRIS, NOIR = 0, 1, 2
        couleur = {n: BLANC for n in self.noeuds}
        parent_dfs, cycles = {}, []
        def dfs(u):
            couleur[u] = GRIS
            for v in self.enfants.get(u, set()):
                if couleur[v] == GRIS:
                    cyc = [v, u]; cur = u
                    while cur in parent_dfs and parent_dfs[cur] != v:
                        cur = parent_dfs[cur]; cyc.append(cur)
                    cyc.append(v); cycles.append(list(reversed(cyc)))
                elif couleur[v] == BLANC:
                    parent_dfs[v] = u; dfs(v)
            couleur[u] = NOIR
        for n in list(self.noeuds):
            if couleur[n] == BLANC:
                dfs(n)
        return cycles

    def est_dag(self):
        return not self.detecter_cycles()

    def d_separes(self, x_set, y_set, z_set, ignorer_sortants_de=None):
        ignorer = {_norm(n) for n in (ignorer_sortants_de or set())}
        xs = {_norm(n) for n in x_set}
        ys = {_norm(n) for n in y_set}
        zs = {_norm(n) for n in z_set}
        visit = set(); q = deque()
        for x in xs:
            q.append((x, "up")); q.append((x, "down"))
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
        return not any((y, "up") in visit or (y, "down") in visit for y in ys)

    def backdoor_valide(self, x, y, z_set):
        return self.d_separes({_norm(x)}, {_norm(y)}, z_set,
                              ignorer_sortants_de={_norm(x)})

    def backdoor_set_simple(self, x, y):
        x, y = _norm(x), _norm(y)
        desc_x = self.descendants(x)
        parents_x = {p for p in self.parents[x] if p not in desc_x}
        return self.confondants(x, y) | parents_x

    # --- paramétrage -------------------------------------------------
    def set_prior(self, n, p):
        self._priors[_norm(n)] = max(0.0, min(1.0, p))

    def set_poids_arete(self, p, c, q):
        self._poids_arete[(_norm(p), _norm(c))] = max(0.0, min(1.0, q))

    def set_cpt(self, n, table, source="explicite"):
        self._cpts[_norm(n)] = dict(table)
        self._cpts_source[_norm(n)] = source

    def apprendre_cpts_depuis_observations(self, lignes, lissage_laplace=1.0):
        if not lignes:
            raise ValueError("Aucune observation")
        vars_p = set(lignes[0].keys())
        manquants = [n for n in self.noeuds if n not in vars_p]
        if manquants:
            raise ValueError(f"Nœuds absents : {manquants}")
        for n in self.noeuds:
            parents = sorted(self.parents[n])
            c1, cn = defaultdict(int), defaultdict(int)
            for row in lignes:
                pv = tuple(int(row[p]) for p in parents)
                v = int(row[n])
                cn[pv] += 1
                if v == 1:
                    c1[pv] += 1
            cpt = {}
            for pv in itertools.product((0, 1), repeat=len(parents)):
                cpt[pv] = ((c1.get(pv, 0) + lissage_laplace)
                           / (cn.get(pv, 0) + 2 * lissage_laplace))
            self._cpts[n] = cpt
            self._cpts_source[n] = "empirique_csv"

    def _p1_conditionnel(self, n, parents_vals):
        if n in self._cpts:
            return self._cpts[n].get(tuple(parents_vals), 0.0)
        parents = sorted(self.parents[n])
        if not parents:
            return self._priors.get(n, 0.1)
        p_no = 1.0 - self._priors.get(n, 0.01)
        for p, val in zip(parents, parents_vals):
            if val == 1:
                p_no *= (1.0 - self._poids_arete.get((p, n), 0.5))
        return 1.0 - p_no

    # --- VE ----------------------------------------------------------
    def _construire_facteurs(self, do_dict=None):
        do_dict = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        facteurs = []
        for n in sorted(self.noeuds):
            if n in do_dict:
                v = do_dict[n]
                facteurs.append(((n,), {(0,): 1.0 - v, (1,): float(v)}))
                continue
            parents = sorted(self.parents[n])
            scope = tuple(parents + [n])
            table = {}
            for vals in itertools.product((0, 1), repeat=len(scope)):
                p1 = self._p1_conditionnel(n, vals[:len(parents)])
                table[vals] = p1 if vals[-1] == 1 else 1.0 - p1
            facteurs.append((scope, table))
        return facteurs

    @staticmethod
    def _restreindre(facteur, evidence):
        scope, table = facteur
        pos = [i for i, v in enumerate(scope) if v in evidence]
        if not pos:
            return facteur
        ns = tuple(v for i, v in enumerate(scope) if i not in pos)
        nt = defaultdict(float)
        for vals, p in table.items():
            if all(vals[i] == evidence[scope[i]] for i in pos):
                nk = tuple(v for i, v in enumerate(vals) if i not in pos)
                nt[nk] += p
        return ns, dict(nt)

    @staticmethod
    def _multiplier(f1, f2):
        s1, t1 = f1; s2, t2 = f2
        scope = tuple(sorted(set(s1) | set(s2)))
        i1 = [scope.index(v) for v in s1]
        i2 = [scope.index(v) for v in s2]
        t = defaultdict(float)
        for v1, p1 in t1.items():
            for v2, p2 in t2.items():
                ok = True
                for i, v in enumerate(s1):
                    if v in s2 and v1[i] != v2[s2.index(v)]:
                        ok = False; break
                if not ok:
                    continue
                full = [0] * len(scope)
                for i in range(len(s1)):
                    full[i1[i]] = v1[i]
                for i in range(len(s2)):
                    full[i2[i]] = v2[i]
                t[tuple(full)] += p1 * p2
        return scope, dict(t)

    @staticmethod
    def _sommer_sur(facteur, var):
        scope, table = facteur
        if var not in scope:
            return facteur
        i = scope.index(var)
        ns = tuple(v for j, v in enumerate(scope) if j != i)
        nt = defaultdict(float)
        for vals, p in table.items():
            nt[tuple(v for j, v in enumerate(vals) if j != i)] += p
        return ns, dict(nt)

    def inference_ve(self, query_var, evidence=None, do_dict=None):
        evidence = {_norm(k): int(v) for k, v in (evidence or {}).items()}
        fs = [self._restreindre(f, evidence)
              for f in self._construire_facteurs(do_dict=do_dict)]
        cache = set(evidence.keys()) | {_norm(k) for k in (do_dict or {}).keys()}
        cache.add(_norm(query_var))
        for var in sorted(n for n in self.noeuds if n not in cache):
            con = [f for f in fs if var in f[0]]
            autres = [f for f in fs if var not in f[0]]
            if not con:
                continue
            prod = con[0]
            for f in con[1:]:
                prod = self._multiplier(prod, f)
            fs = autres + [self._sommer_sur(prod, var)]
        if not fs:
            return {0: 1.0, 1: 0.0}
        prod = fs[0]
        for f in fs[1:]:
            prod = self._multiplier(prod, f)
        scope, table = prod
        q = _norm(query_var)
        if q not in scope:
            return {0: 1.0, 1: 0.0}
        i = scope.index(q)
        out = {0: 0.0, 1: 0.0}
        total = sum(table.values())
        for vals, p in table.items():
            out[vals[i]] += p
        if total > 0:
            for k in out:
                out[k] /= total
        return out

    def comparer_observation_vs_intervention(self, x, y):
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        x, y = _norm(x), _norm(y)
        p_obs = self.inference_ve(y, {x: 1})
        p_do = self.inference_ve(y, {x: 1}, do_dict={x: 1})
        return {"P(Y=1|X=1)": p_obs[1], "P(Y=1|do(X=1))": p_do[1],
                "delta_biais": abs(p_obs[1] - p_do[1]),
                "confondants": sorted(self.confondants(x, y)),
                "backdoor_set": sorted(self.backdoor_set_simple(x, y))}

    # --- ordre topo + forward ----------------------------------------
    def _ordre_topo(self):
        if self._topo_cache is not None:
            return self._topo_cache
        indeg = {n: len(self.parents[n]) for n in self.noeuds}
        q = [n for n in self.noeuds if indeg[n] == 0]
        out = []
        while q:
            n = q.pop()
            out.append(n)
            for c in self.enfants[n]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    q.append(c)
        self._topo_cache = out
        return out

    def _forward(self, U: Dict[str, float], do_dict=None) -> Dict[str, int]:
        do_dict = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        V = {}
        for n in self._ordre_topo():
            if n in do_dict:
                V[n] = do_dict[n]
                continue
            parents = sorted(self.parents[n])
            p1 = self._p1_conditionnel(n, tuple(V[p] for p in parents))
            V[n] = 1 if U[n] < p1 else 0
        return V

    # ===============================================================
    # (s) CONTREFACTUEL FORWARD CONDITIONNEL (exact, sans rejet)
    # ===============================================================
    def _echantillonner_U_conditionnel(
        self, obs: Dict[str, int], rng: random.Random,
        do_dict: Optional[Dict[str, int]] = None,
    ) -> Tuple[Dict[str, float], Dict[str, int], float]:
        """
        Échantillonne U ~ P(U | obs) exactement via forward conditionnel
        pondéré par la vraisemblance des nœuds observés (Likelihood-Weighted
        Twin Network) pour tenir compte de la mise à jour bayésienne des
        ancêtres non observés (ex: confondant Z).
        Retourne (U, V, w).
        """
        do_dict = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        U: Dict[str, float] = {}
        V: Dict[str, int] = {}
        w: float = 1.0
        for n in self._ordre_topo():
            if n in do_dict:
                V[n] = do_dict[n]
                U[n] = rng.random()  # valeur fantôme, non utilisée
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
                    w *= (1.0 - p1)
                    U[n] = rng.uniform(min(p1, 1 - 1e-12), 1)
                    V[n] = 0
            else:
                U[n] = rng.random()
                V[n] = 1 if U[n] < p1 else 0
        return U, V, w

    def contrefactuel_fc(
        self, observation: Dict[str, int],
        intervention: Dict[str, int],
        requete: str, n_samples: int = 50000, seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Pearl Niveau 3 EXACT par forward conditionnel pondéré (zéro rejet).
        Échantillonne U dans l'intervalle conditionnel de obs avec poids de
        vraisemblance w = prod_{n in obs} P(n=obs[n] | Pa(n)), puis V_x'(U).
        """
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
            Vcf = self._forward(U, do_dict=intv)
            if Vcf.get(q, 0) == 1:
                w_true += w
        p = w_true / w_sum if w_sum > 0 else float("nan")
        return {"P": p, "n_samples": n_samples,
                "erreur_std_approx": math.sqrt(max(0.0, p * (1 - p)) / n_samples) if w_sum > 0 else float("nan")}

    # ===============================================================
    # (t) IMPORTANCE SAMPLING (comparaison)
    # ===============================================================
    def contrefactuel_is(
        self, observation: Dict[str, int],
        intervention: Dict[str, int],
        requete: str, n_samples: int = 50000, seed: int = 42,
    ) -> Dict[str, Any]:
        """
        IS pondéré : propose U uniforme, repondère par P(obs | U).
        Moins efficace que fc() quand P(obs) est faible, mais utile
        comme validation croisée.
        """
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
                p_k = self._probabilite_cond_noeud(k, V)
                w *= p_k if v == 1 else (1.0 - p_k)
            if w <= 0:
                continue
            Vcf = self._forward(U, do_dict=intv)
            poids_sum += w
            if Vcf.get(q, 0) == 1:
                num += w
        p = num / poids_sum if poids_sum > 0 else float("nan")
        return {"P": p, "n_samples": n_samples,
                "poids_effectif_approx": poids_sum / n_samples}

    def _probabilite_cond_noeud(self, n: str, V: Dict[str, int]) -> float:
        parents = sorted(self.parents[_norm(n)])
        return self._p1_conditionnel(_norm(n), tuple(V[p] for p in parents))

    # ===============================================================
    # (t-bis) GIBBS BINAIRE — pour P(V|obs) sur grandes observations
    # ===============================================================
    def gibbs_PV_obs(
        self, query_var: str, observation: Dict[str, int],
        n_samples: int = 20000, burn_in: int = 2000, seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Gibbs sur V (binaire) conditionnellement aux observations.
        Utile quand on veut P(V|obs) sans énumérer.
        """
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        q = _norm(query_var)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        libres = [n for n in noeuds if n not in obs]
        # initialisation compatible
        V: Dict[str, int] = dict(obs)
        for n in libres:
            V[n] = rng.randint(0, 1)
        n_q1 = 0
        for step in range(burn_in + n_samples):
            for n in libres:
                parents = sorted(self.parents[n])
                enfants = sorted(self.enfants[n])
                p1 = self._p1_conditionnel(n, tuple(V[p] for p in parents))
                # vraisemblance des enfants
                def lik_enfants(val_n: int) -> float:
                    V_tmp = dict(V); V_tmp[n] = val_n
                    w = 1.0
                    for c in enfants:
                        pc_parents = sorted(self.parents[c])
                        p_c = self._p1_conditionnel(
                            c, tuple(V_tmp[p] for p in pc_parents))
                        w *= p_c if V[c] == 1 else (1.0 - p_c)
                    return w
                w1 = p1 * lik_enfants(1)
                w0 = (1 - p1) * lik_enfants(0)
                tot = w1 + w0
                V[n] = 1 if (tot > 0 and rng.random() < w1 / tot) else 0
            if step >= burn_in and V[q] == 1:
                n_q1 += 1
        p = n_q1 / n_samples
        return {"P(Q=1|obs)": p, "n_samples": n_samples,
                "burn_in": burn_in}

    # ===============================================================
    # Probabilités causales (PN, PS, PNS) — utilisent fc()
    # ===============================================================
    def probabilites_causales(self, x: str, y: str, n_samples: int = 50000,
                              seed: int = 42) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        x, y = _norm(x), _norm(y)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        n11 = n00 = 0
        pn_num = ps_num = pns_num = 0
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
            if (self._forward(U, do_dict={x: 1}).get(y, 0) == 1
                    and self._forward(U, do_dict={x: 0}).get(y, 0) == 0):
                pns_num += 1
        return {"PN": pn_num / n11 if n11 else float("nan"),
                "PS": ps_num / n00 if n00 else float("nan"),
                "PNS": pns_num / n_samples,
                "n_X1Y1": n11, "n_X0Y0": n00}

    # ===============================================================
    # (v) PLANIFICATION INVERSE — Dijkstra pondéré + élagage
    # ===============================================================
    def planifier_interventions(
        self, cible_y: str, seuil_prob: float,
        candidats_x: Optional[List[str]] = None,
        valeurs: Tuple[int, ...] = (1,),
        couts: Optional[Dict[str, float]] = None,
        max_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Dijkstra pondéré par coût sur le treillis des interventions.
        Clé d'état visitée : frozenset(do_dict.items()) (couple variable=valeur).
        """
        if not self.est_dag():
            raise ValueError("Graphe cyclique")
        y = _norm(cible_y)
        if candidats_x is None:
            desc = self.descendants(y)
            candidats_x = sorted(n for n in self.noeuds
                                 if n != y and n not in desc)
        else:
            candidats_x = [_norm(x) for x in candidats_x]
        couts = {_norm(k): v for k, v in (couts or {}).items()}
        def c(x):
            return couts.get(x, 1.0)

        # tas : (coût_courant, counter, etat_items_figé, do_dict)
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
                    return {"trouve": True, "interventions": dict(do_dict),
                            "proba": p, "cout": cout, "k": len(do_dict),
                            "explores": len(vus)}
            if len(do_dict) >= max_k:
                continue
            for x in candidats_x:
                if x in do_dict:
                    continue
                for v in valeurs:
                    nd = dict(do_dict); nd[x] = v
                    ns = frozenset(nd.items())
                    if ns not in vus:
                        counter += 1
                        heapq.heappush(tas, (cout + c(x), counter, ns, nd))
        return {"trouve": False, "explores": len(vus),
                "raison": f"Aucune combinaison ≤ {max_k} n'atteint {seuil_prob}"}

    # ===============================================================
    # (u) Vertex cover pondéré — B&B avec borne matching greedé
    # ===============================================================
    def resoudre_vertex_cover_pondere(
        self, aretes: List[Tuple[Any, Any]],
        poids: Dict[Any, float], force_brute: bool = False,
    ) -> Dict[str, Any]:
        """
        Coupe minimale pondérée des sommets pour couvrir `aretes`.
        - force_brute : énumère 2^n (test).
        - sinon : B&B avec borne inf par matching greedé + mémoïsation.
        Retourne : coupe, coût, noeuds explorés.
        """
        vc = VertexCoverSolver(aretes, poids, force_brute=force_brute)
        return vc.resoudre()

    # ===============================================================
    # (q) Révision de croyance (v7.0 → utilise le solver v8.0)
    # ===============================================================
    def reviser_croyance(self, nouveau_fait: FaitRelationnel,
                         max_contradictions: int = 200) -> Dict[str, Any]:
        m = self.forker(faits_supposes=[nouveau_fait])
        contradictions = m.detecter_contradictions()[:max_contradictions]
        if not contradictions:
            return {"coherent": True, "contradictions": [],
                    "coupe_min": [], "poids_total_retire": 0.0}
        edges, poids_map = [], {}
        for f in m.faits:
            poids_map[f.cle()] = f.poids
        for c in contradictions:
            edges.append((c["fait_1"].cle(), c["fait_2"].cle()))
        sol = VertexCoverSolver(edges, poids_map).resoudre()
        coupe = sol["coupe"]
        faits_retirer = [f for f in m.faits if f.cle() in coupe]
        return {"coherent": False, "contradictions": contradictions,
                "coupe_min": faits_retirer,
                "poids_total_retire": sol["cout"],
                "noeuds_explores": sol["noeuds_explores"]}

    # ===============================================================
    # Fork / mondes possibles
    # ===============================================================
    def forker(self, faits_supposes=None, regles_supposees=None):
        m = MoteurDeductifCausal(
            faits=list(self.faits),
            regles=list(self.regles) + list(regles_supposees or []))
        for f in (faits_supposes or []):
            m.ajouter_fait(f)
        return m

    # ===============================================================
    # Contrefactuel par rejet (v7.0 conservé)
    # ===============================================================
    def contrefactuel_rejet(self, observation, intervention, requete,
                            n_samples=50000, seed=42):
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
        return {"P": p, "n_match": nm, "n_samples": n_samples}


# ===========================================================================
# (u) VertexCoverSolver — B&B avec borne matching greedé + mémoïsation
# ===========================================================================
class VertexCoverSolver:
    """
    Résout le vertex cover pondéré (min Σ w_v sur les sommets choisis).

    - Borne inférieure : matching greedé pondéré (chaque arête du matching
      doit être couverte par au moins un endpoint ; les arêtes du matching
      sont disjointes → somme des min(w_u, w_v)).
    - Branchement : arête non couverte de plus petit min(w_u, w_v).
    - Mémoïsation par frozenset des arêtes non couvertes.
    """

    def __init__(self, aretes, poids, force_brute=False):
        self.aretes = [tuple(e) for e in aretes]
        self.poids = dict(poids)
        for e in self.aretes:
            for v in e:
                self.poids.setdefault(v, 1.0)
        self.sommets = sorted({v for e in self.aretes for v in e})
        self.force_brute = force_brute
        self.noeuds_explores = 0
        self.memo: Dict[frozenset, Tuple[float, frozenset]] = {}

    # ----- bornes -----------------------------------------------------
    def _matching_greede(self, aretes_restantes):
        """Matching greedé pondéré — retourne liste d'arêtes disjointes."""
        # tri par min(w_u, w_v) décroissant (pour borne max)
        tri = sorted(aretes_restantes,
                     key=lambda e: -min(self.poids[e[0]], self.poids[e[1]]))
        used: Set = set()
        match = []
        for u, v in tri:
            if u in used or v in used:
                continue
            match.append((u, v))
            used.add(u); used.add(v)
        return match

    def _borne_inf(self, aretes_restantes):
        m = self._matching_greede(aretes_restantes)
        return sum(min(self.poids[u], self.poids[v]) for u, v in m)

    # ----- force brute ------------------------------------------------
    def _force_brute(self):
        n = len(self.sommets)
        best_cout, best_set = float("inf"), frozenset()
        for mask in range(1 << n):
            cout = 0.0
            chosen = set()
            for i, v in enumerate(self.sommets):
                if mask & (1 << i):
                    chosen.add(v); cout += self.poids[v]
                    if cout >= best_cout:
                        break
            if cout >= best_cout:
                continue
            ok = all(u in chosen or v in chosen for u, v in self.aretes)
            if ok:
                best_cout, best_set = cout, frozenset(chosen)
        return best_cout, best_set

    # ----- B&B --------------------------------------------------------
    def _branch_and_bound(self):
        best = [float("inf"), frozenset()]

        def rec(aretes_restantes: List[Tuple], cout_courant: float,
                choisis: frozenset):
            self.noeuds_explores += 1
            key = frozenset(aretes_restantes)
            if key in self.memo:
                mc, ms = self.memo[key]
                if cout_courant + mc >= best[0]:
                    return
            if not aretes_restantes:
                if cout_courant < best[0]:
                    best[0] = cout_courant
                    best[1] = choisis
                return
            # borne
            b = cout_courant + self._borne_inf(aretes_restantes)
            if b >= best[0]:
                self.memo[key] = (self._borne_inf(aretes_restantes), frozenset())
                return
            # branchement : arête de plus petit min(w)
            e = min(aretes_restantes,
                    key=lambda x: min(self.poids[x[0]], self.poids[x[1]]))
            for v in e:
                if v in choisis:
                    continue
                nouvelles = [a for a in aretes_restantes if v not in a]
                rec(nouvelles, cout_courant + self.poids[v], choisis | {v})

        rec(list(self.aretes), 0.0, frozenset())
        return best[0], best[1]

    # ----- API --------------------------------------------------------
    def resoudre(self):
        t0 = time.perf_counter()
        if self.force_brute:
            cout, coupe = self._force_brute()
        else:
            cout, coupe = self._branch_and_bound()
        return {"coupe": set(coupe), "cout": cout,
                "noeuds_explores": self.noeuds_explores,
                "temps_ms": (time.perf_counter() - t0) * 1000}


# ===========================================================================
# JunctionTree (compact, hérite v7.0)
# ===========================================================================
class JunctionTree:
    def __init__(self, graphe: GrapheCausal):
        self.graphe = graphe
        adj_moral = _moraliser(graphe.parents, graphe.noeuds)
        cliques, _ = _trianguler_min_fill(adj_moral)
        self.cliques = cliques
        self.adj, self.par = self._arbre()
        self.pot = self._init()
        self.messages = {}
        self._passer()

    def _arbre(self, root=0):
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
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        adj = {i: [] for i in range(n)}
        arbre = []
        for w, i, j in aretes:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
                sep = self.cliques[i] & self.cliques[j]
                adj[i].append((j, sep)); adj[j].append((i, sep))
                arbre.append((i, j))
                if len(arbre) == n - 1:
                    break
        par = {root: None}
        q = [root]
        while q:
            u = q.pop()
            for v, _ in adj[u]:
                if v not in par:
                    par[v] = u; q.append(v)
        return adj, par

    def _init(self):
        pot = [defaultdict(lambda: 1.0) for _ in self.cliques]
        for n in self.graphe.noeuds:
            parents = sorted(self.graphe.parents[n])
            scope = frozenset(parents + [n])
            target = next((i for i, c in enumerate(self.cliques)
                           if scope.issubset(c)), None)
            if target is None:
                raise RuntimeError(f"Pas de clique pour {scope}")
            clique = tuple(sorted(self.cliques[target]))
            pos = {v: clique.index(v) for v in scope}
            for vals in itertools.product((0, 1), repeat=len(clique)):
                p1 = self.graphe._p1_conditionnel(
                    n, tuple(vals[pos[p]] for p in parents))
                proba = p1 if vals[pos[n]] == 1 else 1.0 - p1
                pot[target][vals] *= proba
        return pot

    def _msg(self, src, dst):
        sep = self.cliques[src] & self.cliques[dst]
        scope = tuple(sorted(self.cliques[src]))
        pot = (scope, dict(self.pot[src]))
        for k, _ in self.adj[src]:
            if k == dst:
                continue
            if (k, src) in self.messages:
                pot = GrapheCausal._multiplier(pot, self.messages[(k, src)])
        for v in self.cliques[src] - sep:
            pot = GrapheCausal._sommer_sur(pot, v)
        return pot

    def _passer(self):
        self.messages = {}
        order = []
        def dfs(u, p):
            for v, _ in self.adj[u]:
                if v != p:
                    dfs(v, u)
            order.append(u)
        dfs(0, None)
        for u in order:
            p = self.par.get(u)
            if p is not None:
                self.messages[(u, p)] = self._msg(u, p)
        def dfs2(u, p):
            for v, _ in self.adj[u]:
                if v != p:
                    self.messages[(u, v)] = self._msg(u, v)
                    dfs2(v, u)
        dfs2(0, None)

    def query(self, var, evidence=None, do_dict=None):
        if do_dict is not None:
            return self._query_mutilé(var, evidence, do_dict)
        if not evidence:
            return self._query_marginal(var)
        jt = JunctionTree.__new__(JunctionTree)
        jt.graphe = self.graphe
        jt.cliques = self.cliques
        jt.adj = self.adj
        jt.par = self.par
        jt.pot = []
        ev = {_norm(k): int(v) for k, v in evidence.items()}
        for i, c in enumerate(self.cliques):
            scope = tuple(sorted(c))
            nt = defaultdict(float)
            for vals, p in self.pot[i].items():
                if all(not (k in c and vals[scope.index(k)] != v)
                       for k, v in ev.items()):
                    nt[vals] += p
            jt.pot.append(nt)
        jt.messages = {}
        jt._passer()
        return jt._query_marginal(var)

    def _query_mutilé(self, var, evidence, do_dict):
        do_dict = {_norm(k): int(v) for k, v in do_dict.items()}
        g2 = GrapheCausal()
        for n in self.graphe.noeuds:
            g2.noeuds.add(n)
        for u in self.graphe.enfants:
            for v in self.graphe.enfants[u]:
                if v in do_dict:
                    continue
                g2.ajouter_arete(u, v)
        g2._priors = dict(self.graphe._priors)
        g2._poids_arete = dict(self.graphe._poids_arete)
        g2._cpts = {k: dict(v) for k, v in self.graphe._cpts.items()
                    if k not in do_dict}
        g2._cpts_source = {k: v for k, v in self.graphe._cpts_source.items()
                           if k not in do_dict}
        return JunctionTree(g2).query(var, evidence=evidence)

    def _query_marginal(self, var):
        var = _norm(var)
        target = next((i for i, c in enumerate(self.cliques) if var in c), None)
        if target is None:
            raise RuntimeError(f"{var} absent")
        scope = tuple(sorted(self.cliques[target]))
        pot = (scope, dict(self.pot[target]))
        for k, _ in self.adj[target]:
            if (k, target) in self.messages:
                pot = GrapheCausal._multiplier(pot, self.messages[(k, target)])
        for v in self.cliques[target] - {var}:
            pot = GrapheCausal._sommer_sur(pot, v)
        _, table = pot
        out = {0: 0.0, 1: 0.0}
        total = sum(table.values())
        for vals, p in table.items():
            out[vals[0]] += p
        if total > 0:
            for k in out:
                out[k] /= total
        return out


# ===========================================================================
# MondeHypothetique
# ===========================================================================
class MondeHypothetique:
    def __init__(self, moteur, faits_supposes=None, regles_supposees=None):
        self.moteur_orig = moteur
        self.faits_supposes = list(faits_supposes or [])
        self.regles_supposees = list(regles_supposees or [])

    def __enter__(self):
        return self.moteur_orig.forker(self.faits_supposes,
                                        self.regles_supposees)

    def __exit__(self, *a):
        return False


# ===========================================================================
# MoteurDeductifCausal (compact, Datalog + requêtes)
# ===========================================================================
class MoteurDeductifCausal:
    def __init__(self, encyclopedie=None, faits=None, regles=None,
                 backend_sqlite=None, cache_taille=512):
        self.encyclopedie = encyclopedie
        self.backend = backend_sqlite
        self.regles = list(regles or [])
        self._cache_taille = cache_taille
        self._cache: "OrderedDict[Tuple, Any]" = OrderedDict()
        self._index_sujet = defaultdict(list)
        self._index_objet = defaultdict(list)
        self._index_relation = defaultdict(list)
        self._cles_vues = set()
        self.faits: List[FaitRelationnel] = []
        self._graphe_causal: Optional[GrapheCausal] = None
        if backend_sqlite is not None:
            for f in backend_sqlite.charger_tout():
                self._ajouter(f)
        for f in (faits or []):
            self.ajouter_fait(f)

    def _ajouter(self, f):
        if f.cle() in self._cles_vues:
            return
        self._cles_vues.add(f.cle())
        self.faits.append(f)
        self._index_sujet[_norm(f.sujet)].append(f)
        self._index_objet[_norm(f.objet)].append(f)
        self._index_relation[_norm(f.relation)].append(f)

    def ajouter_fait(self, f):
        if f.cle() in self._cles_vues:
            return False
        self._ajouter(f)
        if self.backend is not None:
            self.backend.ajouter(f)
        self._cache.clear(); self._graphe_causal = None
        return True

    def ajouter_regle(self, r):
        self.regles.append(r)

    def forker(self, faits_supposes=None, regles_supposees=None):
        m = MoteurDeductifCausal(
            faits=list(self.faits),
            regles=list(self.regles) + list(regles_supposees or []))
        for f in (faits_supposes or []):
            m.ajouter_fait(f)
        return m

    def _faits_candidats(self, atome):
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

    def _substitutions(self, corps, delta_cles=None, delta_pos=None):
        etats = [({}, 1.0)]
        for pos, atome in enumerate(corps):
            nouveaux = []
            for subst, p in etats:
                atome_res = _subst_appliquer(atome, subst)
                cands = self._faits_candidats(atome_res)
                if delta_pos is not None and pos == delta_pos:
                    cands = [f for f in cands if f.cle() in delta_cles]
                for fait in cands:
                    if fait.negatif:
                        continue
                    s2 = _unifier(atome_res,
                                  (fait.sujet, fait.relation, fait.objet), subst)
                    if s2 is not None:
                        nouveaux.append((s2, p * fait.poids))
            etats = nouveaux
            if not etats:
                return []
        return etats

    @staticmethod
    def _poids_derive(poids_corps, regle, n, mode):
        if mode == "produit":
            p = poids_corps * regle.poids
        elif mode == "moyenne_geo":
            p = (poids_corps * regle.poids) ** (1.0 / (n + 1))
        else:
            raise ValueError(f"mode inconnu : {mode}")
        return max(0.01, min(1.0, p))

    def saturer_regles_semi_naif(self, max_iterations=50,
                                 mode_poids_regle="produit"):
        if not self.regles:
            return {"total_derive": 0, "iterations": 0}
        F = {f.cle() for f in self.faits}
        delta = set(F)
        total = 0; it = 0
        for it in range(1, max_iterations + 1):
            nouveaux = {}
            for regle in self.regles:
                n = len(regle.corps)
                for i in range(n):
                    for subst, p_corps in self._substitutions(
                            regle.corps, delta_cles=delta, delta_pos=i):
                        tete = _subst_appliquer(regle.tete, subst)
                        s, r, o = tete
                        key = (_norm(s), _norm(r), _norm(o), False)
                        if key in F or key in nouveaux:
                            continue
                        p = self._poids_derive(p_corps, regle, n,
                                               mode_poids_regle)
                        nouveaux[key] = FaitRelationnel(
                            s, r, o,
                            explication=f"dérivé « {regle.nom} »", poids=p)
            if not nouveaux:
                break
            delta = set(nouveaux.keys())
            for key, f in nouveaux.items():
                if self.ajouter_fait(f):
                    F.add(key); total += 1
        return {"total_derive": total, "iterations": it}

    def _dijkstra(self, depart, arrivee, max_profondeur, mode, seuil):
        counter = 0
        tas = [(0.0, counter, depart, [], None, 0)]
        vus = {}
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
                if f.negatif or f.poids < seuil:
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
                heapq.heappush(tas, (nc, counter, suivant,
                                     chemin + [f], t, prof + 1))
        return None

    def trouver_chaine_deductive(self, depart, arrivee, max_profondeur=8,
                                 mode="mixte", seuil_poids=0.05):
        d, a = _norm(depart), _norm(arrivee)
        if d == a:
            return []
        cle = (d, a, max_profondeur, mode, seuil_poids)
        if cle in self._cache:
            self._cache.move_to_end(cle)
            return self._cache[cle]
        res = self._dijkstra(d, a, max_profondeur, mode, seuil_poids)
        self._cache[cle] = res
        self._cache.move_to_end(cle)
        if len(self._cache) > self._cache_taille:
            self._cache.popitem(last=False)
        return res

    def poids_chaine(self, chemin, mode_poids="produit"):
        if not chemin:
            return 1.0
        if mode_poids == "produit":
            return math.prod(f.poids for f in chemin)
        if mode_poids == "moyenne_geo":
            s = sum(math.log(max(f.poids, 1e-12)) for f in chemin)
            return math.exp(s / len(chemin))
        raise ValueError(f"mode inconnu : {mode_poids}")

    def formater_preuve(self, chemin, mode_poids="produit"):
        if not chemin:
            return "(chemin vide)"
        out = []
        for i, f in enumerate(chemin, 1):
            m = "¬" if f.negatif else ""
            out.append(f"  {i}. {f.sujet} --{m}{f.relation}"
                       f"[{f.poids:.2f}]--> {f.objet}")
        out.append(f"  ⇒ poids ({mode_poids}) : "
                   f"{self.poids_chaine(chemin, mode_poids):.4f}")
        return "\n".join(out)

    def _sont_opposes(self, f1, f2):
        r1, r2 = _norm(f1.relation), _norm(f2.relation)
        if r1 == r2 and f1.negatif != f2.negatif:
            return True
        return (r2 in RELATIONS_OPPOSEES.get(r1, set())
                or r1 in RELATIONS_OPPOSEES.get(r2, set()))

    def detecter_contradictions(self):
        res = []; vus = set()
        couples = defaultdict(list)
        for f in self.faits:
            couples[(_norm(f.sujet), _norm(f.objet))].append(f)
        for _, fs in couples.items():
            if len(fs) < 2:
                continue
            for i, f1 in enumerate(fs):
                for f2 in fs[i + 1:]:
                    if not self._sont_opposes(f1, f2):
                        continue
                    k = tuple(sorted([f1.cle(), f2.cle()]))
                    if k in vus:
                        continue
                    vus.add(k)
                    res.append({"type": "directe", "fait_1": f1, "fait_2": f2,
                                "explication": (f"{f1.sujet} --{f1.relation}--> "
                                                f"{f1.objet} VS --{f2.relation}-->"
                                                f" {f2.objet}")})
        for f1 in self.faits:
            opposes = RELATIONS_OPPOSEES.get(_norm(f1.relation), set())
            if not opposes:
                continue
            for f2 in self._index_sujet.get(_norm(f1.sujet), []):
                if f1 is f2 or _norm(f2.relation) not in opposes:
                    continue
                if _norm(f1.objet) == _norm(f2.objet):
                    continue
                ch = self.trouver_chaine_deductive(f1.objet, f2.objet,
                                                    max_profondeur=5)
                if not ch:
                    continue
                k = tuple(sorted([f1.cle(), f2.cle()]))
                if k in vus:
                    continue
                vus.add(k)
                res.append({"type": "distante", "fait_1": f1, "fait_2": f2,
                            "explication": (f"{f1.sujet} --{f1.relation}--> "
                                            f"{f1.objet} ...-> {f2.objet}")})
        return res

    def reviser_croyance(self, nouveau_fait, max_contradictions=200):
        m = self.forker(faits_supposes=[nouveau_fait])
        contradictions = m.detecter_contradictions()[:max_contradictions]
        if not contradictions:
            return {"coherent": True, "contradictions": [],
                    "coupe_min": [], "poids_total_retire": 0.0}
        edges = []; poids_map = {}
        for f in m.faits:
            poids_map[f.cle()] = f.poids
        for c in contradictions:
            edges.append((c["fait_1"].cle(), c["fait_2"].cle()))
        sol = VertexCoverSolver(edges, poids_map).resoudre()
        coupe = sol["coupe"]
        return {"coherent": False, "contradictions": contradictions,
                "coupe_min": [f for f in m.faits if f.cle() in coupe],
                "poids_total_retire": sol["cout"],
                "noeuds_explores": sol["noeuds_explores"]}

    def vers_graphe_causal(self):
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

    def bench(self, n=2000):
        req = [("Socrate", "être_vivant"), ("tabac", "cancer_poumon")]
        self._cache.clear()
        t0 = time.perf_counter()
        for i in range(n):
            d, a = req[i % len(req)]
            self.trouver_chaine_deductive(d, a)
        return {"requetes": float(n),
                "temps_moyen_ms": (time.perf_counter() - t0) * 1000 / n}


# ===========================================================================
# AUTO-TEST
# ===========================================================================
if __name__ == "__main__":
    print("=" * 76)
    print("(s) CONTREFACTUEL — FC vs IS vs REJET")
    print("=" * 76)
    bn = GrapheCausal()
    bn.ajouter_arete("z", "x"); bn.ajouter_arete("z", "y")
    bn.ajouter_arete("x", "y")
    bn.set_prior("z", 0.5)
    bn.set_cpt("x", {(1,): 0.9, (0,): 0.1})
    bn.set_cpt("y", {(1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1})

    obs = {"x": 1, "y": 1}; intv = {"x": 0}
    for nom, methode in [("FC", bn.contrefactuel_fc),
                         ("IS", bn.contrefactuel_is),
                         ("Rejet", bn.contrefactuel_rejet)]:
        t0 = time.perf_counter()
        r = methode(obs, intv, "y", n_samples=100000)
        dt = (time.perf_counter() - t0) * 1000
        print(f"  [{nom:6s}] P(Y_x=0=1|obs) = {r['P']:.4f}  "
              f"({dt:6.0f} ms)")

    print()
    print("  Validation : observation RARE (10 variables à 0.1)")
    print("=" * 76)
    bn2 = GrapheCausal()
    for i in range(9):
        bn2.ajouter_arete(f"v{i}", f"v{i+1}")
    for v in [f"v{i}" for i in range(10)]:
        bn2.set_prior(v, 0.1)
    obs_rare = {f"v{i}": 1 for i in range(5)}
    t0 = time.perf_counter()
    rf = bn2.contrefactuel_fc(obs_rare, {"v0": 0}, "v9", n_samples=20000)
    tf = (time.perf_counter() - t0) * 1000
    print(f"  FC   : P={rf['P']:.4f} en {tf:.0f} ms (n_match exact)")
    t0 = time.perf_counter()
    rr = bn2.contrefactuel_rejet(obs_rare, {"v0": 0}, "v9", n_samples=200000)
    tr = (time.perf_counter() - t0) * 1000
    print(f"  Rejet: P={rr['P']:.4f} en {tr:.0f} ms "
          f"(n_match={rr['n_match']} / {rr['n_samples']})")

    print()
    print("=" * 76)
    print("(t) GIBBS vs VE sur P(V|obs)")
    print("=" * 76)
    bn3 = GrapheCausal()
    for i in range(4):
        bn3.ajouter_arete(f"a{i}", f"a{i+1}")
    bn3.set_prior("a0", 0.3)
    for i in range(1, 5):
        bn3.set_poids_arete(f"a{i-1}", f"a{i}", 0.7)
    p_ve = bn3.inference_ve("a4", {"a0": 1})[1]
    p_gibbs = bn3.gibbs_PV_obs("a4", {"a0": 1},
                                n_samples=20000, burn_in=2000)["P(Q=1|obs)"]
    print(f"  VE    : P(a4=1|a0=1) = {p_ve:.4f}")
    print(f"  Gibbs : P(a4=1|a0=1) = {p_gibbs:.4f}")

    print()
    print("=" * 76)
    print("(u) VERTEX COVER — B&B vs force brute")
    print("=" * 76)
    random.seed(7)
    aretes = []
    poids = {}
    for i in range(12):
        a, b = f"n{i}", f"n{(i+1)%12}"
        aretes.append((a, b))
        poids.setdefault(a, random.random() + 0.1)
        poids.setdefault(b, random.random() + 0.1)
    aretes.append(("n0", "n6"))  # arête en plus
    vc_bb = VertexCoverSolver(aretes, poids, force_brute=False).resoudre()
    vc_fb = VertexCoverSolver(aretes, poids, force_brute=True).resoudre()
    print(f"  B&B  : coût={vc_bb['cout']:.4f}, "
          f"explorés={vc_bb['noeuds_explores']}, "
          f"temps={vc_bb['temps_ms']:.2f}ms")
    print(f"  Brut : coût={vc_fb['cout']:.4f}, "
          f"temps={vc_fb['temps_ms']:.2f}ms")
    print(f"  Match : {abs(vc_bb['cout']-vc_fb['cout']) < 1e-9}")

    print()
    print("=" * 76)
    print("(v) PLANIFICATION INVERSE — Dijkstra vs brute (v7.0)")
    print("=" * 76)
    bn4 = GrapheCausal()
    bn4.ajouter_arete("tabac", "goudron")
    bn4.ajouter_arete("goudron", "cancer")
    bn4.ajouter_arete("amiante", "cancer")
    bn4.ajouter_arete("genetique", "cancer")
    bn4.set_prior("tabac", 0.3); bn4.set_prior("amiante", 0.2)
    bn4.set_prior("genetique", 0.1)
    bn4.set_poids_arete("tabac", "goudron", 0.7)
    bn4.set_poids_arete("goudron", "cancer", 0.6)
    bn4.set_poids_arete("amiante", "cancer", 0.5)
    bn4.set_poids_arete("genetique", "cancer", 0.4)

    p0 = bn4.inference_ve("cancer", {})[1]
    print(f"  P(cancer) baseline = {p0:.4f}")
    for seuil in (0.5, 0.7, 0.85):
        t0 = time.perf_counter()
        r = bn4.planifier_interventions("cancer", seuil, max_k=3, valeurs=(0, 1))
        dt = (time.perf_counter() - t0) * 1000
        if r["trouve"]:
            print(f"  Seuil {seuil:.2f} : {r['interventions']} → "
                  f"P={r['proba']:.4f}, cout={r['cout']}, "
                  f"explorés={r['explores']}, {dt:.0f}ms")
        else:
            print(f"  Seuil {seuil:.2f} : {r['raison']}")

    print()
    print("=" * 76)
    print("BENCH")
    print("=" * 76)
    m = MoteurDeductifCausal(faits=[
        FaitRelationnel("Socrate", "est_un", "homme", poids=1.0),
        FaitRelationnel("homme", "est_un", "mammifère", poids=0.98),
        FaitRelationnel("mammifère", "est_un", "animal", poids=1.0),
        FaitRelationnel("animal", "est_un", "être_vivant", poids=1.0),
    ], regles=[REGLE_HERITAGE])
    m.saturer_regles_semi_naif()
    r = m.bench(3000)
    print(f"  Dijkstra : {r['temps_moyen_ms']:.4f} ms/req")

    print()
    print("  Contrefactuel FC — temps vs n:")
    for n in (10000, 50000, 200000):
        t0 = time.perf_counter()
        bn.contrefactuel_fc(obs, intv, "y", n_samples=n)
        dt = (time.perf_counter() - t0) * 1000
        print(f"    n={n:>7} → {dt:7.1f} ms")

    print("\n✓ v8.0 OK")
