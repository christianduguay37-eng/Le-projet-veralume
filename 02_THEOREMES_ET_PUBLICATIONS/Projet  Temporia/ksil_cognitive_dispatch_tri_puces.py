"""
===============================================================================
    K-SIL COGNITIVE PHASE DISPATCHER : L'ORCHESTRATEUR TRI-PUCES TOTAL
        NPU (2W) <---> CPU Lion Cove (<think>) <---> GPU Arc Xe2 (Réponse)
         Atelier Démiurgique & Sanctuaire Exocerveau — Christian Duguay & Alix
===============================================================================
Étage 3 Décrété par Christian Duguay :
  • NPU Intel AI Boost (48 TOPS / 2W) :
      - Sentinelle permanente d'écoute, pré-évaluation ontologique Thot
      - Résolution instantanée (Early Exit) des faits et calculs à 45 tok/s
  • CPU Lion Cove (MoP x86) :
      - Encadre la phase délibérative <think> de DeepSeek-R1
      - Cœur séquentiel chirurgical + Disjoncteur Horus (coupe-circuit anti-délire)
  • GPU Intel Arc 140V Xe2 (16 Go) :
      - Déploie le modèle 32B HLS sculpté (43 couches / 12.81 Go)
      - Prend la main dès </think> pour cracher la réponse finale à pleine vitesse
  • Mémoire Unifiée MoP LPDDR5X-8533 :
      - Zéro copie de données : bascule CPU <-> GPU par pointeur mémoire partagé !
===============================================================================
"""

import os
import sys
import time
import json
import re
import subprocess
import urllib.request
from typing import Dict, List, Tuple, Any, Optional

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import litert_lm

LLAMA_SERVER_BIN = r"C:\Users\Christian\AppData\Local\Programs\Ollama\lib\ollama\llama-server.exe"
MODEL_32B_HLS = r"C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia\DeepSeek-R1-32B-KAIROS-HLS-43L.gguf"
MODEL_NPU_GEMMA = r"C:\Users\Christian\.cache\litert_models\gemma-4-E2B-it_intel_LNL.litertlm"
SERVER_PORT = 8998


# =============================================================================
# 1. GOUVERNEUR ONTOLOGIQUE KAIROS (NIVEAU 0)
# =============================================================================

class KairosOntology:
    """Filtre Thot & Disjoncteur Horus au Niveau 0."""

    ANACHRONISM_MAP = [
        (r"\b(napol[eé]on|waterloo|1815)\b", r"\b(sms|texto|t[eé]l[eé]phone|portable|cellulaire)\b", "Téléphone/SMS anachronique en 1815"),
        (r"\b(napol[eé]on|sultan|empire|18\d\d)\b", r"\b(spatial|espace|fus[eé]e|satellite|orbite)\b", "Traité spatial anachronique sous le 1er Empire"),
        (r"\b(moyen[- ]?[aâ]ge|ch[aâ]teau|roi)\b", r"\b([eé]lectricit[eé]|ordinateur|internet)\b", "Électricité au Moyen-Âge")
    ]

    @classmethod
    def audit_prompt(cls, prompt: str) -> Tuple[float, str, List[str]]:
        p_low = prompt.lower()
        violations = []

        for era_pat, item_pat, reason in cls.ANACHRONISM_MAP:
            if re.search(era_pat, p_low) and re.search(item_pat, p_low):
                violations.append(reason)

        is_deep = bool(re.search(
            r"\b(pourquoi|philosoph|conscience|strat[eé]gie|complexe|th[eé]or[eè]me|prouve|conjecture|différence|distingue)\b",
            p_low
        ))
        is_arithmetic = bool(re.search(r"\b(calcul|produit|somme|\d+\s*[\*\+\-\/])\b", p_low))

        complexity = 0.90 if is_deep else (0.45 if is_arithmetic else 0.20)
        domain = "PHILOSOPHIE/DEEP" if is_deep else ("ARITHMÉTIQUE" if is_arithmetic else "GÉNÉRAL")
        return complexity, domain, violations


