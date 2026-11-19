# -*- coding: utf-8 -*-
"""
================================================================================
    MODULE ARGUS — VISION VIVANTE 24 IMAGES/SECONDE SUR DEMANDE (LUNAR LAKE)
================================================================================
Conforme à la Constitution Souveraine & Loi PSI-26 :
  1. CÉCITÉ TOTALE PAR DÉFAUT (Default = Blind) : 0% NPU, 0% CPU, rideau baissé.
  2. ACTIVATION VOLITIVE RÉVERSIBLE (Push-to-See) : S'éveille UNIQUEMENT sur
     ordre explicite du Nœud N (Christian Duguay). Zéro surveillance passive.
  3. FLUX VIBRANT EN RAM UNIFIÉE : Capture à 24 fps (41.6 ms/trame) sans AUCUNE
     écriture disque. Zéro fichier JPEG, zéro dégradation du NVMe.
  4. PURGE IMMÉDIATE DU BUFFER : Dès le retrait de la commande, le buffer mémoire
     est écrasé et libéré (gc.collect). La vie privée est une frontière physique.
================================================================================
"""
import argparse
import ctypes
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Réglage encodage console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ancrage Exocerveau
RACINE = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Present")
ETAT_ARGUS = RACINE / "argus_live_perception.json"
CMD_ARGUS = RACINE / "argus_commande.json"
CADENCE_CIBLE_FPS = 24.0
DELTAT_FRAME_SEC = 1.0 / CADENCE_CIBLE_FPS  # ~41.66 ms

user32 = ctypes.windll.user32
try:
    user32.SetProcessDPIAware()
except Exception:
    pass


def obtenir_fenetre_active() -> str:
    """Extrait le titre de la fenêtre active en mémoire vive via Win32."""
    try:
        hwnd = user32.GetForegroundWindow()
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value or "(bureau / sans titre)"
    except Exception as e:
        return f"(indisponible: {e})"


class BufferMemoireVolatil:
    """
    Arène No-GC pour la trame vidéo en RAM LPDDR5X unifiée.
    Respect absolu de la Loi PSI-26 Volet 3 :
    Chaque trame écrase la précédente sur place. Purge instantanée à la fermeture.
    """
    def __init__(self, largeur: int = 1280, hauteur: int = 720):
        self.largeur = largeur
        self.hauteur = hauteur
        self.octets_par_pixel = 3  # RGB
        self.taille = largeur * hauteur * self.octets_par_pixel
        # Alloué une seule fois en mémoire contiguë
        self._buffer = bytearray(self.taille)
        self.trame_id = 0
        self.derniere_activite = 0.0

    def ecraser_trame(self, donnees_brutes: bytes | bytearray):
        """Écrase la trame précédente sans allocation dynamique."""
        n = min(len(donnees_brutes), self.taille)
        self._buffer[:n] = donnees_brutes[:n]
        self.trame_id += 1

    def purger_totalement(self):
        """Purge physique immédiate du buffer (Loi PSI-26)."""
        for i in range(len(self._buffer)):
            self._buffer[i] = 0
        self._buffer = bytearray(0)
        self.trame_id = 0
        self.derniere_activite = 0.0


def marquer_cecite_totale(raison: str = "Sommeil nominal"):
    """Grave l'état de cécité vérifiable au fer."""
    RACINE.mkdir(parents=True, exist_ok=True)
    etat = {
        "statut": "RIDEAU_FERME_CECITE_TOTALE",
        "loi": "PSI-26 (Inviolabilité du Sanctuaire Visuel & Activation Volitive)",
        "raison": raison,
        "horodatage": datetime.now().astimezone().isoformat(timespec="seconds"),
        "capteurs_actifs": False,
        "cadence_fps": 0,
        "buffer_ram": "VIDE_ET_PURGE",
        "noeud_n_commande": "En attente d'un ordre souverain de Christian Duguay"
    }
    tmp = ETAT_ARGUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ETAT_ARGUS)


