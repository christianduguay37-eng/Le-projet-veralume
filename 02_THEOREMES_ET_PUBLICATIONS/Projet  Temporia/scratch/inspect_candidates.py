import json, os
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
        print(f"--- Train {i}: in {inp.shape} -> out {out.shape} ---")
        print(f"  in colors: {np.unique(inp)}, out colors: {np.unique(out)}")
        if inp.shape == out.shape and max(inp.shape) <= 12:
            print("  Input:\n", inp)
            print("  Output:\n", out)
        elif out.shape[0] <= 6 and out.shape[1] <= 6:
            print("  Input:\n", inp)
            print("  Output:\n", out)

for tid in ['28e73c20', '2bee17df', '2c608aff', '31aa019c', '321b1fc6', '10fcaaa3', '234bbc79']:
    inspect_task(tid)
