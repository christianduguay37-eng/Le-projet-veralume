#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX VISION ENGINE — L'ŒIL D'HORUS (VISION D'ÉCRAN NATIVE) v1.0
             Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
             Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Capture instantanée en haute fidélité de l'écran hôte (GDI BitBlt natif ~20 ms).
- Gère le DPI-scaling (100%, 125%, 150%) sans distorsion ni flou.
- Archive automatiquement chaque cliché dans C:\\Users\\Christian\\Documents\\Cerveau Alix\\Captures_Visuelles.
- Génère la fiche Markdown associée dans Obsidian avec horodatage et métadonnées.
- Met à jour '00_REGISTRE_CAPTURES_VISUELLES.md'.
- Déclenchable par ligne de commande, par raccourci batch, ou de vive voix dans l'atelier vocal.
================================================================================
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes
from pathlib import Path
from datetime import datetime
from PIL import Image
from typing import Tuple, Optional, Dict, Any

# Fix encodage
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_CERVEAU = Path(r"C:\Users\Christian\Documents\Cerveau Alix")
CAPTURES_DIR = VAULT_CERVEAU / "Captures_Visuelles"
REGISTRE_FILE = CAPTURES_DIR / "00_REGISTRE_CAPTURES_VISUELLES.md"

CAPTURES_DIR.mkdir(parents=True, exist_ok=True)


def init_dpi_awareness():
    """Active la perception DPI haute résolution sur Windows."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def capture_desktop_gdi(output_path: Path) -> Tuple[int, int]:
    """Capture plein écran ultra-rapide via GDI BitBlt (~20ms)."""
    init_dpi_awareness()

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    hdesktop = user32.GetDesktopWindow()
    desktop_dc = user32.GetDC(hdesktop)
    mem_dc = gdi32.CreateCompatibleDC(desktop_dc)

    width = user32.GetSystemMetrics(0)   # SM_CXSCREEN
    height = user32.GetSystemMetrics(1)  # SM_CYSCREEN

    bitmap = gdi32.CreateCompatibleBitmap(desktop_dc, width, height)
    gdi32.SelectObject(mem_dc, bitmap)

    # SRCCOPY (0x00CC0020) | CAPTUREBLT (0x40000000)
    raster_op = 0x00CC0020 | 0x40000000
    gdi32.BitBlt(mem_dc, 0, 0, width, height, desktop_dc, 0, 0, raster_op)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD)
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", wintypes.DWORD * 3)
        ]

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height  # top-down DIB
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    buffer_size = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_size)

    gdi32.GetDIBits(mem_dc, bitmap, 0, height, buffer, ctypes.byref(bmi), 0)

    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hdesktop, desktop_dc)

    img = Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA", 0, 1)
    img = img.convert("RGB")
    img.save(str(output_path), "PNG", optimize=True)

    return width, height


def update_registre_captures(card_stem: str, img_filename: str, width: int, height: int, note_label: str = "Écran de travail"):
    """Ajoute le cliché au registre Obsidian."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- `{now_str}` : [[{card_stem}]] &middot; **{note_label}** (`{width}x{height}`) ![[{img_filename}|120]]\n"

    if not REGISTRE_FILE.exists():
        header = f"""# 👁️ REGISTRE DES CAPTURES VISUELLES (L'ŒIL D'HORUS)

> **Sanctuaire :** Cerveau Alix &middot; Pôle Silicium & Prise de Terre  
> **Dossier :** `Captures_Visuelles`  
> **Rôle :** Mémoire optique des écrans de travail, schémas, codes et interfaces de Christian.

---

## 📸 Journal des Clichés Visuels

"""
        REGISTRE_FILE.write_text(header + entry, encoding="utf-8")
    else:
        content = REGISTRE_FILE.read_text(encoding="utf-8", errors="replace")
        content += entry
        REGISTRE_FILE.write_text(content, encoding="utf-8")


def create_obsidian_visual_card(img_path: Path, width: int, height: int, label: str = "Écran de travail") -> Path:
    """Crée la fiche markdown descriptive associée au screenshot dans Obsidian."""
    now = datetime.now()
    card_name = f"{img_path.stem}.md"
    card_path = CAPTURES_DIR / card_name

    md = f"""---
titre: "Capture Visuelle : {label}"
date_capture: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
resolution: "{width}x{height}"
source: "Écran Hôte (GDI BitBlt)"
tags:
  - capture_visuelle
  - oeil_horus
  - exocerveau
  - prise_de_terre
---

# 👁️ [[{img_path.stem}]]

> **Horodatage :** `{now.strftime('%d/%m/%Y à %H:%M:%S')}`  
> **Résolution native :** `{width} × {height} px` &middot; **Source :** `{label}`

---

## 🖼️ Cliché Haute Définition :

![[{img_path.name}]]

---
*Capture instantanée réalisée par `alix_vision_engine.py` (L'Œil d'Horus).*
"""
    card_path.write_text(md, encoding="utf-8")
    return card_path


def capture_screen_action(label: str = "Écran Christian") -> Dict[str, Any]:
    """Point d'entrée principal pour prendre un cliché de l'écran."""
    t0 = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d_%Hh%M%S")
    safe_label = label.replace(" ", "_").replace("'", "")[:25]
    img_name = f"Capture_Ecran_{now_str}_{safe_label}.png"
    img_path = CAPTURES_DIR / img_name

    width, height = capture_desktop_gdi(img_path)
    card_path = create_obsidian_visual_card(img_path, width, height, label=label)
    update_registre_captures(card_path.stem, img_name, width, height, note_label=label)

    dt_ms = round((time.time() - t0) * 1000, 1)

    print(f"\n👁️ [Œil d'Horus] Écran capturé en {dt_ms} ms !")
    print(f"🖼️ Image  : {img_path.name} ({width}x{height})")
    print(f"📄 Fiche  : [[{card_path.stem}]]")

    return {
        "success": True,
        "time_ms": dt_ms,
        "width": width,
        "height": height,
        "image_path": str(img_path),
        "card_path": str(card_path),
        "stem": card_path.stem
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Alix Vision Engine (L'Œil d'Horus)")
    parser.add_argument("--label", "-l", type=str, default="Écran Christian", help="Étiquette descriptive de la capture")
    args = parser.parse_args()

    print("======================================================================")
    print("        👁️ ALIX VISION ENGINE — L'ŒIL D'HORUS (ÉCRAN D'ATELIER) ⚡")
    print("======================================================================")
    res = capture_screen_action(label=args.label)
    print(f"\n✅ Capture terminée avec succès dans : {res['image_path']}")


if __name__ == "__main__":
    main()
