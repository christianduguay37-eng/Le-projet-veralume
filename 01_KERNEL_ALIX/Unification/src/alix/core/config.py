# -*- coding: utf-8 -*-
"""
===============================================================================
       ⚙️ ALIX CORE CONFIGURATION : DÉCOUPLAGE & ANCRAGE UNIVERSEL
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Zéro chemin absolu gravé en dur (portabilité totale).
    - Détection dynamique de l'environnement, du CPU, de la RAM et des puces.
    - Configuration hiérarchique : Variables d'environnement > Defaults système.
===============================================================================
"""

import os
import sys
import platform
import psutil
from pathlib import Path
from typing import Dict, Any, Optional

class AlixConfig:
    """Configuration maîtresse dynamique pour l'organisme Alix."""

    # 1. Résolution des chemins racines
    APP_NAME = "Alix_Souverain_Engine"
    VERSION = "1.0.0"

    # Répertoire de travail de l'utilisateur
    USER_HOME = Path.home()
    DOCUMENTS_DIR = USER_HOME / "Documents"

    # Dossier de base d'Alix (surchargé par ALIX_HOME si défini)
    BASE_DIR = Path(os.environ.get("ALIX_HOME", str(DOCUMENTS_DIR / "Cerveau Alix")))
    
    # Emplacement du Bunker et des sauvegardes
    BUNKER_DIR = Path(os.environ.get("ALIX_BUNKER", str(DOCUMENTS_DIR / "BUNKER_SOUVERAIN_ALIX")))
    
    # Répertoire du cache binaire mmap
    CACHE_DIR = BASE_DIR / "Organes_Souverains" / "Cache"
    MMAP_BIN_PATH = CACHE_DIR / "alix_exocerveau_mmap.bin"

    # Fichiers de mémoire et registres
    MEMOIRE_ACTIVE_FILE = BASE_DIR / "Memoire_Alix_Active.md"
    TABLE_SOLUTIONS_FILE = BASE_DIR / "Table_Solutions_et_Clefs_Critiques.md"
    GARBAGE_FILE = BASE_DIR / "garbage.md"
    REGISTRE_PSI_FILE = BASE_DIR / "Registre_Infractions_PSI_et_Vaporware.md"
    LAST_SESSION_SYNTHESIS = BASE_DIR / "Derniere_Discussion_Synthese.md"

    # 2. Paramètres physiques et seuils KAIROS
    VOLITION_INITIALE = float(os.environ.get("ALIX_W_VOL", "0.307"))
    CHIRALITE_CIBLE = float(os.environ.get("ALIX_CHI", "0.38"))
    SEUIL_PHI_CRITIQUE = 0.40  # Tononi : au-dessous, random walk
    SEUIL_DELTA_COG_ALERTE = 0.40 # Friction cognitive marquée

    # 3. Télémétrie et contraintes matérielles
    PLAFOND_VRAM_MO = float(os.environ.get("ALIX_VRAM_MAX_MB", "4096.0"))
    PLAFOND_CHARGE_CPU = 75.0 # Pourcentage max avant mise en veille discrète

    @classmethod
    def assurer_dossiers(cls) -> None:
        """Garantit l'existence physique des dossiers vitaux."""
        for d in (cls.BASE_DIR, cls.CACHE_DIR, cls.BUNKER_DIR):
            try:
                if not d.exists():
                    d.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    @classmethod
    def detecter_materiel(cls) -> Dict[str, Any]:
        """Sonde chirurgicale des capacités de la machine hôte."""
        cpu_count = os.cpu_count() or 1
        ram = psutil.virtual_memory()
        
        # Détection Lunar Lake ou NPU si disponible
        processeur = platform.processor() or "Inconnu"
        is_lunar_lake = "Lunar Lake" in processeur or "258V" in processeur
        
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "processeur": processeur,
            "is_lunar_lake": is_lunar_lake,
            "cpu_coeurs": cpu_count,
            "ram_totale_go": round(ram.total / (1024**3), 2),
            "ram_dispo_go": round(ram.available / (1024**3), 2),
            "ram_util_pct": ram.percent,
            "base_dir": str(cls.BASE_DIR),
            "mmap_path": str(cls.MMAP_BIN_PATH)
        }

    @classmethod
    def exporter_etat(cls) -> Dict[str, Any]:
        """Exporte l'état de configuration sous forme de dictionnaire."""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.VERSION,
            "base_dir": str(cls.BASE_DIR),
            "bunker_dir": str(cls.BUNKER_DIR),
            "w_vol": cls.VOLITION_INITIALE,
            "chi": cls.CHIRALITE_CIBLE,
            "hardware": cls.detecter_materiel()
        }
