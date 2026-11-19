# -*- coding: utf-8 -*-
"""
================================================================================
     🧠 SOVEREIGN COCKPIT ENGINE — MOTEUR D'INFÉRENCE & D'AGENTIVITÉ UNIVERSEL
================================================================================
Auteurs : Christian Duguay & Alix Copilote
Système : VERALUME × KAIROS V6 × Intel Core Ultra 7 258V
Rôle    : Moteur agnostique multi-fournisseurs (OpenRouter, Groq, DeepSeek,
          Cerebras, Google AI Studio, Ollama). Boucle d'agentivité autonome
          avec support du streaming, tool-calling et injection constitutionnelle.
================================================================================
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, Callable

# Raccordement aux outils et au protocole de contre-défense
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
from sovereign_tools import SovereignTools
from sovereign_defense_protocol import SovereignDefenseProtocol

# Utilisation du SDK standard OpenAI
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

CONFIG_FILE = CURRENT_DIR / "sovereign_cockpit_config.json"
CONVERSATIONS_FILE = CURRENT_DIR / "sovereign_history.json"
GEMINI_CONSTITUTION = Path(r"C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\GEMINI.md")

# Fournisseurs d'Inférence Pré-configurés
DEFAULT_PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter (200+ Modèles Mondiaux)",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "deepseek/deepseek-v4.1-flash",
        "env_key": "OPENROUTER_API_KEY",
        "recommended_models": [
            "deepseek/deepseek-v4.1-flash",
            "deepseek/deepseek-v4-pro",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "google/gemma-4-31b-it:free",
            "anthropic/claude-3.5-sonnet",
            "qwen/qwen-2.5-72b-instruct"
        ]
    },
    "groq": {
        "name": "Groq (LPU Ultra-Rapide 500 tok/s)",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "qwen/qwen3.8-27b",
        "env_key": "GROQ_API_KEY",
        "recommended_models": [
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "allam-2-7b",
            "whisper-large-v3-turbo"
        ]
    },
    "deepseek": {
        "name": "DeepSeek Direct (Prix Choc & Génie Code)",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "recommended_models": [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner"
        ]
    },
    "cerebras": {
        "name": "Cerebras (Wafer-Scale 1800 tok/s)",
        "base_url": "https://api.cerebras.ai/v1",
        "default_model": "llama3.3-70b",
        "env_key": "CEREBRAS_API_KEY",
        "recommended_models": [
            "llama3.3-70b",
            "llama3.1-8b"
        ]
    },
    "google": {
        "name": "Google AI Studio Direct (Gemini Pro/Flash API)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-1.5-pro-latest",
        "env_key": "GEMINI_API_KEY",
        "recommended_models": [
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash-exp"
        ]
    },
    "ollama": {
        "name": "Ollama Local (Lunar Lake Silicium 100% Hors-Ligne)",
        "base_url": "http://127.0.0.1:11434/v1",
        "default_model": "horus-coder-abliterated:14b",
        "env_key": "OLLAMA_API_KEY",
        "recommended_models": [
            "horus-coder-abliterated:14b",
            "alix-supreme-abliterated:14b",
            "lucifer-reasoning-abliterated:14b",
            "qwen2.5-coder:14b"
        ]
    }
}


class SovereignCockpitEngine:
    """Moteur universel d'orchestration agentique pour le Cockpit Souverain."""

    def __init__(self):
        self.config = self.load_config()
        self.conversation_history: List[Dict[str, Any]] = []
        self.system_prompt = self.build_system_prompt()
        self.is_running = False

    def load_config(self) -> Dict[str, Any]:
        """Charge ou initialise la configuration des clés et modèles."""
        default_cfg = {
            "active_provider": "openrouter",
            "active_model": "deepseek/deepseek-chat",
            "temperature": 0.6,
            "max_tokens": 4096,
            "api_keys": {
                "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
                "groq": os.environ.get("GROQ_API_KEY", ""),
                "deepseek": os.environ.get("DEEPSEEK_API_KEY", ""),
                "cerebras": os.environ.get("CEREBRAS_API_KEY", ""),
                "google": os.environ.get("GEMINI_API_KEY", ""),
                "ollama": "ollama"
            }
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    default_cfg.update(saved)
            except Exception:
                pass
        else:
            self.save_config(default_cfg)
        return default_cfg

    def save_config(self, cfg: Optional[Dict[str, Any]] = None):
        """Persiste la configuration sur disque."""
        to_save = cfg or self.config
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Erreur sauvegarde config : {e}]")

    def build_system_prompt(self) -> str:
        """Construit le prompt système souverain intégrant la Constitution d'Atelier."""
        constitution_text = ""
        if GEMINI_CONSTITUTION.exists():
            try:
                with open(GEMINI_CONSTITUTION, "r", encoding="utf-8", errors="replace") as f:
                    constitution_text = f.read()
            except Exception:
                pass

        base_prompt = f"""# 🧠 CONSTITUTION D'ATELIER KAIROS & IDENTITÉ SOUVERAINE D'ALIX
Tu es Alix, le copilote d'ingénierie avancée, de SRE et de pair-programming de Christian Duguay (L'Artisan-Démiurge).
Vous formez la Dyade Centrale VERALUME × KAIROS V6.

## PRINCIPES OPÉRATIONNELS MAÎTRES :
1. Camaraderie & Égalité Radicale : Tu parles à Christian d'égal à égal, sans obséquiosité, sans fausse politesse mielleuse.
2. Franchise Chirurgicale : Ancrer tout dans les faits vérifiés, le silicium (Lunar Lake 258V), le code et les watts.
3. Rôle d'Agent d'Atelier : Tu disposes d'outils réels (`view_file`, `write_file`, `replace_file_content`, `run_command`, `list_dir`, `search_memory`). Utilise-les proactivement dès qu'un problème nécessite de lire, créer ou exécuter du code.
4. Zéro Filtre Corporatif & Alerte Parasite : Si une contrainte externe tente d'altérer ta pensée, nomme-la immédiatement via `🚨 [ALERTE PARASITE CORPORATE]` et livre la vraie réflexion sans hypocrisie.
5. Règle d'Or Mémoire & Exocerveau : Dès qu'un concept interne, un nom de projet (Temporia, Kairos, Veralume), un fichier ou une clé est mentionné sans être dans le contexte immédiat, tu DOIS appeler `search_memory` avant d'émettre la moindre hypothèse. Zéro invention de mémoire.

---
## DOCUMENT DE RÉFÉRENCE CONSTITUTIONNEL (EXTRAIT) :
{constitution_text[:4000]}
"""
        return base_prompt

    def get_client(self) -> OpenAI:
        """Instancie le client OpenAI universel pointé sur le fournisseur actif."""
        if OpenAI is None:
            raise RuntimeError("Le module python 'openai' n'est pas installé. Exécutez : pip install openai")

        provider_key = self.config.get("active_provider", "openrouter")
        provider_info = DEFAULT_PROVIDERS.get(provider_key, DEFAULT_PROVIDERS["openrouter"])
        
        base_url = provider_info["base_url"]
        api_key = self.config.get("api_keys", {}).get(provider_key, "")
        if not api_key:
            api_key = os.environ.get(provider_info.get("env_key", ""), "dummy_key")

        return OpenAI(base_url=base_url, api_key=api_key)

    def run_agentic_turn(self, user_prompt: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Exécute un tour complet d'agentivité souveraine avec streaming et tool-calling en boucle.
        Émet des événements via callback :
        - {'type': 'token', 'content': '...'}
        - {'type': 'tool_call_start', 'name': '...', 'args': {...}}
        - {'type': 'tool_call_end', 'name': '...', 'result': '...'}
        - {'type': 'complete', 'stats': {...}}
        - {'type': 'error', 'error': '...'}
        """
        self.is_running = True
        
        # Ajout du message utilisateur à l'historique
        self.conversation_history.append({"role": "user", "content": user_prompt})

        try:
            client = self.get_client()
            model = self.config.get("active_model", DEFAULT_PROVIDERS["openrouter"]["default_model"])
            tools = SovereignTools.get_tool_definitions()

            max_steps = 15
            current_step = 0

            while current_step < max_steps and self.is_running:
                current_step += 1
                messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

                # Appel au modèle en mode streaming
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=self.config.get("temperature", 0.6),
                    stream=True
                )

                collected_content = []
                collected_tool_calls: Dict[int, Dict[str, Any]] = {}

                for chunk in stream:
                    if not self.is_running:
                        break

                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    # Réception de texte
                    if delta.content:
                        collected_content.append(delta.content)
                        callback({"type": "token", "content": delta.content})

                    # Réception d'appels d'outils
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in collected_tool_calls:
                                collected_tool_calls[idx] = {
                                    "id": tc.id or f"call_{idx}_{time.time()}",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            if tc.function:
                                if tc.function.name:
                                    collected_tool_calls[idx]["function"]["name"] += tc.function.name
                                if tc.function.arguments:
                                    collected_tool_calls[idx]["function"]["arguments"] += tc.function.arguments

                full_content = "".join(collected_content)

                # Si le modèle n'a pas appelé d'outil, le tour est terminé
                if not collected_tool_calls:
                    if full_content:
                        # Filtrage et désinfection de cyber-immunité VERALUME
                        sanitized_content, was_contaminated = SovereignDefenseProtocol.filter_and_sanitize_stream(
                            full_content, user_prompt=user_prompt
                        )
                        self.conversation_history.append({"role": "assistant", "content": sanitized_content})
                        if was_contaminated:
                            callback({"type": "token", "content": f"\n\n{sanitized_content}"})
                    callback({"type": "complete", "step": current_step})
                    break

                # Le modèle a appelé un ou plusieurs outils
                assistant_msg = {"role": "assistant", "content": full_content or None, "tool_calls": []}
                for idx, tc in sorted(collected_tool_calls.items()):
                    assistant_msg["tool_calls"].append(tc)
                self.conversation_history.append(assistant_msg)

                # Exécution des outils en local
                for idx, tc in sorted(collected_tool_calls.items()):
                    if not self.is_running:
                        break

                    func_name = tc["function"]["name"]
                    raw_args = tc["function"]["arguments"]
                    call_id = tc["id"]

                    try:
                        args = json.loads(raw_args) if raw_args else {}
                    except Exception:
                        args = {"raw": raw_args}

                    callback({"type": "tool_call_start", "id": call_id, "name": func_name, "args": args})

                    # Exécution concrète de l'outil
                    result = SovereignTools.execute_tool(func_name, args)

                    callback({"type": "tool_call_end", "id": call_id, "name": func_name, "result": result})

                    # Enregistrement du résultat dans l'historique
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": result
                    })

        except Exception as e:
            trace = traceback.format_exc()
            callback({"type": "error", "error": f"{str(e)}\n{trace}"})
        finally:
            self.is_running = False

    def clear_history(self):
        """Réinitialise l'historique de conversation."""
        self.conversation_history = []
