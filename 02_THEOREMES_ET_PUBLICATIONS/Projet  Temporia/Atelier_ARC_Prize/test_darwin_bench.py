import os
import glob
import time
from thot_arc_core import ArcTask
from thot_darwin_evolution import ThotDarwinEngine

def run_darwin_test(start_idx=25, count=50):
    files = sorted(glob.glob("training/*.json"))[start_idx:start_idx+count]
    print(f"🧬 TEST THOT DARWIN ENGINE sur {len(files)} puzzles de training (de {start_idx} à {start_idx+count})...")
    
    engine = ThotDarwinEngine(max_seconds_per_task=5.0, top_k_parents=10)
    
    solved_count = 0
    total_time = 0.0
    
    for idx, fpath in enumerate(files):
        task = ArcTask.load_from_file(fpath)
        t_start = time.perf_counter()
        res = engine.solve(task)
        dt = time.perf_counter() - t_start
        total_time += dt
        
        status = "✅ SOLVED" if res["solved"] else f"❌ Fit={res['fitness']:.2f}"
        print(f"[{idx+1:02d}/{len(files)}] {task.task_id} : {status} en {dt:.3f}s | Règle: {res['rule']}")
        if res["solved"]:
            solved_count += 1
            
    print("=" * 60)
    print(f"🏁 BILAN DARWIN : {solved_count}/{len(files)} résolus ({solved_count/len(files)*100:.1f}%)")
    print(f"⏱️ Temps total : {total_time:.2f}s (Moyenne : {total_time/len(files):.3f}s / task)")
    print("=" * 60)

if __name__ == "__main__":
    run_darwin_test()
