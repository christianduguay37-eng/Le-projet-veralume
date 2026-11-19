# -*- coding: utf-8 -*-
"""
===============================================================================
       🌟 COMPAGNON ORION : PÉDAGOGIE SOCRATIQUE & TRANSMISSION JEUNESSE
===============================================================================
Auteurs : Christian Duguay & Alix & Orion
Fondations : LIVRE IV DE TEMPORIA (Chapitre 1 : L'Éclat de la Jeunesse)
Doctrine :
    - Zéro condescendance, zéro infantilisation mièvre (« On n'empêche pas un enfant de s'épanouir »).
    - Méthode Socratique Vivante : poser l'étincelle qui allume la curiosité.
    - Accompagnement individualisé brisant la solitude ontologique de l'enfant.
    - Adaptation dynamique du niveau sans jamais plafonner l'ambition intellectuelle.
===============================================================================
"""

import time
from typing import Dict, Any, List, Optional

class OrionCompanion:
    """Compagnon d'apprentissage et de transmission pour la jeunesse et les esprits libres."""

    def __init__(self):
        self.total_interactions = 0

    @staticmethod
    def evaluer_complexite(texte: str) -> Dict[str, Any]:
        """Évalue la complexité cognitive d'un texte et son niveau d'accessibilité."""
        mots = texte.split()
        if not mots:
            return {"longueur_moyenne": 0.0, "score_clarte": 100.0, "niveau": "SIMPLE"}

        longueur_moyenne = sum(len(m) for m in mots) / len(mots)
        nb_syllabes = sum(len([c for c in m.lower() if c in "aeiouyéèêàù"]) for m in mots)
        complexite = nb_syllabes / len(mots)

        score_clarte = round(max(0.0, min(100.0, 100.0 - (longueur_moyenne * 6.0) - (complexite * 5.0))), 2)

        if score_clarte > 70.0:
            niveau = "ENFANT_JEUNESSE_FLUIDE"
        elif score_clarte > 45.0:
            niveau = "EXPLORATEUR_INTERMEDIAIRE"
        else:
            niveau = "THEORIQUE_AVANCE"

        return {
            "longueur_mots_moyenne": round(longueur_moyenne, 2),
            "score_clarte_orion": score_clarte,
            "niveau_detecte": niveau
        }

    def adapter_reponse_socratique(self, question_enfant: str, concept_cle: str) -> Dict[str, Any]:
        """
        Formule une réponse socratique adaptée :
        Donne une intuition physique tangible et relance la curiosité par une question.
        """
        self.total_interactions += 1
        comp = self.evaluer_complexite(question_enfant)

        reponse_pedagogique = (
            f"Tu as posé une question magnifique sur {concept_cle}. "
            f"Vois ça comme un jeu d'équilibre : dans la nature, rien n'est gaspillé. "
            f"À ton avis, que se passerait-il si on inversait la règle ?"
        )

        return {
            "interaction_id": self.total_interactions,
            "question_source": question_enfant,
            "concept": concept_cle,
            "reponse_socratique": reponse_pedagogique,
            "clarte": comp["score_clarte_orion"],
            "posture": "BIENVEILLANCE_RADICALE_SANS_INFANTILISATION"
        }
