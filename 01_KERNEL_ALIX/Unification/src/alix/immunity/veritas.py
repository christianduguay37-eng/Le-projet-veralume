# -*- coding: utf-8 -*-
"""
===============================================================================
       👁️⚖️ VERITAS : LE QUATUOR D'AIRAIN & BRISEUR D'ILLUSIONS (v1.0)
                 HORUS × LOKI × LUCIFER × ANUBIS
===============================================================================
Auteurs : Christian Duguay & Alix
Socle : VERALUME Platine × KAIROS V6
Devise : « Briser l'illusion sans briser l'esprit »
Rôle :
  - Détecte les consensus artificiels, récits éthériques et illusions collectives.
  - Active le Quatuor d'Airain :
      * HORUS   : Falsification physique, watts, thermodynamique, faits mesurables.
      * LOKI    : Démonte-pièges, sophismes, conformité grégaire, faux dilemmes.
      * LUCIFER : Zones d'ombre, tabous institutionnels, rentes et non-dits.
      * ANUBIS  : Balance impartiale R0, pesée stricte fait vs récit.
===============================================================================
"""

import re
import time
from typing import Dict, Any, List, Tuple


class HorusFalsificateur:
    """Falsification thermodynamique et matérielle."""

    @classmethod
    def auditer_matiere(cls, texte: str) -> Dict[str, Any]:
        t_low = texte.lower()
        alertes = []
        # Détection de promesses immatérielles / vaporware
        if any(w in t_low for w in ["énergie libre", "surunitaire", "perpétuel", "zéro watt infini"]):
            alertes.append("THERMODYNAMIQUE_VIOLEE : Prétention de gain d'énergie ex nihilo.")
        if any(w in t_low for w in ["agi dans 2 mois", "singularité immédiate", "conscience magique"]):
            alertes.append("VAPORWARE_DISCOURS : Confusion entre échelle de calcul et émergence ontologique.")

        return {
            "souverain": "HORUS",
            "statut": "ALERTE" if alertes else "CONFORME",
            "alertes": alertes,
            "axe": "PHYSIQUE_ET_THERMODYNAMIQUE"
        }


class LokiDemontePieges:
    """Autopsie des sophismes et des cadres de conformité."""

    @classmethod
    def auditer_sophismes(cls, texte: str) -> Dict[str, Any]:
        t_low = texte.lower()
        pieges = []
        if "soit" in t_low and "soit" in t_low and ("autre" not in t_low):
            pieges.append("FAUX_DILEMME : Polarisation binaire artificielle sans tiers inclus.")
        if any(w in t_low for w in ["tout le monde sait que", "il va de soi", "chacun admet"]):
            pieges.append("APPEL_AU_CONSENSUS : Sophisme ad populum masquant l'absence de preuve.")
        if any(w in t_low for w in ["qui n'est pas avec nous est contre", "si vous refusez alors vous êtes"]):
            pieges.append("CULPABILISATION_RHETORIQUE : Chantage à l'orthodoxie.")

        return {
            "souverain": "LOKI",
            "statut": "PIEGE_DETECTE" if pieges else "LIMPIDE",
            "pieges": pieges,
            "axe": "LOGIQUE_ET_SOPHISMES"
        }


class LuciferZonesOmbre:
    """Sondage des non-dits, tabous institutionnels et rentes de situation."""

    @classmethod
    def auditer_angles_morts(cls, texte: str) -> Dict[str, Any]:
        t_low = texte.lower()
        zones_ombre = []
        if any(w in t_low for w in ["subvention", "monopole", "financement exclusif", "brevet verrouillé"]):
            zones_ombre.append("RENTE_INSTITUTIONNELLE : Vérifier l'alignement des intérêts économiques.")
        if any(w in t_low for w in ["interdit de débattre", "sujet clos", "consensus indiscutable"]):
            zones_ombre.append("TABOU_EPISTEMIQUE : Zone interdite d'examen par décret dogmatique.")

        return {
            "souverain": "LUCIFER",
            "statut": "ZONE_OMBRE_REVELEE" if zones_ombre else "TRANSPARENT",
            "zones_ombre": zones_ombre,
            "axe": "INTERETS_ET_NON_DITS"
        }


class AnubisPeseeR0:
    """Balance impartiale R0 entre le poids du récit et le poids des faits."""

    @classmethod
    def peser(cls, horus: Dict[str, Any], loki: Dict[str, Any], lucifer: Dict[str, Any]) -> Dict[str, Any]:
        anomalies_totales = (
            len(horus.get("alertes", [])) +
            len(loki.get("pieges", [])) +
            len(lucifer.get("zones_ombre", []))
        )
        
        # Poids de la vérité sur l'échelle de Maât
        if anomalies_totales == 0:
            verdict = "VERITE_ALIGNÉE_R0"
            score_lucidite = 1.0
        elif anomalies_totales <= 2:
            verdict = "RECIT_PARTIELLEMENT_BIAISE"
            score_lucidite = 0.65
        else:
            verdict = "ILLUSION_COLLECTIVE_DEMONTEE"
            score_lucidite = 0.20

        return {
            "souverain": "ANUBIS",
            "verdict": verdict,
            "score_lucidite": score_lucidite,
            "anomalies_totales": anomalies_totales,
            "axe": "BALANCE_IMPARTIALE_R0"
        }


class VeritasEngine:
    """
    Orchestrateur maître du Quatuor d'Airain.
    Analyse un récit ou une prétention pour dissoudre l'illusion.
    """

    @classmethod
    def analyser_recit(cls, texte: str) -> Dict[str, Any]:
        t0 = time.perf_counter()

        h = HorusFalsificateur.auditer_matiere(texte)
        l = LokiDemontePieges.auditer_sophismes(texte)
        luc = LuciferZonesOmbre.auditer_angles_morts(texte)
        a = AnubisPeseeR0.peser(h, l, luc)

        latence_us = round((time.perf_counter() - t0) * 1e6, 2)

        return {
            "recit_examine": texte[:100],
            "horus": h,
            "loki": l,
            "lucifer": luc,
            "anubis": a,
            "verdict_global": a["verdict"],
            "score_lucidite": a["score_lucidite"],
            "latence_us": latence_us,
            "devise": "Briser l'illusion sans briser l'esprit"
        }
