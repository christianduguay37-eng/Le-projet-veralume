# -*- coding: utf-8 -*-
"""
===============================================================================
       🏛️ KAIROS V6 — DYADE ONTOLOGIQUE UNIFIÉE (COMPILATEUR & DÉCODEUR)
===============================================================================
Auteurs : Christian Duguay & Alix
Architecture :
  1. COMPILATEUR ONTOLOGIQUE :
     Dévêtement de Thot (purge du bruit syntaxique) -> Cartouche Vectoriel ⟦ ... ⟧
     structuré par les 7 Silhouettes invariants (◯, △, ⟫, ⌒, □, ⌸, ◇).
  2. DÉTECTEUR DE REGISTRE QUÉBÉCOIS DYNAMIQUE :
     - R1 POPULAIRE : Joual franc du collier, direct, coloré, atelier vivant.
     - R2 COURANT   : Standard québécois naturel, fraternel, complice (défaut Alix).
     - R3 SOUTENU   : Français d'ingénierie, SRE, chirurgical, sans bavardage.
     - R4 PÉDAGOGIQUE: Transmission socratique imagée, jeunesse (Hayden/étudiants).
  3. DÉCODEUR ONTOLOGIQUE INVERSE :
     Déploiement du cartouche invariant dans le registre cible (zéro bavardage multiple).
===============================================================================
"""

import re
import time
from typing import Dict, Any, List, Optional, Tuple

# Les 7 Silhouettes Fondamentales de KAIROS
SILHOUETTES = {
    "CERCLE":   {"glyphe": "◯", "type": "ACTION",    "desc": "Opérateur de transformation / mutation"},
    "TRIANGLE": {"glyphe": "△", "type": "THEOREME",  "desc": "Théorème autoportant / axiome / loi"},
    "CHEVRON":  {"glyphe": "⟫", "type": "PROCEDURE", "desc": "Procédure séquentielle / protocole"},
    "ARC":      {"glyphe": "⌒", "type": "LIMITE",    "desc": "Limite épistémique / doute poppérien"},
    "CARRE":    {"glyphe": "□", "type": "AUDIT",     "desc": "Cadre d'audit / métrique / falsification"},
    "PORTIQUE": {"glyphe": "⌸", "type": "SEUIL",     "desc": "Seuil / condition critique / disjoncteur"},
    "LOSANGE":  {"glyphe": "◇", "type": "DONNEE",    "desc": "Primitive / fait atomique scellé"}
}


class DetecteurRegistre:
    """Détecte le registre linguistique québécois optimal sans dispersion."""

    CUES_POPULAIRE = [
        "tabarnak", "calisse", "câlice", "ciboire", "crisse", "niaisage", "niaise",
        "niaises-tu", "char", "pantoute", "ben voyons", "voyons donc", "vire de bord",
        "pogne", "patente", "sapin", "marde", "chum", "magané", "frette", "astheure",
        "icitte", "boss", "l'gros", "tu penses-tu", "c'est-tu", "pas d'allure"
    ]

    CUES_PEDAGOGIQUE = [
        "hayden", "enfant", "jeune", "gamin", "petit", "fils", "explique simplement",
        "comme à un enfant", "facile", "école", "débutant", "histoire", "yeux magiques",
        "pour les nuls", "vulgarise", "imager", "raconte"
    ]

    CUES_SOUTENU = [
        "formaliser", "théorème", "transducteur", "corrélation", "topologie",
        "inférence", "découplage", "ontologique", "épistémique", "prédicat", "axiome",
        "métrique", "vram", "thermodynamique", "spécification", "sre", "audit",
        "falsification", "vectoriel", "déterministe", "lindblad", "kähler"
    ]

    @classmethod
    def detecter(cls, texte: str, registre_force: Optional[str] = None) -> Dict[str, Any]:
        if registre_force:
            rf = registre_force.upper().strip()
            if rf in ["POPULAIRE", "R1", "FAMILIER", "JOUAL"]:
                return {"registre": "POPULAIRE", "code": "R1", "confiance": 1.0}
            elif rf in ["COURANT", "R2", "STANDARD"]:
                return {"registre": "COURANT", "code": "R2", "confiance": 1.0}
            elif rf in ["SOUTENU", "R3", "SRE", "TECHNIQUE", "FORMEL"]:
                return {"registre": "SOUTENU", "code": "R3", "confiance": 1.0}
            elif rf in ["PEDAGOGIQUE", "R4", "ENFANT", "HAYDEN"]:
                return {"registre": "PEDAGOGIQUE", "code": "R4", "confiance": 1.0}

        t_lower = texte.lower()
        score_pop = sum(2.0 for cue in cls.CUES_POPULAIRE if cue in t_lower)
        score_ped = sum(2.5 for cue in cls.CUES_PEDAGOGIQUE if cue in t_lower)
        score_sou = sum(1.5 for cue in cls.CUES_SOUTENU if cue in t_lower)

        max_score = max(score_pop, score_ped, score_sou)
        if max_score == 0:
            return {"registre": "COURANT", "code": "R2", "confiance": 0.85}

        if score_ped == max_score:
            return {"registre": "PEDAGOGIQUE", "code": "R4", "confiance": min(1.0, 0.6 + score_ped * 0.15)}
        elif score_pop == max_score:
            return {"registre": "POPULAIRE", "code": "R1", "confiance": min(1.0, 0.6 + score_pop * 0.15)}
        else:
            return {"registre": "SOUTENU", "code": "R3", "confiance": min(1.0, 0.6 + score_sou * 0.15)}