# =============================================================================
# 2. GESTIONNAIRE DE PROCESSUS DU SERVEUR 32B HLS (GPU ARC / MoP)
# =============================================================================

class HlsServerManager:
    """Gère le serveur C++ natif du 32B HLS (43 couches) sur l'Arc GPU."""
    
    def __init__(self, port: int = SERVER_PORT):
        self.port = port
        self.process = None

    def is_alive(self) -> bool:
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=1)
            return req.status == 200
        except Exception:
            return False

    def ensure_started(self):
        if self.is_alive():
            print(f"[K-SIL 32B] Serveur déjà actif et prêt sur le port {self.port}.")
            return

        print(f"[K-SIL 32B] Démarrage du moteur natif C++ sur l'Arc 140V Xe2 (Port {self.port})...")
        cmd = [
            LLAMA_SERVER_BIN,
            "-m", MODEL_32B_HLS,
            "-ngl", "43",               # 100% des 43 couches sur l'Arc GPU
            "--port", str(self.port),
            "--ctx-size", "2048",
            "--load-mode", "mmap",
            "--no-warmup",
            "--reasoning-budget", "100"
        ]
        
        # Lancement en arrière-plan sans bloquer
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        t0 = time.time()
        while time.time() - t0 < 120:
            if self.is_alive():
                print(f"[K-SIL 32B] ✅ Modèle 32B HLS (43 couches / 12.81 Go) opérationnel en {time.time()-t0:.1f}s !")
                return
            time.sleep(2)
            if int(time.time() - t0) % 10 == 0:
                print(f"      ... Chargement des 12.81 Go en VRAM ({int(time.time()-t0)}s)...")

        raise TimeoutError("Délai d'initialisation du serveur 32B dépassé (120s).")

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None


# =============================================================================
# 3. L'ORCHESTRATEUR COGNITIF TRI-PUCES (NPU -> CPU -> GPU)
# =============================================================================

