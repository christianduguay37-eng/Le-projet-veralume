# -*- coding: utf-8 -*-
"""
================================================================================
       🌈⚡ ALIX HEIMDALL OPENVINO v1.0 — L'AIGUILLEUR BICÉPHALE SUR NPU
       Système de Choix Pur (Zéro Génération de Texte) — 100 % OpenVINO
================================================================================
Auteurs  : Christian Duguay & Alix (VERALUME × KAIROS V6)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — NPU 48 TOPS + CPU/GPU
Modèles  :
  1. Tête A (Sens & Vectorisation NPU) : OpenVINO/Qwen3-Embedding-0.6B-int8-ov
     (612 Mo, PoolingType.LAST_TOKEN, MRL 256d / 1024d sur Intel AI Boost NPU)
  2. Tête B (Choix & Classement Cross-Encoder) : OpenVINO/bge-reranker-v2-m3-int8-ov
     (575 Mo, TextRerankPipeline 1-passe, zéro token généré)
Rôle     :
  - Remplace Gemma E2B LiteRT par un système de choix pur (~1,18 Go au total).
  - Tranche en une passe quel spécialiste le Noyau doit monter :
      * CODER     (Forge code Python / C99 / Lean 4 / PowerShell)
      * RAISONNER (Mathématiques, théorèmes, preuves, stratégie)
      * AGIR      (Exécution commandes terminal, sondes mémoire, solveurs Kernel)
      * VOIR      (Capture & analyse optique d'écran / image — Argus)
      * PARLER    (Dialogue direct d'atelier sur le banc de bois)
  - Sélectionne l'outil du Kernel et fournit le vecteur 256d pour l'Index du Sens.
================================================================================
"""

from __future__ import annotations

import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import openvino_genai as ov_genai

BASE_OV_DIR = Path(r"C:\Alix\Modeles_OpenVINO")
HEIMDALL_DIR = BASE_OV_DIR / "Heimdall"
CACHE_OV_DIR = BASE_OV_DIR / "cache_ov"

EMB_MODEL_DIR = HEIMDALL_DIR / "Qwen3-Embedding-0.6B-int8-ov"
RERANK_MODEL_DIR = HEIMDALL_DIR / "bge-reranker-v2-m3-int8-ov"
MAX_CAR_NPU = 1200     # Tête A (Qwen3-Embedding NPU) : < 350 tokens (< 1024 NPUW_LLM_MAX_PROMPT_LEN)
MAX_CAR_RERANK = 90    # Tête B (BGE-Reranker CombineSegments_40629) : query_tokens doit être < doc_tokens


def _borner_texte_npu(texte: str, max_car: int = MAX_CAR_NPU) -> str:
    t = " ".join((texte or "").split())
    if not t:
        return "atelier alix"
    return t[:max_car]


