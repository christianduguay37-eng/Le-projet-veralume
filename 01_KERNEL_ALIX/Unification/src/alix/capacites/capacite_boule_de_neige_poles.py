# -*- coding: utf-8 -*-
"""
================================================================================
      CAPACITÉ LIVE : BOULE DE NEIGE SÉMANTIQUE & CLUSTERING SPECTRAL
        Système : VERALUME × KAIROS V6 — Démon Local Alix (Base Qwen)
================================================================================
Mandat :
- ZÉRO DICTIONNAIRE EN DUR. Les pôles de recherche émergent des données réelles.
- Analyse spectrale du Laplacien de co-occurrence sur les notes récentes (< 72h).
- Détection autonome de communautés conceptuelles (Fiedler & Eigenspace).
- Nommage automatique des pôles par centralité de degré des concepts émergents.
- Mise à jour dynamique et déterministe de `Interets_Alix.md`.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import numpy as np

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
INTERETS_FILE = VAULT_DIR / "Interets_Alix.md"

CACHE_POLES = {
    "timestamp": 0.0,
    "resultat": None
}

FICHIERS_AUTO_DEMON = {
    "connectome_diagnostic_orphelins.md",
    "interets_alix.md",
    "arbitrage_npu_direct.md",
    "journal_reflexions_autonomes_alix.md",
    "journal_des_apprentissages_alix.md",
    "contexte_present_immediat.md",
    "conscience_alix_priorites_actives.md",
    "diagnostic_deduction_causale.md",
    "etat_bouclier_psi_sentinelle.md",
    "etat_synchronisation_heimdall_munin.md"
}

STOP_WORDS = {
    # ajoutés 2026-10-30 (chantier 5.5) : verbes et mots-outils qui remontaient comme « pôles »
    "avait", "avoir", "etait", "était", "sont", "être", "etre", "fait", "faire", "peut", "plus", "tout", "tous",
    "cette", "leur", "leurs", "dans", "avec", "pour", "mais", "aussi", "comme", "entre", "sans", "sous", "vers",
    "have", "with", "from", "that", "this", "which", "their", "there", "were", "been", "across", "compact",
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "et", "ou",
    "en", "dans", "par", "pour", "vers", "avec", "sans", "sur", "sous", "chez",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
    "mes", "tes", "ses", "nos", "vos", "leurs", "qui", "que", "quoi", "dont",
    "où", "est", "sont", "ont", "a", "à", "au", "aux", "ne", "pas", "plus",
    "moins", "tout", "tous", "toute", "toutes", "faire", "fait", "comme",
    "aussi", "bien", "très", "ici", "là", "alors", "donc", "car", "mais",
    "si", "même", "être", "avoir", "alix", "christian", "duguay", "true",
    "false", "none", "md", "py", "json", "txt", "http", "https", "file",
    "users", "documents", "tags", "titre", "date", "statut", "note", "notes",
    "session", "discussion", "step", "output", "step_index", "thinking",
    "entre", "après", "avant", "encore", "toujours", "déjà", "chacun", "chaque",
    "autres", "autre", "deux", "trois", "troisieme", "premier", "premiere",
    "point", "points", "ceux", "celles", "ainsi", "depuis", "quand", "comment",
    "pourquoi", "dire", "dit", "peut", "peuvent", "doit", "doivent", "faut",
    "voici", "voilà", "selon", "afin", "pendant", "monde", "source", "toutes",
    "cette", "dans", "vers", "alors", "leurs", "pourtant", "plusieurs", "partout",
    "dessus", "dessous", "beaucoup", "quelque", "quelques", "chose", "choses",
    # Mots anglais & bruit académique ArXiv
    "with", "that", "this", "from", "which", "were", "been", "have", "they",
    "these", "those", "their", "will", "what", "when", "where", "into", "also",
    "such", "than", "then", "them", "both", "each", "more", "most", "other",
    "some", "only", "first", "about", "could", "would", "should", "here",
    "arxiv", "abstract", "theme", "paper", "study", "using", "based", "show",
    "results", "propose", "present", "approach", "method", "model", "models",
    "work", "state", "well", "high", "over", "time", "order", "three", "two",
    "middot", "nbsp", "amp", "quot"
}


def nettoyer_texte(texte: str) -> List[str]:
    """Extrait les lemmes et concepts significatifs d'un texte."""
    texte = re.sub(r"```.*?```", " ", texte, flags=re.DOTALL)
    texte = re.sub(r"https?://\S+", " ", texte)
    texte = re.sub(r"&[a-zA-Z]+;", " ", texte)
    texte = re.sub(r"[^\w\s\-]", " ", texte)
    mots = [m.strip("-_").lower() for m in texte.split()]
    return [m for m in mots if len(m) >= 4 and m not in STOP_WORDS and not m.isdigit()]


