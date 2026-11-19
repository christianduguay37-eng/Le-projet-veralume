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
        print(f"--- Train {i}: in {inp.shape} ---")
        print("  IN:\n", inp)
        print("  OUT:\n", out)

for tid in ['3aa6fb7a', '4258a5f9', '67385a82', '7447852a', 'aedd82e4']:
    inspect_task(tid)
