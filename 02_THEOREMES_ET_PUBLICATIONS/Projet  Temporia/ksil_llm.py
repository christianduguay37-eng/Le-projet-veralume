"""
===============================================================================
              KAIROS-SILICON NATIVE LLM ENGINE (K-SIL LLM) v1.0
          Inférence LLM Souveraine sans Ollama pour Intel Lunar Lake 258V
   Atelier Démiurgique & Sanctuaire Exocerveau — Christian Duguay & Alix
===============================================================================
Exécute des LLM en C++ natif directement sur le silicium (Arc 140V Xe2 GPU,
NPU 4 48 TOPS, CPU Lion Cove) via OpenVINO GenAI, avec streaming temps réel.
===============================================================================
"""

import os
import sys
import time
from typing import Optional

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import openvino_genai as ov_genai

DEFAULT_MODEL_DIR = r"C:\Users\Christian\.cache\openvino_models\Qwen2.5-1.5B-Instruct-int4-ov"


class KsilLLM:
    """Moteur LLM Souverain KAIROS relié directement au silicium Lunar Lake."""

    def __init__(self, model_dir: str = DEFAULT_MODEL_DIR, device: str = "GPU"):
        self.model_dir = model_dir
        self.device = device

        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Modèle introuvable dans {model_dir}")

        print(f"[K-SIL LLM] Chargement natif sur {device} (Intel Lunar Lake)...")
        t0 = time.perf_counter()
        self.pipeline = ov_genai.LLMPipeline(model_dir, device)
        self.load_time_ms = (time.perf_counter() - t0) * 1000.0
        print(f"[K-SIL LLM] Modèle prêt en {self.load_time_ms:.1f} ms !\n")

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """Génère du texte avec affichage token-par-token en temps réel."""
        config = ov_genai.GenerationConfig()
        config.max_new_tokens = max_tokens
        config.temperature = temperature
        config.top_p = top_p

        tokens_count = 0
        t_start = None

        def stream_token(token: str) -> ov_genai.StreamingStatus:
            nonlocal tokens_count, t_start
            if t_start is None:
                t_start = time.perf_counter()
            tokens_count += 1
            sys.stdout.write(token)
            sys.stdout.flush()
            return ov_genai.StreamingStatus.RUNNING

        print("-" * 70)
        print(f"  🧠 PROMPT : {prompt}")
        print("-" * 70)
        print("  ⚡ RÉPONSE SOUVERAINE (STREAMING EN DIRECT) :\n")

        t0_total = time.perf_counter()
        result_text = self.pipeline.generate(prompt, config, stream_token)
        t_total = time.perf_counter() - t0_total

        # Durée de génération pure après le premier token
        t_gen_pure = (time.perf_counter() - t_start) if t_start else t_total
        tok_per_sec = tokens_count / t_gen_pure if t_gen_pure > 0 else 0.0

        print("\n\n" + "=" * 70)
        print("  📊 MÉTRIQUES SILICIUM EN DIRECT :")
        print("=" * 70)
        print(f"  • Puce Active             : {self.device}")
        print(f"  • Tokens Générés          : {tokens_count} tokens")
        print(f"  • Durée Totale            : {t_total:.2f} s")
        print(f"  • Vitesse de Génération   : {tok_per_sec:.1f} TOKENS / SECONDE")
        print("=" * 70 + "\n")

        return {
            "tokens": tokens_count,
            "latency_total_s": t_total,
            "tokens_per_second": tok_per_sec,
            "device": self.device,
        }


def main():
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Explique-moi en 3 phrases percutantes pourquoi la souveraineté technologique et matérielle est indispensable à un créateur."

    device = "GPU"
    llm = KsilLLM(device=device)
    llm.generate_stream(prompt, max_tokens=300)


if __name__ == "__main__":
    main()
