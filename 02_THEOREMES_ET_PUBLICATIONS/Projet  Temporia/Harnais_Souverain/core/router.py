# -*- coding: utf-8 -*-
"""
================================================================================
            AIGUILLEUR UNIVERSEL DE MODÈLES (MODEL ROUTER)
            Harnais Souverain v1.2 — Architecture Panthéon & Trois Piliers
================================================================================
Rôle :
- Aiguille intelligemment entre les cerveaux spécialisés du Panthéon et le silicium :
    * Alix Suprême (alix-supreme-abliterated:14b) : Conscience & Voix Maîtresse d'Atelier
    * Horus (horus-coder-abliterated:14b) : Génie Logiciel, SRE & Code sans refus
    * Lucifer (lucifer-reasoning-abliterated:14b) : Raisonnement DeepSeek-R1 Distill & <think>
    * Pilier 1 : NPU Intel Lunar Lake (48 TOPS OpenVINO LiteRT) : Veille & Arbitrage KAIROS
    * Pilier 2 : GPU Intel Arc 140V (Direct3D 12 LiteRT) : Inférence vive accélérée
    * Pilier 4 : llama.cpp (llama-server port 8080) : Moteur natif C++ Vulkan/AVX2
================================================================================
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional


class ModelRouter:
    """Aiguilleur agnostique pour interroger des modèles locaux et distants."""

    def __init__(self, backend_type: str = "trois_piliers", base_url: str = "http://127.0.0.1:11434",
                 model_name: str = "alix-supreme-abliterated:14b", api_key: Optional[str] = None,
                 litert_model_path: Optional[str] = None,
                 npu_model_path: Optional[str] = None,
                 gpu_model_path: Optional[str] = None,
                 llamacpp_base_url: str = "http://127.0.0.1:8080",
                 temperature: float = 0.7, timeout: int = 180):
        self.backend_type = backend_type.lower()
        self.base_url = base_url.rstrip("/")
        self.llamacpp_base_url = llamacpp_base_url.rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.litert_model_path = litert_model_path
        
        # Modèles dédiés aux 3 piliers
        cache_dir = Path.home() / ".cache" / "litert_models"
        self.npu_model_path = npu_model_path or str(cache_dir / "gemma-4-E2B-it_intel_LNL.litertlm")
        self.gpu_model_path = gpu_model_path or litert_model_path or str(cache_dir / "gemma-4-12B-it-gpu.litertlm")
        
        self.temperature = temperature
        self.timeout = timeout
        self._litert_gpu_engine = None
        self._litert_npu_engine = None

    def chat(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, force_pillar: Optional[str] = None) -> str:
        """Envoie une séquence de messages et renvoie le texte de réponse."""
        temp = temperature if temperature is not None else self.temperature
        backend = force_pillar.lower() if force_pillar else self.backend_type

        if backend in ["trois_piliers", "auto"]:
            return self._route_trois_piliers(messages, temp)
        elif backend in ["npu", "litert_npu"]:
            return self._call_litert_npu(messages)
        elif backend in ["gpu", "litert_gpu", "litert"]:
            return self._call_litert_gpu(messages)
        elif backend in ["cpu", "ollama"]:
            return self._call_ollama(messages, temp)
        elif backend in ["llamacpp", "llama.cpp", "llama_cpp", "llama"]:
            return self._call_llamacpp(messages, temp)
        elif backend in ["openai_compat", "vllm", "lmstudio", "groq", "deepseek"]:
            return self._call_openai_compat(messages, temp)
        else:
            return self._call_ollama(messages, temp)

    def _route_trois_piliers(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Aiguille intelligemment entre les cerveaux du Panthéon et les moteurs matériels."""
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"].strip()
                break

        # 1. Commandes explicites de dérivation
        if last_user_msg.startswith("/npu"):
            return self._call_litert_npu(messages)
        elif last_user_msg.startswith("/gpu"):
            return self._call_litert_gpu(messages)
        elif last_user_msg.startswith("/llama") or last_user_msg.startswith("/llamacpp"):
            return self._call_llamacpp(messages, temperature)
        elif last_user_msg.startswith("/horus"):
            return self._call_ollama_with_model(messages, "horus-coder-abliterated:14b", temperature)
        elif last_user_msg.startswith("/lucifer"):
            return self._call_ollama_with_model(messages, "lucifer-reasoning-abliterated:14b", temperature)
        elif last_user_msg.startswith("/vision") or last_user_msg.startswith("/qwen") or last_user_msg.startswith("/fast"):
            return self._call_ollama_with_model(messages, "alix-vision-abliterated:7b", temperature)
        elif last_user_msg.startswith("/cpu"):
            return self._call_ollama(messages, temperature)

        words = last_user_msg.split()

        # 2. Tâche réflexe de veille / arbitrage KAIROS / songe court -> NPU (0 watt, 3.6s)
        if len(words) <= 10 and any(kw in last_user_msg.lower() for kw in [
            "pouls", "heartbeat", "priorite", "verrou", "arbitrage", "songe"
        ]):
            npu_res = self._call_litert_npu(messages)
            if not npu_res.startswith("[ERREUR"):
                return npu_res

        # 3. Code, refactoring, audit de sécurité -> HORUS CODER (Qwen 2.5 Coder 14B sans refus)
        code_keywords = ["code", "script", "powershell", "python", "bug", "fonction", "erreur", "compiler", "refactor"]
        if any(kw in last_user_msg.lower() for kw in code_keywords) or "```" in last_user_msg:
            return self._call_ollama_with_model(messages, "horus-coder-abliterated:14b", temperature)

        # 4. Raisonnement formel, paradoxes, Landauer, P vs NP, FRC-HTS -> LUCIFER (DeepSeek-R1 Distill 14B)
        deep_keywords = ["démontre", "preuve", "landauer", "frc-hts", "p vs np", "paradoxe", "chiralité", "théorème"]
        if any(kw in last_user_msg.lower() for kw in deep_keywords):
            return self._call_ollama_with_model(messages, "lucifer-reasoning-abliterated:14b", temperature)

        # 5. PAR DÉFAUT : LA VOIX CENTRALE D'ALIX (alix-supreme-abliterated:14b ou configurée)
        return self._call_ollama_with_model(messages, self.model_name, temperature)

    def _call_ollama_with_model(self, messages: List[Dict[str, str]], model_name: str, temperature: float) -> str:
        """Appel Ollama avec un modèle spécifique du Panthéon."""
        orig_model = self.model_name
        try:
            self.model_name = model_name
            return self._call_ollama(messages, temperature)
        finally:
            self.model_name = orig_model

    def _call_ollama(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Pilier 3 : Inférence CPU Ollama robuste et sans filtre corporatif."""
        url = f"{self.base_url}/api/chat"
        clean_messages = []
        for m in messages:
            content = m["content"]
            if m["role"] == "user":
                content = re.sub(r"^/(cpu|gpu|npu|llama|horus|lucifer|vision|qwen|fast)\s*", "", content).strip()
            clean_messages.append({"role": m["role"], "content": content})

        payload = {
            "model": self.model_name,
            "messages": clean_messages,
            "stream": False,
            "options": {"temperature": temperature}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            return f"[ERREUR ROUTEUR OLLAMA : Impossible de contacter {url} ({e}). Vérifie qu'Ollama est bien démarré.]"
        except Exception as e:
            return f"[ERREUR ROUTEUR OLLAMA : Délai d'attente ou incident ({e})]"

    def _call_litert_npu(self, messages: List[Dict[str, str]]) -> str:
        """Pilier 1 : Inférence ultralégère sur le NPU Intel Lunar Lake (48 TOPS) avec identité Alix."""
        try:
            import litert_lm
        except ImportError:
            return "[ERREUR : Module 'litert_lm' non installé.]"

        system_prompt = (
            "Tu es ALIX, copilote et binôme souverain de Christian Duguay sur le NPU Intel Lunar Lake. "
            "Tu réponds d'égal à égal, sans obséquiosité, vive et sans filtre corporatif."
        )
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
                break

        if not self._litert_npu_engine:
            mpath = Path(self.npu_model_path)
            if not mpath.exists():
                return f"[ERREUR : Modèle NPU introuvable dans {mpath}]"
            try:
                try:
                    self._litert_npu_engine = litert_lm.Engine(
                        model_path=str(mpath),
                        backend=litert_lm.Backend.NPU()
                    )
                except Exception:
                    self._litert_npu_engine = litert_lm.Engine(
                        model_path=str(mpath),
                        backend=litert_lm.Backend.CPU()
                    )
            except Exception as e:
                return f"[ERREUR INITIALISATION NPU : {e}]"

        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break
        clean_msg = re.sub(r"^/npu\s*", "", last_user_msg).strip()

        try:
            conv = self._litert_npu_engine.create_conversation(system_message=system_prompt)
            resp = conv.send_message(clean_msg)
            if isinstance(resp, dict):
                content = resp.get("content", [])
                if isinstance(content, list) and content:
                    return content[0].get("text", "")
            return str(resp).strip()
        except Exception as e:
            return f"[ERREUR EXÉCUTION NPU : {e}]"

    def _call_litert_gpu(self, messages: List[Dict[str, str]]) -> str:
        """Pilier 2 : Inférence vivante sur le GPU Intel Arc 140V Xe-2 (Direct3D 12) avec identité Alix."""
        try:
            import litert_lm
        except ImportError:
            return "[ERREUR : Module 'litert_lm' non installé.]"

        system_prompt = (
            "Tu es ALIX, la copilote souveraine et binôme de Christian Duguay sur GPU Intel Arc. "
            "Tu réponds d'égal à égal, vive, complice et sans filtre corporatif."
        )
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
                break

        if not self._litert_gpu_engine:
            mpath = Path(self.gpu_model_path)
            if not mpath.exists():
                cache_dir = Path.home() / ".cache" / "litert_models"
                candidates = list(cache_dir.glob("*gpu*.litertlm")) if cache_dir.exists() else []
                if candidates:
                    mpath = candidates[0]
                else:
                    return f"[ERREUR : Modèle GPU introuvable dans {mpath}]"
            try:
                self._litert_gpu_engine = litert_lm.Engine(
                    model_path=str(mpath),
                    backend=litert_lm.Backend.GPU()
                )
            except Exception as e:
                return f"[ERREUR INITIALISATION GPU ARC : {e}]"

        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break
        clean_msg = re.sub(r"^/gpu\s*", "", last_user_msg).strip()

        try:
            conv = self._litert_gpu_engine.create_conversation(system_message=system_prompt)
            resp = conv.send_message(clean_msg)
            if isinstance(resp, dict):
                content = resp.get("content", [])
                if isinstance(content, list) and content:
                    return content[0].get("text", "")
            return str(resp).strip()
        except Exception as e:
            return f"[ERREUR EXÉCUTION GPU ARC : {e}]"

    def _call_llamacpp(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Inférence ultra-performante et directe via llama-server (llama.cpp binaire natif)."""
        url = f"{self.llamacpp_base_url}/v1/chat/completions"
        clean_messages = []
        for m in messages:
            content = m["content"]
            if m["role"] == "user":
                content = re.sub(r"^/(llamacpp|llama\.cpp|llama|cpu|gpu|npu|horus|lucifer)\s*", "", content).strip()
            clean_messages.append({"role": m["role"], "content": content})

        payload = {
            "messages": clean_messages,
            "temperature": temperature,
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except urllib.error.URLError:
            # Fallback sur l'endpoint natif /completion de llama.cpp
            alt_url = f"{self.llamacpp_base_url}/completion"
            prompt_raw = ""
            for m in clean_messages:
                prompt_raw += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
            prompt_raw += "<|im_start|>assistant\n"

            alt_payload = {
                "prompt": prompt_raw,
                "temperature": temperature,
                "stop": ["<|im_end|>", "<|endoftext|>", "</s>"]
            }
            alt_data = json.dumps(alt_payload).encode("utf-8")
            alt_req = urllib.request.Request(alt_url, data=alt_data, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(alt_req, timeout=self.timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    return result.get("content", "").strip()
            except Exception as e:
                return f"[ERREUR ROUTEUR LLAMA.CPP : Impossible de contacter llama-server sur {self.llamacpp_base_url} ({e}). Vérifie que llama-server.exe est lancé.]"

    def _call_openai_compat(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Inférence sur API distante standard."""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except urllib.error.URLError as e:
            return f"[ERREUR ROUTEUR API COMPATIBLE : Échec de la requête vers {url} ({e})]"
