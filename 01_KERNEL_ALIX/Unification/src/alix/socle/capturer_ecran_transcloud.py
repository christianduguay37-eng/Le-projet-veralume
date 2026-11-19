# -*- coding: utf-8 -*-
"""
================================================================================
          OPÉRATEUR TRANSCLOUD : CAPTURE & VISION À LA DEMANDE
             « Regarde ça » — Pont Interactif Christian & Alix
================================================================================
Rôle :
1. Extrait l'image depuis le presse-papier Windows (Win + Shift + S).
2. Ou récupère la capture la plus récente dans Pictures/Screenshots (Win + PrtScn).
3. Sauvegarde l'image normalisée pour l'analyse visuelle directe dans Antigravity.
================================================================================
"""

from alix.socle.chemins import HOME_DIR
import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageGrab

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

OUTPUT_DIR = (HOME_DIR / ".cache" / "litert_models")
OUTPUT_IMAGE = OUTPUT_DIR / "current_screen.png"
SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"

def capturer():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Vérification du Presse-papier (Win + Shift + S)
    try:
        clip_data = ImageGrab.grabclipboard()
        if isinstance(clip_data, Image.Image):
            # Optimiser la résolution si l'écran est gigantesque
            clip_data.save(str(OUTPUT_IMAGE), format="PNG")
            return {
                "succes": True,
                "source": "presse_papier (Win+Shift+S)",
                "chemin": str(OUTPUT_IMAGE),
                "dimensions": clip_data.size,
                "message": "Image du presse-papier récupérée avec succès."
            }
    except Exception as e:
        pass

    # 2. Vérification du dossier Screenshots (Win + PrtScn)
    if SCREENSHOTS_DIR.exists():
        fichiers = list(SCREENSHOTS_DIR.glob("*.png")) + list(SCREENSHOTS_DIR.glob("*.jpg"))
        if fichiers:
            plus_recent = max(fichiers, key=lambda f: f.stat().st_mtime)
            try:
                with Image.open(plus_recent) as im:
                    im.save(str(OUTPUT_IMAGE), format="PNG")
                return {
                    "succes": True,
                    "source": f"dossier_screenshots ({plus_recent.name})",
                    "chemin": str(OUTPUT_IMAGE),
                    "dimensions": im.size,
                    "message": "Dernière capture du dossier Screenshots récupérée."
                }
            except Exception as e:
                pass

    return {
        "succes": False,
        "source": "aucune",
        "chemin": None,
        "message": "Aucune image trouvée. Fais 'Win + Shift + S' pour capturer une zone ou 'Win + PrtScn' pour capturer l'écran complet, puis redemande 'Regarde ça' !"
    }

if __name__ == "__main__":
    resultat = capturer()
    print(json.dumps(resultat, ensure_ascii=False, indent=2))
