#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""alix_moteur_deductif_poseidon_v3.py — v3.0 (Forge Poséidon / DeepSeek)
Moteur de Raisonnement Déductif local — stdlib uniquement.

Nouveautés v3.0 :
  - Séparation sémantique des relations (taxonomique / causal / logique / opposition)
  - Pondération des faits (poids ∈ [0,1]) ; chaîne = produit
  - Cache LRU sur les recherches de chaînes
  - Négation explicite (negatif=True) + logique à 3 valeurs
  - Bench intégré
"""
from __future__ import annotations

from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import re
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


# ---------------------------------------------------------------------------
# Typage sémantique des relations
# ---------------------------------------------------------------------------
class TypeRelation(Enum):
    TAXONOMIQUE = "taxonomique"   # est_un, est_une, est
    CAUSAL      = "causal"        # cause, permet, entraine, conduit_a, mene_a
    LOGIQUE     = "logique"       # implique, affirme
    OPPOSITION  = "opposition"    # empeche, interdit, nie, contredit


RELATION_TYPE: Dict[str, TypeRelation] = {
    "est":       TypeRelation.TAXONOMIQUE,
    "est_un":    TypeRelation.TAXONOMIQUE,
    "est_une":   TypeRelation.TAXONOMIQUE,
    "cause":     TypeRelation.CAUSAL,
    "permet":    TypeRelation.CAUSAL,
    "entraine":  TypeRelation.CAUSAL,
    "conduit_a": TypeRelation.CAUSAL,
    "mene_a":    TypeRelation.CAUSAL,
    "implique":  TypeRelation.LOGIQUE,
    "affirme":   TypeRelation.LOGIQUE,
    "empeche":   TypeRelation.OPPOSITION,
    "interdit":  TypeRelation.OPPOSITION,
    "nie":       TypeRelation.OPPOSITION,
    "contredit": TypeRelation.OPPOSITION,
}

# Une famille peut-elle se chaîner vers une autre ?
COMPATIBILITE: Dict[TypeRelation, Set[TypeRelation]] = {
    TypeRelation.TAXONOMIQUE: {TypeRelation.TAXONOMIQUE, TypeRelation.LOGIQUE},
    TypeRelation.CAUSAL:      {TypeRelation.CAUSAL, TypeRelation.LOGIQUE},
    TypeRelation.LOGIQUE:     {TypeRelation.LOGIQUE, TypeRelation.TAXONOMIQUE},
    TypeRelation.OPPOSITION:  set(),  # une opposition ne chaîne jamais
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


# ---------------------------------------------------------------------------
# Fait
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Moteur
# ---------------------------------------------------------------------------
class MoteurDeductifCausal:
    def __init__(
        self,
        encyclopedie: Any = None,
        faits: Optional[List[FaitRelationnel]] = None,
        cache_taille: int = 512,
    ) -> None:
        self.faits: List[FaitRelationnel] = list(faits or [])
        self.encyclopedie = encyclopedie
        self._cache_taille = cache_taille
        self._cache: "OrderedDict[Tuple, Any]" = OrderedDict()
        self._index_sujet: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._index_objet: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._index_relation: Dict[str, List[FaitRelationnel]] = defaultdict(list)
        self._reindexer()

    # ------------------------------------------------------------------
    # Indexation / cache
    # ------------------------------------------------------------------
    def _reindexer(self) -> None:
        self._index_sujet.clear()
        self._index_objet.clear()
        self._index_relation.clear()
        for f in self.faits:
            self._indexer_un(f)
        self._cache.clear()

    def _indexer_un(self, f: FaitRelationnel) -> None:
        self._index_sujet[_norm(f.sujet)].append(f)
        self._index_objet[_norm(f.objet)].append(f)
        self._index_relation[_norm(f.relation)].append(f)
        self._cache.clear()

    def ajouter_fait(self, fait: FaitRelationnel) -> None:
        self.faits.append(fait)
        self._indexer_un(fait)

    def _cache_put(self, cle: Tuple, valeur: Any) -> None:
        self._cache[cle] = valeur
        self._cache.move_to_end(cle)
        if len(self._cache) > self._cache_taille:
            self._cache.popitem(last=False)

    # ------------------------------------------------------------------
    # 1) Chaînage déductif N-étapes pondéré
    # ------------------------------------------------------------------
    def trouver_chaine_deductive(
        self,
        depart: str,
        arrivee: str,
        max_profondeur: int = 8,
        mode: str = "mixte",             # "taxonomique"|"causal"|"logique"|"mixte"
        seuil_poids: float = 0.05,
    ) -> Optional[List[FaitRelationnel]]:
        depart_n, arrivee_n = _norm(depart), _norm(arrivee)
        if depart_n == arrivee_n:
            return []

        cle = (depart_n, arrivee_n, max_profondeur, mode, seuil_poids)
        if cle in self._cache:
            self._cache.move_to_end(cle)
            return self._cache[cle]

        resultat = self._bfs_pondere(
            depart_n, arrivee_n, max_profondeur, mode, seuil_poids
        )
        self._cache_put(cle, resultat)
        return resultat

    def _bfs_pondere(
        self,
        depart: str,
        arrivee: str,
        max_profondeur: int,
        mode: str,
        seuil_poids: float,
    ) -> Optional[List[FaitRelationnel]]:
        """
        BFS pondéré. Grâce à poids ∈ [0,1], le produit est monotone décroissant :
        un élagage par (nœud, dernier_type) est équivalent à un Dijkstra ici.
        Retourne la chaîne de poids cumulé maximal trouvée sous les contraintes.
        """
        meilleur: Optional[List[FaitRelationnel]] = None
        meilleur_poids = -1.0
        queue: deque = deque([(depart, [], 1.0, None)])
        vus: Dict[Tuple[str, Optional[TypeRelation]], float] = {
            (depart, None): 1.0
        }

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

    def poids_chaine(self, chemin: List[FaitRelationnel]) -> float:
        p = 1.0
        for f in chemin:
            p *= f.poids
        return p

    def formater_preuve(self, chemin: List[FaitRelationnel]) -> str:
        if not chemin:
            return "(chemin vide : identité)"
        lignes = []
        for i, f in enumerate(chemin, 1):
            marque = "¬" if f.negatif else ""
            lignes.append(
                f"  {i}. {f.sujet} --{marque}{f.relation}"
                f"[{f.poids:.2f}]--> {f.objet}"
            )
        lignes.append(f"  ⇒ poids cumulé : {self.poids_chaine(chemin):.4f}")
        return "\n".join(lignes)

    def syllogisme(
        self, sujet: str, cible: str, max_profondeur: int = 6
    ) -> Optional[Dict[str, Any]]:
        chemin = self.trouver_chaine_deductive(
            sujet, cible, max_profondeur=max_profondeur, mode="taxonomique"
        )
        if chemin is None:
            return None
        return {
            "conclusion": f"{sujet} est_un {cible}",
            "preuves": chemin,
            "etapes": len(chemin),
            "poids": self.poids_chaine(chemin),
        }

    # ------------------------------------------------------------------
    # 2) Logique à 3 valeurs + négation
    # ------------------------------------------------------------------
    def est_prouvable(self, sujet: str, relation: str, objet: str,
                      **kw: Any) -> bool:
        s, r, o = _norm(sujet), _norm(relation), _norm(objet)
        for f in self._index_sujet.get(s, []):
            if (not f.negatif
                    and _norm(f.relation) == r
                    and _norm(f.objet) == o):
                return True
        t = RELATION_TYPE.get(r)
        if t is None or t == TypeRelation.OPPOSITION:
            return False
        return bool(self.trouver_chaine_deductive(sujet, objet, **kw))

    def est_refute(self, sujet: str, relation: str, objet: str) -> bool:
        s, r, o = _norm(sujet), _norm(relation), _norm(objet)
        opposes = RELATIONS_OPPOSEES.get(r, set())
        for f in self._index_sujet.get(s, []):
            if _norm(f.objet) != o:
                continue
            if f.negatif and _norm(f.relation) == r:
                return True
            if _norm(f.relation) in opposes:
                return True
        return False

    def valeur_logique(self, sujet: str, relation: str, objet: str,
                       **kw: Any) -> str:
        """
        'vrai' | 'faux' | 'indetermine'
        'indetermine' couvre : ni prouvé ni réfuté (monde ouvert),
                              OU prouvé ET réfuté (contradiction).
        """
        p = self.est_prouvable(sujet, relation, objet, **kw)
        r = self.est_refute(sujet, relation, objet)
        if p and not r:
            return "vrai"
        if r and not p:
            return "faux"
        return "indetermine"

    def negation_par_echec(self, sujet: str, relation: str, objet: str,
                           **kw: Any) -> bool:
        """
        CONVENTION (monde clos) : si on ne peut pas prouver A, on pose ¬A.
        Ce n'est PAS une vérité logique — c'est un choix de sémantique.
        """
        return not self.est_prouvable(sujet, relation, objet, **kw)

    # ------------------------------------------------------------------
    # 3) Contradictions
    # ------------------------------------------------------------------
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

        # --- directes : même (sujet, objet), relations opposées ---
        couples: Dict[Tuple[str, str], List[FaitRelationnel]] = defaultdict(list)
        for f in self.faits:
            couples[(_norm(f.sujet), _norm(f.objet))].append(f)
        for (_, _), fs in couples.items():
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
                        "type": "directe",
                        "fait_1": f1,
                        "fait_2": f2,
                        "explication": (
                            f"{f1.sujet} --{f1.relation}--> {f1.objet}  VS  "
                            f"--{f2.relation}--> {f2.objet}"
                        ),
                    })

        # --- distantes : A -r1-> X ...-> Y ET A -r2-> Y (r2 opposée à r1) ---
        for f1 in self.faits:
            r1 = _norm(f1.relation)
            opposes = RELATIONS_OPPOSEES.get(r1, set())
            if not opposes:
                continue
            for f2 in self._index_sujet.get(_norm(f1.sujet), []):
                if f1 is f2:
                    continue
                r2 = _norm(f2.relation)
                if r2 not in opposes:
                    continue
                if _norm(f1.objet) == _norm(f2.objet):
                    continue  # déjà détecté en directe
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
                    "type": "distante",
                    "fait_1": f1,
                    "fait_2": f2,
                    "explication": (
                        f"{f1.sujet} --{f1.relation}--> {f1.objet} "
                        f"...-> {f2.objet}, mais {f1.sujet} "
                        f"--{f2.relation}--> {f2.objet}"
                    ),
                })
        return resultats

    # ------------------------------------------------------------------
    # 4) Détecteur de sophismes (heuristique — patterns structurels)
    # ------------------------------------------------------------------
    def analyser_argument_et_sophismes(self, texte: str) -> List[Dict[str, Any]]:
        """
        Détection par PATRONS structurels. Heuristique, NON complète.
        Peut produire des faux positifs. À utiliser comme FILTRE, pas comme juge.
        """
        t = texte.lower()
        detections: List[Dict[str, Any]] = []

        def _add(nom: str, motif: str, marqueur: str, expl: str) -> None:
            m = re.search(motif, t, flags=re.IGNORECASE)
            if m:
                detections.append({
                    "sophisme": nom,
                    "extrait": m.group(0),
                    "marqueur": marqueur,
                    "explication": expl,
                })

        _add("faux_dilemme",
             r"\bsoit\b[^,.!?]{1,80}?,?\s+soit\b[^,.!?]{1,80}",
             "soit... soit...",
             "Présente deux options comme les seules possibles.")

        _add("pente_glissante",
             r"\bsi\s+on\b[^.!?]{0,120}?\b(alors|on finira|finira par|"
             r"mènera|conduira|aboutira)\b",
             "si on... alors...",
             "Enchaîne sans justification vers une conséquence extrême.")

        _add("appel_autorite",
             r"\b(tout le monde sait|tout le monde dit|les experts disent|"
             r"selon les scientifiques|la science dit|c'est évident que|"
             r"il est bien connu que|chacun sait que)\b",
             "tout le monde sait / les experts disent",
             "Invoque une autorité ou la majorité sans preuve.")

        _add("generalisation_hative",
             r"\b(toujours|jamais|tous les|toutes les|aucun|aucune|"
             r"personne ne)\b",
             "toujours / jamais / tous / aucun",
             "Quantificateur universel sans preuve suffisante.")

        _add("ad_hominem",
             r"\b(tu es|vous êtes|il est|c'est|t'es)\s+(qu')?\s*(un|une)?\s*"
             r"(idiot|imbécile|ignorant|incompétent|fou|menteur|naïf|stupide)\b",
             "tu es [insulte]",
             "Attaque la personne, pas l'argument.")

        _add("empoisonnement_puits",
             r"\b(ne l'écoutez pas|ne l'écoute pas|ne le crois pas|"
             r"de toute façon (il|elle))\b[^.!?]{0,60}?"
             r"\b(ment|triche|est payé|est vendu|a un intérêt)\b",
             "ne l'écoute pas, il...",
             "Discrédite la source à l'avance pour éviter d'examiner l'argument.")

        _add("inversion_charge_preuve",
             r"\b(prouve[- ]le|prouve[- ]moi|prouve que|démontre[- ]le|"
             r"démontre que|prouvez[- ]le|prouvez[- ]moi)\b",
             "prouve-le",
             "Exige de l'autre la preuve du négatif.")

        _add("presuppose_cache",
             r"\bpourquoi\b[^.!?]{0,80}?\b(encore|toujours|déjà)\b"
             r"|\bas[- ]tu\s+(arrêté|cessé)\b",
             "pourquoi ... encore / as-tu arrêté de...",
             "La question présuppose un fait non établi.")

        return detections

    # ------------------------------------------------------------------
    # 5) Dialectique thèse / antithèse / synthèse
    # ------------------------------------------------------------------
    def synthese_dialectique(self, sujet_a: str, sujet_b: str) -> Dict[str, Any]:
        """
        La « synthèse » est un AGENCEMENT de matériaux présents dans la base.
        Ce n'est PAS une vérité nouvelle inventée par le moteur.
        """
        a, b = _norm(sujet_a), _norm(sujet_b)
        faits_a = list(self._index_sujet.get(a, []))
        faits_b = list(self._index_sujet.get(b, []))

        these = [
            f"{f.sujet} {f.relation} {f.objet} [{f.poids:.2f}]"
            for f in faits_a
        ]
        antithese = [
            f"{f.sujet} {f.relation} {f.objet} [{f.poids:.2f}]"
            for f in faits_b
        ]

        cles_a = {(_norm(f.relation), _norm(f.objet)) for f in faits_a}
        cles_b = {(_norm(f.relation), _norm(f.objet)) for f in faits_b}
        accords = [f"{r} -> {o}" for r, o in sorted(cles_a & cles_b)]

        par_objet_a = {_norm(f.objet): f for f in faits_a}
        par_objet_b = {_norm(f.objet): f for f in faits_b}
        tensions: List[str] = []
        for o in sorted(set(par_objet_a) & set(par_objet_b)):
            fa, fb = par_objet_a[o], par_objet_b[o]
            ra, rb = _norm(fa.relation), _norm(fb.relation)
            if (rb in RELATIONS_OPPOSEES.get(ra, set())
                    or ra in RELATIONS_OPPOSEES.get(rb, set())):
                tensions.append(
                    f"sur '{o}' : {fa.sujet} --{ra}--> vs {fb.sujet} --{rb}-->"
                )

        ponts: List[str] = []
        ch = self.trouver_chaine_deductive(a, b, max_profondeur=4)
        if ch:
            ponts.append(f"{a} ==> {b} :\n" + self.formater_preuve(ch))

        if tensions:
            synthese = (
                f"Dépassement à construire : les positions s'opposent sur "
                f"{len(tensions)} objet(s). Pistes : (i) distinguer deux sens "
                f"du prédicat en cause, (ii) montrer qu'ils portent sur des "
                f"aspects différents, (iii) trancher empiriquement."
            )
        elif accords:
            synthese = (
                f"Convergence sur {len(accords)} point(s). La synthèse peut "
                f"articuler ces accords en une thèse plus large."
            )
        else:
            synthese = (
                "Aucun accord ni tension directe dans la base. "
                "Enrichir le graphe pour produire une synthèse."
            )

        return {
            "these":     {"sujet": sujet_a, "affirmations": these},
            "antithese": {"sujet": sujet_b, "affirmations": antithese},
            "accords":   accords,
            "tensions":  tensions,
            "ponts":     ponts,
            "synthese":  synthese,
        }

    # ------------------------------------------------------------------
    # 6) Bench
    # ------------------------------------------------------------------
    def bench(self, n: int = 2000) -> Dict[str, float]:
        requetes = [
            ("Socrate", "être_vivant"),
            ("fumer", "mort"),
            ("Socrate", "animal"),
        ]
        self._cache.clear()
        t0 = time.perf_counter()
        for i in range(n):
            d, a = requetes[i % len(requetes)]
            self.trouver_chaine_deductive(d, a)
        dt_ms = (time.perf_counter() - t0) * 1000 / n
        return {"requetes": float(n), "temps_moyen_ms": dt_ms}


# ---------------------------------------------------------------------------
# Auto-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    faits = [
        FaitRelationnel("Socrate", "est_un", "homme",      poids=1.0),
        FaitRelationnel("homme",   "est_un", "mammifère",  poids=0.98),
        FaitRelationnel("mammifère", "est_un", "animal",   poids=1.0),
        FaitRelationnel("animal",  "est_un", "être_vivant", poids=1.0),
        FaitRelationnel("fumer", "cause", "cancer", poids=0.8),
        FaitRelationnel("cancer", "implique", "mort", poids=0.9),
        FaitRelationnel("fumer", "empeche", "santé", poids=0.9),
        FaitRelationnel("fumer", "cause",   "santé", poids=0.3),
        FaitRelationnel("Socrate", "est_un", "dieu", poids=1.0, negatif=True),
    ]

    m = MoteurDeductifCausal(faits=faits)

    print("=== 1. Syllogisme N-étapes ===")
    res = m.syllogisme("Socrate", "être_vivant")
    if res:
        print(res["conclusion"])
        print(m.formater_preuve(res["preuves"]))

    print("\n=== 2. Chaîne causale pondérée ===")
    ch = m.trouver_chaine_deductive("fumer", "mort", mode="causal")
    if ch:
        print(m.formater_preuve(ch))
    else:
        print("aucune chaîne causale pure")

    print("\n=== 3. Chaîne mixte ===")
    ch = m.trouver_chaine_deductive("fumer", "mort", mode="mixte")
    print(m.formater_preuve(ch) if ch else "aucune chaîne")

    print("\n=== 4. Contradictions ===")
    for c in m.detecter_contradictions():
        print(f"[{c['type']}] {c['explication']}")

    print("\n=== 5. Logique à 3 valeurs ===")
    for (s, r, o) in [
        ("Socrate", "est_un", "être_vivant"),
        ("Socrate", "est_un", "dieu"),
        ("Socrate", "est_un", "chat"),
        ("fumer",   "cause",  "cancer"),
    ]:
        print(f"  {s} {r} {o}  →  {m.valeur_logique(s, r, o)}")

    print("\n=== 6. Sophismes ===")
    for t in [
        "Soit tu es avec nous, soit tu es contre nous.",
        "Tout le monde sait que les experts disent que c'est vrai.",
        "Si on autorise ça, alors un jour on en viendra à tout interdire.",
        "Pourquoi es-tu encore en train de mentir ?",
        "Prouve-le si tu es si malin.",
    ]:
        print(f"\n>> {t}")
        for s in m.analyser_argument_et_sophismes(t):
            print(f"   - {s['sophisme']}  →  {s['explication']}")

    print("\n=== 7. Dialectique ===")
    d = m.synthese_dialectique("fumer", "santé")
    print("THÈSE     :", d["these"]["affirmations"])
    print("ANTITHÈSE :", d["antithese"]["affirmations"])
    print("TENSIONS  :", d["tensions"])
    print("SYNTHÈSE  :", d["synthese"])

    print("\n=== 8. Bench ===")
    r = m.bench(2000)
    print(f"  {r['requetes']:.0f} requêtes, {r['temps_moyen_ms']:.4f} ms/req")
