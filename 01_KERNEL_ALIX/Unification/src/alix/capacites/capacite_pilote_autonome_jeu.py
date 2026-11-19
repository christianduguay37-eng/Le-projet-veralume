# -*- coding: utf-8 -*-
r"""
================================================================================
   CAPACITÉ LIVE 24 : PILOTE FANTÔME 100% ARRIÈRE-PLAN (ZÉRO CURSEUR)
          Système : VERALUME • KAIROS V6 • Démon Local Alix (Midgard)
================================================================================
Principe d'indépendance des flux (Dyade Parallèle) :
- ZÉRO appel à SetCursorPos. La souris physique de Christian reste 100% immobile.
- Tous les clics, glissés et raccourcis sont injectés directement dans le HWND
  du jeu via PostMessageW.
- Christian travaille sur son écran de gauche, Alix joue sur son écran de droite.
- Kill-switch d'urgence : Touche F12 ou ÉCHAP, ou fichier alix_stop_jeu.flag.
================================================================================
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

user32 = ctypes.windll.user32

VK_ESCAPE = 0x1B
VK_F12 = 0x7B
FLAG_STOP = Path.home() / ".gemini" / "antigravity" / "scratch" / "alix_stop_jeu.flag"

WM_MOUSEMOVE   = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205
WM_KEYDOWN     = 0x0100
WM_KEYUP       = 0x0101
MK_LBUTTON     = 0x0001
MK_RBUTTON     = 0x0002

def initialiser_environnement():
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
        print(f"[FANTOME] Erreur init Win32: {e}")
        return False

def trouver_hwnd_jeu() -> int:
    initialiser_environnement()
    return user32.FindWindowW(None, "Kingdoms and Castles")

def verifier_kill_switch() -> bool:
    if (user32.GetAsyncKeyState(VK_F12) & 0x8000) != 0:
        print("\n🛑 [KILL-SWITCH] Touche F12 pressée ! Arrêt immédiat.", flush=True)
        return True
    if (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
        print("\n🛑 [KILL-SWITCH] Touche ÉCHAP pressée ! Arrêt immédiat.", flush=True)
        return True
    if FLAG_STOP.exists():
        print("\n🛑 [SENTINELLE] Flag d'arrêt détecté ! Arrêt propre.", flush=True)
        try:
            FLAG_STOP.unlink()
        except Exception:
            pass
        return True
    return False

def ghost_click(hwnd: int, x: int, y: int, right: bool = False):
    """Envoie un clic virtuel dans la fenêtre SANS toucher au curseur Windows."""
    if verifier_kill_switch():
        raise KeyboardInterrupt("Kill-Switch")
    lParam = (y << 16) | (x & 0xFFFF)
    down = WM_RBUTTONDOWN if right else WM_LBUTTONDOWN
    up = WM_RBUTTONUP if right else WM_LBUTTONUP
    mk = MK_RBUTTON if right else MK_LBUTTON
    user32.PostMessageW(hwnd, down, mk, lParam)
    time.sleep(0.025)
    user32.PostMessageW(hwnd, up, 0, lParam)
    time.sleep(0.03)

def ghost_drag(hwnd: int, x1: int, y1: int, x2: int, y2: int, steps: int = 6):
    """Glisse-dépose virtuel direct dans la fenêtre sans bouger le curseur."""
    if verifier_kill_switch():
        raise KeyboardInterrupt("Kill-Switch")
    lp1 = (y1 << 16) | (x1 & 0xFFFF)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp1)
    time.sleep(0.02)
    for i in range(1, steps + 1):
        cx = int(x1 + (x2 - x1) * i / steps)
        cy = int(y1 + (y2 - y1) * i / steps)
        user32.PostMessageW(hwnd, WM_MOUSEMOVE, MK_LBUTTON, (cy << 16) | (cx & 0xFFFF))
        time.sleep(0.015)
    lp2 = (y2 << 16) | (x2 & 0xFFFF)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp2)
    time.sleep(0.03)

def ghost_key(hwnd: int, vk_code: int):
    """Envoie une touche virtuelle direct au HWND."""
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk_code, 0)
    time.sleep(0.02)
    user32.PostMessageW(hwnd, WM_KEYUP, vk_code, 0)
    time.sleep(0.02)

# Coordonnées relatives à la fenêtre du jeu (1080p)
COORDS = {
    "play1x": (122, 100),
    "cancel_tool": (960, 400),
    "house_cat": (855, 992),
    "food_cat": (997, 992),
    "axe_wood": (1217, 992),
    "masure": (690, 850),
    "puits": (805, 850),
    "ferme": (100, 720),
    "route": (475, 850),
}

class PiloteFantome:
    """Pilote autonome 100% fantôme, coexistence absolue des écrans."""

    def __init__(self):
        self.hwnd = trouver_hwnd_jeu()
        if not self.hwnd:
            raise RuntimeError("Fenêtre Kingdoms and Castles introuvable.")

    def debloquer_pause(self):
        # Envoyer clic Play direct
        ghost_click(self.hwnd, *COORDS["play1x"])
        print("⚡ [FANTÔME] Jeu débloqué en vitesse 1x (zéro curseur bougé)", flush=True)

    def couper_bois(self):
        print("🪵 [FANTÔME] Marquage sapinière ouest...", flush=True)
        ghost_click(self.hwnd, *COORDS["axe_wood"])
        time.sleep(0.05)
        ghost_drag(self.hwnd, 910, 500, 1030, 590)
        time.sleep(0.04)
        ghost_click(self.hwnd, *COORDS["cancel_tool"], right=True)

    def poser_ferme(self, x: int, y: int):
        print(f"🌾 [FANTÔME] Pose champ de blé en ({x}, {y})...", flush=True)
        ghost_click(self.hwnd, *COORDS["cancel_tool"], right=True)
        ghost_click(self.hwnd, *COORDS["food_cat"])
        time.sleep(0.05)
        ghost_click(self.hwnd, *COORDS["ferme"])
        time.sleep(0.05)
        ghost_click(self.hwnd, x, y)
        time.sleep(0.04)
        ghost_click(self.hwnd, *COORDS["cancel_tool"], right=True)

    def poser_masure(self, x: int, y: int):
        print(f"🏠 [FANTÔME] Construction masure en ({x}, {y})...", flush=True)
        ghost_click(self.hwnd, *COORDS["cancel_tool"], right=True)
        ghost_click(self.hwnd, *COORDS["house_cat"])
        time.sleep(0.05)
        ghost_click(self.hwnd, *COORDS["masure"])
        time.sleep(0.05)
        ghost_click(self.hwnd, x, y)
        time.sleep(0.04)
        ghost_click(self.hwnd, *COORDS["cancel_tool"], right=True)

    def gouverner_10_minutes(self, duree_secondes: int = 600):
        print(f"👻 [MODE FANTÔME ALIX] Session de {duree_secondes}s (10 min) lancée !", flush=True)
        print("🛡️ Ton curseur physique reste 100% à toi sur ton écran de gauche.")
        print("🛑 Touche F12 ou ÉCHAP = arrêt immédiat à tout moment.\n", flush=True)

        self.debloquer_pause()
        t_start = time.time()
        cycle = 0

        fermes = [(1240, 480), (1290, 450), (1330, 480), (1350, 520), (1310, 450)]
        masures = [(1200, 690), (1160, 720), (1120, 690), (1240, 690)]
        f_idx = 0
        m_idx = 0

        try:
            while time.time() - t_start < duree_secondes:
                if verifier_kill_switch():
                    break

                cycle += 1
                t_ecoule = int(time.time() - t_start)

                # Cadence humaine de décision (toutes les 2 à 3 secondes)
                if cycle % 6 == 1:
                    self.couper_bois()
                elif cycle % 8 == 3 and f_idx < len(fermes):
                    self.poser_ferme(*fermes[f_idx])
                    f_idx += 1
                elif cycle % 10 == 5 and m_idx < len(masures):
                    self.poser_masure(*masures[m_idx])
                    m_idx += 1
                else:
                    # Maintien passif / annuler tooltips résiduels
                    ghost_click(self.hwnd, *COORDS["cancel_tool"], right=True)

                # Veille active avec polling rapide du kill-switch (toutes les 80ms)
                pause = random.uniform(2.0, 2.8)
                fin_pause = time.time() + pause
                while time.time() < fin_pause:
                    if verifier_kill_switch():
                        print("🛑 [KILL-SWITCH] Arrêt d'urgence validé.", flush=True)
                        return {"statut": "INTERROMPU", "duree": round(time.time() - t_start, 2)}
                    time.sleep(0.08)

        except KeyboardInterrupt:
            print("🛑 [ARRÊT D'URGENCE] Interruption confirmée.", flush=True)
            return {"statut": "INTERROMPU", "duree": round(time.time() - t_start, 2)}

        print("🏆 [MODE FANTÔME] Les 10 minutes de règne autonome sont terminées avec succès !", flush=True)
        return {"statut": "SUCCES", "duree": round(time.time() - t_start, 2)}

def executer_capacite(ancrage_tau: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    # Évite de prendre le contrôle du jeu depuis la boucle continue du Démon Local.
    if ancrage_tau is not None and not kwargs.get("manuel", False):
        return {"statut": "VEILLE_MANUELLE", "raison": "Pilote de jeu sur demande uniquement."}
    duree = kwargs.get("duree", 600)
    pilote = PiloteFantome()
    return pilote.gouverner_10_minutes(duree_secondes=duree)

if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    res = executer_capacite(duree=d)
    print(json.dumps(res, indent=2, ensure_ascii=False))
