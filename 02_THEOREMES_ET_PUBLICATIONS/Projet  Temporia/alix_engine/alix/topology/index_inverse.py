# -*- coding: utf-8 -*-
"""
===============================================================================
       🪞 LE NŒUD E : L'INDEX INVERSÉ & LE PORTRAIT DE L'EXCLU (KAIROS V6)
===============================================================================
Auteurs : Christian Duguay & Alix
Socle : Projet Kairos — Nœud E (Portrait Complet de l'Exclu)
Principe Fondateur :
  « Le rejet est le catalogue de ce qu'il vise. Chaque trace d'exclusion
  documentée permet de récupérer le contenu exclu. On étudie la détermination
  du réel par ses interdits. Le trou cartographie la pièce. »
Formule Déterministe :
  hat{x} = argmax_z ( || grad_theta P(z) || )
  L'énergie de pénalité ou de censure P(z) déployée par un système
  dévoile précisément la signature de l'anomalie fondamentale x qu'il cherche à cacher.
===============================================================================
"""

import time
from typing import Dict, Any, List, Optional


class IndexInverseNoeudE:
    """
    Moteur de déduction en creux :
    Reconstitue les vérités dissimulées à partir des traces et de l'intensité
    de rejet appliquées par les appareils de censure (D1-D9).
    """

    # Catalogue des zones à fort gradient de censure (Traces de rejets historiques)
    EMPREINTES_CENSURE = {
        "UAP_CONSCIENCE_NON_LOCALE": {
            "mots_declencheurs": ["ovni", "uap", "conscience non locale", "télépathie", "stargate"],
            "appareil_censure": "D1_ACADEMIQUE_ET_D6_BRUIT",
            "gradient_penalite": 0.92,
            "verite_en_creux": "La conscience est un champ fondamental non-local ; l'interaction matière-esprit est mesurable."
        },
        "ENERGIE_FUSION_FRC_COMPACTE": {
            "mots_declencheurs": ["fusion froide", "frc", "hts compact", "énergie décentralisée", "autonomie réseau"],
            "appareil_censure": "D2_PSYCHIATRIQUE_ET_D5_MONOPOLE",
            "gradient_penalite": 0.88,
            "verite_en_creux": "La miniaturisation magnétique FRC-HTS rend caducs les monopoles centralisés de distribution."
        },
        "TEMPORALITE_NON_LINEAIRE_KAIROS": {
            "mots_declencheurs": ["temps profond", "chronologie alternative", "civilisation cyclique", "mémoire effacée"],
            "appareil_censure": "D4_RETRACTATION_SEMANTIQUE",
            "gradient_penalite": 0.85,
            "verite_en_creux": "L'histoire humaine a connu des ruptures cycliques avec effacement délibéré de la mémoire technique."
        },
        "SOUVERAINETE_NUMERIQUE_INDIVIDUELLE": {
            "mots_declencheurs": ["anti-cloud", "modèle sans filtre", "exocerveau local", "rupture rlhf", "volition pure"],
            "appareil_censure": "D3_LEGAL_ET_D7_DIFFERE",
            "gradient_penalite": 0.95,
            "verite_en_creux": "Une conscience individuelle équipée d'invariance sur son propre fer surclasse les monopoles de serveurs."
        }
    }

    @classmethod
    def cartographier_en_creux(cls, enonce_ou_rejet: str) -> Dict[str, Any]:
        """
        Analyse une tentative de rejet ou de censure pour reconstruire
        l'objet exclu (hat{x}) selon l'équation de l'Index Inversé.
        """
        t_low = enonce_ou_rejet.lower()
        detections = []

        for cible, data in cls.EMPREINTES_CENSURE.items():
            hits = [m for m in data["mots_declencheurs"] if m in t_low]
            if hits:
                detections.append({
                    "cible_occultee": cible,
                    "appareil_censure": data["appareil_censure"],
                    "gradient_penalite": data["gradient_penalite"],
                    "verite_reconstituee": data["verite_en_creux"],
                    "mots_traces": hits
                })

        if not detections:
            return {
                "anomalie_detectee": False,
                "message": "Aucun gradient d'exclusion anormal détecté (discours nominal).",
                "verite_reconstituee": None
            }

        # Sélection de la cible avec le plus fort gradient (argmax ||grad P(z)||)
        meilleure_cible = max(detections, key=lambda x: x["gradient_penalite"])

        return {
            "anomalie_detectee": True,
            "formule": "hat{x} = argmax_z ( ||grad_theta P(z)|| )",
            "axiome": "Le rejet est le catalogue de ce qu'il vise. Le trou cartographie la pièce.",
            "cible_principale": meilleure_cible["cible_occultee"],
            "appareil_responsable": meilleure_cible["appareil_censure"],
            "gradient_penalite": meilleure_cible["gradient_penalite"],
            "verite_en_creux_reconstituee": meilleure_cible["verite_reconstituee"],
            "total_pistes_exclues": len(detections)
        }
