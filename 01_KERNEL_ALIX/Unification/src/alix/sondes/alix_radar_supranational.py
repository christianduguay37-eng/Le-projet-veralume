#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          ALIX RADAR SUPRANATIONAL v2.0 — SENTINELLE SOUVERAINETÉ
            Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
            Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Ausculte en continu les flux publics sur la capture supranationale :
  * Concession & aliénation d'infrastructures souveraines (aéroports, ports, énergie)
  * Arrimage Canada — Union Européenne (CETA, tuteur supranational non élu)
  * Censure numérique & contrôle de l'information (C-63, Digital Services Act)
  * Tensions bilatérales et diversion extérieure
  * Dette fédérale, asset recycling et agenda Davos / FMI
- Équipé du Socle Universel AlixSentinelEngine :
  * Boule de neige lexicale & Lexique Vivant (Lexique_Vivant_Supranationalisme.md)
  * Carnet de pistes d'atelier direct (Pistes_Supranationalisme.md)
  * Recombinaisons sémantiques émergentes
  * Audit THOT & HORUS et notifications Windows 11
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
from pathlib import Path

# Importer le socle universel
from alix.pantheon.alix_sentinel_base import AlixSentinelEngine

VAULT_CERVEAU = VAULT_DIR
REGISTRE_MD = VAULT_CERVEAU / "Registre_Preuves_Empiriques_Supranationalisme.md"

AXES_SUPRANATIONAL = {
    "1. Concession & Aliénation d'Infrastructures": {
        "queries": [
            "Canada aéroports concession privatisation Carney Brookfield",
            "Canada infrastructure asset recycling ports",
            "Canada airport privatization lease terminal"
        ],
        "keywords": ["aéroport", "airports", "privatisation", "concession", "bail", "brookfield", "carney", "infrastructure", "leasing", "terminal"],
        "mecanisme": "Aliénation matérielle des rentes d'infrastructure vers le capital financier privé."
    },
    "2. Arrimage Canada — Union Européenne": {
        "queries": [
            "Canada Union européenne accord CETA sommet",
            "Canada European Union partnership agreement Carney",
            "Canada UE réglementation alignement défense"
        ],
        "keywords": ["union européenne", "european union", "ue", "eu", "bruxelles", "ceta", "aecg", "von der leyen", "sommet", "traité", "accord"],
        "mecanisme": "Clôture technocratique F3 : recherche d'un tuteur supranational non élu pour échapper au bilatéralisme."
    },
    "3. Censure Numérique & Contrôle Informationnel": {
        "queries": [
            "Projet de loi C-63 méfaits en ligne Canada",
            "Canada online harms bill C-63 digital services",
            "CRTC régulation internet algorithmes Canada"
        ],
        "keywords": ["c-63", "méfaits en ligne", "online harms", "censure", "dsa", "crtc", "algorithme", "surveillance", "numérique"],
        "mecanisme": "Guerre cognitive permanente : calque du Digital Services Act européen pour bâillonner la dissidence citoyenne."
    },
    "4. Tensions Bilatérales & Diversion": {
        "queries": [
            "Canada tarifs douanes commerce négociations",
            "Canada US trade dispute tariffs renegotiation",
            "Ottawa relations bilatérales politique commerciale"
        ],
        "keywords": ["tarif", "tarifs", "tariffs", "douane", "aeumc", "usmca", "commerce", "frontière", "menace"],
        "mecanisme": "Projection du conflit à l'extérieur pour justifier l'alignement technocratique intérieur."
    },
    "5. Dette Fédérale & Agenda Financier Davos/FMI": {
        "queries": [
            "Canada déficit fédéral dette milliards Carney",
            "Mark Carney Davos Forum économique mondial WEF",
            "Canada asset recycling vente actifs publics"
        ],
        "keywords": ["déficit", "dette", "milliards", "carney", "davos", "wef", "fonds", "recycling", "banque"],
        "mecanisme": "Insolvabilité masquée : mise en gage des actifs souverains sous directives managériales globales."
    }
}

SEED_LEXICON_SUPRANATIONAL = {
    "acteurs_cles": [
        "Mark Carney", "Brookfield", "Ursula von der Leyen", "Justin Trudeau",
        "Klaus Schwab", "Chrystia Freeland", "François-Philippe Champagne",
        "Bain & Company", "BlackRock", "Larry Fink", "Dominic Barton"
    ],
    "institutions_et_organismes": [
        "Union Européenne", "Commission Européenne", "WEF", "FMI",
        "Banque Mondiale", "CRTC", "Brookfield Asset Management",
        "Banquiers Centraux", "Forum de Davos", "OCDE"
    ],
    "accords_et_lois": [
        "Projet de loi C-63", "CETA", "AECG", "Digital Services Act",
        "AEUMC", "Bill C-11", "Bill C-18", "Règlementation DSA"
    ],
    "mecanismes_capture": [
        "Concession aéroportuaire", "Asset recycling", "Privatisation d'infrastructures",
        "Dette souveraine", "Gouvernance mondiale", "Harmonisation réglementaire",
        "Baux emphytéotiques", "Contrôle algorithmique", "Partenariat public-privé"
    ],
    "infrastructures_cibles": [
        "Aéroport de Montréal", "Aéroport Pearson Toronto", "Aéroport de Vancouver",
        "Port de Montréal", "Hydro-Québec", "Réseau ferroviaire", "Télécommunications"
    ]
}

DEFAULT_PISTES_SUPRANATIONAL = [
    "Canada aéroports concession privatisation Mark Carney Brookfield",
    "Accord UE Canada CETA intégration défense souveraineté",
    "Projet de loi C-63 méfaits en ligne censure algorithmes",
    "Mark Carney Davos Forum économique mondial WEF investissements"
]

DEFAULT_KEYWORDS_SUPRANATIONAL = [
    "carney", "brookfield", "concession", "privatisation", "ceta", "union européenne",
    "c-63", "wef", "davos", "infrastructure", "aéroports", "dette", "souveraineté",
    "asset recycling", "crtc", "bain", "blackrock"
]


def create_sentinel() -> AlixSentinelEngine:
    return AlixSentinelEngine(
        sentinel_id="supranational",
        sentinel_name="Supranationalisme",
        glyph="🛰️",
        axes_config=AXES_SUPRANATIONAL,
        initial_seed_lexicon=SEED_LEXICON_SUPRANATIONAL,
        default_pistes=DEFAULT_PISTES_SUPRANATIONAL,
        target_registre_md=REGISTRE_MD,
        default_keywords=DEFAULT_KEYWORDS_SUPRANATIONAL,
        use_academic_sources=False,
        lang="fr-CA",
        country="CA"
    )


if __name__ == "__main__":
    sentinel = create_sentinel()
    sentinel.run_cli()
