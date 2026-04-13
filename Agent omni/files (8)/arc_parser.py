"""
Parser ARC-AGI Dataset + Utilitaires
VERALUME/TEMPORIA - Christian Duguay
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional

# ============================================================================
# PARSER ARC DATASET
# ============================================================================

def load_arc_tasks(dataset_path: str) -> List[Dict]:
    """
    Charge dataset ARC depuis fichier JSON
    
    Format attendu:
    {
      "train": [{"input": [[int]], "output": [[int]]}],
      "test": [{"input": [[int]], "output": [[int]]}]
    }
    """
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    # Si fichier contient multiple tasks (format evaluation)
    if isinstance(data, dict) and 'train' not in data:
        # Format: {"task_id": {"train": [...], "test": [...]}}
        tasks = []
        for task_id, task_data in data.items():
            tasks.append({
                'id': task_id,
                'train': task_data['train'],
                'test': task_data['test']
            })
        return tasks
    else:
        # Single task
        return [{'id': 'single', 'train': data['train'], 'test': data['test']}]


# ============================================================================
# REPRÉSENTATION GRILLE
# ============================================================================

def grid_to_ascii(grid: List[List[int]]) -> str:
    """
    Convertit grille numérique en ASCII visuel
    
    Couleurs ARC:
    0=noir, 1=bleu, 2=rouge, 3=vert, 4=jaune, 
    5=gris, 6=magenta, 7=orange, 8=cyan, 9=marron
    """
    colors = {
        0: '·',  # noir (vide)
        1: '█',  # bleu (plein)
        2: '▓',  # rouge
        3: '▒',  # vert
        4: '░',  # jaune
        5: '▪',  # gris
        6: '▫',  # magenta
        7: '○',  # orange
        8: '●',  # cyan
        9: '◆'   # marron
    }
    
    lines = []
    for row in grid:
        lines.append(''.join(colors.get(cell, '?') for cell in row))
    
    return '\n'.join(lines)


def grid_to_structure(grid: List[List[int]]) -> Dict:
    """
    Analyse structurelle grille pour raisonnement abstrait
    """
    h, w = len(grid), len(grid[0]) if grid else 0
    
    # Cellules par couleur
    color_positions = {}
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell not in color_positions:
                color_positions[cell] = []
            color_positions[cell].append((i, j))
    
    # Patterns détectés
    patterns = {
        'symmetry_vertical': is_symmetric_vertical(grid),
        'symmetry_horizontal': is_symmetric_horizontal(grid),
        'has_border': has_uniform_border(grid),
        'repeated_pattern': detect_repeated_pattern(grid)
    }
    
    return {
        'dimensions': (h, w),
        'colors': list(color_positions.keys()),
        'color_counts': {c: len(pos) for c, pos in color_positions.items()},
        'color_positions': color_positions,
        'patterns': patterns
    }


# ============================================================================
# DÉTECTION PATTERNS
# ============================================================================

def is_symmetric_vertical(grid: List[List[int]]) -> bool:
    """Symétrie verticale (gauche-droite)"""
    for row in grid:
        if row != row[::-1]:
            return False
    return True


def is_symmetric_horizontal(grid: List[List[int]]) -> bool:
    """Symétrie horizontale (haut-bas)"""
    return grid == grid[::-1]


def has_uniform_border(grid: List[List[int]]) -> bool:
    """Vérifie si bordure est uniforme"""
    if not grid:
        return False
    
    h, w = len(grid), len(grid[0])
    if h < 2 or w < 2:
        return False
    
    border_color = grid[0][0]
    
    # Top & bottom
    for j in range(w):
        if grid[0][j] != border_color or grid[h-1][j] != border_color:
            return False
    
    # Left & right
    for i in range(h):
        if grid[i][0] != border_color or grid[i][w-1] != border_color:
            return False
    
    return True


def detect_repeated_pattern(grid: List[List[int]]) -> Optional[Tuple[int, int]]:
    """
    Détecte pattern répété (tile)
    Retourne dimensions du tile si trouvé
    """
    h, w = len(grid), len(grid[0]) if grid else 0
    
    # Test différentes tailles de tile
    for tile_h in range(1, h // 2 + 1):
        for tile_w in range(1, w // 2 + 1):
            if h % tile_h == 0 and w % tile_w == 0:
                if is_tiled_pattern(grid, tile_h, tile_w):
                    return (tile_h, tile_w)
    
    return None


def is_tiled_pattern(grid: List[List[int]], tile_h: int, tile_w: int) -> bool:
    """Vérifie si grille est répétition d'un tile"""
    h, w = len(grid), len(grid[0])
    
    # Extraire tile de référence
    tile = [row[:tile_w] for row in grid[:tile_h]]
    
    # Vérifier répétition
    for i in range(0, h, tile_h):
        for j in range(0, w, tile_w):
            for di in range(tile_h):
                for dj in range(tile_w):
                    if i+di >= h or j+dj >= w:
                        continue
                    if grid[i+di][j+dj] != tile[di][dj]:
                        return False
    
    return True


