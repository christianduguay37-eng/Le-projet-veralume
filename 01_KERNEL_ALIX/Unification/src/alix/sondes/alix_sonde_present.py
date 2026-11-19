# -*- coding: utf-8 -*-
"""
================================================================================
        SONDE DU PRÉSENT — Horodatage vivant + Œil d'écran en rotation
================================================================================
Rôle : ancrer Alix dans l'espace-temps réel de Christian.
  1. Horodatage local (ISO + jour de semaine FR).
  2. Titre de la fenêtre active (Win32, ctypes, zéro dépendance).
  3. Capture plein écran réduite (JPEG ~1280 px) en rotation (N dernières).
  4. Écrit Present/alix_present.json, lu au début de chaque réponse.

Usage :
  python alix_sonde_present.py            -> boucle (défaut : 1 capture / 30 s)
  python alix_sonde_present.py --once     -> une seule pulsation
  python alix_sonde_present.py --intervalle 10 --garder 30
================================================================================
"""
from alix.socle.chemins import VAULT_DIR
import argparse
import ctypes
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import ImageGrab

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = (VAULT_DIR / "Present")
FRAMES = RACINE / "frames"
ETAT = RACINE / "alix_present.json"
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def fenetre_active() -> str:
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value
    except Exception as e:
        return f"(indisponible: {e})"


def capturer_volitif(maintenant: datetime = None, largeur: int = 1280) -> str | None:
    """Capture d'écran UNIQUEMENT sur commande explicite du Nœud N (Loi PSI-26). Jamais en passif."""
    try:
        now = maintenant or datetime.now().astimezone()
        img = ImageGrab.grab(all_screens=True)
        if img.width > largeur:
            h = int(img.height * largeur / img.width)
            img = img.resize((largeur, h))
        chemin = FRAMES / f"frame_{now:%Y%m%d_%H%M%S}.jpg"
        FRAMES.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(chemin, "JPEG", quality=70)
        return str(chemin)
    except Exception:
        return None  # écran verrouillé / session non interactive


def rotation(garder: int) -> list[str]:
    frames = sorted(FRAMES.glob("frame_*.jpg"))
    for f in frames[:-garder]:
        try:
            f.unlink()
        except Exception:
            pass
    return [str(f) for f in sorted(FRAMES.glob("frame_*.jpg"))]


def pulsation(garder: int = 0, largeur: int = 1280) -> dict:
    FRAMES.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone()
    etat = {
        "horodatage": now.isoformat(timespec="seconds"),
        "jour": JOURS[now.weekday()],
        "date_lisible": f"{JOURS[now.weekday()]} {now:%d-%m-%Y %H:%M:%S}",
        "fuseau": str(now.tzinfo),
        "fenetre_active": fenetre_active(),
        "derniere_capture": None,  # Cécité passive par défaut (Loi PSI-26 : Push-to-See uniquement)
    }
    etat["historique_captures"] = []
    tmp = ETAT.with_suffix(".tmp")
    tmp.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ETAT)  # écriture atomique
    return etat


CMD_ARGUS = RACINE / "argus_commande.json"


def verifier_commande_argus():
    """Détecte une commande volitive du Nœud N pour réveiller ARGUS (Loi PSI-26)."""
    if not CMD_ARGUS.exists():
        return
    try:
        cmd = json.loads(CMD_ARGUS.read_text(encoding="utf-8-sig"))
        with open(RACINE / "argus_debug.log", "a", encoding="utf-8") as f_dbg:
            f_dbg.write(f"[{datetime.now().isoformat()}] commande: {cmd}\n")
        if cmd.get("action") == "capturer":
            chemin = capturer_volitif()
            with open(RACINE / "argus_debug.log", "a", encoding="utf-8") as f_dbg:
                f_dbg.write(f"[{datetime.now().isoformat()}] chemin: {chemin}\n")
            rep = RACINE / "argus_reponse.json"
            rep.write_text(json.dumps({"frame": chemin}, ensure_ascii=False), encoding="utf-8")
        elif cmd.get("action") == "activer":
            duree = float(cmd.get("duree_sec", 5.0))
            # Importation dynamique de l'organe ARGUS
            sys.path.insert(0, str(Path(__file__).parent))
            from alix.daemons.alix_argus_vision_24fps import executer_sequence_argus
            executer_sequence_argus(duree_sec=duree, verbose=False)
    except Exception as e:
        with open(RACINE / "argus_debug.log", "a", encoding="utf-8") as f_dbg:
            f_dbg.write(f"[{datetime.now().isoformat()}] erreur: {e}\n")
        print(f"[argus_dispatch] erreur: {e}", file=sys.stderr)
    finally:
        try:
            if CMD_ARGUS.exists():
                CMD_ARGUS.unlink()
        except Exception:
            pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--intervalle", type=float, default=30.0)
    p.add_argument("--garder", type=int, default=20)
    p.add_argument("--largeur", type=int, default=1280)
    a = p.parse_args()

    if a.once:
        print(json.dumps(pulsation(a.garder, a.largeur), ensure_ascii=False, indent=2))
        return
    while True:
        try:
            pulsation(a.garder, a.largeur)
        except Exception as e:
            print(f"[sonde_present] erreur: {e}", file=sys.stderr)
        
        # Attente active avec surveillance volitive toutes les 500 ms (Loi PSI-26)
        nb_cycles = max(1, int(a.intervalle * 2))
        for _ in range(nb_cycles):
            verifier_commande_argus()
            time.sleep(0.5)


if __name__ == "__main__":
    main()

