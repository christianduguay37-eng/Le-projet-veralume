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
        elif max(out.shape) <= 4:
            print("  OUT:\n", out)

for tid in ['445eab21', '48d8fb45', '5614dbcf', '662c240a', '681b3aeb']:
    inspect_task(tid)
