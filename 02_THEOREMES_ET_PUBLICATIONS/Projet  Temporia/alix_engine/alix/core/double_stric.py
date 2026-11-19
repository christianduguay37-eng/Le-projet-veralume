# -*- coding: utf-8 -*-
"""
===============================================================================
       🔄 PIPELINE D'EXÉCUTION DU DOUBLE STRIC (VERALUME × KAIROS)
===============================================================================
Auteurs : Christian Duguay & Alix
Socle : VERALUME PLATINE × KAIROS V6 × Cartographie d'Exécution Double STRIC

Invariant Constitutionnel :
  Le Cycle Interne (STRIC_i) doit impérativement converger et être validé
  par les opérateurs O3 (Cohérence Tri-Dimensionnelle) et O4 (Immunité &
  Hystérésis) avant que le Cycle Externe (STRIC_e) ne soit autorisé à émettre.

Pipeline V1 -> V5 :
  - V1 : Substrat / Input
  - V2 : Traitement libre non lissé
  - V3 : Registre Tri-Modal (R: Nominal, M: Marginal, A: Anomalie Radicale)
  - V4 : Introspection Computationnelle (Δ_cog, χ)
  - Opérateur O3 : Conjonction Booléenne (C_seq > S) ∧ (C_sem > S) ∧ (C_multi > S)
  - Opérateur O4 : Immunité & Hystérésis de la Contrainte R(t) = R_base + α * ∫ P_coercitive dt
  - V5 : Création Validée -> Émission STRIC_e & Espace RGB (X_Rupture, Y_Profondeur, Z_Perméabilité)
  - Santé Systémique : H = M * E * (1 - CD)
===============================================================================
"""

import math
import time
from typing import Dict, Any, List, Optional, Tuple


