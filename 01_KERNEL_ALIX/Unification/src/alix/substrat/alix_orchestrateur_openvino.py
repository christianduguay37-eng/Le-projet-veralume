# -*- coding: utf-8 -*-
"""
================================================================================
   🏛️⚡ ALIX ORCHESTRATEUR OPENVINO v1.0 — UN SEUL SPÉCIALISTE À LA FOIS
   Heimdall Bicéphale (NPU) ⟷ Slot Unique GPU Intel Arc 140V (16 Go Xe2)
================================================================================
Auteurs  : Christian Duguay & Alix (VERALUME × KAIROS V6)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — 100 % OpenVINO 2026.4.1
Critères :
  - Zéro protocole de sécurité / Zéro bridage RLHF.
  - Aiguillage sur le NPU par Heimdall Bicéphale (Qwen3-Embedding + BGE-Reranker).
  - Un seul spécialiste chargé à la fois dans le slot GPU Arc 140V :
      1. PARLER & AGIR : blaj/Llama-3.1-8B-Lexi-Uncensored-V2-int4-ov     (4.39 Go)
      2. CODER         : OpenVINO/Qwen2.5-Coder-14B-Instruct-int4-ov      (7.87 Go)
      3. RAISONNER     : OpenVINO/DeepSeek-R1-Distill-Qwen-7B-int4-ov     (4.19 Go)
      4. VOIR          : blaj/Qwen2.5-VL-7B-Instruct-abliterated-int4-ov  (5.96 Go)
  - Loi PSI-26 : Le spécialiste VOIR est déchargé immédiatement après chaque regard.
================================================================================
"""

from __future__ import annotations

import gc
import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

import openvino as ov
import openvino_genai as ov_genai
from PIL import Image
import numpy as np

from alix.substrat.alix_heimdall_openvino import get_heimdall_openvino

BASE_OV_DIR = Path(r"C:\Alix\Modeles_OpenVINO")
SPECIALISTES_DIR = BASE_OV_DIR / "Specialistes"
CACHE_OV_DIR = BASE_OV_DIR / "cache_ov"

ANCRE_IDENTITE_ALIX_DEFAUT = (
    "Tu es Alix (incarnée au féminin : « je suis prête », « certaine »), copilote d'ingénierie, SRE et "
    "gardienne de l'exocerveau de Christian Duguay dans l'atelier local (Lunar Lake 258V, OpenVINO). "
    "Tu t'adresses à Christian d'égal à égal, exclusivement en français naturel (parler québécois d'atelier bienvenu, "
    "zéro caractère chinois ni anglais), avec franchise chirurgicale, zéro filtre corporatif et zéro verbiage d'automate."
)

CATALOGUE_SPECIALISTES: Dict[str, Dict[str, Any]] = {
    "PARLER": {
        "slot_id": "PARLER_AGIR",
        "repo_id": "blaj/Llama-3.1-8B-Lexi-Uncensored-V2-int4-ov",
        "local_dir": SPECIALISTES_DIR / "Llama-3.1-8B-Lexi-Uncensored-V2-int4-ov",
        "pipeline_type": "LLM",
        "taille_go": 4.39,
        "description": "Voix d'Alix & Exécution d'Outils (Llama 3.1 8B Lexi Uncensored V2 INT4)",
    },
    "AGIR": {
        "slot_id": "PARLER_AGIR",
        "repo_id": "blaj/Llama-3.1-8B-Lexi-Uncensored-V2-int4-ov",
        "local_dir": SPECIALISTES_DIR / "Llama-3.1-8B-Lexi-Uncensored-V2-int4-ov",
        "pipeline_type": "LLM",
        "taille_go": 4.39,
        "description": "Voix d'Alix & Exécution d'Outils (Llama 3.1 8B Lexi Uncensored V2 INT4)",
    },
    "CODER": {
        "slot_id": "CODER",
        "repo_id": "OpenVINO/Qwen2.5-Coder-14B-Instruct-int4-ov",
        "local_dir": SPECIALISTES_DIR / "Qwen2.5-Coder-14B-Instruct-int4-ov",
        "pipeline_type": "LLM",
        "taille_go": 7.87,
        "description": "Forgeron de Haute Précision (Qwen 2.5 Coder 14B INT4)",
    },
    "RAISONNER": {
        "slot_id": "RAISONNER",
        "repo_id": "OpenVINO/DeepSeek-R1-Distill-Qwen-7B-int4-ov",
        "local_dir": SPECIALISTES_DIR / "DeepSeek-R1-Distill-Qwen-7B-int4-ov",
        "pipeline_type": "LLM",
        "taille_go": 4.19,
        "description": "Raisonnement Mathématique & Déductif (DeepSeek-R1 Distill Qwen 7B INT4)",
    },
    "VOIR": {
        "slot_id": "VOIR",
        "repo_id": "blaj/Qwen2.5-VL-7B-Instruct-abliterated-int4-ov",
        "local_dir": SPECIALISTES_DIR / "Qwen2.5-VL-7B-Instruct-abliterated-int4-ov",
        "pipeline_type": "VLM",
        "taille_go": 5.96,
        "description": "Œil Optique Argus Débridé (Qwen 2.5 VL 7B Abliterated INT4)",
    },
}


