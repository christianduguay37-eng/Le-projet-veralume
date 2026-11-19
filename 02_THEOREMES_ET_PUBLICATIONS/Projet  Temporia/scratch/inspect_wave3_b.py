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
        if max(inp.shape) <= 14 and max(out.shape) <= 6:
            print("  IN:\n", inp)
            print("  OUT:\n", out)
        elif inp.shape == out.shape and max(inp.shape) <= 10:
            diff = np.where(inp != out)
            print("  diff count:", len(diff[0]))
            print("  IN:\n", inp)
            print("  OUT:\n", out)

for tid in ['75b8110e', '995c5fa3', '6e19193c', '496994bd', '6c434453']:
    inspect_task(tid)
