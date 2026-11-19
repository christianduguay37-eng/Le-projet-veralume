# -*- coding: utf-8 -*-
"""
Outils « métal » d'Alix (Couche 3 — réveil des organes dormants ; Christian, Alix & Claude, 2026-11-03).

Les organes dormants qui font un vrai calcul, vérifié dans le bac à sable du 3 novembre,
deviennent des outils du noyau partagé (port 5071 et MCP) : on les appelle à la demande,
aucun démon de plus ne tourne. Toutes les bibliothèques lourdes sont importées DANS les
fonctions : importer ce module ne coûte rien (le relais MCP léger le lit aussi).

Phase 1 :
  alix_resoudre_contraintes   Hadès CDCL(T) + MaxSAT (organe de LKB-SMT) : SAT, logique de différence, relaxation minimale.
  alix_inferer_causal         Poséidon v10 : réseau bayésien (apprentissage des tables sur observations, inférence, do()).
  alix_optimiser_lineaire     Poséidon v10 : simplexe révisé (min/max c·x sous A·x ≤ b, x ≥ 0, b ≥ 0).
  alix_ponts_caches           Résonateur sémantique : notes proches par TF-IDF et pas encore reliées par un [[lien]].
  alix_recherche_lexicale     Connecteur FTS5 : recherche par mots exacts dans l'exocerveau et la Cathédrale (si l'index existe).

Phase 2 :
  alix_deduire                Moteur déductif causal v10 : chaîne de preuve et contradictions sur des faits donnés.
  alix_poles_emergents        Boule de neige spectrale : pôles de pensée des notes récentes (lecture seule).
  alix_audit_coffre           Audit topologique d'un coffre (lecture seule).
  alix_echantillon_cathedrale Tirage au hasard dans les Parquet de la Cathédrale.
  alix_compiler_matiere       Compilateur de matière LP-SMT (scénario prospectif).
  alix_lmh_verifier           Suite de preuves formelles de LMH v3.
  alix_calculer_exact         Calcul exact (AST Fraction, SymPy, dimensionnel, logique, auditeur Lean 4).
Non branchés : l'expérience signal/MaxSAT (démo fixe d'Hadès, qui réécrit son .lkb : le dilemme se pose
directement dans alix_resoudre_contraintes), probe_deep_links (même calcul qu'alix_ponts_caches),
la forensique Horus (attend un vocabulaire d'hypothèse avant de toucher des noms réels).
"""
import json
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Définitions MCP
# ---------------------------------------------------------------------------
DEFINITIONS_METAL = [
    {
        "name": "alix_resoudre_contraintes",
        "description": ("Solveur de contraintes d'Alix (Hadès CDCL(T), vérifié 350/350 le 2026-11-03). Variables booléennes, "
                        "clauses dures et souples pondérées, contraintes de différence x − y ≤ c (délais). Si tout ne tient pas, "
                        "trouve la relaxation de coût minimal et le noyau contradictoire. Littéraux : 'a' ou '-a'."),
        "inputSchema": {"type": "object", "properties": {
            "dures": {"type": "array", "description": "Clauses dures : liste de listes de littéraux, ex. [['a','-b'],['b']]."},
            "souples": {"type": "array", "description": "Clauses souples : [{'clause': ['a'], 'poids': 3, 'nom': 'préférence'}]."},
            "differences": {"type": "array", "description": "[{'x':'A','y':'B','c':-250,'poids':10}] ; sans poids = dure. Sens : x − y ≤ c."}
        }}
    },
    {
        "name": "alix_inferer_causal",
        "description": ("Raisonnement causal bayésien (Poséidon v10) sur variables 0/1 : apprend les probabilités à partir d'observations, "
                        "puis calcule P(variable = 1 | indices) ou sous intervention do(). Calcul exact par élimination de variables."),
        "inputSchema": {"type": "object", "properties": {
            "aretes": {"type": "array", "description": "Arêtes causales [['tabac','cancer'], …]."},
            "observations": {"type": "array", "description": "Lignes observées [{'tabac':1,'cancer':0}, …] (toutes les variables)."},
            "variable": {"type": "string"},
            "indices": {"type": "object", "description": "Évidence observée {'toux': 1}."},
            "intervention": {"type": "object", "description": "do() {'tabac': 0}."}
        }, "required": ["aretes", "observations", "variable"]}
    },
    {
        "name": "alix_optimiser_lineaire",
        "description": "Programmation linéaire exacte (simplexe révisé de Poséidon v10) : optimise c·x sous A·x ≤ b, x ≥ 0 (b ≥ 0).",
        "inputSchema": {"type": "object", "properties": {
            "objectif": {"type": "string", "enum": ["max", "min"]},
            "c": {"type": "array"}, "A": {"type": "array"}, "b": {"type": "array"},
            "noms": {"type": "array", "description": "Noms des variables (facultatif)."}
        }, "required": ["c", "A", "b"]}
    },
    {
        "name": "alix_ponts_caches",
        "description": ("Résonateur sémantique (TF-IDF) : trouve des notes de l'exocerveau proches par leur contenu mais pas encore "
                        "reliées par un [[lien]]. Autour d'une note précise, ou les meilleurs ponts de tout le coffre."),
        "inputSchema": {"type": "object", "properties": {
            "note": {"type": "string", "description": "Titre d'une note (facultatif)."},
            "k": {"type": "integer"}, "seuil": {"type": "number"}
        }}
    },
    {
        "name": "alix_recherche_lexicale",
        "description": "Recherche par mots exacts (SQLite FTS5) dans l'exocerveau et la Cathédrale. Complète la recherche par le sens.",
        "inputSchema": {"type": "object", "properties": {
            "requete": {"type": "string"},
            "portee": {"type": "string", "enum": ["exocerveau", "cathedrale", "les_deux"]},
            "max": {"type": "integer"}
        }, "required": ["requete"]}
    },
]
NOMS_METAL = {d["name"] for d in DEFINITIONS_METAL}


