import numpy as np
from typing import Dict, Callable, List
from collections import Counter
from scipy.ndimage import label
import itertools

try:
    from alix.solveurs.arc.taches.test_10fcaaa3 import solve_10fcaaa3
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_10fcaaa3 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_150deff5 import solve_150deff5
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_150deff5 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_234bbc79 import solve_234bbc79
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_234bbc79 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_0e206a2e import solve_0e206a2e
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_0e206a2e = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_264363fd import solve_264363fd
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_264363fd = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_2dd70a9a import solve_2dd70a9a
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_2dd70a9a = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_3631a71a import solve_3631a71a
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_3631a71a = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_36d67576 import solve_36d67576
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_36d67576 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_36fdfd69 import solve_36fdfd69
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_36fdfd69 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_3e980e27 import solve_3e980e27
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_3e980e27 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_40853293 import solve_40853293
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_40853293 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_4290ef0e import solve_4290ef0e
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_4290ef0e = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_447fd412 import solve_447fd412
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_447fd412 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_484b58aa import solve_484b58aa
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_484b58aa = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_50846271 import solve_50846271
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_50846271 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_57aa92db import solve_57aa92db
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_57aa92db = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_5c2c9af4 import solve_5c2c9af4
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_5c2c9af4 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_5daaa586 import solve_5daaa586
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_5daaa586 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_6455b5f5 import solve_6455b5f5
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_6455b5f5 = lambda *_a, **_k: None
try:
    from alix.solveurs.arc.taches.test_6a1e5592 import solve_6a1e5592
except ImportError as _e_repli:  # module propre à une tâche, introuvable sur le disque
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    solve_6a1e5592 = lambda *_a, **_k: None

def wrap(solver):
    def wrapper(grid: np.ndarray, train_pairs=None):
        try:
            return solver(np.array(grid))
        except Exception:
            return None
    return wrapper

def get_wave21_primitives() -> Dict[str, Callable]:
    return {
        "tile_2x2_and_diagonal_neighbors_of_dots_to_8": wrap(solve_10fcaaa3),
        "partition_into_2x2_squares_8_and_1x3_bars_2": wrap(solve_150deff5),
        "compact_columns_and_balance_puzzle_pieces_around_spine": wrap(solve_234bbc79),
        "teleport_carrier_pattern_via_d4_anchor_isometry": wrap(solve_0e206a2e),
        "template_ray_and_local_stamp_propagation": wrap(solve_264363fd),
        "orthogonal_laser_bouncing_to_docking_domino": wrap(solve_2dd70a9a),
        "dynamic_d4_symmetry_propagation_fill_9s": wrap(solve_3631a71a),
        "d4_isometry_transfer_of_decorations_via_anchor_2": wrap(solve_36d67576),
        "chebyshev_cluster_bounding_box_rect_fill_4": wrap(solve_36fdfd69),
        "anchor_color_conditioned_d4_stamping": wrap(solve_3e980e27),
        "connect_matching_color_pairs_with_orthogonal_segments": wrap(solve_40853293),
        "concentric_square_frames_multiscale_d4": wrap(solve_4290ef0e),
        "homothetic_kronecker_scaling_from_anchor_block": wrap(solve_447fd412),
        "wallpaper_lattice_periodic_translation_inpaint": wrap(solve_484b58aa),
        "complete_incomplete_crosses_of_radius_r": wrap(solve_50846271),
        "homothetic_expansion_of_anchor_attached_block": wrap(solve_57aa92db),
        "concentric_hollow_square_frames_from_diagonal_triplet": wrap(solve_5c2c9af4),
        "crop_subgrid_between_4_lines_and_directional_dot_rays": wrap(solve_5daaa586),
        "color_largest_and_smallest_empty_components": wrap(solve_6455b5f5),
        "dock_falling_shapes_into_stalactite_ceiling_cavities": wrap(solve_6a1e5592),
    }
