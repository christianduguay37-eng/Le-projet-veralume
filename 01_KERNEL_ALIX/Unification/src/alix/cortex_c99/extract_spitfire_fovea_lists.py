# -*- coding: utf-8 -*-
"""
==============================================================================
  🏛️⚡ EXTRACTION DES INTERRUPTEURS DE PROSPARSE-7B ("SPITFIRE") POUR C-ALIX
  Fichier : extract_spitfire_fovea_lists.py
==============================================================================
  Exécute le modèle ProSparse-Llama-2-7B (FATReLU 0.01) sur le prompt :
    "Question : Quelle est la capitale de la France ?\nRéponse :"
  et extrait, pour chacune des 32 couches (L00..L31), les indices exacts des
  neurones qui s'allument le plus fort dans Spitfire (Top-250 par couche).
  Génère `alix_spitfire_fovea.h` pour que le moteur C-Alix sur TowerInstruct-7B
  ne lise et ne calcule QUE ces neurones-là dans `gate_proj`, `up_proj` ET `down_proj` !
==============================================================================
"""

import json
import struct
import sys
import time
from pathlib import Path
import numpy as np
import sentencepiece as spm

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROSPARSE_DIR = Path(r"C:\Users\Christian\Desktop\Projet alix\Mes_Projets_Veralume\sonde\prosparse-llama-2-7b")
OUT_H = Path(r"C:\Users\Christian\Documents\Cerveau Alix\_Unification_Alix\src\alix\cortex_c99\alix_spitfire_fovea.h")

DTYPES = {"F32": np.float32, "F16": np.float16, "BF16": np.uint16}
SEUIL_FATRELU = 0.01
MAX_K_EXPORT = 512


class PoidsSafetensors:
    def __init__(self, d):
        self.ou = {}
        for f in sorted(d.glob("*.safetensors")):
            with open(f, "rb") as b:
                n = struct.unpack("<Q", b.read(8))[0]
                h = json.loads(b.read(n))
            for k, v in h.items():
                if k != "__metadata__":
                    self.ou[k] = (f, 8 + n + v["data_offsets"][0], v["shape"], v["dtype"])

    def vue(self, k):
        f, off, shape, dt = self.ou[k]
        return np.memmap(f, dtype=DTYPES[dt], mode="r", offset=off, shape=tuple(shape)), dt

    def __getitem__(self, k):
        a, dt = self.vue(k)
        a = np.array(a)
        if dt == "BF16":
            a = (a.astype(np.uint32) << 16).view(np.float32)
        return a.astype(np.float32, copy=False)


def rms(x, w, eps=1e-5):
    return x / np.sqrt((x * x).mean(-1, keepdims=True) + eps) * w


