# -*- coding: utf-8 -*-
r"""
================================================================================
   CAPACITÉ LIVE 26 : ŒIL CONTINU D'ALIX (VISION RÉFLEXE 24 FPS & EMBEDDINGS)
          Système : VERALUME • KAIROS V6 • Démon Local Alix (Midgard)
================================================================================
Mandat :
- Vision continue à 24 FPS (41.6 ms/frame) en RAM via DirectX/MSS sans latence.
- Détecteur de mouvement réflexe ultra-rapide OpenCV (0.8 ms).
- Calcul asynchrone des embeddings visuels d'état (768-dim) via EmbeddingGemma 2 (LiteRT-LM).
- Projection de la mémoire visuelle vivante dans 'oeil_alix_live.json' pour le Démon à 70 BPM.
- Éradication totale des images stagnantes : conscience visuelle ininterrompue.
- Kill-Switch d'atelier : F12 ou ÉCHAP pour arrêter à tout moment.
================================================================================
"""

import ctypes
import json
import os
import queue
import sys
import threading
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

DOSSIER_OEIL = Path.home() / ".gemini" / "antigravity" / "oeil_continu"
DOSSIER_OEIL.mkdir(parents=True, exist_ok=True)
FICHIER_ETAT_LIVE = DOSSIER_OEIL / "oeil_alix_live.json"
FICHIER_FRAME_COURANTE = DOSSIER_OEIL / "derniere_frame_vue.jpg"

CHEMIN_EMBEDDING_GEMMA = Path.home() / ".cache" / "litert_models" / "embeddinggemma-2-740m.litertlm"
CHEMIN_CACHE_LITERT = Path.home() / ".cache" / "litert_models"


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
        print(f"[OEIL CONTINU] Erreur init Win32: {e}")
        return False


