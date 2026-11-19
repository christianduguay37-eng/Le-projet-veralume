# -*- coding: utf-8 -*-
import gguf
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.decoders import ByteLevel as ByteLevelDecoder

r = gguf.GGUFReader(r'E:\Modeles_4e_Etage\Llama-3.3-70B-Instruct-Q4_K_M.gguf')
f_tokens = r.fields['tokenizer.ggml.tokens']
vocab = {bytes(f_tokens.parts[f_tokens.data[i]]).decode('latin-1'): i for i in range(len(f_tokens.data))}

f_merges = r.fields['tokenizer.ggml.merges']
merges = []
for i in range(len(f_merges.data)):
    m_bytes = bytes(f_merges.parts[f_merges.data[i]])
    parts = m_bytes.decode('latin-1').split(' ')
    if len(parts) == 2:
        merges.append((parts[0], parts[1]))

tokenizer = Tokenizer(BPE(vocab, merges))
tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=False)
tokenizer.decoder = ByteLevelDecoder()

questions = [
    ("GEO_FR",  "La capitale de la France est :"),
    ("GEO_JAP", "La capitale du Japon est :"),
    ("BIOCHIM", "L'enzyme qui degrade l'amidon est :"),
    ("MATHS",   "Le resultat de sept fois huit est :"),
    ("INFO_C",  "En langage C le pointeur NULL est :")
]

for name, q in questions:
    enc = tokenizer.encode(q)
    print(f"{name} ({len(enc.ids)} tokens):")
    print(f"  IDs: {enc.ids}")
    print(f"  Tokens: {enc.tokens}\n")