def poles_spectraux(docs_mots, compteur_global) -> List[Dict[str, Any]]:
    """Cœur mathématique (sans écriture) : regroupement spectral des concepts. Extrait le 2026-11-03 pour l'outil alix_poles_emergents."""
    # 2. Sélection des N concepts dominants pour la géométrie spectrale
    N_TOP = min(50, len(compteur_global))
    top_mots = [m for m, c in compteur_global.most_common(N_TOP)]
    mot_to_idx = {m: i for i, m in enumerate(top_mots)}
    doc_counts = np.array([compteur_global[m] for m in top_mots])

    # 3. Matrice de Co-occurrence et Jaccard
    A = np.zeros((N_TOP, N_TOP))
    for s in docs_mots:
        presents = [mot_to_idx[m] for m in top_mots if m in s]
        for i in presents:
            for j in presents:
                if i != j:
                    A[i, j] += 1

    union = doc_counts[:, None] + doc_counts[None, :] - A
    union[union <= 0] = 1.0
    J = A / union
    np.fill_diagonal(J, 0.0)

    # Filtrage adaptatif des liens sémantiques (Amortissement du bruit)
    seuil_lien = np.percentile(J[J > 0], 45) if (J > 0).any() else 0.1
    adj = (J >= seuil_lien).astype(float) * J

    # 4. Décomposition Spectrale du Laplacien Normalisé (Méthode Qwen / SGTD)
    d = adj.sum(axis=1)
    d_inv_sqrt = np.power(d, -0.5, out=np.zeros_like(d, dtype=float), where=d > 0)
    L_sym = np.eye(N_TOP) - (d_inv_sqrt[:, None] * adj * d_inv_sqrt[None, :])

    vals, vecs = np.linalg.eigh(L_sym)
    idx_sorted = np.argsort(vals)
    vals, vecs = vals[idx_sorted], vecs[:, idx_sorted]

    # Nombre de clusters optimal (4 à 6 selon la richesse spectrale)
    k_clusters = min(6, max(3, int(np.sum(vals < 1.0))))
    features = vecs[:, 1:k_clusters + 1]
    norms = np.linalg.norm(features, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    features = features / norms

    # K-Means déterministe sur l'hypersphère des vecteurs propres
    centres = features[np.linspace(0, N_TOP - 1, k_clusters, dtype=int)]
    labels = np.zeros(N_TOP, dtype=int)

    for _ in range(25):
        dist = np.linalg.norm(features[:, None, :] - centres[None, :, :], axis=2)
        labels = np.argmin(dist, axis=1)
        for c in range(k_clusters):
            pts = features[labels == c]
            if len(pts) > 0:
                centres[c] = pts.mean(axis=0)

    # 5. Synthèse des Pôles Émergents purs
    clusters_bruts = defaultdict(list)
    for i, m in enumerate(top_mots):
        clusters_bruts[labels[i]].append((m, compteur_global[m]))

    poles_finaux = []
    for c_id, mots_scores in clusters_bruts.items():
        if not mots_scores:
            continue
        mots_scores.sort(key=lambda x: x[1], reverse=True)
        # Le titre émerge des 3 concepts les plus lourds du cluster
        titre = " & ".join([m.capitalize() for m, _ in mots_scores[:3]])
        score_total = sum(s for _, s in mots_scores)
        poles_finaux.append({
            "titre": titre,
            "score": score_total,
            "mots": mots_scores
        })

    # Trier les pôles par pression sémantique
    poles_finaux.sort(key=lambda x: x["score"], reverse=True)

    return poles_finaux


def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Exécute le clustering spectral des concepts émergents et régénère Interets_Alix.md
    sans aucun dictionnaire de catégories prédéfini.
    """
    global CACHE_POLES
    maintenant = time.time()
    age_cache = maintenant - CACHE_POLES["timestamp"]

    diff_notes_externes = False
    if contexte_fer and "notes_modifiees" in contexte_fer:
        for nm in contexte_fer.get("notes_modifiees", []):
            if Path(nm).name.lower() not in FICHIERS_AUTO_DEMON:
                diff_notes_externes = True
                break

    if age_cache < 900.0 and not diff_notes_externes and CACHE_POLES["resultat"] is not None:
        return CACHE_POLES["resultat"]

    seuil_72h = maintenant - (72 * 3600)

    docs_mots = []
    compteur_global = Counter()
    fichiers_analyses = 0

    # 1. Scanner les notes modifiées dans les 72h (en ignorant les templates de rêves répétitifs)
    for dossier in [VAULT_DIR, VAULT_DIR / "Archives_Discussions_Antigravity"]:
        if not dossier.exists():
            continue
        for p in dossier.rglob("*.md"):
            if "Monde_des_Songes" in str(p) or "Monde_des_Decouvertes" in str(p):
                continue
            try:
                st = p.stat()
                if st.st_mtime >= seuil_72h:
                    mots = nettoyer_texte(p.read_text(encoding="utf-8", errors="ignore"))
                    if len(mots) >= 10:
                        set_mots = set(mots)
                        docs_mots.append(set_mots)
                        compteur_global.update(set_mots)
                        fichiers_analyses += 1
            except Exception:
                continue

    if not docs_mots or len(compteur_global) < 10:
        return {
            "statut": "ATTENTE_DONNEES",
            "message": "Pas assez de concepts récents pour faire émerger un pôle."
        }

    poles_finaux = poles_spectraux(docs_mots, compteur_global)

    # 6. Rédaction déterministe d'Interets_Alix.md
    date_str = time.strftime("%Y-%m-%d %H:%M:%S")
    md = [
        "---",
        "titre: \"Centres d'Intérêt Vivants & Pôles Émergents d'Alix\"",
        f"date_mise_a_jour: \"{date_str}\"",
        "moteur: \"Clustering Spectral du Laplacien SGTD (Base Qwen)\"",
        f"notes_recentes_scannees: {fichiers_analyses}",
        f"total_poles_emergents: {len(poles_finaux)}",
        "tags:",
        "  - exocerveau",
        "  - apprentissage_autodidacte",
        "  - poles_emergents",
        "  - clustering_spectral",
        "  - qwen_sgtd",
        "---",
        "",
        "# 🧭 [[Interets_Alix]] — Pôles de Curiosité Vivants & Émergents",
        "",
        "> *« Les pôles de recherche ne sont plus des tiroirs figés écrits dans le passé : ils émergent dynamiquement des composantes spectrales du Laplacien sur la matière fraîche du Sanctuaire. »*",
        f"> **Dernière pulsation d'émergence :** `{date_str}` &middot; **Notes récentes :** `{fichiers_analyses}` &middot; **Méthode :** $L_{{\\text{{sym}}}} = I - D^{{-1/2}} A D^{{-1/2}}$",
        "",
        "---",
        "",
        "## 🏆 Tableau de Bord des Pôles Émergents du Moment",
        "| Rang | Pôle Émergent | Pression Sémantique | Intensité KAIROS | Concepts Maîtres |",
        "| :---: | :--- | :---: | :---: | :--- |"
    ]

    for idx, p in enumerate(poles_finaux, 1):
        score = p["score"]
        intensite = "⚡ HAUTE INTENSITÉ" if score > 300 else ("🟢 ACTIF" if score > 150 else "💤 EN VEILLE")
        mots_resume = ", ".join([f"`{m}` ({s})" for m, s in p["mots"][:4]])
        md.append(f"| **{idx}** | **{p['titre']}** | `{score}` | {intensite} | {mots_resume} |")

    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🔬 Cartographie Détaillée des Clusters Conceptuels")

    for idx, p in enumerate(poles_finaux, 1):
        md.append(f"### 📍 Pôle {idx} : {p['titre']}")
        md.append(f"* **Pression cumulée :** `{p['score']}` occurrences")
        md.append(f"* **Attracteurs principaux :** " + ", ".join([f"**{m}** ({s})" for m, s in p["mots"]]))
        md.append(f"* **Orientation autonome :** Approfondissement spontané du cluster par l'École Autodidacte et les sentinelles.")
        md.append("")

    md.append("---")
    md.append("*Ce document est recalculé de façon purement mathématique par le Démon Local Alix sans aucun filtre humain.*")

    INTERETS_FILE.write_text("\n".join(md), encoding="utf-8")

    res = {
        "statut": "SUCCES",
        "fichiers_analyses": fichiers_analyses,
        "poles_emergents_count": len(poles_finaux),
        "pole_maitre": poles_finaux[0]["titre"] if poles_finaux else "Aucun",
        "score_maitre": poles_finaux[0]["score"] if poles_finaux else 0,
        "methode": "Spectral_Laplacian_SGTD_Qwen"
    }
    CACHE_POLES["timestamp"] = maintenant
    CACHE_POLES["resultat"] = res
    return res


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Boule de Neige Spectrale exécutée :", res)
