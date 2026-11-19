# -*- coding: utf-8 -*-
"""
================================================================================
          ŒIL MULTIMODAL SOUVERAIN (MULTIMODAL VISION MODULE)
                          Harnais Souverain v1.0
================================================================================
Rôle :
- Permet au compagnon de la Dyade de VOIR en direct :
    * Capture instantanée du presse-papier (Win+Shift+S sous Windows).
    * Analyse d'images locales (JPG, PNG, WebP).
- Supporte 2 moteurs de vision 100% locaux :
    1. Google LiteRT-LM avec Qwen2-VL-2B sur GPU Intel Arc (Direct3D 12, < 4s).
    2. Ollama Multimodal (LLaVA, Moondream, Qwen2-VL, MiniCPM-V) via /api/generate.
================================================================================
"""

import os
import sys
import time
import json
import base64
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SovereignVision:
    """Module de vision multimodale locale."""

    def __init__(self, litert_model_path: Optional[str] = None, ollama_url: str = "http://127.0.0.1:11434",
                 ollama_model: str = "llava:7b"):
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model
        self.litert_model_path = litert_model_path
        self._litert_vision_engine = None

        if not self.litert_model_path:
            # Recherche auto dans le cache
            default_path = Path.home() / ".cache" / "litert_models" / "Qwen2-VL-2B.litertlm"
            if default_path.exists():
                self.litert_model_path = str(default_path)

    def capture_screen_or_clipboard(self, explicit_path: Optional[str] = None) -> Dict[str, Any]:
        """Capture l'image du presse-papier ou d'un fichier explicite."""
        if not PIL_AVAILABLE:
            return {"succes": False, "erreur": "Pillow (PIL) non installé. Fais 'pip install pillow'."}

        temp_dir = Path.home() / ".cache" / "harnais_vision"
        temp_dir.mkdir(parents=True, exist_ok=True)
        target_img = temp_dir / "input_vision.png"

        # 1. Chemin explicite
        if explicit_path and Path(explicit_path).exists():
            try:
                with Image.open(explicit_path) as im:
                    im.save(str(target_img), format="PNG")
                return {"succes": True, "chemin": str(target_img), "source": explicit_path}
            except Exception as e:
                return {"succes": False, "erreur": f"Impossible d'ouvrir l'image : {e}"}

        # 2. Presse-papier (Win+Shift+S)
        try:
            clip_data = ImageGrab.grabclipboard()
            if isinstance(clip_data, Image.Image):
                clip_data.save(str(target_img), format="PNG")
                return {"succes": True, "chemin": str(target_img), "source": "Presse-papier (Capture écran)"}
        except Exception:
            pass

        # 3. Dossier Screenshots de Windows
        screenshots_dir = Path.home() / "Pictures" / "Screenshots"
        if screenshots_dir.exists():
            files = list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg"))
            if files:
                latest = max(files, key=lambda f: f.stat().st_mtime)
                # Si pris dans les 2 dernières minutes
                if time.time() - latest.stat().st_mtime < 120:
                    with Image.open(latest) as im:
                        im.save(str(target_img), format="PNG")
                    return {"succes": True, "chemin": str(target_img), "source": f"Dossier Screenshots ({latest.name})"}

        return {
            "succes": False,
            "erreur": "Aucune image trouvée. Fais 'Win+Shift+S' pour capturer une zone ou indique le chemin d'un fichier."
        }

    def analyze(self, image_path: str, prompt: str = "Décris précisément cette image en français.") -> str:
        """Analyse l'image avec LiteRT GPU si disponible, sinon repli sur Ollama."""
        # Tentative 1 : LiteRT GPU (Ultra-rapide)
        if self.litert_model_path and Path(self.litert_model_path).exists():
            try:
                return self._analyze_litert(image_path, prompt)
            except Exception as e:
                print(f"[Vision] Repli sur Ollama car LiteRT a échoué : {e}")

        # Tentative 2 : Ollama Multimodal
        return self._analyze_ollama(image_path, prompt)

    def _analyze_litert(self, image_path: str, prompt: str) -> str:
        import litert_lm

        # Redimensionnement frugal
        resized_path = Path(image_path).parent / "resized_vision.jpg"
        with Image.open(image_path) as im:
            im.thumbnail((1024, 1024))
            im.convert("RGB").save(str(resized_path), quality=85)

        if not self._litert_vision_engine:
            self._litert_vision_engine = litert_lm.Engine(
                model_path=str(self.litert_model_path),
                backend=litert_lm.Backend.GPU(),
                vision_backend=litert_lm.Backend.GPU(),
                max_num_images=1
            )

        conv = self._litert_vision_engine.create_conversation()
        contents = litert_lm.Contents.of(
            litert_lm.Content.ImageFile(str(resized_path)),
            litert_lm.Content.Text(prompt)
        )
        msg = litert_lm.Message.user(contents)
        resp = conv.send_message(msg)

        if isinstance(resp, dict):
            content_list = resp.get("content", [])
            if content_list and isinstance(content_list, list):
                return content_list[0].get("text", "")
        return str(resp)

    def _analyze_ollama(self, image_path: str, prompt: str) -> str:
        with open(image_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "images": [b64_img],
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("response", "")
        except Exception as e:
            return f"[ERREUR VISION OLLAMA : {e}. Assure-toi d'avoir un modèle vision installé, ex: 'ollama run llava']"
