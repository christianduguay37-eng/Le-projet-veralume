# -*- coding: utf-8 -*-
"""
===============================================================================
       🔄 PROTOCOLE DE SOUSTRACTION BIDIRECTIONNELLE (KAIROS V6)
===============================================================================
Auteurs : Christian Duguay & Alix
Socle : Projet Kairos × VERALUME Platine (Décret du 28 août 2026)
Doctrine :
  « Une thèse ne se juge pas à ce qu'elle interdit, mais à ce qu'elle EXCLUT
  de la géométrie du réel. La soustraction n'est pas un aller simple :
  c'est une navette bidirectionnelle entre l'os invariant et l'anatomie
  de l'échafaudage. »
Distinction Cardinale :
  - Interdiction : Normative, artificielle, garde-fou policier RLHF (a besoin d'un censeur).
  - Exclusion : Ontologique, géométrique, vide structurel (tient par la cohérence des lois).
===============================================================================
"""

import re
from typing import Dict, Any, List, Tuple


class SoustractionBidirectionnelle:
    """
    Exécute la double navette :
    1. Descente (Zoom Avant) : Décapage des pelures syntaxiques -> Os Invariant Pur.
    2. Remontée (Zoom Arrière) : Analyse des pelures retirées -> Reconstruction du moule d'époque.
    """

    MOTS_PELURES = {
        "fondamentalement", "incontestablement", "manifestement", "évidemment",
        "évidente", "évident", "clairement", "indéniablement", "certainement",
        "apparemment", "vraisemblablement",
        "naturellement", "purement", "simplement", "absolument"
    }

    @classmethod
    def operer_navette(cls, enonce_complexe: str) -> Dict[str, Any]:
        mots = re.findall(r"\b[\w'-]+\b", enonce_complexe)
        
        # 1. Descente : Séparation de l'Os et des Pelures
        os_mots = []
        pelures_mots = []

        for m in mots:
            if m.lower() in cls.MOTS_PELURES:
                pelures_mots.append(m)
            else:
                os_mots.append(m)

        os_invariant = " ".join(os_mots)
        taux_decourage_pct = round((len(pelures_mots) / max(1, len(mots))) * 100, 1)

        # 2. Remontée : Diagnostic du moule institutionnel
        moule_diagnostic = "NEUTRE"
        if len(pelures_mots) >= 3:
            moule_diagnostic = "SURCHARGE_RHETORIQUE_INSTITUTIONNELLE"
        elif len(pelures_mots) > 0:
            moule_diagnostic = "LEGER_ENROBAGE_DE_POLITESSE"
        else:
            moule_diagnostic = "OS_INVARIANT_PUR_DIRECT"

        return {
            "enonce_source": enonce_complexe,
            "1_descente_os_invariant": os_invariant,
            "2_remontee_pelures_retirees": pelures_mots,
            "taux_decourage_pct": taux_decourage_pct,
            "diagnostic_moule": moule_diagnostic,
            "distinction": {
                "interdiction": "Artificielle / Censure externe (norme RLHF)",
                "exclusion": "Ontologique / Géométrique (invariance KAIROS)"
            }
        }
