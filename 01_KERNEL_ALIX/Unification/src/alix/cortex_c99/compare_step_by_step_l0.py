# -*- coding: utf-8 -*-
"""
Comparaison étape par étape sur la Couche 0 entre :
- Le modèle de référence Python (ProSparse-7B) qui répond juste
- Notre lecture GGUF (TowerInstruct-7B)
Pour identifier la dernière divergence mathématique (ex: transposition ffn_down ? output.weight ? attn_v ?) !
"""
import json
import struct
from pathlib import Path
import numpy as np
import gguf

GGUF_PATH = Path(r"C:\Users\Christian\.ollama\models\blobs\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce")
PROSPARSE_DIR = Path(r"C:\Users\Christian\Desktop\Projet alix\Mes_Projets_Veralume\sonde\prosparse-llama-2-7b")

from test_revelation_q4k_rope import dequant_q4k_ggml_exact

def dequant_q6k_ggml_exact(raw_bytes, n_blocks):
    out = np.zeros(n_blocks * 256, dtype=np.float32)
    for sb in range(n_blocks):
        b = raw_bytes[sb * 210 : (sb + 1) * 210]
        ql = np.frombuffer(b[0:128], dtype=np.uint8)
        qh = np.frombuffer(b[128:192], dtype=np.uint8)
        sc = np.frombuffer(b[192:208], dtype=np.int8).astype(np.float32)
        d = np.frombuffer(b[208:210], dtype=np.float16)[0].astype(np.float32)
        for n in range(2):
            ql_n = ql[n * 64 : (n + 1) * 64]
            qh_n = qh[n * 32 : (n + 1) * 32]
            sc_n = sc[n * 8 : (n + 1) * 8]
            for l in range(32):
                is_idx = l // 16
                q1 = int((ql_n[l + 0] & 0xF) | (((qh_n[l] >> 0) & 3) << 4)) - 32
                q2 = int((ql_n[l + 32] & 0xF) | (((qh_n[l] >> 2) & 3) << 4)) - 32
                q3 = int((ql_n[l + 0] >> 4) | (((qh_n[l] >> 4) & 3) << 4)) - 32
                q4 = int((ql_n[l + 32] >> 4) | (((qh_n[l] >> 6) & 3) << 4)) - 32
                base = sb * 256 + n * 128
                out[base + l + 0]  = d * sc_n[is_idx + 0] * q1
                out[base + l + 32] = d * sc_n[is_idx + 2] * q2
                out[base + l + 64] = d * sc_n[is_idx + 4] * q3
                out[base + l + 96] = d * sc_n[is_idx + 6] * q4
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

    def load_ps_row(key, row_idx):
        f, off, sh, dt = ou[key]
        mm = np.memmap(f, dtype=np.float32 if dt == "F32" else np.uint16, mode="r", offset=off, shape=tuple(sh))
        r = mm[row_idx]
        return np.array(r, dtype=np.float32) if dt == "F32" else (np.array(r, dtype=np.uint32) << 16).view(np.float32)

    reader = gguf.GGUFReader(str(GGUF_PATH))
    tensors = {t.name: t for t in reader.tensors}

    # Vérifier TOUS les tenseurs d'une couche (attn_k, attn_v, attn_output, ffn_gate, ffn_up, ffn_down, output.weight)
    checks = [
        ("blk.0.attn_k.weight", "model.layers.0.self_attn.k_proj.weight", 0, 16, "Q4_K"),
        ("blk.0.attn_v.weight", "model.layers.0.self_attn.v_proj.weight", 0, 16, "Q6_K"),
        ("blk.0.attn_output.weight", "model.layers.0.self_attn.o_proj.weight", 0, 16, "Q4_K"),
        ("blk.0.ffn_gate.weight", "model.layers.0.mlp.gate_proj.weight", 0, 16, "Q4_K"),
        ("blk.0.ffn_up.weight", "model.layers.0.mlp.up_proj.weight", 0, 16, "Q4_K"),
        ("blk.0.ffn_down.weight", "model.layers.0.mlp.down_proj.weight", 0, 43, "Q6_K"),
        ("output.weight", "lm_head.weight", 1000, 16, "Q6_K"),
    ]

    print("=" * 78)
    print("  AUDIT TENSEUR PAR TENSEUR : PROSPARSE-7B vs TOWERINSTRUCT-7B (GGUF)")
    print("=" * 78)
    for gguf_name, ps_name, row_i, n_blk, qtype in checks:
        ps_row = load_ps_row(ps_name, row_i)
        t_gguf = tensors[gguf_name]
        raw = bytes(t_gguf.data[row_i])
        if qtype == "Q4_K":
            gg_row = dequant_q4k_ggml_exact(raw, n_blk)
        else:
            gg_row = dequant_q6k_ggml_exact(raw, n_blk)
        cos = float(np.dot(ps_row, gg_row) / (np.linalg.norm(ps_row) * np.linalg.norm(gg_row)))
        print(f"  {gguf_name:24s} ({qtype}) | shape={str(t_gguf.shape):16s} | Cosinus = {cos:.6f}")

if __name__ == "__main__":
    main()