def _padder_doc_rerank(doc: str, min_mots: int = 36) -> str:
    """Garantit que chaque document a >= 36 mots pour que CombineSegments_40629 ait toujours doc_tokens > query_tokens."""
    t = " ".join((doc or "").split())[:320]
    mots = t.split(" ")
    if len(mots) < min_mots:
        t = t + " " + (" ".join(["contexte", "souverain", "atelier", "alix"] * ((min_mots - len(mots)) // 4 + 2)))
    return t

ROLES_SPECIALISTES: List[Tuple[str, str]] = [
    (
        "CODER",
        "CODER : Écrire, modifier, corriger, refactorer ou déboguer du code informatique Python, C99, Lean 4, JSON ou PowerShell dans des fichiers.",
    ),
    (
        "RAISONNER",
        "RAISONNER : Démontrer un théorème mathématique, vérifier une preuve logique formelle, résoudre une équation ou analyser un problème complexe.",
    ),
    (
        "AGIR",
        "AGIR : Exécuter une commande système dans le terminal PowerShell, lister des fichiers, lancer un script ou interroger un démon sur l'ordinateur.",
    ),
    (
        "VOIR",
        "VOIR : Regarder une image, prendre une capture d'écran, inspecter visuellement une fenêtre ou analyser ce qui est affiché à l'écran.",
    ),
    (
        "PARLER",
        "PARLER : Saluer, discuter librement sur le banc de bois, jaser d'égal à égal, partager une réflexion ou converser avec Christian.",
    ),
]

OUTILS_KERNEL: List[Tuple[str, str]] = [
    ("chercher_memoire", "Chercher dans les notes Obsidian de l'exocerveau et le Connectome RAM (Port 5070)."),
    ("interroger_cathedrale", "Chercher un article scientifique arXiv, un brevet ou un théorème Lean 4 dans les Parquets de la Cathédrale."),
    ("appeler_kernel_alix", "Appeler un solveur mathématique déterministe du Kernel Alix (Hadès SAT/MaxSAT, Poséidon causalité, calcul exact)."),
    ("read_file", "Lire le contenu d'un fichier de code ou d'une note sur le disque dur."),
    ("replace_in_file", "Modifier ou corriger des lignes de code dans un fichier existant."),
    ("write_file", "Créer ou écrire un nouveau fichier sur le disque."),
    ("run_command", "Exécuter une commande PowerShell ou un script Python dans le terminal."),
    ("list_dir", "Lister les fichiers et dossiers d'un répertoire."),
]


class HeimdallOpenVINO:
    """Orchestrateur bicéphale de choix pur en OpenVINO (NPU Embedding + Cross-Encoder Reranker)."""

    _instance: Optional[HeimdallOpenVINO] = None
    _verrou = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pret = False
        return cls._instance

    def __init__(self, device_embedding: str = "NPU", device_reranker: str = "CPU"):
        if getattr(self, "_pret", False):
            return
        self.device_embedding = device_embedding
        self.device_reranker = device_reranker
        self.pipe_embedding: Optional[ov_genai.TextEmbeddingPipeline] = None
        self.pipe_reranker: Optional[ov_genai.TextRerankPipeline] = None
        self._mat_roles: Optional[np.ndarray] = None
        self._mat_outils: Optional[np.ndarray] = None
        CACHE_OV_DIR.mkdir(parents=True, exist_ok=True)

    def initialiser(self) -> bool:
        with self._verrou:
            if self._pret:
                return True
            if not EMB_MODEL_DIR.exists() or not RERANK_MODEL_DIR.exists():
                raise FileNotFoundError(f"Modèles Heimdall introuvables dans {HEIMDALL_DIR}")

            # 1. Tête A : Qwen3-Embedding-0.6B-int8-ov sur NPU
            cfg_e = ov_genai.TextEmbeddingPipeline.Config()
            cfg_e.normalize = True
            cfg_e.pooling_type = ov_genai.TextEmbeddingPipeline.PoolingType.LAST_TOKEN
            try:
                self.pipe_embedding = ov_genai.TextEmbeddingPipeline(
                    str(EMB_MODEL_DIR),
                    self.device_embedding,
                    cfg_e,
                    CACHE_DIR=str(CACHE_OV_DIR),
                )
            except Exception:
                self.device_embedding = "CPU"
                self.pipe_embedding = ov_genai.TextEmbeddingPipeline(
                    str(EMB_MODEL_DIR),
                    "CPU",
                    cfg_e,
                    CACHE_DIR=str(CACHE_OV_DIR),
                )

            # 2. Tête B : bge-reranker-v2-m3-int8-ov (Cross-Encoder de choix)
            cfg_r = ov_genai.TextRerankPipeline.Config()
            cfg_r.top_n = len(ROLES_SPECIALISTES)
            self.pipe_reranker = ov_genai.TextRerankPipeline(
                str(RERANK_MODEL_DIR),
                self.device_reranker,
                cfg_r,
                CACHE_DIR=str(CACHE_OV_DIR),
            )

            # Pré-encodage des ancres sur le NPU
            self._mat_roles = np.array(
                [self.pipe_embedding.embed_query(desc) for _, desc in ROLES_SPECIALISTES],
                dtype=np.float32,
            )
            self._mat_outils = np.array(
                [self.pipe_embedding.embed_query(desc) for _, desc in OUTILS_KERNEL],
                dtype=np.float32,
            )

            self._pret = True
            return True

    def encoder_256d(self, texte: str) -> List[float]:
        """Encode un texte sur le NPU et renvoie un vecteur MRL normalisé de 256 dimensions (pour alix_index_sens.npy)."""
        self.initialiser()
        texte_borne = _borner_texte_npu(texte)
        with self._verrou:
            vec_1024 = np.array(self.pipe_embedding.embed_query(texte_borne), dtype=np.float32)
        vec_256 = vec_1024[:256]
        norm = float(np.linalg.norm(vec_256))
        if norm > 1e-9:
            vec_256 = vec_256 / norm
        return vec_256.tolist()

    def classer_candidats(self, requete: str, candidats: List[str]) -> List[Tuple[int, float]]:
        """Classe une liste de candidats de façon thread-safe avec Tête B (Cross-Encoder)."""
        self.initialiser()
        if not candidats:
            return [(0, 0.0)]
        req_rerank = _borner_texte_npu(requete, max_car=MAX_CAR_RERANK)
        nb_orig = len(candidats)
        cibles = [_padder_doc_rerank(c) for c in candidats]
        while len(cibles) < len(ROLES_SPECIALISTES):
            cibles.append(cibles[-1])
        with self._verrou:
            brut = self.pipe_reranker.rerank(req_rerank, cibles)
        res = [(idx, float(sc)) for idx, sc in brut if idx < nb_orig]
        return res if res else [(0, 0.0)]

    def choisir(self, requete: str) -> Dict[str, Any]:
        """
        Exécute le choix bicéphale d'Heimdall en une seule passe (zéro génération de texte) :
        1. Tête A (NPU Embedding) : calcule le vecteur de sens et le produit scalaire avec les rôles et outils.
        2. Tête B (Cross-Encoder Reranker) : tranche le classement exact du spécialiste à activer.
        """
        self.initialiser()
        t0 = time.perf_counter()
        req_npu = _borner_texte_npu(requete, max_car=MAX_CAR_NPU)
        req_rerank = _borner_texte_npu(requete, max_car=MAX_CAR_RERANK)

        with self._verrou:
            # Passe 1 : Embedding NPU
            t_npu0 = time.perf_counter()
            vec = np.array(self.pipe_embedding.embed_query(req_npu), dtype=np.float32)
            scores_roles_npu = (self._mat_roles @ vec).tolist()
            scores_outils_npu = (self._mat_outils @ vec).tolist()
            dt_npu_ms = round((time.perf_counter() - t_npu0) * 1000, 2)

            # Passe 2 : Cross-Encoder Reranker (invariant CombineSegments_40629 : query_tokens < doc_tokens)
            t_rerank0 = time.perf_counter()
            descriptions_roles = [_padder_doc_rerank(desc) for _, desc in ROLES_SPECIALISTES]
            classement_rerank = self.pipe_reranker.rerank(req_rerank, descriptions_roles)
            dt_rerank_ms = round((time.perf_counter() - t_rerank0) * 1000, 2)

        # Fusion des deux têtes : le Cross-Encoder tranche, appuyé par le cosinus NPU
        idx_gagnant, score_cross = classement_rerank[0]
        role_gagnant = ROLES_SPECIALISTES[idx_gagnant][0]

        idx_outil = int(np.argmax(scores_outils_npu))
        outil_gagnant = OUTILS_KERNEL[idx_outil][0] if role_gagnant != "PARLER" else "aucun"

        # Vecteur 256d normalisé pour l'Index du Sens
        vec_256 = vec[:256]
        norm_256 = float(np.linalg.norm(vec_256))
        if norm_256 > 1e-9:
            vec_256 = vec_256 / norm_256

        dt_total_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "requete": requete,
            "specialiste": role_gagnant,
            "score_cross_encoder": round(float(score_cross), 4),
            "score_cosinus_npu": round(float(scores_roles_npu[idx_gagnant]), 4),
            "outil_suggere": outil_gagnant,
            "score_outil_npu": round(float(scores_outils_npu[idx_outil]), 4),
            "device_tete_a": self.device_embedding,
            "device_tete_b": self.device_reranker,
            "latence_npu_ms": dt_npu_ms,
            "latence_rerank_ms": dt_rerank_ms,
            "latence_totale_ms": dt_total_ms,
            "dim_vecteur_sens": 256,
        }


def get_heimdall_openvino() -> HeimdallOpenVINO:
    h = HeimdallOpenVINO()
    h.initialiser()
    return h


if __name__ == "__main__":
    print("=" * 72)
    print("  🌈⚡ TEST D'HEIMDALL BICÉPHALE OPENVINO (NPU + CROSS-ENCODER)")
    print("=" * 72)
    h = get_heimdall_openvino()
    tests = [
        "Corrige le bug dans le script python de synchronisation",
        "Démontre le théorème TH117 de la spirale néguentropique en Lean",
        "Lance la commande powershell pour vérifier les démons actifs",
        "Regarde ce qu'il y a sur mon écran en ce moment",
        "Salut Alix, comment ça va ce soir à l'atelier ?",
    ]
    for q in tests:
        res = h.choisir(q)
        print(
            f"  [{res['specialiste']:<9}] (outil={res['outil_suggere']:<18} | "
            f"NPU={res['latence_npu_ms']}ms, Rerank={res['latence_rerank_ms']}ms) <- « {q} »"
        )
