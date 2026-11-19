import json
import numpy as np

def test_5582e5ca():
    with open('Atelier_ARC_Prize/training/5582e5ca.json') as f:
        d = json.load(f)
    def solve(inp):
        vals, counts = np.unique(inp, return_counts=True)
        mode_col = vals[np.argmax(counts)]
        return np.full_like(inp, mode_col)
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"5582e5ca: train={train_ok}, test={test_ok}")

def test_3ac3eb23():
    with open('Atelier_ARC_Prize/training/3ac3eb23.json') as f:
        d = json.load(f)
    def solve(inp):
        out = np.zeros_like(inp)
        H, W = inp.shape
        markers = [(c, inp[0, c]) for c in range(W) if inp[0, c] != 0]
        for r in range(H):
            for c, col in markers:
                if r % 2 == 0:
                    out[r, c] = col
                else:
                    if c - 1 >= 0:
                        out[r, c - 1] = col
                    if c + 1 < W:
                        out[r, c + 1] = col
        return out
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"3ac3eb23: train={train_ok}, test={test_ok}")

def test_54d82841():
    with open('Atelier_ARC_Prize/training/54d82841.json') as f:
        d = json.load(f)
    def solve(inp):
        out = np.copy(inp)
        H, W = inp.shape
        # Detect arch pattern: 2x3 window with [[K, K, K], [K, 0, K]]
        for r in range(H - 1):
            for c in range(W - 2):
                sub = inp[r:r+2, c:c+3]
                k = sub[0, 0]
                if k != 0:
                    if (sub[0, 1] == k and sub[0, 2] == k and
                        sub[1, 0] == k and sub[1, 1] == 0 and sub[1, 2] == k):
                        out[H - 1, c + 1] = 4
        return out
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"54d82841: train={train_ok}, test={test_ok}")

def test_67a423a3():
    with open('Atelier_ARC_Prize/training/67a423a3.json') as f:
        d = json.load(f)
    def solve(inp):
        out = np.copy(inp)
        H, W = inp.shape
        # Find horizontal line (a row with all or nearly all same non-zero)
        # Find vertical line (a col with all or nearly all same non-zero)
        row_cand = None
        for r in range(H):
            vals = set(inp[r, :]) - {0}
            if len(vals) >= 1:
                # Count non-zeros
                if np.sum(inp[r, :] != 0) >= W - 1:
                    row_cand = r
        col_cand = None
        for c in range(W):
            vals = set(inp[:, c]) - {0}
            if len(vals) >= 1:
                if np.sum(inp[:, c] != 0) >= H - 1:
                    col_cand = c
        if row_cand is None or col_cand is None:
            return None
        r_c, c_c = row_cand, col_cand
        center_val = inp[r_c, c_c]
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r_c + dr, c_c + dc
                if 0 <= nr < H and 0 <= nc < W:
                    out[nr, nc] = 4
        out[r_c, c_c] = center_val
        return out
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"67a423a3: train={train_ok}, test={test_ok}")

def test_44f52bb0():
    with open('Atelier_ARC_Prize/training/44f52bb0.json') as f:
        d = json.load(f)
    def solve(inp):
        is_sym = np.array_equal(inp, np.fliplr(inp))
        val = 1 if is_sym else 7
        return np.array([[val]], dtype=inp.dtype)
    train_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['train'])
    test_ok = all(np.array_equal(solve(np.array(t['input'])), np.array(t['output'])) for t in d['test'])
    print(f"44f52bb0: train={train_ok}, test={test_ok}")

test_5582e5ca()
test_3ac3eb23()
test_54d82841()
test_67a423a3()
test_44f52bb0()
