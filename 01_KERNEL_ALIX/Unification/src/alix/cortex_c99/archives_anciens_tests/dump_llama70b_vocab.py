import gguf
import struct
from pathlib import Path

gguf_path = Path(r"E:\Modeles_4e_Etage\Llama-3.3-70B-Instruct-Q4_K_M.gguf")
out_bin = Path(r"C:\Users\Christian\Documents\Cerveau Alix\_Unification_Alix\src\alix\cortex_c99\llama3_vocab.bin")

print(f"Extraction du vocabulaire depuis {gguf_path}...")
reader = gguf.GGUFReader(str(gguf_path))

f_tokens = reader.fields['tokenizer.ggml.tokens']
num_tokens = len(f_tokens.data)
print(f"Nombre de tokens : {num_tokens}")

# Format binaire simple pour C99 :
# Header:
#   uint32_t magic = 0x564F4333 ('VOC3')
#   uint32_t num_tokens
# Table:
#   uint32_t offset[num_tokens] (offset relatif au début du blob texte)
#   uint16_t length[num_tokens]
# Blob texte:
#   bytes concaténés

token_bytes_list = []
total_bytes = 0
offsets = []
lens = []

for idx in f_tokens.data:
    b = bytes(f_tokens.parts[idx])
    offsets.append(total_bytes)
    lens.append(len(b))
    total_bytes += len(b)
    token_bytes_list.append(b)

with open(out_bin, "wb") as f:
    f.write(struct.pack("<II", 0x564F4333, num_tokens))
    for off in offsets:
        f.write(struct.pack("<I", off))
    for l in lens:
        f.write(struct.pack("<H", l))
    for b in token_bytes_list:
        f.write(b)

print(f"Vocabulaire extrait avec succès dans {out_bin} ({out_bin.stat().st_size / (1024*1024):.2f} Mo) !")
