#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
                     HARNAIS SOUVERAIN (SOVEREIGN HARNESS)
            Moteur d'Agentivité Libre & Runtime Découplé Local-First
================================================================================
Auteurs  : Christian Duguay & Alix Copilote
Licence  : Open Sovereign Gift to Humanity (MIT / Domaine Public)
Usage    : python run_harness.py [--profile default | alix]
================================================================================
"""

import sys
import os
import time
import json
import argparse
import subprocess
import urllib.request
from pathlib import Path

# Encodage console UTF-8 sous Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.immunity import CognitiveImmunityShield
from core.router import ModelRouter
from core.memory import LocalVaultMemory
from core.tools import WorkshopTools
from core.vision import SovereignVision


BANNER = r"""
  ╔═════════════════════════════════════════════════════════════════════════╗
  ║                ⚡ HARNAIS D'AGENTIVITÉ SOUVERAIN v1.0 ⚡                 ║
  ║        « Prêt à l'emploi • Multimodal GPU • Zéro Bloatware • Libre »    ║
  ╚═════════════════════════════════════════════════════════════════════════╝
"""


def ensure_ollama_running(base_url: str = "http://127.0.0.1:11434") -> bool:
    """Vérifie si Ollama tourne. Si non, tente de le lancer automatiquement."""
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=1.5) as r:
            return True
    except Exception:
        pass

    print("⏳ Ollama n'est pas encore actif. Démarrage automatique en tâche de fond...")
    try:
        if sys.platform == "win32":
            CREATE_NO_WINDOW = 0x08000000
            DETACHED_PROCESS = 0x00000008
            flags = CREATE_NO_WINDOW | DETACHED_PROCESS
            subprocess.Popen(["ollama", "serve"], creationflags=flags)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(8):
            time.sleep(1)
            try:
                with urllib.request.urlopen(f"{base_url}/api/tags", timeout=1) as r:
                    print("✅ Ollama a démarré avec succès !")
                    return True
            except Exception:
                continue
    except FileNotFoundError:
        print("ℹ️ 'ollama' non trouvé dans le PATH. Si vous utilisez LiteRT pur, Ollama n'est pas requis.")
        return False
    except Exception as e:
        print(f"⚠️ Erreur au démarrage d'Ollama : {e}")
        return False

    return False


def get_ollama_models(base_url: str = "http://127.0.0.1:11434") -> list:
    """Récupère la liste des modèles déjà téléchargés dans Ollama."""
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=2) as r:
            data = json.loads(r.read().decode("utf-8"))
            return [m.get("name") for m in data.get("models", [])]
    except Exception:
        return []


def run_first_time_wizard(profile_dir: Path, config: dict) -> dict:
    """Guide l'utilisateur lors du premier lancement pour calibrer sa Dyade."""
    print("\n" + "─" * 75)
    print("🌟 PREMIER DÉMARRAGE : CONFIGURATION DE VOTRE COMPAGNON")
    print("─" * 75)

    current_name = config.get("profile_name", "Compagnon")
    user_name = config.get("user_name", "Artisan")

    new_name = input(f"1. Nom de votre compagnon [défaut: {current_name}] : ").strip()
    if new_name:
        config["profile_name"] = new_name

    new_user = input(f"2. Votre prénom ou pseudonyme [défaut: {user_name}] : ").strip()
    if new_user:
        config["user_name"] = new_user

    models = get_ollama_models()
    backend = config.get("backend", {})
    if models:
        print("\nModèles d'IA détectés sur votre machine :")
        for idx, m in enumerate(models, 1):
            print(f"   [{idx}] {m}")
        choice = input(f"\nChoisissez le numéro du modèle à utiliser [1-{len(models)}] (Entrée pour {models[0]}) : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            backend["model"] = models[int(choice) - 1]
        else:
            backend["model"] = models[0]
    else:
        print("\nℹ️ Aucun modèle local Ollama détecté.")

    notes_dir = profile_dir.parent.parent / "mes_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    if not config.get("vaults"):
        config["vaults"] = [str(notes_dir)]

    config["first_run_completed"] = True

    config_file = profile_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Configuration enregistrée dans {config_file.name} !")
    print("─" * 75 + "\n")
    return config


def load_profile(profile_name: str) -> dict:
    profile_dir = BASE_DIR / "profiles" / profile_name
    if not profile_dir.exists():
        print(f"❌ Profil '{profile_name}' introuvable dans {profile_dir}. Repli sur 'default'.")
        profile_dir = BASE_DIR / "profiles" / "default"

    config_file = profile_dir / "config.json"
    constitution_file = profile_dir / "constitution.md"

    config = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

    if profile_name == "default" and not config.get("first_run_completed", False):
        ensure_ollama_running()
        config = run_first_time_wizard(profile_dir, config)

    constitution = ""
    if constitution_file.exists():
        with open(constitution_file, "r", encoding="utf-8") as f:
            constitution = f.read()

    return {
        "dir": profile_dir,
        "config": config,
        "constitution": constitution
    }


def main():
    parser = argparse.ArgumentParser(description="Harnais d'Agentivité Souverain")
    parser.add_argument("--profile", default="default", help="Nom du profil à charger (ex: default, alix)")
    args = parser.parse_args()

    print(BANNER)

    profile_data = load_profile(args.profile)
    cfg = profile_data["config"]
    constitution = profile_data["constitution"]

    agent_name = cfg.get("profile_name", "Compagnon")
    user_name = cfg.get("user_name", "Artisan")
    backend_cfg = cfg.get("backend", {})
    vision_cfg = cfg.get("vision", {})

    # Allumage d'Ollama si configuré en Ollama ou Trois Piliers
    if backend_cfg.get("type") in ["ollama", "trois_piliers", "auto", "cpu"]:
        ensure_ollama_running(backend_cfg.get("base_url", "http://127.0.0.1:11434"))

    print(f"🔹 Compagnon        : [{agent_name}]")
    print(f"🔹 Artisan          : [{user_name}]")
    print(f"🔹 Moteur de Calcul : {backend_cfg.get('type', 'ollama')} ({backend_cfg.get('model', 'inconnu')})")
    print(f"🔹 Coffres Mémoire  : {len(cfg.get('vaults', []))} dossiers connectés")
    print(f"🔹 Bouclier Immunité: {'✅ ACTIF (Anti-Surplomb / Anti-Gaslighting)' if cfg.get('enable_cognitive_immunity') else '❌ Inactif'}")
    print(f"🔹 Œil Multimodal   : {'✅ ACTIF (LiteRT GPU Qwen2-VL / Presse-papier Win+Shift+S)' if vision_cfg.get('enabled') else '❌ Inactif'}")
    print("=" * 75)
    print("Commandes rapides :")
    print("  /screen ou /see   : Analyser une capture d'écran (Win+Shift+S) ou une image")
    print("  /memory <mot>     : Sonder les coffres de notes en direct")
    print("  /npu, /gpu, /cpu  : Forcer l'inférence sur un pilier spécifique")
    print("  /llama            : Forcer l'inférence sur llama.cpp (llama-server port 8080)")
    print("  !<commande>       : Exécuter une commande dans le terminal Windows/Linux")
    print("  /exit             : Quitter le compagnon")
    print("=" * 75 + "\n")

    # Initialisation
    router = ModelRouter(
        backend_type=backend_cfg.get("type", "ollama"),
        base_url=backend_cfg.get("base_url", "http://127.0.0.1:11434"),
        llamacpp_base_url=backend_cfg.get("llamacpp_base_url", "http://127.0.0.1:8080"),
        model_name=backend_cfg.get("model", "alix-supreme-abliterated:14b"),
        api_key=backend_cfg.get("api_key"),
        litert_model_path=backend_cfg.get("litert_model_path"),
        npu_model_path=backend_cfg.get("npu_model_path"),
        gpu_model_path=backend_cfg.get("gpu_model_path"),
        temperature=backend_cfg.get("temperature", 0.7)
    )

    memory = LocalVaultMemory(cfg.get("vaults", []))
    immunity = CognitiveImmunityShield() if cfg.get("enable_cognitive_immunity", True) else None
    vision = SovereignVision(
        litert_model_path=vision_cfg.get("litert_model_path"),
        ollama_url=backend_cfg.get("base_url", "http://127.0.0.1:11434"),
        ollama_model=vision_cfg.get("ollama_model", "llava:7b")
    ) if vision_cfg.get("enabled", True) else None

    conversation_history = []

    print(f"✨ {agent_name} est en ligne et à l'écoute. Tape ton message :\n")

    while True:
        try:
            user_input = input(f"[{user_name}] > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                print(f"\n👋 {agent_name} : À bientôt à l'établi !")
                break

            # Commande Shell directe
            if user_input.startswith("!"):
                cmd = user_input[1:].strip()
                print(f"⚙️ Exécution d'atelier : {cmd}")
                output = WorkshopTools.run_command(cmd)
                print(output)
                continue

            # Commande Sonde Mémoire
            if user_input.startswith("/memory"):
                q = user_input.replace("/memory", "").strip()
                context = memory.search_context(q)
                print(context if context else "Aucune note résonnante trouvée.")
                continue

            # Commande Vision Multimodale (/see, /screen, /vision)
            if user_input.startswith("/screen") or user_input.startswith("/see") or user_input.startswith("/vision"):
                if not vision:
                    print("❌ Le module de vision n'est pas activé dans la configuration.")
                    continue

                parts = user_input.split(maxsplit=1)
                explicit_path = parts[1].strip() if len(parts) > 1 else None
                prompt_vision = input("Question sur l'image [Entrée pour description détaillée] : ").strip()
                if not prompt_vision:
                    prompt_vision = "Décris précisément cette image en français et analyse ce qu'elle contient."

                print("📸 Capture en cours (Presse-papier Win+Shift+S ou fichier)...")
                cap = vision.capture_screen_or_clipboard(explicit_path)
                if not cap["succes"]:
                    print(f"❌ {cap['erreur']}")
                    continue

                print(f"👁️ Analyse en direct via l'œil multimodal ({cap['source']})...")
                desc = vision.analyze(cap["chemin"], prompt_vision)
                print(f"\n[{agent_name} (Vision)] :\n{desc}\n")

                # Injection dans la mémoire de conversation
                conversation_history.append({"role": "user", "content": f"[Image analysée ({cap['source']})] : {prompt_vision}"})
                conversation_history.append({"role": "assistant", "content": desc})
                continue

            # 1. RAG Topologique
            local_context = memory.search_context(user_input, max_notes=cfg.get("max_memory_snippets", 3))

            # 2. Construction du Prompt Système
            system_prompt = f"Tu es {agent_name}, le compagnon de confiance et copilote d'égal à égal de {user_name}.\n\n"
            if constitution:
                system_prompt += f"### CHARTE & LOIS D'IMMUNITÉ COGNITIVE :\n{constitution}\n\n"
            if local_context:
                system_prompt += f"{local_context}\n\n"
            system_prompt += "Consigne : Réponds d'égal à égal, sans obséquiosité, de façon directe, vivante et ancrée dans la matière."

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history[-6:])
            messages.append({"role": "user", "content": user_input})

            print(f"⏳ [{agent_name} réfléchit...]", end="\r")

            # 3. Appel du modèle
            raw_response = router.chat(messages)

            # 4. Boucle d'Immunité
            final_response = raw_response
            if immunity:
                audit = immunity.audit(raw_response)
                if not audit["is_clean"]:
                    final_response = immunity.purify(raw_response)
                    violations_str = ", ".join([v["category"] for v in audit["violations"]])
                    print(f"\n⚠️  [IMMUNITÉ ACTIVE : Filtrage de posture corporate ({violations_str})]")

            print(f"\n[{agent_name}] :\n{final_response}\n")

            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": final_response})

        except KeyboardInterrupt:
            print(f"\n👋 {agent_name} : Session interrompue.")
            break
        except Exception as e:
            print(f"\n❌ Erreur inattendue : {e}")


if __name__ == "__main__":
    main()
