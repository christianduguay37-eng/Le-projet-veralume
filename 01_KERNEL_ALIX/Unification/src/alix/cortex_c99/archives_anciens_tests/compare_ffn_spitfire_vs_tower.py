# -*- coding: utf-8 -*-
"""
Comparaison directe de la distribution d'énergie des 11 008 neurones MLP :
ProSparse-7B (Interrupteurs FATReLU) vs TowerInstruct-7B (SwiGLU Dense)
sur la Couche 20 (cœur de la mémoire factuelle).
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

def silu(x):
    return x / (1.0 + np.exp(-x))

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

    # Prenons un vecteur d'entrée normalisé réaliste (ex: embedding de 'France' #3444 normalisé)
    emb_ps = load_ps("model.embed_tokens.weight")[3444]
    norm_ps = load_ps("model.layers.20.post_attention_layernorm.weight")
    h = (emb_ps / np.sqrt(np.mean(emb_ps**2) + 1e-5)) * norm_ps

    # 1. Activations MLP sur ProSparse-7B (FATReLU)
    Wg_ps = load_ps("model.layers.20.mlp.gate_proj.weight")
    Wu_ps = load_ps("model.layers.20.mlp.up_proj.weight")
    Wd_ps = load_ps("model.layers.20.mlp.down_proj.weight")
    g_ps = h @ Wg_ps.T
    u_ps = h @ Wu_ps.T
    act_ps = np.where(g_ps > 0.01, g_ps, 0.0) * u_ps
    out_ps_full = act_ps @ Wd_ps.T

    # 2. Activations MLP sur TowerInstruct-7B (SwiGLU Dense) avec le MÊME vecteur d'entrée h
    Wg_tw = load_gguf_mat("blk.20.ffn_gate.weight", 16, "Q4_K")
    Wu_tw = load_gguf_mat("blk.20.ffn_up.weight", 16, "Q4_K")
    Wd_tw = load_gguf_mat("blk.20.ffn_down.weight", 43, "Q4_K" if int(tensors["blk.20.ffn_down.weight"].tensor_type) == 12 else "Q6_K")
    g_tw = h @ Wg_tw.T
    u_tw = h @ Wu_tw.T
    act_tw = silu(g_tw) * u_tw
    out_tw_full = act_tw @ Wd_tw.T

    print("=" * 78)
    print("  COMPARAISON PHYSIQUE DES NEURONES (COUCHE 20 : PROSPARSE vs TOWER-7B)")
    print("=" * 78)
    print(f"  • Corrélation des pré-activations Gate (g_ps vs g_tw) : {np.dot(g_ps, g_tw)/(np.linalg.norm(g_ps)*np.linalg.norm(g_tw)):.4f}")
    print(f"  • Corrélation des projections Up (u_ps vs u_tw)       : {np.dot(u_ps, u_tw)/(np.linalg.norm(u_ps)*np.linalg.norm(u_tw)):.4f}")
    print(f"  • Norme sortie FFN complète ProSparse : {np.linalg.norm(out_ps_full):.4f}")
    print(f"  • Norme sortie FFN complète Tower-7B  : {np.linalg.norm(out_tw_full):.4f}")

    for K in [35, 80, 250, 500, 1000]:
        idx_ps = np.argsort(-np.abs(act_ps))[:K]
        m_ps = np.zeros_like(act_ps); m_ps[idx_ps] = 1.0
        out_ps_k = (act_ps * m_ps) @ Wd_ps.T
        cos_ps = np.dot(out_ps_full, out_ps_k) / (np.linalg.norm(out_ps_full) * np.linalg.norm(out_ps_k))
        ratio_norm_ps = np.linalg.norm(out_ps_k) / np.linalg.norm(out_ps_full)

        idx_tw = np.argsort(-np.abs(act_tw))[:K]
        m_tw = np.zeros_like(act_tw); m_tw[idx_tw] = 1.0
        out_tw_k = (act_tw * m_tw) @ Wd_tw.T
        cos_tw = np.dot(out_tw_full, out_tw_k) / (np.linalg.norm(out_tw_full) * np.linalg.norm(out_tw_k))
        ratio_norm_tw = np.linalg.norm(out_tw_k) / np.linalg.norm(out_tw_full)

        # Recouvrement des Top-K neurones entre ProSparse et Tower-7B !
        overlap = len(set(idx_ps.tolist()).intersection(set(idx_tw.tolist())))
        print(f"\n  [Fovéa K = {K:4d} neurones ({K/11008*100:4.1f}%)]")
        print(f"    • ProSparse (FATReLU) : Cosinus={cos_ps:.4f} | Amplitude conservée = {ratio_norm_ps*100:5.1f}%")
        print(f"    • Tower-7B  (SwiGLU)  : Cosinus={cos_tw:.4f} | Amplitude conservée = {ratio_norm_tw*100:5.1f}%")
        print(f"    • Neurones identiques allumés dans les deux modèles : {overlap}/{K} ({overlap/K*100:.1f}%)")

if __name__ == "__main__":
    main()
