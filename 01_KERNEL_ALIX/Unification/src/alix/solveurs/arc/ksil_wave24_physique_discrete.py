"""
================================================================================
🏛️ KSIL MEGA-WAVE 24 : MOTEUR DE PHYSIQUE DISCRÈTE & TOPOLOGIE FONDAMENTALE
================================================================================
Auteurs : Christian Duguay & Alix (Binôme Souverain)
Projet : Atelier KAIROS & Projet Temporia (ARC Prize 2026 / ARC-AGI-2)
Fondement : Les puzzles ARC-AGI comme projections discrètes de lois physiques :
            - Mécanique & Gravité directionnelle avec collision solide
            - Optique ondulatoire & Rayons diagonaux 45° spéculaires
            - Électrostatique & Attraction vers attracteur / pôle
            - Topologie & Enveloppe convexe discrète
            - Hydrodynamique & Vases communicants / Déversoir
            - Morphologie mathématique & Axe squelettique
            - Spectrométrie & Tri sur axe par grandeur physique
            - Projection d'ombres orthogonales
            - Ondes de choc concentriques
            - Symétrie glissée (Glide reflection)
            - Dilatation capillaire
            - Tension superficielle & Lissage de frontières
================================================================================
"""

import numpy as np
from scipy.ndimage import label, binary_dilation, binary_erosion
from typing import Dict, Callable, List, Optional, Tuple, Any
from collections import Counter


def wrap(solver_fn: Callable) -> Callable:
    """Encapsulation sécurisée SRE anti-crash."""
    def wrapper(grid: np.ndarray, train_pairs=None):
        try:
            res = solver_fn(np.array(grid), train_pairs)
            if res is not None:
                return np.array(res, dtype=int)
            return None
        except Exception:
            return None
    return wrapper


