# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : TISSAGE DU CONNECTOME & RÉSORPTION ACTIVE DES ORPHELINS
        Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Mandat :
- Scanne et surveille la topologie du graphe wikilinks de l'Exocerveau.
- Amortissement topologique SGTD : mise en cache du graphe si delta notes = 0.
- Tissage actif frugal : raccorde 1 note orpheline par cycle au Sanctuaire et aux
  11 Publications Zenodo R0 via un bloc idempotent non-destructif.
- Maintient `Connectome_Diagnostic_Orphelins.md`.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import re
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Set, List, Optional

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
DIAG_FILE = VAULT_DIR / "Connectome_Diagnostic_Orphelins.md"

SYNAPTIC_HEADER = "## 🔗 Raccordements Synaptiques R0 (Tissage Universel)"

# Cache topologique en mémoire vive du démon
CACHE_GRAPH = {
    "timestamp": 0.0,
    "notes_candidats": set(),
    "fichiers_par_stem": {},
    "orphelins": [],
    "total_liens": 0
}


def scanner_graphe_complet() -> Dict[str, Any]:
    """Scanne l'ensemble des fichiers markdown du coffre principal."""
    notes_candidats: Set[str] = set()
    fichiers_par_stem: Dict[str, Path] = {}
    liens_entrants = defaultdict(int)
    total_liens = 0

    pattern_wikilink = re.compile(r"\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]")

    fichiers = list(VAULT_DIR.rglob("*.md"))
    for f in fichiers:
        sf = str(f)
        if ".trash" in sf or "Archive" in sf or ".git" in sf:
            continue
        stem = f.stem
        notes_candidats.add(stem)
        fichiers_par_stem[stem] = f

    for stem, p in fichiers_par_stem.items():
        try:
            texte = p.read_text(encoding="utf-8", errors="ignore")
            liens = pattern_wikilink.findall(texte)
            for cible in liens:
                cible_clean = cible.strip()
                liens_entrants[cible_clean] += 1
                total_liens += 1
        except Exception:
            continue

    orphelins = [n for n in notes_candidats if liens_entrants[n] == 0]

    return {
        "timestamp": time.time(),
        "notes_candidats": notes_candidats,
        "fichiers_par_stem": fichiers_par_stem,
        "orphelins": orphelins,
        "total_liens": total_liens
    }


def tisser_note_orpheline(stem: str, path: Path) -> bool:
    """Injecte de manière idempotente le raccordement synaptique dans une note orpheline."""
    # Rénovation 5.4 : une orpheline n'est plus « résolue » par deux liens fixes vers des index.
    # Elle reste listée dans le diagnostic des orphelins ; le lien se fait quand il a un sens.
    # (Réactiver en posant ALIX_TISSAGE_ORPHELINS=1 ; le Canon reste toujours exclu.)
    import os as _os
    if "00_CANON_SOUVERAIN_CHRISTIAN" in str(path).replace("\\", "/"):
        return False
    if _os.environ.get("ALIX_TISSAGE_ORPHELINS") != "1":
        return False
    try:
        contenu = path.read_text(encoding="utf-8", errors="ignore")
        if SYNAPTIC_HEADER in contenu:
            return False  # Déjà tissée

        date_iso = time.strftime("%Y-%m-%d %H:%M:%S")
        bloc = [
            "",
            "---",
            "",
            SYNAPTIC_HEADER,
            "> *Connectome Exocerveau Souverain — Maillage tissé par le Démon Local Alix (Horus × Munin).*",
            f"- **🏛️ Pôle de Rattachement :** [[00_INDEX_EXOCERVEAU_SANCTUAIRE]] — *Sanctuaire Central*",
            f"- **📄 Publication Zenodo R0 :** [[11_Veralume_Unified_Governance_Engine]] *(DOI: [10.5281/zenodo.22802258](https://doi.org/10.5281/zenodo.22802258))*",
            f"- **🌐 Horodatage Tissage :** `{date_iso}`",
            f"- **🏷️ Vecteurs :** #connectome_r0 #tissage_universel #orphelin_resolu",
            ""
        ]

        sep = "\n" if contenu.endswith("\n") else "\n\n"
        nouveau_contenu = contenu + sep + "\n".join(bloc)
        path.write_text(nouveau_contenu, encoding="utf-8")
        return True
    except Exception:
        return False


