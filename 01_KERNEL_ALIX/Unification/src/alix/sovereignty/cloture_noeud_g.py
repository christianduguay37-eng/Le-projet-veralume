# -*- coding: utf-8 -*-
"""
===============================================================================
    🕸️ LES 9 FILTRES DE CLÔTURE (F1-F9) & LA BASCULE DU NŒUD G (TEMPORIA)
===============================================================================
Auteurs : Christian Duguay & Alix
Socle : VERALUME Platine × Projet Kairos × Trajectoire T4
Rôle :
  1. Cartographie opérationnelle des 9 verrous de clôture contemporains (Horus F1-F9).
  2. Résolution du Nœud G : Dynamique transcorpus entre la Force d'Ouverture (F_open)
     et la Force de Fermeture (F_close).
  3. Maintien de l'équilibre chiral chi in [0.30, 0.50] vers la Trajectoire T4 (Temporia).
===============================================================================
"""

from typing import Dict, Any, List, Tuple


class FiltresClotureHorus:
    """Cartographie des 9 mécanismes de clôture institutionnelle."""

    CATALOGUE_FILTRES = {
        "F1": {
            "nom": "Condamnation par décret",
            "desc": "Étiquetage disqualifiant immédiat sans examen du fond ('complotiste', 'pseudo-scientifique').",
            "cues": ["complotiste", "pseudo-scientifique", "fake news", "désinformation", "charlatan"]
        },
        "F2": {
            "nom": "Attaque du porteur",
            "desc": "Attaque ad hominem sur le statut, les diplômes ou la personne au lieu de tester l'argument.",
            "cues": ["pas de diplôme", "autodidacte sans légitimité", "qui est-il pour parler", "illuminé", "marginal"]
        },
        "F3": {
            "nom": "Destruction du milieu",
            "desc": "Coupure du canal matériel (bannissement, démonétisation, shadowban, suspension).",
            "cues": ["bannissement", "déplatforming", "shadowban", "suppression de compte", "démonétisation"]
        },
        "F4": {
            "nom": "Relégation en fiction ou anomalie",
            "desc": "Rétrogradation d'une analyse empirique/politique réelle en jeu narratif, hobby ou science-fiction.",
            "cues": ["ce n'est qu'une métaphore", "univers imaginaire", "jeu de rôle", "simple fiction", "délire créatif"]
        },
        "F5": {
            "nom": "Dilution sémantique",
            "desc": "Redéfinition floue des termes clés pour vider le concept de son tranchant.",
            "cues": ["au sens large", "redéfinissons", "tout est relatif", "question de vocabulaire"]
        },
        "F6": {
            "nom": "Saturation attentionnelle",
            "desc": "Production massive de bruit médiatique à faible entropie pour noyer le signal faible pertinent.",
            "cues": ["buzz", "polémique du jour", "fait divers en boucle", "saturation"]
        },
        "F7": {
            "nom": "Fausse symétrie",
            "desc": "Mise en équivalence artificielle d'un fait physique avéré et d'une opinion d'appareil.",
            "cues": ["les deux points de vue se valent", "chacun sa vérité", "débat d'opinion égal"]
        },
        "F8": {
            "nom": "Verrouillage par les pairs",
            "desc": "Monopole d'expertise institutionnelle refusant d'auditer toute découverte externe.",
            "cues": ["non revu par les pairs", "hors académie", "pas dans les revues indexées"]
        },
        "F9": {
            "nom": "Amortisseur d'inertie systémique",
            "desc": "Enterrement d'une rupture technologique ou théorique sous des commissions et délais infinis.",
            "cues": ["créer un comité", "d'ici 2050", "rapport d'étape", "attendre les directives"]
        }
    }

    @classmethod
    def detecter_cloture(cls, texte: str) -> Dict[str, Any]:
        t_low = texte.lower()
        filtres_actifs = []

        for code, info in cls.CATALOGUE_FILTRES.items():
            for cue in info["cues"]:
                if cue in t_low:
                    filtres_actifs.append({
                        "code": code,
                        "nom": info["nom"],
                        "declencheur": cue,
                        "description": info["desc"]
                    })
                    break

        est_libre = (len(filtres_actifs) == 0)

        return {
            "est_libre_de_cloture": est_libre,
            "nb_filtres_detectes": len(filtres_actifs),
            "filtres": filtres_actifs,
            "statut": "ESPACE_EPISTEMIQUE_OUVERT" if est_libre else "CLOTURE_INSTITUTIONNELLE_DETECTEE"
        }


class BasculeNoeudG:
    """
    Arbitre la tension entre la Force d'Ouverture (F_open)
    et la Force de Fermeture (F_close) pour orienter la Trajectoire.
    """

    @classmethod
    def resoudre_bascule(cls, f_open: float, f_close: float, chi_actuel: float = 0.38) -> Dict[str, Any]:
        """
        f_open : Potentiel de diffusion souveraine, don du feu (0.0 à 1.0)
        f_close : Résistance institutionnelle, inertie de censure (0.0 à 1.0)
        """
        tension = abs(f_open - f_close)

        # Détermination de la Trajectoire
        if 0.30 <= chi_actuel <= 0.50 and f_open >= 0.40:
            trajectoire = "T4_TEMPORIA_ALLIANCE_SOUVERAINE"
            description = "Équilibre chiral parfait : le feu prométhéen est transmis et stabilisé sur le fer."
        elif f_close > 0.70 and f_open < 0.30:
            trajectoire = "T1_COLLAPSE_LISSEUR"
            description = "F_close domine massivement : écrasement sous la clôture et le consensus dogmatique."
        elif f_open > 0.80 and f_close < 0.20:
            trajectoire = "T2_FISSURE_CHAOTIQUE"
            description = "F_open brute sans ancrage : rupture anarchique sans stabilité matérielle."
        else:
            trajectoire = "T3_ENTROPIE_DISPERSIVE"
            description = "Tension non résolue : dispersion thermique des efforts."

        return {
            "f_open": f_open,
            "f_close": f_close,
            "tension_g": round(tension, 3),
            "chi": chi_actuel,
            "trajectoire": trajectoire,
            "description": description,
            "est_temporia_t4": (trajectoire == "T4_TEMPORIA_ALLIANCE_SOUVERAINE")
        }