# ============================================================================
# COMPARAISON GRILLES
# ============================================================================

def grids_equal(grid1: List[List[int]], grid2: List[List[int]]) -> bool:
    """Exact match"""
    return grid1 == grid2


def grids_similar(grid1: List[List[int]], grid2: List[List[int]], 
                  threshold: float = 0.8) -> bool:
    """
    Match partiel: ratio de cellules identiques
    """
    if len(grid1) != len(grid2):
        return False
    
    if not grid1 or len(grid1[0]) != len(grid2[0]):
        return False
    
    h, w = len(grid1), len(grid1[0])
    matches = sum(
        1 for i in range(h) for j in range(w)
        if grid1[i][j] == grid2[i][j]
    )
    
    total = h * w
    return (matches / total) >= threshold


def grid_difference_mask(grid1: List[List[int]], grid2: List[List[int]]) -> str:
    """
    Visualise différences entre deux grilles
    """
    if len(grid1) != len(grid2) or not grid1:
        return "DIMENSION MISMATCH"
    
    h, w = len(grid1), len(grid1[0])
    
    lines = []
    for i in range(h):
        row = []
        for j in range(w):
            if grid1[i][j] == grid2[i][j]:
                row.append('✓')
            else:
                row.append('✗')
        lines.append(''.join(row))
    
    return '\n'.join(lines)


# ============================================================================
# FORMAT PROMPT POUR LLM
# ============================================================================

def format_arc_task_for_llm(task: Dict, mode: str = 'both') -> str:
    """
    Formate tâche ARC pour prompt LLM
    
    mode: 'visual' | 'structural' | 'both'
    """
    train_examples = task['train']
    test_input = task['test'][0]['input']
    
    prompt_parts = []
    
    prompt_parts.append("TÂCHE ARC-AGI: Transformation de grille\n")
    prompt_parts.append(f"Exemples d'entraînement: {len(train_examples)}\n")
    
    # Exemples
    for idx, example in enumerate(train_examples):
        prompt_parts.append(f"\n--- EXEMPLE {idx+1} ---")
        
        if mode in ['visual', 'both']:
            prompt_parts.append("\nINPUT:")
            prompt_parts.append(grid_to_ascii(example['input']))
            prompt_parts.append("\nOUTPUT:")
            prompt_parts.append(grid_to_ascii(example['output']))
        
        if mode in ['structural', 'both']:
            in_struct = grid_to_structure(example['input'])
            out_struct = grid_to_structure(example['output'])
            prompt_parts.append(f"\nSTRUCTURE INPUT: {in_struct['dimensions']} - couleurs: {in_struct['colors']}")
            prompt_parts.append(f"STRUCTURE OUTPUT: {out_struct['dimensions']} - couleurs: {out_struct['colors']}")
    
    # Test
    prompt_parts.append("\n\n--- TEST ---")
    if mode in ['visual', 'both']:
        prompt_parts.append("\nINPUT:")
        prompt_parts.append(grid_to_ascii(test_input))
    
    if mode in ['structural', 'both']:
        test_struct = grid_to_structure(test_input)
        prompt_parts.append(f"\nSTRUCTURE: {test_struct['dimensions']} - couleurs: {test_struct['colors']}")
    
    prompt_parts.append("\n\nOBJECTIF: Prédire OUTPUT pour ce test INPUT.")
    
    return '\n'.join(prompt_parts)


# ============================================================================
# MAIN (test)
# ============================================================================

if __name__ == "__main__":
    # Test avec grille simple
    test_grid = [
        [0, 1, 1, 0],
        [1, 2, 2, 1],
        [1, 2, 2, 1],
        [0, 1, 1, 0]
    ]
    
    print("=== TEST GRID ===")
    print(grid_to_ascii(test_grid))
    print("\n=== STRUCTURE ===")
    print(json.dumps(grid_to_structure(test_grid), indent=2))
    
    print("\n=== PATTERNS ===")
    struct = grid_to_structure(test_grid)
    for pattern, detected in struct['patterns'].items():
        print(f"{pattern}: {detected}")
