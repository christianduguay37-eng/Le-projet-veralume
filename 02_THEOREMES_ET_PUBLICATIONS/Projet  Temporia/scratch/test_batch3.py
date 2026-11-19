import os, sys
sys.path.append("Atelier_ARC_Prize")
from thot_arc_core import ArcTask
from thot_ksil_multiverse import ThotMultiverseSolver

solver = ThotMultiverseSolver()
tasks = ['3618c87e', '3906de3d', '4258a5f9', '3aa6fb7a', 'aedd82e4', '67385a82']
for tid in tasks:
    task = ArcTask.load_from_file(f'Atelier_ARC_Prize/training/{tid}.json')
    res = solver.solve(task)
    solved = res['solved']
    tpass = res['test_pass']
    rule = res['rule']
    dt = res['dt_ms']
    print(f"Tache {tid}: solved={solved}, test_pass={tpass}, rule={rule}, time={dt:.2f}ms")
