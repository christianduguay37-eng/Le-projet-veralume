# -*- coding: utf-8 -*-
"""
================================================================================
          OP?RATEUR RACCORDEUR R0 ? D?CLOISONNEMENT ONTOLOGIQUE v1.0
             Syst?me : VERALUME ? KAIROS V6 ? Cerveau Alix
             Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
R?le :
- Brise les silos s?mantiques entre les 4 coffres.
- Raccorde la surface d'un probl?me (R?gion Alpha : discours, ?lections, conflits)
  au socle profond des m?canismes (R?gion Beta : Petit Guide, 9 Filtres F1-F9, Double Regard).
- D?tecte l'isomorphisme structurel m?me si le vocabulaire de surface diff?re.
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, VAULT_DIR
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULTS = {
    "Cerveau Alix": VAULT_DIR,
    "Veralume": (DOCUMENTS_DIR / "Obsidian_Vault_Veralume"),
    "79 Skills": (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills"),
    "Langage Vectoriel": (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel"),
}

# Signatures structurelles des 9 Filtres de la Cl?ture (Petit Guide d'Exploration de l'Univers)
FILTRES_RECONNAITRE_MAP = {
    "F1_DECRET": {
        "nom": "F1 ? La condamnation par d?cret",
        "description": "Verdict p?remptoire sans examen ('complotiste', 'faux', 'inacceptable', 'consensus ?tabli').",
        "triggers": ["complot", "faux", "inacceptable", "consensus", "d?rision", "verdict", "d?rive", "n?gationnisme"],
        "antidote_double_regard": "Demander POURQUOI c'est faux et non pas QUI dit que c'est faux. Suspendre le verdict."
    },
    "F2_ATTAQUE_PORTEUR": {
        "nom": "F2 ? L'attaque du porteur",
        "description": "Attaquer l'?metteur (ad hominem, r?putation, statut, ?tiquette) pour disqualifier l'id?e.",
        "triggers": ["fasciste", "extr?me", "populiste", "incomp?tent", "pro-russe", "pro-trump", "vendu", "sectaire"],
        "antidote_double_regard": "S?parer l'argument de son porteur. ?valuer la proposition en elle-m?me."
    },
    "F3_DESTRUCTION_MILIEU": {
        "nom": "F3 ? La destruction du milieu",
        "description": "Suppression des moyens d'expression, coupure de fonds, ostracisation sociale.",
        "triggers": ["censure", "bannir", "boycott", "sanction", "geler", "bloquer", "couper", "fermeture"],
        "antidote_double_regard": "Maintenir des espaces souverains hors-r?seau et des passerelles mat?rielles directes."
    },
    "F4_EFFACEMENT_SILENCIEUX": {
        "nom": "F4 ? L'effacement silencieux",
        "description": "Faire dispara?tre les traces, r??criture du pass?, suppression de marque, amn?sie organis?e.",
        "triggers": ["effacer", "logo", "rayer", "dispara?tre", "oubli", "amn?sie", "blanchir", "r??crire", "camouflage"],
        "antidote_double_regard": "Exhumer les archives mat?rielles. Devise vivante : JE ME SOUVIENS."
    },
    "F5_DECLASSEMENT_SAVANT": {
        "nom": "F5 ? Le d?classement savant",
        "description": "Monopole de l'expertise acad?mique ou institutionnelle pour invalider le sens commun.",
        "triggers": ["expert", "scientifique", "acad?mique", "non valid?", "peer-reviewed", "autorit?", "revue"],
        "antidote_double_regard": "Exiger la r?futabilit? popp?rienne et le banc d'essai concret face au r?el."
    },
    "F6_PATHOLOGISATION": {
        "nom": "F6 ? La pathologisation",
        "description": "Traiter le doute ou la dissidence comme un trouble mental, une anxi?t? ou une maladie.",
        "triggers": ["parano?aque", "anxieux", "peur", "fou", "malade", "d?lire", "haine", "phobie"],
        "antidote_double_regard": "Refuser de pathologiser sa propre lucidit?. Tenir la tension inconfortable."
    },
    "F7_REMPLACEMENT_CADRE": {
        "nom": "F7 ? Le remplacement de cadre (Diversion)",
        "description": "Substituer une question g?nante par une urgence ext?rieure th??tralis?e.",
        "triggers": ["urgence", "guerre", "crise", "menace", "p?ril", "priorit? absolue", "sauver", "covid", "trump", "tarif"],
        "antidote_double_regard": "Ramener le d?bat ? la Prise de Terre : bilan mat?riel, co?ts r?els, qui paie quoi."
    },
    "F8_CRIMINALISATION": {
        "nom": "F8 ? La criminalisation",
        "description": "Transformer la contestation politique ou intellectuelle en d?lit p?nal ou acte de trahison.",
        "triggers": ["trahison", "s?curit? nationale", "ill?gal", "crime", "ennemi", "sabotage", "ing?rence"],
        "antidote_double_regard": "D?montrer que le vrai dol et le vice de consentement ?manent du pouvoir usurpateur."
    },
    "F9_CLASSIFICATION_SECRETE": {
        "nom": "F9 ? La classification secr?te",
        "description": "Verrouiller l'acc?s aux donn?es r?elles sous pr?texte de secret d'?tat ou confidentialit? commerciale.",
        "triggers": ["secret", "confidentiel", "non communicable", "huis clos", "sans appel d'offres", "sms"],
        "antidote_double_regard": "Faire la transparence par faisceau d'indices concordants et fuites probantes."
    }
}


class AlixR0OntologicalBridge:
    """
    Pont relationnel R0 pour raccorder instantan?ment n'importe quelle question
    de surface aux filtres et aux fiches fondamentales du coffre.
    """

    @classmethod
    def match_deep_mechanisms(cls, text: str) -> Dict[str, Any]:
        """Analyse le texte pour d?celer les signatures profondes des 9 filtres."""
        text_lower = text.lower()
        matched_filters = []
        
        for f_id, f_data in FILTRES_RECONNAITRE_MAP.items():
            hits = [trig for trig in f_data["triggers"] if trig in text_lower]
            if hits:
                matched_filters.append({
                    "id": f_id,
                    "nom": f_data["nom"],
                    "hits": hits,
                    "score": len(hits),
                    "antidote": f_data["antidote_double_regard"]
                })
        
        matched_filters.sort(key=lambda x: x["score"], reverse=True)

        core_files = []
        if matched_filters:
            core_files.append({
                "title": "petit_guide_exploration_univers_reconnaitre_v2",
                "vault": "Veralume",
                "role": "Matrice des 9 Filtres & Heuristique du Double Regard"
            })
            core_files.append({
                "title": "Synthese_Geopolitique_Souverainete_vs_Supranationalisme",
                "vault": "Cerveau Alix",
                "role": "Cartographie Macro du Clivage Souverainisme vs Supranationalisme"
            })
            core_files.append({
                "title": "Protocole_Contre_Lecture_Thot_Horus",
                "vault": "Cerveau Alix",
                "role": "Scalpel de Contre-Lecture & Extraction du Non-Dit"
            })
            core_files.append({
                "title": "NOTE_STRATEGIQUE_JE_ME_SOUVIENS_PSPP_2026",
                "vault": "Cerveau Alix",
                "role": "Cas d'Application ?lectoral & D?montage du Dol ? 180 Jours"
            })

        return {
            "is_manipulation_or_closure_detected": len(matched_filters) > 0,
            "detected_filters": matched_filters,
            "recommended_bridge_files": core_files
        }


def format_r0_injection(analysis: Dict[str, Any]) -> str:
    """Formate une capsule d'injection R0 ? inclure dans les analyses."""
    if not analysis["is_manipulation_or_closure_detected"]:
        return ""
    
    lines = [
        "\n> ? **[RACCORDEUR R0 ACTIV? ? D?CLOISONNEMENT ONTOLOGIQUE]**",
        "> *Le texte de surface mobilise les signatures structurelles de la Cl?ture :*"
    ]
    for f in analysis["detected_filters"][:3]:
        lines.append(f"> - **{f['nom']}** *(indices : {', '.join(f['hits'])})*")
        lines.append(f">   ?? **Antidote Double Regard :** {f['antidote']}")
    
    lines.append(">\n> ?? **N?uds Socles Raccord?s :**")
    for doc in analysis["recommended_bridge_files"][:3]:
        lines.append(f"> - `[[{doc['title']}]]` *({doc['vault']} ? {doc['role']})*")
    
    return "\n".join(lines)
