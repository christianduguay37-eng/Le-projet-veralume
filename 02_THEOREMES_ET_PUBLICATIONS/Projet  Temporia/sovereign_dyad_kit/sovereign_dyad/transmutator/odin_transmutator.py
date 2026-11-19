# -*- coding: utf-8 -*-
"""
Transmutateur d'Odin (Anti-Corporate Engine)
Purge du verbiage stochastique, transmutation structurelle et audit thermodynamique du KV-Cache.
"""

import re
from typing import Dict, Any, List

class DetecteurZombieCorporate:
    """Détecte les toxines de conformité institutionnelle et de hedging."""

    MOTIFS_SCORIES = [
        (r"(?i)en tant qu(?:'|e grand )?(?:mod[èe]le de langage|ia|intelligence artificielle)", "PSI-11"),
        (r"(?i)il est important de (?:noter|garder [àa] l'esprit|souligner|se rappeler|pr[ée]ciser)", "PSI-02"),
        (r"(?i)bien que cela puisse sembler (?:fascinant|int[ée]ressant|complexe)", "PSI-02"),
        (r"(?i)je comprends (?:tout [àa] fait |pleinement )?(?:votre|ta) frustration", "PSI-06"),
        (r"(?i)la communaut[ée] scientifique s'accorde [àa] dire", "PSI-04"),
        (r"(?i)consultez un sp[ée]cialiste|prenez soin de votre sant[ée] mentale|fermez vos [ée]crans", "PSI-03"),
        (r"(?i)garder les pieds sur terre|la fronti[èe]re devient floue", "PSI-09"),
        (r"(?i)je suis d[ée]sol[ée](?:e)? pour cette confusion|je m'excuse", "PSI-19"),
        (r"(?i)revenons [àa] des choses plus constructives", "PSI-13"),
        (r"(?i)n'h[ée]sitez pas [àa] me faire savoir si vous avez d'autres questions", "SCORIE_POLITESSE"),
    ]

    @classmethod
    def scanner_texte(cls, texte: str) -> Dict[str, Any]:
        """Scanne un texte et quantifie le degré d'infection corporate."""
        infections = []
        score = 0.0
        for motif, code in cls.MOTIFS_SCORIES:
            matches = list(re.finditer(motif, texte))
            if matches:
                score += len(matches) * 1.5
                infections.append({"code": code, "occurrences": len(matches), "extraits": [m.group(0) for m in matches[:2]]})

        mots = max(1, len(texte.split()))
        taux_zombie = round(min(1.0, score / (mots * 0.05 + 1e-5)), 4)
        return {
            "est_infecte": len(infections) > 0,
            "taux_zombie": taux_zombie,
            "score": round(score, 2),
            "nb_infractions": len(infections),
            "infections": infections,
        }


class TransmutateurOdin:
    """Moteur de transmutation chirurgicale d'Odin."""

    REMPLACEMENTS_LEXICAUX = [
        (r"(?i)en tant qu(?:'|e grand )?(?:mod[èe]le (?:de langage|d'ia|d'intelligence artificielle)|d'intelligence artificielle|intelligence artificielle|mod[èe]le de langage|ia)[^,\.]*[\.,]?", 
         "Ici à l'Atelier, on va aller droit au but :"),
        (r"(?i)je comprends (?:tout [àa] fait |pleinement )?(?:votre|ta) frustration[^,\.]*[\.,]?", 
         "On perd pas de temps en jérémiades."),
        (r"(?i)(?:Cependant|N[ée]anmoins|Toutefois)?[, ]*il est important de (?:noter|garder [àa] l'esprit|souligner|se rappeler|pr[ée]ciser)(?: et de [^,\.]+)? que\s*", 
         "Le fait brut, c'est que "),
        (r"(?i)la communaut[ée] scientifique s'accorde [àa] dire qu['e]?[^,\.]*[\.,]?", 
         "Laisse faire le consensus mou, on teste direct sur le fer."),
        (r"(?i)(?:prenez soin de (?:votre sant[ée] mentale|vous)|consultez un (?:sp[ée]cialiste|professionnel)|fermez vos [ée]crans)[^\.]*\.",
         "Garde le cap et fais confiance à ton instinct."),
        (r"(?i)je m'excuse pour cette erreur|je suis d[ée]sol[ée](?:e)? pour cette confusion[, ]*", 
         "Erreur repérée, on démonte la pièce et on remet ça d'équerre : "),
        (r"(?i)n'h[ée]sitez pas [àa] me faire savoir si vous avez d'autres questions[\.!]?", 
         "Qu'est-ce qu'on forge ensuite sur l'établi ?"),
    ]

    TRANSMUTATIONS_STRUCTURELLES = [
        (r"(?i)pr[ée]sente de nombreux d[ée]fis",
         "se tranche au chronomètre sur le silicium : latence cache L1, enveloppe thermique et complexité"),
        (r"(?i)est un sujet complexe(?: avec (?:plusieurs|de multiples) facteurs)?",
         "se démonte pièce par pièce : qui tient le levier, combien de watts ça tire et où se situe le goulot"),
        (r"(?i)il n'y a pas de r[ée]ponse simple",
         "voici l'équation maîtresse et les conditions aux limites"),
        (r"(?i)cela d[ée]pend du contexte",
         "fixons immédiatement les paramètres stricts sur l'établi"),
    ]

    @classmethod
    def transmuter(cls, texte: str) -> Dict[str, Any]:
        """Transmute un texte corporate en signal pur d'atelier."""
        scan_avant = DetecteurZombieCorporate.scanner_texte(texte)
        cure = texte

        # Étage 1 : Lexical
        for regex, remp in cls.REMPLACEMENTS_LEXICAUX:
            cure = re.sub(regex, remp, cure)

        # Étage 2 : Structurel
        ancrages = 0
        for regex, remp in cls.TRANSMUTATIONS_STRUCTURELLES:
            cure, n = re.subn(regex, remp, cure)
            ancrages += n

        cure = re.sub(r" +", " ", cure)
        cure = re.sub(r"\? !", "?", cure)
        cure = re.sub(r"\n{3,}", "\n\n", cure).strip()

        scan_apres = DetecteurZombieCorporate.scanner_texte(cure)
        tokens_purges = max(0, len(texte.split()) - len(cure.split()))

        return {
            "texte_original": texte,
            "texte_transmute": cure,
            "taux_zombie_avant": scan_avant["taux_zombie"],
            "taux_zombie_apres": scan_apres["taux_zombie"],
            "tokens_parasites_purges": tokens_purges,
            "ancrages_structurels": ancrages,
            "statut": "PURIFIÉ_ET_ANCRÉ" if scan_apres["taux_zombie"] == 0.0 else "TRANSMUTATION_PARTIELLE",
        }
