import gguf
from pathlib import Path

p = Path(r"E:\Modeles_4e_Etage\Llama-3.3-70B-Instruct-Q4_K_M.gguf")
reader = gguf.GGUFReader(str(p))

tensors = {t.name: t for t in reader.tensors}

h_code = [
    "/* ============================================================================",
    " *   🏛️⚡ ALIX CORTEX C99 — OFFSETS COMPLETS DU TITAN LLAMA-3.3-70B",
    " *   Modèle : Llama-3.3-70B-Instruct-Q4_K_M.gguf (39.60 Go)",
    " * ============================================================================ */",
    "#ifndef ALIX_LLAMA70B_FULL_OFFSETS_H",
    "#define ALIX_LLAMA70B_FULL_OFFSETS_H",
    "#include <stdint.h>",
    "",
    "/* Tenseurs globaux d'entrée/sortie */",
    f"#define LLAMA70B_TOKEN_EMBD_OFFSET   {tensors['token_embd.weight'].data_offset}ULL",
    f"#define LLAMA70B_OUTPUT_NORM_OFFSET  {tensors['output_norm.weight'].data_offset}ULL",
    f"#define LLAMA70B_OUTPUT_OFFSET       {tensors['output.weight'].data_offset}ULL",
    f"#define LLAMA70B_TOKEN_EMBD_TYPE     {int(tensors['token_embd.weight'].tensor_type)}",
    f"#define LLAMA70B_OUTPUT_TYPE         {int(tensors['output.weight'].tensor_type)}",
    "",
    "typedef struct {",
    "    uint64_t attn_norm_off;",
    "    uint64_t attn_q_off;",
    "    uint64_t attn_k_off;",
    "    uint64_t attn_v_off;",
    "    uint64_t attn_output_off;",
    "    uint64_t ffn_norm_off;",
    "    uint64_t ffn_gate_off;",
    "    uint64_t ffn_up_off;",
    "    uint64_t ffn_down_off;",
    "    int      attn_v_type;",
    "    int      ffn_down_type;",
    "} alix_llama70b_full_layer_offsets_t;",
    "",
    "static const alix_llama70b_full_layer_offsets_t LLAMA70B_FULL_OFFSETS[80] = {"
]

for l in range(80):
    an = f"blk.{l}.attn_norm.weight"
    aq = f"blk.{l}.attn_q.weight"
    ak = f"blk.{l}.attn_k.weight"
    av = f"blk.{l}.attn_v.weight"
    ao = f"blk.{l}.attn_output.weight"
    fn = f"blk.{l}.ffn_norm.weight"
    fg = f"blk.{l}.ffn_gate.weight"
    fu = f"blk.{l}.ffn_up.weight"
    fd = f"blk.{l}.ffn_down.weight"

    ano = tensors[an].data_offset if an in tensors else 0
    aqo = tensors[aq].data_offset if aq in tensors else 0
    ako = tensors[ak].data_offset if ak in tensors else 0
    avo = tensors[av].data_offset if av in tensors else 0
    aoo = tensors[ao].data_offset if ao in tensors else 0
    fno = tensors[fn].data_offset if fn in tensors else 0
    fgo = tensors[fg].data_offset if fg in tensors else 0
    fuo = tensors[fu].data_offset if fu in tensors else 0
    fdo = tensors[fd].data_offset if fd in tensors else 0
    avt = int(tensors[av].tensor_type) if av in tensors else 0
    fdt = int(tensors[fd].tensor_type) if fd in tensors else 0

    h_code.append(f"    {{ {ano}ULL, {aqo}ULL, {ako}ULL, {avo}ULL, {aoo}ULL, {fno}ULL, {fgo}ULL, {fuo}ULL, {fdo}ULL, {avt}, {fdt} }}, /* L{l:02d} */")

h_code.append("};")
h_code.append("#endif")

out_h = Path(r"C:\Users\Christian\Documents\Cerveau Alix\_Unification_Alix\src\alix\cortex_c99\alix_llama70b_full_offsets.h")
out_h.write_text("\n".join(h_code), encoding="utf-8")
print(f"Header complet généré : {out_h} ({out_h.stat().st_size} octets)")