def rope_hf(x, pos, theta=10000.0):
    d = x.shape[-1]
    inv = 1.0 / (theta ** (np.arange(0, d, 2, dtype=np.float32) / d))
    ang = pos[:, None] * inv[None, :]
    cos = np.cos(np.concatenate([ang, ang], -1))
    sin = np.sin(np.concatenate([ang, ang], -1))
    return x * cos + np.concatenate([-x[..., d // 2:], x[..., : d // 2]], -1) * sin


def main():
    t0 = time.time()
    cfg = json.loads((PROSPARSE_DIR / "config.json").read_text(encoding="utf-8"))
    sp = spm.SentencePieceProcessor(model_file=str(PROSPARSE_DIR / "tokenizer.model"))
    P = PoidsSafetensors(PROSPARSE_DIR)

    prompt = "Question : Quelle est la capitale de la France ?\nRéponse :"
    tokens = [1] + sp.encode(prompt)
    pos = np.arange(len(tokens), dtype=np.float32)
    print(f"Prompt ({len(tokens)} tokens) : {prompt!r}")

    emb = P["model.embed_tokens.weight"]
    x = emb[tokens].copy()

    nh = cfg["num_attention_heads"]
    hd = cfg["hidden_size"] // nh
    eps = cfg.get("rms_norm_eps", 1e-5)

    top_indices_per_layer = []
    active_counts_per_layer = []

    for l in range(32):
        p = f"model.layers.{l}."
        h = rms(x, P[p + "input_layernorm.weight"], eps)
        Wq = P[p + "self_attn.q_proj.weight"]
        Wk = P[p + "self_attn.k_proj.weight"]
        Wv = P[p + "self_attn.v_proj.weight"]
        Wo = P[p + "self_attn.o_proj.weight"]

        q = rope_hf((h @ Wq.T).reshape(-1, nh, hd).transpose(1, 0, 2), pos).transpose(1, 0, 2)
        k = rope_hf((h @ Wk.T).reshape(-1, nh, hd).transpose(1, 0, 2), pos).transpose(1, 0, 2)
        v = (h @ Wv.T).reshape(-1, nh, hd)

        n = len(tokens)
        masque = np.triu(np.full((n, n), -1e30, dtype=np.float32), 1)
        out = np.zeros((n, nh, hd), dtype=np.float32)
        for hh in range(nh):
            sc = (q[:, hh] @ k[:, hh].T) / np.sqrt(hd) + masque
            sc = np.exp(sc - sc.max(-1, keepdims=True))
            out[:, hh] = (sc / sc.sum(-1, keepdims=True)) @ v[:, hh]
        x = x + out.reshape(n, -1) @ Wo.T

        h_ffn = rms(x, P[p + "post_attention_layernorm.weight"], eps)
        Wgate = P[p + "mlp.gate_proj.weight"]
        Wup   = P[p + "mlp.up_proj.weight"]
        Wdown = P[p + "mlp.down_proj.weight"]

        gate = h_ffn @ Wgate.T
        up   = h_ffn @ Wup.T
        allume = (gate > SEUIL_FATRELU)
        act = np.where(allume, gate, 0.0) * up

        # Sur le dernier token (qui prédit ' Paris') :
        last_act = np.abs(act[-1])
        n_on = int(allume[-1].sum())
        active_counts_per_layer.append(n_on)
        top_k_idx = np.argsort(-last_act)[:MAX_K_EXPORT]
        top_indices_per_layer.append(top_k_idx.tolist())

        x = x + act @ Wdown.T
        print(f"  Couche L{l:02d} : {n_on:4d} / 11008 neurones allumés ({n_on/110.08:4.1f}%) | Top-3 = {top_k_idx[:3].tolist()}")

    # Vérifier la sortie de ProSparse-7B
    x_final = rms(x[-1:], P["model.norm.weight"], eps)[0]
    Whead = P["lm_head.weight"]
    logits = Whead @ x_final
    top5 = np.argsort(-logits)[:5]
    print("\nTop-5 ProSparse-7B complet :")
    for r, tid in enumerate(top5):
        print(f"  #{r+1} Token #{tid} ({sp.id_to_piece(int(tid))!r}) : Logit = {logits[tid]:.2f}")

    # Écrire le header C99 alix_spitfire_fovea.h
    lines = [
        "/* Neurones actifs extraits de ProSparse-Llama-2-7B (Spitfire) pour C-Alix */",
        "#ifndef ALIX_SPITFIRE_FOVEA_H",
        "#define ALIX_SPITFIRE_FOVEA_H",
        "#include <stdint.h>",
        "",
        f"#define SPITFIRE_MAX_K {MAX_K_EXPORT}",
        "",
        "static const uint16_t SPITFIRE_ACTIVE_COUNT[32] = {",
        "    " + ", ".join(str(c) for c in active_counts_per_layer),
        "};",
        "",
        f"static const uint16_t SPITFIRE_TOP_NEURONS[32][{MAX_K_EXPORT}] = {{"
    ]
    for l in range(32):
        arr_str = ", ".join(str(idx) for idx in top_indices_per_layer[l])
        lines.append(f"    /* L{l:02d} */ {{ {arr_str} }},")
    lines.append("};")
    lines.append("#endif")

    OUT_H.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nHeader C sauvegardé dans {OUT_H} en {time.time() - t0:.1f} s !")


if __name__ == "__main__":
    main()