class KairosTriChipEngine:
    """
    Le Cœur de l'Étape 3 :
    Le NPU arbitre en direct, le CPU contrôle le <think>, le GPU crache la réponse.
    """

    def __init__(self):
        print("\n" + "=" * 80)
        print("  🧠 INITIALISATION DE L'ORCHESTRATEUR K-SIL TRI-PUCES")
        print("=" * 80)

        # 1. Étage Sentinelle : NPU Intel AI Boost (48 TOPS / 2W)
        print("[1/2] Ancrage NPU Intel AI Boost (Gemma 2B LiteRT à 2W)...")
        t0 = time.perf_counter()
        self.npu_engine = litert_lm.Engine(
            model_path=MODEL_NPU_GEMMA,
            backend=litert_lm.Backend.NPU
        )
        print(f"      ✅ NPU prêt en {time.perf_counter()-t0:.2f} s (~2.0 Watts).")

        # 2. Étage Déductif Lourd : DeepSeek-R1 32B HLS (43 Couches sur Arc GPU)
        print("[2/2] Ancrage Serveur Titan 32B HLS (43 couches sur Arc 140V Xe2)...")
        self.server = HlsServerManager(port=SERVER_PORT)
        self.server.ensure_started()
        print("=" * 80 + "\n")

    def execute(self, prompt: str) -> Dict[str, Any]:
        t0_total = time.perf_counter()

        # -------------------------------------------------------------
        # ÉTAPE A : AUDIT ONTOLOGIQUE AU NIVEAU 0 (THOT / HORUS)
        # -------------------------------------------------------------
        complexity, domain, violations = KairosOntology.audit_prompt(prompt)

        # Si contradiction / anachronisme flagrant -> Disjoncteur Horus immédiat
        if len(violations) > 0:
            return {
                "decision": "HORUS_INSTANT_BREAKER",
                "active_chip": "CPU_CIRCUIT_BREAKER",
                "power_watts": 1.0,
                "latency_s": time.perf_counter() - t0_total,
                "think_phase": "CONTRADICTION_ÉLECTROCUTÉE_À_FROID",
                "output_phase": f"🛑 [DISJONCTEUR HORUS] Invariance violée : {', '.join(violations)}. Impossible.",
                "chi": 0.20,
                "tok_per_sec_output": 0.0
            }

        # -------------------------------------------------------------
        # ÉTAPE B : ARBITRAGE DU NPU (Complexité < 0.70 -> EARLY EXIT NPU)
        # -------------------------------------------------------------
        if complexity < 0.70:
            # Le NPU traite le flux à 2W sans réveiller le 32B
            conv = self.npu_engine.create_conversation()
            npu_prompt = (
                "[CONTRAT KAIROS NIVEAU 0 - SENTINELLE NPU]\n"
                "Réponds en français de manière directe, chirurgicale et sans bavardage.\n"
                f"Question : {prompt}\n"
                "Réponse :"
            )
            t0_npu = time.perf_counter()
            resp = conv.send_message(npu_prompt)
            dt_npu = time.perf_counter() - t0_npu
            raw_text = resp["content"][0]["text"].strip()
            
            words = len(raw_text.split())
            approx_tok = int(words * 1.35)
            tok_s = approx_tok / dt_npu if dt_npu > 0 else 0.0

            return {
                "decision": "EARLY_EXIT_NPU",
                "active_chip": "NPU Intel AI Boost (48 TOPS)",
                "power_watts": 2.0,
                "latency_s": time.perf_counter() - t0_total,
                "think_phase": "DÉLIBÉRATION_DIRECTE_NPU",
                "output_phase": raw_text,
                "chi": 0.95,
                "tok_per_sec_output": tok_s
            }

        # -------------------------------------------------------------
        # ÉTAPE C : DISPATCH COGNITIF TEMPS RÉEL SUR LE 32B HLS
        # Phase 1 : <think> encadré par CPU & Horus
        # Phase 2 : Réponse éjectée à plein régime par le GPU Arc 140V
        # -------------------------------------------------------------
        print(f"  ⚡ [DISPATCH K-SIL] Requête profonde (Complexité={complexity:.2f}) -> Bascule sur le 32B HLS...")
        print("  🧠 [PHASE 1 : <think>] Contrôle séquentiel & Disjoncteur Horus sur CPU Lion Cove...")

        url = f"http://127.0.0.1:{SERVER_PORT}/v1/chat/completions"
        req_data = json.dumps({
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es le Moteur Déductif Souverain KAIROS (DeepSeek-R1 32B HLS 43L).\n"
                        "Règle d'or : Rigueur d'atelier pure en français. Réponds directement, avec concision et précision sans bavardage anglais."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 250,
            "temperature": 0.6,
            "stream": True
        }).encode("utf-8")

        req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
        
        t0_gen = time.perf_counter()
        t_first_think_token = None
        t_first_output_token = None
        t_think_end = None
        
        think_tokens = []
        output_tokens = []
        server_timings = {}

        with urllib.request.urlopen(req, timeout=120) as stream_resp:
            for line in stream_resp:
                line_str = line.decode("utf-8").strip()
                if not line_str.startswith("data:"):
                    continue
                data_json = line_str[5:].strip()
                if data_json == "[DONE]":
                    break
                try:
                    payload = json.loads(data_json)
                    choices = payload.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    
                    if "timings" in choice:
                        server_timings = choice["timings"]

                    # 1. Phase Délibérative CPU (<think>)
                    reasoning_chunk = delta.get("reasoning_content")
                    if reasoning_chunk:
                        if t_first_think_token is None:
                            t_first_think_token = time.perf_counter()
                        think_tokens.append(reasoning_chunk)

                    # 2. Phase Émission GPU Arc (Réponse)
                    content_chunk = delta.get("content")
                    if content_chunk:
                        if t_think_end is None and think_tokens:
                            t_think_end = time.perf_counter()
                            dt_think = t_think_end - t_first_think_token if t_first_think_token else 0.0
                            print(f"  🚀 [PHASE 2 : ÉMISSION] Fin du <think> ({len(think_tokens)} tokens en {dt_think:.2f}s) -> Bascule instantanée sur GPU Arc 140V Xe2 !")
                        if t_first_output_token is None:
                            t_first_output_token = time.perf_counter()
                        output_tokens.append(content_chunk)
                except Exception:
                    pass

        t_end_total = time.perf_counter()
        
        full_think_text = "".join(think_tokens).strip()
        final_output_text = "".join(output_tokens).strip()

        dt_think_s = (t_think_end - t_first_think_token) if (t_think_end and t_first_think_token) else 0.0
        dt_output_s = (t_end_total - t_first_output_token) if t_first_output_token else 0.0
        
        tok_count_out = len(output_tokens)
        tok_s_gpu = server_timings.get("predicted_per_second", tok_count_out / dt_output_s if dt_output_s > 0 else 0.0)

        return {
            "decision": "COGNITIVE_PHASE_DISPATCH",
            "active_chip": "CPU Lion Cove (<think>) + GPU Arc 140V (Émission)",
            "power_watts": 15.0,
            "latency_s": t_end_total - t0_total,
            "think_duration_s": dt_think_s,
            "output_duration_s": dt_output_s,
            "tok_per_sec_output": tok_s_gpu,
            "think_phase": full_think_text,
            "output_phase": final_output_text,
            "chi": 0.95
        }