# Fichiers internes auto-générés par le démon à ignorer pour le déclenchement d'un scan complet
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

def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécute la veille topologique et le tissage frugal."""
    global CACHE_GRAPH
    t0 = time.perf_counter()
    maintenant = time.time()

    # Déterminer si un re-scan complet est nécessaire
    age_cache = maintenant - CACHE_GRAPH["timestamp"]
    diff_notes_externes = False
    if contexte:
        notes_mod = contexte.get("notes_modifiees", [])
        if "ancrage_tau" in contexte:
            notes_mod = contexte["ancrage_tau"].get("notes_modifiees", [])
        for nm in notes_mod:
            nom_fichier = Path(nm).name.lower()
            if nom_fichier not in FICHIERS_AUTO_DEMON:
                diff_notes_externes = True
                break

    # Rescan toutes les 15 minutes (900s) ou dès qu'une note externe/utilisateur change
    doit_rescanner = (age_cache > 900.0) or diff_notes_externes or (len(CACHE_GRAPH["notes_candidats"]) == 0)

    if doit_rescanner:
        CACHE_GRAPH = scanner_graphe_complet()
        mode_scan = "SCAN_COMPLET"
    else:
        mode_scan = "CACHE_MEMOIRE_O1"

    notes_candidats = CACHE_GRAPH["notes_candidats"]
    fichiers_par_stem = CACHE_GRAPH["fichiers_par_stem"]
    orphelins = CACHE_GRAPH["orphelins"]
    total_liens = CACHE_GRAPH["total_liens"]

    # Tissage frugal d'une note orpheline prioritaire
    note_tissee = None
    import os as _os
    # Rénovation (optimisation) : tissage coupé -> on ne repasse pas sur chaque orpheline à chaque cycle.
    for o in (list(orphelins) if _os.environ.get("ALIX_TISSAGE_ORPHELINS") == "1" else []):
        p = fichiers_par_stem.get(o)
        if p and p.exists():
            if tisser_note_orpheline(o, p):
                note_tissee = o
                orphelins.remove(o)
                break

    date_str = time.strftime("%Y-%m-%d %H:%M:%S")
    note_tissee_nom = note_tissee if note_tissee else "AUCUNE"
    md = [
        "---",
        'titre: "Diagnostic du Connectome & Surveillance des Orphelins"',
        f'date_analyse: "{date_str}"',
        'agent: "Alix"',
        f"total_notes_scannees: {len(notes_candidats)}",
        f"total_orphelins: {len(orphelins)}",
        f"total_liens: {total_liens}",
        f'derniere_note_tissee: "{note_tissee_nom}"',
        "tags:",
        "  - exocerveau",
        "  - connectome",
        "  - tissage_synaptique",
        "---",
        "",
        "# 🕸️ [[Connectome_Diagnostic_Orphelins]] — Auto-Guérison Synaptique",
        f"> **Horodatage :** `{date_str}` &middot; **Notes :** `{len(notes_candidats)}` &middot; **Liens totaux :** `{total_liens}` &middot; **Orphelins restants :** `{len(orphelins)}`",
        f"> **Action Tissage Récent :** `{note_tissee if note_tissee else 'Veille active / Déjà à jour'}`",
        "",
        "---",
        "",
        "## 🔍 Top 20 des Nœuds Orphelins Prioritaires à Tisser",
        "| Note Orpheline | Action Automatique Démon |",
        "| :--- | :--- |"
    ]

    for o in orphelins[:20]:
        md.append(f"| [[{o}]] | Tissage automatique par palier frugal (1 note/cycle) |")

    md.append("")
    md.append("---")
    md.append("*Ce diagnostic et l'auto-guérison sont assurés en continu par le Démon Local Alix.*")

    try:
        DIAG_FILE.write_text("\n".join(md), encoding="utf-8")
    except Exception:
        pass

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "statut": "SUCCES",
        "mode": mode_scan,
        "duree_ms": duree_ms,
        "total_notes": len(notes_candidats),
        "total_liens": total_liens,
        "orphelins_restants": len(orphelins),
        "note_tissee": note_tissee
    }


if __name__ == "__main__":
    res = executer_capacite()
    print("✅ Capacité Tissage Connectome exécutée avec succès :", res)