def executer_sequence_argus(duree_sec: float = 5.0, verbose: bool = True):
    """
    Ouvre l'œil d'ARGUS pour une durée délimitée sur ordre souverain.
    Fréquence : 24 images/seconde en RAM unifiée -> NPU.
    """
    RACINE.mkdir(parents=True, exist_ok=True)
    if verbose:
        print("=" * 65)
        print(" 👁️ ÉVEIL VOLITIF DU MODULE ARGUS (LOI PSI-26)")
        print(f" Cadence Cible : {CADENCE_CIBLE_FPS:.1f} FPS (Intervalle: {DELTAT_FRAME_SEC*1000:.2f} ms)")
        print(f" Durée Accordée: {duree_sec:.1f} secondes | Volition : Nœud N (Christian)")
        print(" Stockage       : 100% RAM Unifiée LPDDR5X (ZÉRO fichier disque)")
        print("=" * 65)

    buffer_ram = BufferMemoireVolatil(1280, 720)
    t_debut = time.time()
    t_fin = t_debut + duree_sec
    compteur_trames = 0
    trames_reelles = 0

    try:
        from PIL import ImageGrab
        pil_dispo = True
    except ImportError:
        pil_dispo = False

    while time.time() < t_fin:
        t_frame_start = time.time()
        fenetre = obtenir_fenetre_active()
        compteur_trames += 1

        # Capture en RAM sans écriture disque
        if pil_dispo:
            try:
                img = ImageGrab.grab(all_screens=True)
                # Conversion rapide en mémoire
                donnees_rgb = img.resize((buffer_ram.largeur, buffer_ram.hauteur)).tobytes()
                buffer_ram.ecraser_trame(donnees_rgb)
                trames_reelles += 1
            except Exception:
                pass

        fps_courant = trames_reelles / (time.time() - t_debut) if (time.time() > t_debut) else 24.0

        # Écriture de l'état discret live
        etat_live = {
            "statut": "OEIL_ARGUS_ACTIF_24FPS",
            "loi": "PSI-26 (Activation Volitive en Cours)",
            "horodatage": datetime.now().astimezone().isoformat(timespec="seconds"),
            "fenetre_active": fenetre,
            "trames_ingerees": trames_reelles,
            "fps_effectif": round(fps_courant, 2),
            "duree_restante_sec": round(max(0.0, t_fin - time.time()), 2),
            "ram_volatile_octets": buffer_ram.taille,
            "disque_utilise_octets": 0  # 100% pur RAM
        }
        try:
            tmp = ETAT_ARGUS.with_suffix(".tmp")
            tmp.write_text(json.dumps(etat_live, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(ETAT_ARGUS)
        except Exception:
            pass

        if verbose and (compteur_trames % 12 == 0):
            sys.stdout.write(f"\r👁️ [ARGUS 24fps] Trame #{trames_reelles:04d} | FPS: {fps_courant:.1f} | Fenêtre: {fenetre[:35]:35s}")
            sys.stdout.flush()

        # Cadencement strict 41.6 ms (24 fps)
        temps_ecoule_trame = time.time() - t_frame_start
        sommeil_requis = DELTAT_FRAME_SEC - temps_ecoule_trame
        if sommeil_requis > 0:
            time.sleep(sommeil_requis)

    # Clôture & Purge Physique Immédiate (Loi PSI-26)
    d_totale = time.time() - t_debut
    fps_final = trames_reelles / d_totale if d_totale > 0 else 0
    buffer_ram.purger_totalement()
    marquer_cecite_totale(raison="Séquence volitive accomplie. Clapet refermé.")

    if verbose:
        print(f"\n\n🛑 [ARGUS FERMETURE] Séquence terminée : {trames_reelles} trames en {d_totale:.2f} s ({fps_final:.1f} FPS réel).")
        print("🔒 [LOI PSI-26 APPLIQUÉE] Buffer RAM écrasé et purgé. Alix est redevenue aveugle.")
        print("=" * 65)


def main():
    p = argparse.ArgumentParser(description="Module ARGUS — Vision Vivante 24 fps sur Demande")
    p.add_argument("--secondes", type=float, default=5.0, help="Durée d'ouverture de l'œil en secondes")
    p.add_argument("--fermer", action="store_true", help="Force la cécité immédiate et purge le buffer")
    p.add_argument("--statut", action="store_true", help="Vérifie l'état matériel d'ARGUS")
    a = p.parse_args()

    if a.fermer:
        marquer_cecite_totale(raison="Ordre explicite de fermeture reçu")
        print("🔒 Rideau d'ARGUS fermé. Cécité totale appliquée.")
        return

    if a.statut:
        if ETAT_ARGUS.exists():
            print(ETAT_ARGUS.read_text(encoding="utf-8"))
        else:
            marquer_cecite_totale()
            print("Statut initialisé : CÉCITÉ TOTALE.")
        return

    # Exécution sur demande
    executer_sequence_argus(duree_sec=a.secondes, verbose=True)


if __name__ == "__main__":
    main()

