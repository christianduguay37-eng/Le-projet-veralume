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

for tid in ['6e19193c', '94f9d214', '6773b310', 'a68b268e']:
    inspect_task(tid)
