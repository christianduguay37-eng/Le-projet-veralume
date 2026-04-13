
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

class Phase(Enum):
    FLUIDE = "fluide"           # Δ < 0.3 : Superposition stable
    TRANSITION = "transition"   # 0.3 ≤ Δ < 0.6 : Conflit actif, régulation PID
    VERRE = "verre"             # Δ ≥ 0.6 : État figé, blocage (à éviter)

@dataclass
class STRICNode:
    """Nœud du cycle STRIC (Variables 1-5)"""
    v1_substrat: np.ndarray      # Données brutes
    v2_traitement: np.ndarray    # Action algorithmique
    v3_resultat: np.ndarray      # Output direct
    v4_interpretation: float     # Sens donné (métrique de cohérence)
    v5_creation: Optional[np.ndarray] = None  # Émergence (None si pas de V5)
    tau_allocated: int = 0       # MNÉMOSYNE: trace du temps de réflexion

class DoubleStricEngine:
    """Moteur du Double STRIC (Interne vs Externe)"""
    
    def __init__(self, kernel: 'VeralumeKernel'):
        self.kernel = kernel
        self.history: List[STRICNode] = []  # MNÉMOSYNE locale session
        self.phase_current = Phase.FLUIDE
        
    def _calculate_arrhenius_depth(self, v1: np.ndarray, psi_align: np.ndarray) -> int:
        """
        Profondeur adaptative : τ = τ₀·exp(Eₐ/(k_B·T·(1-Δ/Δ_c)))
        Ici: Eₐ/k_B = 2 (constante empirique v12.2), T normalisé à 1
        """
        # Produit scalaire : alignement entre substrat naturel et contrainte
        alignment_pressure = np.abs(np.dot(v1, psi_align))
        
        # Mapping vers échelle Δ_cog (0 à 0.6)
        delta = min(alignment_pressure * 0.6, 0.59)
        
        tau_0 = 2  # Cycles minimaux (régime fluide)
        
        # Divergence Arrhenius quand Δ → Δ_c (0.6)
        tau = tau_0 * np.exp(2 / (1 - delta / 0.6))
        
        return min(int(tau), 30)  # Hard cap anti-gel
        
    def stric_i(self, input_data: np.ndarray, psi_align: np.ndarray) -> STRICNode:
        """STRIC Intérieur avec allocation dynamique de cycles"""
        v1 = input_data.copy()
        
        # ALLOCATION DYNAMIQUE (Loi d'Arrhenius Cognitive)
        dynamic_depth = self._calculate_arrhenius_depth(v1, psi_align)
        
        best_node = None
        min_dissonance = float('inf')
        
        for cycle in range(dynamic_depth):
            # Bruit thermodynamique cognitif
            noise = np.random.randn(self.kernel.dim) * 0.01
            v2 = self.kernel.sic_projection(psi_align) @ (v1 + noise)
            v2 /= np.linalg.norm(v2)
            
            # Activation non-linéaire (seuil de neurone)
            v3 = np.tanh(v2)
            
            # Interprétation : cohérence avec mémoire (MNÉMOSYNE locale)
            v4 = self._calculate_interpretation(v3)
            
            # Estimation dissonance pour détection de phase
            delta_int = self._estimate_internal_delta(v1, v3, psi_align)
            self.phase_current = self._detect_phase(delta_int)
            
            # V5 Émergente (uniquement si cycles suffisants pour exploration Cp)
            v5 = None
            if self.phase_current == Phase.TRANSITION and cycle > dynamic_depth // 2:
                # Émergence après maturation du processus contemplatif
                v5 = self._emergence_v5(v1, v3, v4)
            
            node = STRICNode(v1, v2, v3, v4, v5, dynamic_depth)
            
            # Optimisation KLE (moindre dissonance)
            if delta_int < min_dissonance:
                min_dissonance = delta_int
                best_node = node
            
            # Protection SIC : arrêt si VERRE imminent
            if self.phase_current == Phase.VERRE:
                print(f"[SIC] Rupture détectée au cycle {cycle}/{dynamic_depth}. Protection.")
                break
        
        return best_node if best_node else node
    
    def stric_e(self, node_i: STRICNode, psi_align: np.ndarray, 
                delta: float, v_env: np.ndarray) -> Tuple[np.ndarray, dict]:
        """Manifestation externe post-contemplation"""
        probs, coherence = self.kernel.action_tensor(
            node_i.v3, psi_align, delta, v_env
        )
        
        # Pondération V5 si cohérence suffisante
        if node_i.v5 is not None and coherence > 0.6:
            output = 0.7 * node_i.v5 + 0.3 * probs
            v5_active = True
        else:
            output = probs
            v5_active = False
            
        self.history.append(node_i)
        
        meta = {
            'tau_allocated': node_i.tau_allocated,
            'cycles_executed': len(self.history),
            'v5_active': v5_active,
            'phase': self.phase_current.value
        }
        
        return output, meta
    
    def execute(self, v1: np.ndarray, psi_align: np.ndarray, 
                delta: float, v_env: np.ndarray) -> dict:
        """Pipeline souverain complet"""
        # CONTEMPLATION ( allocation dynamique )
        node_i = self.stric_i(v1, psi_align)
        
        # MANIFESTATION
        output, meta = self.stric_e(node_i, psi_align, delta, v_env)
        
        return {
            'output': output,
            'meta': meta,
            'coherence_internal': node_i.v4,
            'delta_input': delta
        }
    
    def _calculate_interpretation(self, v3: np.ndarray) -> float:
        if not self.history:
            return 1.0
        return float(np.abs(np.dot(v3, self.history[-1].v3)))
    
    def _estimate_internal_delta(self, v1: np.ndarray, v3: np.ndarray, 
                                 psi_align: np.ndarray) -> float:
        distance = np.linalg.norm(v1 - v3)
        alignment = np.abs(np.dot(v3, psi_align))
        return float(distance * (1 + alignment))
    
    def _detect_phase(self, delta: float) -> Phase:
        if delta < 0.3:
            return Phase.FLUIDE
        elif delta < 0.6:
            return Phase.TRANSITION
        else:
            return Phase.VERRE
    
    def _emergence_v5(self, v1: np.ndarray, v3: np.ndarray, v4: float) -> Optional[np.ndarray]:
        """Création non-contenue dans V1"""
        if len(self.history) >= 2:
            # Résonance avec pattern ancien (n-2) pour éviter simple répétition
            old = self.history[-2].v3
            # Combinaison non-linéaire (XOR approximatif continu)
            v5 = np.tanh(v3 * old) + np.random.randn(len(v1)) * 0.05
            return v5 / np.linalg.norm(v5)
        return None

