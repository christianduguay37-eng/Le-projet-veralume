import os, sys
sys.path.append("Atelier_ARC_Prize")
from thot_arc_core import ArcTask
from thot_ksil_multiverse import ThotMultiverseSolver

solver = ThotMultiverseSolver()
tasks = [
    '5bd6f4ac', 'a87f7484', '6773b310', '94f9d214',
    '496994bd', '6c434453', '29623171', '5c0a986e', '444801d8'
]
for tid in tasks:
    task = ArcTask.load_from_file(f'Atelier_ARC_Prize/training/{tid}.json')
    res = solver.solve(task)
    solved = res['solved']
    tpass = res['test_pass']
    rule = res['rule']
    dt = res['dt_ms']
    print(f"Tache {tid}: solved={solved}, test_pass={tpass}, rule={rule}, time={dt:.2f}ms")
