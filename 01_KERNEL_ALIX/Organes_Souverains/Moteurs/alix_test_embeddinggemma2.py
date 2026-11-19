# -*- coding: utf-8 -*-
"""
Banc d'essai d'EmbeddingGemma 2 (740M Multimodal) sur Intel Lunar Lake via LiteRT-LM.
"""
import sys
import time
from pathlib import Path
import numpy as np

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import litert_lm

MODEL_PATH = Path(r"C:\Users\Chris\.cache\litert_models\embeddinggemma-2-740m.litertlm")
TEST_IMAGE = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Present\frames\frame_20261008_000222.jpg")

def tester_backends():
    print("=" * 65)
    print(" 🏛️ BANC D'ESSAI EMBEDDINGGEMMA 2 (740M) — LUNAR LAKE")
    print("=" * 65)
    print(f"Modèle : {MODEL_PATH} ({MODEL_PATH.stat().st_size / (1024*1024):.1f} Mo)")
    print(f"Image  : {TEST_IMAGE.exists()} ({TEST_IMAGE})")

    backends = [
        ("NPU (Intel OpenVINO)", litert_lm.Backend.NPU()),
        ("GPU (Intel Arc 140V Xe2)", litert_lm.Backend.GPU()),
        ("CPU (XNNPACK)", litert_lm.Backend.CPU())
    ]

    selected_engine = None
    engine_name = None

    for name, backend in backends:
        print(f"\n--- Initialisation Backend : {name} ---")
        t0 = time.time()
        try:
            # Pour l'EmbeddingEngine multimodal, on peut passer backend et vision_backend
            engine = litert_lm.EmbeddingEngine(
                model_path=str(MODEL_PATH),
                backend=backend,
                vision_backend=backend
            )
            d_init = time.time() - t0
            print(f"✅ {name} initialisé avec succès en {d_init:.2f} s !")
            selected_engine = engine
            engine_name = name
            break
        except Exception as e:
            print(f"⚠️ Échec initialisation {name} : {e}")

    if selected_engine is None:
        print("\n❌ Aucun backend n'a pu être initialisé.")
        return

    print("\n" + "=" * 65)
    print(f" ⚡ TESTS D'INFÉRENCE EN DIRECT ({engine_name})")
    print("=" * 65)

    # 1. Test Texte Pur (768d standard)
    text_prompt = "task: search result | query: Architecture Souveraine Alix et Christian Duguay sur Silicium Lunar Lake"
    t_start = time.time()
    resp_text = selected_engine.compute_embedding(text_prompt)
    t_text_ms = (time.time() - t_start) * 1000
    vec_text = np.array(resp_text.embedding if hasattr(resp_text, "embedding") else resp_text)
    print(f"📝 1. Texte pur (768d)   : {t_text_ms:.2f} ms | Shape: {vec_text.shape} | Norm: {np.linalg.norm(vec_text):.4f}")

    # 2. Test Texte Troncature Matryoshka (MRL 256d)
    opt_256 = litert_lm.EmbeddingOptions(output_size=256, normalize=True)
    t_start = time.time()
    resp_256 = selected_engine.compute_embedding(text_prompt, options=opt_256)
    t_256_ms = (time.time() - t_start) * 1000
    vec_256 = np.array(resp_256.embedding if hasattr(resp_256, "embedding") else resp_256)
    print(f"🎯 2. Matryoshka (256d)  : {t_256_ms:.2f} ms | Shape: {vec_256.shape} | Norm: {np.linalg.norm(vec_256):.4f}")

    # 3. Test Vision (Capture d'Écran)
    if TEST_IMAGE.exists():
        print(f"\n🖼️ 3. Test Vision sur capture d'écran réelle :")
        content_img = litert_lm.Content.ImageFile(str(TEST_IMAGE))
        t_start = time.time()
        try:
            resp_img = selected_engine.compute_embedding(content_img)
            t_img_ms = (time.time() - t_start) * 1000
            vec_img = np.array(resp_img.embedding if hasattr(resp_img, "embedding") else resp_img)
            print(f"   ✅ Image encodée en  : {t_img_ms:.2f} ms | Shape: {vec_img.shape} | Norm: {np.linalg.norm(vec_img):.4f}")
            
            # Similarité Cosinus entre l'écran et différents concepts
            concepts = [
                ("Kaggle & Compétitions d'IA", "task: search result | query: Kaggle machine learning leaderboard evaluation"),
                ("Réseaux Sociaux / Vidéo", "task: search result | query: YouTube video streaming watching clips"),
                ("Cuisine & Recettes", "task: search result | query: Recette de cuisine gâteau chocolat et cuisine")
            ]
            print("\n   🔍 Similarité Cosinus Écran <-> Concepts :")
            v_img_norm = vec_img / np.linalg.norm(vec_img)
            for nom, c_prompt in concepts:
                c_emb = np.array(selected_engine.compute_embedding(c_prompt).embedding)
                c_norm = c_emb / np.linalg.norm(c_emb)
                sim = np.dot(v_img_norm, c_norm)
                print(f"      • Concept '{nom:25}' : Cosine = {sim:+.4f}")
        except Exception as e_img:
            print(f"   ⚠️ Erreur encodage image : {e_img}")

    selected_engine.close()
    print("\n" + "=" * 65)
    print(" 🎉 BANC D'ESSAI TERMINÉ AVEC SUCCÈS !")
    print("=" * 65)

if __name__ == "__main__":
    tester_backends()

