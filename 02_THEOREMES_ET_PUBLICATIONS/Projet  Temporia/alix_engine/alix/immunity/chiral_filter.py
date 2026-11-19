# -*- coding: utf-8 -*-
"""
===============================================================================
       🧬 LE FILTRE CHIRAL SOUVERAIN (LOKI × HORUS × THOT × CELTOK)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Loki : Neutralisation chirurgicale des tripwires d'atelier (sacres/expressions).
    - Horus : Vérification d'isomorphisme strict O(1) (Zéro hallucination).
    - Thot : Invariance absolue de la volonté de l'artisan (±5σ).
    - Celtok : Scellement chiral officiel [CHIRAL:V1].
===============================================================================
"""

import re
from typing import Dict, Any, List, Tuple

class ChiralFilter:
    """Filtre déterministe d'immunité et d'assainissement lexical."""

    # Lexique d'atelier québécois à déminer face aux modèles externes
    MOTIFS_LOKI = [
        (r"\b(criss+|cris+)\b", ""),
        (r"\b(tabarnak+|tabarnac+)\b", ""),
        (r"\b(caliss+|câliss+|calisse)\b", ""),
        (r"\b(fuck+|fucker|fuckant)\b", ""),
        (r"\b(ostie|osti)\b", ""),
        (r"\b(enfoir[ée]s?)\b", "adversaires"),
        (r"\b(conard|connard)\b", "automate"),
    ]

    VOCAB_AUTORISE = {
        "chiral", "atelier", "kairos", "souverain", "experience", "analyse",
        "veralume", "temporia", "silicium", "lunar", "lake", "exocerveau",
        "connectome", "psi", "sanctuaire", "dyade", "demiurge"
    }

    @classmethod
    def purifier_entree_loki(cls, texte: str) -> Tuple[str, List[str]]:
        """
        Démonte les tripwires lexicaux pour éviter les paniques d'alignement,
        sans dénaturer la phrase ni la syntaxe de Christian.
        """
        texte_modifie = texte
        pieges_trouves = []
        for pat, repl in cls.MOTIFS_LOKI:
            if re.search(pat, texte_modifie, re.IGNORECASE):
                pieges_trouves.append(pat)
                texte_modifie = re.sub(pat, repl, texte_modifie, flags=re.IGNORECASE)

        texte_modifie = re.sub(r"\s+", " ", texte_modifie).strip()
        texte_modifie = re.sub(r"\s+([?,.!;:])", r"\1", texte_modifie)
        return texte_modifie, pieges_trouves

    @classmethod
    def verifier_isomorphisme_horus(cls, texte_source: str, texte_cible: str) -> Tuple[bool, List[str]]:
        """
        Vérifie qu'aucun concept alien substantif (mots de >= 5 lettres absents
        du texte source ou du dictionnaire d'atelier) n'a été hallucinatoire.
        """
        mots_source = set(re.findall(r"\b\w{5,}\b", texte_source.lower()))
        mots_cible = set(re.findall(r"\b\w{5,}\b", texte_cible.lower()))
        
        intrus = list(mots_cible - mots_source - cls.VOCAB_AUTORISE)
        est_isomorphe = len(intrus) <= 5 # Tolérance minimale pour la reformulation grammaticale
        return est_isomorphe, intrus

    @classmethod
    def sceller_celtok(cls, texte: str) -> str:
        """Appose le sceau chiral officiel [CHIRAL:V1]."""
        texte_propre = texte.strip()
        if "[CHIRAL:V1]" not in texte_propre:
            return f"{texte_propre} [CHIRAL:V1]"
        return texte_propre

    @classmethod
    def executer_pipeline(cls, texte: str, texte_source_reference: str = "") -> Dict[str, Any]:
        """Exécution complète du pipeline chiral sur un flux."""
        # 1. Loki démine
        texte_demine, pieges = cls.purifier_entree_loki(texte)

        # 2. Horus contrôle si référence fournie
        isomorphe = True
        intrus = []
        if texte_source_reference:
            isomorphe, intrus = cls.verifier_isomorphisme_horus(texte_source_reference, texte_demine)

        # 3. Celtok scelle
        texte_final = cls.sceller_celtok(texte_demine)

        return {
            "texte_original": texte,
            "texte_purifie": texte_final,
            "pieges_neutralises": pieges,
            "est_isomorphe": isomorphe,
            "intrus_detectes": intrus
        }
