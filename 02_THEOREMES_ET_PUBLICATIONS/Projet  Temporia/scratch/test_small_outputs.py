import json
import numpy as np
from scipy.ndimage import label

def test_445eab21():
    with open('Atelier_ARC_Prize/training/445eab21.json') as f:
        d = json.load(f)
    def solve(inp):
        # Find non-zero colors, pick the one with the maximum count
        vals, counts = np.unique(inp[inp != 0], return_counts=True)
        max_col = vals[np.argmax(counts)]
        return np.full((2, 2), max_col, dtype=inp.dtype)
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"445eab21: train={train_ok}, test={test_ok}")

def test_48d8fb45():
    with open('Atelier_ARC_Prize/training/48d8fb45.json') as f:
        d = json.load(f)
    def solve(inp):
        # Find marker 5
        m_pts = np.argwhere(inp == 5)
        if len(m_pts) == 0:
            return None
        mr, mc = m_pts[0]
        # Find non-zero, non-5 color
        colors = [c for c in np.unique(inp) if c != 0 and c != 5]
        if not colors:
            return None
        target_color = colors[0]
        
        # 8-connected or 4-connected components of target_color
        # Find which component is closest or adjacent to marker (mr, mc)
        lbl, num = label(inp == target_color, structure=np.ones((3, 3)))
        best_cid = None
        min_dist = 999
        for cid in range(1, num + 1):
            pts = np.argwhere(lbl == cid)
            # Distance from marker to component
            dist = np.min(np.abs(pts[:, 0] - mr) + np.abs(pts[:, 1] - mc))
            if dist < min_dist:
                min_dist = dist
                best_cid = cid
        pts = np.argwhere(lbl == best_cid)
        rmin, cmin = pts.min(axis=0)
        rmax, cmax = pts.max(axis=0)
        # Bounding box cropped to 3x3 if needed
        crop = inp[rmin:rmax+1, cmin:cmax+1]
        if crop.shape != (3, 3):
            # Pad or adjust to 3x3
            pass
        return crop
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"48d8fb45: train={train_ok}, test={test_ok}")

def test_5614dbcf():
    with open('Atelier_ARC_Prize/training/5614dbcf.json') as f:
        d = json.load(f)
    def solve(inp):
        out = np.zeros((3, 3), dtype=inp.dtype)
        for br in range(3):
            for bc in range(3):
                sub = inp[br*3:(br+1)*3, bc*3:(bc+1)*3]
                # Non-zero, non-5 colors
                cols = [c for c in sub.flatten() if c != 0 and c != 5]
                if cols:
                    # Most frequent color among non-5
                    vals, counts = np.unique(cols, return_counts=True)
                    out[br, bc] = vals[np.argmax(counts)]
        return out
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"5614dbcf: train={train_ok}, test={test_ok}")

test_445eab21()
test_48d8fb45()
test_5614dbcf()
