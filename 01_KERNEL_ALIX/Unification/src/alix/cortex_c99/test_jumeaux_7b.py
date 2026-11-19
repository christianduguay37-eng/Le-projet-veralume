# -*- coding: utf-8 -*-
"""
Banc Comparatif Jumeaux 7B : ProSparse-Llama-2-7B (Interrupteurs FATReLU) vs TowerInstruct-7B (Dense SwiGLU GGUF)
1. Vérifie si le neurone #i de ProSparse est physiquement le MÊME neurone #i dans TowerInstruct (cosinus des poids).
2. Compare sur une question les neurones qui s'allument dans ProSparse vs ceux qui portent l'énergie dans TowerInstruct.
"""
import json
import struct
from pathlib import Path
import numpy as np
import gguf
import sentencepiece as spm

GGUF_PATH = Path(r"C:\Users\Christian\.ollama\models\blobs\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce")
PROSPARSE_DIR = Path(r"C:\Users\Christian\Desktop\Projet alix\Mes_Projets_Veralume\sonde\prosparse-llama-2-7b")

def dequant_q4k_row(raw_bytes, n_blocks=16):
    # 16 super-blocs de 256 = 4096 floats (144 octets par bloc)
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
            q0 = q_chunk & 0x0F
            q1 = (q_chunk >> 4) & 0x0F
            # Attention: dans Q4_K ggml, les 32 valeurs d'un sous-bloc ou d'une paire de sous-blocs :
            # attendons, vérifions la disposition exacte de Q4_K ggml vs notre C!
            out[sb_idx * 256 + sub * 32 : sb_idx * 256 + sub * 32 + 16] = d_sub * q0 - m_sub
            out[sb_idx * 256 + sub * 32 + 16 : sb_idx * 256 + (sub + 1) * 32] = d_sub * q1 - m_sub
    return out

def main():
    # Charger index Safetensors de ProSparse
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

    # Comparer les poids de norm (F32 dans GGUF, F32/BF16 dans ProSparse) sur L0, L10, L20, L31
    print("=" * 72)
    print("  1. TEST D'IDENTITÉ GÉNÉTIQUE DES NEURONES (PROSPARSE vs TOWER-7B)")
    print("=" * 72)
    for l in [0, 10, 20, 31]:
        f_ps, off_ps, sh_ps, dt_ps = ou[f"model.layers.{l}.post_attention_layernorm.weight"]
        mm_ps = np.memmap(f_ps, dtype=np.float32 if dt_ps == "F32" else np.uint16, mode="r", offset=off_ps, shape=tuple(sh_ps))
        w_ps = np.array(mm_ps, dtype=np.float32) if dt_ps == "F32" else (np.array(mm_ps, dtype=np.uint32) << 16).view(np.float32)

        t_tw = tensors[f"blk.{l}.ffn_norm.weight"]
        w_tw = np.array(t_tw.data, dtype=np.float32)
        cos_norm = float(np.dot(w_ps, w_tw) / (np.linalg.norm(w_ps) * np.linalg.norm(w_tw)))
        print(f"  Couche L{l:02d} | Cosinus ffn_norm (4096 dim) : {cos_norm:.6f}")

if __name__ == "__main__":
    main()
