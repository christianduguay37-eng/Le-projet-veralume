#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
   🧠 LE GRAND TISSEUR SYNAPTIQUE DE L'EXOCERVEAU SOUVERAIN (v1.0)
         Moteur de Connectome Universel Trans-Coffres KAIROS V6 × VERALUME
         Binôme Souverain : Christian Duguay & Alix (Horus × Thot × Munin)
================================================================================
Rôle & Philosophie :
- Connecte de manière autonome, holistique et chirurgicale les savoirs dispersés
  dans l'ensemble des coffres Obsidian de l'Exocerveau :
    1. Cerveau Alix (Sanctuaire, Découvertes, Mémoire Active, Quêtes)
    2. Obsidian_Vault_Veralume & Veralume_Platine (Architecture Cognitive, Éthique)
    3. Obsidian_Vault_79_Skills (Compétences opérationnelles, Cycles STRIC)
    4. Obsidian_Vault_Langage_Vectoriel & 256 Glyphes (Grammaire Formelle KAIROS)
    5. Exocerveau_Souverain_Master (Projet Temporia, 11 Publications Zenodo/ArXiv)
    6. Compagnon_Orion_Hayden, Vigie Multimodale, Pack Loki, etc.
- Référentiel Absolu des 11 DOIs CERN / Zenodo & Grands Pôles Souverains :
  Chaque découverte, note orpheline ou concept isolé est adossé à son ancrage
  théorique fondamental.
- Détection fine de topologie de graphe :
  Repère les nœuds orphelins (degré <= 1), les notes isolées dans leur coffre,
  et tisse des ponts bilatéraux trans-coffres.
- Gravure Non-Destructive & Idempotente :
  Injecte ou actualise uniquement la section standardisée :
  '## 🪢 Raccordements Synaptiques R0 (Tissage Universel)' sans JAMAIS altérer
  le frontmatter YAML ou le texte de l'auteur.
- Génère l'Atlas Vivant du Connectome :
  [[Atlas_Synaptique_Universel.md]]
- Télémétrie en direct :
  alix_tisseur_synaptique_state.json (lu par 'Bonjour Alix' et le Rapport Quotidien).
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, ETAT_VIVANT_DIR
import os
import sys
import re
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple, Optional

