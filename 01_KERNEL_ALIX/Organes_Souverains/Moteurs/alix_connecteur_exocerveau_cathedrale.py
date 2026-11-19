#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
   🏛️🕸️ CONNECTEUR UNIFIÉ : EXOCERVEAU (4 COFFRES) × CATHÉDRALE (13 PILIERS)
   Moteur FTS5 Sans Diacritiques + Expansion Bilingue (< 3 ms — 100% Hors-Ligne)
================================================================================
Auteurs : Christian Duguay & Alix (Atelier Kairos — Rimouski)
Rôle :
  Relier en temps réel chaque parole de Christian dans `alix.py` (`ALIX.bat`) à :
  1. L'EXOCERVEAU COMPLET (Les 4 Coffres Obsidian — 5 884 notes) :
     - `Cerveau Alix` (Racine, Corpus Souverains, Monde des Découvertes [634],
       SAS Assimilation [230], Chroniques Pensée, Archives Discussions [191],
       Faisceaux Synaptiques, Topologie Pôles, Découvertes FrontierMath, Songes)
     - `Obsidian_Vault_Veralume` (389 notes)
     - `Obsidian_Vault_79_Skills` (93 notes)
     - `Obsidian_Vault_Langage_Vectoriel` (66 notes)
  2. LA CATHÉDRALE DU SAVOIR UNIVERSEL (Les 13 Piliers sur NVMe) :
     - Pilier 01 : `Arxiv_Souverain` (3,21 M preprints scientifiques)
     - Pilier 02 : `Invariants_Physiques` (`nist_constantes.db` + `oeis_souverain.db` 400k suites)
     - Pilier 03 : `03_Vivant_PubMed_BioRxiv` (55 000+ études médicales & longévité)
     - Pilier 04 : `04_Ingenierie_Brevets_USPTO` (35 000 brevets industriels)
     - Pilier 05 : `05_Preuves_Formelles_Lean4` (Théorèmes formels Lean 4)
     - Pilier 06 : `06_Temps_Profond_Gutenberg` (`gutenberg_souverain.db` 752 Mo FTS5 + Poincaré)
     - Pilier 07 : `07_MIT_Science_et_Cybernetique` (Traités MIT, OCW, Inventions Sci-Fi Technovelgy)
     - Pilier 08 : `08_Mythes_Legendes_Cosmogonies` (Cosmogonies KAIROS, Berezkin, Thompson, Theoi, Épopées)
     - Pilier 09 : `09_Savoirs_Pratiques_et_Traditions` (Québec Boréal, Ethnobotanique Moerman, PFAF, Bushcraft, D-PLACE, UNESCO, WikiHow)
     - Pilier 10 : `10_Matiere_Materiaux_et_Chimie` (Matériaux d'ingénierie & Chimie)
     - Pilier 11 : `11_Dynamique_Historique_et_Macro_Sociale` (Seshat Cliodynamique Turchin & Géopolitique)
     - Pilier 12 : `12_Heuristique_Innovation_et_Biomimetisme` (Matrice TRIZ Altshuller, Biomimétisme AskNature, Design Patterns)
     - Pilier 13 : `13_Geometrie_Semantique_et_Biais_Cognitifs` (FrameNet, Codex des Biais, Sophismes)
================================================================================
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VAULT_ALIX = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
COFFRES_OBSIDIAN: Dict[str, Path] = {
    "Cerveau Alix": VAULT_ALIX,
    "Veralume": Path(r"C:\Alix\SAUVEGARDE_ALIX\Obsidian_Vault_Veralume"),
    "79 Skills": Path(r"C:\Alix\SAUVEGARDE_ALIX\Obsidian_Vault_79_Skills"),
    "Langage Vectoriel": Path(r"C:\Alix\SAUVEGARDE_ALIX\Obsidian_Vault_Langage_Vectoriel"),
}

CATHEDRALE_DIR = VAULT_ALIX / "Cathedrale_du_Savoir_Universel"
INVARIANTS_DIR = VAULT_ALIX / "Invariants_Physiques"
ARXIV_DIR = VAULT_ALIX / "Arxiv_Souverain" / "data"

DOWNLOADS_ALIX = Path(r"C:\Alix\Etat_Vivant")
ALIX_ENGINE_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Exocerveau_Souverain_Master\Projet  Temporia\alix_engine")
INDEX_DB_PATH = ALIX_ENGINE_DIR / "alix_index_unifie_v2.sqlite"


def strip_accents(s: str) -> str:
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn"
    ).lower()


