# -*- coding: utf-8 -*-
"""
===============================================================================
       👁️ ALIX SONAR MULTIMODAL v1.0 — EMBEDDINGGEMMA 2 LUNAR LAKE 🧠
===============================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — LiteRT-LM (XNNPACK / OpenVINO)
Modèle   : embeddinggemma-2-740m.litertlm (~462 Mo)
Mandat :
    - Encodage multimodal universel ultra-frugal (Texte, Écran, Audio, Vidéo).
    - Remplace définitivement la dépendance aux modèles 7B-VL lourds.
    - Projection instantanée dans l'espace unifié 768d / 256d (Matryoshka MRL).
    - Sonde continue de l'écran en temps réel pour Alix_Sonde_Present.
===============================================================================
"""

from alix.socle.chemins import HOME_DIR, VAULT_DIR
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import litert_lm

MODEL_PATH = (HOME_DIR / ".cache" / "litert_models" / "embeddinggemma-2-740m.litertlm")
PRESENT_FRAMES_DIR = (VAULT_DIR / "Present" / "frames")

BALISES_ATELIER = [
    ("Kaggle & Compétitions IA", "task: search result | query: Kaggle machine learning coding notebook evaluation leaderboard"),
    ("Obsidian & Exocerveau", "task: search result | query: Obsidian markdown notes exocerveau knowledge base writing"),
    ("YouTube & Vidéos / Musique", "task: search result | query: YouTube video streaming watching music entertainment"),
    ("Terminal & Compilation Code", "task: search result | query: Terminal PowerShell Python compile git commit build execution"),
    ("Sciences & Papiers Académiques", "task: search result | query: CERN Zenodo research paper physics math equations review"),
    ("Actualités & Société / Politique", "task: search result | query: Actualités journal politique Québec nouvelles articles de presse")
]


class AlixSonarMultimodal:
    """Moteur de sonar sémantique multimodal d'atelier."""
    _instance = None
    _engine = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AlixSonarMultimodal, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_path: Optional[Path] = None):
        if getattr(self, "_initialized", False):
            return
        self.model_path = model_path or MODEL_PATH
        self._engine = None
        self._initialized = True
        self._ensure_engine()

    def _ensure_engine(self) -> bool:
        if self._engine is not None:
            return True

        if not self.model_path.exists():
            print(f"⚠️ [Sonar Multimodal] Modèle introuvable : {self.model_path}")
            return False

        try:
            # CPU XNNPACK ultra-stable et rapide (95 ms texte / 500 ms image)
            self._engine = litert_lm.EmbeddingEngine(
                model_path=str(self.model_path),
                backend=litert_lm.Backend.CPU(),
                vision_tokens_per_image=70
            )
            return True
        except Exception as e:
            print(f"❌ [Sonar Multimodal] Erreur chargement moteur : {e}")
            return False

    def encoder_texte(self, texte: str, mrl_dim: int = 256, instruction: str = "query") -> np.ndarray:
        """Encode un texte avec instruction de tâche et troncature Matryoshka."""
        if not self._ensure_engine():
            return np.zeros(mrl_dim, dtype=np.float32)

        prompt = f"task: search result | {instruction}: {texte}"
        options = litert_lm.EmbeddingOptions(output_size=mrl_dim, normalize=True)
        res = self._engine.compute_embedding(prompt, options=options)
        vec = np.array(res.embedding if hasattr(res, "embedding") else res, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def encoder_image(self, chemin_image: Union[str, Path], mrl_dim: int = 256, fast_mode: bool = True) -> np.ndarray:
        """Encode une image en vecteur MRL normalisé."""
        if not self._ensure_engine():
            return np.zeros(mrl_dim, dtype=np.float32)

        p = Path(chemin_image)
        if not p.exists():
            print(f"⚠️ Image inexistante : {p}")
            return np.zeros(mrl_dim, dtype=np.float32)

        tokens_vision = 70 if fast_mode else 140
        options = litert_lm.EmbeddingOptions(
            output_size=mrl_dim,
            normalize=True,
            vision_tokens_per_image=tokens_vision
        )
        content = litert_lm.Content.ImageFile(str(p))
        res = self._engine.compute_embedding(content, options=options)
        vec = np.array(res.embedding if hasattr(res, "embedding") else res, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def encoder_audio(self, chemin_audio: Union[str, Path], mrl_dim: int = 256) -> np.ndarray:
        """Encode un fichier audio (wav, mp3, ogg)."""
        if not self._ensure_engine():
            return np.zeros(mrl_dim, dtype=np.float32)

        p = Path(chemin_audio)
        if not p.exists():
            print(f"⚠️ Audio inexistant : {p}")
            return np.zeros(mrl_dim, dtype=np.float32)

        options = litert_lm.EmbeddingOptions(output_size=mrl_dim, normalize=True)
        content = litert_lm.Content.AudioFile(str(p))
        res = self._engine.compute_embedding(content, options=options)
        vec = np.array(res.embedding if hasattr(res, "embedding") else res, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def sonder_ecran_actuel(self, top_k: int = 3) -> Dict[str, Any]:
        """Analyse en direct la capture la plus récente de l'écran."""
        frames = list(PRESENT_FRAMES_DIR.glob("*.jpg"))
        if not frames:
            return {"statut": "erreur", "message": "Aucune capture d'écran trouvée"}

        latest_frame = max(frames, key=os.path.getmtime)
        t0 = time.time()
        v_img = self.encoder_image(latest_frame, mrl_dim=256, fast_mode=True)
        d_enc = round((time.time() - t0) * 1000, 1)

        scores = []
        for etiquette, query in BALISES_ATELIER:
            v_balise = self.encoder_texte(query, mrl_dim=256)
            sim = float(np.dot(v_img, v_balise))
            scores.append((etiquette, round(sim, 4)))

        scores.sort(key=lambda x: x[1], reverse=True)

        return {
            "statut": "succes",
            "frame": latest_frame.name,
            "temps_encodage_ms": d_enc,
            "palier_mrl": 256,
            "domaine_dominant": scores[0][0],
            "score_dominant": scores[0][1],
            "top_affinites": scores[:top_k]
        }

    def close(self):
        if self._engine is not None:
            try:
                self._engine.close()
            except Exception:
                pass
            self._engine = None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Alix Sonar Multimodal (EmbeddingGemma 2)")
    parser.add_argument("--ecran", action="store_true", help="Sonder l'écran actuel")
    parser.add_argument("--texte", type=str, help="Encoder un texte")
    args = parser.parse_args()

    sonar = AlixSonarMultimodal()

    if args.ecran or len(sys.argv) == 1:
        print("\n🔍 --- SONDE EN DIRECT DE L'ÉCRAN ACTUEL ---")
        diag = sonar.sonder_ecran_actuel()
        print(f"🖼️ Capture        : {diag.get('frame')}")
        print(f"⚡ Temps encodage : {diag.get('temps_encodage_ms')} ms (256d MRL)")
        print(f"🎯 Pôle Dominant  : {diag.get('domaine_dominant')} ({diag.get('score_dominant'):+.4f})")
        print("\n📊 Top Affinités Sémantiques :")
        for etiquette, score in diag.get("top_affinites", []):
            print(f"   • {etiquette:32} : {score:+.4f}")
        print("-" * 50)

    if args.texte:
        print(f"\n📝 Encodage texte : « {args.texte} »")
        v = sonar.encoder_texte(args.texte, mrl_dim=256)
        print(f"Vecteur 256d généré | Norme : {np.linalg.norm(v):.4f}")

    sonar.close()
