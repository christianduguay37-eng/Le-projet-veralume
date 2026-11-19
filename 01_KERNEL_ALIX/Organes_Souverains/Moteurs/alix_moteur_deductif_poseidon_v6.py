"""alix_moteur_deductif_causal.py — v6.0
Moteur de Raisonnement Déductif local — stdlib uniquement.

Nouveautés v6.0 :
  (k) SQL pushdown du Datalog semi-naïf : compilation de chaque clause de Horn
      en INSERT ... SELECT ... JOIN, exécutée par le moteur C de SQLite.
      Table `delta` pour ne joindre qu'avec les faits frais de l'itération k-1.
  (m) JoinPlanner : estime la cardinalité de chaque atome par COUNT(*),
      ordonne les atomes du corps du plus sélectif au moins sélectif.
  (n) apprendre_cpts_depuis_observations() : fréquences conditionnelles
      avec lissage de Laplace. Tag source_modele = "empirique_csv" |
      "heuristique_noisy_or" | "mixte".
  (l) JunctionTree (Shafer-Shenoy) : moralisation, triangulation min-fill,
      cliques maximales, arbre couvrant max par intersection, messages
      exacts collect + distribute.

LIMITES :
  - JT exact mais exponentiel en largeur d'arbre. Pour > ~20 nœuds denses,
    passer à une décomposition par junction tree avec compression.
  - L'apprentissage CPT suppose i.i.d. et absence de confusion — c'est un
    estimateur observationnel, pas causal.
  - SQL pushdown prend le premier dérivé (ordre plan). Pour un dérivé "optimal"
    en poids, agréger avec MAX(poids) en GROUP BY (non fait ici).
"""
from __future__ import annotations

import heapq
import itertools
import math
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
        # Fonctions SQL custom (stdlib) pour le poids
        self.conn.create_function(
            "prod_all", -1,
            lambda *xs: max(0.01, min(1.0, math.prod(xs))))
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
             f.explication, f.poids, int(f.negatif), int(derive)),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def chercher_atome(self, sujet: Any, relation: Any, objet: Any,
                       negatif: Optional[bool] = None) -> List[FaitRelationnel]:
        clauses, args = [], []
        if not est_variable(sujet):
            clauses.append("sujet=?"); args.append(_norm(sujet))
        if not est_variable(relation):
            clauses.append("relation=?"); args.append(_norm(relation))
        if not est_variable(objet):
            clauses.append("objet=?"); args.append(_norm(objet))
        if negatif is not None:
            clauses.append("negatif=?"); args.append(int(negatif))
        sql = "SELECT * FROM faits"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        return [self._row_to_fait(r) for r in self.conn.execute(sql, args)]

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
# (m) JoinPlanner
# ===========================================================================
class JoinPlanner:
    """Ordonne les atomes d'un corps par cardinalité estimée (COUNT(*))."""

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
        """Retourne l'ordre des indices d'atomes du plus sélectif au moins."""
        scores = [(i, self.estimer_cardinalite(a))
                  for i, a in enumerate(corps)]
        scores.sort(key=lambda x: x[1])
        return [i for i, _ in scores]


# ===========================================================================
# (k) Compilateur SQL pour clauses de Horn
# ===========================================================================
def _compiler_regle_sql(
    regle: Regle, delta_pos: Optional[int] = None,
    ordre: Optional[List[int]] = None,
    mode_poids: str = "produit",
    table_cible: str = "faits",
) -> Tuple[str, List[Any]]:
    """
    Compile une règle en INSERT OR IGNORE INTO <cible> SELECT ... JOIN ...
    `ordre` : si fourni, réordonne les atomes du corps (indices dans corps).
    """
    n = len(regle.corps)
    corps_effectif = regle.corps if ordre is None else tuple(
        regle.corps[i] for i in ordre)
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
# Helpers GrapheCausal : moralisation + triangulation min-fill
# ===========================================================================
def _moraliser(parents: Dict[str, Set[str]], noeuds: Set[str]
               ) -> Dict[str, Set[str]]:
    adj: Dict[str, Set[str]] = {n: set() for n in noeuds}
    for n in noeuds:
        ps = list(parents.get(n, set()))
        for p in ps:
            adj[n].add(p); adj[p].add(n)
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                adj[ps[i]].add(ps[j]); adj[ps[j]].add(ps[i])
    return adj