# ---------------------------------------------------------------------------
# 1. Contraintes (Hadès)
# ---------------------------------------------------------------------------
def resoudre_contraintes(args: Dict[str, Any], max_noeuds: int = 4000) -> Dict[str, Any]:
    from alix.solveurs.alix_dpll_t_solver_hades import Solver
    dures = args.get("dures") or []
    souples = args.get("souples") or []
    diffs = args.get("differences") or []
    s = Solver("idl" if diffs else None)
    noms: Dict[str, int] = {}

    def lit(t: str) -> int:
        t = str(t).strip()
        neg = t.startswith("-") or t.startswith("¬")
        n = t.lstrip("-¬").strip()
        if n not in noms:
            noms[n] = s.new_var()
        return -noms[n] if neg else noms[n]

    for cl in dures:
        s.add_clause([lit(x) for x in cl])
    selecteurs: List[Dict[str, Any]] = []
    for i, so in enumerate(souples):
        sel = s.add_soft([lit(x) for x in so.get("clause", [])])
        selecteurs.append({"sel": sel, "poids": float(so.get("poids", 1)), "nom": so.get("nom") or f"souple#{i}"})
    for j, d in enumerate(diffs):
        a = s.le(str(d["x"]), str(d["y"]), d["c"])
        desc = f"{d['x']} − {d['y']} ≤ {d['c']}"
        if d.get("poids") is None:
            s.add_clause([a])
        else:
            sel = s.add_soft([a])
            selecteurs.append({"sel": sel, "poids": float(d["poids"]), "nom": d.get("nom") or desc})

    t0 = time.perf_counter()
    if not s.solve([]):
        return {"statut": "CONTRADICTION_DURE", "message": "Les contraintes dures se contredisent entre elles : aucune solution.",
                "duree_ms": round((time.perf_counter() - t0) * 1000, 2)}

    par_sel = {x["sel"]: x for x in selecteurs}
    meilleur = {"cout": float("inf"), "relaxe": None}
    noyaux: List[List[str]] = []
    compteur = {"n": 0}

    def dfs(relaxe: frozenset, cout: float):
        compteur["n"] += 1
        if compteur["n"] > max_noeuds or cout >= meilleur["cout"]:
            return
        actifs = [x["sel"] for x in selecteurs if x["sel"] not in relaxe]
        if s.solve(actifs):
            meilleur["cout"], meilleur["relaxe"] = cout, relaxe
            return
        mus = s.minimal_unsat_subset(actifs) or []
        if len(noyaux) < 3:
            noyaux.append([par_sel[m]["nom"] for m in mus if m in par_sel])
        for m in sorted(mus, key=lambda q: par_sel[q]["poids"]):
            dfs(relaxe | {m}, cout + par_sel[m]["poids"])

    dfs(frozenset(), 0.0)
    if meilleur["relaxe"] is None:
        return {"statut": "LIMITE_ATTEINTE", "noeuds": compteur["n"], "noyaux_contradictoires": noyaux}
    actifs = [x["sel"] for x in selecteurs if x["sel"] not in meilleur["relaxe"]]
    s.solve(actifs)
    booleens = {n: s.model_value(v) for n, v in noms.items()}
    entiers = {k: (float(v) if not isinstance(v, (int, float)) else v) for k, v in (s.int_model or {}).items()} if diffs else {}
    relaxees = [par_sel[m]["nom"] for m in meilleur["relaxe"]]
    return {
        "statut": "OPTIMAL" if not relaxees else "OPTIMAL_AVEC_RELAXATION",
        "cout_relaxation": meilleur["cout"],
        "contraintes_relachees": relaxees,
        "noyaux_contradictoires": noyaux,
        "booleens": booleens,
        "valeurs_entieres": entiers,
        "noeuds_explores": compteur["n"],
        "duree_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


# ---------------------------------------------------------------------------
# 2. Inférence causale (Poséidon)
# ---------------------------------------------------------------------------
def inferer_causal(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.solveurs.alix_moteur_deductif_poseidon_v10 import GrapheCausal, _norm
    g = GrapheCausal()
    for a, b in args["aretes"]:
        g.ajouter_arete(a, b)
    if not g.est_dag():
        return {"statut": "ERREUR", "message": "Le graphe contient un cycle : ce n'est pas un réseau causal (DAG)."}
    obs = args.get("observations") or []
    if not obs:
        return {"statut": "ERREUR", "message": "Il faut des observations pour apprendre les probabilités."}
    obs_norm = [{_norm(k): int(v) for k, v in row.items()} for row in obs]
    manquantes = sorted({n for n in g.noeuds for row in obs_norm if n not in row})
    if manquantes:
        return {"statut": "ERREUR", "message": f"Variables absentes de certaines observations : {manquantes}"}
    g.apprendre_cpts_depuis_observations(obs_norm)
    var = args["variable"]
    p = g.inference_ve(var, evidence=args.get("indices") or {}, do_dict=args.get("intervention") or None)
    base = g.inference_ve(var)
    return {
        "statut": "OK",
        "variable": var,
        "P(variable=1)": round(p[1], 4),
        "P(variable=1) sans indice ni intervention": round(base[1], 4),
        "indices": args.get("indices") or {},
        "intervention": args.get("intervention") or {},
        "nb_observations": len(obs),
        "methode": "Tables apprises par comptage (lissage de Laplace α=1), inférence exacte par élimination de variables.",
    }


# ---------------------------------------------------------------------------
# 3. Programmation linéaire (Poséidon)
# ---------------------------------------------------------------------------
def optimiser_lineaire(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.solveurs.alix_moteur_deductif_poseidon_v10 import RevisedSimplex
    c = [float(x) for x in args["c"]]
    sens = (args.get("objectif") or "max").lower()
    cc = [-x for x in c] if sens == "max" else c
    r = RevisedSimplex([[float(v) for v in row] for row in args["A"]], [float(v) for v in args["b"]], cc).resoudre()
    if r.get("statut") != "optimal":
        return {"statut": r.get("statut"), "iterations": r.get("iterations")}
    noms = args.get("noms") or [f"x{i + 1}" for i in range(len(c))]
    x = r["x"]
    return {
        "statut": "OPTIMAL",
        "objectif": sens,
        "valeur": round(sum(ci * xi for ci, xi in zip(c, x)), 6),
        "solution": {n: round(v, 6) for n, v in zip(noms, x)},
        "marges_des_contraintes": [round(v, 6) for v in r["slacks"]],
        "iterations": r["iterations"],
    }


# ---------------------------------------------------------------------------
# 4. Ponts cachés (résonateur sémantique, TF-IDF)
# ---------------------------------------------------------------------------
_EXCLUS = ("Sanctuaire_Hors_Ordi_R0", "Leurres_Souverains", ".trash", ".obsidian", "_Archives", "Archives_Discussions")
_CACHE: Dict[str, Any] = {}
_VERROU_CORPUS = threading.Lock()
_RE_LIEN = re.compile(r"\[\[([^\]|#]+)")


def _corpus():
    """Notes .md des coffres de la tête (mêmes 5 coffres que le connectome), en cache 10 minutes."""
    with _VERROU_CORPUS:  # deux appels simultanés ne construisent pas deux fois
        if _CACHE.get("t") and time.time() - _CACHE["t"] < 600:
            return _CACHE
        return _construire_corpus()


def _construire_corpus():
    from alix.substrat.alix_noyau_resident import VAULTS
    titres, textes, liens = [], [], []
    for _, racine in VAULTS.items():
        racine = Path(racine)
        if not racine.exists():
            continue
        for f in racine.rglob("*.md"):
            if any(e in f.parts for e in _EXCLUS):
                continue
            try:
                t = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            t = re.sub(r"\A---.*?\n---\s*\n", "", t, count=1, flags=re.S)
            titres.append(f.stem)
            textes.append(f.stem.replace("_", " ") + " " + t[:4000])
            liens.append({x.strip().lower() for x in _RE_LIEN.findall(t)})
    from sklearn.feature_extraction.text import TfidfVectorizer
    X = TfidfVectorizer(max_features=40000, min_df=2, max_df=0.5, sublinear_tf=True,
                        token_pattern=r"(?u)\b[^\W\d_]{3,}\b").fit_transform(textes)
    _CACHE.update({"t": time.time(), "titres": titres, "X": X, "liens": liens,
                   "index": {t.lower(): i for i, t in enumerate(titres)}})
    return _CACHE


def _relies(c, i, j) -> bool:
    ti, tj = c["titres"][i].lower(), c["titres"][j].lower()
    if ti == tj:
        return True
    return tj in c["liens"][i] or ti in c["liens"][j]


def ponts_caches(args: Dict[str, Any]) -> Dict[str, Any]:
    import numpy as np
    t0 = time.perf_counter()
    c = _corpus()
    X, titres = c["X"], c["titres"]
    k = int(args.get("k") or 10)
    seuil = float(args.get("seuil") or 0.25)
    note = (args.get("note") or "").strip()
    ponts = []
    if note:
        i = c["index"].get(note.lower().replace(" ", "_")) if note.lower() not in c["index"] else c["index"][note.lower()]
        if i is None:
            return {"statut": "NOTE_INTROUVABLE", "note": note, "nb_notes": len(titres)}
        sims = (X[i] @ X.T).toarray().ravel()
        sims[i] = -1
        for j in np.argsort(-sims)[: k * 4]:
            if sims[j] < seuil:
                break
            if not _relies(c, i, j):
                ponts.append({"de": titres[i], "vers": titres[j], "similarite": round(float(sims[j]), 3)})
            if len(ponts) >= k:
                break
    else:
        meilleurs = []
        for d in range(0, X.shape[0], 400):
            S = (X[d:d + 400] @ X.T).toarray()
            for a in range(S.shape[0]):
                i = d + a
                S[a, : i + 1] = -1
                j = int(np.argmax(S[a]))
                if S[a, j] >= seuil and not _relies(c, i, j):
                    meilleurs.append((float(S[a, j]), i, j))
        meilleurs.sort(reverse=True)
        ponts = [{"de": titres[i], "vers": titres[j], "similarite": round(s, 3)} for s, i, j in meilleurs[:k]]
    return {"statut": "OK", "nb_notes": len(titres), "ponts": ponts,
            "methode": "TF-IDF (scikit-learn), cosinus ; exclut les paires déjà reliées par [[lien]] ; coffres secrets exclus.",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 1)}


# ---------------------------------------------------------------------------
# 5. Recherche lexicale (FTS5)
# ---------------------------------------------------------------------------
def recherche_lexicale(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.sondes import alix_connecteur_exocerveau_cathedrale as conn
    db = Path(conn.INDEX_DB_PATH)
    if not db.exists() or db.stat().st_size < 100 * 1024:
        # On ne construit JAMAIS l'index pendant une question (lourd, écrit sur disque) : construction à part.
        return {"statut": "INDEX_ABSENT", "message": f"Index lexical absent ({db}). À construire une fois, à part."}
    m = conn.MoteurConnexionExocerveauCathedrale(db)
    n = int(args.get("max") or 5)
    portee = args.get("portee") or "les_deux"
    out: Dict[str, Any] = {"statut": "OK", "requete": args["requete"]}
    if portee in ("exocerveau", "les_deux"):
        out["exocerveau"] = m.chercher_exocerveau(args["requete"], max_resultats=n)
    if portee in ("cathedrale", "les_deux"):
        out["cathedrale"] = m.chercher_cathedrale(args["requete"], max_resultats=n)
    return out


# ===========================================================================
# PHASE 2 (2026-11-03, demande de Christian : « branche tous »)
# ===========================================================================
def _exclu(p: Path) -> bool:
    return any(e in p.parts for e in _EXCLUS)


# 6. Déduction de faits (moteur déductif causal v10)
def deduire(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.solveurs.alix_moteur_deductif_causal import MoteurDeductifCausal, FaitRelationnel
    faits = []
    for f in args.get("faits") or []:
        if isinstance(f, dict):
            faits.append(FaitRelationnel(f["sujet"], f["relation"], f["objet"], negatif=bool(f.get("negatif"))))
        else:
            faits.append(FaitRelationnel(f[0], f[1], f[2], negatif=len(f) > 3 and str(f[3]).lower() in ("non", "negatif", "faux")))
    if not faits:
        return {"statut": "ERREUR", "message": "Il faut au moins un fait : [sujet, relation, objet]."}
    t0 = time.perf_counter()
    m = MoteurDeductifCausal(faits=faits, auto_saturer=True)   # n'utilise QUE les faits donnés (+ règle d'héritage)
    out: Dict[str, Any] = {"statut": "OK", "faits_donnes": len(faits), "faits_apres_deduction": len(m.faits)}
    if args.get("de"):
        chaine = m.trouver_chaine_deductive(args["de"], args.get("vers"))
        out["chaine_trouvee"] = bool(chaine)
        out["preuve"] = m.formater_preuve(chaine) if chaine else "Aucune chaîne déductive entre ces deux termes."
    out["contradictions"] = [c.get("explication", str(c)) for c in m.detecter_contradictions()]
    out["relations_connues"] = "est, est_un, possede_propriete (taxonomie) ; cause, permet, entraine, conduit_a, mene_a (causal) ; implique, affirme (logique) ; empeche, interdit, nie, contredit (opposition)"
    out["duree_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return out


# 7. Pôles émergents (boule de neige spectrale)
def poles_emergents(args: Dict[str, Any]) -> Dict[str, Any]:
    from collections import Counter
    from alix.capacites import capacite_boule_de_neige_poles as bn
    heures = float(args.get("heures") or 72)
    seuil = time.time() - heures * 3600
    docs, compteur, n = [], Counter(), 0
    for dossier in [bn.VAULT_DIR, bn.VAULT_DIR / "Archives_Discussions_Antigravity"]:
        if not dossier.exists():
            continue
        for p in dossier.rglob("*.md"):
            if _exclu(p) or "Monde_des_Songes" in str(p) or "Monde_des_Decouvertes" in str(p):
                continue
            try:
                if p.stat().st_mtime < seuil:
                    continue
                mots = bn.nettoyer_texte(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if len(mots) >= 10:
                docs.append(set(mots))
                compteur.update(set(mots))
                n += 1
    if not docs or len(compteur) < 10:
        return {"statut": "ATTENTE_DONNEES", "notes_lues": n, "message": f"Pas assez de notes modifiées dans les {heures:g} dernières heures."}
    poles = bn.poles_spectraux(docs, compteur)   # même calcul que la capacité, sans écrire Interets_Alix.md
    return {"statut": "OK", "fenetre_heures": heures, "notes_lues": n,
            "poles": [{"titre": p["titre"], "score": p["score"], "mots": [m for m, _ in p["mots"][:10]]} for p in poles],
            "methode": "Co-occurrence (Jaccard) des 50 mots dominants, laplacien normalisé, k-moyennes sur vecteurs propres."}


# 8. Audit topologique d'un coffre (lecture seule)
def audit_coffre(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.sondes.alix_vault_audit import extract_wikilinks
    from alix.substrat.alix_noyau_resident import VAULTS
    nom = args.get("coffre") or "Cerveau Alix"
    if nom not in VAULTS:
        return {"statut": "ERREUR", "message": f"Coffre inconnu. Choix : {list(VAULTS)}"}
    racine = Path(VAULTS[nom])
    notes = {f.stem: f for f in racine.rglob("*.md") if not _exclu(f)}
    entrants = {k: 0 for k in notes}
    sortants, casses, nb_liens = {}, {}, 0
    for k, f in notes.items():
        try:
            cibles = set(extract_wikilinks(f.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            continue
        sortants[k] = len(cibles)
        nb_liens += len(cibles)
        for c in cibles:
            c = Path(c).stem
            if c in entrants:
                entrants[c] += 1
            else:
                casses[c] = casses.get(c, 0) + 1
    n = len(notes)
    orphelines = sorted(k for k in notes if entrants[k] == 0 and sortants.get(k, 0) == 0)
    hubs = sorted(entrants.items(), key=lambda kv: -kv[1])[:10]
    return {"statut": "OK", "coffre": nom, "notes": n, "liens": nb_liens,
            "densite": round(nb_liens / (n * (n - 1)), 5) if n > 1 else 0.0,
            "orphelines": len(orphelines), "exemples_orphelines": orphelines[:15],
            "liens_casses": sum(casses.values()), "cibles_cassees_frequentes": sorted(casses.items(), key=lambda kv: -kv[1])[:10],
            "notes_les_plus_citees": hubs,
            "note": "Lecture seule (aucun rapport écrit). Dossiers secrets exclus."}


# 9. Échantillon de la Cathédrale
def echantillon_cathedrale(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.solveurs.alix_echantillonneur_cathedrale import echantillonner_pepite_cathedrale
    n = max(1, min(10, int(args.get("n") or 3)))
    pepites = [p for p in (echantillonner_pepite_cathedrale() for _ in range(n)) if p]
    if not pepites:
        return {"statut": "VIDE", "message": "Aucun Parquet de la Cathédrale trouvé."}
    return {"statut": "OK", "pepites": pepites}


# 10. Compilateur de matière (scénario prospectif VERALUME)
def compiler_matiere(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.solveurs.alix_compilateur_matiere_lp_smt import compiler_allocation_optimale_lp, ELEMENTS_ORDRE
    dechets = {k: float(v) for k, v in (args.get("dechets_g") or {}).items()}
    inconnus = [k for k in dechets if k not in ELEMENTS_ORDRE]
    if not dechets or inconnus:
        return {"statut": "ERREUR", "message": f"dechets_g attend des grammes par élément parmi {ELEMENTS_ORDRE}."}
    profil = (args.get("profil") or "NUTRITION").upper()
    if profil not in ("NUTRITION", "HYDRATATION", "CONSTRUCTION"):
        return {"statut": "ERREUR", "message": "profil : NUTRITION, HYDRATATION ou CONSTRUCTION."}
    r = compiler_allocation_optimale_lp(dechets, profil_besoin=profil,
                                        plafond_brillouin_W=float(args.get("plafond_W") or 1200.0))
    r["avertissement"] = ("Scénario prospectif (chambre holographique VERALUME) : le calcul LP et la conservation de la masse "
                          "sont exacts, mais le catalogue de molécules et les coûts sont des hypothèses du modèle, pas une recette.")
    return r


# 11. LMH v3 : vérification formelle des actes de langage
def lmh_verifier(args: Dict[str, Any]) -> Dict[str, Any]:
    import contextlib
    import io
    import runpy
    tampon = io.StringIO()
    t0 = time.perf_counter()
    try:
        with contextlib.redirect_stdout(tampon):
            runpy.run_module("alix.solveurs.lmh_v3_force", run_name="__main__")
        statut = "OK"
        erreur = ""
    except AssertionError as e:
        statut, erreur = "ECHEC", f"Assertion violée : {e}"
    texte = tampon.getvalue()
    lignes = [l for l in texte.splitlines() if l.strip() and not set(l.strip()) <= {"=", "-"}]
    return {"statut": statut, "erreur": erreur, "lignes": len(lignes),
            "resume": lignes[-12:], "duree_ms": round((time.perf_counter() - t0) * 1000, 1),
            "portee": "Suite de preuves de LMH v3 (T8–T10, R12–R15, fidélité D3∘C3 = id). Vérifie le langage formel, pas un texte libre."}


# 12. Calcul symbolique, arithmétique exacte, dimensionnel & auditeur Lean 4
def calculer_exact(args: Dict[str, Any]) -> Dict[str, Any]:
    from alix.solveurs.alix_calcul_symbolique_lean import calculer_exact as _calculer
    return _calculer(
        expression=str(args.get("expression") or ""),
        mode=str(args.get("mode") or "auto"),
        action=str(args.get("action") or "auto"),
        variable=str(args.get("variable") or ""),
        vers_unite=str(args.get("vers_unite") or ""),
        premisses=args.get("premisses"),
        conclusion=str(args.get("conclusion") or ""),
        utiliser_57m=bool(args.get("utiliser_57m", False)),
    )


DEFINITIONS_METAL += [
    {"name": "alix_deduire",
     "description": ("Moteur déductif causal (v10) : à partir de faits [sujet, relation, objet] (ajouter 'non' en 4e position pour une négation), "
                     "sature les règles, trouve la chaîne de preuve entre deux termes et détecte les contradictions. N'utilise que les faits donnés."),
     "inputSchema": {"type": "object", "properties": {
         "faits": {"type": "array", "description": "[['socrate','est_un','homme'], ['homme','est','mortel']]"},
         "de": {"type": "string"}, "vers": {"type": "string"}}, "required": ["faits"]}},
    {"name": "alix_poles_emergents",
     "description": "Pôles de pensée qui émergent des notes récentes de l'exocerveau (regroupement spectral, boule de neige). Lecture seule.",
     "inputSchema": {"type": "object", "properties": {"heures": {"type": "number", "description": "Fenêtre (défaut 72 h)."}}}},
    {"name": "alix_audit_coffre",
     "description": "Audit topologique d'un coffre Obsidian : notes, liens, densité, orphelines, liens cassés, notes les plus citées. Lecture seule.",
     "inputSchema": {"type": "object", "properties": {"coffre": {"type": "string", "description": "Cerveau Alix (défaut), Veralume, 79 Skills, Langage Vectoriel, Exocerveau Master."}}}},
    {"name": "alix_echantillon_cathedrale",
     "description": "Tire au hasard 1 à 10 documents dans les Parquet de la Cathédrale du Savoir (sérendipité).",
     "inputSchema": {"type": "object", "properties": {"n": {"type": "integer"}}}},
    {"name": "alix_compiler_matiere",
     "description": ("Compilateur de matière LP (scénario prospectif VERALUME) : répartit des grammes de déchets (C, H, O, N, Si, Fe, Cl) en molécules utiles "
                     "selon un profil de besoin, sous conservation de la masse et plafond thermique."),
     "inputSchema": {"type": "object", "properties": {
         "dechets_g": {"type": "object"}, "profil": {"type": "string", "enum": ["NUTRITION", "HYDRATATION", "CONSTRUCTION"]},
         "plafond_W": {"type": "number"}}, "required": ["dechets_g"]}},
    {"name": "alix_lmh_verifier",
     "description": "Lance la suite de preuves formelles de LMH v3 (actes de langage, réécriture québécoise, fidélité) et dit si elle tient.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "alix_calculer_exact",
     "description": ("Calculatrice exacte & auditeur Lean 4 déterministe (AST Fraction, SymPy, analyse dimensionnelle vectorielle, "
                     "logique propositionnelle, audit Lean 4, et couplage optionnel à alix_math_lean_60m.pt). Remplace tout calcul mental."),
     "inputSchema": {"type": "object", "properties": {
         "expression": {"type": "string", "description": "Expression arithmétique, équation, inégalité, calcul physique ('40 Go / 8 s', '25 W + 40 ms'), formule booléenne ou code Lean 4."},
         "mode": {"type": "string", "enum": ["auto", "arithmetique", "sympy", "dimensionnel", "logique", "auditer_lean4", "generer_lean4"]},
         "action": {"type": "string", "enum": ["auto", "resoudre", "inegalite", "developper", "factoriser", "simplifier", "deriver", "integrer", "verifier_egalite"]},
         "variable": {"type": "string", "description": "Variable symbolique (ex. 'x', 'u')."},
         "vers_unite": {"type": "string", "description": "Unité cible pour conversion ou expression physique (ex. 'Mo', 'Mo/s', 'W')."},
         "premisses": {"type": "array", "description": "Liste de formules logiques prémisses (ex. ['P -> Q', '~Q'])."},
         "conclusion": {"type": "string", "description": "Conclusion logique à vérifier (ex. '~P')."},
         "utiliser_57m": {"type": "boolean", "description": "Si true en mode 'generer_lean4', génère le théorème avec alix_math_lean_60m.pt puis l'audite sous SymPy."}
     }}},
]
NOMS_METAL = {d["name"] for d in DEFINITIONS_METAL}

_FONCTIONS = {
    "alix_resoudre_contraintes": resoudre_contraintes,
    "alix_inferer_causal": inferer_causal,
    "alix_optimiser_lineaire": optimiser_lineaire,
    "alix_ponts_caches": ponts_caches,
    "alix_recherche_lexicale": recherche_lexicale,
    "alix_deduire": deduire,
    "alix_poles_emergents": poles_emergents,
    "alix_audit_coffre": audit_coffre,
    "alix_echantillon_cathedrale": echantillon_cathedrale,
    "alix_compiler_matiere": compiler_matiere,
    "alix_lmh_verifier": lmh_verifier,
    "alix_calculer_exact": calculer_exact,
}


def executer_metal(nom: str, args: Dict[str, Any]) -> str:
    """Point d'entrée unique depuis executer_outil : renvoie un texte JSON lisible."""
    try:
        res = _FONCTIONS[nom](args or {})
    except Exception as e:
        res = {"statut": "ERREUR", "message": f"{type(e).__name__}: {e}"}
    return json.dumps(res, ensure_ascii=False, indent=1, default=str)