# Pont lexical Franco-Anglais pour interroger les tables anglaises de la Cathédrale (NIST, OEIS, BioRxiv, USPTO, MIT, Thompson...)
PONT_FR_EN: Dict[str, Tuple[str, ...]] = {
    "lumiere": ("light", "speed of light", "photon", "optical"),
    "vitesse": ("speed", "velocity", "fast"),
    "gravite": ("gravity", "gravitational", "newton"),
    "planck": ("planck", "quantum", "constant"),
    "electron": ("electron", "mass", "charge"),
    "proton": ("proton", "nuclear", "baryon"),
    "boltzmann": ("boltzmann", "entropy", "thermodynamic"),
    "avogadro": ("avogadro", "mole"),
    "constante": ("constant", "fundamental"),
    "suite": ("sequence", "numbers", "series"),
    "premier": ("prime", "primes"),
    "premiers": ("prime", "primes"),
    "fibonacci": ("fibonacci", "golden"),
    "longevite": ("longevity", "aging", "lifespan", "senescence", "rejuvenation"),
    "vieillissement": ("aging", "senescence", "longevity", "telomere"),
    "rajeunissement": ("rejuvenation", "regeneration", "bioelectric", "aging"),
    "cellule": ("cell", "cellular", "stem", "membrane"),
    "cancer": ("cancer", "tumor", "oncology"),
    "adn": ("dna", "crispr", "genome", "genetic"),
    "cerveau": ("brain", "neural", "synaptic", "cognitive", "memory"),
    "memoire": ("memory", "recall", "synaptic", "memex"),
    "conscience": ("consciousness", "mind", "awareness", "cognitive"),
    "eau": ("water", "purification", "filtration", "drinking"),
    "feu": ("fire", "ignition", "tinder", "flame", "prometheus"),
    "foret": ("forest", "bushcraft", "wilderness", "survival", "boreal"),
    "survie": ("survival", "bushcraft", "shelter", "water", "fire"),
    "abri": ("shelter", "tarp", "cabin", "survival"),
    "plante": ("plant", "medicinal", "edible", "herb", "flora"),
    "plantes": ("plants", "medicinal", "edible", "herbs"),
    "sapin": ("abies", "balsamea", "fir", "spruce", "resin"),
    "epinette": ("picea", "spruce", "boreal"),
    "bouleau": ("betula", "birch", "bark"),
    "cuivre": ("copper", "thermal", "conductivity"),
    "titane": ("titanium", "alloy"),
    "acier": ("steel", "iron", "carbon"),
    "aluminium": ("aluminum", "alloy"),
    "silicium": ("silicon", "semiconductor", "wafer", "3d"),
    "fusion": ("fusion", "plasma", "magnetic", "confinement", "frc", "tokamak"),
    "plasma": ("plasma", "magnetic", "fusion", "ion"),
    "aimant": ("magnet", "magnetic", "superconducting", "coil"),
    "supraconducteur": ("superconductor", "superconducting", "hts", "critical"),
    "mythe": ("myth", "mythology", "creation", "cosmogony", "gods"),
    "mythes": ("myths", "mythology", "creation", "cosmogony"),
    "deluge": ("flood", "deluge", "ark", "gilgamesh"),
    "promethee": ("prometheus", "fire", "titan"),
    "odin": ("odin", "yggdrasil", "runes", "mimir"),
    "gilgamesh": ("gilgamesh", "enkidu", "immortality"),
    "thot": ("thoth", "maat", "hermes", "writing"),
    "empire": ("empire", "civilization", "collapse", "turchin", "seshat"),
    "civilisation": ("civilization", "state", "complexity", "seshat"),
    "guerre": ("war", "conflict", "military", "peace"),
    "biais": ("bias", "cognitive", "fallacy", "heuristic"),
    "sophisme": ("fallacy", "rhetoric", "argument"),
    "invention": ("invention", "patent", "triz", "innovation"),
    "brevet": ("patent", "invention", "apparatus", "method"),
    "biomimetisme": ("biomimicry", "nature", "biological", "adaptation"),
    "temps": ("time", "temporal", "chronos", "kairos", "relativity"),
    "entropie": ("entropy", "thermodynamics", "information", "shannon"),
    "cybernetique": ("cybernetics", "feedback", "wiener", "control"),
    "aurele": ("aurelius", "stoicism", "meditations", "roman emperor"),
    "socrate": ("socrates", "plato", "athens"),
    "platon": ("plato", "republic", "timaeus"),
    "aristote": ("aristotle", "syllogism", "metaphysics"),
    "descartes": ("descartes", "cartesian", "method"),
    "poincare": ("poincare", "topology", "dynamical"),
}


