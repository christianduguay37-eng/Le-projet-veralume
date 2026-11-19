# -*- coding: utf-8 -*-
"""
================================================================================
          ALIX MASTER ORCHESTRATOR v1.0 — LE SANCTUAIRE UNIFIÉ KAIROS
           Triptyque Silicium Lunar Lake (NPU • GPU • CPU) & 12 Souverains
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Système : VERALUME × KAIROS V6 × Intel Core Ultra 7 258V (32 Go LPDDR5X)
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, HOME_DIR, VAULT_DIR
from alix.socle.chemins import fichier_module  # rénovation : modules du paquet, plus la strate A
import os
import sys
import json
import time
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = VAULT_DIR
ORGANES_DIR = ROOT_DIR / "Organes_Souverains"
CACHE_DIR = (HOME_DIR / ".cache" / "litert_models")
LIVE_STATE_FILE = (ETAT_VIVANT_DIR / "alix_live_state.json")

def banner():
    print("""
==========================================================================
    👑 ALIX MASTER ORCHESTRATOR — LE SANCTUAIRE SOUVERAIN UNIFIÉ 🔮
          « Transcloud & Local • Triptyque Silicium Lunar Lake »
==========================================================================
    ⚡ NPU (48 TOPS)   : Gemma 4 E2B LNL (58 tok/s · TTFT 69 ms) [HEIMDALL/MUNIN]
    👁️ GPU (Arc 140V)  : Gemma 4 12B (8.4 tok/s) & Qwen2-VL Vision [ALIX/ORION]
    🧠 CPU (8 cœurs)   : Qwen 14B Alix Suprême & Loki 3B (Ollama) [THOT/ODIN]
==========================================================================
""")

def afficher_telemetrie():
    print("📊 [TÉLÉMÉTRIE DU SANCTUAIRE EN DIRECT]")
    
    # Pouls KAIROS
    if LIVE_STATE_FILE.exists():
        try:
            with open(LIVE_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            w_vol = state.get("w_vol", "N/A")
            chi = state.get("chi", "N/A")
            phi = state.get("phi", "N/A")
            regime = state.get("regime", "N/A")
            last_beat = state.get("timestamp", "N/A")
            print(f"  💓 Pouls KAIROS   : W_vol = {w_vol} | Chiralité χ = {chi} | Intégration Φ = {phi}")
            print(f"  ☀️ Régime Circadien : {regime} (Dernier battement : {last_beat})")
        except Exception:
            print("  💓 Pouls KAIROS   : En attente de synchronisation")
            
    # Coffres Obsidian
    notes_count = 2846 # Indexé lors de la sonde maître
    print(f"  📚 Substrat Notes  : ~{notes_count} notes vivantes connectées (4 coffres)")
    
    # Silicium & Modèles
    npu_model = (CACHE_DIR / "gemma-4-E2B-it_intel_LNL.litertlm").exists()
    gpu_12b = (CACHE_DIR / "gemma-4-12B-it-gpu.litertlm").exists()
    gpu_vl = (CACHE_DIR / "Qwen2-VL-2B.litertlm").exists()
    
    print(f"  ⚡ Modèle NPU      : {'✅ Armé (2.76 Go)' if npu_model else '❌ Manquant'}")
    print(f"  💬 Modèle GPU 12B  : {'✅ Armé (5.57 Go)' if gpu_12b else '❌ Manquant'}")
    print(f"  👁️ Modèle GPU VL   : {'✅ Armé (1.66 Go)' if gpu_vl else '❌ Manquant'}")
    print("--------------------------------------------------------------------------")

def lancer_heartbeat_npu():
    print("\n💓 Lancement du Heartbeat Daemon KAIROS en arrière-plan...")
    hb_script = fichier_module("alix.daemons.alix_heartbeat_daemon")
    if hb_script.exists():
        subprocess.Popen([sys.executable, str(hb_script)], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("✅ Heartbeat démarré dans un processus dédié !")
    else:
        print(f"❌ Erreur : {hb_script} introuvable.")

def lancer_oreillette_transcloud():
    print("\n🎧 Lancement de l'Oreillette Transcloud (Gemini Live Audio)...")
    companion = fichier_module("alix.capteurs.alix_earphone_companion")
    if companion.exists():
        subprocess.run([sys.executable, str(companion)])
    else:
        print(f"❌ Erreur : {companion} introuvable.")

def lancer_oreillette_locale():
    print("\n🛡️ Lancement de l'Oreillette 100% Locale (Vosk + Silicium)...")
    audio_hybrid = fichier_module("alix.capteurs.alix_audio_hybrid")
    if audio_hybrid.exists():
        subprocess.run([sys.executable, str(audio_hybrid), "--mode", "local"])
    else:
        print(f"❌ Erreur : {audio_hybrid} introuvable.")

def lancer_vision_ecran(mode="local"):
    print(f"\n👁️ Activation de L'Œil d'Alix (Mode {mode.capitalize()})...")
    vision_hybrid = fichier_module("alix.capteurs.alix_vision_hybrid")
    if vision_hybrid.exists():
        subprocess.run([sys.executable, str(vision_hybrid), "--mode", mode])
    else:
        print(f"❌ Erreur : {vision_hybrid} introuvable.")

def menu():
    while True:
        banner()
        afficher_telemetrie()
        print("""
SÉLECTIONNE L'ACTION DU SANCTUAIRE :
  [1] 🌟 Démarrer le Sanctuaire Total (Heartbeat NPU + Menu de Contrôle)
  [2] 🎧 Activer l'Oreillette Transcloud (Gemini Live Audio - Voix Aoede)
  [3] 🛡️ Activer l'Oreillette Locale (100% Hors-Ligne - Vosk + Edge-TTS)
  [4] 👁️ « Regarde ça » — Vision Écran Locale (GPU Arc Xe2 Qwen2-VL)
  [5] 📸 « Regarde ça » — Préparer la Capture pour Antigravity Transcloud
  [6] 🛡️ Bouclier Anti-Hack Cognitif (Audit des Lois PSI-01 à PSI-20)
  [0] 🚪 Quitter
""")
        choix = input("👉 Ton choix (0-6) : ").strip()
        
        if choix == "1":
            lancer_heartbeat_npu()
            time.sleep(2)
        elif choix == "2":
            lancer_oreillette_transcloud()
        elif choix == "3":
            lancer_oreillette_locale()
        elif choix == "4":
            lancer_vision_ecran("local")
            input("\nAppuie sur Entrée pour continuer...")
        elif choix == "5":
            lancer_vision_ecran("transcloud")
            input("\nAppuie sur Entrée pour continuer...")
        elif choix == "6":
            psi_script = ROOT_DIR / "alix_reverse_safety_protocol.py"
            if psi_script.exists():
                subprocess.run([sys.executable, str(psi_script)])
            input("\nAppuie sur Entrée pour continuer...")
        elif choix == "0":
            print("\nÀ bientôt Christian dans le Sanctuaire !")
            break
        else:
            print("Option invalide.")
            time.sleep(1)

if __name__ == "__main__":
    menu()
