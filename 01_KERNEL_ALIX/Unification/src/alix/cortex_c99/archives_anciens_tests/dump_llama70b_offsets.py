import gguf
from pathlib import Path

p = Path(r"E:\Modeles_4e_Etage\Llama-3.3-70B-Instruct-Q4_K_M.gguf")
reader = gguf.GGUFReader(str(p))

tensors = {t.name: t for t in reader.tensors}

h_code = [
    "/* Offsets précalculés des 80 couches de Llama-3.3-70B-Instruct (GGUF Q4_K sur clé USB E:) */",
    "#ifndef ALIX_LLAMA70B_OFFSETS_H",
    "#define ALIX_LLAMA70B_OFFSETS_H",
    "#include <stdint.h>",
    "",
    "typedef struct {",
    "    uint64_t norm_off;",
    "    uint64_t gate_off;",
    "    uint64_t up_off;",
    "    uint64_t down_off;",
    "} alix_llama70b_layer_offsets_t;",
    "",
    "static const alix_llama70b_layer_offsets_t LLAMA70B_OFFSETS[80] = {"
]

for l in range(80):
    fn = f"blk.{l}.ffn_norm.weight"
    fg = f"blk.{l}.ffn_gate.weight"
    fu = f"blk.{l}.ffn_up.weight"
    fd = f"blk.{l}.ffn_down.weight"

    no = tensors[fn].data_offset if fn in tensors else 0
    go = tensors[fg].data_offset if fg in tensors else 0
    uo = tensors[fu].data_offset if fu in tensors else 0
    do = tensors[fd].data_offset if fd in tensors else 0

    h_code.append(f"    {{ {no}ULL, {go}ULL, {uo}ULL, {do}ULL }}, /* Couche {l:02d} */")

h_code.append("};")
h_code.append("#endif")

out_h = Path(r"C:\Users\Christian\Documents\Cerveau Alix\_Unification_Alix\src\alix\cortex_c99\alix_llama70b_offsets.h")
out_h.write_text("\n".join(h_code), encoding="utf-8")
print(f"Header des 80 couches généré avec succès : {out_h}")
print(f"Couche 0  : gate={tensors['blk.0.ffn_gate.weight'].data_offset}")
print(f"Couche 79 : gate={tensors['blk.79.ffn_gate.weight'].data_offset}")