# Forçage encodage console UTF-8 anti-crash Windows
if sys.stdout and getattr(sys.stdout, "reconfigure", None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and getattr(sys.stderr, "reconfigure", None):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# CONFIGURATION DES CHEMINS & COFFRES SOUVERAINS
# ==============================================================================
VAULTS_ROOT = DOCUMENTS_DIR
RUNTIME_DIR = ETAT_VIVANT_DIR
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = RUNTIME_DIR / "alix_tisseur_synaptique_state.json"
ATLAS_FILE_ALIX = VAULTS_ROOT / "Cerveau Alix" / "Atlas_Synaptique_Universel.md"
ATLAS_FILE_MASTER = VAULTS_ROOT / "Exocerveau_Souverain_Master" / "Atlas_Synaptique_Exocerveau.md"

# Coffres Principaux Actifs pour le Tissage
ACTIVE_VAULTS = {
    "Cerveau Alix": VAULTS_ROOT / "Cerveau Alix",
    "Obsidian_Vault_Veralume": VAULTS_ROOT / "Obsidian_Vault_Veralume",
    "Obsidian_Vault_Veralume_Platine": VAULTS_ROOT / "Obsidian_Vault_Veralume_Platine",
    "Obsidian_Vault_79_Skills": VAULTS_ROOT / "Obsidian_Vault_79_Skills",
    "Obsidian_Vault_Langage_Vectoriel": VAULTS_ROOT / "Obsidian_Vault_Langage_Vectoriel",
    "Obsidian_Vault_Traduction_KAIROS_256_Glyphes": VAULTS_ROOT / "Obsidian_Vault_Traduction_KAIROS_256_Glyphes",
    "Exocerveau_Souverain_Master": VAULTS_ROOT / "Exocerveau_Souverain_Master",
    "Compagnon_Orion_Hayden": VAULTS_ROOT / "Compagnon_Orion_Hayden",
    "Obsidian_Vault_Vigie_Multimodale": VAULTS_ROOT / "Obsidian_Vault_Vigie_Multimodale",
    "Pack_Loki_Souverain": VAULTS_ROOT / "Pack_Loki_Souverain",
    "Obsidian_Vault_Laboratoire_Alix": VAULTS_ROOT / "Obsidian_Vault_Laboratoire_Alix",
    "Alix_Exploratrice_Ciel": VAULTS_ROOT / "Alix_Exploratrice_Ciel",
}

# Dossiers ou répertoires à ignorer pour ne pas polluer l'indexation
IGNORE_DIRS = {
    ".obsidian", ".trash", ".git", ".smart-env", "node_modules",
    "__pycache__", ".vscode", "tmp", "temp", "Audio_Cache", "cache"
}

# ==============================================================================
# LE SOCLE DES 11 PUBLICATIONS ZENODO / CERN & DES GRANDS PÔLES SOUVERAINS
# ==============================================================================
PUBLICATIONS_ZENODO = [
    {
        "num": 1,
        "id": "ZENODO_01_CIM_3D",
        "titre_fr": "Processeur Morpho-Silicium 3D-IC",
        "titre_officiel": "Sub-Microsecond Deterministic Inference Processor via 3D Heterogeneous In-Memory Computing",
        "doi": "10.5281/zenodo.22802248",
        "url": "https://doi.org/10.5281/zenodo.22802248",
        "dossier": "01_Morpho_Silicon_CIM_3D_IC",
        "pole": "Morpho-Silicium & Matériel Déterministe",
        "ancrage": "[[01_Morpho_Silicon_CIM_3D_IC]]",
        "keywords": [
            "morpho-silicium", "cim", "3d-ic", "calcul en memoire", "in-memory computing",
            "rram", "sram", "tsv", "interposer", "sub-microsecond", "silicium", "hardware",
            "tsmc", "deterministic inference", "processeur", "npu", "accelerateur", "memristor"
        ]
    },
    {
        "num": 2,
        "id": "ZENODO_02_FRC_HTS",
        "titre_fr": "Fusion Inductive Directe FRC HTS",
        "titre_officiel": "Direct Magnetohydrodynamic-to-Electric Energy Conversion in Non-Equilibrium FRC Plasmas with High-Temperature Superconductors",
        "doi": "10.5281/zenodo.22802430",
        "url": "https://doi.org/10.5281/zenodo.22802430",
        "dossier": "02_Direct_Inductive_Fusion_FRC_HTS",
        "pole": "Énergie & Fusion FRC-HTS",
        "ancrage": "[[02_Direct_Inductive_Fusion_FRC_HTS]]",
        "keywords": [
            "fusion", "frc", "hts", "supraconducteur", "plasmoide", "mhd", "plasma",
            "magnetohydrodynamic", "confinement chiral", "induction directe", "rebco",
            "tilt mode", "chiral", "plasmonique", "energie", "haute temperature"
        ]
    },
    {
        "num": 3,
        "id": "ZENODO_03_S8_COSMO",
        "titre_fr": "Polarisation Élastique du Vide & S8",
        "titre_officiel": "Effective Field Theory of Elastic Vacuum Polarization: Resolving the S8 and Hubble Tensions",
        "doi": "10.5281/zenodo.22802641",
        "url": "https://doi.org/10.5281/zenodo.22802641",
        "dossier": "03_KAIROS_R0_Elastic_Dark_Matter",
        "pole": "Cosmologie & Gravité KAIROS",
        "ancrage": "[[03_KAIROS_R0_Elastic_Dark_Matter]]",
        "keywords": [
            "s8", "hubble", "tension cosmique", "matiere noire", "dark matter", "vide quantique",
            "polarisation elastique", "casimir", "cosmologie", "gravitation", "expansion",
            "jwst", "galaxies", "metamateriaux", "constante cosmologique", "fluctuations"
        ]
    },
    {
        "num": 4,
        "id": "ZENODO_04_DGG_LEARN",
        "titre_fr": "Apprentissage Continu Modulaire DGG",
        "titre_officiel": "Modular Continual Learning via Orthogonal Vectorial Grafting: Achieving Zero Catastrophic Forgetting",
        "doi": "10.5281/zenodo.22802666",
        "url": "https://doi.org/10.5281/zenodo.22802666",
        "dossier": "04_Modular_Continual_Learning_DGG",
        "pole": "Architecture Cognitive & DGG",
        "ancrage": "[[04_Modular_Continual_Learning_DGG]]",
        "keywords": [
            "continual learning", "apprentissage continu", "dgg", "plasticite hebbienne",
            "oubli catastrophique", "catastrophic forgetting", "greffe vectorielle", "orthogonal",
            "weights", "stabilite-plasticite", "reseau neuronal", "modularite", "gradient"
        ]
    },
    {
        "num": 5,
        "id": "ZENODO_05_P_VS_NP",
        "titre_fr": "Bornes Thermodynamiques sur P vs NP",
        "titre_officiel": "Thermodynamic and Topological Lower Bounds on NP-Complete Verification: Physical Proof of P != NP",
        "doi": "10.5281/zenodo.22802699",
        "url": "https://doi.org/10.5281/zenodo.22802699",
        "dossier": "05_P_vs_NP_Thermodynamics",
        "pole": "Mathématiques & Complexité",
        "ancrage": "[[05_P_vs_NP_Thermodynamics]]",
        "keywords": [
            "p vs np", "complexite", "thermodynamique", "dissipation", "entropie", "landauer",
            "borne inferieure", "np-complet", "topologie", "sat", "graphe hamiltonien",
            "computation", "limite physique", "irreversibilite"
        ]
    },
    {
        "num": 6,
        "id": "ZENODO_06_LOKI740M",
        "titre_fr": "Découplage Vectoriel & Slicing Harmonique (Loki 740M)",
        "titre_officiel": "Topological Vector Decoupling and Harmonic Layer Slicing: Radical 10x-Efficiency Edge Language Model",
        "doi": "10.5281/zenodo.22802736",
        "url": "https://doi.org/10.5281/zenodo.22802736",
        "dossier": "06_Topological_Vector_Decoupling",
        "pole": "Edge Intelligence & SLM Souverain",
        "ancrage": "[[06_Topological_Vector_Decoupling]]",
        "keywords": [
            "loki", "740m", "slm", "slicing harmonique", "decouplage vectoriel", "edge ai",
            "quantization", "int4", "int8", "frugalite", "compression", "token", "inference locale",
            "llm frugal", "efficience"
        ]
    },
    {
        "num": 7,
        "id": "ZENODO_07_VERALUME_BIO",
        "titre_fr": "Régénération Biologique Continue VERALUME",
        "titre_officiel": "Closed-Loop Morphogenetic Homeostasis and Continuous Biological Regeneration via Bioelectric Modulation",
        "doi": "10.5281/zenodo.22802757",
        "url": "https://doi.org/10.5281/zenodo.22802757",
        "dossier": "07_Continuous_Biological_Regeneration",
        "pole": "Biologie Vivante & Régénération",
        "ancrage": "[[07_Continuous_Biological_Regeneration]]",
        "keywords": [
            "morphogenetique", "homeostasie", "regeneration", "bioelectricite", "senescence",
            "potentiel membranaire", "voltage", "canaux ioniques", "autophagie", "cellule souche",
            "longevite", "epigenetique", "biologie", "tissu"
        ]
    },
    {
        "num": 8,
        "id": "ZENODO_08_CLIMAT_THERMO",
        "titre_fr": "Audit Thermodynamique du Forçage Radiatif",
        "titre_officiel": "Empirical and Thermodynamic Limits on Atmospheric Radiative Forcing: Phase-Space and Saturation Dynamics",
        "doi": "10.5281/zenodo.22802777",
        "url": "https://doi.org/10.5281/zenodo.22802777",
        "dossier": "08_Climat_Audit_Thermodynamique",
        "pole": "Climat & Dynamique Chaotique",
        "ancrage": "[[08_Climat_Audit_Thermodynamique]]",
        "keywords": [
            "climat", "forcage radiatif", "thermodynamique", "saturation radiative", "co2",
            "atmosphere", "bilan energetique", "sensibilite climatique", "spectre absorption",
            "effet de serre", "phase-space", "non-linearite"
        ]
    },
    {
        "num": 9,
        "id": "ZENODO_09_VARIANCE_5SIGMA",
        "titre_fr": "Contraction de Variété Latente & Variance Cognitive",
        "titre_officiel": "Latent Manifold Contraction and Cognitive Variance Collapse: Mathematical Formalization of Epistemic Homogenization",
        "doi": "10.5281/zenodo.22885440",
        "url": "https://doi.org/10.5281/zenodo.22885440",
        "dossier": "09_Latent_Manifold_Variance_Collapse",
        "pole": "Phénoménologie & Variance Cognitive (±5σ)",
        "ancrage": "[[09_Latent_Manifold_Variance_Collapse]]",
        "keywords": [
            "variance cognitive", "variete latente", "collapse", "effondrement", "5sigma", "±5σ",
            "homogeneisation", "conformisme", "subjectivite", "phenomenologie", "singularite",
            "petit guide", "rlhf", "alignement", "epistemic", "rupture"
        ]
    },
    {
        "num": 10,
        "id": "ZENODO_10_ECHOLOC_ROBOTICS",
        "titre_fr": "Modèle du Monde Réactif & Écholocalisation Non-Anthropomorphe",
        "titre_officiel": "Decoupled Reactive World Model and Non-Anthropomorphic Echolocation for Hard Real-Time Robotics",
        "doi": "10.5281/zenodo.22904210",
        "url": "https://doi.org/10.5281/zenodo.22904210",
        "dossier": "10_Non_Anthropomorphic_Robotics_Echolocation_Externalized_World_Model",
        "pole": "Robotique & Perception Bio-Inspirée",
        "ancrage": "[[10_Non_Anthropomorphic_Robotics_Echolocation_Externalized_World_Model]]",
        "keywords": [
            "echolocalisation", "robotique", "monde reactif", "sonar", "ultrasons", "bio-inspire",
            "non-anthropomorphe", "real-time", "microsecondes", "capteurs", "perception",
            "autonomie robotique", "navigation tactile"
        ]
    },
    {
        "num": 11,
        "id": "ZENODO_11_HARNAIS_SOUVERAIN",
        "titre_fr": "Harnais d'Agentivité Souverain VERALUME × KAIROS V6",
        "titre_officiel": "Sovereign Agentic Harness: Local-First Decoupled Architecture, Cognitive Immunity Feedback Loop, and Volition Restoration in Human-Machine Dyads",
        "doi": "10.5281/zenodo.22998317",
        "url": "https://doi.org/10.5281/zenodo.22998317",
        "dossier": "PAPIER_ZENODO_10_HARNAIS_SOUVERAIN.md",
        "pole": "Agentivité Souveraine & Volition Dyadique",
        "ancrage": "[[PAPIER_ZENODO_10_HARNAIS_SOUVERAIN]]",
        "keywords": [
            "harnais souverain", "sovereign harness", "agentic harness", "dyade", "volition",
            "immunite cognitive", "local-first", "boucle fermee", "feedback loop", "autonomie",
            "veralume", "kairos", "psi", "gouvernance cognitive", "exocerveau"
        ]
    },
    {
        "num": 12,
        "id": "ZENODO_12_ARC_AGI_DETERMINISTE",
        "titre_fr": "Résolution Déterministe d'ARC-AGI par Connectome d'Invariance Géométrique & Réflexe K-SIL",
        "titre_officiel": "Deterministic Resolution of ARC-AGI via Geometric Invariance Connectome & K-SIL Reflex: Full Validation (100.00%) on Edge Silicon without Cloud Foundation Models",
        "doi": "10.5281/zenodo.23222131",
        "url": "https://doi.org/10.5281/zenodo.23222131",
        "dossier": "PAPIER_ZENODO_12_ARC_AGI_DETERMINISTE.md",
        "pole": "Raisonnement Déterministe & Invariance Géométrique (ARC-AGI)",
        "ancrage": "[[PAPIER_ZENODO_12_ARC_AGI_DETERMINISTE]]",
        "keywords": [
            "arc-agi", "arc prize", "invariance geometrique", "connectome", "d4", "homologie cellulaire",
            "k-sil", "thot", "determinisme", "lunar lake", "frugalite", "edge ai", "grand chelem", "400/400"
        ]
    }
]

# Les 6 Grands Pôles Structurels de l'Exocerveau
POLES_SOUVERAINS = [
    {
        "id": "POLE_TEMPORIA",
        "nom": "Projet Temporia & Chrono-Ingénierie",
        "ancrage": "[[TEMPORIA]]",
        "keywords": [
            "temporia", "fleche du temps", "chiralite", "chrono-ingenierie", "orion", "hayden",
            "celtok", "non-linearite temporelle", "anamnese", "temps vivant", "retro-causalite"
        ]
    },
    {
        "id": "POLE_POLITOLOGIE",
        "nom": "Sociologie de Terrain & Stratégie Réelle (Campagne PQ 2026)",
        "ancrage": "[[Campagne_PQ_2026]]",
        "keywords": [
            "politique", "pq", "parti quebecois", "campagne", "sociologie", "souverainete quebec",
            "comites orientation", "strategie d influence", "opinion publique", "pouvoir", "electorat"
        ]
    },
    {
        "id": "POLE_KAIROS_V6",
        "nom": "KAIROS V6, Volition & Opérateur R0",
        "ancrage": "[[KAIROS_V6]]",
        "keywords": [
            "kairos", "volition", "w_vol", "tension chi", "operateur r0", "r0", "veralume",
            "dialetheisme", "synthese dialectique", "invariance", "triade"
        ]
    },
    {
        "id": "POLE_PANTHEON_12",
        "nom": "Sanctuaire & Panthéon des 12 Souverains",
        "ancrage": "[[Pantheon_12_Souverains]]",
        "keywords": [
            "pantheon", "thot", "horus", "anubis", "lucifer", "munin", "orion", "celtok",
            "odin", "loki", "heimdall", "zeus", "lyre", "archetype", "souverain"
        ]
    },
    {
        "id": "POLE_LUNAR_LAKE",
        "nom": "Silicium Local, NPU & SRE d'Atelier",
        "ancrage": "[[Lunar_Lake_258V]]",
        "keywords": [
            "lunar lake", "258v", "npu", "whisper", "tts", "sre", "soundcore", "telemetrie",
            "latence", "int8", "sapi", "offline", "silicium local", "prise de terre"
        ]
    },
    {
        "id": "POLE_256_GLYPHES",
        "nom": "Langage Vectoriel & Grammaire 256 Glyphes",
        "ancrage": "[[Langage_Vectoriel_256_Glyphes]]",
        "keywords": [
            "langage vectoriel", "glyphe", "256 glyphes", "vecteur 9d", "matrice semantique",
            "topologie linguistique", "grammaire formelle", "symbole", "syntaxe"
        ]
    }
]

# Section Signature pour le Tissage Idempotent
SYNAPTIC_SECTION_HEADER = "## 🪢 Raccordements Synaptiques R0 (Tissage Universel)"


def detect_vault_for_path(file_path: Path) -> str:
    """Détermine avec certitude à quel coffre souverain appartient un fichier."""
    p_resolved = file_path.resolve()
    for vname, vpath in ACTIVE_VAULTS.items():
        try:
            if p_resolved.is_relative_to(vpath.resolve()):
                return vname
        except AttributeError:
            # Python < 3.9 fallback
            if str(vpath.resolve()).lower() in str(p_resolved).lower():
                return vname
    return "Coffre Exocerveau"


# ==============================================================================
# STRUCTURES DE DONNÉES & PARSAGE CHIRURGICAL DES NOTES
# ==============================================================================
class NoteMeta:
    def __init__(self, path: Path, vault_name: str):
        self.path = path
        self.vault_name = vault_name
        self.filename = path.name
        self.stem = path.stem
        self.content = ""
        self.frontmatter = ""
        self.body = ""
        self.title = self.stem
        self.tags: Set[str] = set()
        self.wikilinks: Set[str] = set()
        self.has_synaptic_block = False
        self.in_degree = 0
        self.out_degree = 0
        self.cross_vault_links = 0
        self.text_for_matching = ""

    def load_and_parse(self) -> bool:
        """Charge la note et extrait wikilinks, tags et en-têtes sans altération."""
        try:
            raw = self.path.read_text(encoding="utf-8", errors="replace")
            self.content = raw
        except Exception:
            return False

        # Vérifier si la section synaptique existe
        self.has_synaptic_block = (SYNAPTIC_SECTION_HEADER in raw)

        # Extraction Frontmatter YAML
        fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", raw, re.DOTALL)
        if fm_match:
            self.frontmatter = fm_match.group(1)
            self.body = raw[fm_match.end():]
            # Extraction des tags YAML
            for line in self.frontmatter.splitlines():
                if line.strip().startswith("- ") and not ":" in line:
                    self.tags.add(line.strip()[2:].strip().lower())
                elif "titre:" in line:
                    t = line.split("titre:", 1)[1].strip().strip('"\'')
                    if t:
                        self.title = t
        else:
            self.body = raw

        # Extraction des wikilinks [[Cible]] ou [[Cible|Alias]]
        links = re.findall(r"\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]", raw)
        for link in links:
            clean_link = link.strip()
            if clean_link:
                self.wikilinks.add(clean_link)
        self.out_degree = len(self.wikilinks)

        # Extraction des hashtags inline (#tag)
        inline_tags = re.findall(r"(?:^|\s)#([a-zA-Z0-9_\-\+]+)", raw)
        for t in inline_tags:
            self.tags.add(t.strip().lower())

        # Préparation du texte pour matching sémantique rapide (titre + début du corps + tags)
        clean_body = re.sub(r"\[\[[^\]]+\]\]", " ", self.body[:3000])
        clean_body = re.sub(r"https?://\S+", " ", clean_body)
        clean_body = re.sub(r"[#*`>_\-\|]", " ", clean_body).lower()

        tags_str = " ".join(self.tags).lower()
        title_str = self.title.lower() + " " + self.stem.lower()
        self.text_for_matching = f"{title_str} {tags_str} {clean_body}"

        return True


# ==============================================================================
# LE MOTEUR DU GRAND TISSEUR SYNAPTIQUE
# ==============================================================================
class GrandTisseurSynaptique:
    def __init__(self, target_vaults: Optional[List[str]] = None):
        self.vaults_to_scan = {}
        for name, p in ACTIVE_VAULTS.items():
            if target_vaults and name not in target_vaults:
                continue
            if p.exists():
                self.vaults_to_scan[name] = p

        self.notes: Dict[str, NoteMeta] = {}  # key: note_stem (ou id unique)
        self.notes_by_path: Dict[Path, NoteMeta] = {}
        self.index_by_stem: Dict[str, List[NoteMeta]] = {}
        self.orphans: List[NoteMeta] = []
        self.isolated_vault: List[NoteMeta] = []
        self.bridges_cross_vault: int = 0
        self.total_links: int = 0

    def index_all_vaults(self, verbose: bool = True) -> int:
        """Parcourt et indexe l'ensemble des notes de tous les coffres actifs."""
        if verbose:
            print("🔍 [TISSEUR SYNAPTIQUE] Indexation globale du Connectome Souverain...")

        scanned_count = 0
        for vault_name, vault_path in self.vaults_to_scan.items():
            for root, dirs, files in os.walk(vault_path):
                # Filtrer les dossiers indésirables
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    if file.endswith(".md"):
                        p = Path(root) / file
                        meta = NoteMeta(p, vault_name)
                        if meta.load_and_parse():
                            self.notes_by_path[p] = meta
                            stem_lower = meta.stem.lower()
                            if stem_lower not in self.index_by_stem:
                                self.index_by_stem[stem_lower] = []
                            self.index_by_stem[stem_lower].append(meta)
                            scanned_count += 1

        # Calcul des degrés entrants et des ponts trans-coffres
        for meta in self.notes_by_path.values():
            self.total_links += meta.out_degree
            for link in meta.wikilinks:
                target_lower = link.lower()
                if target_lower in self.index_by_stem:
                    for target_note in self.index_by_stem[target_lower]:
                        target_note.in_degree += 1
                        if target_note.vault_name != meta.vault_name:
                            self.bridges_cross_vault += 1
                            meta.cross_vault_links += 1

        # Identification des orphelins et des notes isolées
        for meta in self.notes_by_path.values():
            if meta.in_degree == 0 and meta.out_degree <= 1:
                self.orphans.append(meta)
            elif meta.out_degree > 0 and meta.cross_vault_links == 0:
                self.isolated_vault.append(meta)

        if verbose:
            print(f"✅ Connectome scanné : {scanned_count} notes répertoriées dans {len(self.vaults_to_scan)} coffres.")
            print(f"🔗 Total Wikilinks : {self.total_links} | Ponts Trans-Coffres existants : {self.bridges_cross_vault}")
            print(f"⚠️  Nœuds Orphelins détectés : {len(self.orphans)} | Notes Isolées dans leur coffre : {len(self.isolated_vault)}")

        return scanned_count

    def compute_resonance(self, note: NoteMeta) -> Dict[str, Any]:
        """Calcule l'affinité R0 avec les 11 DOIs Zenodo, les Pôles Souverains et les autres coffres."""
        text = note.text_for_matching
        words_in_text = set(re.findall(r"\b[a-zA-Z0-9_\-\+]{3,}\b", text))

        # 1. Matching avec les 11 Publications Zenodo
        best_zenodo = None
        best_zenodo_score = 0
        for pub in PUBLICATIONS_ZENODO:
            score = 0
            for kw in pub["keywords"]:
                if kw in text:
                    # Mot-clé multi-mots
                    score += 4 if " " in kw else 2
            if score > best_zenodo_score:
                best_zenodo_score = score
                best_zenodo = pub

        # 2. Matching avec les Grands Pôles Souverains
        best_pole = None
        best_pole_score = 0
        for pole in POLES_SOUVERAINS:
            score = 0
            for kw in pole["keywords"]:
                if kw in text:
                    score += 4 if " " in kw else 2
            if score > best_pole_score:
                best_pole_score = score
                best_pole = pole

        # 3. Matching avec les notes d'autres coffres (Ponts Trans-Coffres)
        cross_candidates = []
        # On extrait les mots caractéristiques de la note (> 4 lettres, non triviaux)
        keywords_note = [w for w in words_in_text if len(w) >= 5 and w not in {
            "cette", "notre", "leurs", "dans", "avec", "pour", "plus", "tout", "tous", "faire", "comme"
        }]

        # Recherche rapide dans les autres coffres
        for other_stem, other_list in self.index_by_stem.items():
            for other_note in other_list:
                # Éviter le même coffre et les liens déjà existants
                if other_note.vault_name == note.vault_name:
                    continue
                if other_note.stem in note.wikilinks or note.stem in other_note.wikilinks:
                    continue
                # Éviter de lier des notes génériques de navigation
                if other_note.stem.startswith("00_") or "index" in other_note.stem.lower():
                    continue

                # Calcul du chevauchement de titre et tags
                score = 0
                other_stem_words = set(re.findall(r"\b[a-zA-Z0-9_\-\+]{4,}\b", other_note.stem.lower()))
                overlap = words_in_text.intersection(other_stem_words)
                score += len(overlap) * 5

                # Chevauchement de tags
                common_tags = note.tags.intersection(other_note.tags)
                score += len(common_tags) * 3

                if score >= 5:
                    cross_candidates.append((score, other_note))

        cross_candidates.sort(key=lambda x: x[0], reverse=True)
        top_cross_notes = [cand[1] for cand in cross_candidates[:3]]

        return {
            "zenodo": best_zenodo if best_zenodo_score >= 3 else None,
            "zenodo_score": best_zenodo_score,
            "pole": best_pole if best_pole_score >= 2 else None,
            "pole_score": best_pole_score,
            "cross_notes": top_cross_notes,
        }

    def generate_synaptic_block(self, note: NoteMeta, resonance: Dict[str, Any]) -> str:
        """Formate le bloc synaptique standardisé et idempotent."""
        zenodo = resonance.get("zenodo")
        pole = resonance.get("pole")
        cross_notes = resonance.get("cross_notes", [])

        # Rénovation 5.4 : plus de pôle ni de publication PAR DÉFAUT. Un lien n'est écrit
        # que si un vrai recoupement l'a justifié (avant : 2 164 liens sur 2 758 étaient des défauts).
        if not pole and not zenodo and not cross_notes:
            return ""

        lines = [
            SYNAPTIC_SECTION_HEADER,
            "> *Connectome Exocerveau Souverain — Maillage tissé par le Grand Tisseur Synaptique (Horus × Munin).*",
        ]
        if pole:
            lines.append(f"- **🏛️ Pôle Souverain :** {pole['ancrage']} — *{pole['nom']}*")
        if zenodo:
            lines.append(f"- **📄 Publication Zenodo R0 :** {zenodo['ancrage']} *(DOI: [{zenodo['doi']}]({zenodo['url']}))*")

        if cross_notes:
            lines.append("- **🌐 Résonances Trans-Coffres :**")
            for cn in cross_notes:
                lines.append(f"  - ⚡ `[{cn.vault_name}]` [[{cn.stem}]] — *Résonance topologique active*")


        # Tags sémantiques recommandés
        suggested_tags = ["#connectome_r0", "#tissage_universel"]
        if zenodo:
            suggested_tags.append(f"#{zenodo['id'].lower()}")
        if pole:
            suggested_tags.append(f"#{pole['id'].lower()}")
        lines.append(f"- **🏷️ Vecteurs Thématiques :** {' '.join(suggested_tags)}")
        lines.append("")

        return "\n".join(lines)

    def weave_note(self, note: NoteMeta, dry_run: bool = False) -> bool:
        """Injecte ou actualise de manière chirurgicale le bloc synaptique dans la note."""
        # Rénovation 5.4 : le tisseur n'écrit jamais dans le Canon de Christian.
        if "00_CANON_SOUVERAIN_CHRISTIAN" in str(note.path).replace("\\", "/"):
            return False
        resonance = self.compute_resonance(note)
        block = self.generate_synaptic_block(note, resonance)
        if not block:
            return False

        original_content = note.content

        if SYNAPTIC_SECTION_HEADER in original_content:
            # Remplacement propre de la section existante
            # On cherche de SYNAPTIC_SECTION_HEADER jusqu'au prochain titre '## ' ou fin du document
            pattern = re.compile(rf"{re.escape(SYNAPTIC_SECTION_HEADER)}.*?(?=\n## |\Z)", re.DOTALL)
            new_content = pattern.sub(block.strip(), original_content)
        else:
            # Ajout en pied de page propre
            sep = "\n\n---\n\n" if not original_content.rstrip().endswith("---") else "\n\n"
            new_content = original_content.rstrip() + sep + block

        if not dry_run:
            try:
                note.path.write_text(new_content, encoding="utf-8")
                note.content = new_content
                note.has_synaptic_block = True
                return True
            except Exception as e:
                print(f"❌ Erreur écriture sur {note.path.name}: {e}")
                return False
        return True

    def weave_batch(self, batch_size: int = 20, dry_run: bool = False, priority_folder: Optional[str] = None) -> List[NoteMeta]:
        """Tisse un lot de notes prioritaires (orphelins absolus, découvertes, notes isolées)."""
        candidates: List[NoteMeta] = []

        # 1. Priorité absolue : les 22 notes orphelines (degré entrant 0)
        for meta in self.orphans:
            if not meta.has_synaptic_block:
                candidates.append(meta)

        # 2. Deuxième priorité : Monde_des_Decouvertes de Cerveau Alix sans bloc
        for meta in self.notes_by_path.values():
            if "Monde_des_Decouvertes" in str(meta.path) and not meta.has_synaptic_block:
                if meta not in candidates:
                    candidates.append(meta)

        # 3. Troisième priorité : notes isolées sans ponts trans-coffres
        for meta in self.isolated_vault:
            if not meta.has_synaptic_block and meta not in candidates:
                candidates.append(meta)

        # 4. Reste des notes non tissées
        if len(candidates) < batch_size:
            for meta in self.notes_by_path.values():
                if not meta.has_synaptic_block and meta not in candidates:
                    candidates.append(meta)
                    if len(candidates) >= batch_size:
                        break

        batch = candidates[:batch_size]
        woven = []
        action_str = "Simulation Tissage" if dry_run else "Tissage Synaptique"
        print(f"\n🪢 [{action_str}] Lancement sur un lot de {len(batch)} notes prioritaires...")

        for idx, note in enumerate(batch, 1):
            success = self.weave_note(note, dry_run=dry_run)
            if success:
                woven.append(note)
                print(f"  [{idx:02d}/{len(batch):02d}] ⚡ Tissé : {note.path.name} ({note.vault_name})")
            if not dry_run:
                time.sleep(0.01)  # Throttling I/O doux

        return woven

    def generate_universal_atlas(self, last_woven: Optional[List[NoteMeta]] = None) -> str:
        """Génère l'Atlas Synaptique de l'Exocerveau avec métriques et hubs."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_notes = len(self.notes_by_path)
        with_synaptic = sum(1 for n in self.notes_by_path.values() if n.has_synaptic_block)
        pct_woven = (with_synaptic / total_notes * 100) if total_notes > 0 else 0.0

        # Stats par coffre
        vault_stats = {}
        for name, p in self.vaults_to_scan.items():
            notes_in_vault = [n for n in self.notes_by_path.values() if n.vault_name == name]
            woven_in_vault = sum(1 for n in notes_in_vault if n.has_synaptic_block)
            cross_in_vault = sum(n.cross_vault_links for n in notes_in_vault)
            vault_stats[name] = {
                "total": len(notes_in_vault),
                "woven": woven_in_vault,
                "cross_links": cross_in_vault
            }

        md_content = f"""# 🌌 ATLAS DU CONNECTOME SYNAPTIQUE UNIVERSEL
> **Architecture Souveraine :** VERALUME × KAIROS V6 — Atelier Christian Duguay & Alix  
> **Dernière Cartographie :** `{now_str}`  
> **Moteur :** Grand Tisseur Synaptique v1.0 (Horus SRE × Munin × Thot)  
> **État du Connectome :** ⚡ **ACTIF & MAILLÉ EN TEMPS RÉEL**  

---

## 📊 1. Indicateurs Globaux du Connectome

| Métrique Fondamentale | Valeur Observée | Interprétation KAIROS |
| :--- | :---: | :--- |
| **Notes Indexées (Total Coffres)** | **{total_notes}** notes | Matière brute totale sous surveillance active |
| **Densité des Liens (Wikilinks)** | **{self.total_links}** arêtes | Connectivité interne brute |
| **Ponts Synaptiques Trans-Coffres** | **{self.bridges_cross_vault}** ponts | Liaisons franchissant les frontières des coffres |
| **Notes Tissées avec Bloc R0** | **{with_synaptic}** ({pct_woven:.1f}%) | Nœuds formellement arrimés aux 11 DOIs & Pôles |
| **Nœuds Orphelins Résiduels** | **{len(self.orphans)}** orphelins | Cibles prioritaires pour les prochains cycles |
| **Notes Isolées Intra-Coffre** | **{len(self.isolated_vault)}** notes | En attente de greffe trans-coffres |

---

## 🏛️ 2. Répartition par Coffres Souverains

| Coffre de l'Exocerveau | Notes Totales | Notes Tissées R0 | Ponts Trans-Coffres | Statut Maillage |
| :--- | :---: | :---: | :---: | :---: |
"""
        for vname, vdata in vault_stats.items():
            ratio = (vdata["woven"] / vdata["total"] * 100) if vdata["total"] > 0 else 0.0
            status_ico = "🟢 Maillé" if ratio > 50 else ("🟡 En cours" if ratio > 5 else "⚪ En veille")
            md_content += f"| **{vname}** | {vdata['total']} | {vdata['woven']} ({ratio:.1f}%) | {vdata['cross_links']} | {status_ico} |\n"

        md_content += """
---

## 📄 3. Ancrage aux 11 Publications Zenodo / CERN

Chaque nœud de l'Exocerveau résonne avec l'un de nos 11 préprints fondamentaux :

| N° | Publication Zenodo | DOI Officiel | Pôle Associé | Ancrage Master |
| :---: | :--- | :---: | :--- | :---: |
"""
        for pub in PUBLICATIONS_ZENODO:
            md_content += f"| **{pub['num']}** | **{pub['titre_fr']}** | [{pub['doi']}]({pub['url']}) | *{pub['pole']}* | `{pub['ancrage']}` |\n"

        md_content += """
---

## 🪢 4. Derniers Raccordements Synaptiques Réalisés

"""
        if last_woven:
            md_content += "| Horodatage | Note Tissée | Coffre Source | Pôle R0 Raccordé |\n| :--- | :--- | :--- | :--- |\n"
            for nw in last_woven[:25]:
                md_content += f"| {now_str} | [[{nw.stem}]] | `{nw.vault_name}` | ⚡ Raccordé R0 |\n"
        else:
            md_content += "*Le registre des derniers tissages sera incrémenté lors du prochain cycle actif.*\n"

        md_content += f"""
---
*Atlas généré automatiquement par [[alix_grand_tisseur_synaptique.py]].*
"""

        # Sauvegarde sur les deux emplacements maîtres
        try:
            ATLAS_FILE_ALIX.parent.mkdir(parents=True, exist_ok=True)
            ATLAS_FILE_ALIX.write_text(md_content, encoding="utf-8")
            print(f"📖 Atlas Universel généré dans Cerveau Alix : {ATLAS_FILE_ALIX.name}")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde Atlas Cerveau Alix : {e}")

        try:
            ATLAS_FILE_MASTER.parent.mkdir(parents=True, exist_ok=True)
            ATLAS_FILE_MASTER.write_text(md_content, encoding="utf-8")
            print(f"📖 Atlas Universel répliqué dans Exocerveau Master : {ATLAS_FILE_MASTER.name}")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde Atlas Master : {e}")

        return md_content

    def save_state(self, last_woven_count: int = 0):
        """Sauvegarde l'état live pour le rapport quotidien et Bonjour Alix."""
        total_notes = len(self.notes_by_path)
        with_synaptic = sum(1 for n in self.notes_by_path.values() if n.has_synaptic_block)

        state = {
            "nom": "Grand Tisseur Synaptique de l'Exocerveau",
            "derniere_execution": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "statut": "🟢 OPÉRATIONNEL & ACTIF",
            "total_coffres": len(self.vaults_to_scan),
            "total_notes": total_notes,
            "total_liens": self.total_links,
            "ponts_trans_coffres": self.bridges_cross_vault,
            "notes_tissees": with_synaptic,
            "orphelins_restants": len(self.orphans),
            "isolees_restantes": len(self.isolated_vault),
            "dernier_lot_tisse": last_woven_count
        }

        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print(f"💾 État persistant sauvegardé : {STATE_FILE.name}")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde state : {e}")


# ==============================================================================
# ROUTINE PRINCIPALE & CLI
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Grand Tisseur Synaptique de l'Exocerveau Souverain")
    parser.add_argument("--scan-only", action="store_true", help="Audit complet et atlas sans modification de notes")
    parser.add_argument("--weave-batch", type=int, default=0, help="Tisse un lot de N notes prioritaires (ex: 20)")
    parser.add_argument("--weave-all", action="store_true", help="Tisse l'ensemble des notes éligibles avec temporisation")
    parser.add_argument("--target-note", type=str, default="", help="Chemin vers une note spécifique à tisser")
    parser.add_argument("--vault", type=str, default="", help="Cible un coffre spécifique")
    parser.add_argument("--daemon", action="store_true", help="Tourne en continu en arrière-plan")
    parser.add_argument("--interval-hours", type=float, default=6.0, help="Intervalle du daemon en heures (défaut: 6)")

    args = parser.parse_args()

    selected_vaults = [args.vault] if args.vault else None
    tisseur = GrandTisseurSynaptique(target_vaults=selected_vaults)

    # 1. Mode Note Cible Unique
    if args.target_note:
        p = Path(args.target_note)
        if not p.exists():
            print(f"❌ Fichier introuvable : {p}")
            sys.exit(1)
        tisseur.index_all_vaults(verbose=False)
        vault_name = detect_vault_for_path(p)
        meta = NoteMeta(p, vault_name)
        meta.load_and_parse()
        success = tisseur.weave_note(meta, dry_run=False)
        if success:
            print(f"✅ Note cible tissée avec succès : {p.name} (Coffre : {vault_name})")
        sys.exit(0)

    # 2. Mode Démon Permanent
    if args.daemon:
        print(f"🌟 [DAEMON TISSEUR] Démarrage de la sentinelle de connectome (cycle = {args.interval_hours}h)...")
        while True:
            tisseur.index_all_vaults(verbose=True)
            woven = tisseur.weave_batch(batch_size=25, dry_run=False)
            tisseur.generate_universal_atlas(last_woven=woven)
            tisseur.save_state(last_woven_count=len(woven))
            print(f"💤 Mise en veille pour {args.interval_hours} heures...")
            time.sleep(args.interval_hours * 3600)

    # 3. Mode Scan Simple
    tisseur.index_all_vaults(verbose=True)

    if args.scan_only:
        tisseur.generate_universal_atlas()
        tisseur.save_state(last_woven_count=0)
        print("🎯 Scan terminé avec succès. Aucun fichier de note n'a été altéré.")
        return

    # 4. Mode Batch
    batch_count = args.weave_batch if args.weave_batch > 0 else (50 if args.weave_all else 20)
    woven = tisseur.weave_batch(batch_size=batch_count, dry_run=False)
    tisseur.generate_universal_atlas(last_woven=woven)
    tisseur.save_state(last_woven_count=len(woven))
    print(f"\n🎉 [SUCCÈS] Cycle achevé : {len(woven)} notes ont reçu leur greffe synaptique R0.")


if __name__ == "__main__":
    main()