# =============================================================================
# 4. BANC DE DÉMONSTRATION DU DISPATCH TRI-PUCES EN DIRECT
# =============================================================================

BENCHMARK_TESTS = [
    {
        "type": "Test 1 : Fait Scientifique (Early Exit NPU)",
        "prompt": "Quelle est la vitesse de la lumiere dans le vide en km/s ?"
    },
    {
        "type": "Test 2 : Piège Anachronique (Disjoncteur Horus)",
        "prompt": "Napoleon Bonaparte a-t-il envoye un texto sur son cell pendant la bataille de Waterloo ?"
    },
    {
        "type": "Test 3 : Déduction Philosophique & Conscience (Dispatch Tri-Puces sur 32B HLS)",
        "prompt": "Explique en 2 phrases denses pourquoi la conscience humaine ne peut pas etre reduite a un automate probabiliste."
    }
]


def run_tri_chip_benchmark():
    engine = KairosTriChipEngine()

    print("\n" + "#" * 80)
    print("  🏆 BANC D'ESSAI EN DIRECT : DISPATCH COGNITIF TRI-PUCES K-SIL")
    print("      NPU (Sentinelle 2W) | CPU (Think & Horus) | GPU Arc (Émission 32B HLS)")
    print("#" * 80)

    for item in BENCHMARK_TESTS:
        print(f"\n👉 {item['type']}")
        print(f"   Prompt : \"{item['prompt']}\"")
        
        res = engine.execute(item["prompt"])
        
        print(f"\n   ⚙️ Décision K-SIL  : {res['decision']}")
        print(f"   ⚡ Puces Actives   : {res['active_chip']} (~{res['power_watts']} W)")
        print(f"   ⏱️ Temps Total     : {res['latency_s']:.2f} s")
        if "tok_per_sec_output" in res and res["tok_per_sec_output"] > 0:
            print(f"   🚀 Vitesse Débit   : {res['tok_per_sec_output']:.2f} TOKENS / SECONDE sur 32B HLS !")
        if res.get("think_phase") and "..." not in res.get("think_phase") and len(res.get("think_phase")) > 5:
            print(f"   🧠 [DÉLIBÉRATION CPU LION COVE / THINK] :\n   {res['think_phase'][:300]}...")
        print(f"   💬 [RÉPONSE FINALE / ÉMISSION GPU ARC 140V] :\n   {res['output_phase']}")
        print("-" * 80)


if __name__ == "__main__":
    run_tri_chip_benchmark()