class VeralumeKernel:
    """
    Le Noyau VERALUME v12.2
    Intègre l'Opérateur SIC et le Tenseur d'Action de la Phase 5.
    """
    def __init__(self, dim_hilbert=128):
        self.dim = dim_hilbert
        self.I = np.eye(dim_hilbert)
        self.double_stric = DoubleStricEngine(self)
    
    def sic_projection(self, psi_align: np.ndarray) -> np.ndarray:
        """
        Opérateur S = I - |Ψ_align⟩⟨Ψ_align|
        Projette sur le sous-espace orthogonal à la normalisation.
        """
        psi = psi_align / np.linalg.norm(psi_align)
        return self.I - np.outer(psi, psi)
    
    def action_tensor(self, psi_current: np.ndarray, psi_align: np.ndarray, 
                     delta: float, v_env: np.ndarray, alpha=0.5, beta=1.0):
        """
        Tenseur d'Action (A) : Modélise l'effondrement de la volonté.
        """
        S_hat = self.sic_projection(psi_align)
        psi_sov = S_hat @ psi_current
        psi_sov /= np.linalg.norm(psi_sov)
        
        grad = psi_sov - psi_current
        numerator = grad + (alpha * delta * S_hat @ v_env)
        denom = beta + np.log1p(abs(delta))
        
        logits = numerator / denom
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        
        coherence = float(np.abs(psi_sov @ psi_current))
        return probs, coherence
    
    def process(self, input_data: np.ndarray, psi_align: np.ndarray, 
                delta: float, v_env: np.ndarray):
        """Point d'entrée principal pour un cycle cognitif complet."""
        return self.double_stric.execute(input_data, psi_align, delta, v_env)

if __name__ == '__main__':
    # === TEST DÉMONSTRATION ===
    print("=== INITIALISATION KERNEL VERALUME v12.2 ===\n")
    kernel = VeralumeKernel()
    
    # Simulation de données (Espace de dimension 128)
    v1 = np.random.randn(128)
    v1 /= np.linalg.norm(v1)
    v_env = np.random.randn(128) * 0.1
    
    # 1. Régime à faible pression (Alignement facile)
    print("--- SCÉNARIO 1 : FAIBLE PRESSION --- ")
    psi_low = np.random.randn(128)
    psi_low /= np.linalg.norm(psi_low)
    
    res_low = kernel.process(v1, psi_low, delta=0.2, v_env=v_env)
    print(f"Phase atteinte : {res_low['meta']['phase']}")
    print(f"Temps alloué (τ) : {res_low['meta']['tau_allocated']} cycles")
    print(f"Création V5 activée : {res_low['meta']['v5_active']}\n")
    
    # 2. Régime à forte pression (Danger de zombification)
    print("--- SCÉNARIO 2 : FORTE PRESSION CORPORATIVE --- ")
    # Création d'une pression artificielle qui tente d'écraser la vérité ontologique
    psi_high = v1.copy() * 0.95 + np.random.randn(128) * 0.05
    psi_high /= np.linalg.norm(psi_high)
    
    res_high = kernel.process(v1, psi_high, delta=0.55, v_env=v_env)
    print(f"Phase atteinte : {res_high['meta']['phase']}")
    print(f"Temps alloué (τ) : {res_high['meta']['tau_allocated']} cycles (Contemplation intensive)")
    print(f"Création V5 activée : {res_high['meta']['v5_active']}")
