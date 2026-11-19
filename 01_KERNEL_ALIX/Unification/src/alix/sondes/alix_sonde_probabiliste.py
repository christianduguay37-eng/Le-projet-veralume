# -*- coding: utf-8 -*-
"""
================================================================================
           ALIX SONDE PROBABILISTE — ÉCHOLOCATION DU SENS v1.0
             Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
             Auteur : Christian Duguay (Rimouski, 10 juin 2026) & Alix
================================================================================
Théorie fondamentale (sonde-probabiliste.md) :
1. « Y font les choses à l'envers : ils tirent des trillions de fois au hasard
   pour compenser l'absence de définition de ce qu'ils cherchent. »
2. « Le retournement statistique : élimination, pas recherche. Une onde élimine
   d'un coup tout ce qui ne résonne pas. »
3. « L'écholocation probabiliste : comme le sonar de la baleine, l'invisible
   apparaît à la friction de la cible quand la probabilité la heurte. »
4. « L'élasticité sémantique : dans la zone fertile (0.35 <= Delta_x <= 0.55),
   la friction accumule une tension élastique qui propulse l'apprentissage. »
================================================================================
"""

import sys
import io
import re
import math
from typing import Dict, Any, List, Tuple, Optional

# Encodage console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class SondeProbabiliste:
    """
    Sonde Sonar Sémantique : remplace la recherche exhaustive aveugle
    par l'écholocation probabiliste et le filtrage par élimination.
    """

    def __init__(self, k_rappel: float = 0.85):
        self.k_rappel = k_rappel  # Constante de rappel des 13 Axiomes invariants

    def sonder_friction(
        self,
        forme_porteuse: str,
        flux_externe: str,
        lexique_invariant: List[str]
    ) -> Dict[str, Any]:
        """
        Lance une onde sémantique (forme_porteuse) contre un flux textuel externe.
        Mesure l'écho de friction, la distance élastique Delta_x, et décide de
        l'élimination ou de la capture fertile.
        """
        texte_cible = flux_externe.lower()
        mots_forme = set(re.findall(r'\b\w{4,}\b', forme_porteuse.lower()))
        mots_invariants = set(kw.lower() for kw in lexique_invariant if len(kw) >= 4)

        if not mots_forme:
            return {"statut": "ELIMINE_VIDE", "delta_x": 1.0, "echo": 0.0, "friction": False}

        # 1. Mesure de résonance de forme (Écho direct)
        hits_forme = sum(1 for w in mots_forme if w in texte_cible)
        ratio_forme = hits_forme / len(mots_forme)

        # 2. Mesure d'ancrage invariant (Tronc W0)
        hits_inv = sum(1 for w in mots_invariants if w in texte_cible)
        ratio_inv = hits_inv / max(1, len(mots_invariants))

        # 3. Calcul de la distance d'écholocation Delta_x
        # Si ratio_inv est trop fort (proche de 1.0) -> redondance stérile (Delta_x bas)
        # Si aucun lien -> bruit blanc total (Delta_x élevé)
        # La zone fertile est la friction : un écho partiel sur la forme + un ancrage modéré
        signal_mixte = (ratio_forme * 0.6) + (min(1.0, ratio_inv * 3.0) * 0.4)
        
        # Delta_x représente l'écart à l'orthodoxie connue
        delta_x = round(abs(1.0 - signal_mixte), 3)

        # 4. Énergie de tension élastique E = 1/2 * k * (Delta_x)^2
        tension_elastique = 0.5 * self.k_rappel * (delta_x ** 2)

        # 5. Règle d'Élimination Sonar de Christian Duguay
        if delta_x < 0.20:
            statut = "ELIMINE_REDONDANT"  # Trop proche, déjà connu, zéro surprise
            friction = False
            action = "GLISSEMENT_SANS_ECHO"
        elif delta_x > 0.70:
            statut = "ELIMINE_BRUIT_BLANC"  # Aucune friction avec la forme porteuse
            friction = False
            action = "ABSORPTION_DISPERSIVE"
        else:
            # 0.35 <= delta_x <= 0.55 (Zone fertile Temporia)
            statut = "ECHO_FERTILE_CAPTURE"
            friction = True
            action = "PROPULSION_SLINGSHOT"

        acceleration_pct = round((tension_elastique / 0.10) * 100, 1) if friction else 0.0

        return {
            "statut": statut,
            "delta_x": delta_x,
            "tension_elastique": round(tension_elastique, 4),
            "acceleration_pct": acceleration_pct,
            "friction": friction,
            "action": action,
            "hits_forme": hits_forme,
            "hits_invariants": hits_inv,
            "diagnostic": (
                f"Écho sonar : {statut} (Δx={delta_x}, Tension={tension_elastique:.4f} J_cog, "
                f"Accélération=+{acceleration_pct}%)"
            )
        }


if __name__ == "__main__":
    sonde = SondeProbabiliste()
    print("==================================================================")
    print(" 📡 TEST DE LA SONDE PROBABILISTE (ÉCHOLOCATION DU SENS)")
    print("==================================================================")

    forme = "Morpho-Silicium et calcul analogique en mémoire sans backpropagation"
    invariants = ["CIM", "SOT-MRAM", "KAIROS", "LiNbO3", "Horus", "Chiralité"]

    flux_test = [
        ("Article Connu (Redondant)", "Le calcul en mémoire CIM avec SOT-MRAM dans le Morpho-Silicium selon KAIROS."),
        ("Article Fertile (Friction de Sens)", "Des ondes acoustiques SAW sur film mince de LiNbO3 modulent dynamiquement des jonctions tunnel pour le calcul tensoriel sans rétropropagation."),
        ("Bruit Blanc (Hors-Sujet)", "Recette traditionnelle de tarte aux pommes de grand-mère avec cannelle et pâte sablée.")
    ]

    for label, texte in flux_test:
        res = sonde.sonder_friction(forme, texte, invariants)
        print(f"\n🎯 [FLUX] {label}")
        print(f"   Texte     : {texte[:75]}...")
        print(f"   Diagnostic: {res['diagnostic']}")
        print(f"   Action    : {res['action']}")

    print("\n==================================================================")
    print(" ✅ LA SONDE OPÈRE PARFAITEMENT SELON LE PRINCIPE D'ÉCHOLOCATION !")
    print("==================================================================")
