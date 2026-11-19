# -*- coding: utf-8 -*-
"""
Vérification de la passe avant (Forward Pass) de la Couche 0 :
ProSparse-7B (Safetensors) vs TowerInstruct-7B (GGUF déquantifié).
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

def main():
    reader = gguf.GGUFReader(str(GGUF_PATH))
    tensors = {t.name: t for t in reader.tensors}
    for k in ["token_embd.weight", "blk.0.attn_q.weight", "blk.0.ffn_gate.weight", "blk.0.ffn_down.weight", "output.weight"]:
        t = tensors[k]
        print(f"Tensor {k:24s} : gguf shape={t.shape}, data.shape={t.data.shape}, data.nbytes={t.data.nbytes}")

if __name__ == "__main__":
    main()
