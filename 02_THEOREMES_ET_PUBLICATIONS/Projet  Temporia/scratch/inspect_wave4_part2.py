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
        print(f"--- Train {i}: in {inp.shape} -> out {out.shape} ---")
        if max(inp.shape) <= 12 and max(out.shape) <= 6:
            print("  IN:\n", inp)
            print("  OUT:\n", out)
        elif max(out.shape) <= 3:
            print("  OUT:\n", out)
        elif inp.shape == out.shape and max(inp.shape) <= 10:
            diff = np.where(inp != out)
            print("  diff count:", len(diff[0]))

for tid in ['760b3cac', '7ddcd7ec', '39a8645d', '5117e062', 'cdecee7f']:
    inspect_task(tid)
