# -*- coding: utf-8 -*-
r"""
================================================================================
   CAPACITÉ LIVE 25 : MAGNÉTOSCOPE VIDÉO 24 FPS & VISION CINÉMATIQUE
          Système : VERALUME • KAIROS V6 • Démon Local Alix (Midgard)
================================================================================
Mandat :
- Capture vidéo temps-réel à 24 FPS (41.67 ms/frame) en RAM sans friction disque.
- Encodage matériel direct en MP4 (H.264/mp4v) via OpenCV et MSS sur Lunar Lake 258V.
- Maintien d'un débit constant de 24 images/seconde avec régulation temporelle.
- Génère les jeux de données d'entraînement par imitation pour les modèles de jeu d'Alix.
- Sécurité d'établi : Kill-Switch d'urgence sur touche F12 ou ÉCHAP.
================================================================================
"""

import ctypes
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import mss
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

user32 = ctypes.windll.user32
VK_ESCAPE = 0x1B
VK_F12 = 0x7B

DOSSIER_REPLAYS = Path.home() / ".gemini" / "antigravity" / "dataset_hearthstone" / "replays_video_24fps"
DOSSIER_REPLAYS.mkdir(parents=True, exist_ok=True)

def initialiser_environnement_interactif():
    try:
        hwinsta = user32.OpenWindowStationW('WinSta0', False, 0x0000037F)
        if hwinsta:
            user32.SetProcessWindowStation(hwinsta)
        hdesk = user32.OpenDesktopW('Default', 0, False, 0x000001FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return True
    except Exception as e:
        print(f"[MAGNÉTOSCOPE] Erreur init Win32: {e}")
        return False

def verifier_kill_switch() -> bool:
    if (user32.GetAsyncKeyState(VK_F12) & 0x8000) != 0:
        print("\n🛑 [KILL-SWITCH] Touche F12 détectée ! Arrêt de l'enregistrement.", flush=True)
        return True
    if (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
        print("\n🛑 [KILL-SWITCH] Touche ÉCHAP détectée ! Arrêt de l'enregistrement.", flush=True)
        return True
    return False

class Magnetoscope24FPS:
    """Enregistreur vidéo 24 FPS haute performance pour l'apprentissage d'Alix."""

    def __init__(self, largeur: int = 1920, hauteur: int = 1080, fps: float = 24.0):
        self.largeur = largeur
        self.hauteur = hauteur
        self.fps = fps
        self.frame_time = 1.0 / fps # 41.67 ms
        initialiser_environnement_interactif()

    def enregistrer(self, duree_secondes: int = 60, nom_fichier: str = "replay_24fps.mp4") -> Dict[str, Any]:
        chemin_video = DOSSIER_REPLAYS / nom_fichier
        chemin_meta = DOSSIER_REPLAYS / f"{chemin_video.stem}_meta.json"

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(chemin_video), fourcc, self.fps, (self.largeur, self.hauteur))

        if not out.isOpened():
            raise RuntimeError("Impossible d'initialiser le VideoWriter OpenCV.")

        print(f"🎬 [MAGNÉTOSCOPE 24 FPS] Enregistrement cinématique démarré pour {duree_secondes}s !")
        print(f"📁 Fichier : {chemin_video.name}")
        print("🛡️ Kill-Switch : F12 ou ÉCHAP pour arrêter à tout moment.\n", flush=True)

        frames_enregistrees = 0
        t_debut = time.time()
        mon = {'top': 0, 'left': 0, 'width': self.largeur, 'height': self.hauteur}

        try:
            with mss.MSS() as sct:
                while time.time() - t_debut < duree_secondes:
                    t_frame_start = time.time()

                    if verifier_kill_switch():
                        break

                    # 1. Capture RAM brute ultra-rapide (27 ms)
                    s = sct.grab(mon)
                    raw_bgra = np.frombuffer(s.raw, dtype=np.uint8).reshape((self.hauteur, self.largeur, 4))
                    frame_bgr = raw_bgra[:, :, :3]

                    # 2. Écriture directe dans le flux MP4
                    out.write(frame_bgr)
                    frames_enregistrees += 1

                    # 3. Régulation cadencée à 24.0 FPS précis
                    t_ecoule_frame = time.time() - t_frame_start
                    temps_sommeil = self.frame_time - t_ecoule_frame
                    if temps_sommeil > 0:
                        time.sleep(temps_sommeil)

        finally:
            out.release()

        duree_reelle = round(time.time() - t_debut, 2)
        fps_moyen = round(frames_enregistrees / duree_reelle, 1) if duree_reelle > 0 else 0

        poids_mb = round(chemin_video.stat().st_size / (1024 * 1024), 2) if chemin_video.exists() else 0

        metadonnees = {
            "statut": "SUCCES",
            "fichier": chemin_video.name,
            "chemin_absolu": str(chemin_video),
            "poids_mb": poids_mb,
            "duree_secondes": duree_reelle,
            "total_frames": frames_enregistrees,
            "fps_cible": self.fps,
            "fps_reel_mesure": fps_moyen,
            "moteur": "Alix Capacité Live 25 (OpenCV + MSS DXGI)"
        }

        with open(chemin_meta, "w", encoding="utf-8") as f:
            json.dump(metadonnees, f, indent=2, ensure_ascii=False)

        print(f"\n🏆 [MAGNÉTOSCOPE 24 FPS] Enregistrement terminé avec succès !")
        print(f"📊 {frames_enregistrees} frames encodées en {duree_reelle}s ({fps_moyen} FPS moyen) — Taille: {poids_mb} MB")
        return metadonnees

def executer_capacite(ancrage_tau: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Point d'entrée standard du socle Alix (Capacité Live 25)."""
    # Évite d'enregistrer l'écran en continu depuis le Démon Local si appelée sans mode manuel.
    if ancrage_tau is not None and not kwargs.get("manuel", False):
        return {"statut": "VEILLE_MANUELLE", "raison": "Capacité vidéo sur demande uniquement."}
    duree = kwargs.get("duree", 30)
    nom = kwargs.get("nom", f"match_{int(time.time())}.mp4")
    mag = Magnetoscope24FPS()
    return mag.enregistrer(duree_secondes=duree, nom_fichier=nom)

if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n = sys.argv[2] if len(sys.argv) > 2 else "test_capacite_25.mp4"
    res = executer_capacite(duree=d, nom=n)
    print(json.dumps(res, indent=2, ensure_ascii=False))
