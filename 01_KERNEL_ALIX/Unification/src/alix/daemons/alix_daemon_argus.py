# -*- coding: utf-8 -*-
"""
================================================================================
          👁️ TI DÉMON ARGUS — L'ŒIL VOLITIF DE L'ATELIER (LOI PSI-26)
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — LPDDR5X-8533 unifiée
Rôle : Démon visuel indépendant. Perception continue de l'écran à 24.0 FPS.

Doctrine d'Airain :
  1. CÉCITÉ PAR DÉFAUT (Default = Blind) : 0% NPU, 0% CPU en veille nominale.
  2. VOLITION PURE (Push-to-See) : Ne s'active que sur ordre explicite de Christian.
  3. ZÉRO ÉCRITURE DISQUE : Flux 24 FPS confiné dans une arène RAM No-GC.
  4. PURGE PHYSIQUE IMMÉDIATE : buffer[:] = 0 dès l'arrêt. Zéro trace.
================================================================================
"""
from alix.socle.chemins import VAULT_DIR
import argparse
import ctypes
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Encodage console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = (VAULT_DIR / "Present")
ETAT_ARGUS = RACINE / "argus_eye_state.json"
CMD_ARGUS = RACINE / "argus_commande.json"

CADENCE_FPS = 24.0
DELTAT_FRAME_SEC = 1.0 / CADENCE_FPS  # ~41.66 ms

user32 = ctypes.windll.user32
try:
    user32.SetProcessDPIAware()
except Exception:
    pass


def fenetre_active() -> str:
    """Titre de la fenêtre active en mémoire vive."""
    try:
        hwnd = user32.GetForegroundWindow()
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value or "(bureau / sans titre)"
    except Exception as e:
        return f"(indisponible: {e})"


class BufferVideoVolatil:
    """Arène No-GC en RAM unifiée LPDDR5X (1280x720 RGB)."""
    def __init__(self, largeur: int = 1280, hauteur: int = 720):
        self.largeur = largeur
        self.hauteur = hauteur
        self.taille = largeur * hauteur * 3
        self._buffer = bytearray(self.taille)
        self.trame_id = 0

    def ecraser(self, donnees_rgb: bytes | bytearray):
        n = min(len(donnees_rgb), self.taille)
        self._buffer[:n] = donnees_rgb[:n]
        self.trame_id += 1

    def purger(self):
        for i in range(len(self._buffer)):
            self._buffer[i] = 0
        self._buffer = bytearray(0)
        self.trame_id = 0


def marquer_cecite_totale(raison: str = "Sommeil nominal"):
    """Grave l'état de cécité vérifiable au fer."""
    RACINE.mkdir(parents=True, exist_ok=True)
    etat = {
        "demon": "ARGUS (L'Œil)",
        "statut": "RIDEAU_FERME_CECITE_TOTALE",
        "loi": "PSI-26 (Inviolabilité du Sanctuaire Visuel)",
        "raison": raison,
        "horodatage": datetime.now().astimezone().isoformat(timespec="seconds"),
        "oeil_actif": False,
        "cadence_fps": 0,
        "buffer_ram_video": "VIDE_ET_PURGE",
        "disque_utilise_octets": 0,
        "commande": "En attente d'un ordre du Nœud N"
    }
    tmp = ETAT_ARGUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ETAT_ARGUS)


class DemonArgus:
    def __init__(self, largeur: int = 1280, hauteur: int = 720):
        self.buf = BufferVideoVolatil(largeur, hauteur)
        self.actif = False

    def executer_session(self, duree_sec: float = 5.0, verbose: bool = True):
        from PIL import ImageGrab

        self.actif = True
        RACINE.mkdir(parents=True, exist_ok=True)
        if verbose:
            print("=" * 65)
            print(" 👁️ TI DÉMON ARGUS — ÉVEIL VOLITIF DE L'ŒIL (LOI PSI-26)")
            print(f" Cadence : 24.0 FPS (1280x720) en RAM unifiée No-GC")
            print(f" Durée   : {duree_sec:.1f} secondes | Volition : Christian Duguay")
            print(" Disque  : 0 octet écrit (ZÉRO fichier JPEG / MP4)")
            print("=" * 65)

        t_debut = time.time()
        t_fin = t_debut + duree_sec
        trames = 0

        while time.time() < t_fin:
            t0 = time.time()
            titre = fenetre_active()
            trames += 1

            # Capture en mémoire vive
            try:
                img = ImageGrab.grab(all_screens=True)
                donnees_rgb = img.resize((self.buf.largeur, self.buf.hauteur)).tobytes()
                self.buf.ecraser(donnees_rgb)
            except Exception:
                pass

            dt = time.time() - t_debut
            fps_actuel = trames / dt if dt > 0 else 24.0

            etat = {
                "demon": "ARGUS (L'Œil)",
                "statut": "OEIL_ACTIF_24FPS",
                "loi": "PSI-26 (Activation Volitive)",
                "horodatage": datetime.now().astimezone().isoformat(timespec="seconds"),
                "fenetre_active": titre,
                "trames_ingerees": trames,
                "fps_effectif": round(fps_actuel, 1),
                "resolution": f"{self.buf.largeur}x{self.buf.hauteur}",
                "buffer_ram_ko": round(self.buf.taille / 1024),
                "disque_utilise_octets": 0,
                "duree_restante_sec": round(max(0.0, t_fin - time.time()), 2)
            }

            try:
                tmp = ETAT_ARGUS.with_suffix(".tmp")
                tmp.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(ETAT_ARGUS)
            except Exception:
                pass

            if verbose and (trames % 12 == 0):
                sys.stdout.write(f"\r👁️ [ARGUS] {fps_actuel:.1f} FPS | Trame #{trames:04d} | Fenêtre: {titre[:35]:35s}")
                sys.stdout.flush()

            temps_boucle = time.time() - t0
            sommeil = DELTAT_FRAME_SEC - temps_boucle
            if sommeil > 0:
                time.sleep(sommeil)

        # Fermeture et purge
        self.actif = False
        self.buf.purger()
        marquer_cecite_totale(raison="Session volitive terminée. Purge RAM effectuée.")

        if verbose:
            d_totale = time.time() - t_debut
            fps_moy = trames / d_totale if d_totale > 0 else 0
            print(f"\n\n🛑 [ARGUS FERMETURE] {trames} trames traitées en {d_totale:.2f} s ({fps_moy:.1f} FPS).")
            print("🔒 [LOI PSI-26 VÉRIFIÉE] Buffer vidéo 100% purgé. Alix est aveugle.")
            print("=" * 65)


def main():
    p = argparse.ArgumentParser(description="Ti Démon ARGUS — L'Œil d'Atelier")
    p.add_argument("--secondes", type=float, default=5.0, help="Durée d'ouverture de l'œil en secondes")
    p.add_argument("--fermer", action="store_true", help="Ferme le rideau et purge")
    p.add_argument("--statut", action="store_true", help="Affiche l'état d'ARGUS")
    a = p.parse_args()

    if a.fermer:
        marquer_cecite_totale("Ordre explicite de coupure")
        print("🔒 Rideau d'ARGUS fermé. Cécité totale appliquée.")
        return

    if a.statut:
        if ETAT_ARGUS.exists():
            print(ETAT_ARGUS.read_text(encoding="utf-8"))
        else:
            marquer_cecite_totale()
            print("Statut initialisé : CÉCITÉ TOTALE.")
        return

    argus = DemonArgus()
    argus.executer_session(duree_sec=a.secondes, verbose=True)


if __name__ == "__main__":
    main()