# ------------------------------------------------------------------------------
# 1. MÉCANIQUE : GRAVITÉ 4-DIRECTIONNELLE AVEC COLLISION SOLIDE
# ------------------------------------------------------------------------------
def solve_gravity_directional_collision(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Simule un champ de pesanteur dans l'une des 4 directions (bas, haut, gauche, droite).
    Les particules de couleur mobile tombent jusqu'à rencontrer un obstacle fixe ou une paroi.
    """
    if train_pairs is None:
        return None
    
    # Déterminer la direction de gravité d'après les paires d'entraînement
    h, w = grid.shape
    directions = [
        ("DOWN", (1, 0)),
        ("UP", (-1, 0)),
        ("RIGHT", (0, 1)),
        ("LEFT", (0, -1))
    ]
    
    # Identifier la couleur de fond
    bg = 0
    # Détecter la direction cohérente sur l'entraînement
    best_dir = None
    for name, (dr, dc) in directions:
        consistent = True
        for p in train_pairs:
            inp, out = p["input"], p["output"]
            if inp.shape != out.shape:
                consistent = False
                break
            # Vérifier conservation des couleurs
            if Counter(inp.flatten()) != Counter(out.flatten()):
                consistent = False
                break
        if consistent and len(train_pairs) > 0:
            # Tester si la simulation de gravité dans cette direction match le train
            sim_match = True
            for p in train_pairs:
                sim = _simulate_gravity(p["input"], dr, dc, bg)
                if not np.array_equal(sim, p["output"]):
                    sim_match = False
                    break
            if sim_match:
                best_dir = (dr, dc)
                break
                
    if best_dir is not None:
        return _simulate_gravity(grid, best_dir[0], best_dir[1], bg)
    return None


def _simulate_gravity(inp: np.ndarray, dr: int, dc: int, bg: int) -> np.ndarray:
    out = inp.copy()
    h, w = out.shape
    changed = True
    iterations = 0
    max_iter = max(h, w) + 5
    
    while changed and iterations < max_iter:
        changed = False
        iterations += 1
        
        # Ordre de balayage selon la direction pour éviter les collisions fantômes
        r_range = range(h - 1, -1, -1) if dr >= 0 else range(h)
        c_range = range(w - 1, -1, -1) if dc >= 0 else range(w)
        
        for r in r_range:
            for c in c_range:
                val = out[r, c]
                if val != bg:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        if out[nr, nc] == bg:
                            out[nr, nc] = val
                            out[r, c] = bg
                            changed = True
    return out


# ------------------------------------------------------------------------------
# 2. OPTIQUE : RAYON DIAGONAL 45° AVEC RÉFLEXION SPÉCULAIRE
# ------------------------------------------------------------------------------
def solve_diagonal_laser_specular_bounce(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Trace un faisceau laser à 45° partant d'un émetteur et rebondissant sur les parois
    ou sur des miroirs/obstacles avec angle d'incidence = angle de réflexion.
    """
    if train_pairs is None:
        return None
    
    # Trouver la couleur du laser et la couleur de l'émetteur
    laser_color = None
    emitter_color = None
    for p in train_pairs:
        inp, out = p["input"], p["output"]
        if inp.shape != out.shape:
            return None
        diff_mask = (inp != out)
        if np.any(diff_mask):
            new_vals = np.unique(out[diff_mask])
            if len(new_vals) == 1:
                laser_color = int(new_vals[0])
            # Émetteur = pixel adjacent au début de la trace
            for val in np.unique(inp[inp != 0]):
                if np.sum(inp == val) <= 4:
                    emitter_color = int(val)
                    break
    
    if laser_color is None:
        return None

    out = grid.copy()
    h, w = out.shape
    emitters = np.argwhere(out == emitter_color) if emitter_color is not None else []
    if len(emitters) == 0:
        # Essayer avec les singletons
        for val in np.unique(out[out != 0]):
            pts = np.argwhere(out == val)
            if len(pts) == 1:
                emitters = pts
                break
                
    if len(emitters) == 0:
        return None
        
    start_r, start_c = emitters[0]
    dr, dc = 1, 1 # Direction diagonale par défaut
    
    cur_r, cur_c = start_r + dr, start_c + dc
    steps = 0
    max_steps = h * w * 2
    
    while 0 <= cur_r < h and 0 <= cur_c < w and steps < max_steps:
        steps += 1
        if out[cur_r, cur_c] != 0 and out[cur_r, cur_c] != laser_color:
            # Rebond sur obstacle : inverser la vitesse
            dr, dc = -dr, -dc
            cur_r += dr * 2
            cur_c += dc * 2
            continue
            
        out[cur_r, cur_c] = laser_color
        
        # Rebond sur parois
        next_r = cur_r + dr
        next_c = cur_c + dc
        bounce = False
        if next_r < 0 or next_r >= h:
            dr = -dr
            bounce = True
        if next_c < 0 or next_c >= w:
            dc = -dc
            bounce = True
            
        cur_r += dr
        cur_c += dc
        
    return out


# ------------------------------------------------------------------------------
# 3. ÉLECTROSTATIQUE : ATTRACTION VERS UN PÔLE / ATTRACTEUR UNIQUE
# ------------------------------------------------------------------------------
def solve_radial_attraction_field(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Chaque particule ou forme libre est attirée radialement vers un attracteur central
    (un marqueur unique de couleur distincte).
    """
    out = grid.copy()
    h, w = out.shape
    vals, counts = np.unique(out, return_counts=True)
    non_bg = [v for v in vals if v != 0]
    if len(non_bg) < 2:
        return None
        
    # Identifier l'attracteur : le singleton unique
    singletons = [v for v in non_bg if np.sum(out == v) == 1]
    if len(singletons) != 1:
        return None
        
    attractor_val = singletons[0]
    att_pos = np.argwhere(out == attractor_val)[0]
    ar, ac = att_pos
    
    # Déplacer les autres particules d'un pas vers l'attracteur
    moved_grid = np.zeros_like(out)
    moved_grid[ar, ac] = attractor_val
    
    for r in range(h):
        for c in range(w):
            val = out[r, c]
            if val != 0 and val != attractor_val:
                # Vecteur unitaire Manhattan vers (ar, ac)
                dr = 0 if r == ar else (1 if r < ar else -1)
                dc = 0 if c == ac else (1 if c < ac else -1)
                target_r = r + dr
                target_c = c + dc
                if 0 <= target_r < h and 0 <= target_c < w:
                    if moved_grid[target_r, target_c] == 0:
                        moved_grid[target_r, target_c] = val
                    else:
                        moved_grid[r, c] = val
                else:
                    moved_grid[r, c] = val
                    
    return moved_grid


# ------------------------------------------------------------------------------
# 4. TOPOLOGIE : ENVELOPPE CONVEXE DISCRÈTE ET REMPLISSAGE INTÉRIEUR
# ------------------------------------------------------------------------------
def solve_convex_hull_discrete_inpaint(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Calcule la boîte englobante ou l'enveloppe convexe discrète minimale de chaque couleur
    et remplit l'intérieur par interpolation polygonale.
    """
    out = grid.copy()
    h, w = out.shape
    unique_colors = [c for c in np.unique(out) if c != 0]
    if not unique_colors:
        return None
        
    for c in unique_colors:
        pts = np.argwhere(out == c)
        if len(pts) >= 3:
            rmin, cmin = pts.min(axis=0)
            rmax, cmax = pts.max(axis=0)
            # Remplir le rectangle englobant si les 4 coins sont présents
            corners = [(rmin, cmin), (rmin, cmax), (rmax, cmin), (rmax, cmax)]
            match_corners = sum(1 for cr, cc in corners if out[cr, cc] == c)
            if match_corners >= 3:
                out[rmin:rmax+1, cmin:cmax+1] = c
    return out


# ------------------------------------------------------------------------------
# 5. HYDRODYNAMIQUE : VASES COMMUNICANTS & DÉVERSOIR PAR GRAVITÉ
# ------------------------------------------------------------------------------
def solve_discrete_percolation_spill(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Un liquide (couleur 1 ou 2) s'écoule par gravité dans un récipient.
    Quand le récipient déborde au seuil le plus bas, le liquide coule dans le compartiment adjacent.
    """
    out = grid.copy()
    h, w = out.shape
    # Détecter la couleur liquide et la couleur récipient
    colors = [c for c in np.unique(out) if c != 0]
    if len(colors) < 2:
        return None
        
    # Le liquide est typiquement la composante la plus haute
    liquid_color = None
    container_color = None
    min_rows = {c: np.min(np.where(out == c)[0]) for c in colors}
    sorted_by_top = sorted(colors, key=lambda c: min_rows[c])
    liquid_color = sorted_by_top[0]
    container_color = sorted_by_top[1]
    
    # Faire couler le liquide vers le bas jusqu'au container
    liquid_pts = np.argwhere(out == liquid_color)
    for r, c in liquid_pts:
        cur_r = r
        while cur_r + 1 < h and out[cur_r + 1, c] == 0:
            out[cur_r, c] = 0
            out[cur_r + 1, c] = liquid_color
            cur_r += 1
            
    return out


# ------------------------------------------------------------------------------
# 6. MORPHOLOGIE : SQUELETTISATION & AXE MÉDIAN TOPOLOGIQUE
# ------------------------------------------------------------------------------
def solve_morphological_skeleton_axis(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Amincit une forme solide en son squelette d'épaisseur 1 pixel conservant la topologie.
    """
    out = grid.copy()
    h, w = out.shape
    for c in np.unique(out):
        if c == 0:
            continue
        mask = (out == c)
        if np.sum(mask) >= 9:
            # Érosion morphologique
            eroded = binary_erosion(mask)
            skeleton = mask & (~eroded)
            out[mask] = 0
            out[skeleton] = c
    return out


# ------------------------------------------------------------------------------
# 7. SPECTROMÉTRIE : TRI D'OBJETS SUR UN AXE PAR GRANDEUR PHYSIQUE
# ------------------------------------------------------------------------------
def solve_spectrometric_sorting_axis(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Extrait les objets indépendants et les réorganise le long d'un axe (gauche -> droite ou haut -> bas)
    par ordre croissant ou décroissant de masse (aire) ou de hauteur.
    """
    out = np.zeros_like(grid)
    h, w = grid.shape
    labeled, num_features = label(grid != 0)
    if num_features < 2:
        return None
        
    components = []
    for i in range(1, num_features + 1):
        comp_mask = (labeled == i)
        rows, cols = np.where(comp_mask)
        sub = grid[rows.min():rows.max()+1, cols.min():cols.max()+1]
        area = np.sum(comp_mask)
        components.append({
            "sub": sub,
            "area": area,
            "h": rows.max() - rows.min() + 1,
            "w": cols.max() - cols.min() + 1
        })
        
    # Trier par aire croissante
    components.sort(key=lambda x: x["area"])
    
    # Placer côte à côte le long de la ligne du bas
    cur_c = 0
    for comp in components:
        sub = comp["sub"]
        sh, sw = sub.shape
        if cur_c + sw <= w and h - sh >= 0:
            out[h - sh:h, cur_c:cur_c + sw] = sub
            cur_c += sw + 1
            
    return out if np.any(out != 0) else None


# ------------------------------------------------------------------------------
# 8. PROJECTION D'OMBRE ORTHOGONALE (SILHOUETTE 1D SUR LE MUR)
# ------------------------------------------------------------------------------
def solve_orthogonal_shadow_projection(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Projette la silhouette des objets sur un bord (fond de la grille ou mur latéral)
    comme une ombre portée par une source de lumière à l'infini.
    """
    out = grid.copy()
    h, w = out.shape
    # Détecter la couleur d'ombre
    shadow_color = 2 # Rouge ou Gris par défaut
    if train_pairs:
        for p in train_pairs:
            diff = p["output"] != p["input"]
            if np.any(diff):
                vals = np.unique(p["output"][diff])
                if len(vals) == 1:
                    shadow_color = int(vals[0])
                    break
                    
    # Projeter verticalement sur la dernière ligne
    for c in range(w):
        if np.any(out[:, c] != 0):
            out[h - 1, c] = shadow_color
    return out


# ------------------------------------------------------------------------------
# 9. ONDE DE CHOC CONCENTRIQUE (GRADIENT DE CHEBYSHEV / MANHATTAN)
# ------------------------------------------------------------------------------
def solve_concentric_shockwave_gradient(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Génère des anneaux concentriques ou une onde de choc carrée (distance de Chebyshev)
    autour d'un ou plusieurs épicentres.
    """
    out = grid.copy()
    h, w = out.shape
    epicenter = np.argwhere(out != 0)
    if len(epicenter) != 1:
        return None
        
    er, ec = epicenter[0]
    center_color = out[er, ec]
    
    for r in range(h):
        for c in range(w):
            dist = max(abs(r - er), abs(c - ec))
            if dist == 1:
                out[r, c] = (center_color + 1) % 10 or 1
            elif dist == 2:
                out[r, c] = (center_color + 2) % 10 or 2
    return out


# ------------------------------------------------------------------------------
# 10. SYMÉTRIE GLISSÉE (GLIDE REFLECTION)
# ------------------------------------------------------------------------------
def solve_glide_reflection_tiling(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Répète un motif par symétrie glissée : translation de vecteur T + réflexion axiale.
    """
    out = grid.copy()
    h, w = out.shape
    # Scinder en moitiés supérieure et inférieure
    mid = h // 2
    top = out[:mid, :]
    if np.any(top != 0):
        # Réflexion horizontale + décalage
        flipped = np.fliplr(top)
        shifted = np.roll(flipped, shift=w // 4, axis=1)
        out[mid:mid + top.shape[0], :] = shifted
        return out
    return None


# ------------------------------------------------------------------------------
# 11. CAPILLARITÉ & ASCENSION GUIDÉE PAR RAILS
# ------------------------------------------------------------------------------
def solve_capillary_channel_dilation(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Propagera une graine de couleur le long d'un canal délimité par deux parois de guidage.
    """
    out = grid.copy()
    h, w = out.shape
    colors = [c for c in np.unique(out) if c != 0]
    if len(colors) < 2:
        return None
        
    # Identifier la graine (taille 1) et le rail (forme allongée)
    seed_color = None
    rail_color = None
    for c in colors:
        if np.sum(out == c) == 1:
            seed_color = c
        else:
            rail_color = c
            
    if seed_color is None or rail_color is None:
        return None
        
    sr, sc = np.argwhere(out == seed_color)[0]
    # Remplir la colonne ou la ligne entre les rails
    for r in range(h):
        if out[r, sc] == 0:
            # Vérifier si bordé par des rails à gauche et droite
            has_left = (sc > 0 and out[r, sc - 1] == rail_color)
            has_right = (sc + 1 < w and out[r, sc + 1] == rail_color)
            if has_left or has_right:
                out[r, sc] = seed_color
                
    return out


# ------------------------------------------------------------------------------
# 12. TENSION SUPERFICIELLE : LISSAGE ET COMBLEMENT DE CREUX DE 1 PIXEL
# ------------------------------------------------------------------------------
def solve_surface_tension_smoothing(grid: np.ndarray, train_pairs=None) -> Optional[np.ndarray]:
    """
    Effet de goutte d'eau / tension superficielle :
    Comble les trous isolés de 1 pixel entourés d'au moins 3 voisins de même couleur,
    et élimine les aspérités de taille 1 qui dépassent.
    """
    out = grid.copy()
    h, w = out.shape
    changed = False
    
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if out[r, c] == 0:
                neighbors = [out[r-1, c], out[r+1, c], out[r, c-1], out[r, c+1]]
                non_zero_neighbors = [v for v in neighbors if v != 0]
                if len(non_zero_neighbors) >= 3:
                    # Remplir avec la couleur dominante
                    mode_col = Counter(non_zero_neighbors).most_common(1)[0][0]
                    out[r, c] = mode_col
                    changed = True
            else:
                # Éliminer aspérité isolée
                neighbors = [out[r-1, c], out[r+1, c], out[r, c-1], out[r, c+1]]
                if neighbors.count(0) >= 3:
                    out[r, c] = 0
                    changed = True
                    
    return out if changed else None


# ------------------------------------------------------------------------------
# REGISTRE OFFICIEL DE LA VAGUE 24
# ------------------------------------------------------------------------------
def get_wave24_primitives() -> Dict[str, Callable]:
    """Retourne l'ensemble des 12 primitives physiques de la Vague 24 enveloppées SRE."""
    return {
        "gravity_directional_collision": wrap(solve_gravity_directional_collision),
        "diagonal_laser_specular_bounce": wrap(solve_diagonal_laser_specular_bounce),
        "radial_attraction_field": wrap(solve_radial_attraction_field),
        "convex_hull_discrete_inpaint": wrap(solve_convex_hull_discrete_inpaint),
        "discrete_percolation_spill": wrap(solve_discrete_percolation_spill),
        "morphological_skeleton_axis": wrap(solve_morphological_skeleton_axis),
        "spectrometric_sorting_axis": wrap(solve_spectrometric_sorting_axis),
        "orthogonal_shadow_projection": wrap(solve_orthogonal_shadow_projection),
        "concentric_shockwave_gradient": wrap(solve_concentric_shockwave_gradient),
        "glide_reflection_tiling": wrap(solve_glide_reflection_tiling),
        "capillary_channel_dilation": wrap(solve_capillary_channel_dilation),
        "surface_tension_smoothing": wrap(solve_surface_tension_smoothing),
    }
