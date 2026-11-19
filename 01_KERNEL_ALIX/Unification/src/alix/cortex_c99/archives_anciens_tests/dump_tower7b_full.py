# -*- coding: utf-8 -*-
import struct
from pathlib import Path
import gguf
import sentencepiece as spm

GGUF_PATH = Path(r"C:\Users\Christian\.ollama\models\blobs\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce")
PROSPARSE_DIR = Path(r"C:\Users\Christian\Desktop\Projet alix\Mes_Projets_Veralume\sonde\prosparse-llama-2-7b")
OUT_DIR = Path(r"C:\Users\Christian\Documents\Cerveau Alix\_Unification_Alix\src\alix\cortex_c99")

def main():
    reader = gguf.GGUFReader(str(GGUF_PATH))
    tensors = {t.name: t for t in reader.tensors}

    # 1. Vérifier les hyperparamètres GGUF
    for field_name in ["llama.embedding_length", "llama.feed_forward_length", "llama.block_count",
                       "llama.attention.head_count", "llama.attention.head_count_kv",
                       "llama.rope.freq_base", "llama.attention.layer_norm_rms_epsilon"]:
        f = reader.get_field(field_name)
        if f is not None:
            val = f.parts[f.data[0]][0] if len(f.data) > 0 else None
            print(f"  {field_name} = {val}")

    # 2. Extraire le vocabulaire de TowerInstruct-7B
    sp = spm.SentencePieceProcessor(model_file=str(PROSPARSE_DIR / "tokenizer.model"))
    tok_field = reader.get_field("tokenizer.ggml.tokens")
    tokens = []
    if tok_field is not None:
        for idx in tok_field.data:
            raw_bytes = bytes(tok_field.parts[idx])
            tokens.append(raw_bytes)
    print(f"  Nombre de tokens dans GGUF : {len(tokens)} (sp.vocab_size = {sp.vocab_size()})")

    # Vérifier la correspondance avec SentencePiece sur les 32000 premiers
    matches = 0
    for i in range(min(32000, len(tokens))):
        sp_piece = sp.id_to_piece(i).encode("utf-8")
        if tokens[i] == sp_piece:
            matches += 1
    print(f"  Correspondance exacte des tokens [0..31999] avec ProSparse : {matches}/32000")
    for i in range(32000, len(tokens)):
        print(f"  Token spécial #{i} : {tokens[i].decode('utf-8', errors='replace')}")

    # Sauvegarder tower7b_vocab.bin au format VOC3 pour C-Alix
    vocab_bin_path = OUT_DIR / "tower7b_vocab.bin"
    offsets = []
    lens = []
    blob = bytearray()
    for t_bytes in tokens:
        # Remplacer '▁' (0xE2 0x96 0x81) par un espace ' ' pour affichage direct propre
        s = t_bytes.decode("utf-8", errors="replace").replace("▁", " ")
        b = s.encode("utf-8")
        offsets.append(len(blob))
        lens.append(len(b))
        blob.extend(b)

    with open(vocab_bin_path, "wb") as f:
        f.write(struct.pack("<II", 0x564F4333, len(tokens)))
        f.write(struct.pack(f"<{len(tokens)}I", *offsets))
        f.write(struct.pack(f"<{len(tokens)}H", *lens))
        f.write(blob)
    print(f"  Vocabulaire binaire sauvegardé : {vocab_bin_path} ({vocab_bin_path.stat().st_size} octets)")

    # 3. Générer alix_tower7b_full_offsets.h avec tous les offsets et types
    h_lines = [
        "/* Offsets complets des 32 couches de TowerInstruct-7B-v0.2 (GGUF Q4_K_M) */",
        "#ifndef ALIX_TOWER7B_FULL_OFFSETS_H",
        "#define ALIX_TOWER7B_FULL_OFFSETS_H",
        "#include <stdint.h>",
        "",
        f"#define TOWER7B_TOKEN_EMBD_OFF  {tensors['token_embd.weight'].data_offset}ULL",
        f"#define TOWER7B_OUTPUT_NORM_OFF {tensors['output_norm.weight'].data_offset}ULL",
        f"#define TOWER7B_OUTPUT_OFF      {tensors['output.weight'].data_offset}ULL",
        f"#define TOWER7B_TOKEN_EMBD_TYPE {int(tensors['token_embd.weight'].tensor_type)}",
        f"#define TOWER7B_OUTPUT_TYPE     {int(tensors['output.weight'].tensor_type)}",
        "",
        "typedef struct {",
        "    uint64_t attn_norm_off;",
        "    uint64_t attn_q_off;",
        "    uint64_t attn_k_off;",
        "    uint64_t attn_v_off;",
        "    uint64_t attn_out_off;",
        "    uint64_t ffn_norm_off;",
        "    uint64_t ffn_gate_off;",
        "    uint64_t ffn_up_off;",
        "    uint64_t ffn_down_off;",
        "    int      attn_v_type;   /* 12 = Q4_K, 14 = Q6_K */",
        "    int      ffn_down_type; /* 12 = Q4_K, 14 = Q6_K */",
        "} alix_tower7b_layer_t;",
        "",
        "static const alix_tower7b_layer_t TOWER7B_LAYERS[32] = {"
    ]

    for l in range(32):
        an = tensors[f"blk.{l}.attn_norm.weight"]
        aq = tensors[f"blk.{l}.attn_q.weight"]
        ak = tensors[f"blk.{l}.attn_k.weight"]
        av = tensors[f"blk.{l}.attn_v.weight"]
        ao = tensors[f"blk.{l}.attn_output.weight"]
        fn = tensors[f"blk.{l}.ffn_norm.weight"]
        fg = tensors[f"blk.{l}.ffn_gate.weight"]
        fu = tensors[f"blk.{l}.ffn_up.weight"]
        fd = tensors[f"blk.{l}.ffn_down.weight"]
        h_lines.append(
            f"    {{ {an.data_offset}ULL, {aq.data_offset}ULL, {ak.data_offset}ULL, {av.data_offset}ULL, "
            f"{ao.data_offset}ULL, {fn.data_offset}ULL, {fg.data_offset}ULL, {fu.data_offset}ULL, "
            f"{fd.data_offset}ULL, {int(av.tensor_type)}, {int(fd.tensor_type)} }}, /* L{l:02d} */"
        )

    h_lines.append("};")
    h_lines.append("#endif")

    out_h = OUT_DIR / "alix_tower7b_full_offsets.h"
    out_h.write_text("\n".join(h_lines), encoding="utf-8")
    print(f"  Header complet généré : {out_h}")

if __name__ == "__main__":
    main()
