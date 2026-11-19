"""alix_moteur_deductif_causal.py — v7.0
Moteur de Raisonnement Déductif local — stdlib uniquement.

Nouveautés v7.0 :
  (o) Mondes possibles : MondeHypothetique (context manager) + Moteur.forker().
      Fork O(n) mémoire (PAS O(1)), saturation isolée, aucune pollution.
  (p) Contrefactuel Pearl Niveau 3 : abduction-action-prédiction via
      Monte-Carlo rejet sur SCM binaire (U ~ Uniform[0,1] par nœud).
      Expose : contrefactuel(), contrefactuel_joint(), probabilites_causales()
      (PN, PS, PNS).
  (q) Révision de croyances : reviser_croyance() → coupe minimale pondérée
      (vertex cover) des faits à suspendre pour restaurer la cohérence.
  (r) Planification inverse : trouver_interventions_optimales() →
      plus petit ensemble do(X_i=x_i) tel que P(Y=1|do) ≥ seuil, coût min.
  + inférence multi-interventions : inference_ve_multi(do_dict=...).
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
# Utils
# ===========================================================================
def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


_VARIABLE_RE = re.compile(r"^\?[A-Za-z_][A-Za-z0-9_]*$")


def est_variable(t: Any) -> bool:
    return isinstance(t, str) and bool(_VARIABLE_RE.match(t))


# ===========================================================================
# Typage sémantique
# ===========================================================================
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

VERBES_FR: Dict[str, str] = {
    "est_un": "est un", "est_une": "est une", "est": "est",
    "cause": "cause", "permet": "permet", "entraine": "entraîne",
    "conduit_a": "conduit à", "mene_a": "mène à", "implique": "implique",
    "affirme": "affirme", "empeche": "empêche", "interdit": "interdit",
    "nie": "nie", "contredit": "contredit",
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


def _unifier(p: Pattern, t: Pattern, s: Dict[str, str]) -> Optional[Dict[str, str]]:
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
# (g) Backend SQLite
# ===========================================================================
class BackendSQLite:
    SCHEMA = """
    PRAGMA journal_mode = MEMORY;
    PRAGMA synchronous = OFF;
    PRAGMA temp_store = MEMORY;
    CREATE TABLE IF NOT EXISTS faits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sujet TEXT NOT NULL, relation TEXT NOT NULL, objet TEXT NOT NULL,
        explication TEXT DEFAULT '', poids REAL DEFAULT 1.0,
        negatif INTEGER DEFAULT 0, derive INTEGER DEFAULT 0,
        UNIQUE(sujet, relation, objet, negatif)
    );
    CREATE INDEX IF NOT EXISTS idx_sr  ON faits(sujet, relation);
    CREATE INDEX IF NOT EXISTS idx_or  ON faits(objet, relation);
    CREATE INDEX IF NOT EXISTS idx_rso ON faits(relation, sujet, objet);
    CREATE INDEX IF NOT EXISTS idx_s   ON faits(sujet);
    CREATE INDEX IF NOT EXISTS idx_o   ON faits(objet);
    """

    def __init__(self, chemin: str = ":memory:") -> None:
        self.chemin = chemin
        self.conn = sqlite3.connect(chemin)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(self.SCHEMA)
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

    def charger_tout(self) -> List[FaitRelationnel]:
        return [self._row_to_fait(r)
                for r in self.conn.execute("SELECT * FROM faits")]

    def compter(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM faits").fetchone()[0]

    @staticmethod
    def _row_to_fait(r: sqlite3.Row) -> FaitRelationnel:
        return FaitRelationnel(r["sujet"], r["relation"], r["objet"],
                               r["explication"] or "", (), float(r["poids"]),
                               bool(r["negatif"]))

    def fermer(self) -> None:
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
        if not est_variable(s):
            clauses.append("sujet=?"); args.append(_norm(s))
        if not est_variable(r):
            clauses.append("relation=?"); args.append(_norm(r))
        if not est_variable(o):
            clauses.append("objet=?"); args.append(_norm(o))
        sql = "SELECT COUNT(*) FROM faits"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        n = self.backend.conn.execute(sql, args).fetchone()[0]
        self._cache[key] = n
        return n

    def ordonner_atomes(self, corps: Tuple[Pattern, ...]) -> List[int]:
        scores = [(i, self.estimer_cardinalite(a))
                  for i, a in enumerate(corps)]
        scores.sort(key=lambda x: x[1])
        return [i for i, _ in scores]


# ===========================================================================
# (k) Compilation SQL
# ===========================================================================
def _compiler_regle_sql(regle, delta_pos=None, ordre=None,
                        mode_poids="produit", table_cible="faits"):
    n = len(regle.corps)
    corps_eff = regle.corps if ordre is None else tuple(regle.corps[i] for i in ordre)
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
    poids_expr = f"{fn}({poids_cols}, ?)"
    explication = f"dérivé « {regle.nom} » (SQL)"

    sql = (
        f"INSERT OR IGNORE INTO {table_cible} "
        f"(sujet, relation, objet, explication, poids, negatif, derive) "
        f"SELECT {', '.join(select_parts)}, ?, {poids_expr}, 0, 1 "
        f"FROM {' JOIN '.join(froms)} WHERE {' AND '.join(wheres)}")
    all_params = head_params + [explication, regle.poids] + params_where
    return sql, all_params


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
# GrapheCausal (avec contrefactuel Pearl 3)
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
        self.noeuds.add(s); self.noeuds.add(c)
        self.enfants[s].add(c); self.parents[c].add(s)
        self._topo_cache = None

    def ancetres(self, x: str) -> Set[str]:
        vus = set(); q = deque(self.parents[_norm(x)])
        while q:
            p = q.popleft()
            if p in vus:
                continue
            vus.add(p); q.extend(self.parents[p])
        return vus

    def descendants(self, x: str) -> Set[str]:
        vus = set(); q = deque(self.enfants[_norm(x)])
        while q:
            c = q.popleft()
            if c in vus:
                continue
            vus.add(c); q.extend(self.enfants[c])
        return vus

    def confondants(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return (self.ancetres(x) & self.ancetres(y)) - {x, y}

    def detecter_cycles(self) -> List[List[str]]:
        BLANC, GRIS, NOIR = 0, 1, 2
        couleur = {n: BLANC for n in self.noeuds}
        parent_dfs = {}
        cycles = []
        def dfs(u):
            couleur[u] = GRIS
            for v in self.enfants.get(u, set()):
                if couleur[v] == GRIS:
                    cycle = [v, u]; cur = u
                    while cur in parent_dfs and parent_dfs[cur] != v:
                        cur = parent_dfs[cur]; cycle.append(cur)
                    cycle.append(v)
                    cycles.append(list(reversed(cycle)))
                elif couleur[v] == BLANC:
                    parent_dfs[v] = u; dfs(v)
            couleur[u] = NOIR
        for n in list(self.noeuds):
            if couleur[n] == BLANC:
                dfs(n)
        return cycles

    def est_dag(self) -> bool:
        return not self.detecter_cycles()

    def d_separes(self, x_set, y_set, z_set, ignorer_sortants_de=None) -> bool:
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
        for y in ys:
            if (y, "up") in visit or (y, "down") in visit:
                return False
        return True

    def backdoor_valide(self, x, y, z_set) -> bool:
        return self.d_separes({_norm(x)}, {_norm(y)}, z_set,
                              ignorer_sortants_de={_norm(x)})

    def backdoor_set_simple(self, x, y) -> Set[str]:
        x, y = _norm(x), _norm(y)
        desc_x = self.descendants(x)
        parents_x = {p for p in self.parents[x] if p not in desc_x}
        return self.confondants(x, y) | parents_x

    # --- Paramétrage -------------------------------------------------
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
        vars_presentes = set(lignes[0].keys())
        manquants = [n for n in self.noeuds if n not in vars_presentes]
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
                n1 = c1.get(pv, 0); nt = cn.get(pv, 0)
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
        if src <= {"heuristique_noisy_or", "explicite"}:
            return "heuristique_noisy_or"
        return "mixte"

    def _p1_conditionnel(self, n, parents_vals):
        if n in self._cpts:
            return self._cpts[n].get(tuple(parents_vals), 0.0)
        parents = sorted(self.parents[n])
        if not parents:
            return self._priors.get(n, 0.1)
        leak = self._priors.get(n, 0.01)
        p_no = 1.0 - leak
        for p, val in zip(parents, parents_vals):
            if val == 1:
                p_no *= (1.0 - self._poids_arete.get((p, n), 0.5))
        return 1.0 - p_no

    # --- Facteurs + VE ----------------------------------------------
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
                pv = vals[:len(parents)]
                p1 = self._p1_conditionnel(n, pv)
                table[vals] = p1 if vals[-1] == 1 else 1.0 - p1
            facteurs.append((scope, table))
        return facteurs

    @staticmethod
    def _restreindre(facteur, evidence):
        scope, table = facteur
        pos = [i for i, v in enumerate(scope) if v in evidence]
        if not pos:
            return facteur
        new_scope = tuple(v for i, v in enumerate(scope) if i not in pos)
        new_table = defaultdict(float)
        for vals, p in table.items():
            if all(vals[i] == evidence[scope[i]] for i in pos):
                nk = tuple(v for i, v in enumerate(vals) if i not in pos)
                new_table[nk] += p
        return new_scope, dict(new_table)

    @staticmethod
    def _multiplier(f1, f2):
        s1, t1 = f1; s2, t2 = f2
        scope = tuple(sorted(set(s1) | set(s2)))
        idx1 = [scope.index(v) for v in s1]
        idx2 = [scope.index(v) for v in s2]
        table = defaultdict(float)
        for vals1, p1 in t1.items():
            for vals2, p2 in t2.items():
                ok = True
                for i, v in enumerate(s1):
                    if v in s2 and vals1[i] != vals2[s2.index(v)]:
                        ok = False; break
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
    def _sommer_sur(facteur, var):
        scope, table = facteur
        if var not in scope:
            return facteur
        i = scope.index(var)
        new_scope = tuple(v for j, v in enumerate(scope) if j != i)
        new_table = defaultdict(float)
        for vals, p in table.items():
            key = tuple(v for j, v in enumerate(vals) if j != i)
            new_table[key] += p
        return new_scope, dict(new_table)

    def inference_ve(self, query_var, evidence=None, do_dict=None):
        evidence = {_norm(k): int(v) for k, v in (evidence or {}).items()}
        facteurs = [self._restreindre(f, evidence)
                    for f in self._construire_facteurs(do_dict=do_dict)]
        cache = set(evidence.keys())
        cache.update({_norm(k) for k in (do_dict or {}).keys()})
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

    def comparer_observation_vs_intervention(self, x, y):
        if not self.est_dag():
            raise ValueError("Graphe cyclique — do(X) refusé.")
        x, y = _norm(x), _norm(y)
        p_obs = self.inference_ve(y, {x: 1})
        p_do = self.inference_ve(y, {x: 1}, do_dict={x: 1})
        return {"P(Y=1|X=1)": p_obs[1],
                "P(Y=1|do(X=1))": p_do[1],
                "delta_biais": abs(p_obs[1] - p_do[1]),
                "confondants": sorted(self.confondants(x, y)),
                "backdoor_set": sorted(self.backdoor_set_simple(x, y))}

    # --- (p) Contrefactuel Pearl Niveau 3 ---------------------------
    def _ordre_topo(self) -> List[str]:
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
        """Propagation déterministe V = f(Pa(V), U_V)."""
        do_dict = {_norm(k): int(v) for k, v in (do_dict or {}).items()}
        V: Dict[str, int] = {}
        for n in self._ordre_topo():
            if n in do_dict:
                V[n] = do_dict[n]
                continue
            parents = sorted(self.parents[n])
            pv = tuple(V[p] for p in parents)
            p1 = self._p1_conditionnel(n, pv)
            V[n] = 1 if U[n] < p1 else 0
        return V

    def _compatible(self, V: Dict[str, int], evidence: Dict[str, int]) -> bool:
        return all(V.get(k) == v for k, v in evidence.items())

    def contrefactuel(self, observation: Dict[str, int],
                      intervention: Dict[str, int],
                      requete: str,
                      n_samples: int = 50000,
                      seed: int = 42) -> Dict[str, Any]:
        """
        Pearl Niveau 3 : P(Y_x = 1 | observation).
        Étape 1 (Abduction) + Action + Prédiction.
        Monte-Carlo rejet — erreur-type ≈ 1/√n_effectif.
        """
        if not self.est_dag():
            raise ValueError("Graphe cyclique — contrefactuel refusé.")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        intv = {_norm(k): int(v) for k, v in intervention.items()}
        q = _norm(requete)
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        n_match = 0
        n_true = 0
        for _ in range(n_samples):
            U = {n: rng.random() for n in noeuds}
            V = self._forward(U)
            if not self._compatible(V, obs):
                continue
            n_match += 1
            Vcf = self._forward(U, do_dict=intv)
            if Vcf.get(q, 0) == 1:
                n_true += 1
        if n_match == 0:
            return {"P": float("nan"), "n_match": 0, "n_samples": n_samples}
        return {"P": n_true / n_match,
                "n_match": n_match, "n_samples": n_samples,
                "erreur_std_approx": math.sqrt(
                    (n_true / n_match) * (1 - n_true / n_match)
                    / max(n_match, 1))}

    def contrefactuel_joint(self, observation: Dict[str, int],
                            interventions: List[Dict[str, int]],
                            requetes: List[str],
                            n_samples: int = 50000,
                            seed: int = 42) -> Dict[str, Any]:
        """
        P(requete_1^do_1 = 1, ..., requete_k^do_k = 1 | observation).
        Même U pour tous les mondes contrefactuels — c'est l'essence du twin network.
        """
        if not self.est_dag():
            raise ValueError("Graphe cyclique — contrefactuel refusé.")
        obs = {_norm(k): int(v) for k, v in observation.items()}
        intvs = [{_norm(k): int(v) for k, v in d.items()} for d in interventions]
        qs = [_norm(q) for q in requetes]
        if len(intvs) != len(qs):
            raise ValueError("interventions et requetes doivent avoir même longueur")
        rng = random.Random(seed)
        noeuds = list(self.noeuds)
        n_match = 0
        n_joint = 0
        for _ in range(n_samples):
            U = {n: rng.random() for n in noeuds}
            V = self._forward(U)
            if not self._compatible(V, obs):
                continue
            n_match += 1
            ok = True
            for intv, q in zip(intvs, qs):
                Vcf = self._forward(U, do_dict=intv)
                if Vcf.get(q, 0) != 1:
                    ok = False; break
            if ok:
                n_joint += 1
        if n_match == 0:
            return {"P": float("nan"), "n_match": 0}
        return {"P": n_joint / n_match, "n_match": n_match,
                "n_samples": n_samples}

    def probabilites_causales(self, x: str, y: str,
                              n_samples: int = 50000,
                              seed: int = 42) -> Dict[str, Any]:
        """
        Pearl :
          PN  = P(Y_{x=0}=0 | X=1, Y=1)   (nécessité)
          PS  = P(Y_{x=1}=1 | X=0, Y=0)   (suffisance)
          PNS = P(Y_{x=1}=1, Y_{x=0}=0)    (joint, sans conditionnement)
        """
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
                Vcf = self._forward(U, do_dict={x: 0})
                if Vcf.get(y, 0) == 0:
                    pn_num += 1
            if xv == 0 and yv == 0:
                n00 += 1
                Vcf = self._forward(U, do_dict={x: 1})
                if Vcf.get(y, 0) == 1:
                    ps_num += 1
            Vcf1 = self._forward(U, do_dict={x: 1})
            Vcf0 = self._forward(U, do_dict={x: 0})
            if Vcf1.get(y, 0) == 1 and Vcf0.get(y, 0) == 0:
                pns_num += 1
        return {
            "PN":  pn_num / n11 if n11 else float("nan"),
            "PS":  ps_num / n00 if n00 else float("nan"),
            "PNS": pns_num / n_samples,
            "n_X1Y1": n11, "n_X0Y0": n00, "n_samples": n_samples,
        }


# ===========================================================================
# (l) Junction Tree
# ===========================================================================
class JunctionTree:
    def __init__(self, graphe: GrapheCausal) -> None:
        self.graphe = graphe
        adj_moral = _moraliser(graphe.parents, graphe.noeuds)
        cliques, _ = _trianguler_min_fill(adj_moral)
        self.cliques = cliques
        self.adj_cliques, self.parent_tree = self._construire_arbre()
        self.potentiels = self._init_potentiels()
        self.messages = {}
        self._passer_messages()

    def _construire_arbre(self, root=0):
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
        par_tree = {root: None}
        q = [root]
        while q:
            u = q.pop()
            for v, _ in adj[u]:
                if v not in par_tree:
                    par_tree[v] = u; q.append(v)
        return adj, par_tree

    def _init_potentiels(self):
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
                pv = tuple(vals[pos[p]] for p in parents)
                p1 = self.graphe._p1_conditionnel(n, pv)
                proba = p1 if vals[pos[n]] == 1 else 1.0 - p1
                pot[target][vals] *= proba
        return pot

    def _message(self, src, dst):
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

    def _passer_messages(self):
        self.messages = {}
        ordre_post = []
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

    def _query_marginal(self, var):
        var = _norm(var)
        target = next((i for i, c in enumerate(self.cliques) if var in c), None)
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

    def query(self, var, evidence=None, do_dict=None):
        if do_dict is not None:
            g2 = self.graphe._graphe_sans_parents_multi(do_dict)
            return JunctionTree(g2).query(var, evidence=evidence)
        if not evidence:
            return self._query_marginal(var)
        ev = {_norm(k): int(v) for k, v in evidence.items()}
        jt = JunctionTree.__new__(JunctionTree)
        jt.graphe = self.graphe
        jt.cliques = self.cliques
        jt.adj_cliques = self.adj_cliques
        jt.parent_tree = self.parent_tree
        jt.potentiels = []
        for i, c in enumerate(self.cliques):
            scope = tuple(sorted(c))
            new_pot = defaultdict(float)
            for vals, p in self.potentiels[i].items():
                ok = True
                for k, v in ev.items():
                    if k in c and vals[scope.index(k)] != v:
                        ok = False; break
                if ok:
                    new_pot[vals] += p
            jt.potentiels.append(new_pot)
        jt.messages = {}
        jt._passer_messages()
        return jt._query_marginal(var)


# Patch : _graphe_sans_parents_multi
def _graphe_sans_parents_multi(self, do_dict):
    do_dict = {_norm(k): int(v) for k, v in do_dict.items()}
    g = GrapheCausal()
    for n in self.noeuds:
        g.noeuds.add(n)
    for u in self.enfants:
        for v in self.enfants[u]:
            if v in do_dict:
                continue
            g.ajouter_arete(u, v)
    g._priors = dict(self._priors)
    g._poids_arete = dict(self._poids_arete)
    g._cpts = {k: dict(v) for k, v in self._cpts.items() if k not in do_dict}
    g._cpts_source = {k: v for k, v in self._cpts_source.items()
                      if k not in do_dict}
    return g


GrapheCausal._graphe_sans_parents_multi = _graphe_sans_parents_multi


# ===========================================================================
# (o) Mondes possibles
# ===========================================================================
class MondeHypothetique:
    """Context manager : fork isolé du moteur.
    O(n) mémoire — PAS O(1). Utiliser pour petits graphes (< 10⁵ faits)."""

    def __init__(self, moteur, faits_supposes=None, regles_supposees=None):
        self.moteur_orig = moteur
        self.faits_supposes = list(faits_supposes or [])
        self.regles_supposees = list(regles_supposees or [])
        self.moteur_local: Optional[MoteurDeductifCausal] = None

    def __enter__(self):
        self.moteur_local = self.moteur_orig.forker(
            faits_supposes=self.faits_supposes,
            regles_supposees=self.regles_supposees)
        return self.moteur_local

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.moteur_local = None
        return False


# ===========================================================================
# Moteur
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
                self._ajouter_en_memoire(f)
        for f in (faits or []):
            self.ajouter_fait(f)

    def _ajouter_en_memoire(self, f):
        k = f.cle()
        if k in self._cles_vues:
            return
        self._cles_vues.add(k)
        self.faits.append(f)
        self._index_sujet[_norm(f.sujet)].append(f)
        self._index_objet[_norm(f.objet)].append(f)
        self._index_relation[_norm(f.relation)].append(f)

    def ajouter_fait(self, f) -> bool:
        if f.cle() in self._cles_vues:
            return False
        self._ajouter_en_memoire(f)
        if self.backend is not None:
            self.backend.ajouter(f)
        self._cache.clear()
        self._graphe_causal = None
        return True

    def ajouter_regle(self, r):
        self.regles.append(r)

    def forker(self, faits_supposes=None, regles_supposees=None):
        """Clone isolé. O(n) mémoire."""
        m = MoteurDeductifCausal(
            faits=list(self.faits),
            regles=list(self.regles) + list(regles_supposees or []))
        for f in (faits_supposes or []):
            m.ajouter_fait(f)
        return m

    def _cache_put(self, cle, valeur):
        self._cache[cle] = valeur
        self._cache.move_to_end(cle)
        if len(self._cache) > self._cache_taille:
            self._cache.popitem(last=False)

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

    def _trouver_substitutions(self, corps, delta_cles=None, delta_pos=None):
        etats = [({}, 1.0)]
        for pos, atome in enumerate(corps):
            nouveaux = []
            for subst, poids in etats:
                atome_res = _subst_appliquer(atome, subst)
                candidats = self._faits_candidats(atome_res)
                if delta_pos is not None and pos == delta_pos:
                    candidats = [f for f in candidats if f.cle() in delta_cles]
                for fait in candidats:
                    if fait.negatif:
                        continue
                    s2 = _unifier(atome_res,
                                  (fait.sujet, fait.relation, fait.objet), subst)
                    if s2 is not None:
                        nouveaux.append((s2, poids * fait.poids))
            etats = nouveaux
            if not etats:
                return []
        return etats

    @staticmethod
    def _poids_derive(poids_corps, regle, n_atomes, mode):
        if mode == "produit":
            p = poids_corps * regle.poids
        elif mode == "moyenne_geo":
            p = (poids_corps * regle.poids) ** (1.0 / (n_atomes + 1))
        else:
            raise ValueError(f"mode inconnu : {mode}")
        return max(0.01, min(1.0, p))

    def saturer_regles_semi_naif(self, max_iterations=50,
                                 mode_poids_regle="produit"):
        if not self.regles:
            return {"total_derive": 0, "iterations": 0}
        F = {f.cle() for f in self.faits}
        delta = set(F)
        total = 0
        it = 0
        for it in range(1, max_iterations + 1):
            nouveaux = {}
            for regle in self.regles:
                n = len(regle.corps)
                for i in range(n):
                    for subst, p_corps in self._trouver_substitutions(
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
                            explication=f"dérivé « {regle.nom} » (py)", poids=p)
            if not nouveaux:
                break
            delta = set(nouveaux.keys())
            for key, f in nouveaux.items():
                if self.ajouter_fait(f):
                    F.add(key); total += 1
        return {"total_derive": total, "iterations": it}

    def saturer_regles_sql(self, max_iterations=50,
                           mode_poids_regle="produit",
                           utiliser_planner=True):
        if self.backend is None:
            raise RuntimeError("Backend SQLite requis")
        conn = self.backend.conn
        planner = JoinPlanner(self.backend) if utiliser_planner else None
        conn.execute("DROP TABLE IF EXISTS delta")
        conn.execute("CREATE TEMP TABLE delta AS SELECT * FROM faits")
        conn.commit()
        total = 0
        it = 0
        for it in range(1, max_iterations + 1):
            conn.execute("DROP TABLE IF EXISTS nouveaux")
            conn.execute("""CREATE TEMP TABLE nouveaux (
                sujet TEXT, relation TEXT, objet TEXT,
                explication TEXT, poids REAL, negatif INTEGER, derive INTEGER)""")
            for regle in self.regles:
                ordre = planner.ordonner_atomes(regle.corps) if planner else None
                for pos in range(len(regle.corps)):
                    sql, params = _compiler_regle_sql(
                        regle, delta_pos=pos, ordre=ordre,
                        mode_poids=mode_poids_regle, table_cible="nouveaux")
                    conn.execute(sql, params)
            conn.execute("DROP TABLE IF EXISTS delta_tmp")
            conn.execute("""CREATE TEMP TABLE delta_tmp AS
                SELECT DISTINCT n.sujet, n.relation, n.objet,
                                n.explication, n.poids, n.negatif, n.derive
                FROM nouveaux n WHERE NOT EXISTS (
                    SELECT 1 FROM faits f
                    WHERE f.sujet=n.sujet AND f.relation=n.relation
                      AND f.objet=n.objet AND f.negatif=n.negatif)""")
            n_new = conn.execute("SELECT COUNT(*) FROM delta_tmp").fetchone()[0]
            if n_new == 0:
                break
            conn.execute("""INSERT INTO faits
                (sujet, relation, objet, explication, poids, negatif, derive)
                SELECT sujet, relation, objet, explication, poids, negatif, 1
                FROM delta_tmp""")
            conn.execute("DROP TABLE IF EXISTS delta")
            conn.execute("ALTER TABLE delta_tmp RENAME TO delta")
            conn.commit()
            total += n_new
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
        return {"total_derive": total, "iterations": it}

    # --- Dijkstra ----------------------------------------------------
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
        self._cache_put(cle, res)
        return res

    def poids_chaine(self, chemin, mode_poids="produit"):
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

    # --- Contradictions ---------------------------------------------
    def _sont_opposes(self, f1, f2):
        r1, r2 = _norm(f1.relation), _norm(f2.relation)
        if r1 == r2 and f1.negatif != f2.negatif:
            return True
        return (r2 in RELATIONS_OPPOSEES.get(r1, set())
                or r1 in RELATIONS_OPPOSEES.get(r2, set()))

    def detecter_contradictions(self):
        res = []
        vus = set()
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
                                                f"{f1.objet} VS --{f2.relation}--> "
                                                f"{f2.objet}")})
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
                                            f"{f1.objet} ...-> {f2.objet}, "
                                            f"mais --{f2.relation}--> {f2.objet}")})
        return res

    # --- (q) Révision -------------------------------------------------
    @staticmethod
    def _vertex_cover_min_weight(edges, weights):
        """
        edges : list de (a, b), a,b clés de faits
        weights : dict clé → coût (poids du fait — bas = cheap à retirer)
        Retourne set de clés à retirer (coupe min pondérée).
        """
        best = [None]
        best_w = [float("inf")]

        def rec(remaining, chosen, w):
            if w >= best_w[0]:
                return
            if not remaining:
                if w < best_w[0]:
                    best_w[0] = w
                    best[0] = set(chosen)
                return
            # heuristique : prendre l'arête avec les plus gros poids
            remaining.sort(key=lambda e: -(weights.get(e[0], 1)
                                            + weights.get(e[1], 1)))
            a, b = remaining[0]
            for x in (a, b):
                new_rem = [e for e in remaining if x not in e]
                rec(new_r := new_rem, chosen | {x}, w + weights.get(x, 1.0))

        rec(list(edges), set(), 0.0)
        return best[0] or set()

    def reviser_croyance(self, nouveau_fait, max_contradictions=200):
        """
        Ajoute hypothétiquement `nouveau_fait`, identifie les contradictions,
        calcule la coupe minimale pondérée (faits à suspendre).
        """
        m = self.forker(faits_supposes=[nouveau_fait])
        contradictions = m.detecter_contradictions()[:max_contradictions]
        if not contradictions:
            return {"coherent": True, "contradictions": [],
                    "coupe_min": [], "poids_total_retire": 0.0}
        edges = []
        poids_map = {f.cle(): f.poids for f in m.faits}
        for c in contradictions:
            edges.append((c["fait_1"].cle(), c["fait_2"].cle()))
        coupe = self._vertex_cover_min_weight(edges, poids_map)
        faits_a_retirer = [f for f in m.faits if f.cle() in coupe]
        return {
            "coherent": False,
            "contradictions": contradictions,
            "coupe_min": faits_a_retirer,
            "poids_total_retire": sum(poids_map[k] for k in coupe),
        }

    # --- (r) Planification inverse -----------------------------------
    def trouver_interventions_optimales(
        self, cible_y, seuil_prob,
        candidats_x=None, max_k=3,
        couts=None, valeurs=(1,), verbose=False,
    ):
        """
        Plus petit ensemble do(X_i = x_i) t.q. P(Y=1|do) ≥ seuil_prob
        avec coût minimal. Enumération exhaustive jusqu'à max_k.
        valeurs : tuple de valeurs cibles à tester pour chaque X.
        """
        g = self.vers_graphe_causal()
        if not g.est_dag():
            raise ValueError("Graphe cyclique")
        y = _norm(cible_y)
        if candidats_x is None:
            desc = g.descendants(y)
            candidats_x = sorted(n for n in g.noeuds
                                 if n != y and n not in desc)
        else:
            candidats_x = [_norm(x) for x in candidats_x]
        couts = {_norm(k): v for k, v in (couts or {}).items()}
        def cout(v):
            return couts.get(v, 1.0)
        meilleur = None
        for k in range(1, min(max_k, len(candidats_x)) + 1):
            for subset in itertools.combinations(candidats_x, k):
                for values in itertools.product(valeurs, repeat=k):
                    do = dict(zip(subset, values))
                    p = g.inference_ve(y, {}, do_dict=do)[1]
                    if p >= seuil_prob:
                        c = sum(cout(v) for v in subset)
                        if meilleur is None or c < meilleur["cout"]:
                            meilleur = {"interventions": do, "proba": p,
                                        "cout": c, "k": k}
            if meilleur is not None:
                break
        if meilleur is None:
            return {"trouve": False, "raison":
                    f"Aucune combinaison ≤ {max_k} interventions n'atteint "
                    f"{seuil_prob}"}
        return {"trouve": True, **meilleur}

    # --- Graphe causal -----------------------------------------------
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

    # --- Bench -------------------------------------------------------
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
    print("(o) MONDES POSSIBLES — fork isolé")
    print("=" * 76)
    faits = [
        FaitRelationnel("Socrate", "est_un", "homme", poids=1.0),
        FaitRelationnel("homme", "est_un", "mammifère", poids=0.98),
        FaitRelationnel("mammifère", "est_un", "animal", poids=1.0),
        FaitRelationnel("animal", "est_un", "être_vivant", poids=1.0),
        FaitRelationnel("animal", "est", "mortel", poids=0.99),
    ]
    m = MoteurDeductifCausal(faits=faits, regles=[REGLE_HERITAGE])
    m.saturer_regles_semi_naif()
    n_orig = len(m.faits)
    with MondeHypothetique(m, faits_supposes=[
        FaitRelationnel("Socrate", "est_un", "dieu", poids=0.9),
    ], regles_supposees=[
        Regle(("?x", "est", "immortel"),
              (("?x", "est_un", "dieu"),), nom="dieu_immortel"),
    ]) as m_hyp:
        m_hyp.saturer_regles_semi_naif()
        print(f"  Monde réel : {n_orig} faits")
        print(f"  Monde hyp. : {len(m_hyp.faits)} faits")
        for f in m_hyp.faits:
            if "immortel" in f.objet or "dieu" in f.objet:
                print(f"    → {f.sujet} {f.relation} {f.objet} "
                      f"[{f.poids:.2f}]")
    print(f"  Après sortie : {len(m.faits)} faits (inchangé)")

    print()
    print("=" * 76)
    print("(p) CONTREFACTUEL PEARL 3 — modèle à confondant Z")
    print("=" * 76)
    bn = GrapheCausal()
    bn.ajouter_arete("z", "x"); bn.ajouter_arete("z", "y")
    bn.ajouter_arete("x", "y")
    bn.set_prior("z", 0.5)
    bn.set_cpt("x", {(1,): 0.9, (0,): 0.1})
    bn.set_cpt("y", {(1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1})

    cf = bn.contrefactuel({"x": 1, "y": 1}, {"x": 0}, "y",
                          n_samples=100000)
    print(f"  P(Y_{{do(X=0)}}=1 | X=1, Y=1) = {cf['P']:.4f}  "
          f"(n_match={cf['n_match']}, ±{cf['erreur_std_approx']:.4f})")
    print(f"  → Probabilité de nécessité contrefactuelle = "
          f"{1 - cf['P']:.4f}")

    pc = bn.probabilites_causales("x", "y", n_samples=100000)
    print(f"  PN  = {pc['PN']:.4f}  (nécessité)")
    print(f"  PS  = {pc['PS']:.4f}  (suffisance)")
    print(f"  PNS = {pc['PNS']:.4f}  (nécessité et suffisance)")

    print()
    print("=" * 76)
    print("(q) RÉVISION — coupe minimale d'incohérence")
    print("=" * 76)
    m2 = MoteurDeductifCausal(faits=[
        FaitRelationnel("fumer", "cause", "cancer", poids=0.8),
        FaitRelationnel("fumer", "empeche", "cancer", poids=0.4),
        FaitRelationnel("fumer", "cause", "santé", poids=0.6),
        FaitRelationnel("tabac", "cause", "cancer", poids=0.9),
        FaitRelationnel("tabac", "empeche", "cancer", poids=0.3),
    ])
    print(f"  Contradictions pré-existantes : "
          f"{len(m2.detecter_contradictions())}")
    rev = m2.reviser_croyance(
        FaitRelationnel("fumer", "empeche", "santé", poids=0.5))
    print(f"  Cohérent après ajout : {rev['coherent']}")
    if not rev["coherent"]:
        print(f"  Coupe min ({len(rev['coupe_min'])} fait(s), "
              f"poids total {rev['poids_total_retire']:.2f}) :")
        for f in rev["coupe_min"]:
            print(f"    ⊘ {f.sujet} {f.relation} {f.objet} [{f.poids:.2f}]")

    print()
    print("=" * 76)
    print("(r) PLANIFICATION INVERSE")
    print("=" * 76)
    bn2 = GrapheCausal()
    bn2.ajouter_arete("tabac", "goudron")
    bn2.ajouter_arete("goudron", "cancer")
    bn2.ajouter_arete("amiante", "cancer")
    bn2.ajouter_arete("genetique", "cancer")
    bn2.set_prior("tabac", 0.3)
    bn2.set_prior("amiante", 0.2)
    bn2.set_prior("genetique", 0.1)
    bn2.set_poids_arete("tabac", "goudron", 0.7)
    bn2.set_poids_arete("goudron", "cancer", 0.6)
    bn2.set_poids_arete("amiante", "cancer", 0.5)
    bn2.set_poids_arete("genetique", "cancer", 0.4)

    p0 = bn2.inference_ve("cancer", {})[1]
    print(f"  P(cancer) baseline = {p0:.4f}")
    for seuil in (0.5, 0.7, 0.85):
        moteur_fictif = MoteurDeductifCausal(faits=[])
        moteur_fictif._graphe_causal = bn2
        res = moteur_fictif.trouver_interventions_optimales(
            "cancer", seuil, max_k=3, valeurs=(0, 1))
        if res["trouve"]:
            print(f"  Seuil {seuil:.2f} : {res['interventions']} "
                  f"→ P={res['proba']:.4f}, coût={res['cout']}")
        else:
            print(f"  Seuil {seuil:.2f} : {res['raison']}")

    print()
    print("=" * 76)
    print("BENCH")
    print("=" * 76)
    r = m.bench(3000)
    print(f"  Dijkstra : {r['temps_moyen_ms']:.4f} ms/req")

    print()
    print("=" * 76)
    print("BENCH CONTREFACTUEL")
    print("=" * 76)
    for n in (10000, 50000, 100000):
        t0 = time.perf_counter()
        bn.contrefactuel({"x": 1, "y": 1}, {"x": 0}, "y", n_samples=n)
        dt = (time.perf_counter() - t0) * 1000
        print(f"  n={n:>7} → {dt:7.1f} ms")

    print("\n✓ v7.0 OK")
