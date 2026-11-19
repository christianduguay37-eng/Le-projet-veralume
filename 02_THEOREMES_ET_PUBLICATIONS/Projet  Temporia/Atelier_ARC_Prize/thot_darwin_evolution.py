"""
==========================================================================
 🧬 THOT DARWIN EVOLUTION : MOTEUR DE PROGRAMMATION GÉNÉTIQUE DÉTERMINISTE
==========================================================================
Auteurs : Christian Duguay & Alix (Binôme Souverain)
Architecture : Programmation Génétique Déterministe & Recombinaison Multi-Paliers
Principes :
 1. Génération 0 : Criblage des 389 primitives atomiques en O(1)
 2. Génération 1 : Gradient de palette bijectif discret (Color Mapping O(1))
 3. Génération 2 : Croisement & Recombinaison P2 o P1 (Top-K Parents)
 4. Génération 3 : Hybridation par superposition booléenne (P1 (+) P2)
 5. Garde-fou Horus : Bornage strict des boucles et timeout par puzzle
 6. Survie du plus apte : Fallback intelligent sur le plus haut fitness
==========================================================================
"""

import time
from typing import List, Dict, Tuple, Optional, Callable, Any
import numpy as np

from thot_arc_core import ArcGrid, ArcTask
from thot_ksil_multiverse import ThotMultiverseSolver, VeralumeMicrowaveFilter


class DarwinGenome:
    """Représente un programme candidat (séquence ou composition d'opérateurs)."""
    
    def __init__(self, name: str, apply_fn: Callable[[np.ndarray, List[Dict[str, np.ndarray]]], Optional[np.ndarray]], depth: int = 1):
        self.name = name
        self.apply_fn = apply_fn
        self.depth = depth
        self.fitness = 0.0
        self.train_matches = False
        
    def execute(self, inp: np.ndarray, train_pairs: List[Dict[str, np.ndarray]]) -> Optional[np.ndarray]:
        try:
            return self.apply_fn(inp, train_pairs)
        except Exception:
            return None


