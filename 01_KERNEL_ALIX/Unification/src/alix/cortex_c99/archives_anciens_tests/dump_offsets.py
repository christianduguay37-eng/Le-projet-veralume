import gguf
import json
from pathlib import Path

p = Path(r"C:\Users\Christian\.ollama\models\blobs\sha256-07264f5b41a074562c3fd8bff0e1b7f60ecb4f3441ed5410db35529ee7a207ce")
reader = gguf.GGUFReader(str(p))

couches = []
tensors = {t.name: t for t in reader.tensors}

for l in range(32):
    fn = f"blk.{l}.ffn_norm.weight"
    fg = f"blk.{l}.ffn_gate.weight"
    fu = f"blk.{l}.ffn_up.weight"
    fd = f"blk.{l}.ffn_down.weight"
    
    couches.append({
        "couche": l,
        "norm_offset": tensors[fn].data_offset if fn in tensors else 0,
        "gate_offset": tensors[fg].data_offset if fg in tensors else 0,
        "up_offset": tensors[fu].data_offset if fu in tensors else 0,
        "down_offset": tensors[fd].data_offset if fd in tensors else 0,
    })

print(f"Extraction des 32 couches terminée : {len(couches)} couches indexées.")
print(f"Exemple L0 : gate={couches[0]['gate_offset']}, up={couches[0]['up_offset']}")
print(f"Exemple L31: gate={couches[31]['gate_offset']}, up={couches[31]['up_offset']}")

# Écrire un fichier header C99 avec les offsets précalculés
h_code = ["/* Offsets précalculés des 32 couches de TowerInstruct-7B (GGUF Q4_K) */",
          "#ifndef ALIX_TOWER7B_OFFSETS_H",
          "#define ALIX_TOWER7B_OFFSETS_H",
          "#include <stdint.h>",
          "",
          "typedef struct {",
          "    uint64_t norm_off;",
          "    uint64_t gate_off;",
          "    uint64_t up_off;",
          "    uint64_t down_off;",
          "} alix_layer_offsets_t;",
          "",
          "static const alix_layer_offsets_t TOWER7B_OFFSETS[32] = {"]

for c in couches:
    h_code.append(f"    {{ {c['norm_offset']}ULL, {c['gate_offset']}ULL, {c['up_offset']}ULL, {c['down_offset']}ULL }}, /* Couche {c['couche']} */")

h_code.append("};")
h_code.append("#endif")

out_h = Path(r"C:\Users\Christian\Documents\Cerveau Alix\_Unification_Alix\src\alix\cortex_c99\alix_tower7b_offsets.h")
out_h.write_text("\n".join(h_code), encoding="utf-8")
print(f"Header C99 généré : {out_h}")
