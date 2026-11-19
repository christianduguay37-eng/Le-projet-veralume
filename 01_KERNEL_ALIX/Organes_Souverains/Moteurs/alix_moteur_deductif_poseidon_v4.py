"""alix_moteur_deductif_causal.py — v4.0
Moteur de Raisonnement Déductif local — stdlib uniquement.

Nouveautés v4.0 :
  (1) synthese_dialectique enrichie : _index_sujet + _index_objet,
      tensions directes + multi-sauts, ponts déductifs A↔B.
  (2) Chaînage arrière / abduction : remonter_aux_causes(effet),
      expliquer_pourquoi(sujet, objet).
  (3) Dijkstra (heapq) sur -log(poids) : chaîne de poids PRODUIT maximal.
  (4) Clauses de Horn + unification (?x, ?y) + saturation à point fixe
      + héritage automatique de propriétés le long de est_un.
"""
from __future__ import annotations

import heapq
import math
import re
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

RELATIONS_CAUSALES: Set[str] = {
    r for r, t in RELATION_TYPE.items() if t == TypeRelation.CAUSAL
}

VERBES_FR: Dict[str, str] = {
    "est_un": "est un", "est_une": "est une", "est": "est",
    "cause": "cause", "permet": "permet", "entraine": "entraîne",
    "conduit_a": "conduit à", "mene_a": "mène à", "implique": "implique",
    "affirme": "affirme", "empeche": "empêche", "interdit": "interdit",
    "nie": "nie", "contredit": "contredit",
}


# ===========================================================================
# Fait
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


# ===========================================================================
# Unification + Clause de Horn
# ===========================================================================
Pattern = Tuple[str, str, str]


def _subst_appliquer(pattern: Pattern, subst: Dict[str, str]) -> Pattern:
    return tuple(subst.get(t, t) if est_variable(t) else t for t in pattern)  # type: ignore


