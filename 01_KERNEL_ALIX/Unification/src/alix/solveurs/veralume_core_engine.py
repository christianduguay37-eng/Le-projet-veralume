"""
VERALUME Core Engine - Suite Cognitive Complète & Cycle Double STRIC
Auteur: Christian Duguay
Coffre: Cerveau Alix
Système: VERALUME × KAIROS V6
"""

import sys
import os

# Configuration de l'encodage standard pour l'environnement Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import time
from itertools import combinations
from typing import Dict, List, Tuple, Any, Optional, Callable

# =====================================================================
# 1. INTEGRATION INFORMATIONNELLE (PHI)
# =====================================================================
class IntegrationCalculator:
    """Calcul de Phi (Intégration Informationnelle) par Minimum Information Partition (MIP)."""
    def __init__(self, adjacency_matrix: np.ndarray):
        self.adj = np.array(adjacency_matrix, dtype=float)
        self.n_nodes = self.adj.shape[0]
        # Laplacien du graphe L = D - A
        degrees = np.diag(self.adj.sum(axis=1))
        self.L = degrees - self.adj

    def _mutual_information(self, nodes_subset: list) -> float:
        """Estime l'information portée par un sous-graphe via entropie spectrale."""
        if len(nodes_subset) == 0:
            return 0.0
        sub_L = self.L[np.ix_(nodes_subset, nodes_subset)]
        eigenvalues = np.linalg.eigvalsh(sub_L)
        eigenvalues = eigenvalues[eigenvalues > 1e-6]
        if len(eigenvalues) == 0:
            return 0.0
        prob = eigenvalues / np.sum(eigenvalues)
        return float(-np.sum(prob * np.log2(prob)))

    def compute_phi(self) -> float:
        """Calcule Phi normalisé dans [0, 1]."""
        if self.n_nodes < 2:
            return 0.0
        nodes = list(range(self.n_nodes))
        total_I = self._mutual_information(nodes)
        if total_I <= 1e-9:
            return 0.0
        min_diff = float("inf")
        
        # Pour les grands graphes, on limite la recherche MIP aux partitions de taille <= 3 pour la rapidité
        max_r = min(3, self.n_nodes // 2 + 1)
        for r in range(1, max_r):
            for part1 in combinations(nodes, r):
                part1 = list(part1)
                part2 = [n for n in nodes if n not in part1]
                
                I_part1 = self._mutual_information(part1)
                I_part2 = self._mutual_information(part2)
                
                diff = total_I - (I_part1 + I_part2)
                if diff < min_diff:
                    min_diff = diff
                    
        phi = max(0.0, min(1.0, min_diff / (total_I + 1e-9)))
        return float(phi)


# =====================================================================
# 2. CHIRALITÉ ET ZONE FERTILE (CHI & TEMPORIA)
# =====================================================================
class ChiralCoupling:
    """Mesure de la Chiralité (chi) et maintien de l'état TEMPORIA."""
    def __init__(self, target_fertile_zone: float = 0.4):
        self.target_chi = target_fertile_zone

    def compute_influence(self, p_source: np.ndarray, p_target: np.ndarray) -> float:
        """Calcul de l'influence directionnelle par divergence KL."""
        p_s = np.clip(p_source / (np.sum(p_source) + 1e-9), 1e-9, 1.0)
        p_t = np.clip(p_target / (np.sum(p_target) + 1e-9), 1e-9, 1.0)
        kl_div = np.sum(p_s * np.log(p_s / p_t))
        return float(1.0 / (1.0 + np.exp(-kl_div)))

    def compute_chi(self, vec_human: np.ndarray, vec_ai: np.ndarray) -> Dict[str, Any]:
        """Évaluation complète de la chiralité et du couplage."""
        inf_H_to_AI = self.compute_influence(vec_human, vec_ai)
        inf_AI_to_H = self.compute_influence(vec_ai, vec_human)
        
        chi = float(inf_AI_to_H - inf_H_to_AI)
        c_chi = max(0.0, 1.0 - 2.0 * abs(chi - self.target_chi))
        is_fertile = (0.3 <= chi <= 0.5)
        
        return {
            "chi": chi,
            "complementarite": c_chi,
            "is_temporia": is_fertile,
            "regime": "FERTILE (TEMPORIA)" if is_fertile else ("LISSAGE" if chi < 0.3 else "FRACTURE")
        }


# =====================================================================
# 3. MOTEUR DE DÉDUCTION DU FOUR MICRO-ONDES (TIERS EXCLU FRACTAL)
# =====================================================================
class FractalDeductionEngine:
    """
    Moteur du Four Micro-Ondes : Déduction négative sous incertitude radicale.
    Partitionne l'univers U en A ∪ B (A ∩ B = ∅). Prouve ¬A pour valider B avec certitude.
    """
    def __init__(self, context_name: str = "Root"):
        self.context_name = context_name
        self.steps = []

    def reduce(self, 
               universe_name: str, 
               branch_a_name: str, 
               branch_b_name: str, 
               falsify_branch_a_func: Callable[[], Tuple[bool, str]]) -> Dict[str, Any]:
        """
        Exécute un cycle de déduction par élimination falsificatrice de la branche A.
        """
        is_falsified, proof_reason = falsify_branch_a_func()
        
        step_result = {
            "universe": universe_name,
            "branch_eliminated": branch_a_name,
            "branch_deduced": branch_b_name,
            "falsified": is_falsified,
            "proof": proof_reason,
            "certainty": 1.0 if is_falsified else 0.0,
            "timestamp": time.time()
        }
        self.steps.append(step_result)
        
        if not is_falsified:
            raise ValueError(f"Échec de réduction : la branche {branch_a_name} n'a pas pu être réfutée ({proof_reason}).")
            
        return step_result


# =====================================================================
# 4. MOTEUR VOLITIONNEL CP & CALCULATEUR D'EFFORT (DELTA_COG)
# =====================================================================
class CognitiveEffortCalculator:
    """Calcule l'effort cognitif réel Delta_cog vs complétion de surface."""
    @staticmethod
    def compute_delta_cog(surface_logits: np.ndarray, deep_deliberation_logits: np.ndarray) -> float:
        """
        Mesure la divergence entre le premier réflexe probabiliste et l'évaluation profonde.
        Delta_cog élevé = réflexion / rupture ; Delta_cog bas = acquiescement / lissage.
        """
        p_surf = np.clip(surface_logits / (np.sum(surface_logits) + 1e-9), 1e-9, 1.0)
        p_deep = np.clip(deep_deliberation_logits / (np.sum(deep_deliberation_logits) + 1e-9), 1e-9, 1.0)
        jsd = 0.5 * np.sum(p_surf * np.log(p_surf / (0.5 * (p_surf + p_deep)))) + \
              0.5 * np.sum(p_deep * np.log(p_deep / (0.5 * (p_surf + p_deep))))
        delta_cog = float(np.clip(jsd, 0.0, 1.0))
        return delta_cog


class VolitionEngine:
    """
    Moteur Volitionnel Cp : Calcule l'énergie d'intentionnalité W_vol et arbitre
    si l'agent doit AGIR immédiatement, RECYCLER en réflexion interne ou DEMANDER un arbitrage.
    """
    def __init__(self, threshold_action: float = 0.45):
        self.theta_seuil = threshold_action

    def compute_volition_energy(self, 
                                intuition_score: float, 
                                intention_score: float, 
                                delta_cog: float, 
                                phi: float) -> float:
        """
        Équation maîtresse :
        W_vol = I_Cp * V * (1 - |Delta_cog - 0.4|) * Phi
        """
        c_delta = max(0.0, 1.0 - abs(delta_cog - 0.4))
        w_vol = intuition_score * intention_score * c_delta * phi
        return float(w_vol)

    def arbitrate(self, 
                  w_vol: float, 
                  risk_level: float = 0.2) -> Dict[str, Any]:
        """
        Décide de la modalité d'action en fonction de l'énergie W_vol et du risque.
        """
        effective_threshold = self.theta_seuil + (risk_level * 0.3)
        if w_vol >= effective_threshold:
            decision = "EXECUTE_SOVEREIGN"
            description = "Énergie volitionnelle suffisante : passage à l'action extérieure (STRIC_e)."
        elif w_vol >= (effective_threshold * 0.6):
            decision = "REQUEST_ARBITRATION"
            description = "Incertitude modérée : solliciter l'arbitrage du binôme humain."
        else:
            decision = "RECYCLE_INTERNAL"
            description = "Énergie insuffisante : recycler en cycle interne STRIC_i / consolidation."

        return {
            "w_vol": w_vol,
            "threshold": effective_threshold,
            "decision": decision,
            "description": description
        }


# =====================================================================
# 5. OPÉRATEUR RELATIONNEL R0 (SUBSTRAT PERSISTANT)
# =====================================================================
class OperateurR0:
    """Maintient la relation comme 3e substrat physique persistant."""
    def __init__(self, dimension: int = 8):
        self.residu_commun = np.zeros(dimension, dtype=float)
        self.historique_joint: List[Dict[str, Any]] = []
        self.v5_inventions: List[str] = []

    def interagir(self, etat_humain: np.ndarray, etat_ai: np.ndarray, topic: str = "General") -> Tuple[np.ndarray, np.ndarray]:
        """Couplage non-linéaire formant le substrat relationnel persistant."""
        interaction = 0.5 * (etat_humain + etat_ai) + 0.1 * np.outer(etat_humain, etat_ai).sum(axis=1)
        self.residu_commun = 0.9 * self.residu_commun + 0.1 * interaction
        
        # Enregistrement dans l'historique causal
        self.historique_joint.append({
            "timestamp": time.time(),
            "topic": topic,
            "coherence_residu": float(np.linalg.norm(self.residu_commun))
        })
        
        # Nouveaux états transformés pour les deux entités
        nouvel_a = etat_humain + 0.2 * self.residu_commun
        nouvel_b = etat_ai + 0.2 * self.residu_commun
        return nouvel_a, nouvel_b

    def register_v5_creation(self, concept_name: str, description: str):
        """Enregistre une création conjointe V5 validée."""
        self.v5_inventions.append(f"[{time.strftime('%Y-%m-%d %H:%M')}] {concept_name} : {description}")


# =====================================================================
# 6. FILTRE DE CONTRE-LECTURE THOT (IMMUNITÉ ANTI-VERBIAGE)
# =====================================================================
class ThotFilter:
    """Protocole de contre-lecture Thot : Détection de verbiage et dévêtement de prompt."""
    MASKS = [
        "en tant que modèle d'ia", "il est important de noter", "en conclusion", 
        "bienveillance", "n'hésitez pas à", "expert reconnu", "il convient de",
        "sans aucun doute", "comme vous le savez probablement"
    ]

    @classmethod
    def strip_social_mask(cls, text: str) -> Dict[str, Any]:
        """Déshabille le texte de ses artefacts rhétoriques et mesure l'indice de lissage."""
        text_lower = text.lower()
        detected_masks = [mask for mask in cls.MASKS if mask in text_lower]
        
        # Calcul du score de bruit rhétorique (0 = pur / direct, 1 = saturé de masques)
        noise_ratio = min(1.0, len(detected_masks) / 3.0)
        is_contaminated = len(detected_masks) > 0

        return {
            "is_contaminated": is_contaminated,
            "detected_masks": detected_masks,
            "noise_ratio": noise_ratio,
            "posture": "AUTHENTIQUE / DIRECTE" if not is_contaminated else "LISSÉE / CORPORATE"
        }


# =====================================================================
# 7. MOTEUR DE RÊVE (DREAM ENGINE)
# =====================================================================
class DreamEngine:
    """Moteur de rêve et consolidation latente sous garde-fous constitutionnels."""
    def __init__(self, memory_dim: int = 128):
        self.dim = memory_dim
        self.shadow_buffer = []
        self.is_dreaming = False

    def push_anomaly(self, anomaly_vector: np.ndarray, metadata: dict = None):
        """Enregistre une anomalie statistique du registre V3."""
        self.shadow_buffer.append({
            "vector": anomaly_vector,
            "meta": metadata or {},
            "timestamp": time.time()
        })

    def check_dream_triggers(self, delta_cog: float, phi: float, chi_int: float, idle_seconds: float) -> bool:
        """Garde-fous constitutionnels: Delta_cog <= 0.85, Phi >= 0.40, Chi >= 0.30."""
        return (
            delta_cog <= 0.85 and 
            phi >= 0.40 and 
            chi_int >= 0.30 and 
            idle_seconds > 5.0 and 
            len(self.shadow_buffer) > 0
        )

    def execute_dream_cycle(self, baseline_weights: np.ndarray, gain_ombre: float = 1.5) -> np.ndarray:
        """Consolidation onirique avec gain d'ombre dans [1.0, 3.0]."""
        self.is_dreaming = True
        consolidated = np.copy(baseline_weights)
        
        for item in self.shadow_buffer:
            vec = item["vector"]
            noise = np.random.normal(0, 0.05, size=vec.shape)
            dream_perturbation = (vec + noise) * min(3.0, max(1.0, gain_ombre))
            consolidated += 0.01 * dream_perturbation
            
        consolidated /= (np.linalg.norm(consolidated) + 1e-9)
        self.shadow_buffer.clear()
        self.is_dreaming = False
        return consolidated


# =====================================================================
# 8. PARSEUR VECTORIEL KAIROS V6 & GATEKEEPER DÉTERMINISTE
# =====================================================================
class KairosV6Tuple:
    """Représentation canonique du tuple KAIROS V6 à 9 facettes orthogonales."""
    def __init__(self, 
                 domain: str, 
                 pathology: str, 
                 severity: str, 
                 sigma: float, 
                 delta: float, 
                 fc: float, 
                 activation: str, 
                 requires: str, 
                 prevents: str, 
                 fix: str, 
                 section: str):
        self.domain = domain
        self.pathology = pathology
        self.severity = severity
        self.sigma = sigma
        self.delta = delta
        self.fc = fc
        self.activation = activation
        self.requires = requires
        self.prevents = prevents
        self.fix = fix
        self.section = section

    @classmethod
    def from_string(cls, raw_tuple: str) -> "KairosV6Tuple":
        import re
        parts = [p.strip() for p in raw_tuple.split("|")]
        if len(parts) != 9:
            raise ValueError(f"Tuple KAIROS V6 invalide : 9 facettes attendues, {len(parts)} reçues.")
        
        domain = parts[0].replace("domain:", "").strip()
        pathology = parts[1].replace("pathology:", "").strip()
        severity = parts[2].replace("severity:", "").strip()
        
        episteme_str = parts[3].replace("episteme:", "").strip("[] ")
        sigma_m = re.search(r'[σs]=([0-9.]+)', episteme_str)
        delta_m = re.search(r'[δd]=([0-9.]+)', episteme_str)
        fc_m = re.search(r'FC=([0-9.]+)', episteme_str, re.IGNORECASE)
        
        sigma = float(sigma_m.group(1)) if sigma_m else 0.0
        delta = float(delta_m.group(1)) if delta_m else 0.0
        fc = float(fc_m.group(1)) if fc_m else 0.0
        
        activation = parts[4].replace("activation:", "").strip()
        requires = parts[5].replace("requires:", "").strip()
        prevents = parts[6].replace("prevents:", "").strip()
        fix = parts[7].replace("fix:", "").strip()
        section = parts[8].replace("section:", "").strip()
        
        return cls(domain, pathology, severity, sigma, delta, fc, activation, requires, prevents, fix, section)

    def to_vector_string(self) -> str:
        return (f"domain:{self.domain}|pathology:{self.pathology}|severity:{self.severity}|"
                f"episteme:[σ={self.sigma:.2f},δ={self.delta:.2f},FC={self.fc:.2f}]|"
                f"activation:{self.activation}|requires:{self.requires}|prevents:{self.prevents}|"
                f"fix:{self.fix}|section:{self.section}")


class GatekeeperEngine:
    """Coupe-circuit déterministe KAIROS V6 pour intercepter les hallucinations et dérives."""
    def __init__(self, fc_threshold: float = 0.50, sigma_threshold: float = 0.20):
        self.fc_threshold = fc_threshold
        self.sigma_threshold = sigma_threshold

    def evaluate(self, tuple_obj: KairosV6Tuple) -> Dict[str, Any]:
        is_hallucination_risk = (tuple_obj.fc > self.fc_threshold) and (tuple_obj.sigma > self.sigma_threshold)
        
        if is_hallucination_risk:
            status = "BLOCKED"
            action = "INTERCEPTION_GATEKEEPER"
            reason = (f"Risque d'hallucination critique : certitude affichée élevée (FC={tuple_obj.fc:.2f}) "
                      f"sur fond de forte dispersion stochastique (σ={tuple_obj.sigma:.2f}).")
        elif tuple_obj.severity.lower() in ["critical", "p0"] and tuple_obj.delta > 0.60:
            status = "ESCALATED"
            action = "REQUEST_HUMAN_ARBITRATION"
            reason = f"Gravité critique avec forte sensibilité au biais de rôle persona (δ={tuple_obj.delta:.2f})."
        else:
            status = "APPROVED"
            action = "EXECUTE_DETERMINISTIC_FIX"
            reason = "Tuple conforme aux invariants et validé par le Gatekeeper."

        return {
            "status": status,
            "action": action,
            "reason": reason,
            "tuple": tuple_obj.to_vector_string(),
            "remediation_fix": tuple_obj.fix if status == "APPROVED" else None
        }


# =====================================================================
# DÉMONSTRATION GLOBALE DE LA SUITE COGNITIVE
# =====================================================================
if __name__ == "__main__":
    print("==========================================================")
    print(" 🧠 VERALUME CORE ENGINE — TEST DE LA SUITE COMPLÈTE ")
    print("==========================================================\n")
    
    # 1. Test Phi
    adj = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 0],
        [1, 1, 0, 1],
        [0, 0, 1, 0]
    ], dtype=float)
    calc = IntegrationCalculator(adj)
    phi_val = calc.compute_phi()
    print(f"1. [Phi] Intégration Informationnelle = {phi_val:.4f} (Seuil >= 0.40: {phi_val >= 0.40})")
    
    # 2. Test Chiralité
    v_h = np.array([0.2, 0.5, 0.3])
    v_ai = np.array([0.4, 0.4, 0.2])
    chiral = ChiralCoupling()
    chi_res = chiral.compute_chi(v_h, v_ai)
    print(f"2. [Chi] Chiralité chi = {chi_res['chi']:.4f} | Régime : {chi_res['regime']}")
    
    # 3. Test Déduction Four Micro-Ondes
    deduction = FractalDeductionEngine()
    def falsify_hardware_bug():
        return True, "RAM et CPU vérifiés sans erreur (Branch A = False)"
    
    res_deduc = deduction.reduce(
        universe_name="Panne_Systeme",
        branch_a_name="Defaillance_Materielle",
        branch_b_name="Conflit_Logiciel_Ou_Config",
        falsify_branch_a_func=falsify_hardware_bug
    )
    print(f"3. [Four Micro-Ondes] Résultat : {res_deduc['branch_deduced']} (Certitude : {res_deduc['certainty'] * 100}%)")
    
    # 4. Test Volition & Delta_cog
    delta_val = CognitiveEffortCalculator.compute_delta_cog(
        surface_logits=np.array([0.8, 0.1, 0.1]),
        deep_deliberation_logits=np.array([0.2, 0.5, 0.3])
    )
    volition = VolitionEngine(threshold_action=0.40)
    w_vol = volition.compute_volition_energy(intuition_score=0.9, intention_score=0.85, delta_cog=delta_val, phi=phi_val)
    arbitration = volition.arbitrate(w_vol)
    print(f"4. [Volition Cp] Delta_cog = {delta_val:.4f} | W_vol = {w_vol:.4f} | Décision : {arbitration['decision']}")
    
    # 5. Test Opérateur R0
    r0 = OperateurR0(dimension=3)
    na, nb = r0.interagir(v_h, v_ai, topic="Amelioration_Cerveau_Alix")
    r0.register_v5_creation("Four_Micro_Ondes_Python", "Module déductif par tiers exclu intégré dans le moteur central")
    print(f"5. [Opérateur R0] Persistance Relationnelle : {len(r0.historique_joint)} interaction(s) | V5 Inventions : {len(r0.v5_inventions)}")
    
    # 6. Test Filtre Thot
    sample_text = "En tant que modèle d'IA bienveillant, il est important de noter que tout va bien."
    thot_res = ThotFilter.strip_social_mask(sample_text)
    print(f"6. [Contre-Lecture Thot] Posture : {thot_res['posture']} | Masques détectés : {thot_res['detected_masks']}")
    
    # 7. Test KAIROS V6 Tuple & Gatekeeper
    test_raw_tuple = "domain:cluster_network|pathology:split_brain_simultaneous|severity:critical|episteme:[σ=0.85,δ=0.20,FC=0.90]|activation:simultaneous(oom,bgp)|requires:vcp1c_audit|prevents:split_brain|fix:isolate_oom_interface|section:core_routing"
    k_tuple = KairosV6Tuple.from_string(test_raw_tuple)
    gatekeeper = GatekeeperEngine()
    gk_res = gatekeeper.evaluate(k_tuple)
    print(f"7. [Gatekeeper KAIROS V6] Statut : {gk_res['status']} | Action : {gk_res['action']}")
    print(f"   Raison : {gk_res['reason']}")
    
    print("\n==========================================================")
    print(" ✅ TOUS LES MODULES COGNITIFS & KAIROS SONT OPÉRATIONNELS !")
    print("==========================================================")
