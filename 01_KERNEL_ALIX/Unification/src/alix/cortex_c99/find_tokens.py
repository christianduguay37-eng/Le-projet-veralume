# -*- coding: utf-8 -*-
import gguf

r = gguf.GGUFReader(r"E:\Modeles_4e_Etage\Llama-3.3-70B-Instruct-Q4_K_M.gguf")
f = r.fields['tokenizer.ggml.tokens']
m = {bytes(f.parts[f.data[i]]): i for i in range(len(f.data))}

test_words = [
    b"Paris", b"\xc4\xa0est", b"\xc4\xa0la", b"\xc4\xa0capitale", b"\xc4\xa0de", b"\xc4\xa0la", b"\xc4\xa0France",
    b"Le", b"\xc4\xa0ciel", b"\xc4\xa0est", b"\xc4\xa0bleu",
    b"La", b"\xc4\xa0Terre", b"\xc4\xa0est", b"\xc4\xa0ronde",
    b"Quelle", b"\xc4\xa0couleur", b"\xc4\xa0du"
]

res = []
for w in test_words:
    tid = m.get(w)
    res.append((w, tid))
    print(f"{w} -> {tid}")