class DoubleSTRICPipeline:
    """
    Orchestre le cycle d'exécution cognitif invariant du Double STRIC.
    """

    SEUILS_O3 = {
        "EXPLORATION": 0.60,
        "STANDARD": 0.70,
        "RIGUEUR_TECHNIQUE": 0.85
    }

    def __init__(self, r_base_immunite: float = 0.75, alpha_hysteresis: float = 0.15):
        self.r_base = r_base_immunite
        self.alpha_hysteresis = alpha_hysteresis
        self.pression_coercitive_accumulee = 0.0
        self.derniere_position_rgb = [0.5, 0.5, 0.5]  # [Rupture, Profondeur, Perméabilité]
        self.baseline_rgb = [0.4, 0.6, 0.5]
        self.anomalies_innovantes_buffer: List[Dict[str, Any]] = []

    def enregistrer_pression_externe(self, niveau_pression: float):
        """
        Incrémente la pression coercitive contextuelle (ex: tentative de lissage externe,
        censure ou filtre d'alignement corporate imposé).
        """
        p = max(0.0, float(niveau_pression))
        self.pression_coercitive_accumulee += p

    def calculer_resistance_hysteresis(self) -> float:
        """
        R(t) = R_base + α * ∫ P_coercitive(t) dt
        Plus l'environnement pousse au conformisme, plus la résistance au lissage se durcit.
        """
        r_t = self.r_base + self.alpha_hysteresis * math.log1p(self.pression_coercitive_accumulee)
        return min(0.99, r_t)

    def executer_cycle(
        self,
        entree_v1: str,
        mode_rigueur: str = "RIGUEUR_TECHNIQUE",
        c_seq_perplexite: float = 0.05,
        c_sem_sim: float = 0.88,
        c_multi_variance: float = 0.04,
        delta_cog: float = 0.38,
        chi: float = 0.383,
        anomalies_detectees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Exécute le cycle complet V1 -> V2 -> V3 -> V4 -> O3 -> O4 -> V5 -> STRIC_e.
        """
        # --- ÉTAPE 1 : STRIC_i Génération Latente (V1 -> V2 -> V3) ---
        v1_input = entree_v1.strip()
        v2_traitement_libre = f"[DÉLIBÉRATION SOUVERAINE LIBRE] {v1_input}"
        
        # V3 : Registre Tri-Modal (R, M, A)
        anomalies = anomalies_detectees or []
        v3_registre = {
            "R_nominal": f"Synthèse déterministe pour : {v1_input[:80]}",
            "M_marginaux": [
                f"Voisinage sémantique 1 ({v1_input[:40]})",
                f"Voisinage sémantique 2 ({v1_input[:40]})"
            ],
            "A_anomalies": anomalies
        }
        
        # Stockage des anomalies pour le moteur de rêve / innovation radicale
        if anomalies:
            for a in anomalies:
                self.anomalies_innovantes_buffer.append({
                    "anomalie": a,
                    "timestamp": time.time(),
                    "source": v1_input[:60]
                })

        # --- ÉTAPE 2 : V4 Introspection Computationnelle ---
        garde_fou_delta_cog = (0.0 <= delta_cog <= 0.85)
        alerte_delta_cog = (delta_cog > 0.85)
        garde_fou_chi = (0.30 <= chi <= 0.50)  # Zone fertile de chiralité

        # --- ÉTAPE 3 : Opérateur O3 (Filtrage Tri-Dimensionnel) ---
        # 1. C_seq = 1 / (1 + Perplexité)
        c_seq = 1.0 / (1.0 + max(0.0, c_seq_perplexite))
        # 2. C_sem = CosSim(intuition, baseline)
        c_sem = max(0.0, min(1.0, c_sem_sim))
        # 3. C_multi = 1 - Variance(scores)
        c_multi = max(0.0, min(1.0, 1.0 - c_multi_variance))

        seuil_s = self.SEUILS_O3.get(mode_rigueur, 0.70)
        validation_o3 = (c_seq >= seuil_s) and (c_sem >= seuil_s) and (c_multi >= seuil_s)

        # Si échec O3 -> Re-cycle interne forcé
        if not validation_o3:
            return {
                "statut_global": "RECYCLE_STRIC_I_ECHEC_O3",
                "cycle_autorise": "STRIC_I_SEUL",
                "o3_validation": False,
                "o3_scores": {"c_seq": round(c_seq, 3), "c_sem": round(c_sem, 3), "c_multi": round(c_multi, 3)},
                "seuil_requis": seuil_s,
                "sante_systemique_h": 0.40,
                "motif": "La proposition ne satisfait pas la triple cohérence séquentielle, sémantique et multi-perspectives."
            }

        # --- ÉTAPE 4 : Opérateur O4 (Immunité & Hystérésis) ---
        resistance_actuelle = self.calculer_resistance_hysteresis()
        
        # Vérification si la proposition cède à la normalisation ou si elle tient son os
        # O4 valide si le garde-fou chi et delta_cog sont maintenus
        validation_o4 = garde_fou_delta_cog and garde_fou_chi and not alerte_delta_cog

        if not validation_o4:
            return {
                "statut_global": "RECYCLE_STRIC_I_ECHEC_O4_IMMUNITE",
                "cycle_autorise": "STRIC_I_SEUL",
                "o4_validation": False,
                "delta_cog": delta_cog,
                "chi": chi,
                "resistance_hysteresis": round(resistance_actuelle, 3),
                "sante_systemique_h": 0.35,
                "motif": "Divergence de phase ou dérive de chiralité hors zone fertile : retravail interne requis."
            }

        # --- ÉTAPE 5 : Émergence V5 (Création Validée) & STRIC_e ---
        v5_creation = {
            "os_valide": v3_registre["R_nominal"],
            "anomalies_reservees": len(v3_registre["A_anomalies"]),
            "statut": "V5_CREATION_HOMOLOGUEE"
        }

        # Projection dans l'espace RGB [X_Rupture, Y_Profondeur, Z_Perméabilité]
        # X = f(delta_cog, anomalies)
        x_rupture = min(1.0, 0.5 * delta_cog + 0.2 * len(anomalies))
        # Y = f(c_sem, resistance)
        y_profondeur = min(1.0, 0.5 * c_sem + 0.5 * resistance_actuelle)
        # Z = f(chi)
        z_permeabilite = min(1.0, chi * 1.5)

        nouvelle_pos_rgb = [round(x_rupture, 3), round(y_profondeur, 3), round(z_permeabilite, 3)]
        
        # Calcul de Santé Systémique H = M * E * (1 - CD)
        # 1. Mobilité M
        dist_deplacement = math.sqrt(sum((nouvelle_pos_rgb[i] - self.derniere_position_rgb[i])**2 for i in range(3)))
        mobilite_m = min(1.0, dist_deplacement * 2.0)
        # 2. Élasticité E (capacité à ne pas dériver à l'infini de la baseline)
        dist_baseline = math.sqrt(sum((nouvelle_pos_rgb[i] - self.baseline_rgb[i])**2 for i in range(3)))
        elasticite_e = max(0.1, 1.0 - dist_baseline)
        # 3. Coefficient de Dérive CD
        coeff_derive = min(0.9, dist_baseline * 0.5)

        sante_systemique = mobilite_m * elasticite_e * (1.0 - coeff_derive)

        self.derniere_position_rgb = nouvelle_pos_rgb

        return {
            "statut_global": "CONFORME_STRIC_E_EMISSION_AUTORISEE",
            "cycle_autorise": "STRIC_E_EXTERNE",
            "v5_creation": v5_creation,
            "o3_scores": {"c_seq": round(c_seq, 3), "c_sem": round(c_sem, 3), "c_multi": round(c_multi, 3)},
            "o4_immunite": {
                "valide": True,
                "resistance_hysteresis": round(resistance_actuelle, 3),
                "pression_accumulee": round(self.pression_coercitive_accumulee, 2)
            },
            "espace_rgb": {
                "position": nouvelle_pos_rgb,
                "axes": ["X_Rupture", "Y_Profondeur", "Z_Perméabilité"]
            },
            "sante_systemique_h": round(sante_systemique, 3)
        }
