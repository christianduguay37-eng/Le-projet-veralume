import glob, json, os, sys
import numpy as np

sys.path.append("Atelier_ARC_Prize")
from palier_20_darwin import CANONICAL_BENCHMARK_TASKS

canonical_set = set(CANONICAL_BENCHMARK_TASKS)
all_files = sorted(glob.glob("Atelier_ARC_Prize/training/*.json"))

unsolved = []
for fpath in all_files:
    tid = os.path.splitext(os.path.basename(fpath))[0]
    if tid in canonical_set:
        continue
    with open(fpath) as f:
        d = json.load(f)
    trains = d["train"]
    tests = d["test"]
    in0 = np.array(trains[0]["input"])
    out0 = np.array(trains[0]["output"])
    
    same_shape = all(np.array(t["input"]).shape == np.array(t["output"]).shape for t in trains)
    constant_out_shape = all(np.array(t["output"]).shape == out0.shape for t in trains)
    
    unsolved.append({
        "tid": tid,
        "n_train": len(trains),
        "n_test": len(tests),
        "same_shape": same_shape,
        "in0_shape": in0.shape,
        "out0_shape": out0.shape,
        "constant_out_shape": constant_out_shape,
        "in0_colors": len(np.unique(in0)),
        "out0_colors": len(np.unique(out0)),
    })

print(f"Total remaining unsolved tasks: {len(unsolved)}")

# Filter promising small tasks
# 1. Same shape <= 15
same_small = [u for u in unsolved if u["same_shape"] and max(u["in0_shape"]) <= 12 and u["in0_colors"] <= 4]
print(f"\n--- Same Shape (<=12, <=4 colors): {len(same_small)} tasks ---")
for u in same_small[:15]:
    print(f"  {u['tid']}: shape {u['in0_shape']}, train={u['n_train']}, in_cols={u['in0_colors']}, out_cols={u['out0_colors']}")

# 2. Output is small (<= 5x5) and constant
small_out = [u for u in unsolved if u["constant_out_shape"] and max(u["out0_shape"]) <= 5 and not u["same_shape"]]
print(f"\n--- Small constant output (<= 5x5): {len(small_out)} tasks ---")
for u in small_out[:15]:
    print(f"  {u['tid']}: in {u['in0_shape']} -> out {u['out0_shape']}, train={u['n_train']}")
