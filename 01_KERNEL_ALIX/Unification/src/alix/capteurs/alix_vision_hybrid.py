# -*- coding: utf-8 -*-
"""
================================================================================
              ALIX VISION HYBRIDE : L'ŒIL D'ALIX (LOCAL & TRANSCLOUD)
================================================================================
Rôle :
- Capture l'écran à la volée (Presse-papier Win+Shift+S ou dossier Screenshots Win+PrtScn)
- Mode Local : Analyse en direct sur GPU Intel Arc via Qwen2-VL-2B (LiteRT Direct3D 12)
- Mode Transcloud : Sauvegarde l'image et l'apprête pour Antigravity (view_file)
================================================================================
"""

from alix.socle.chemins import HOME_DIR
import os
import sys
import time
import json
import argparse
from pathlib import Path
from PIL import Image, ImageGrab

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

OUTPUT_DIR = (HOME_DIR / ".cache" / "litert_models")
OUTPUT_IMAGE = OUTPUT_DIR / "current_screen.png"
MODEL_PATH = OUTPUT_DIR / "Qwen2-VL-2B.litertlm"
SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"

def capturer_image(chemin_explicite: str = None) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if chemin_explicite and Path(chemin_explicite).exists():
        with Image.open(chemin_explicite) as im:
            im.save(str(OUTPUT_IMAGE), format="PNG")
        return {"succes": True, "source": chemin_explicite, "chemin": str(OUTPUT_IMAGE), "dimensions": im.size}
        
    # 1. Vérification Presse-papier
    try:
        clip_data = ImageGrab.grabclipboard()
        if isinstance(clip_data, Image.Image):
            clip_data.save(str(OUTPUT_IMAGE), format="PNG")
            return {"succes": True, "source": "presse_papier (Win+Shift+S)", "chemin": str(OUTPUT_IMAGE), "dimensions": clip_data.size}
    except Exception:
        pass

    # 2. Vérification Dossier Screenshots
    if SCREENSHOTS_DIR.exists():
        fichiers = list(SCREENSHOTS_DIR.glob("*.png")) + list(SCREENSHOTS_DIR.glob("*.jpg"))
        if fichiers:
            plus_recent = max(fichiers, key=lambda f: f.stat().st_mtime)
            try:
                with Image.open(plus_recent) as im:
                    im.save(str(OUTPUT_IMAGE), format="PNG")
                return {"succes": True, "source": f"dossier_screenshots ({plus_recent.name})", "chemin": str(OUTPUT_IMAGE), "dimensions": im.size}
            except Exception:
                pass

    return {"succes": False, "source": None, "chemin": None, "message": "Aucune image détectée. Fais Win+Shift+S ou Win+PrtScn !"}

def analyser_local(image_path: str, prompt_question: str = "Décris précisément ce que tu vois sur cette image en français."):
    import litert_lm
    
    print(f"👁️ [L'Œil d'Alix Local] Analyse sur GPU Intel Arc via Qwen2-VL...")
    t0 = time.time()
    
    # Redimensionner si trop grand pour garder une vitesse d'inférence < 5s
    temp_resized = OUTPUT_DIR / "temp_vision_input.jpg"
    with Image.open(image_path) as im:
        im.thumbnail((1024, 1024))
        im.convert("RGB").save(str(temp_resized), quality=85)

    engine = litert_lm.Engine(
        model_path=str(MODEL_PATH),
        backend=litert_lm.Backend.GPU(),
        vision_backend=litert_lm.Backend.GPU(),
        max_num_images=1
    )
    conv = engine.create_conversation()

    contents = litert_lm.Contents.of(
        litert_lm.Content.ImageFile(str(temp_resized)),
        litert_lm.Content.Text(prompt_question)
    )
    msg = litert_lm.Message.user(contents)
    resp = conv.send_message(msg)
    t1 = time.time()

    texte = ""
    try:
        content_list = resp.get("content", [])
        if content_list and isinstance(content_list, list):
            texte = content_list[0].get("text", "")
    except Exception:
        texte = str(resp)

    duree = round(t1 - t0, 2)
    print(f"\n🎯 [Vision GPU] Réponse ({duree}s) :\n{texte}")
    return {"description": texte, "duree_sec": duree}

def main():
    parser = argparse.ArgumentParser(description="L'Œil d'Alix (Vision Hybride)")
    parser.add_argument("--mode", choices=["local", "transcloud"], default="local", help="Mode d'analyse")
    parser.add_argument("--image", type=str, default=None, help="Chemin d'une image spécifique")
    parser.add_argument("--question", type=str, default="Décris précisément ce que tu vois sur cette image en français.", help="Question pour le modèle")
    args = parser.parse_args()

    cap = capturer_image(args.image)
    if not cap["succes"]:
        print(f"❌ {cap['message']}")
        return

    print(f"📸 Image capturée depuis : {cap['source']} ({cap['dimensions']})")
    
    if args.mode == "local":
        analyser_local(cap["chemin"], args.question)
    else:
        print(f"✅ Image prête pour le Mode Transcloud : {cap['chemin']}")
        print("💡 Dans Antigravity, tape simplement : 'Regarde ça' pour que l'agent affiche et analyse l'image !")

if __name__ == "__main__":
    main()