class MoteurConnexionExocerveauCathedrale:
    """
    Moteur FTS5 unifié reliant les 4 Coffres de l'Exocerveau (5 884 notes) et
    les 13 Piliers de la Cathédrale du Savoir Universel en < 3 millisecondes.
    """

    MOTS_VIDES = {
        "dans", "pour", "avec", "tout", "tous", "toute", "toutes", "comme", "quoi",
        "comment", "pourquoi", "quand", "est-ce", "maintenant", "discuter", "quebecois",
        "modele", "marcher", "faire", "fait", "sont", "etre", "avoir", "plus", "moins",
        "cette", "ces", "mais", "donc", "alors", "parle", "parler", "explique", "expliquer",
        "dis-moi", "dire", "veux", "peux", "peut", "nous", "vous", "leur", "leurs",
        "notre", "votre", "meme", "bien", "tres", "aussi", "encore", "entre", "sans",
        "sous", "vers", "chez", "dont", "quel", "quelle", "quels", "quelles", "ecrit",
        "dit", "parle", "trouve", "cherche", "montre", "donne", "sujet", "affaire",
        "affaires", "chose", "choses", "quest", "qu'est", "qu'on", "quon", "c'est",
        "est", "ets", "sur", "les", "des", "une", "par", "aux", "son", "ses", "nos", "vos",
        "ton", "mon", "ont", "ete", "pas", "que", "qui", "oui", "non", "moi", "toi",
        "lui", "elle", "elles", "eux", "savoir", "cathedrale", "exocerveau", "alix",
        "christian", "dis", "moi", "un", "le", "la", "de", "du", "au", "en", "et", "ou",
    }

    FICHIERS_INDEX_EXCLUS = {
        "00_Grande_Classification_Bibliothecaire_KAIROS.md",
        "00_Index_Vectoriel_Topologique.md",
        "00_Index_Topologique_Maitre_4_Coffres.md",
        "garbage.md",
    }

    def __init__(self, db_path: Path = INDEX_DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialiser_ou_ouvrir()

    def _initialiser_ou_ouvrir(self) -> None:
        doit_construire = not self.db_path.exists() or self.db_path.stat().st_size < 1024 * 100
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        if doit_construire:
            self.construire_index_complet()
        else:
            # Vérifie que les tables existent et contiennent des données
            try:
                c_exo = self.conn.execute("SELECT count(*) FROM exocerveau_fts").fetchone()[0]
                c_cat = self.conn.execute("SELECT count(*) FROM cathedrale_fts").fetchone()[0]
                if c_exo < 500 or c_cat < 500:
                    self.construire_index_complet()
            except Exception:
                self.construire_index_complet()

    def construire_index_complet(self, silencieux: bool = False) -> Dict[str, int]:
        """
        Construit l'index FTS5 complet :
          1. Les 4 Coffres Obsidian (Exocerveau)
          2. Les 13 Piliers de la Cathédrale du Savoir Universel
        """
        t0 = time.perf_counter()
        if not silencieux:
            print("⚡ [Index Unifié] Soudure des 4 Coffres Obsidian & des 13 Piliers de la Cathédrale en FTS5...")

        cur = self.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS exocerveau_fts")
        cur.execute("DROP TABLE IF EXISTS cathedrale_fts")
        cur.execute("DROP TABLE IF EXISTS meta_index")

        cur.execute(
            """
            CREATE VIRTUAL TABLE exocerveau_fts USING fts5(
                coffre,
                fichier,
                section,
                texte,
                liens,
                priorite UNINDEXED,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        cur.execute(
            """
            CREATE VIRTUAL TABLE cathedrale_fts USING fts5(
                pilier,
                source,
                titre,
                texte,
                extra,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        cur.execute("CREATE TABLE meta_index (cle TEXT PRIMARY KEY, valeur TEXT)")

        nb_blocs_exo = self._indexer_4_coffres_obsidian(cur)
        nb_blocs_cat = self._indexer_13_piliers_cathedrale(cur)

        cur.execute("INSERT INTO meta_index VALUES ('last_build_ts', ?)", (str(time.time()),))
        cur.execute("INSERT INTO meta_index VALUES ('nb_blocs_exo', ?)", (str(nb_blocs_exo),))
        cur.execute("INSERT INTO meta_index VALUES ('nb_blocs_cat', ?)", (str(nb_blocs_cat),))
        self.conn.commit()

        dt_s = round(time.perf_counter() - t0, 2)
        if not silencieux:
            print(f"✅ [Index Unifié] {nb_blocs_exo} blocs Exocerveau + {nb_blocs_cat} entrées Cathédrale soudés en {dt_s} s !")
        return {"exocerveau_blocs": nb_blocs_exo, "cathedrale_entrees": nb_blocs_cat}

    def _indexer_4_coffres_obsidian(self, cur: sqlite3.Cursor) -> int:
        batch: List[Tuple[str, str, str, str, str, int]] = []
        total = 0

        fichiers_maitres = {
            "Memoire_Alix_Active.md",
            "Table_Solutions_et_Clefs_Critiques.md",
            "Conscience_Alix_Priorites_Actives.md",
            "Derniere_Discussion_Synthese.md",
            "00_PANTHEON_ISA_OPERATEURS_CPU.md",
            "TEMPORIA.md",
            "Solutions_Contournement_Verrous_Fusion_FRC_HTS.md",
            "Preprint_ArXiv_Direct_Inductive_Fusion_FRC_HTS.md",
            "MEMO_STRATEGIQUE_CAMPAGNE_PQ_2026.md",
            "Theorie_du_Tout_Reel_Matiere_Vivante_et_Present_Vibrant.md",
            "Theorie_Universelle_Regeneration_Biologique_Continue_VERALUME.md",
        }

        for nom_coffre, path_coffre in COFFRES_OBSIDIAN.items():
            if not path_coffre.exists():
                continue

            tous_md = list(path_coffre.rglob("*.md"))
            # Pour Monde_des_Songes (3 817 fichiers), on garde les 250 plus récents pour que l'index reste ultra-dense et vif
            songes_dir = path_coffre / "Monde_des_Songes"
            if songes_dir.exists():
                autres_md = [p for p in tous_md if "Monde_des_Songes" not in str(p) and "_Archives" not in str(p)]
                songes_md = sorted(
                    [p for p in tous_md if "Monde_des_Songes" in str(p)],
                    key=lambda x: x.name,
                    reverse=True,
                )[:250]
                liste_finale = autres_md + songes_md
            else:
                liste_finale = [p for p in tous_md if "_Archives" not in str(p)]

            for doc in liste_finale:
                if doc.name in self.FICHIERS_INDEX_EXCLUS:
                    continue
                try:
                    texte = doc.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel_path = str(doc.relative_to(path_coffre)).replace("\\", "/")
                dossier_parent = rel_path.split("/")[0] if "/" in rel_path else "Racine"

                priorite = 3 if doc.name in fichiers_maitres else (2 if dossier_parent in ("Racine", "Corpus_Souverains", "Monde_des_Decouvertes", "Chroniques_Pensee") else 1)

                paragraphes = re.split(r"\n\s*\n|\n(?=- 202[56]-|###?\s)", texte)
                titre_section = doc.stem
                for p in paragraphes:
                    p_clean = p.strip()
                    if not p_clean or p_clean.startswith("---"):
                        continue
                    if p_clean.startswith("#"):
                        titre_section = re.sub(r"^#+\s*", "", p_clean.splitlines()[0]).strip()[:90]
                        if len(p_clean.splitlines()) <= 1:
                            continue
                    if len(p_clean) < 40:
                        continue

                    liens = ", ".join(re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", p_clean)[:6])
                    extrait_net = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", p_clean)
                    extrait_net = re.sub(r"\[\[([^\]]+)\]\]", r"\1", extrait_net)
                    if len(extrait_net) > 700:
                        extrait_net = extrait_net[:700] + "…"

                    batch.append((f"{nom_coffre} ({dossier_parent})", doc.name, titre_section, extrait_net, liens, priorite))
                    total += 1
                    if len(batch) >= 2000:
                        cur.executemany("INSERT INTO exocerveau_fts VALUES (?, ?, ?, ?, ?, ?)", batch)
                        batch.clear()

        if batch:
            cur.executemany("INSERT INTO exocerveau_fts VALUES (?, ?, ?, ?, ?, ?)", batch)
            batch.clear()
        return total

    def _indexer_13_piliers_cathedrale(self, cur: sqlite3.Cursor) -> int:
        import pyarrow.parquet as pq

        batch: List[Tuple[str, str, str, str, str]] = []
        total = 0

        def push(pilier: str, source: str, titre: str, texte: str, extra: str = "") -> None:
            nonlocal total
            if not texte or len(str(texte).strip()) < 10:
                return
            batch.append((pilier, str(source)[:100], str(titre)[:140], str(texte)[:650], str(extra)[:200]))
            total += 1
            if len(batch) >= 3000:
                cur.executemany("INSERT INTO cathedrale_fts VALUES (?, ?, ?, ?, ?)", batch)
                batch.clear()

        # 1. Indexation des notes .md de la Cathédrale (MIT-01..10, MYTH-01..10, etc.)
        if CATHEDRALE_DIR.exists():
            for md_file in CATHEDRALE_DIR.rglob("*.md"):
                try:
                    txt = md_file.read_text(encoding="utf-8", errors="ignore").strip()
                    pilier_nom = md_file.relative_to(CATHEDRALE_DIR).parts[0]
                    push(pilier_nom, "Traité Fondateur Cathédrale", md_file.stem, txt, "Texte Souverain Intégral")
                except Exception:
                    pass

        # 2. Pilier 10 : Matériaux & Chimie
        p10 = CATHEDRALE_DIR / "10_Matiere_Materiaux_et_Chimie" / "data"
        if p10.exists():
            for pf in p10.glob("*.parquet"):
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "nom_materiau" in tb:
                        for i in range(len(tb["nom_materiau"])):
                            push("Pilier 10 (Matériaux & Chimie)", f"Matériau [{tb['classe_materiau'][i]}]", tb["nom_materiau"][i], tb["texte_complet"][i], f"Usage: {tb['applications'][i]}")
                    elif "nom_chimique" in tb:
                        for i in range(len(tb["nom_chimique"])):
                            push("Pilier 10 (Matériaux & Chimie)", f"Chimie [{tb['formule_brute'][i]}]", tb["nom_chimique"][i], tb["texte_complet"][i], f"Sécurité: {tb['neutralisation_securite'][i]}")
                except Exception:
                    pass

        # 3. Pilier 11 : Histoire, Cliodynamique Seshat & Géopolitique
        p11 = CATHEDRALE_DIR / "11_Dynamique_Historique_et_Macro_Sociale" / "data"
        if p11.exists():
            for pf in p11.glob("*.parquet"):
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "region_nga" in tb:
                        for i in range(len(tb["region_nga"])):
                            push("Pilier 11 (Histoire & Seshat)", f"Cliodynamique Seshat ({tb['annee_historique'][i]})", f"{tb['entite_politique'][i]} — {tb['region_nga'][i]}", tb["texte_complet"][i], f"Complexité: {tb['niveau_complexite'][i]}")
                    elif "pays_ou_acteur" in tb:
                        for i in range(len(tb["pays_ou_acteur"])):
                            push("Pilier 11 (Histoire & Géopolitique)", f"{tb['nature_donnee'][i]} ({tb['annee'][i]})", tb["pays_ou_acteur"][i], tb["texte_complet"][i], tb["indicateurs"][i])
                except Exception:
                    pass

        # 4. Pilier 12 : Innovation TRIZ, Design Patterns & Biomimétisme
        p12 = CATHEDRALE_DIR / "12_Heuristique_Innovation_et_Biomimetisme" / "data"
        if p12.exists():
            for pf in p12.glob("*.parquet"):
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "parametre_a_ameliorer_nom" in tb:
                        for i in range(len(tb["parametre_a_ameliorer_nom"])):
                            push("Pilier 12 (TRIZ & Innovation)", "Matrice TRIZ d'Altshuller", f"Améliorer {tb['parametre_a_ameliorer_nom'][i]} sans dégrader {tb['parametre_degrade_nom'][i]}", tb["principes_recommandes_texte"][i], tb["texte_complet"][i])
                    elif "nom" in tb and "invariant" in tb:
                        for i in range(len(tb["nom"])):
                            push("Pilier 12 (Patterns Architecture)", f"Design Pattern [{tb['domaine'][i]}]", tb["nom"][i], f"Problème : {tb['probleme'][i]} | Solution : {tb['solution'][i]}", f"Invariant : {tb['invariant'][i]}")
                    elif "organisme_ou_sujet" in tb:
                        # Échantillon riche des 2 500 premières stratégies biomimétiques
                        n_rows = min(len(tb["organisme_ou_sujet"]), 2500)
                        for i in range(n_rows):
                            push("Pilier 12 (Biomimétisme AskNature)", f"Biomimétisme ({tb['organisme_ou_sujet'][i]})", tb["probleme_ou_requete"][i], tb["strategie_biologique_et_resolution"][i], "Ingénierie inspirée du vivant")
                except Exception:
                    pass

        # 5. Pilier 13 : Géométrie Sémantique, Biais Cognitifs & Sophismes
        p13 = CATHEDRALE_DIR / "13_Geometrie_Semantique_et_Biais_Cognitifs" / "data"
        if p13.exists():
            for pf in p13.glob("*.parquet"):
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "nom_biais" in tb:
                        for i in range(len(tb["nom_biais"])):
                            push("Pilier 13 (Biais & Sophismes)", f"Codex Biais Cognitif ({tb['quadrant_benson'][i]})", tb["nom_biais"][i], f"Déformation : {tb['deformation_mentale'][i]}", f"Antidote : {tb['antidote_debiaisement'][i]}")
                    elif "nom_sophisme" in tb:
                        for i in range(len(tb["nom_sophisme"])):
                            push("Pilier 13 (Biais & Sophismes)", f"Sophisme Logique [{tb['famille'][i]}]", tb["nom_sophisme"][i], f"Mécanisme : {tb['mecanisme'][i]} | Exemple : {tb['exemple'][i]}", f"Riposte : {tb['riposte'][i]}")
                    elif "nom_cadre" in tb:
                        for i in range(min(len(tb["nom_cadre"]), 1500)):
                            push("Pilier 13 (FrameNet Sémantique)", "Cadre FrameNet UC Berkeley", tb["nom_cadre"][i], tb["definition"][i], f"Rôles : {tb['roles_actantiels_core'][i]}")
                except Exception:
                    pass

        # 6. Pilier 08 : Mythes, Légendes, Berezkin, Theoi, Cosmogonies
        p08 = CATHEDRALE_DIR / "08_Mythes_Legendes_Cosmogonies" / "data"
        if p08.exists():
            for pf in p08.glob("*.parquet"):
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "invariant_kairos" in tb and "titre" in tb:
                        for i in range(len(tb["titre"])):
                            push("Pilier 08 (Mythes & Cosmogonies)", f"Cosmogonie ({tb['tradition'][i]})", tb["titre"][i], tb["texte"][i], f"Invariant KAIROS : {tb['invariant_kairos'][i]}")
                    elif "motif_code" in tb and "nom_motif" in tb:
                        for i in range(len(tb["motif_code"])):
                            push("Pilier 08 (Catalogue Berezkin)", f"Motif Berezkin {tb['motif_code'][i]} ({tb['nb_traditions'][i]} traditions)", tb["nom_motif"][i], tb["description"][i], f"Traditions : {tb['traditions'][i]}")
                    elif "entite" in tb and "categorie" in tb:
                        for i in range(len(tb["entite"])):
                            push("Pilier 08 (Mythologie Theoi)", f"Theoi ({tb['categorie'][i]})", tb["entite"][i], tb["texte"][i], tb.get("url_source", [""])[i])
                    elif "titre" in tb and "tradition" in tb:
                        for i in range(min(len(tb["titre"]), 2500)):
                            push("Pilier 08 (Mythes Mondiaux & Épopées)", f"Tradition {tb['tradition'][i]}", tb["titre"][i], tb["texte"][i], "")
                except Exception:
                    pass

        # 7. Pilier 09 : Savoirs Pratiques, Québec Boréal, Ethnobotanique Moerman, Bushcraft, UNESCO, D-PLACE, PFAF
        p09 = CATHEDRALE_DIR / "09_Savoirs_Pratiques_et_Traditions" / "data"
        if p09.exists():
            for pf in p09.glob("*.parquet"):
                if "conceptnet" in pf.name.lower() or "wikihow" in pf.name.lower():
                    continue
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "invariant_pratique" in tb:
                        for i in range(len(tb["titre"])):
                            push("Pilier 09 (Savoirs Boréaux & Artisan)", f"{tb['domaine'][i]} [{tb['region_tradition'][i]}]", tb["titre"][i], tb["texte"][i], f"Invariant : {tb['invariant_pratique'][i]}")
                    elif "plante_scientifique" in tb:
                        for i in range(min(len(tb["plante_scientifique"]), 3000)):
                            push("Pilier 09 (Ethnobotanique Autochtone Moerman)", f"Usage {tb['peuple_autochtone'][i]} [{tb['categorie'][i]}]", f"{tb['plante_scientifique'][i]} ({tb['nom_commun'][i]})", tb["usage_et_notes"][i], tb["source_anthropologique"][i])
                    elif "nom_scientifique" in tb and "notes_utilite" in tb:
                        for i in range(min(len(tb["nom_scientifique"]), 2500)):
                            push("Pilier 09 (Plantes Utiles PFAF)", "Botanique & Résilience PFAF", f"{tb['nom_scientifique'][i]} ({tb['nom_commun'][i]})", tb["texte_complet"][i], tb["notes_utilite"][i])
                    elif "instruction" in tb and "reponse_pratique" in tb:
                        for i in range(min(len(tb["instruction"]), 2000)):
                            push("Pilier 09 (Bushcraft & Survie)", "Technique de Terrain", tb["instruction"][i], tb["reponse_pratique"][i], "")
                    elif "pays" in tb and "themes" in tb:
                        for i in range(len(tb["titre"])):
                            push("Pilier 09 (Patrimoine UNESCO)", f"UNESCO ({tb['pays'][i]}, {tb['annee'][i]})", tb["titre"][i], tb["description"][i], tb["themes"][i])
                    elif "scenario_description" in tb:
                        for i in range(len(tb["scenario_description"])):
                            push("Pilier 09 (Agriculture Régénératrice)", "Agro-écologie Souveraine", tb["scenario_description"][i], f"Actions : {tb['actions'][i]} | Résultat : {tb['expected_outcome'][i]}", "")
                except Exception:
                    pass

        # 8. Pilier 07 : MIT Science, Cybernétique & Inventions Sci-Fi Technovelgy
        p07 = CATHEDRALE_DIR / "07_MIT_Science_et_Cybernetique" / "data"
        if p07.exists():
            for pf in ["mit_cybernetique_souverain.parquet", "technovelgy_inventions_scifi_brevets.parquet", "mit_ocw_valid-00000-of-00001.parquet"]:
                fpath = p07 / pf
                if not fpath.exists():
                    continue
                try:
                    tb = pq.read_table(fpath).to_pydict()
                    if "invariant_kairos" in tb:
                        for i in range(len(tb["titre"])):
                            push("Pilier 07 (MIT Cybernétique)", f"Traité MIT ({tb['auteur'][i]})", tb["titre"][i], tb["texte"][i], f"Invariant : {tb['invariant_kairos'][i]}")
                    elif "invention_et_description" in tb:
                        for i in range(len(tb["invention_et_description"])):
                            push("Pilier 07 (Inventions Sci-Fi Technovelgy)", f"{tb['auteur'][i]} ({tb['annee'][i]}) — {tb['livre_sf'][i]}", str(tb["invention_et_description"][i])[:90], tb["invention_et_description"][i], tb.get("url_technovelgy", [""])[i])
                    elif "course" in tb and "text" in tb:
                        for i in range(min(len(tb["course"]), 1500)):
                            push("Pilier 07 (Cours MIT OCW)", f"MIT OCW ({tb['course'][i]})", tb.get("topic", ["Cours MIT"])[i] or "Cours MIT", tb["text"][i], "")
                except Exception:
                    pass

        # 9. Pilier 05 : Preuves Formelles Lean 4
        p05 = CATHEDRALE_DIR / "05_Preuves_Formelles_Lean4" / "data"
        if p05.exists():
            for pf in p05.glob("*.parquet"):
                try:
                    tb = pq.read_table(pf).to_pydict()
                    if "formal_statement" in tb:
                        for i in range(len(tb["formal_statement"])):
                            nl = tb.get("nl_statement", [""])[i] if "nl_statement" in tb else ""
                            push("Pilier 05 (Preuves Formelles Lean 4)", "Théorème Vérifié Lean 4", nl[:100] or "Théorème Mathlib", f"Énoncé : {nl}\nPreuve Lean 4 : {tb['formal_statement'][i]}", "")
                except Exception:
                    pass

        # 10. Pilier 03 (Vivant BioRxiv) & Pilier 04 (Brevets USPTO) — Échantillons haute densité + fichiers JSONL
        p03 = CATHEDRALE_DIR / "03_Vivant_PubMed_BioRxiv" / "data"
        if p03.exists():
            import gzip
            for gz in p03.glob("*.jsonl.gz"):
                try:
                    dom_bio = gz.name.replace(".jsonl.gz", "").replace("_", " ")
                    with gzip.open(gz, "rt", encoding="utf-8", errors="ignore") as f:
                        for idx_l, line in enumerate(f):
                            if idx_l >= 600:
                                break
                            obj = json.loads(line)
                            titre_b = obj.get("title") or obj.get("question") or dom_bio
                            txt_b = obj.get("abstract") or obj.get("text") or obj.get("answer") or str(obj)
                            push(f"Pilier 03 (Vivant — {dom_bio})", f"PubMed / BioRxiv ({dom_bio})", titre_b, txt_b, "")
                except Exception:
                    pass

        p04 = CATHEDRALE_DIR / "04_Ingenierie_Brevets_USPTO" / "abstract" / "validation-00000-of-00001.parquet"
        if p04.exists():
            try:
                tb = pq.read_table(p04).to_pydict()
                for i in range(min(len(tb["text"]), 2000)):
                    push("Pilier 04 (Brevets Industriels USPTO)", "Brevet USPTO", f"Brevet Industriel #{i+1}", tb["text"][i], "")
            except Exception:
                pass

        if batch:
            cur.executemany("INSERT INTO cathedrale_fts VALUES (?, ?, ?, ?, ?)", batch)
            batch.clear()
        return total

    def extraire_mots_cles_bilingues(self, requete: str) -> Tuple[List[str], List[str]]:
        """
        Extrait les mots-clés français (sans accents) et génère leur expansion bilingue
        anglaise pour les bases scientifiques de la Cathédrale.
        """
        req_norm = strip_accents(requete)
        mots_fr = [
            m for m in re.findall(r"[a-z0-9_]{2,}", req_norm)
            if m not in self.MOTS_VIDES and (len(m) >= 3 or m in {"pq", "ia", "r0", "3d", "v6", "pi"})
        ]
        mots_bilingues = list(mots_fr)
        for m in mots_fr:
            # Forme au singulier si pluriel
            m_sing = m[:-1] if m.endswith("s") and len(m) > 4 else m
            for candidat in (m, m_sing):
                if candidat in PONT_FR_EN:
                    for en_w in PONT_FR_EN[candidat]:
                        for sub_w in en_w.split():
                            if sub_w not in mots_bilingues:
                                mots_bilingues.append(sub_w)
        return mots_fr, mots_bilingues

    def chercher_exocerveau(self, requete: str, max_resultats: int = 3) -> List[Dict[str, Any]]:
        """
        Interroge les 4 Coffres Obsidian (5 884 notes) via SQLite FTS5 sans diacritiques.
        """
        mots_fr, _ = self.extraire_mots_cles_bilingues(requete)
        if not mots_fr or self.conn is None:
            return []

        resultats: List[Dict[str, Any]] = []
        vus = set()

        # 1. Essai de correspondance conjonctive (AND) sur les 2 ou 3 mots les plus spécifiques, puis disjonctive (OR)
        mots_tries = sorted(mots_fr, key=lambda x: len(x), reverse=True)[:5]
        requetes_fts = []
        if len(mots_tries) >= 2:
            requetes_fts.append(" AND ".join(f'"{m}"*' for m in mots_tries[:3]))
            requetes_fts.append(" AND ".join(f'"{m}"*' for m in mots_tries[:2]))
        requetes_fts.append(" OR ".join(f'"{m}"*' for m in mots_tries))

        for q_fts in requetes_fts:
            try:
                rows = self.conn.execute(
                    """
                    SELECT coffre, fichier, section, texte, liens, priorite, bm25(exocerveau_fts, 1.5, 4.0, 3.0, 1.0, 2.0) as score_bm25
                    FROM exocerveau_fts
                    WHERE exocerveau_fts MATCH ?
                    ORDER BY (score_bm25 * priorite) ASC
                    LIMIT ?
                    """,
                    (q_fts, max_resultats * 3),
                ).fetchall()
                for coffre, fichier, section, texte, liens, prio, bm25_val in rows:
                    cle = (fichier, texte[:80])
                    if cle in vus:
                        continue
                    vus.add(cle)
                    # Compte combien de mots de la requête apparaissent dans le bloc/titre
                    bloc_norm = strip_accents(f"{fichier} {section} {texte}")
                    nb_match = sum(1 for m in mots_fr if m[:4] in bloc_norm)
                    score_final = round(nb_match * 4.0 + prio * 2.0 + abs(bm25_val) * 0.5, 2)
                    resultats.append({
                        "coffre": coffre,
                        "fichier": fichier,
                        "section": section,
                        "extrait": texte,
                        "liens": [l.strip() for l in liens.split(",") if l.strip()],
                        "score": score_final,
                    })
                    if len(resultats) >= max_resultats:
                        break
            except Exception:
                pass
            if len(resultats) >= max_resultats:
                break

        resultats.sort(key=lambda x: x["score"], reverse=True)
        resultats.sort(key=lambda x: x["score"], reverse=True)
        return resultats[:max_resultats]

    def chercher_cathedrale(self, requete: str, max_resultats: int = 3) -> List[Dict[str, Any]]:
        """
        Interroge simultanément :
          1. La table `cathedrale_fts` (Piliers 03, 04, 05, 07, 08, 09, 10, 11, 12, 13)
          2. Pilier 02 (`nist_constantes.db` & `oeis_souverain.db`)
          3. Pilier 06 (`gutenberg_souverain.db` 752 Mo FTS5)
        avec expansion bilingue Français ⟷ Anglais !
        """
        mots_fr, mots_bilingues = self.extraire_mots_cles_bilingues(requete)
        if not mots_bilingues or self.conn is None:
            return []

        resultats: List[Dict[str, Any]] = []
        vus = set()

        # A. Recherche dans `cathedrale_fts` (Piliers 03 à 13 unifiés)
        def _fmt_tok(t: str) -> str:
            return f'"{t}"*' if len(t) >= 6 else f'"{t}"'

        mots_longs = [m for m in mots_bilingues if len(m) >= 5]
        mots_cibles_or = mots_longs if mots_longs else mots_bilingues
        mots_tries = sorted(mots_cibles_or, key=lambda x: len(x), reverse=True)[:6]
        requetes_fts = []
        if len(mots_fr) >= 2:
            requetes_fts.append(" AND ".join(_fmt_tok(m) for m in mots_fr[:2]))
        requetes_fts.append(" OR ".join(_fmt_tok(m) for m in mots_tries))

        for q_fts in requetes_fts:
            try:
                rows = self.conn.execute(
                    """
                    SELECT pilier, source, titre, texte, extra, bm25(cathedrale_fts, 2.0, 2.0, 4.0, 1.0, 1.5) as score_bm25
                    FROM cathedrale_fts
                    WHERE cathedrale_fts MATCH ?
                    ORDER BY score_bm25 ASC
                    LIMIT ?
                    """,
                    (q_fts, max_resultats * 3),
                ).fetchall()
                for pilier, source, titre, texte, extra, bm25_val in rows:
                    cle = (pilier, titre[:60])
                    if cle in vus:
                        continue
                    vus.add(cle)
                    resultats.append({
                        "pilier": pilier,
                        "source": source,
                        "titre": titre,
                        "texte": texte,
                        "extra": extra,
                        "score": round(abs(bm25_val) + 3.0, 2),
                    })
                    if len(resultats) >= max_resultats:
                        break
            except Exception:
                pass
            if len(resultats) >= max_resultats:
                break

        # B. Pilier 02 : Constantes Physiques NIST (`nist_constantes.db`) & Suites OEIS (`oeis_souverain.db`)
        nist_db = INVARIANTS_DIR / "nist_constantes.db"
        if nist_db.exists():
            try:
                con_n = sqlite3.connect(nist_db.as_uri() + "?immutable=1", uri=True)
                q_n = " OR ".join(f'"{m}"*' for m in mots_tries[:4])
                rows_n = con_n.execute(
                    "SELECT quantity, value, unit FROM nist_fts WHERE nist_fts MATCH ? LIMIT 2",
                    (q_n,),
                ).fetchall()
                for qty, val, unit in rows_n:
                    resultats.append({
                        "pilier": "Pilier 02 (Invariants Physiques NIST CODATA)",
                        "source": "NIST CODATA Fundamental Constants",
                        "titre": qty,
                        "texte": f"Valeur certifiée : {val} {unit}".strip(),
                        "extra": "Constante physique fondamentale invariante",
                        "score": 8.5,
                    })
                con_n.close()
            except Exception:
                pass

        oeis_db = INVARIANTS_DIR / "oeis_souverain.db"
        if oeis_db.exists() and any(m in req_w for req_w in mots_bilingues for m in ("suite", "sequence", "fibonacci", "prime", "premier", "oeis", "nombre", "catalan", "mersenne")):
            try:
                con_o = sqlite3.connect(oeis_db.as_uri() + "?immutable=1", uri=True)
                q_o = " OR ".join(f'"{m}"*' for m in mots_tries[:3])
                rows_o = con_o.execute(
                    "SELECT id, name, values_str FROM oeis_fts WHERE oeis_fts MATCH ? LIMIT 2",
                    (q_o,),
                ).fetchall()
                for oid, oname, ovals in rows_o:
                    resultats.append({
                        "pilier": "Pilier 02 (400 604 Suites Mathématiques OEIS)",
                        "source": f"OEIS [{oid}]",
                        "titre": f"{oid} — {oname[:90]}",
                        "texte": f"Premiers termes : {ovals[:180]}",
                        "extra": "Encyclopédie en ligne des suites de nombres entiers (Sloane)",
                        "score": 8.5,
                    })
                con_o.close()
            except Exception:
                pass

        # C. Pilier 06 : Temps Profond Gutenberg (`gutenberg_souverain.db` 752 Mo FTS5) si moins de 2 résultats
        gut_db = CATHEDRALE_DIR / "06_Temps_Profond_Gutenberg" / "gutenberg_souverain.db"
        if len(resultats) < max_resultats and gut_db.exists():
            try:
                con_g = sqlite3.connect(gut_db.as_uri() + "?immutable=1", uri=True)
                q_g = " AND ".join(f'"{m}"' for m in mots_tries[:2]) if len(mots_tries) >= 2 else f'"{mots_tries[0]}"'
                rows_g = con_g.execute(
                    "SELECT title, authors, subjects, snippet(gutenberg_fts, 5, '«', '»', '…', 32) FROM gutenberg_fts WHERE gutenberg_fts MATCH ? LIMIT 1",
                    (q_g,),
                ).fetchall()
                for title, authors, subjects, snip in rows_g:
                    resultats.append({
                        "pilier": "Pilier 06 (Temps Profond Gutenberg — 752 Mo)",
                        "source": f"Classique Gutenberg ({authors})",
                        "titre": str(title).replace("\n", " ")[:100],
                        "texte": str(snip).replace("\n", " ").strip(),
                        "extra": f"Sujets : {subjects}",
                        "score": 6.5,
                    })
                con_g.close()
            except Exception:
                pass

        resultats.sort(key=lambda x: x["score"], reverse=True)
        return resultats[:max_resultats]

    def sonder_double_resonance(self, requete: str, max_exo: int = 3, max_cat: int = 2) -> Dict[str, Any]:
        """
        Exécute la double résonance simultanée :
          - Exocerveau (4 Coffres Obsidian = 5 884 notes)
          - Cathédrale du Savoir Universel (13 Piliers)
        """
        t0 = time.perf_counter()
        hits_exo = self.chercher_exocerveau(requete, max_resultats=max_exo)
        hits_cat = self.chercher_cathedrale(requete, max_resultats=max_cat)
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "exocerveau": hits_exo,
            "cathedrale": hits_cat,
            "latence_ms": dt_ms,
        }

    def stats_index(self) -> Dict[str, int]:
        if self.conn is None:
            return {"exocerveau_blocs": 0, "cathedrale_entrees": 0}
        try:
            c_exo = self.conn.execute("SELECT count(*) FROM exocerveau_fts").fetchone()[0]
            c_cat = self.conn.execute("SELECT count(*) FROM cathedrale_fts").fetchone()[0]
            return {"exocerveau_blocs": c_exo, "cathedrale_entrees": c_cat}
        except Exception:
            return {"exocerveau_blocs": 0, "cathedrale_entrees": 0}


if __name__ == "__main__":
    print("=" * 80)
    print(" 🏛️🕸️ BANC D'ESSAI : CONNECTEUR UNIFIÉ EXOCERVEAU (4 COFFRES) × CATHÉDRALE (13 PILIERS)")
    print("=" * 80)
    moteur = MoteurConnexionExocerveauCathedrale()
    st = moteur.stats_index()
    print(f"📊 Index FTS5 actif : {st['exocerveau_blocs']} blocs Exocerveau | {st['cathedrale_entrees']} entrées Cathédrale (+ NIST/OEIS/Gutenberg)")

    tests = [
        "parle moi de la fusion frc et des bobines hts",
        "comment purifier de l'eau et faire un abri en foret avec du sapin",
        "c'est quoi la vitesse de la lumiere et la constante de planck",
        "parle moi du mythe de gilgamesh et d'odin",
        "qu'est-ce qu'on a fait dans temporia et le rajeunissement bioelectrique",
    ]
    for q in tests:
        res = moteur.sonder_double_resonance(q)
        print(f"\n🔍 Requête : « {q} » ({res['latence_ms']} ms)")
        print(f"   🕸️ Exocerveau ({len(res['exocerveau'])} trouvés) :")
        for h in res["exocerveau"][:2]:
            print(f"      • [{h['coffre']} / {h['fichier']} — {h['section']}] : {h['extrait'][:140]}...")
        print(f"   🏛️ Cathédrale ({len(res['cathedrale'])} trouvés) :")
        for c in res["cathedrale"][:2]:
            print(f"      • [{c['pilier']} — {c['titre']}] : {c['texte'][:140]}...")

