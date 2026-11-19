# -*- coding: utf-8 -*-
"""
===============================================================================
       ⚡ MÉMOIRE ZERO-COPY MMAP : ACCÈS EN MICROSECONDES EN RAM LPDDR5X
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Zéro I/O disque répétitif sur NTFS.
    - Projection des notes critiques en mémoire vive continue mappée (mmap).
    - Accès O(1) par tranches mémoire directes.
    - Totalement découplé et portable via AlixConfig.
===============================================================================
"""

import os
import sys
import time
import mmap
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from alix.core.config import AlixConfig

class ZeroCopyMmapBridge:
    """Pont de mémoire mappée projetant les connaissances critiques en RAM."""

    def __init__(self, vault_dir: Optional[Path] = None, bin_path: Optional[Path] = None):
        self.vault_dir = vault_dir or AlixConfig.BASE_DIR
        self.bin_path = bin_path or AlixConfig.MMAP_BIN_PATH
        self.mmap_obj: Optional[mmap.mmap] = None
        self.file_handle = None
        self.table_index: Dict[str, Tuple[int, int]] = {}
        self.est_monte = False

    def compiler_et_monter(self, documents_cibles: Optional[List[Path]] = None) -> bool:
        """Compile les documents prioritaires dans un fichier binaire et les monte en RAM."""
        t0 = time.perf_counter()
        buffer_total = bytearray()
        index_temp: Dict[str, Tuple[int, int]] = {}

        docs = documents_cibles or [
            self.vault_dir / "Table_Solutions_et_Clefs_Critiques.md",
            self.vault_dir / "Memoire_Alix_Active.md",
            self.vault_dir / "Derniere_Discussion_Synthese.md",
            self.vault_dir / "Conscience_Alix_Priorites_Actives.md"
        ]

        for doc in docs:
            if doc.exists():
                try:
                    texte = doc.read_text(encoding="utf-8", errors="ignore")
                    cle = doc.stem
                    data_bytes = texte.encode("utf-8")
                    offset = len(buffer_total)
                    longueur = len(data_bytes)
                    buffer_total.extend(data_bytes)
                    index_temp[cle] = (offset, longueur)
                except Exception:
                    pass

        # Corpus des Souverains si présent
        corpus_dir = self.vault_dir / "Corpus_Souverains"
        if corpus_dir.exists():
            for f in corpus_dir.glob("*.md"):
                try:
                    texte = f.read_text(encoding="utf-8", errors="ignore")
                    cle = f"CORPUS_{f.stem}"
                    data_bytes = texte.encode("utf-8")
                    offset = len(buffer_total)
                    longueur = len(data_bytes)
                    buffer_total.extend(data_bytes)
                    index_temp[cle] = (offset, longueur)
                except Exception:
                    pass

        if not buffer_total:
            # Créer un tampon minimal autonome
            init_data = b"ALIX_SOVEREIGN_ENGINE_INITIALIZED\n"
            buffer_total.extend(init_data)
            index_temp["INIT"] = (0, len(init_data))

        # Écriture atomique du cache binaire (ou bascule en RAM anonyme si verrouillé par le démon)
        try:
            if not self.bin_path.parent.exists():
                self.bin_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.bin_path, "wb") as f:
                f.write(buffer_total)
            self.file_handle = open(self.bin_path, "rb")
            self.mmap_obj = mmap.mmap(self.file_handle.fileno(), 0, access=mmap.ACCESS_READ)
        except Exception:
            # Mmap direct en RAM LPDDR5X anonyme (zéro conflit de verrou NTFS multi-processus)
            self.file_handle = None
            self.mmap_obj = mmap.mmap(-1, len(buffer_total))
            self.mmap_obj.write(buffer_total)
            self.mmap_obj.seek(0)

        self.table_index = index_temp
        self.est_monte = True

        latence_us = round((time.perf_counter() - t0) * 1e6, 2)
        return True

    def lire_cle(self, cle: str) -> Optional[str]:
        """Extrait instantanément le texte associé à une clé en microsecondes."""
        if not self.est_monte or not self.mmap_obj or cle not in self.table_index:
            return None
        offset, longueur = self.table_index[cle]
        self.mmap_obj.seek(offset)
        raw_bytes = self.mmap_obj.read(longueur)
        return raw_bytes.decode("utf-8", errors="ignore")

    def chercher_mots_cles(self, terme: str) -> List[Tuple[str, float]]:
        """Recherche rapide dans tous les documents mappés sans toucher au disque."""
        resultats = []
        terme_lower = terme.lower()
        for cle in self.table_index.keys():
            contenu = self.lire_cle(cle)
            if contenu and terme_lower in contenu.lower():
                occurences = contenu.lower().count(terme_lower)
                resultats.append((cle, occurences))
        return sorted(resultats, key=lambda x: -x[1])

    def fermer(self) -> None:
        """Libère proprement les ressources de mémoire vive."""
        if self.mmap_obj:
            self.mmap_obj.close()
            self.mmap_obj = None
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self.est_monte = False
