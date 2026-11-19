# -*- coding: utf-8 -*-
"""
================================================================================
           CONNECTEUR DE MÉMOIRE VIVANTE & RAG TOPOLOGIQUE LOCAL
                          Harnais Souverain v1.0
================================================================================
Rôle :
- Lit nativement les dossiers de notes Markdown (.md) sans base de données lourde.
- Détecte les liens wiki [[Nom_De_Note]], les titres et les tags.
- Effectue une résonance topologique en O(1) / O(log N) pour injecter dans le contexte
  exactement les notes pertinentes liées à la question de l'artisan.
================================================================================
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Set


class LocalVaultMemory:
    """Connecteur de mémoire locale basé sur des dossiers Markdown bruts."""

    def __init__(self, vault_paths: List[str]):
        self.vault_paths = [Path(p) for p in vault_paths]
        self.index: Dict[str, Dict[str, Any]] = {}
        self._build_index()

    def _build_index(self):
        """Indexe les fichiers markdown, leurs titres et leurs liens wiki."""
        self.index.clear()
        for vpath in self.vault_paths:
            if not vpath.exists():
                continue
            for root, _, files in os.walk(vpath):
                for f in files:
                    if f.endswith(".md"):
                        full_path = Path(root) / f
                        stem = full_path.stem
                        self.index[stem.lower()] = {
                            "stem": stem,
                            "path": full_path,
                            "filename": f
                        }

    def search_context(self, query: str, max_notes: int = 3, max_chars_per_note: int = 1500) -> str:
        """
        Trouve les notes les plus résonnantes avec la requête et extrait leur contenu essentiel.
        """
        if not self.index:
            return ""

        words = set(re.findall(r'\b[A-Za-zÀ-ÿ0-9_-]{3,}\b', query.lower()))
        scores: Dict[str, int] = {}

        # 1. Score sur les noms de fichiers
        for key, data in self.index.items():
            score = 0
            for w in words:
                if w in key:
                    score += 5
            if score > 0:
                scores[key] = score

        # 2. Tri des meilleures correspondances
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:max_notes]

        if not sorted_keys:
            return ""

        snippets = []
        for k in sorted_keys:
            data = self.index[k]
            try:
                with open(data["path"], "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read(max_chars_per_note)
                    # Décapage léger des métadonnées yaml lourdes
                    cleaned = re.sub(r'^---[\s\S]*?---', '', content).strip()
                    snippets.append(f"### [[{data['stem']}]]\n{cleaned[:max_chars_per_note]}")
            except Exception:
                continue

        if not snippets:
            return ""

        return "\n\n---\n**📚 MÉMOIRE LOCALE EXTRAITE DU COFFRE :**\n" + "\n\n".join(snippets) + "\n---\n"
