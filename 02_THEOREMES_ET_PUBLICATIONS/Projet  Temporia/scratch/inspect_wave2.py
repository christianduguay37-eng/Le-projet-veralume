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
        print("  IN:\n", inp)
        print("  OUT:\n", out)

for tid in ['5582e5ca', '44f52bb0', '44d8ac46', '54d82841', '3ac3eb23', '67a423a3']:
    inspect_task(tid)
