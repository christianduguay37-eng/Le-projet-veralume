import json, os, sys
import numpy as np

def inspect_task(tid):
    p = f"Atelier_ARC_Prize/training/{tid}.json"
    if not os.path.exists(p):
        print(f"Tâche {tid} introuvable")
        return
    with open(p, "r") as f:
        d = json.load(f)
    print(f"\n=================== TÂCHE {tid} ===================")
    print(f"Nb train: {len(d['train'])}, nb test: {len(d['test'])}")
    for i, ex in enumerate(d['train']):
        inp = np.array(ex['input'])
        out = np.array(ex['output'])
        diff = np.where(inp != out)
        print(f"--- Train {i}: in {inp.shape} -> out {out.shape} ---")
        print(f"  in colors: {np.unique(inp)}, out colors: {np.unique(out)}, diff count: {len(diff[0])}")
        if inp.shape == out.shape and max(inp.shape) <= 15:
            print("  Input:\n", inp)
            print("  Output:\n", out)
        elif out.shape[0] <= 6 and out.shape[1] <= 6:
            print("  Output:\n", out)

for tid in ['0e206a2e', '264363fd', '3618c87e', '36f4146c', '3906de3d']:
    inspect_task(tid)
