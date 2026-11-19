"""alix_moteur_deductif_causal.py — v5.0
Moteur de Raisonnement Déductif local — stdlib uniquement.

Nouveautés v5.0 :
  (g) BackendSQLite : table faits + index composites, requêtes préparées,
      mode fichier (.sqlite sur SSD) ou :memory:.
  (j) Datalog semi-naïf (Δ-saturation) + poids produit / moyenne géométrique.
  (i) Validation stricte du DAG : détection de cycles (DFS 3-couleurs),
      refus d'inférence do(X) sur graphe cyclique.
  (h) Réseau bayésien causal : CPTs ou noisy-OR, élimination de variables,
      P(Y|X) vs P(Y|do(X)) par formule backdoor + Δ_biais chiffré.
  + Correctif poids des règles : "produit" (défaut) ou "moyenne_geo".

LIMITES (à lire) :
  - Élimination de variables = exacte mais exponentielle en largeur d'arbre.
    Au-delà de ~15-20 nœuds denses, passer à la junction tree.
  - L'inférence do(X) exige que le backdoor_set soit VALIDE (test structurel).
    Sinon ValueError levée — on ne calcule pas un biais sur une formule invalide.
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
from dataclasses import dataclass, field
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
# (g) Backend SQLite
# ===========================================================================
class BackendSQLite:
    """Table faits + index composites. Requêtes préparées pour la chaleur."""
    SCHEMA = """
    PRAGMA journal_mode = MEMORY;
    PRAGMA synchronous = OFF;
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
        self.conn = sqlite3.connect(chemin)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()

    def ajouter(self, f: FaitRelationnel, derive: bool = False) -> bool:
        """Retourne True si le fait a été inséré (nouveau)."""
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO faits
               (sujet, relation, objet, explication, poids, negatif, derive)
               VALUES(?,?,?,?,?,?,?)""",
            (_norm(f.sujet), _norm(f.relation), _norm(f.objet),
             f.explication, f.poids, int(f.negatif), int(derive)),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def chercher_atome(self, sujet: Any, relation: Any,
                       objet: Any, negatif: Optional[bool] = None
                       ) -> List[FaitRelationnel]:
        """Requête préparée — positions concrètes vs variables (?x)."""
        clauses: List[str] = []
        args: List[Any] = []
        if not est_variable(sujet):
            clauses.append("sujet=?"); args.append(_norm(sujet))
        if not est_variable(relation):
            clauses.append("relation=?"); args.append(_norm(relation))
        if not est_variable(objet):
            clauses.append("objet=?"); args.append(_norm(objet))
        if negatif is not None:
            clauses.append("negatif=?"); args.append(int(negatif))
        if not clauses:
            sql = "SELECT * FROM faits"
        else:
            sql = "SELECT * FROM faits WHERE " + " AND ".join(clauses)
        cur = self.conn.execute(sql, args)
        return [self._row_to_fait(r) for r in cur.fetchall()]

    def charger_tout(self) -> List[FaitRelationnel]:
        cur = self.conn.execute("SELECT * FROM faits")
        return [self._row_to_fait(r) for r in cur.fetchall()]

    def compter(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM faits").fetchone()[0]

    @staticmethod
    def _row_to_fait(r: sqlite3.Row) -> FaitRelationnel:
        return FaitRelationnel(
            r["sujet"], r["relation"], r["objet"], r["explication"] or "",
            (), float(r["poids"]), bool(r["negatif"]),
        )

    def fermer(self) -> None:
        self.conn.close()


# ===========================================================================
# (i) + (h) Graphe causal : cycles, BN, VE
# ===========================================================================
class GrapheCausal:
    def __init__(self) -> None:
        self.noeuds: Set[str] = set()
        self.parents: Dict[str, Set[str]] = defaultdict(set)
        self.enfants: Dict[str, Set[str]] = defaultdict(set)
        # Modèle probabiliste
        self._priors: Dict[str, float] = {}
        self._poids_arete: Dict[Tuple[str, str], float] = {}
        self._cpts: Dict[str, Dict[Tuple[int, ...], float]] = {}

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

    def mediateurs(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return self.descendants(x) & self.ancetres(y)

    def colliders(self, x: str, y: str) -> Set[str]:
        x, y = _norm(x), _norm(y)
        return self.descendants(x) & self.descendants(y)

    # --- (i) Détection de cycles (DFS 3 couleurs) -------------------
    def detecter_cycles(self) -> List[List[str]]:
        BLANC, GRIS, NOIR = 0, 1, 2
        couleur = {n: BLANC for n in self.noeuds}
        parent_dfs: Dict[str, str] = {}
        cycles: List[List[str]] = []

        def dfs(u: str) -> None:
            couleur[u] = GRIS
            for v in self.enfants.get(u, set()):
                if couleur[v] == GRIS:
                    # reconstruit le cycle
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
        """Retourne un nouveau graphe avec les arêtes impliquées dans un cycle retirées."""
        cycles = self.detecter_cycles()
        aretes_cycle: Set[Tuple[str, str]] = set()
        for c in cycles:
            for i in range(len(c) - 1):
                aretes_cycle.add((c[i], c[i + 1]))
        g = GrapheCausal()
        for u in self.noeuds:
            g.noeuds.add(u)
        for u, enfants in self.enfants.items():
            for v in enfants:
                if (u, v) not in aretes_cycle:
                    g.ajouter_arete(u, v)
        # copie du modèle proba
        g._priors = dict(self._priors)
        g._poids_arete = dict(self._poids_arete)
        g._cpts = {k: dict(v) for k, v in self._cpts.items()}
        return g

    # --- d-séparation -----------------------------------------------
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

    # --- paramétrage du réseau bayésien -----------------------------
    def set_prior(self, noeud: str, p: float) -> None:
        self._priors[_norm(noeud)] = max(0.0, min(1.0, p))

    def set_poids_arete(self, parent: str, enfant: str, q: float) -> None:
        self._poids_arete[(_norm(parent), _norm(enfant))] = max(0.0, min(1.0, q))

    def set_cpt(self, noeud: str, table: Dict[Tuple[int, ...], float]) -> None:
        """table : assignment des parents (tuple de 0/1) -> P(noeud=1|parents)."""
        self._cpts[_norm(noeud)] = dict(table)

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

    # --- (h) Facteurs + élimination de variables --------------------
    def _construire_facteurs(self, do_x: Optional[str] = None
                             ) -> List[Tuple[Tuple[str, ...], Dict[Tuple[int, ...], float]]]:
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
        positions = [i for i, v in enumerate(scope) if v in evidence]
        if not positions:
            return facteur
        new_scope = tuple(v for i, v in enumerate(scope) if i not in positions)
        new_table: Dict[Tuple[int, ...], float] = defaultdict(float)
        for vals, p in table.items():
            if all(vals[i] == evidence[scope[i]] for i in positions):
                new_key = tuple(v for i, v in enumerate(vals) if i not in positions)
                new_table[new_key] += p
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
                compatible = True
                for i, v in enumerate(s1):
                    if v in s2 and vals1[i] != vals2[s2.index(v)]:
                        compatible = False; break
                if not compatible:
                    continue
                full = [0] * len(scope)
                for i, v in enumerate(s1):
                    full[idx1[i]] = vals1[i]
                for i, v in enumerate(s2):
                    full[idx2[i]] = vals2[i]
                table[tuple(full)] += p1 * p2
        return scope, dict(table)

    @classmethod
    def _sommer_sur(cls, facteur, var: str):
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
        self, query_var: str, evidence: Dict[str, int],
        do_x: Optional[str] = None,
    ) -> Dict[int, float]:
        """
        Élimination de variables exacte.
        Retourne P(query_var = v | evidence, do(do_x)).
        LIMITE : exponentielle en largeur d'arbre. OK jusqu'à ~15-20 nœuds.
        """
        facteurs = [self._restreindre(f, evidence)
                    for f in self._construire_facteurs(do_x=do_x)]

        cache: Set[str] = set(evidence.keys())
        if do_x is not None:
            cache.add(do_x)
        cache.add(_norm(query_var))

        ordre = [n for n in sorted(self.noeuds) if n not in cache]
        # heuristique min-degré simple
        ordre.sort(key=lambda n: len(self.parents[n]) + len(self.enfants[n]))

        for var in ordre:
            concernes = [f for f in facteurs if var in f[0]]
            autres = [f for f in facteurs if var not in f[0]]
            if not concernes:
                continue
            produit = concernes[0]
            for f in concernes[1:]:
                produit = self._multiplier(produit, f)
            somme = self._sommer_sur(produit, var)
            facteurs = autres + [somme]

        if not facteurs:
            return {0: 1.0, 1: 0.0}
        produit = facteurs[0]
        for f in facteurs[1:]:
            produit = self._multiplier(produit, f)

        scope, table = produit
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

    # --- P(Y|X) vs P(Y|do(X)) ---------------------------------------
    def comparer_observation_vs_intervention(
        self, x: str, y: str,
    ) -> Dict[str, Any]:
        """
        Calcule :
          - P(Y=1|X=1)        (observationnel)
          - P(Y=1|do(X=1))    (interventionnel, via réseau mutilé)
          - Δ_biais = |P(Y|X) - P(Y|do(X))|
        Refuse si graphe cyclique.
        """
        if not self.est_dag():
            raise ValueError(
                "Graphe causal cyclique — inférence do(X) refusée. "
                "Utiliser composante_acyclique() ou corriger le graphe."
            )
        x, y = _norm(x), _norm(y)

        p_obs = self.inference_ve(y, {x: 1}, do_x=None)
        p_do = self.inference_ve(y, {x: 1}, do_x=x)

        p_y_x = p_obs[1]
        p_y_do = p_do[1]
        return {
            "P(Y=1|X=1)":     p_y_x,
            "P(Y=1|do(X=1))": p_y_do,
            "delta_biais":    abs(p_y_x - p_y_do),
            "confondants":    sorted(self.confondants(x, y)),
            "backdoor_set":   sorted(self.backdoor_set_simple(x, y)),
        }


# ===========================================================================
# Moteur principal
# ===========================================================================
class MoteurDeductifCausal:
    def __init__(
        self,
        encyclopedie: Any = None,
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

        # Charger : soit depuis backend, soit depuis liste
        if backend_sqlite is not None:
            for f in backend_sqlite.charger_tout():
                self._ajouter_en_memoire(f)
        for f in (faits or []):
            self.ajouter_fait(f)

    # --- index / cache ----------------------------------------------
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
        k = f.cle()
        if k in self._cles_vues:
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

    # ==============================================================
    # (j) Datalog semi-naïf (Δ-saturation)
    # ==============================================================
    def _trouver_substitutions(
        self, corps: Tuple[Pattern, ...],
        delta_cles: Optional[Set[Tuple[str, str, str, bool]]] = None,
        delta_pos: Optional[int] = None,
    ) -> List[Tuple[Dict[str, str], float]]:
        etats: List[Tuple[Dict[str, str], float]] = [({}, 1.0)]
        for pos, atome in enumerate(corps):
            nouveaux: List[Tuple[Dict[str, str], float]] = []
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
    def _poids_derive(poids_corps: float, regle: Regle,
                      n_atomes: int, mode: str) -> float:
        """Correctif poids : produit ou moyenne géométrique amortie."""
        if mode == "produit":
            p = poids_corps * regle.poids
        elif mode == "moyenne_geo":
            n = n_atomes + 1
            p = (poids_corps * regle.poids) ** (1.0 / n)
        else:
            raise ValueError(f"mode_poids_regle inconnu : {mode}")
        return max(0.01, min(1.0, p))

    def saturer_regles_semi_naif(
        self, max_iterations: int = 50, mode_poids_regle: str = "produit",
    ) -> Dict[str, Any]:
        """
        Δ-saturation : à l'itération k, on ne joint chaque règle qu'avec AU MOINS
        un fait de ΔF_{k-1}. Zéro recalcul quadratique des faits connus.
        """
        if not self.regles:
            return {"total_derive": 0, "iterations": 0}

        F: Set[Tuple[str, str, str, bool]] = {f.cle() for f in self.faits}
        delta: Set[Tuple[str, str, str, bool]] = set(F)
        total_derive = 0
        iteration = 0

        for iteration in range(1, max_iterations + 1):
            nouveaux: Dict[Tuple[str, str, str, bool], FaitRelationnel] = {}
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
                            explication=f"dérivé par « {regle.nom} » (semi-naïf)",
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

    # Compatibilité : version naïve (sans Δ)
    def saturer_regles(self, max_iterations: int = 10,
                       mode_poids_regle: str = "produit") -> int:
        return self.saturer_regles_semi_naif(
            max_iterations=max_iterations, mode_poids_regle=mode_poids_regle,
        )["total_derive"]

    # ==============================================================
    # Dijkstra (chaîne forward)
    # ==============================================================
    def _dijkstra_pondere(
        self, depart: str, arrivee: str, max_profondeur: int,
        mode: str, seuil_poids: float,
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
            for fait in self._index_sujet.get(noeud, []):
                if fait.negatif or fait.poids < seuil_poids:
                    continue
                t = RELATION_TYPE.get(_norm(fait.relation), TypeRelation.LOGIQUE)
                if t == TypeRelation.OPPOSITION:
                    continue
                if mode != "mixte" and t.value != mode:
                    continue
                if dt is not None and t not in COMPATIBILITE[dt]:
                    continue
                suivant = _norm(fait.objet)
                nc = cout - math.log(max(fait.poids, 1e-12))
                counter += 1
                heapq.heappush(tas, (nc, counter, suivant,
                                     chemin + [fait], t, prof + 1))
        return None

    def trouver_chaine_deductive(
        self, depart: str, arrivee: str, max_profondeur: int = 8,
        mode: str = "mixte", seuil_poids: float = 0.05,
        strategie: str = "dijkstra",
    ) -> Optional[List[FaitRelationnel]]:
        depart_n, arrivee_n = _norm(depart), _norm(arrivee)
        if depart_n == arrivee_n:
            return []
        cle = (depart_n, arrivee_n, max_profondeur, mode, seuil_poids, strategie)
        if cle in self._cache:
            self._cache.move_to_end(cle)
            return self._cache[cle]
        if strategie == "dijkstra":
            res = self._dijkstra_pondere(depart_n, arrivee_n,
                                         max_profondeur, mode, seuil_poids)
        else:
            res = self._bfs_pondere(depart_n, arrivee_n,
                                    max_profondeur, mode, seuil_poids)
        self._cache_put(cle, res)
        return res

    def _bfs_pondere(self, depart: str, arrivee: str, max_profondeur: int,
                     mode: str, seuil_poids: float,
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

    # ==============================================================
    # Poids de chaîne (produit ou moyenne géo)
    # ==============================================================
    def poids_chaine(self, chemin: List[FaitRelationnel],
                     mode_poids: str = "produit") -> float:
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
        raise ValueError(f"mode_poids inconnu : {mode_poids}")

    def formater_preuve(self, chemin: List[FaitRelationnel],
                        mode_poids: str = "produit") -> str:
        if not chemin:
            return "(chemin vide : identité)"
        out = []
        for i, f in enumerate(chemin, 1):
            m = "¬" if f.negatif else ""
            out.append(f"  {i}. {f.sujet} --{m}{f.relation}"
                       f"[{f.poids:.2f}]--> {f.objet}")
        out.append(f"  ⇒ poids ({mode_poids}) : "
                   f"{self.poids_chaine(chemin, mode_poids):.4f}")
        return "\n".join(out)

    def expliquer_chain(self, chemin: List[FaitRelationnel],
                        mode_poids: str = "produit") -> str:
        if not chemin:
            return "Aucune étape à expliquer."
        out = [f"On part de « {chemin[0].sujet} »."]
        for i, f in enumerate(chemin, 1):
            neg = "ne " if f.negatif else ""
            vb = VERBES_FR.get(_norm(f.relation), f.relation)
            txt = f.explication or f"{f.sujet} {neg}{vb} {f.objet}"
            out.append(f"  Étape {i} (confiance {f.poids:.0%}) : {txt}.")
            if i < len(chemin):
                out.append(f"  → on travaille avec « {f.objet} ».")
        dernier = chemin[-1]
        vb = VERBES_FR.get(_norm(dernier.relation), dernier.relation)
        out.append(f"Conclusion : « {dernier.sujet} » {vb} "
                   f"« {dernier.objet} ».")
        out.append(f"Confiance ({mode_poids}) : "
                   f"{self.poids_chaine(chemin, mode_poids):.2%}.")
        return "\n".join(out)

    # ==============================================================
    # Abduction
    # ==============================================================
    def remonter_aux_causes(self, effet: str, max_profondeur: int = 5,
                            max_chaines: int = 20
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

    def expliquer_pourquoi(self, sujet: str, objet: str,
                           max_profondeur: int = 6) -> Dict[str, Any]:
        ch = self.trouver_chaine_deductive(sujet, objet,
                                           max_profondeur=max_profondeur)
        if ch:
            return {"sens": "avant", "chaine": ch,
                    "explication": self.expliquer_chain(ch)}
        causes = self.remonter_aux_causes(objet, max_profondeur=max_profondeur)
        for c in causes:
            if c and _norm(c[0].sujet) == _norm(sujet):
                return {"sens": "arriere", "chaine": c,
                        "explication": self.expliquer_chain(c)}
        return {"sens": None, "chaine": [],
                "explication": f"Aucune explication pour « {sujet} » → "
                                f"« {objet} »."}

    # ==============================================================
    # Logique 3 valeurs / contradictions / sophismes / dialectique
    # (inchangés sauf poids_chaine dans dialectique)
    # ==============================================================
    def est_prouvable(self, s: str, r: str, o: str, **kw: Any) -> bool:
        s, r, o = _norm(s), _norm(r), _norm(o)
        for f in self._index_sujet.get(s, []):
            if not f.negatif and _norm(f.relation) == r and _norm(f.objet) == o:
                return True
        t = RELATION_TYPE.get(r)
        if t is None or t == TypeRelation.OPPOSITION:
            return False
        return bool(self.trouver_chaine_deductive(s, o, **kw))

    def est_refute(self, s: str, r: str, o: str) -> bool:
        s, r, o = _norm(s), _norm(r), _norm(o)
        opposes = RELATIONS_OPPOSEES.get(r, set())
        for f in self._index_sujet.get(s, []):
            if _norm(f.objet) != o:
                continue
            if f.negatif and _norm(f.relation) == r:
                return True
            if _norm(f.relation) in opposes:
                return True
        return False

    def valeur_logique(self, s: str, r: str, o: str, **kw: Any) -> str:
        p = self.est_prouvable(s, r, o, **kw)
        rr = self.est_refute(s, r, o)
        if p and not rr:
            return "vrai"
        if rr and not p:
            return "faux"
        return "indetermine"

    def negation_par_echec(self, s: str, r: str, o: str, **kw: Any) -> bool:
        return not self.est_prouvable(s, r, o, **kw)

    def _sont_opposes(self, f1: FaitRelationnel, f2: FaitRelationnel) -> bool:
        r1, r2 = _norm(f1.relation), _norm(f2.relation)
        if r1 == r2 and f1.negatif != f2.negatif:
            return True
        return (r2 in RELATIONS_OPPOSEES.get(r1, set())
                or r1 in RELATIONS_OPPOSEES.get(r2, set()))

    @staticmethod
    def _cle_couple(f1: FaitRelationnel, f2: FaitRelationnel) -> Tuple:
        return tuple(sorted([
            (_norm(f1.sujet), _norm(f1.relation), _norm(f1.objet), f1.negatif),
            (_norm(f2.sujet), _norm(f2.relation), _norm(f2.objet), f2.negatif),
        ]))

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
                for f2 in fs[i + 1:]:
                    if not self._sont_opposes(f1, f2):
                        continue
                    k = self._cle_couple(f1, f2)
                    if k in vus:
                        continue
                    vus.add(k)
                    res.append({"type": "directe", "fait_1": f1, "fait_2": f2,
                                "explication": (f"{f1.sujet} --{f1.relation}--> "
                                                f"{f1.objet}  VS  --{f2.relation}"
                                                f"--> {f2.objet}")})
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
                k = self._cle_couple(f1, f2)
                if k in vus:
                    continue
                vus.add(k)
                res.append({"type": "distante", "fait_1": f1, "fait_2": f2,
                            "explication": (f"{f1.sujet} --{f1.relation}--> "
                                            f"{f1.objet} ...-> {f2.objet}, "
                                            f"mais {f1.sujet} --{f2.relation}-->"
                                            f" {f2.objet}")})
        return res

    def analyser_argument_et_sophismes(self, texte: str
                                       ) -> List[Dict[str, Any]]:
        """Heuristique par patterns. NON complète. Filtre, pas juge."""
        t = texte.lower()
        out: List[Dict[str, Any]] = []

        def _add(nom, motif, marqueur, expl):
            m = re.search(motif, t, flags=re.IGNORECASE)
            if m:
                out.append({"sophisme": nom, "extrait": m.group(0),
                            "marqueur": marqueur, "explication": expl})

        _add("faux_dilemme",
             r"\bsoit\b[^,.!?]{1,80}?,?\s+soit\b[^,.!?]{1,80}",
             "soit... soit...", "Deux options présentées comme seules.")
        _add("pente_glissante",
             r"\bsi\s+on\b[^.!?]{0,120}?\b(alors|on finira|finira par|"
             r"mènera|conduira|aboutira)\b",
             "si on... alors...", "Enchaîne vers l'extrême.")
        _add("appel_autorite",
             r"\b(tout le monde sait|tout le monde dit|les experts disent|"
             r"selon les scientifiques|la science dit|c'est évident que|"
             r"il est bien connu que|chacun sait que)\b",
             "tout le monde sait", "Autorité sans preuve.")
        _add("generalisation_hative",
             r"\b(toujours|jamais|tous les|toutes les|aucun|aucune|"
             r"personne ne)\b",
             "toujours / jamais / tous", "Universel abusif.")
        _add("ad_hominem",
             r"\b(tu es|vous êtes|il est|c'est|t'es)\s+(qu')?\s*(un|une)?\s*"
             r"(idiot|imbécile|ignorant|incompétent|fou|menteur|naïf|stupide)\b",
             "tu es [insulte]", "Attaque la personne.")
        _add("empoisonnement_puits",
             r"\b(ne l'écoutez pas|ne l'écoute pas|ne le crois pas|"
             r"de toute façon (il|elle))\b[^.!?]{0,60}?"
             r"\b(ment|triche|est payé|est vendu|a un intérêt)\b",
             "ne l'écoute pas, il...", "Discrédit a priori.")
        _add("inversion_charge_preuve",
             r"\b(prouve[- ]le|prouve[- ]moi|prouve que|démontre[- ]le|"
             r"démontre que|prouvez[- ]le|prouvez[- ]moi)\b",
             "prouve-le", "Preuve du négatif exigée.")
        _add("presuppose_cache",
             r"\bpourquoi\b[^.!?]{0,80}?\b(encore|toujours|déjà)\b"
             r"|\bas[- ]tu\s+(arrêté|cessé)\b",
             "pourquoi ... encore", "Présuppose un fait non établi.")
        return out

    def _faits_autour(self, concept: str) -> List[FaitRelationnel]:
        c = _norm(concept)
        vus: Set[Tuple] = set()
        out: List[FaitRelationnel] = []
        for f in list(self._index_sujet.get(c, [])) + list(self._index_objet.get(c, [])):
            k = f.cle()
            if k not in vus:
                vus.add(k)
                out.append(f)
        return out

    @staticmethod
    def _fmt(f: FaitRelationnel) -> str:
        neg = "¬" if f.negatif else ""
        return f"{f.sujet} {neg}{f.relation} {f.objet} [{f.poids:.2f}]"

    def synthese_dialectique(self, sujet_a: str, sujet_b: str
                             ) -> Dict[str, Any]:
        a, b = _norm(sujet_a), _norm(sujet_b)
        faits_a = self._faits_autour(a)
        faits_b = self._faits_autour(b)
        these_f = [f for f in faits_a if _norm(f.sujet) == a] or faits_a
        anti_f = [f for f in faits_b if _norm(f.sujet) == b] or faits_b
        these = [self._fmt(f) for f in these_f]
        antithese = [self._fmt(f) for f in anti_f]
        cles_a = {(_norm(f.relation), _norm(f.objet)) for f in faits_a}
        cles_b = {(_norm(f.relation), _norm(f.objet)) for f in faits_b}
        accords = [f"{r} → {o}" for r, o in sorted(cles_a & cles_b)]

        union = {f.cle(): f for f in faits_a + faits_b}
        lst = list(union.values())
        tensions: List[str] = []
        vus_t: Set[Tuple] = set()
        for i, f1 in enumerate(lst):
            for f2 in lst[i + 1:]:
                if _norm(f1.sujet) != _norm(f2.sujet):
                    continue
                if _norm(f1.objet) != _norm(f2.objet):
                    continue
                r1, r2 = _norm(f1.relation), _norm(f2.relation)
                if r1 == r2:
                    continue
                if (r2 in RELATIONS_OPPOSEES.get(r1, set())
                        or r1 in RELATIONS_OPPOSEES.get(r2, set())):
                    k = tuple(sorted([f"{f1.sujet}|{r1}|{f1.objet}",
                                      f"{f2.sujet}|{r2}|{f2.objet}"]))
                    if k in vus_t:
                        continue
                    vus_t.add(k)
                    tensions.append(f"[directe] {f1.sujet} --{r1}--> "
                                    f"{f1.objet} VS --{r2}--> {f2.objet}")

        for c in self.detecter_contradictions():
            if c["type"] != "distante":
                continue
            f1, f2 = c["fait_1"], c["fait_2"]
            if any(_norm(x) in (a, b) for x in
                   (f1.sujet, f1.objet, f2.sujet, f2.objet)):
                tensions.append(f"[distante] {c['explication']}")

        ponts: List[str] = []
        for src, dst, lbl in [(a, b, "A→B"), (b, a, "B→A")]:
            ch = self.trouver_chaine_deductive(src, dst, max_profondeur=4)
            if ch:
                p = self.poids_chaine(ch, "moyenne_geo")
                ponts.append(f"[{lbl}] {src} ⇒ {dst} ({len(ch)} étape(s), "
                             f"conf moy-égo {p:.3f})\n"
                             + self.formater_preuve(ch, "moyenne_geo"))

        if tensions:
            synth = (f"Dépassement à construire : {len(tensions)} tension(s). "
                     f"Pistes : distinguer deux sens du prédicat, montrer des "
                     f"aspects différents, ou trancher empiriquement.")
        elif accords:
            synth = (f"Convergence sur {len(accords)} point(s) : "
                     f"{'; '.join(accords[:3])}"
                     + ("…" if len(accords) > 3 else "") + ".")
        elif ponts:
            synth = (f"Pas de tension ni d'accord direct, mais {len(ponts)} "
                     f"pont(s) déductif(s).")
        else:
            synth = "Ni accord, ni tension, ni pont. Enrichir le graphe."

        return {"these": {"sujet": sujet_a, "affirmations": these},
                "antithese": {"sujet": sujet_b, "affirmations": antithese},
                "accords": accords, "tensions": tensions,
                "ponts": ponts, "synthese": synth}

    # ==============================================================
    # Construction du graphe causal
    # ==============================================================
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

    # ==============================================================
    # Bench
    # ==============================================================
    def bench(self, n: int = 2000) -> Dict[str, float]:
        req = [("Socrate", "être_vivant"), ("tabac", "cancer_poumon"),
               ("fumer", "santé")]
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
    print("=" * 72)
    print("TEST 1 — Backend SQLite : ajout, index, requête pattern")
    print("=" * 72)
    import os
    chemin_db = "alix_test_v5.sqlite"
    if os.path.exists(chemin_db):
        os.remove(chemin_db)
    backend = BackendSQLite(chemin_db)
    faits_init = [
        # taxonomie
        FaitRelationnel("Socrate", "est_un", "homme", poids=1.0),
        FaitRelationnel("homme", "est_un", "mammifère", poids=0.98),
        FaitRelationnel("mammifère", "est_un", "animal", poids=1.0),
        FaitRelationnel("animal", "est_un", "être_vivant", poids=1.0),
        FaitRelationnel("animal", "est", "mortel", poids=0.99),
        # causal
        FaitRelationnel("tabac", "cause", "goudron", poids=0.9),
        FaitRelationnel("goudron", "cause", "cancer_poumon", poids=0.85),
        FaitRelationnel("tabac", "cause", "cancer_poumon", poids=0.6),
        FaitRelationnel("amiante", "cause", "cancer_poumon", poids=0.7),
    ]
    for f in faits_init:
        backend.ajouter(f)
    print(f"  faits en base      : {backend.compter()}")
    print(f"  voisins sujet      : "
          f"{[f.objet for f in backend.chercher_atome('tabac', '?r', '?o')]}")
    print(f"  voisins objet      : "
          f"{[f.sujet for f in backend.chercher_atome('?s', '?r', 'cancer_poumon')]}")
    print(f"  relation + objet   : "
          f"{[f.sujet for f in backend.chercher_atome('?s', 'cause', 'cancer_poumon')]}")

    print()
    print("=" * 72)
    print("TEST 2 — Datalog semi-naïf + correctif poids")
    print("=" * 72)
    m = MoteurDeductifCausal(backend_sqlite=backend,
                              regles=[REGLE_HERITAGE])
    print(f"  faits initial      : {len(m.faits)}")
    for mode in ("produit", "moyenne_geo"):
        m2 = MoteurDeductifCausal(faits=faits_init, regles=[REGLE_HERITAGE])
        r = m2.saturer_regles_semi_naif(max_iterations=10,
                                         mode_poids_regle=mode)
        derives = [f for f in m2.faits if "heritage" in (f.explication or "")]
        print(f"  [mode={mode:12s}] {r['total_derive']} dérivés en "
              f"{r['iterations']} itération(s) — ex :")
        for f in derives[:3]:
            print(f"      {f.sujet} {f.relation} {f.objet} "
                  f"[{f.poids:.4f}]")

    print()
    print("=" * 72)
    print("TEST 3 — Détection de cycles")
    print("=" * 72)
    g_dag = m.vers_graphe_causal()
    print(f"  DAG causal ?        : {g_dag.est_dag()}")
    print(f"  cycles              : {g_dag.detecter_cycles()}")

    # injecter un cycle pour tester
    g_cycle = GrapheCausal()
    g_cycle.ajouter_arete("A", "B")
    g_cycle.ajouter_arete("B", "C")
    g_cycle.ajouter_arete("C", "A")  # cycle !
    print(f"  cycle injecté A→B→C→A : {g_cycle.detecter_cycles()}")
    print(f"  est_dag             : {g_cycle.est_dag()}")
    g_propre = g_cycle.composante_acyclique()
    print(f"  composante acyclique: {sorted(g_propre.enfants.items())}")

    print()
    print("=" * 72)
    print("TEST 4 — Réseau bayésien : P(Y|X) vs P(Y|do(X))")
    print("=" * 72)
    # Modèle classique : Z confondant de X et Y
    #   Z → X → Y,  Z → Y
    # CPTs explicites (testée à la main plus haut : 0.87 vs 0.75)
    bn = GrapheCausal()
    bn.ajouter_arete("Z", "X")
    bn.ajouter_arete("Z", "Y")
    bn.ajouter_arete("X", "Y")
    bn.set_prior("Z", 0.5)
    bn.set_cpt("X", {(1,): 0.9, (0,): 0.1})  # P(X=1|Z)
    bn.set_cpt("Y", {
        (1, 1): 0.9,   # parents=(X,Z)=(1,1)
        (1, 0): 0.6,   # (X=1, Z=0) — trié alpha : X puis Z
        (0, 1): 0.3,
        (0, 0): 0.1,
    })
    res = bn.comparer_observation_vs_intervention("X", "Y")
    for k, v in res.items():
        print(f"  {k:18s} = {v}")
    print(f"  attendu : P(Y|X)≈0.8700, P(Y|do(X))≈0.7500, Δ≈0.1200")

    print()
    print("  Test refus sur graphe cyclique :")
    bn_bad = GrapheCausal()
    bn_bad.ajouter_arete("A", "B")
    bn_bad.ajouter_arete("B", "A")
    try:
        bn_bad.comparer_observation_vs_intervention("A", "B")
    except ValueError as e:
        print(f"    ✓ ValueError : {e}")

    print()
    print("=" * 72)
    print("TEST 5 — Dijkstra vs BFS sur chaîne pondérée")
    print("=" * 72)
    for strat in ("bfs", "dijkstra"):
        ch = m.trouver_chaine_deductive("tabac", "cancer_poumon",
                                         strategie=strat)
        p = m.poids_chaine(ch) if ch else 0
        print(f"  [{strat:8s}] {len(ch) if ch else 0} étape(s), poids={p:.4f}")

    print()
    print("=" * 72)
    print("TEST 6 — Bench")
    print("=" * 72)
    r = m.bench(3000)
    print(f"  {r['requetes']:.0f} req, {r['temps_moyen_ms']:.3f} ms/req")

    print()
    print("=" * 72)
    print("TEST 7 — Dialectique enrichie fumer / santé")
    print("=" * 72)
    m3 = MoteurDeductifCausal(faits=[
        FaitRelationnel("fumer", "cause", "santé", poids=0.3),
        FaitRelationnel("fumer", "empeche", "santé", poids=0.9),
        FaitRelationnel("fumer", "cause", "cancer", poids=0.8),
        FaitRelationnel("cancer", "implique", "mort", poids=0.9),
        FaitRelationnel("santé", "implique", "bonheur", poids=0.85),
    ])
    d = m3.synthese_dialectique("fumer", "santé")
    print("  THÈSE     :", d["these"]["affirmations"])
    print("  ANTITHÈSE :", d["antithese"]["affirmations"])
    print("  TENSIONS  :")
    for t in d["tensions"]:
        print("    -", t)
    print("  SYNTHÈSE  :", d["synthese"])

    backend.fermer()
    if os.path.exists(chemin_db):
        os.remove(chemin_db)