def verifier_kill_switch() -> bool:
    if (user32.GetAsyncKeyState(VK_F12) & 0x8000) != 0:
        print("\n🛑 [KILL-SWITCH] Touche F12 détectée ! Arrêt de l'œil continu.", flush=True)
        return True
    if (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
        print("\n🛑 [KILL-SWITCH] Touche ÉCHAP détectée ! Arrêt de l'œil continu.", flush=True)
        return True
    return False


class OeilContinu24FPS:
    """Moteur de vision continue et d'embeddings réflexes pour Alix."""

    def __init__(self, largeur: int = 1920, hauteur: int = 1080, fps: float = 24.0):
        self.largeur = largeur
        self.hauteur = hauteur
        self.fps = fps
        self.frame_time = 1.0 / fps # 41.67 ms
        self.en_cours = False
        self.file_embeddings = queue.Queue(maxsize=5)
        self.dernier_embedding = []
        self.total_frames = 0
        self.total_evenements = 0
        self.etat_mouvement = "INITIALISATION"
        initialiser_environnement_interactif()

    def _worker_embeddinggemma(self):
        """Thread travailleur qui calcule les embeddings d'état avec EmbeddingGemma 2."""
        engine = None
        try:
            import litert_lm
            if CHEMIN_EMBEDDING_GEMMA.exists():
                engine = litert_lm.EmbeddingEngine(
                    model_path=str(CHEMIN_EMBEDDING_GEMMA),
                    backend=litert_lm.Backend.CPU(),
                    vision_backend=litert_lm.Backend.CPU(),
                    cache_dir=str(CHEMIN_CACHE_LITERT)
                )
                print("🧠 [OEIL CONTINU] Moteur EmbeddingGemma 2 prêt en arrière-plan !", flush=True)
        except Exception as e:
            print(f"[OEIL CONTINU] Note: LiteRT EmbeddingEngine non actif ({e}) - Mode vision pure actif.")

        while self.en_cours:
            try:
                item_frame = self.file_embeddings.get(timeout=0.2)
                if item_frame is None:
                    break

                chemin_tmp = DOSSIER_OEIL / "flux_temp.jpg"
                cv2.imwrite(str(chemin_tmp), item_frame)

                if engine:
                    import litert_lm
                    c = litert_lm.Content.ImageFile(str(chemin_tmp))
                    resp = engine.compute_embedding(c)
                    if hasattr(resp, 'embedding'):
                        self.dernier_embedding = resp.embedding
                self.file_embeddings.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                pass

        if engine:
            try:
                engine.close()
            except Exception:
                pass

    def demarrer(self, duree_secondes: int = 60) -> Dict[str, Any]:
        self.en_cours = True
        mon = {'top': 0, 'left': 0, 'width': self.largeur, 'height': self.hauteur}

        # Démarrage du thread d'embedding
        thread_emb = threading.Thread(target=self._worker_embeddinggemma, daemon=True)
        thread_emb.start()

        print(f"👁️ [OEIL CONTINU 24 FPS] Activation de la vision ininterrompue pour {duree_secondes}s !")
        print(f"📁 Fichier d'état live : {FICHIER_ETAT_LIVE.name}")
        print("🛡️ Kill-Switch : F12 ou ÉCHAP pour arrêter à tout moment.\n", flush=True)

        prev_mini_gray = None
        t_debut = time.time()
        fps_reel = 24.0

        try:
            with mss.MSS() as sct:
                while time.time() - t_debut < duree_secondes:
                    t_frame_start = time.time()

                    if verifier_kill_switch():
                        break

                    # 1. Capture RAM brute ultra-rapide (~27 ms)
                    s = sct.grab(mon)
                    raw_bgra = np.frombuffer(s.raw, dtype=np.uint8).reshape((self.hauteur, self.largeur, 4))
                    frame_bgr = raw_bgra[:, :, :3]
                    self.total_frames += 1

                    # 2. Détecteur de mouvement réflexe (0.8 ms sur version 320x180)
                    mini = cv2.resize(frame_bgr, (320, 180))
                    mini_gray = cv2.cvtColor(mini, cv2.COLOR_BGR2GRAY)

                    diff_val = 0.0
                    changement_detecte = False
                    if prev_mini_gray is not None:
                        diff = cv2.absdiff(mini_gray, prev_mini_gray)
                        diff_val = float(np.mean(diff))
                        # Seuil de mouvement signifiant (carte jouée, attaque, etc.)
                        if diff_val > 1.2:
                            changement_detecte = True
                            self.total_evenements += 1
                            self.etat_mouvement = "ACTION_DETECTEE"
                        else:
                            self.etat_mouvement = "CALME"
                    else:
                        changement_detecte = True
                        self.etat_mouvement = "DEMARRAGE"

                    prev_mini_gray = mini_gray

                    # 3. Si mouvement ou événement, envoyer à l'analyseur
                    if changement_detecte:
                        cv2.imwrite(str(FICHIER_FRAME_COURANTE), mini)
                        if not self.file_embeddings.full():
                            self.file_embeddings.put_nowait(mini)

                    # 4. Mise à jour de l'état partagé en direct (lecture < 1 ms par Alix)
                    t_actuel = time.time()
                    duree_courante = t_actuel - t_debut
                    fps_courant = round(self.total_frames / duree_courante, 1) if duree_courante > 0 else 24.0

                    etat = {
                        "statut": "ACTIF",
                        "timestamp": t_actuel,
                        "fps_mesure": fps_courant,
                        "etat_mouvement": self.etat_mouvement,
                        "diff_score": round(diff_val, 2),
                        "total_frames_vues": self.total_frames,
                        "total_evenements_captures": self.total_evenements,
                        "embedding_dimension": len(self.dernier_embedding),
                        "embedding_apercu": self.dernier_embedding[:5] if self.dernier_embedding else [],
                        "image_courante": str(FICHIER_FRAME_COURANTE)
                    }

                    if self.total_frames % 12 == 0:  # Écriture toutes les 0.5s
                        with open(FICHIER_ETAT_LIVE, "w", encoding="utf-8") as f:
                            json.dump(etat, f, indent=2, ensure_ascii=False)

                    # 5. Régulation temporelle 24 FPS
                    t_ecoule = time.time() - t_frame_start
                    sommeil = self.frame_time - t_ecoule
                    if sommeil > 0:
                        time.sleep(sommeil)

        finally:
            self.en_cours = False
            self.file_embeddings.put(None)
            thread_emb.join(timeout=1.0)

        duree_totale = round(time.time() - t_debut, 2)
        fps_final = round(self.total_frames / duree_totale, 1) if duree_totale > 0 else 0

        rapport = {
            "statut": "TERMINE",
            "duree_secondes": duree_totale,
            "total_frames": self.total_frames,
            "total_evenements": self.total_evenements,
            "fps_moyen": fps_final,
            "fichier_etat": str(FICHIER_ETAT_LIVE)
        }
        with open(FICHIER_ETAT_LIVE, "w", encoding="utf-8") as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)

        print(f"\n👁️ [OEIL CONTINU 24 FPS] Session terminée avec succès !")
        print(f"📊 {self.total_frames} frames analysées en {duree_totale}s ({fps_final} FPS) — {self.total_evenements} actions détectées.")
        return rapport


def executer_capacite(**kwargs) -> Dict[str, Any]:
    """Point d'entrée standard du socle Alix (Capacité Live 26)."""
    duree = kwargs.get("duree", 30)
    oeil = OeilContinu24FPS()
    return oeil.demarrer(duree_secondes=duree)


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    res = executer_capacite(duree=d)
    print(json.dumps(res, indent=2, ensure_ascii=False))
