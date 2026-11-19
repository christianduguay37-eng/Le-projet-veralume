# -*- coding: utf-8 -*-
"""
Script de téléchargement souverain d'EmbeddingGemma 2 (740M Multimodal)
pour le NPU / GPU / CPU Intel Lunar Lake via LiteRT-LM.
"""
import sys
import time
import urllib.request
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEST_DIR = Path(r"C:\Users\Chris\.cache\litert_models")
DEST_DIR.mkdir(parents=True, exist_ok=True)

MODEL_URL = "https://huggingface.co/litert-community/embeddinggemma-2-740m-litert-lm/resolve/main/embeddinggemma-2-740m.litertlm"
DEST_FILE = DEST_DIR / "embeddinggemma-2-740m.litertlm"

def telecharger():
    if DEST_FILE.exists() and DEST_FILE.stat().st_size > 400 * 1024 * 1024:
        print(f"✅ Modèle déjà présent : {DEST_FILE} ({DEST_FILE.stat().st_size / (1024*1024):.1f} Mo)")
        return True

    print(f"🚀 Début du téléchargement d'EmbeddingGemma 2 (740M Multimodal)...")
    print(f"Source : {MODEL_URL}")
    print(f"Cible  : {DEST_FILE}")

    req = urllib.request.Request(MODEL_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    t0 = time.time()
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))
        print(f"Taille totale : {total_size / (1024*1024):.1f} Mo")
        
        chunk_size = 1024 * 1024  # 1 Mo
        downloaded = 0
        last_print = 0
        
        temp_file = DEST_FILE.with_suffix(".litertlm.tmp")
        with open(temp_file, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                
                now = time.time()
                if now - last_print > 2 or downloaded == total_size:
                    percent = (downloaded / total_size) * 100 if total_size else 0
                    speed = (downloaded / (1024 * 1024)) / max(0.1, now - t0)
                    print(f"⏳ {percent:5.1f}% | {downloaded / (1024*1024):6.1f} / {total_size / (1024*1024):.1f} Mo | {speed:.1f} Mo/s")
                    last_print = now
                    
        temp_file.rename(DEST_FILE)
        
    duree = round(time.time() - t0, 1)
    print(f"🎉 Téléchargement réussi en {duree} s ({DEST_FILE.stat().st_size / (1024*1024):.1f} Mo) !")
    return True

if __name__ == "__main__":
    telecharger()