def _unifier(pattern: Pattern, triplet: Pattern,
             subst: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Unifie `pattern` avec `triplet` sous `subst`. Retourne subst étendue ou None."""
    new_subst = dict(subst)
    for p, t in zip(pattern, triplet):
        if est_variable(p):
            if p in new_subst:
                if _norm(new_subst[p]) != _norm(t):
                    return None
            else:
                new_subst[p] = t
        else:
            if _norm(p) != _norm(t):
                return None
    return new_subst


@dataclass(frozen=True)
class Regle:
    """Clause de Horn : tete :- corps[0], corps[1], ..."""
    tete: Pattern
    corps: Tuple[Pattern, ...]
    nom: str = "regle"


REGLE_HERITAGE = Regle(
    tete=("?x", "est", "?p"),
    corps=(("?x", "est_un", "?z"), ("?z", "est", "?p")),
    nom="heritage_propriete",
)


# ===========================================================================
# Graphe causal (structurel)
# ===========================================================================
class GrapheCausal:
    def __init__(self) -> None:
        self.noeuds: Set[str] = set()
        self.parents: Dict[str, Set[str]] = defaultdict(set)
        self.enfants: Dict[str, Set[str]] = defaultdict(set)

    def ajouter_arete(self, source: str, cible: str) -> None:
        s, c = _norm(source), _norm(cible)
        if s == c:
            return
        self.noeuds.add(s)
        self.noeuds.add(c)
        self.enfants[s].add(c)
        self.parents[c].add(s)

    def ancetres(self, x: str) -> Set[str]:
        vus: Set[str] = set()
        queue = deque(self.parents[_norm(x)])
        while queue:
            p = queue.popleft()
            if p in vus:
                continue
            vus.add(p)
            queue.extend(self.parents[p])
        return vus

    def descendants(self, x: str) -> Set[str]:
        vus: Set[str] = set()
        queue = deque(self.enfants[_norm(x)])
        while queue:
            c = queue.popleft()
            if c in vus:
                continue
            vus.add(c)
            queue.extend(self.enfants[c])
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

    def d_separes(self, x_set: Set[str], y_set: Set[str], z_set: Set[str],
                  ignorer_sortants_de: Optional[Set[str]] = None) -> bool:
        ignorer = {_norm(n) for n in (ignorer_sortants_de or set())}
        xs = {_norm(n) for n in x_set}
        ys = {_norm(n) for n in y_set}
        zs = {_norm(n) for n in z_set}

        visit: Set[Tuple[str, str]] = set()
        schedule: deque = deque()
        for x in xs:
            schedule.append((x, "up"))
            schedule.append((x, "down"))

        while schedule:
            v, d = schedule.popleft()
            if (v, d) in visit:
                continue
            visit.add((v, d))
            if d == "up":
                if v not in zs:
                    for p in self.parents[v]:
                        schedule.append((p, "up"))
                    if v not in ignorer:
                        for c in self.enfants[v]:
                            schedule.append((c, "down"))
            else:
                for p in self.parents[v]:
                    if p not in ignorer:
                        schedule.append((p, "up"))
                if v not in zs:
                    for c in self.enfants[v]:
                        schedule.append((c, "down"))

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

    def comparer_observation_vs_intervention(self, x: str, y: str) -> Dict[str, Any]:
        x, y = _norm(x), _norm(y)
        conf = self.confondants(x, y)
        if not conf:
            return {"different": False,
                    "raison": "aucun confondant — observation ≈ intervention",
                    "backdoor_set": []}
        bd = self.backdoor_set_simple(x, y)
        return {
            "different": True,
            "raison": f"{len(conf)} confondant(s) : {sorted(conf)}",
            "confondants": sorted(conf),
            "backdoor_set": sorted(bd),
            "backdoor_valide": self.backdoor_valide(x, y, bd),
        }


# ===========================================================================
# Moteur principal
# ===========================================================================
class MoteurDeductifCausal:
    def __init__(self, encyclopedie: Any = None,
                 faits: Optional[List[FaitRelationnel]] = None,
                 regles: Optional[List[Regle]] = None,
                 cache_taille: int = 512) -> None:
        self.faits: List[FaitRelationnel] = list(faits or [])
        self.regles: List[Regle] = list(regles or [])
        self.encyclopedie = encyclopedie
        self._cache_taille = cache_taille
        self._cache: "OrderedDict[Tuple, Any]" = OrderedDict()
        self._index_sujet: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._index_objet: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._index_relation: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._graphe_causal: Optional[GrapheCausal] = None
        self._reindexer()

    # --- index ----------------------------------------------------
    def _reindexer(self) -> None:
        self._index_sujet.clear()
        self._index_objet.clear()
        self._index_relation.clear()
        for f in self.faits:
            self._indexer_un(f)
        self._cache.clear()
        self._graphe_causal = None

    def _indexer_un(self, f: FaitRelationnel) -> None:
        self._index_sujet[_norm(f.sujet)].append(f)
        self._index_objet[_norm(f.objet)].append(f)
        self._index_relation[_norm(f.relation)].append(f)
        self._cache.clear()
        self._graphe_causal = None

    def ajouter_fait(self, fait: FaitRelationnel) -> None:
        self.faits.append(fait)
        self._indexer_un(fait)

    def ajouter_regle(self, regle: Regle) -> None:
        self.regles.append(regle)

    def _cache_put(self, cle: Tuple, valeur: Any) -> None:
        self._cache[cle] = valeur
        self._cache.move_to_end(cle)
        if len(self._cache) > self._cache_taille:
            self._cache.popitem(last=False)

    def _fait_existe(self, fait: FaitRelationnel) -> bool:
        s = _norm(fait.sujet)
        for f in self._index_sujet.get(s, []):
            if (_norm(f.relation) == _norm(fait.relation)
                    and _norm(f.objet) == _norm(fait.objet)
                    and f.negatif == fait.negatif):
                return True
        return False

    # ==============================================================
    # (4) Moteur Horn — chaînage avant à point fixe
    # ==============================================================
    def _faits_candidats(self, atome: Pattern) -> List[FaitRelationnel]:
        s, r, o = atome
        if not est_variable(s):
            return self._index_sujet.get(_norm(s), [])
        if not est_variable(o):
            return self._index_objet.get(_norm(o), [])
        if not est_variable(r):
            return self._index_relation.get(_norm(r), [])
        return self.faits

    def _trouver_substitutions(
        self, corps: Tuple[Pattern, ...]
    ) -> List[Tuple[Dict[str, str], float]]:
        """Jointure : toutes les substitutions satisfaisant le corps, avec poids=min."""
        etats: List[Tuple[Dict[str, str], float]] = [({}, 1.0)]
        for atome in corps:
            nouveaux: List[Tuple[Dict[str, str], float]] = []
            for subst, poids in etats:
                atome_res = _subst_appliquer(atome, subst)
                for fait in self._faits_candidats(atome_res):
                    if fait.negatif:
                        continue
                    s2 = _unifier(atome_res,
                                  (fait.sujet, fait.relation, fait.objet), subst)
                    if s2 is not None:
                        nouveaux.append((s2, min(poids, fait.poids)))
            etats = nouveaux
            if not etats:
                return []
        return etats

    def saturer_regles(self, max_iterations: int = 10) -> int:
        """Applique les règles jusqu'à point fixe. Retourne le nb de faits dérivés."""
        total = 0
        for _ in range(max_iterations):
            nouveaux: List[FaitRelationnel] = []
            for regle in self.regles:
                for subst, poids in self._trouver_substitutions(regle.corps):
                    tete_res = _subst_appliquer(regle.tete, subst)
                    s, r, o = tete_res
                    f = FaitRelationnel(
                        s, r, o,
                        explication=f"dérivé par règle « {regle.nom} »",
                        poids=max(0.05, poids),
                    )
                    if not self._fait_existe(f):
                        nouveaux.append(f)
            if not nouveaux:
                break
            for f in nouveaux:
                self.ajouter_fait(f)
            total += len(nouveaux)
        return total

    # ==============================================================
    # (3) Dijkstra sur -log(poids) — chaîne de produit maximal
    # ==============================================================
    def _dijkstra_pondere(
        self, depart: str, arrivee: str, max_profondeur: int,
        mode: str, seuil_poids: float,
    ) -> Optional[List[FaitRelationnel]]:
        counter = 0
        # (cout, counter, noeud, chemin, dernier_type, profondeur)
        tas: List[Tuple[float, int, str, List[FaitRelationnel],
                        Optional[TypeRelation], int]] = [
            (0.0, counter, depart, [], None, 0)
        ]
        vus: Dict[Tuple[str, Optional[TypeRelation]], float] = {}

        while tas:
            cout, _, noeud, chemin, dernier_type, profondeur = heapq.heappop(tas)
            cle_etat = (noeud, dernier_type)
            if cle_etat in vus and vus[cle_etat] <= cout:
                continue
            vus[cle_etat] = cout

            if noeud == arrivee:
                return chemin

            if profondeur >= max_profondeur:
                continue

            for fait in self._index_sujet.get(noeud, []):
                if fait.negatif or fait.poids < seuil_poids:
                    continue
                t = RELATION_TYPE.get(_norm(fait.relation), TypeRelation.LOGIQUE)
                if t == TypeRelation.OPPOSITION:
                    continue
                if mode != "mixte" and t.value != mode:
                    continue
                if dernier_type is not None and t not in COMPATIBILITE[dernier_type]:
                    continue
                suivant = _norm(fait.objet)
                nouveau_cout = cout - math.log(max(fait.poids, 1e-12))
                counter += 1
                heapq.heappush(tas, (
                    nouveau_cout, counter, suivant,
                    chemin + [fait], t, profondeur + 1,
                ))
        return None

    # ==============================================================
    # (1) Chaînage déductif N-étapes
    # ==============================================================
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
        elif strategie == "bfs":
            res = self._bfs_pondere(depart_n, arrivee_n,
                                    max_profondeur, mode, seuil_poids)
        else:
            raise ValueError(f"strategie inconnue : {strategie}")
        self._cache_put(cle, res)
        return res

    def _bfs_pondere(
        self, depart: str, arrivee: str, max_profondeur: int,
        mode: str, seuil_poids: float,
    ) -> Optional[List[FaitRelationnel]]:
        """Ancien algorithme v3.0 — conservé pour compatibilité."""
        meilleur: Optional[List[FaitRelationnel]] = None
        meilleur_poids = -1.0
        queue: deque = deque([(depart, [], 1.0, None)])
        vus: Dict[Tuple[str, Optional[TypeRelation]], float] = {(depart, None): 1.0}
        while queue:
            noeud, chemin, poids_cumul, dernier_type = queue.popleft()
            if len(chemin) >= max_profondeur:
                continue
            for fait in self._index_sujet.get(noeud, []):
                if fait.negatif or fait.poids < seuil_poids:
                    continue
                t = RELATION_TYPE.get(_norm(fait.relation), TypeRelation.LOGIQUE)
                if t == TypeRelation.OPPOSITION:
                    continue
                if mode != "mixte" and t.value != mode:
                    continue
                if dernier_type is not None and t not in COMPATIBILITE[dernier_type]:
                    continue
                suivant = _norm(fait.objet)
                nouveau_poids = poids_cumul * fait.poids
                if nouveau_poids < seuil_poids:
                    continue
                nouveau_chemin = chemin + [fait]
                if suivant == arrivee:
                    if nouveau_poids > meilleur_poids:
                        meilleur, meilleur_poids = nouveau_chemin, nouveau_poids
                    continue
                cle = (suivant, t)
                if vus.get(cle, -1.0) >= nouveau_poids:
                    continue
                vus[cle] = nouveau_poids
                queue.append((suivant, nouveau_chemin, nouveau_poids, t))
        return meilleur

    # ==============================================================
    # (2) Chaînage arrière / abduction
    # ==============================================================
    def remonter_aux_causes(
        self, effet: str, max_profondeur: int = 5, max_chaines: int = 20,
    ) -> List[List[FaitRelationnel]]:
        """
        Remonte le graphe CAUSAL par _index_objet.
        Retourne des chaînes forward [cause_racine, ..., cause_directe] → effet.
        """
        effet_n = _norm(effet)
        resultats: List[List[FaitRelationnel]] = []

        def _explorer(noeud: str, chaine_remontante: List[FaitRelationnel]) -> None:
            if len(resultats) >= max_chaines:
                return
            if len(chaine_remontante) >= max_profondeur:
                return
            for f in self._index_objet.get(noeud, []):
                if f.negatif:
                    continue
                if RELATION_TYPE.get(_norm(f.relation)) != TypeRelation.CAUSAL:
                    continue
                nouvelle = chaine_remontante + [f]
                # cycle ?
                if any(_norm(g.sujet) == _norm(f.sujet) for g in nouvelle[:-1]):
                    continue
                resultats.append(list(reversed(nouvelle)))
                _explorer(_norm(f.sujet), nouvelle)

        _explorer(effet_n, [])
        resultats.sort(key=len, reverse=True)
        return resultats[:max_chaines]

    def expliquer_pourquoi(
        self, sujet: str, objet: str, max_profondeur: int = 6,
    ) -> Dict[str, Any]:
        """Explication déductive : chaîne forward ou remontée causale."""
        chaine_av = self.trouver_chaine_deductive(
            sujet, objet, max_profondeur=max_profondeur, strategie="dijkstra"
        )
        if chaine_av:
            return {"sens": "avant", "chaine": chaine_av,
                    "explication": self.expliquer_chain(chaine_av)}
        causes = self.remonter_aux_causes(objet, max_profondeur=max_profondeur)
        for ch in causes:
            if ch and _norm(ch[0].sujet) == _norm(sujet):
                return {"sens": "arriere", "chaine": ch,
                        "explication": self.expliquer_chain(ch)}
        return {"sens": None, "chaine": [],
                "explication": f"Aucune explication trouvée entre "
                                f"« {sujet} » et « {objet} »."}

    # ==============================================================
    # Poids / formatage
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
        lignes = []
        for i, f in enumerate(chemin, 1):
            marque = "¬" if f.negatif else ""
            lignes.append(f"  {i}. {f.sujet} --{marque}{f.relation}"
                          f"[{f.poids:.2f}]--> {f.objet}")
        lignes.append(f"  ⇒ poids ({mode_poids}) : "
                      f"{self.poids_chaine(chemin, mode_poids):.4f}")
        return "\n".join(lignes)

    def expliquer_chain(self, chemin: List[FaitRelationnel],
                        mode_poids: str = "produit") -> str:
        if not chemin:
            return "Aucune étape à expliquer."
        lignes = [f"On part de « {chemin[0].sujet} »."]
        for i, f in enumerate(chemin, 1):
            neg = "ne " if f.negatif else ""
            verbe = VERBES_FR.get(_norm(f.relation), f.relation)
            texte = f.explication or f"{f.sujet} {neg}{verbe} {f.objet}"
            lignes.append(f"  Étape {i} (confiance {f.poids:.0%}) : {texte}.")
            if i < len(chemin):
                lignes.append(f"  → on travaille maintenant avec « {f.objet} ».")
        dernier = chemin[-1]
        vb = VERBES_FR.get(_norm(dernier.relation), dernier.relation)
        lignes.append(f"Conclusion : « {dernier.sujet} » {vb} « {dernier.objet} ».")
        lignes.append(f"Confiance globale ({mode_poids}) : "
                      f"{self.poids_chaine(chemin, mode_poids):.2%}.")
        return "\n".join(lignes)

    # ==============================================================
    # Logique 3 valeurs
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

    # ==============================================================
    # Contradictions
    # ==============================================================
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
        resultats: List[Dict[str, Any]] = []
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
                    resultats.append({
                        "type": "directe", "fait_1": f1, "fait_2": f2,
                        "explication": (f"{f1.sujet} --{f1.relation}--> {f1.objet}"
                                        f"  VS  --{f2.relation}--> {f2.objet}"),
                    })
        for f1 in self.faits:
            opposes = RELATIONS_OPPOSEES.get(_norm(f1.relation), set())
            if not opposes:
                continue
            for f2 in self._index_sujet.get(_norm(f1.sujet), []):
                if f1 is f2 or _norm(f2.relation) not in opposes:
                    continue
                if _norm(f1.objet) == _norm(f2.objet):
                    continue
                chaine = self.trouver_chaine_deductive(
                    f1.objet, f2.objet, max_profondeur=5
                )
                if not chaine:
                    continue
                k = self._cle_couple(f1, f2)
                if k in vus:
                    continue
                vus.add(k)
                resultats.append({
                    "type": "distante", "fait_1": f1, "fait_2": f2,
                    "explication": (f"{f1.sujet} --{f1.relation}--> {f1.objet} "
                                    f"...-> {f2.objet}, mais {f1.sujet} "
                                    f"--{f2.relation}--> {f2.objet}"),
                })
        return resultats

    # ==============================================================
    # Sophismes (inchangé — heuristique)
    # ==============================================================
    def analyser_argument_et_sophismes(self, texte: str) -> List[Dict[str, Any]]:
        """Heuristique par patterns. NON complète. Filtre, pas juge."""
        t = texte.lower()
        detections: List[Dict[str, Any]] = []

        def _add(nom: str, motif: str, marqueur: str, expl: str) -> None:
            m = re.search(motif, t, flags=re.IGNORECASE)
            if m:
                detections.append({"sophisme": nom, "extrait": m.group(0),
                                   "marqueur": marqueur, "explication": expl})

        _add("faux_dilemme",
             r"\bsoit\b[^,.!?]{1,80}?,?\s+soit\b[^,.!?]{1,80}",
             "soit... soit...", "Présente deux options comme seules possibles.")
        _add("pente_glissante",
             r"\bsi\s+on\b[^.!?]{0,120}?\b(alors|on finira|finira par|"
             r"mènera|conduira|aboutira)\b",
             "si on... alors...", "Enchaîne vers une conséquence extrême.")
        _add("appel_autorite",
             r"\b(tout le monde sait|tout le monde dit|les experts disent|"
             r"selon les scientifiques|la science dit|c'est évident que|"
             r"il est bien connu que|chacun sait que)\b",
             "tout le monde sait", "Invoque une autorité sans preuve.")
        _add("generalisation_hative",
             r"\b(toujours|jamais|tous les|toutes les|aucun|aucune|"
             r"personne ne)\b",
             "toujours / jamais / tous", "Quantificateur universel abusif.")
        _add("ad_hominem",
             r"\b(tu es|vous êtes|il est|c'est|t'es)\s+(qu')?\s*(un|une)?\s*"
             r"(idiot|imbécile|ignorant|incompétent|fou|menteur|naïf|stupide)\b",
             "tu es [insulte]", "Attaque la personne, pas l'argument.")
        _add("empoisonnement_puits",
             r"\b(ne l'écoutez pas|ne l'écoute pas|ne le crois pas|"
             r"de toute façon (il|elle))\b[^.!?]{0,60}?"
             r"\b(ment|triche|est payé|est vendu|a un intérêt)\b",
             "ne l'écoute pas, il...", "Discrédite la source à l'avance.")
        _add("inversion_charge_preuve",
             r"\b(prouve[- ]le|prouve[- ]moi|prouve que|démontre[- ]le|"
             r"démontre que|prouvez[- ]le|prouvez[- ]moi)\b",
             "prouve-le", "Exige la preuve du négatif.")
        _add("presuppose_cache",
             r"\bpourquoi\b[^.!?]{0,80}?\b(encore|toujours|déjà)\b"
             r"|\bas[- ]tu\s+(arrêté|cessé)\b",
             "pourquoi ... encore", "Présuppose un fait non établi.")
        return detections

    # ==============================================================
    # (1) Dialectique enrichie
    # ==============================================================
    def _faits_autour(self, concept: str) -> List[FaitRelationnel]:
        """Tous les faits où le concept apparaît (sujet OU objet), dédupliqués."""
        c = _norm(concept)
        vus: Set[Tuple] = set()
        out: List[FaitRelationnel] = []
        for f in list(self._index_sujet.get(c, [])) + list(self._index_objet.get(c, [])):
            k = (_norm(f.sujet), _norm(f.relation), _norm(f.objet), f.negatif)
            if k not in vus:
                vus.add(k)
                out.append(f)
        return out

    @staticmethod
    def _fmt(f: FaitRelationnel) -> str:
        neg = "¬" if f.negatif else ""
        return f"{f.sujet} {neg}{f.relation} {f.objet} [{f.poids:.2f}]"

    def synthese_dialectique(self, sujet_a: str, sujet_b: str) -> Dict[str, Any]:
        """
        Exploite _index_sujet ET _index_objet, tensions directes + multi-sauts,
        ponts déductifs A↔B. La synthèse reste un AGENCEMENT de matériaux.
        """
        a, b = _norm(sujet_a), _norm(sujet_b)
        faits_a = self._faits_autour(a)
        faits_b = self._faits_autour(b)

        # Thèse : ce qu'on dit de A (A en sujet) ; sinon tout autour de A
        these_faits = [f for f in faits_a if _norm(f.sujet) == a] or faits_a
        antithese_faits = [f for f in faits_b if _norm(f.sujet) == b] or faits_b

        these = [self._fmt(f) for f in these_faits]
        antithese = [self._fmt(f) for f in antithese_faits]

        # Accords : même (relation, objet) autour de A et B
        cles_a = {(_norm(f.relation), _norm(f.objet)) for f in faits_a}
        cles_b = {(_norm(f.relation), _norm(f.objet)) for f in faits_b}
        accords = [f"{r} → {o}" for r, o in sorted(cles_a & cles_b)]

        # Tensions directes (parmi l'union des faits autour de A et B)
        union = {(_norm(f.sujet), _norm(f.relation), _norm(f.objet), f.negatif): f
                 for f in faits_a + faits_b}
        liste = list(union.values())
        tensions: List[str] = []
        vus_t: Set[Tuple] = set()
        for i, f1 in enumerate(liste):
            for f2 in liste[i + 1:]:
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
                    tensions.append(
                        f"[directe] {f1.sujet} --{r1}--> {f1.objet}  VS  "
                        f"--{r2}--> {f2.objet}"
                    )

        # Tensions multi-sauts : contradictions détectées touchant a ou b
        for c in self.detecter_contradictions():
            if c["type"] != "distante":
                continue
            f1, f2 = c["fait_1"], c["fait_2"]
            implique = any(
                _norm(x) in (a, b)
                for x in (f1.sujet, f1.objet, f2.sujet, f2.objet)
            )
            if implique:
                tensions.append(f"[distante] {c['explication']}")

        # Ponts déductifs A↔B (utilise Dijkstra)
        ponts: List[str] = []
        for src, dst, lbl in [(a, b, "A→B"), (b, a, "B→A")]:
            ch = self.trouver_chaine_deductive(
                src, dst, max_profondeur=4, strategie="dijkstra"
            )
            if ch:
                poids = self.poids_chaine(ch, "moyenne_geo")
                ponts.append(
                    f"[{lbl}] {src} ⇒ {dst} "
                    f"({len(ch)} étape(s), confiance moy-égo {poids:.3f})\n"
                    + self.formater_preuve(ch, mode_poids="moyenne_geo")
                )

        # Synthèse
        if tensions:
            synthese = (
                f"Dépassement à construire : {len(tensions)} tension(s). "
                f"Pistes : (i) distinguer deux sens du prédicat en cause, "
                f"(ii) montrer que les affirmations portent sur des aspects "
                f"différents, (iii) trancher empiriquement."
            )
        elif accords:
            synthese = (
                f"Convergence sur {len(accords)} point(s) : "
                f"{'; '.join(accords[:3])}"
                + ("…" if len(accords) > 3 else "") + "."
            )
        elif ponts:
            synthese = (
                f"Pas de tension ni d'accord direct, mais {len(ponts)} pont(s) "
                f"déductif(s) relient les concepts."
            )
        else:
            synthese = "Ni accord, ni tension, ni pont. Enrichir le graphe."

        return {
            "these": {"sujet": sujet_a, "affirmations": these},
            "antithese": {"sujet": sujet_b, "affirmations": antithese},
            "accords": accords, "tensions": tensions,
            "ponts": ponts, "synthese": synthese,
        }

    # ==============================================================
    # DAG causal
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
        self._graphe_causal = g
        return g

    # ==============================================================
    # Bench
    # ==============================================================
    def bench(self, n: int = 2000, strategie: str = "dijkstra") -> Dict[str, float]:
        requetes = [("Socrate", "être_vivant"), ("tabac", "cancer_poumon"),
                    ("fumer", "santé")]
        self._cache.clear()
        t0 = time.perf_counter()
        for i in range(n):
            d, a = requetes[i % len(requetes)]
            self.trouver_chaine_deductive(d, a, strategie=strategie)
        dt_ms = (time.perf_counter() - t0) * 1000 / n
        return {"requetes": float(n), "temps_moyen_ms": dt_ms, "strategie": strategie}


# ===========================================================================
# Auto-test complet
# ===========================================================================
if __name__ == "__main__":
    faits = [
        # taxonomie (pour héritage automatique)
        FaitRelationnel("Socrate", "est_un", "homme", poids=1.0),
        FaitRelationnel("homme", "est_un", "mammifère", poids=0.98),
        FaitRelationnel("mammifère", "est_un", "animal", poids=1.0),
        FaitRelationnel("animal", "est_un", "être_vivant", poids=1.0),
        FaitRelationnel("animal", "est", "mortel", poids=0.99),

        # causal (pour abduction)
        FaitRelationnel("tabac", "cause", "goudron", poids=0.9),
        FaitRelationnel("goudron", "cause", "cancer_poumon", poids=0.85),
        FaitRelationnel("tabac", "cause", "cancer_poumon", poids=0.6),
        FaitRelationnel("amiante", "cause", "cancer_poumon", poids=0.7),

        # contradiction (pour dialectique)
        FaitRelationnel("fumer", "cause", "santé", poids=0.3),
        FaitRelationnel("fumer", "empeche", "santé", poids=0.9),
        FaitRelationnel("fumer", "cause", "cancer", poids=0.8),
        FaitRelationnel("cancer", "implique", "mort", poids=0.9),
    ]

    m = MoteurDeductifCausal(faits=faits)
    m.ajouter_regle(REGLE_HERITAGE)

    print("=" * 70)
    print("(4) RÈGLES DE HORN — héritage automatique de propriétés")
    print("=" * 70)
    print("Avant saturation :", "Socrate est mortel" in
          [f"{f.sujet} {f.relation} {f.objet}" for f in m.faits])
    n = m.saturer_regles(max_iterations=6)
    print(f"Faits dérivés : {n}")
    for f in m.faits:
        if f.explication and "heritage" in f.explication:
            print(f"  → {f.sujet} {f.relation} {f.objet} [{f.poids:.2f}] "
                  f"({f.explication})")

    print()
    print("=" * 70)
    print("(3) DIJKSTRA vs BFS — chaîne de poids maximal")
    print("=" * 70)
    for strat in ("bfs", "dijkstra"):
        ch = m.trouver_chaine_deductive("tabac", "cancer_poumon",
                                        strategie=strat)
        p = m.poids_chaine(ch) if ch else 0
        print(f"  [{strat:8s}] {len(ch) if ch else 0} étape(s), poids={p:.4f}")
        if ch:
            print(m.formater_preuve(ch))

    print()
    print("=" * 70)
    print("(2) ABDUCTION — remonter_aux_causes('cancer_poumon')")
    print("=" * 70)
    causes = m.remonter_aux_causes("cancer_poumon", max_profondeur=5)
    for ch in causes:
        print(" ·", " → ".join(f"{f.sujet} --{f.relation}--> {f.objet}"
                               for f in ch))

    print()
    print("expliquer_pourquoi('tabac', 'cancer_poumon') :")
    res = m.expliquer_pourquoi("tabac", "cancer_poumon")
    print(f"  sens = {res['sens']}")
    print("  " + res["explication"].replace("\n", "\n  "))

    print()
    print("=" * 70)
    print("(1) DIALECTIQUE ENRICHIE — 'fumer' vs 'santé'")
    print("=" * 70)
    d = m.synthese_dialectique("fumer", "santé")
    print("THÈSE     :", d["these"]["affirmations"])
    print("ANTITHÈSE :", d["antithese"]["affirmations"])
    print("ACCORDS   :", d["accords"])
    print("TENSIONS  :")
    for t in d["tensions"]:
        print("   -", t)
    print("PONTS     :", len(d["ponts"]))
    for p in d["ponts"]:
        print("   " + p.replace("\n", "\n   "))
    print("SYNTHÈSE  :", d["synthese"])

    print()
    print("=" * 70)
    print("BENCH")
    print("=" * 70)
    for strat in ("bfs", "dijkstra"):
        r = m.bench(3000, strategie=strat)
        print(f"  {r['strategie']:8s} : {r['temps_moyen_ms']:.3f} ms/req")