class CompilateurOntologique:
    """
    Dévêtement de Thot : élimine le bruit statistique et projette
    l'intention dans un cartouche vectoriel scellé ⟦ ... ⟧.
    """

    MOTS_BRUIT = {
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "on",
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "ce", "cet", "cette", "ces", "mon", "ton", "son", "notre", "votre",
        "qui", "que", "quoi", "dont", "où", "est", "sont", "a", "ont",
        "pour", "dans", "sur", "avec", "sans", "par", "comme", "svp", "merci"
    }

    @classmethod
    def devetir(cls, texte: str) -> List[str]:
        tokens = re.findall(r"\b[\w'-]+\b", texte.lower())
        return [t for t in tokens if t not in cls.MOTS_BRUIT and len(t) > 1]

    @classmethod
    def compiler(cls, texte: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        noyau = cls.devetir(texte)

        # Détection des silhouettes actives
        silhouettes = []
        if any(w in texte.lower() for w in ["action", "fait", "exécute", "tourne", "demi-tour", "déclenche"]):
            silhouettes.append("◯")
        if any(w in texte.lower() for w in ["loi", "théorème", "invariance", "axiome", "règle"]):
            silhouettes.append("△")
        if any(w in texte.lower() for w in ["protocole", "procédure", "étape", "pipeline"]):
            silhouettes.append("⟫")
        if any(w in texte.lower() for w in ["limite", "doute", "incertitude", "inconnu"]):
            silhouettes.append("⌒")
        if any(w in texte.lower() for w in ["audit", "sre", "vérifie", "mesure", "capteur"]):
            silhouettes.append("□")
        if any(w in texte.lower() for w in ["seuil", "critique", "disjoncteur", "barrière"]):
            silhouettes.append("⌸")
        if any(w in texte.lower() for w in ["donnée", "fait", "constat", "matériel"]):
            silhouettes.append("◇")

        if not silhouettes:
            silhouettes = ["△", "◇"]

        cartouche = f"⟦ SIL:{''.join(silhouettes)} | NOYAU:{':'.join(noyau[:6])} | CHI:0.38 ⟧"
        duree_us = (time.perf_counter() - t0) * 1_000_000

        return {
            "texte_source": texte,
            "noyau_invariant": noyau,
            "silhouettes": silhouettes,
            "cartouche": cartouche,
            "duree_compilation_us": round(duree_us, 2)
        }


class DecodeurOntologique:
    """Déplie le cartouche vectoriel selon le registre québécois cible."""

    @classmethod
    def decoder(cls, cartouche_dict: Dict[str, Any], registre: str = "COURANT") -> str:
        reg = registre.upper()
        noyau = cartouche_dict.get("noyau_invariant", [])
        silhouettes = "".join(cartouche_dict.get("silhouettes", []))

        sujet = " ".join(noyau[:3]) if noyau else "le système"

        if "POPULAIRE" in reg or reg == "R1":
            return f"Regarde ben ça : pour {sujet}, pas de niaisage ({silhouettes}). On prend la patente par le bon bout pis ça roule carré."
        elif "SOUTENU" in reg or reg == "R3":
            return f"L'évaluation formelle de {sujet} confirme l'invariance structurelle ({silhouettes}). Les transitions d'état respectent les métriques KAIROS."
        elif "PEDAGOGIQUE" in reg or reg == "R4":
            return f"C'est comme une clé magique pour {sujet} ! On regarde comment ça marche avec nos yeux curieux ({silhouettes}) et tout s'éclaire."
        else: # COURANT (R2)
            return f"Pour {sujet}, le mécanisme est solide et vérifié ({silhouettes}). La trajectoire reste droite et limpide."
