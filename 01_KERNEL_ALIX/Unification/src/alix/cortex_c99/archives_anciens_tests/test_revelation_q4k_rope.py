# -*- coding: utf-8 -*-
"""
Vérification directe bit-à-bit de Q4_K et RoPE grâce au comparatif ProSparse-7B <-> TowerInstruct-7B !
"""
import json
import struct
from pathlib import Path
import numpy as np
import gguf

GGUF_PATH = Path(r"C:\Users\Christian\.ollama\models\blobs\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce")
PROSPARSE_DIR = Path(r"C:\Users\Christian\Desktop\Projet alix\Mes_Projets_Veralume\sonde\prosparse-llama-2-7b")

def dequant_q4k_ancien(raw_bytes, n_blocks=16):
    """Ancien décodage Q4_K (entrelacé i, i+1)"""
    out = np.zeros(n_blocks * 256, dtype=np.float32)
    for sb_idx in range(n_blocks):
        b = raw_bytes[sb_idx * 144 : (sb_idx + 1) * 144]
        d = np.frombuffer(b[0:2], dtype=np.float16)[0].astype(np.float32)
        dmin = np.frombuffer(b[2:4], dtype=np.float16)[0].astype(np.float32)
        scales = np.frombuffer(b[4:16], dtype=np.uint8)
        qs = np.frombuffer(b[16:144], dtype=np.uint8)
        sc = np.zeros(8, dtype=np.float32)
        m = np.zeros(8, dtype=np.float32)
        for j in range(4):
            sc[j] = scales[j] & 63
            m[j] = scales[j + 4] & 63
            sc[j + 4] = (scales[j + 8] & 15) | ((scales[j] >> 6) << 4)
            m[j + 4] = (scales[j + 8] >> 4) | ((scales[j + 4] >> 6) << 4)
        for sub in range(8):
            d_sub = d * sc[sub]
            m_sub = dmin * m[sub]
            q_chunk = qs[sub * 16 : (sub + 1) * 16]
            out[sb_idx * 256 + sub * 32 + 0 : sb_idx * 256 + (sub + 1) * 32 : 2] = d_sub * (q_chunk & 0x0F) - m_sub
            out[sb_idx * 256 + sub * 32 + 1 : sb_idx * 256 + (sub + 1) * 32 : 2] = d_sub * (q_chunk >> 4) - m_sub
    return out

