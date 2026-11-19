import os, sys
sys.path.append("Atelier_ARC_Prize")
from thot_arc_core import ArcTask
from thot_ksil_multiverse import ThotMultiverseSolver

solver = ThotMultiverseSolver()
tasks = [
    '5582e5ca', '3ac3eb23', '54d82841', '67a423a3', '44f52bb0',
    '44d8ac46', '445eab21', '48d8fb45', '5614dbcf', '681b3aeb'
]
for tid in tasks:
    task = ArcTask.load_from_file(f'Atelier_ARC_Prize/training/{tid}.json')
    res = solver.solve(task)
    solved = res['solved']
    tpass = res['test_pass']
    rule = res['rule']
    dt = res['dt_ms']
    print(f"Tache {tid}: solved={solved}, test_pass={tpass}, rule={rule}, time={dt:.2f}ms")