class ThotDarwinEngine:
    """Moteur d'évolution darwinienne pour la synthèse de programmes ARC-AGI."""

    def __init__(self, max_seconds_per_task: float = 10.0, top_k_parents: int = 15):
        self.max_seconds = max_seconds_per_task
        self.top_k = top_k_parents
        self.base_solver = ThotMultiverseSolver()
        self.prims = self.base_solver.prims

    @staticmethod
    def compute_fitness(pred: Optional[np.ndarray], target: np.ndarray) -> float:
        """Calcule le fitness de ressemblance pixel-perfect [0.0 à 1.0]."""
        if pred is None:
            return 0.0
        if pred.shape != target.shape:
            # Pénalité de forme mais petit score si le ratio est exact
            h1, w1 = pred.shape
            h2, w2 = target.shape
            if h1 * w2 == h2 * w1:
                return 0.1
            return 0.0
        
        total_pixels = target.size
        matching_pixels = np.sum(pred == target)
        return float(matching_pixels / total_pixels)

    @staticmethod
    def derive_exact_palette_mutation(preds: List[np.ndarray], targets: List[np.ndarray]) -> Optional[Dict[int, int]]:
        """
        Dérive en O(1) la mutation de palette optimale par analyse de congruence.
        Si une bijection existe telle que map(pred) == target pour toutes les paires :
        renvoie le dictionnaire de mapping exact.
        """
        mapping = {}
        for p, t in zip(preds, targets):
            if p is None or p.shape != t.shape:
                return None
            p_flat = p.flatten()
            t_flat = t.flatten()
            for c_in, c_out in zip(p_flat, t_flat):
                c_in_int = int(c_in)
                c_out_int = int(c_out)
                if c_in_int in mapping:
                    if mapping[c_in_int] != c_out_int:
                        return None # Conflit : pas de mapping bijectif uniforme
                else:
                    mapping[c_in_int] = c_out_int
        return mapping

    @staticmethod
    def apply_palette_mapping(grid: np.ndarray, mapping: Dict[int, int]) -> np.ndarray:
        """Applique un dictionnaire de mapping de couleur sur une grille numpy."""
        out = grid.copy()
        for src, dst in mapping.items():
            if src != dst:
                out[grid == src] = dst
        return out

    def solve(self, task: ArcTask) -> Dict[str, Any]:
        """
        Exécute la boucle évolutive de Darwin sur le puzzle ARC.
        Retourne la meilleure solution certifiée à 100% ou le génome ayant le plus haut fitness.
        """
        t0 = time.perf_counter()
        train_inputs = [p["input"] for p in task.train_pairs]
        train_targets = [p["output"] for p in task.train_pairs]
        num_pairs = len(train_inputs)

        # ----------------------------------------------------------------------
        # 1. GÉNÉRATION 0 : ÉVALUATION DES PRIMITIVES ATOMIQUES EN O(1)
        # ----------------------------------------------------------------------
        candidates_gen0: List[Tuple[float, str, Callable, List[Optional[np.ndarray]]]] = []
        
        for name, fn in self.prims.items():
            if (time.perf_counter() - t0) > self.max_seconds:
                break
                
            preds = []
            scores = []
            all_perfect = True
            
            for inp, tgt in zip(train_inputs, train_targets):
                try:
                    p = fn(inp, task.train_pairs)
                except Exception:
                    p = None
                preds.append(p)
                fit = self.compute_fitness(p, tgt)
                scores.append(fit)
                if fit < 1.0:
                    all_perfect = False
            
            mean_fitness = sum(scores) / num_pairs if scores else 0.0
            
            # Victoire immédiate
            if all_perfect:
                return self._package_solution(task, f"Darwin:Gen0[{name}]", fn, preds, t0, 1.0)
                
            if mean_fitness > 0.0:
                candidates_gen0.append((mean_fitness, name, fn, preds))

        # Trier par ordre décroissant de fitness
        candidates_gen0.sort(key=lambda x: x[0], reverse=True)
        best_overall_fitness = candidates_gen0[0][0] if candidates_gen0 else 0.0
        best_overall_fn = candidates_gen0[0][2] if candidates_gen0 else (lambda x, ctx: x.copy())
        best_overall_name = candidates_gen0[0][1] if candidates_gen0 else "fallback_identity"

        # ----------------------------------------------------------------------
        # 2. GÉNÉRATION 1 : GRADIENT DE PALETTE PAR BIJECTION DISCRÈTE O(1)
        # ----------------------------------------------------------------------
        # On teste les candidats ayant la forme exacte pour voir si une mutation de palette résout le puzzle
        for fit, name, fn, preds in candidates_gen0[:30]:
            if (time.perf_counter() - t0) > self.max_seconds:
                break
            # Vérifier si toutes les prédictions ont la bonne forme
            shapes_match = all(p is not None and p.shape == t.shape for p, t in zip(preds, train_targets))
            if shapes_match:
                mapping = self.derive_exact_palette_mutation(preds, train_targets)
                if mapping is not None:
                    # BINGO ! Règle exacte trouvée par mutation de palette !
                    mutated_fn = lambda inp, ctx, f=fn, m=mapping: self.apply_palette_mapping(f(inp, ctx), m)
                    mutated_preds = [self.apply_palette_mapping(p, mapping) for p in preds]
                    return self._package_solution(task, f"Darwin:Gen1[PaletteMap o {name}]", mutated_fn, mutated_preds, t0, 1.0)

        # ----------------------------------------------------------------------
        # 3. GÉNÉRATION 2 : CROISEMENT DARWINIEN & RECOMBINAISON P2 o P1
        # ----------------------------------------------------------------------
        top_parents = candidates_gen0[:self.top_k]
        
        for fit1, name1, fn1, preds1 in top_parents:
            if (time.perf_counter() - t0) > self.max_seconds:
                break
            # Ne tester que si P1 a produit des grilles valides
            if any(p is None for p in preds1):
                continue
                
            # Les sorties de P1 deviennent les entrées pour P2
            inter_pairs = [{"input": p, "output": t} for p, t in zip(preds1, train_targets)]
            
            for name2, fn2 in self.prims.items():
                if name1 == name2:
                    continue
                if (time.perf_counter() - t0) > self.max_seconds:
                    break
                    
                preds2 = []
                scores2 = []
                all_perfect2 = True
                
                for p1, tgt in zip(preds1, train_targets):
                    try:
                        p2 = fn2(p1, inter_pairs)
                    except Exception:
                        p2 = None
                    preds2.append(p2)
                    f2 = self.compute_fitness(p2, tgt)
                    scores2.append(f2)
                    if f2 < 1.0:
                        all_perfect2 = False
                        
                mean_fit2 = sum(scores2) / num_pairs if scores2 else 0.0
                
                if all_perfect2:
                    composite_fn = lambda inp, ctx, f1=fn1, f2=fn2: f2(f1(inp, ctx), ctx)
                    return self._package_solution(task, f"Darwin:Gen2[{name2} o {name1}]", composite_fn, preds2, t0, 1.0)
                    
                # Vérifier mutation de palette sur P2 o P1
                if all(p is not None and p.shape == t.shape for p, t in zip(preds2, train_targets)):
                    m2 = self.derive_exact_palette_mutation(preds2, train_targets)
                    if m2 is not None:
                        comp_mut_fn = lambda inp, ctx, f1=fn1, f2=fn2, m=m2: self.apply_palette_mapping(f2(f1(inp, ctx), ctx), m)
                        mut_preds2 = [self.apply_palette_mapping(p, m2) for p in preds2]
                        return self._package_solution(task, f"Darwin:Gen2[PaletteMap o {name2} o {name1}]", comp_mut_fn, mut_preds2, t0, 1.0)
                        
                if mean_fit2 > best_overall_fitness:
                    best_overall_fitness = mean_fit2
                    best_overall_fn = lambda inp, ctx, f1=fn1, f2=fn2: f2(f1(inp, ctx), ctx)
                    best_overall_name = f"Darwin:Gen2[{name2} o {name1}]"

        # ----------------------------------------------------------------------
        # 4. GÉNÉRATION 3 : SUPERPOSITION BOOLÉENNE P1 (+) P2 (Overlay)
        # ----------------------------------------------------------------------
        if len(top_parents) >= 2:
            for i in range(min(5, len(top_parents))):
                for j in range(i + 1, min(6, len(top_parents))):
                    if (time.perf_counter() - t0) > self.max_seconds:
                        break
                    _, n1, f1, p1_list = top_parents[i]
                    _, n2, f2, p2_list = top_parents[j]
                    
                    overlay_preds = []
                    all_overlay_perfect = True
                    for p1, p2, tgt in zip(p1_list, p2_list, train_targets):
                        if p1 is not None and p2 is not None and p1.shape == p2.shape and p1.shape == tgt.shape:
                            # Superposer P2 sur P1 là où P2 est non-zéro
                            ov = p1.copy()
                            ov[p2 != 0] = p2[p2 != 0]
                            overlay_preds.append(ov)
                            if not np.array_equal(ov, tgt):
                                all_overlay_perfect = False
                        else:
                            all_overlay_perfect = False
                            break
                            
                    if all_overlay_perfect and len(overlay_preds) == num_pairs:
                        ov_fn = lambda inp, ctx, fa=f1, fb=f2: np.where(fb(inp, ctx) != 0, fb(inp, ctx), fa(inp, ctx))
                        return self._package_solution(task, f"Darwin:Gen3[{n2} (+) {n1}]", ov_fn, overlay_preds, t0, 1.0)

        # ----------------------------------------------------------------------
        # 5. SÉLECTION NATURELLE : RENVOI DU MEILLEUR SURVIVANT
        # ----------------------------------------------------------------------
        is_solved = (best_overall_fitness == 1.0)
        return self._package_solution(task, best_overall_name, best_overall_fn, None, t0, best_overall_fitness)

    def _package_solution(self, task: ArcTask, rule_name: str, fn: Callable, train_preds: Optional[List[np.ndarray]], t0: float, fitness: float) -> Dict[str, Any]:
        """Emballe la prédiction de test à partir du meilleur génome validé."""
        dt_ms = (time.perf_counter() - t0) * 1000
        test_preds = []
        test_matches = []
        
        for tp in task.test_pairs:
            inp = tp["input"]
            try:
                pred = fn(inp, task.train_pairs)
            except Exception:
                pred = None
                
            if pred is not None:
                test_preds.append(pred.astype(int).tolist())
            else:
                test_preds.append(inp.astype(int).tolist()) # repli d'urgence
                
            if tp.get("output") is not None and pred is not None:
                test_matches.append(bool(np.array_equal(pred, tp["output"])))
                
        return {
            "solved": (fitness == 1.0),
            "rule": rule_name,
            "fitness": fitness,
            "task_id": task.task_id,
            "test_pass": all(test_matches) if test_matches else None,
            "predictions": test_preds,
            "dt_ms": dt_ms
        }