def dequant_q4k_ggml_exact(raw_bytes, n_blocks=16):
    """Décodage Q4_K exact selon la spécification GGML (32 nibbles bas = bloc pair, 32 nibbles hauts = bloc impair)"""
    out = np.zeros(n_blocks * 256, dtype=np.float32)
    for sb_idx in range(n_blocks):
        b = raw_bytes[sb_idx * 144 : (sb_idx + 1) * 144]
        d = np.frombuffer(b[0:2], dtype=np.float16)[0].astype(np.float32)
        dmin = np.frombuffer(b[2:4], dtype=np.float16)[0].astype(np.float32)
        scales = np.frombuffer(b[4:16], dtype=np.uint8)
        qs = np.frombuffer(b[16:144], dtype=np.uint8)
        sc = np.zeros(8, dtype=np.float32)
        m = np.zeros(8, dtype=np.float32)
        for j in range(4):
            sc[j] = scales[j] & 63
            m[j] = scales[j + 4] & 63
            sc[j + 4] = (scales[j + 8] & 15) | ((scales[j] >> 6) << 4)
            m[j + 4] = (scales[j + 8] >> 4) | ((scales[j + 4] >> 6) << 4)
        for j in range(4):
            q_chunk = qs[j * 32 : (j + 1) * 32]
            # Sous-bloc pair (2*j) : 32 nibbles bas
            d1 = d * sc[2 * j]
            m1 = dmin * m[2 * j]
            out[sb_idx * 256 + j * 64 : sb_idx * 256 + j * 64 + 32] = d1 * (q_chunk & 0x0F) - m1
            # Sous-bloc impair (2*j + 1) : 32 nibbles hauts
            d2 = d * sc[2 * j + 1]
            m2 = dmin * m[2 * j + 1]
            out[sb_idx * 256 + j * 64 + 32 : sb_idx * 256 + (j + 1) * 64] = d2 * (q_chunk >> 4) - m2
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

    reader = gguf.GGUFReader(str(GGUF_PATH))
    tensors = {t.name: t for t in reader.tensors}

    # 1. Comparer token_embd (mot #1000) entre ProSparse et TowerInstruct-7B
    f_ps, off_ps, sh_ps, dt_ps = ou["model.embed_tokens.weight"]
    mm_ps = np.memmap(f_ps, dtype=np.float32 if dt_ps == "F32" else np.uint16, mode="r", offset=off_ps, shape=tuple(sh_ps))
    row_ps = np.array(mm_ps[1000], dtype=np.float32) if dt_ps == "F32" else (np.array(mm_ps[1000], dtype=np.uint32) << 16).view(np.float32)

    t_emb = tensors["token_embd.weight"]
    raw_row = bytes(t_emb.data[1000])

    row_ancien = dequant_q4k_ancien(raw_row, 16)
    row_exact = dequant_q4k_ggml_exact(raw_row, 16)

    cos_ancien = float(np.dot(row_ps, row_ancien) / (np.linalg.norm(row_ps) * np.linalg.norm(row_ancien)))
    cos_exact = float(np.dot(row_ps, row_exact) / (np.linalg.norm(row_ps) * np.linalg.norm(row_exact)))

    print("=" * 76)
    print("  RÉVÉLATION DU BANC COMPARATIF (PROSPARSE-7B vs TOWERINSTRUCT-7B)")
    print("=" * 76)
    print(f"  [Token Embedding #1000]")
    print(f"    • Avec ancien décodage Q4_K (entrelacé) : Cosinus = {cos_ancien:.6f}")
    print(f"    • Avec décodage Q4_K GGML exact (32/32) : Cosinus = {cos_exact:.6f}  <-- BINGO !")

    # 2. Comparer ffn_up.weight et ffn_gate.weight (Neurone #0 de la Couche 10)
    f_up, off_up, sh_up, dt_up = ou["model.layers.10.mlp.up_proj.weight"]
    mm_up = np.memmap(f_up, dtype=np.float32 if dt_up == "F32" else np.uint16, mode="r", offset=off_up, shape=tuple(sh_up))
    up_ps = np.array(mm_up[0], dtype=np.float32) if dt_up == "F32" else (np.array(mm_up[0], dtype=np.uint32) << 16).view(np.float32)

    t_up = tensors["blk.10.ffn_up.weight"]
    raw_up = bytes(t_up.data[0])
    up_ancien = dequant_q4k_ancien(raw_up, 16)
    up_exact = dequant_q4k_ggml_exact(raw_up, 16)

    cos_up_anc = float(np.dot(up_ps, up_ancien) / (np.linalg.norm(up_ps) * np.linalg.norm(up_ancien)))
    cos_up_ex = float(np.dot(up_ps, up_exact) / (np.linalg.norm(up_ps) * np.linalg.norm(up_exact)))
    print(f"\n  [Neurone MLP #0 Couche 10 (ffn_up)]")
    print(f"    • Avec ancien décodage Q4_K (entrelacé) : Cosinus = {cos_up_anc:.6f}")
    print(f"    • Avec décodage Q4_K GGML exact (32/32) : Cosinus = {cos_up_ex:.6f}  <-- MÊME NEURONE !")

    # 3. Vérifier l'ordre des dimensions de attn_q dans GGUF vs Safetensors (Permutation RoPE !)
    f_q, off_q, sh_q, dt_q = ou["model.layers.0.self_attn.q_proj.weight"]
    mm_q = np.memmap(f_q, dtype=np.float32 if dt_q == "F32" else np.uint16, mode="r", offset=off_q, shape=tuple(sh_q))
    q_ps_0 = np.array(mm_q[0], dtype=np.float32) if dt_q == "F32" else (np.array(mm_q[0], dtype=np.uint32) << 16).view(np.float32)
    q_ps_1 = np.array(mm_q[1], dtype=np.float32) if dt_q == "F32" else (np.array(mm_q[1], dtype=np.uint32) << 16).view(np.float32)
    q_ps_64 = np.array(mm_q[64], dtype=np.float32) if dt_q == "F32" else (np.array(mm_q[64], dtype=np.uint32) << 16).view(np.float32)

    t_q = tensors["blk.0.attn_q.weight"]
    q_gguf_0 = dequant_q4k_ggml_exact(bytes(t_q.data[0]), 16)
    q_gguf_1 = dequant_q4k_ggml_exact(bytes(t_q.data[1]), 16)
    q_gguf_2 = dequant_q4k_ggml_exact(bytes(t_q.data[2]), 16)

    print(f"\n  [Disposition RoPE dans GGUF attn_q (Tête 0, dim=128)]")
    print(f"    • GGUF ligne 0 vs Safetensors ligne 0  : Cosinus = {float(np.dot(q_gguf_0, q_ps_0)/(np.linalg.norm(q_gguf_0)*np.linalg.norm(q_ps_0))):.6f}")
    print(f"    • GGUF ligne 1 vs Safetensors ligne 1  : Cosinus = {float(np.dot(q_gguf_1, q_ps_1)/(np.linalg.norm(q_gguf_1)*np.linalg.norm(q_ps_1))):.6f}")
    print(f"    • GGUF ligne 1 vs Safetensors ligne 64 : Cosinus = {float(np.dot(q_gguf_1, q_ps_64)/(np.linalg.norm(q_gguf_1)*np.linalg.norm(q_ps_64))):.6f}")
    print(f"    • GGUF ligne 2 vs Safetensors ligne 1  : Cosinus = {float(np.dot(q_gguf_2, q_ps_1)/(np.linalg.norm(q_gguf_2)*np.linalg.norm(q_ps_1))):.6f}")

if __name__ == "__main__":
    main()
