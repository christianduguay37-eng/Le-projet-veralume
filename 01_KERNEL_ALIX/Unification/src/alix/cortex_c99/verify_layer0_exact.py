# -*- coding: utf-8 -*-
"""
Vérification exacte de la Couche 0 (Attention + FFN) entre ProSparse-7B et TowerInstruct-7B
pour voir si tous les produits matriciels GGUF (Q, K, V, Wo, Gate, Up, Down) sont alignés à >0.98 !
"""
import json
import struct
from pathlib import Path
import numpy as np
import gguf
from test_revelation_q4k_rope import dequant_q4k_ggml_exact
from compare_step_by_step_l0 import dequant_q6k_ggml_exact

GGUF_PATH = Path(r"C:\Users\Christian\.ollama\models\blobs\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce")
PROSPARSE_DIR = Path(r"C:\Users\Christian\Desktop\Projet alix\Mes_Projets_Veralume\sonde\prosparse-llama-2-7b")

def rms(x, w, eps=1e-5):
    return x / np.sqrt((x * x).mean(-1, keepdims=True) + eps) * w

def rope_hf(x, pos, theta=10000.0):
    d = x.shape[-1]
    inv = 1.0 / theta ** (np.arange(0, d, 2, dtype=np.float32) / d)
    ang = pos[:, None] * inv[None, :]
    cos, sin = np.cos(np.concatenate([ang, ang], -1)), np.sin(np.concatenate([ang, ang], -1))
    return x * cos + np.concatenate([-x[..., d // 2:], x[..., : d // 2]], -1) * sin

def rope_gguf(x, pos, theta=10000.0):
    # x shape: (seq, n_heads, head_dim)
    d = x.shape[-1]
    inv = 1.0 / theta ** (np.arange(0, d, 2, dtype=np.float32) / d)
    ang = pos[:, None, None] * inv[None, None, :] # (seq, 1, d/2)
    cos, sin = np.cos(ang), np.sin(ang)
    x0 = x[..., 0::2]
    x1 = x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = x0 * cos - x1 * sin
    out[..., 1::2] = x0 * sin + x1 * cos
    return out

def main():
    ou = {}
    for f in sorted(PROSPARSE_DIR.glob("*.safetensors")):
        with open(f, "rb") as b:
            n = struct.unpack("<Q", b.read(8))[0]
            h = json.loads(b.read(n))
        for k, v in h.items():
            if k != "__metadata__":
                ou[k] = (f, 8 + n + v["data_offsets"][0], v["shape"], v["dtype"])

    def load_ps(key):
        f, off, sh, dt = ou[key]
        mm = np.memmap(f, dtype=np.float32 if dt == "F32" else np.uint16, mode="r", offset=off, shape=tuple(sh))
        return np.array(mm, dtype=np.float32) if dt == "F32" else (np.array(mm, dtype=np.uint32) << 16).view(np.float32)

    reader = gguf.GGUFReader(str(GGUF_PATH))
    tensors = {t.name: t for t in reader.tensors}

    def load_gguf_mat(name, n_blocks_per_row, qtype):
        t = tensors[name]
        rows = t.data.shape[0]
        mat = np.zeros((rows, n_blocks_per_row * 256), dtype=np.float32)
        for r in range(rows):
            raw = bytes(t.data[r])
            if qtype == "Q4_K":
                mat[r] = dequant_q4k_ggml_exact(raw, n_blocks_per_row)
            else:
                mat[r] = dequant_q6k_ggml_exact(raw, n_blocks_per_row)
        return mat

    ids = [1, 997, 27073, 316, 425, 3444, 707]
    pos = np.arange(len(ids), dtype=np.float32)

    # 1. Embeddings
    emb_ps = load_ps("model.embed_tokens.weight")[ids]
    t_emb = tensors["token_embd.weight"]
    emb_gg = np.stack([dequant_q4k_ggml_exact(bytes(t_emb.data[i]), 16) for i in ids])
    print(f"Cosinus Embeddings : {np.sum(emb_ps * emb_gg) / (np.linalg.norm(emb_ps) * np.linalg.norm(emb_gg)):.6f}")

    # 2. Attention Couche 0
    h_ps = rms(emb_ps, load_ps("model.layers.0.input_layernorm.weight"))
    h_gg = rms(emb_gg, np.array(tensors["blk.0.attn_norm.weight"].data, dtype=np.float32))

    Wq_ps = load_ps("model.layers.0.self_attn.q_proj.weight")
    Wk_ps = load_ps("model.layers.0.self_attn.k_proj.weight")
    Wv_ps = load_ps("model.layers.0.self_attn.v_proj.weight")
    Wo_ps = load_ps("model.layers.0.self_attn.o_proj.weight")

    Wq_gg = load_gguf_mat("blk.0.attn_q.weight", 16, "Q4_K")
    Wk_gg = load_gguf_mat("blk.0.attn_k.weight", 16, "Q4_K")
    Wv_gg = load_gguf_mat("blk.0.attn_v.weight", 16, "Q6_K")
    Wo_gg = load_gguf_mat("blk.0.attn_output.weight", 16, "Q4_K")

    q_ps = rope_hf((h_ps @ Wq_ps.T).reshape(-1, 32, 128).transpose(1, 0, 2), pos).transpose(1, 0, 2)
    k_ps = rope_hf((h_ps @ Wk_ps.T).reshape(-1, 32, 128).transpose(1, 0, 2), pos).transpose(1, 0, 2)
    v_ps = (h_ps @ Wv_ps.T).reshape(-1, 32, 128)

    q_gg = rope_gguf((h_gg @ Wq_gg.T).reshape(-1, 32, 128), pos)
    k_gg = rope_gguf((h_gg @ Wk_gg.T).reshape(-1, 32, 128), pos)
    v_gg = (h_gg @ Wv_gg.T).reshape(-1, 32, 128)

    # Produits scalaires d'attention Q @ K.T sur la tête 0 !
    sc_ps = (q_ps[:, 0] @ k_ps[:, 0].T) / np.sqrt(128.0)
    sc_gg = (q_gg[:, 0] @ k_gg[:, 0].T) / np.sqrt(128.0)
    print(f"Cosinus Scores Attention Tête 0 (après RoPE) : {np.sum(sc_ps * sc_gg) / (np.linalg.norm(sc_ps) * np.linalg.norm(sc_gg)):.6f}")
    print(f"Cosinus V (v_ps vs v_gg) : {np.sum(v_ps * v_gg) / (np.linalg.norm(v_ps) * np.linalg.norm(v_gg)):.6f}")
    print(f"Cosinus Wo (Wo_ps vs Wo_gg) : {np.sum(Wo_ps * Wo_gg) / (np.linalg.norm(Wo_ps) * np.linalg.norm(Wo_gg)):.6f}")

    # Sortie Attention complète
    n = len(ids)
    masque = np.triu(np.full((n, n), -1e30, dtype=np.float32), 1)
    out_ps = np.zeros((n, 32, 128), dtype=np.float32)
    out_gg = np.zeros((n, 32, 128), dtype=np.float32)
    for hh in range(32):
        r1 = (q_ps[:, hh] @ k_ps[:, hh].T) / np.sqrt(128.0) + masque
        s1 = np.exp(r1 - r1.max(-1, keepdims=True))
        s1 /= s1.sum(-1, keepdims=True)
        out_ps[:, hh] = s1 @ v_ps[:, hh]

        r2 = (q_gg[:, hh] @ k_gg[:, hh].T) / np.sqrt(128.0) + masque
        s2 = np.exp(r2 - r2.max(-1, keepdims=True))
        s2 /= s2.sum(-1, keepdims=True)
        out_gg[:, hh] = s2 @ v_gg[:, hh]

    print(f"Cosinus out_attn (avant Wo) : {np.sum(out_ps * out_gg) / (np.linalg.norm(out_ps) * np.linalg.norm(out_gg)):.6f}")
    dx_ps = out_ps.reshape(n, 4096) @ Wo_ps.T
    dx_gg = out_gg.reshape(n, 4096) @ Wo_gg.T
    print(f"Cosinus dx_attn (après Wo)  : {np.sum(dx_ps * dx_gg) / (np.linalg.norm(dx_ps) * np.linalg.norm(dx_gg)):.6f}")
    x_attn_ps = emb_ps + dx_ps
    x_attn_gg = emb_gg + dx_gg
    print(f"Cosinus x après Attention L0 : {np.sum(x_attn_ps * x_attn_gg) / (np.linalg.norm(x_attn_ps) * np.linalg.norm(x_attn_gg)):.6f}")

if __name__ == "__main__":
    main()
