import json, os
import numpy as np

def inspect_task(tid):
    p = f"Atelier_ARC_Prize/training/{tid}.json"
    with open(p) as f:
        d = json.load(f)
    print(f"\n=================== TÂCHE {tid} ===================")
    for i, ex in enumerate(d['train']):
        inp = np.array(ex['input'])
        out = np.array(ex['output'])
        diff = np.where(inp != out)
        print(f"--- Train {i}: in {inp.shape} -> out {out.shape}, diff count: {len(diff[0])} ---")
        if max(inp.shape) <= 11 and len(diff[0]) <= 20:
            print("  diff in vals:", inp[diff], "-> out vals:", out[diff])
            print("  IN:\n", inp)
            print("  OUT:\n", out)

for tid in ['29623171', '3befdf3e', '444801d8', '56ff96f3', '5c0a986e', '60b61512']:
    inspect_task(tid)
