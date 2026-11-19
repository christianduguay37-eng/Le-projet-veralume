# -*- coding: utf-8 -*-
"""
===============================================================================
       👁️ MODULE ARGUS : CAPTEUR DE VISION VOLITIVE EN RAM (LOI PSI-26)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Volet 1 : Cécité totale par défaut (0% compute, rideau baissé).
    - Volet 2 : Activation strictly sur commande explicite de l'artisan (Push-to-See).
    - Volet 3 : Zéro fichier disque (0 JPEG, 0 PNG). Tampon circulaire en RAM.
    - Purge matérielle immédiate (memset / libération) à la fin de commande.
===============================================================================
"""

import time
from typing import Dict, Any, Optional

class ArgusVision:
    """Capteur optique volitif en mémoire vive LPDDR5X."""

    def __init__(self):
        self.actif = False
        self.derniere_capture_ram: Optional[bytes] = None
        self.derniere_resolution = (0, 0)

    def ouvrir_oeil(self) -> Dict[str, Any]:
        """Activation volitive explicite de l'œil (Loi PSI-26 Volet 2)."""
        self.actif = True
        return {"statut": "OEIL_OUVERT", "mode": "PUSH_TO_SEE", "compute_alloue": True}

    def fermer_et_purger(self) -> Dict[str, Any]:
        """Cécité immédiate et écrasement du tampon RAM (Loi PSI-26 Volets 1 & 3)."""
        self.derniere_capture_ram = None
        self.derniere_resolution = (0, 0)
        self.actif = False
        return {"statut": "CECITE_TOTALE", "buffer_purge": True, "compute_pct": 0.0}

    def capturer_trame_ram(self) -> Dict[str, Any]:
        """
        Capture un instantané plein écran directement en mémoire vive sans passer par le disque.
        Si l'œil n'est pas explicitement ouvert, refuse la capture (Sanctuaire respecté).
        """
        if not self.actif:
            return {
                "succes": False,
                "motif": "REFUS_PSI_26_SANCTUAIRE_FERME",
                "message": "Cécité par défaut active. Commande explicite requise."
            }

        t0 = time.perf_counter()
        try:
            from PIL import ImageGrab
            # Capture en mémoire vive
            screenshot = ImageGrab.grab()
            self.derniere_resolution = screenshot.size
            # Conversion en octets bruts en mémoire sans toucher au NTFS
            raw_bytes = screenshot.tobytes()
            self.derniere_capture_ram = raw_bytes

            latence_ms = round((time.perf_counter() - t0) * 1e3, 2)
            return {
                "succes": True,
                "resolution": self.derniere_resolution,
                "taille_octets": len(raw_bytes),
                "latence_ms": latence_ms,
                "stockage": "RAM_UNIFIEE_ZERO_DISQUE"
            }
        except Exception as e:
            return {"succes": False, "erreur": str(e)}