def _trianguler_min_fill(adj_in: Dict[str, Set[str]]
                         ) -> Tuple[List[frozenset], Dict[str, Set[str]]]:
    """Retourne (cliques maximales, adj triangulée)."""
    adj = {k: set(v) for k, v in adj_in.items()}
    remaining = set(adj.keys())
    cliques_pot: List[frozenset] = []

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

    # Garder les cliques maximales
    maximales: List[frozenset] = []
    for c in cliques_pot:
        if not any(c != c2 and c.issubset(c2) for c2 in cliques_pot):
            maximales.append(c)
    # dédup
    vues: Set[frozenset] = set()
    out: List[frozenset] = []
    for c in maximales:
        if c not in vues:
            vues.add(c); out.append(c)
    return out, adj


# ===========================================================================
# (i) + (h) + (n) + (l) GrapheCausal + JunctionTree
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

    # --- structure ---------------------------------------------------
    def ajouter_arete(self, s: str, c: str) -> None:
        s, c = _norm(s), _norm(c)
        if s == c:
            return
        self.noeuds.add(s); self.noeuds.add(c)
        self.enfants[s].add(c); self.parents[c].add(s)

    def ancetres(self, x: str) -> Set[str]:
        vus: Set[str] = set(); q = deque(self.parents[_norm(x)])
        while q:
            p = q.popleft()
            if p in vus:
                continue
            vus.add(p); q.extend(self.parents[p])
        return vus

    def descendants(self, x: str) -> Set[str]:
        vus: Set[str] = set(); q = deque(self.enfants[_norm(x)])
        while q:
            c = q.popleft()
            if c in vus:
                continue
            vus.add(c); q.extend(self.enfants[c])
        return vus

    def confondants(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return (self.ancetres(x) & self.ancetres(y)) - {x, y}

    # --- (i) Cycles --------------------------------------------------
    def detecter_cycles(self) -> List[List[str]]:
        BLANC, GRIS, NOIR = 0, 1, 2
        couleur = {n: BLANC for n in self.noeuds}
        parent_dfs: Dict[str, str] = {}
        cycles: List[List[str]] = []

        def dfs(u: str) -> None:
            couleur[u] = GRIS
            for v in self.enfants.get(u, set()):
                if couleur[v] == GRIS:
                    cycle = [v, u]; cur = u
                    while cur in parent_dfs and parent_dfs[cur] != v:
                        cur = parent_dfs[cur]; cycle.append(cur)
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

    def d_separes(self, x_set: Set[str], y_set: Set[str], z_set: Set[str],
                  ignorer_sortants_de: Optional[Set[str]] = None) -> bool:
        ignorer = {_norm(n) for n in (ignorer_sortants_de or set())}
        xs = {_norm(n) for n in x_set}
        ys = {_norm(n) for n in y_set}
        zs = {_norm(n) for n in z_set}
        visit: Set[Tuple[str, str]] = set()
        q: deque = deque()
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

    def backdoor_valide(self, x: str, y: str, z_set: Set[str]) -> bool:
        return self.d_separes({_norm(x)}, {_norm(y)}, z_set,
                              ignorer_sortants_de={_norm(x)})

    def backdoor_set_simple(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        desc_x = self.descendants(x)
        parents_x = {p for p in self.parents[x] if p not in desc_x}
        return self.confondants(x, y) | parents_x

    # --- Paramétrage -------------------------------------------------
    def set_prior(self, noeud: str, p: float) -> None:
        self._priors[_norm(noeud)] = max(0.0, min(1.0, p))

    def set_poids_arete(self, parent: str, enfant: str, q: float) -> None:
        self._poids_arete[(_norm(parent), _norm(enfant))] = max(0.0, min(1.0, q))

    def set_cpt(self, noeud: str, table: Dict[Tuple[int, ...], float],
                source: str = "explicite") -> None:
        self._cpts[_norm(noeud)] = dict(table)
        self._cpts_source[_norm(noeud)] = source

    # --- (n) Apprentissage CPT empirique ----------------------------
    def apprendre_cpts_depuis_observations(
        self, lignes: List[Dict[str, int]],
        lissage_laplace: float = 1.0,
    ) -> None:
        """
        Estime P(V=1 | pa(V)) par fréquences conditionnelles observées
        avec lissage de Laplace α. Suppose i.i.d. — estimateur OBSERVATIONNEL,
        PAS causal. Marque _cpts_source = "empirique_csv".
        """
        if not lignes:
            raise ValueError("Aucune observation fournie")
        vars_presentes = set(lignes[0].keys())
        manquants = [n for n in self.noeuds if n not in vars_presentes]
        if manquants:
            raise ValueError(
                f"Nœuds absents des observations : {manquants}")
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
                cpt[pv] = ((n1 + lissage_laplace)
                           / (nt + 2 * lissage_laplace))
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
                p_no *= (1.0 - q)
        return 1.0 - p_no

    # --- Facteurs (VE et JT partagent ces primitives) ---------------
    def _construire_facteurs(self, do_x: Optional[str] = None
                             ) -> List[Tuple[Tuple[str, ...],
                                             Dict[Tuple[int, ...], float]]]:
        facteurs = []
        for n in sorted(self.noeuds):
            if n == do_x:
                p1 = self._priors.get(n, 0.1)
                facteurs.append(((n,), {(0,): 1.0 - p1, (1,): p1}))
                continue
            parents = sorted(self.parents[n])
            scope = tuple(parents + [n])
            table: Dict[Tuple[int, ...], float] = {}
            for vals in itertools.product((0, 1), repeat=len(scope)):
                pv = vals[:len(parents)]
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
        s1, t1 = f1; s2, t2 = f2
        scope = tuple(sorted(set(s1) | set(s2)))
        idx1 = [scope.index(v) for v in s1]
        idx2 = [scope.index(v) for v in s2]
        table: Dict[Tuple[int, ...], float] = defaultdict(float)
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

    # --- VE (déjà v5.0) ---------------------------------------------
    def inference_ve(self, query_var: str, evidence: Dict[str, int],
                     do_x: Optional[str] = None) -> Dict[int, float]:
        facteurs = [self._restreindre(f, evidence)
                    for f in self._construire_facteurs(do_x=do_x)]
        cache: Set[str] = set(evidence.keys())
        if do_x is not None:
            cache.add(_norm(do_x))
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

    def comparer_observation_vs_intervention(self, x: str, y: str
                                             ) -> Dict[str, Any]:
        if not self.est_dag():
            raise ValueError("Graphe cyclique — do(X) refusé.")
        x, y = _norm(x), _norm(y)
        p_obs = self.inference_ve(y, {x: 1}, do_x=None)
        p_do = self.inference_ve(y, {x: 1}, do_x=x)
        return {
            "P(Y=1|X=1)":     p_obs[1],
            "P(Y=1|do(X=1))": p_do[1],
            "delta_biais":    abs(p_obs[1] - p_do[1]),
            "confondants":    sorted(self.confondants(x, y)),
            "backdoor_set":   sorted(self.backdoor_set_simple(x, y)),
        }

    def _graphe_sans_parents(self, do_x: str) -> "GrapheCausal":
        do_x = _norm(do_x)
        g = GrapheCausal()
        for n in self.noeuds:
            g.noeuds.add(n)
        for u in self.enfants:
            for v in self.enfants[u]:
                if v == do_x:
                    continue
                g.ajouter_arete(u, v)
        g._priors = dict(self._priors)
        g._poids_arete = dict(self._poids_arete)
        g._cpts = {k: dict(v) for k, v in self._cpts.items() if k != do_x}
        g._cpts_source = {k: v for k, v in self._cpts_source.items() if k != do_x}
        return g


# ===========================================================================
# (l) Junction Tree — Shafer-Shenoy
# ===========================================================================
class JunctionTree:
    """Arbre de cliques. Exact mais exponentiel en largeur d'arbre."""

    def __init__(self, graphe: GrapheCausal) -> None:
        self.graphe = graphe
        self.adj_moral = _moraliser(graphe.parents, graphe.noeuds)
        cliques, _ = _trianguler_min_fill(self.adj_moral)
        self.cliques: List[frozenset] = cliques
        self.adj_cliques, self.parent_tree = self._construire_arbre()
        self.potentiels = self._initialiser_potentiels()
        self.messages: Dict[Tuple[int, int], Any] = {}
        self._passer_messages()

    # --- Construction -----------------------------------------------
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
                adj[i].append((j, sep)); adj[j].append((i, sep))
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
                    target = idx; break
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

    # --- Message passing --------------------------------------------
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
        # Collecte (post-order)
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
        # Distribution (pre-order)
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
                target = i; break
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

    def query(self, var: str, evidence: Optional[Dict[str, int]] = None,
              do_x: Optional[str] = None) -> Dict[int, float]:
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
                            ok = False; break
                    if ok:
                        new_pot[vals] += p
                jt.potentiels[i] = new_pot
            jt.messages = {}
            jt._passer_messages()
        return jt._query_marginal(var)

    def comparer_observation_vs_intervention(self, x: str, y: str
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
# Moteur principal
# ===========================================================================
class MoteurDeductifCausal:
    def __init__(
        self, encyclopedie: Any = None,
        faits: Optional[List[FaitRelationnel]] = None,
        regles: Optional[List[Regle]] = None,
        backend_sqlite: Optional[BackendSQLite] = None,
        cache_taille: int = 512,
    ) -> None:
        self.encyclopedie = encyclopedie
        self.backend = backend_sqlite
        self.regles: List[Regle] = list(regles or [])
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
        for f in (faits or []):
            self.ajouter_fait(f)

    def _ajouter_en_memoire(self, f: FaitRelationnel) -> None:
        k = f.cle()
        if k in self._cles_vues:
            return
        self._cles_vues.add(k)
        self.faits.append(f)
        self._index_sujet[_norm(f.sujet)].append(f)
        self._index_objet[_norm(f.objet)].append(f)
        self._index_relation[_norm(f.relation)].append(f)

    def ajouter_fait(self, f: FaitRelationnel) -> bool:
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

    # --- Semi-naïf Python (v5.0) ------------------------------------
    def _trouver_substitutions(self, corps, delta_cles=None, delta_pos=None
                               ) -> List[Tuple[Dict[str, str], float]]:
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
                                  (fait.sujet, fait.relation, fait.objet),
                                  subst)
                    if s2 is not None:
                        nouveaux.append((s2, poids * fait.poids))
            etats = nouveaux
            if not etats:
                return []
        return etats

    @staticmethod
    def _poids_derive(poids_corps, regle, n_atomes, mode) -> float:
        if mode == "produit":
            p = poids_corps * regle.poids
        elif mode == "moyenne_geo":
            p = (poids_corps * regle.poids) ** (1.0 / (n_atomes + 1))
        else:
            raise ValueError(f"mode_poids_regle inconnu : {mode}")
        return max(0.01, min(1.0, p))

    def saturer_regles_semi_naif(self, max_iterations=50,
                                 mode_poids_regle="produit") -> Dict[str, Any]:
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
                        regle.corps, delta_cles=delta, delta_pos=i,
                    ):
                        tete = _subst_appliquer(regle.tete, subst)
                        s, r, o = tete
                        key = (_norm(s), _norm(r), _norm(o), False)
                        if key in F or key in nouveaux:
                            continue
                        p = self._poids_derive(poids_corps, regle, n,
                                               mode_poids_regle)
                        nouveaux[key] = FaitRelationnel(
                            s, r, o,
                            explication=f"dérivé « {regle.nom} » (py)", poids=p)
            if not nouveaux:
                break
            delta = set(nouveaux.keys())
            for key, f in nouveaux.items():
                if self.ajouter_fait(f):
                    F.add(key); total_derive += 1
        return {"total_derive": total_derive, "iterations": iteration}

    # --- (k) Semi-naïf SQL pushdown ---------------------------------
    def saturer_regles_sql(self, max_iterations: int = 50,
                           mode_poids_regle: str = "produit",
                           utiliser_planner: bool = True) -> Dict[str, Any]:
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
            conn.execute("""CREATE TEMP TABLE nouveaux (
                sujet TEXT, relation TEXT, objet TEXT,
                explication TEXT, poids REAL, negatif INTEGER, derive INTEGER)""")
            for regle in self.regles:
                ordre = (planner.ordonner_atomes(regle.corps)
                         if planner else None)
                for pos in range(len(regle.corps)):
                    sql, params = _compiler_regle_sql(
                        regle, delta_pos=pos, ordre=ordre,
                        mode_poids=mode_poids_regle,
                        table_cible="nouveaux",
                    )
                    conn.execute(sql, params)

            conn.execute("DROP TABLE IF EXISTS delta_tmp")
            conn.execute("""
                CREATE TEMP TABLE delta_tmp AS
                SELECT DISTINCT n.sujet, n.relation, n.objet,
                                n.explication, n.poids, n.negatif, n.derive
                FROM nouveaux n
                WHERE NOT EXISTS (
                    SELECT 1 FROM faits f
                    WHERE f.sujet=n.sujet AND f.relation=n.relation
                      AND f.objet=n.objet AND f.negatif=n.negatif
                )
            """)
            n_new = conn.execute(
                "SELECT COUNT(*) FROM delta_tmp").fetchone()[0]
            if n_new == 0:
                break

            conn.execute("""
                INSERT INTO faits (sujet, relation, objet, explication,
                                   poids, negatif, derive)
                SELECT sujet, relation, objet, explication, poids, negatif, 1
                FROM delta_tmp
            """)
            conn.execute("DROP TABLE IF EXISTS delta")
            conn.execute("ALTER TABLE delta_tmp RENAME TO delta")
            conn.commit()
            total_derive += n_new
            if planner:
                planner._cache.clear()

        # Recharger en mémoire
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

    # --- Dijkstra / chaînage forward --------------------------------
    def _dijkstra_pondere(self, depart, arrivee, max_profondeur, mode,
                          seuil_poids):
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
        res = self._dijkstra_pondere(d, a, max_profondeur, mode, seuil_poids)
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
            out.append(f"  {i}. {f.sujet} --{m}{f.relation}"
                       f"[{f.poids:.2f}]--> {f.objet}")
        out.append(f"  ⇒ poids ({mode_poids}) : "
                   f"{self.poids_chaine(chemin, mode_poids):.4f}")
        return "\n".join(out)

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

    def bench(self, n: int = 2000) -> Dict[str, float]:
        req = [("Socrate", "être_vivant"), ("tabac", "cancer_poumon")]
        self._cache.clear()
        t0 = time.perf_counter()
        for i in range(n):
            d, a = req[i % len(req)]
            self.trouver_chaine_deductive(d, a)
        dt = (time.perf_counter() - t0) * 1000 / n
        return {"requetes": float(n), "temps_moyen_ms": dt}


# ===========================================================================
# AUTO-TEST
# ===========================================================================
if __name__ == "__main__":
    import os, random

    print("=" * 76)
    print("(k) SQL PUSHDOWN vs PYTHON — même résultat ?")
    print("=" * 76)
    faits = [
        FaitRelationnel("Socrate", "est_un", "homme", poids=1.0),
        FaitRelationnel("homme", "est_un", "mammifère", poids=0.98),
        FaitRelationnel("mammifère", "est_un", "animal", poids=1.0),
        FaitRelationnel("animal", "est_un", "être_vivant", poids=1.0),
        FaitRelationnel("animal", "est", "mortel", poids=0.99),
    ]
    # --- version Python
    m_py = MoteurDeductifCausal(faits=faits, regles=[REGLE_HERITAGE])
    r_py = m_py.saturer_regles_semi_naif(max_iterations=10)
    cles_py = {f.cle() for f in m_py.faits}

    # --- version SQL
    backend = BackendSQLite(":memory:")
    for f in faits:
        backend.ajouter(f)
    m_sql = MoteurDeductifCausal(backend_sqlite=backend,
                                  regles=[REGLE_HERITAGE])
    r_sql = m_sql.saturer_regles_sql(max_iterations=10)
    cles_sql = {f.cle() for f in m_sql.faits}

    print(f"  Python : {r_py['total_derive']} dérivés en "
          f"{r_py['iterations']} itération(s)")
    print(f"  SQL    : {r_sql['total_derive']} dérivés en "
          f"{r_sql['iterations']} itération(s)")
    print(f"  Ensembles identiques ? {cles_py == cles_sql}")
    for f in sorted(m_sql.faits, key=lambda x: (x.sujet, x.objet)):
        if "heritage" in (f.explication or ""):
            print(f"    {f.sujet} {f.relation} {f.objet} [{f.poids:.4f}]")

    print()
    print("=" * 76)
    print("(m) JOIN PLANNER — ordre par sélectivité")
    print("=" * 76)
    planner = JoinPlanner(backend)
    ordre = planner.ordonner_atomes(REGLE_HERITAGE.corps)
    for i, atome in enumerate(REGLE_HERITAGE.corps):
        n = planner.estimer_cardinalite(atome)
        print(f"    atome {i} {atome}  cardinalité={n}")
    print(f"  → ordre sélectif : {ordre}")
    print(f"  → avant : {list(range(len(REGLE_HERITAGE.corps)))}")

    print()
    print("=" * 76)
    print("(n) CPT EMPIRIQUE — apprentissage depuis 20k observations")
    print("=" * 76)
    random.seed(42)
    lignes = []
    for _ in range(20000):
        z = 1 if random.random() < 0.5 else 0
        x = 1 if random.random() < (0.9 if z else 0.1) else 0
        p_y = {(1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1}[(x, z)]
        y = 1 if random.random() < p_y else 0
        lignes.append({"z": z, "x": x, "y": y})

    bn = GrapheCausal()
    bn.ajouter_arete("z", "x"); bn.ajouter_arete("z", "y")
    bn.ajouter_arete("x", "y")
    bn.apprendre_cpts_depuis_observations(lignes, lissage_laplace=1.0)
    print(f"  source_modele : {bn.source_modele}")
    print(f"  CPT X appris  :")
    for k, v in sorted(bn._cpts["x"].items()):
        print(f"    P(X=1|Z={k[0]}) ≈ {v:.3f}  (attendu : "
              f"{0.9 if k[0]==1 else 0.1:.3f})")
    print(f"  CPT Y appris  :")
    for k, v in sorted(bn._cpts["y"].items()):
        attendu = {(1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1}[k]
        print(f"    P(Y=1|X={k[0]},Z={k[1]}) ≈ {v:.3f}  "
              f"(attendu : {attendu:.3f})")

    print()
    print("=" * 76)
    print("(l) JUNCTION TREE — vs VE sur réseau confondu")
    print("=" * 76)
    bn2 = GrapheCausal()
    bn2.ajouter_arete("z", "x"); bn2.ajouter_arete("z", "y")
    bn2.ajouter_arete("x", "y")
    bn2.set_prior("z", 0.5)
    bn2.set_cpt("x", {(1,): 0.9, (0,): 0.1})
    bn2.set_cpt("y", {
        (1, 1): 0.9, (1, 0): 0.6, (0, 1): 0.3, (0, 0): 0.1,
    })

    ve_obs = bn2.inference_ve("y", {"x": 1}, do_x=None)
    ve_do = bn2.inference_ve("y", {"x": 1}, do_x="x")
    print(f"  VE : P(Y|X=1) = {ve_obs[1]:.4f}, "
          f"P(Y|do(X=1)) = {ve_do[1]:.4f}")

    jt = JunctionTree(bn2)
    print(f"  Cliques : {[sorted(c) for c in jt.cliques]}")
    print(f"  Arbre   : {jt.adj_cliques}")
    jt_obs = jt.query("y", evidence={"x": 1})
    jt_do = jt.query("y", evidence={"x": 1}, do_x="x")
    print(f"  JT : P(Y|X=1) = {jt_obs[1]:.4f}, "
          f"P(Y|do(X=1)) = {jt_do[1]:.4f}")
    print(f"  Match VE↔JT ? "
          f"{abs(ve_obs[1]-jt_obs[1]) < 1e-9 and abs(ve_do[1]-jt_do[1]) < 1e-9}")

    print()
    print("  Comparaison JT vs VE sur le biais observationnel :")
    print(f"    Δ_biais (VE) = {abs(ve_obs[1]-ve_do[1]):.4f}")
    print(f"    Δ_biais (JT) = {abs(jt_obs[1]-jt_do[1]):.4f}")

    print()
    print("=" * 76)
    print("(l-bis) JUNCTION TREE — réseau à plusieurs cliques")
    print("=" * 76)
    bn3 = GrapheCausal()
    bn3.ajouter_arete("a", "c"); bn3.ajouter_arete("b", "c")
    bn3.ajouter_arete("c", "d"); bn3.ajouter_arete("e", "d")
    bn3.ajouter_arete("d", "f")
    for n in "abcdef":
        bn3.set_prior(n, 0.5)
    jt3 = JunctionTree(bn3)
    print(f"  Cliques : {[sorted(c) for c in jt3.cliques]}")
    print(f"  Nb cliques : {len(jt3.cliques)}")
    seps = [(i, j, sorted(jt3.cliques[i] & jt3.cliques[j]))
            for i, j in jt3.messages.keys() if i < j]
    print(f"  Séparateurs : {seps}")
    p = jt3.query("f", evidence={"a": 1})
    p_ve = bn3.inference_ve("f", {"a": 1})
    print(f"  JT P(F=1|A=1) = {p[1]:.4f}")
    print(f"  VE P(F=1|A=1) = {p_ve[1]:.4f}")
    print(f"  Match : {abs(p[1]-p_ve[1]) < 1e-9}")

    print()
    print("=" * 76)
    print("BENCH")
    print("=" * 76)
    r = m_sql.bench(3000)
    print(f"  Dijkstra : {r['temps_moyen_ms']:.4f} ms/req ({r['requetes']:.0f} req)")

    backend.fermer()
    print("\n✓ v6.0 OK")