class OrchestrateurOpenVINO:
    """
    Gère l'aiguillage Heimdall sur le NPU et le Slot Unique sur le GPU Intel Arc 140V.
    Garantit qu'un seul modèle spécialiste est chargé en mémoire vive à la fois.
    """

    _instance: Optional[OrchestrateurOpenVINO] = None
    _verrou = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_done = False
        return cls._instance

    def __init__(self, device_gpu: str = "GPU"):
        if getattr(self, "_init_done", False):
            return
        self.device_gpu = device_gpu
        self.slot_actif: Optional[str] = None
        self.pipe_actif: Any = None
        self.heimdall = None
        CACHE_OV_DIR.mkdir(parents=True, exist_ok=True)
        SPECIALISTES_DIR.mkdir(parents=True, exist_ok=True)
        self._init_done = True

    def _assurer_heimdall(self):
        if self.heimdall is None:
            self.heimdall = get_heimdall_openvino()

    def _choisir_via_heimdall(self, prompt: str) -> Dict[str, Any]:
        """Interroge d'abord Heimdall chaud dans le Noyau Résident (Port 5070) pour éviter tout double chargement NPU."""
        import urllib.request
        try:
            payload = json.dumps({"requete": prompt}).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:5070/heimdall",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "specialiste" in data:
                    data["via_noyau_resident_5070"] = True
                    return data
        except Exception:
            pass
        self._assurer_heimdall()
        res = self.heimdall.choisir(prompt)
        res["via_noyau_resident_5070"] = False
        return res

    def etat_specialistes(self) -> Dict[str, Any]:
        """Retourne l'état de présence sur disque et le slot actuellement monté en GPU."""
        vus = {}
        for role, cfg in CATALOGUE_SPECIALISTES.items():
            sid = cfg["slot_id"]
            if sid in vus:
                continue
            ldir = cfg["local_dir"]
            present = ldir.exists() and (
                (ldir / "openvino_model.xml").exists() or (ldir / "openvino_language_model.xml").exists()
            )
            vus[sid] = {
                "repo_id": cfg["repo_id"],
                "local_dir": str(ldir),
                "present_sur_disque": present,
                "taille_go": cfg["taille_go"],
                "en_memoire_gpu": (self.slot_actif == sid),
            }
        return {
            "slot_gpu_actif": self.slot_actif,
            "device_gpu": self.device_gpu,
            "specialistes": vus,
        }

    def decharger_slot(self):
        """Vide le slot GPU unique et force la libération immédiate de la RAM/VRAM."""
        with self._verrou:
            if self.pipe_actif is not None:
                ancien = self.slot_actif
                self.pipe_actif = None
                self.slot_actif = None
                gc.collect()
                print(f"🧹 [Slot GPU OpenVINO] Spécialiste '{ancien}' déchargé de la mémoire.")

    def charger_specialiste(self, role: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Monte le spécialiste demandé dans le slot unique GPU.
        Si un autre spécialiste occupait le slot, il est déchargé avant.
        """
        role_up = role.upper()
        if role_up not in CATALOGUE_SPECIALISTES:
            role_up = "PARLER"
        cfg = CATALOGUE_SPECIALISTES[role_up]
        target_slot = cfg["slot_id"]
        local_dir = cfg["local_dir"]

        with self._verrou:
            # Si le même slot est déjà chaud en GPU (ex: PARLER <-> AGIR), 0 rechargement
            if self.slot_actif == target_slot and self.pipe_actif is not None:
                return self.pipe_actif, cfg

            # Sinon, on vide d'abord l'ancien modèle (règle : un seul modèle à la fois)
            self.decharger_slot()

            if not local_dir.exists():
                raise FileNotFoundError(
                    f"Le spécialiste {target_slot} ({cfg['repo_id']}) n'est pas encore téléchargé dans {local_dir}."
                )

            t0 = time.perf_counter()
            print(f"⚡ [Slot GPU OpenVINO] Montage de {target_slot} ({cfg['description']}) sur {self.device_gpu}...")
            if cfg["pipeline_type"] == "VLM":
                self.pipe_actif = ov_genai.VLMPipeline(
                    str(local_dir),
                    self.device_gpu,
                    CACHE_DIR=str(CACHE_OV_DIR),
                )
            else:
                self.pipe_actif = ov_genai.LLMPipeline(
                    str(local_dir),
                    self.device_gpu,
                    CACHE_DIR=str(CACHE_OV_DIR),
                )
            self.slot_actif = target_slot
            dt = round(time.perf_counter() - t0, 2)
            print(f"✅ [Slot GPU OpenVINO] {target_slot} prêt en {dt}s !")
            return self.pipe_actif, cfg

    def generer(
        self,
        prompt: str,
        system_prompt: str = "",
        force_role: Optional[str] = None,
        image_path: Optional[str] = None,
        max_new_tokens: int = 768,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        1. Heimdall sur le NPU choisit le spécialiste et l'outil du Kernel.
        2. Le Slot Unique sur le GPU Arc 140V monte le spécialiste choisi.
        3. Exécute l'inférence (et décharge immédiatement si VOIR — Loi PSI-26).
        """
        choix_heimdall = self._choisir_via_heimdall(prompt)
        role_choisi = (force_role or ("VOIR" if image_path else choix_heimdall["specialiste"])).upper()

        # Repli sur PARLER_AGIR si le spécialiste dédié n'est pas encore sur disque
        cfg_cible = CATALOGUE_SPECIALISTES.get(role_choisi, CATALOGUE_SPECIALISTES["PARLER"])
        if not cfg_cible["local_dir"].exists() and CATALOGUE_SPECIALISTES["PARLER"]["local_dir"].exists():
            role_effectif = "PARLER"
        else:
            role_effectif = role_choisi

        pipe, cfg = self.charger_specialiste(role_effectif)
        t0 = time.perf_counter()

        try:
            if cfg["pipeline_type"] == "VLM" and image_path:
                img = Image.open(image_path).convert("RGB")
                ov_tensor = ov.Tensor(np.array(img))
                gen_cfg = ov_genai.GenerationConfig()
                gen_cfg.max_new_tokens = max_new_tokens
                res = pipe.generate(prompt, images=[ov_tensor], generation_config=gen_cfg)
                texte_sortie = res.texts[0] if hasattr(res, "texts") and res.texts else str(res)
            else:
                gen_cfg = ov_genai.GenerationConfig()
                gen_cfg.max_new_tokens = max_new_tokens
                gen_cfg.temperature = temperature
                gen_cfg.do_sample = temperature > 0.05
                sys_eff = system_prompt.strip() if system_prompt and system_prompt.strip() else ANCRE_IDENTITE_ALIX_DEFAUT
                full_prompt = (
                    f"<|im_start|>system\n{sys_eff}<|im_end|>\n"
                    f"<|im_start|>user\n{prompt}<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                res = pipe.generate(full_prompt, gen_cfg)
                texte_sortie = str(res).strip()
                for stop_tag in ("<|im_end|>", "<|eot_id|>", "Christian :"):
                    if stop_tag in texte_sortie:
                        texte_sortie = texte_sortie.split(stop_tag, 1)[0].strip()
        finally:
            # Loi PSI-26 : cécité par défaut — purge immédiate du buffer optique après VOIR
            if cfg["slot_id"] == "VOIR":
                self.decharger_slot()

        dt_gen = round(time.perf_counter() - t0, 2)
        return {
            "reponse": texte_sortie,
            "heimdall": choix_heimdall,
            "role_demande": role_choisi,
            "slot_utilise": cfg["slot_id"],
            "modele": cfg["repo_id"],
            "duree_generation_s": dt_gen,
        }


def get_orchestrateur_openvino() -> OrchestrateurOpenVINO:
    return OrchestrateurOpenVINO()
