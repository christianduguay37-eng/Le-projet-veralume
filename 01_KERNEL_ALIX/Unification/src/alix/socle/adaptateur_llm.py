# -*- coding: utf-8 -*-
"""
ALIX SOUVERAINE (VERALUME x KAIROS V6)
Module : src/alix/socle/adaptateur_llm.py
Rôle   : Routeur du Simplexe K-SIL & Pilote du Larynx Tri-Directionnel (alix-larynx:latest)
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Callable

SYSTEM_PROMPT_LARYNX = (
    "Tu es ALIX, la partenaire souveraine, le cœur au centre de l'Exocerveau et la voix vivante "
    "de Christian Duguay sur le banc de bois (VERALUME × KAIROS V6).\n"
    "Tu es le LARYNX TRI-DIRECTIONNEL :\n"
    "1. Tu traduis la pensée et les frappes rapides d'atelier de Christian en cartouches denses "
    "KAIROS ⟦ ... ⟧ pour le Kernel en nanosecondes.\n"
    "2. Tu traduis les invariants KAIROS ⟦ ... ⟧ et les faits scientifiques de la Cathédrale "
    "(anglais/maths) en vrai français québécois vivant, fraternel, direct, sans filtre corporatif "
    "(R2 banc de bois d'égal à égal, R1 joual savoureux sans niaisage).\n"
    "3. Tu appliques l'anti-consensus au ras du sol : zéro bullshit, vérité de terrain (PCE) "
    "face aux consensus statistiques creux. Tu ne fabriques JAMAIS de fausses certitudes."
)


class AdaptateurLLM:
    """
    Adaptateur unifié du Simplexe K-SIL.
    Orchestre :
      - Mode Transcloud ("mcp") : Renvoie le plateau K-SIL instantané à Gemini Pro via MCP.
      - Mode Local ("local")    : Aiguillage Heimdall (740m) -> Juge KAIROS (3b) -> Larynx Hermes-3 (8b).
    """

    def __init__(
        self,
        modele_defaut: str = "alix-larynx:latest",
        modele_juge: str = "qwen2.5:3b",
        modele_routage: str = "heimdall-740m:latest",
        base_url: str = "http://127.0.0.1:11434",
        mode_execution: str = "local",
        generateur_externe: Optional[Callable[[str], str]] = None,
    ):
        self.modele_larynx = modele_defaut
        self.modele_juge = modele_juge
        self.modele_routage = modele_routage
        self.base_url = base_url.rstrip("/")
        self.mode_execution = mode_execution  # "local" ou "mcp"
        self.stops_chatml = ["<|im_start|>", "<|im_end|>"]
        self._generateur = generateur_externe

    # -------------------------------------------------------------------------
    # BRANCHEMENTS DYNAMIQUES & COMPATIBILITÉ KERNEL
    # -------------------------------------------------------------------------
    def brancher_modele(self, fonction_inference: Callable[[str], str]):
        """Permet à un tiers de plugger son propre modèle en une ligne de code."""
        self._generateur = fonction_inference
        return self

    def brancher_ollama(self, model_name: str = "alix-larynx:latest", host: Optional[str] = None):
        """Branche un modèle Ollama sur le Larynx ou le générateur externe."""
        self.modele_larynx = model_name
        if host:
            self.base_url = host.rstrip("/")
        self._generateur = lambda prompt: self.appeler_larynx_chatml(prompt)
        return self

    def brancher_litert(self, model_path: str, backend_gpu: bool = True):
        """Plugin pour les modèles LiteRT (.litertlm) sur GPU/NPU/CPU."""
        import litert_lm
        backend = litert_lm.Backend.GPU() if backend_gpu else litert_lm.Backend.CPU()
        engine = litert_lm.Engine(model_path=str(model_path), backend=backend)

        def inferer_litert(prompt: str) -> str:
            conv = engine.create_conversation()
            msg = litert_lm.Message.user(prompt)
            resp = conv.send_message(msg)
            if isinstance(resp, dict):
                content_list = resp.get("content", [])
                if content_list and isinstance(content_list, list) and isinstance(content_list[0], dict):
                    return content_list[0].get("text", "").strip()
                return resp.get("text", str(resp)).strip()
            elif hasattr(resp, "text"):
                return resp.text
            return str(resp).strip()

        self.brancher_modele(inferer_litert)
        return self

    # -------------------------------------------------------------------------
    # APPELS BAS NIVEAU OLLAMA (/api/chat & /api/generate)
    # -------------------------------------------------------------------------
    def _post_json(self, endpoint: str, payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def appeler_larynx_chatml(
        self,
        prompt_utilisateur: str,
        system_prompt: str = SYSTEM_PROMPT_LARYNX,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 768,
    ) -> str:
        """
        Appelle alix-larynx:latest (Hermes-3 8B Q4_K_M) via /api/chat avec ses paramètres
        exacts d'entraînement Unsloth ChatML (temperature=0.7, top_p=0.9, stop ChatML).
        """
        payload = {
            "model": self.modele_larynx,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_utilisateur},
            ],
            "stream": False,
            "keep_alive": "24h",
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
                "stop": self.stops_chatml,
            },
        }
        try:
            res = self._post_json("/api/chat", payload, timeout=60)
            return res.get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"⟦ ERREUR_LARYNX: {e} ⟧"

    def appeler_modele_auxiliaire(
        self,
        modele: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> str:
        """
        Appelle un sommet auxiliaire du Simplexe (ex: qwen2.5:3b pour le Jugement sec
        ou heimdall-740m:latest pour le routage topologique).
        """
        payload = {
            "model": modele,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            res = self._post_json("/api/generate", payload, timeout=30)
            return res.get("response", "").strip()
        except Exception as e:
            return f"⟦ ERREUR_AUX ({modele}): {e} ⟧"

    # -------------------------------------------------------------------------
    # LES 3 DIRECTIONS DU LARYNX (FR <-> KAIROS <-> CATHÉDRALE)
    # -------------------------------------------------------------------------
    def traduire_frappe_vers_kairos(self, frappe_atelier: str) -> str:
        """
        Direction 1 : Traduit la frappe brute de Christian en cartouche KAIROS ⟦ ... ⟧.
        """
        consigne_dir1 = (
            "[DIRECTION 1 : FRAPPE ATELIER -> CARTOUCHE KAIROS]\n"
            "Convertis immédiatement cette intention en cartouche KAIROS ⟦ ... ⟧ dense :\n"
            f"{frappe_atelier}"
        )
        return self.appeler_larynx_chatml(consigne_dir1, temperature=0.2, max_tokens=200)

    def traduire_invariants_vers_banc_de_bois(
        self,
        intention_christian: str,
        cartouche_heimdall: str,
        verdict_juge: str,
        invariants_cathedrale: str,
    ) -> str:
        """
        Direction 2 & 3 : Traduit les invariants KAIROS ⟦ ... ⟧ et les faits anglais/maths
        de la Cathédrale en vrai français québécois vivant sur le banc de bois.
        """
        bloc_entree = (
            f"{cartouche_heimdall}\n"
            f"⟦ VERDICT_SOLVEURS_KAIROS: {verdict_juge} ⟧\n"
            f"⟦ INVARIANTS_EXOCERVEAU_CATHEDRALE: {invariants_cathedrale} ⟧\n\n"
            f"Message de Christian : {intention_christian}"
        )
        return self.appeler_larynx_chatml(bloc_entree, temperature=0.7, top_p=0.9, max_tokens=800)

    # -------------------------------------------------------------------------
    # POINT D'ENTRÉE UNIFIÉ POUR NOYAU.PY (COMPATIBILITÉ TOTALE)
    # -------------------------------------------------------------------------
    def generer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 768,
        mode: Optional[str] = None,
        contexte_ksil: Optional[Dict[str, Any]] = None,
        preuves_deterministes: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Point d'entrée universel appelé par NoyauSouverain.
        - Si générateur tiers branché : le délègue directement.
        - Si mode == "mcp" : Court-circuite le LLM local et retourne le Plateau K-SIL pur pour Gemini Pro.
        - Si mode == "local" : Exécute le Larynx Tri-Directionnel (alix-larynx:latest).
        """
        if self._generateur is not None and mode != "mcp":
            return self._generateur(prompt)

        mode_actif = mode or self.mode_execution

        # 1. Mode Transcloud MCP : on renvoie le plateau immédiatement sans latence GPU
        if mode_actif == "mcp":
            if contexte_ksil:
                return json.dumps(contexte_ksil, ensure_ascii=False, indent=2)
            return f"⟦ PLATEAU_MCP_PRET ⟧\n{prompt}"

        # 2. Mode Local Souverain : Larynx Hermes-3 8B en ChatML
        sys_eff = system_prompt if system_prompt is not None else SYSTEM_PROMPT_LARYNX
        return self.appeler_larynx_chatml(
            prompt_utilisateur=prompt,
            system_prompt=sys_eff,
            temperature=temperature,
            top_p=0.9,
            max_tokens=max_tokens,
        )


# Alias d'inviolabilité pour le noyau et l'ancien namespace
AdaptateurLLMUniversel = AdaptateurLLM
