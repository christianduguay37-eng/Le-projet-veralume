#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX RADAR ANTI-CORRUPTION v2.0 — SENTINELLE MARCHÉS PUBLICS & PROBITÉ
           Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
           Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Ausculte en continu les flux de données ouverts, registres et enquêtes sur :
  * Les contrats publics de gré à gré (sans appel d'offres / cabinets-conseils)
  * Les subventions industrielles massives et risques de faillite (Northvolt, filière batterie)
  * La concession / privatisation des infrastructures souveraines (aéroports, ports, énergie)
  * Le lobbying d'influence, le pantouflage et les conflits d'intérêts
  * Les rapports des Vérificateurs Généraux et enquêtes policières (ArriveCAN, SAAQclic)
- Équipé du Socle Universel AlixSentinelEngine :
  * Boule de neige lexicale & Lexique Vivant (Lexique_Vivant_Anti_Corruption.md)
  * Carnet de pistes d'atelier direct (Pistes_Anti_Corruption.md)
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
REGISTRE_MD = VAULT_CERVEAU / "Registre_Forensique_Corruption_et_Contrats_Publics.md"

AXES_CORRUPTION = {
    "1. Contrats de Gré à Gré & Cabinets-Conseils Privés": {
        "queries": [
            "Canada contrats sans appel d'offres millions McKinsey",
            "Canada sous-traitance cabinets conseil Deloitte PwC Accenture",
            "Québec contrats de gré à gré firmes conseil millions",
            "Canada sole-source contracts consulting millions federal"
        ],
        "keywords": [
            "gré à gré", "sans appel d'offres", "sole-source", "mckinsey", "deloitte", 
            "pwc", "kpmg", "accenture", "bain", "firme", "consultants", "sous-traitance", 
            "avenant", "dépassement", "millions"
        ],
        "mecanisme": "Privatisation occulte des fonctions régaliennes de l'État et érosion de l'imputabilité publique au profit de firmes privées sans mise en concurrence."
    },
    "2. Subventions Industrielles & Risques de Faillite (Filière Batterie)": {
        "queries": [
            "Northvolt faillite difficultés milliards fonds publics Québec Canada",
            "Canada subventions filière batterie milliards multinationales",
            "Investissement Québec pertes subventions entreprises privées",
            "Northvolt financial crisis subsidies Canada bailout"
        ],
        "keywords": [
            "northvolt", "batterie", "subvention", "subventions", "milliards", 
            "investissement québec", "fonds publics", "faillite", "pertes", "difficultés", 
            "aide gouvernementale", "bailout", "sauvetage"
        ],
        "mecanisme": "Socialisation intégrale des pertes et risques technologiques sur les contribuables, avec captation privée des retours sur investissement."
    },
    "3. Concessions & Privatisation d'Actifs Souverains": {
        "queries": [
            "Canada aéroports concession privatisation Mark Carney Brookfield",
            "Québec privatisation Hydro-Québec éolien privé Fitzgibbon",
            "Canada vente actifs publics ports infrastructures milliards",
            "Canada airport privatization Brookfield asset recycling"
        ],
        "keywords": [
            "aéroports", "privatisation", "concession", "brookfield", "carney", 
            "hydro-québec", "fitzgibbon", "éolien", "infrastructures", "ports", "vente"
        ],
        "mecanisme": "Aliénation des monopoles naturels et rentes stratégiques d'État au bénéfice de fonds d'investissement privés."
    },
    "4. Conflits d'Intérêts, Lobbying & Pantouflage": {
        "queries": [
            "Québec éthique députés ministres conflits intérêts Fitzgibbon",
            "Canada commissaire au lobbying enquêtes registre ministres",
            "Québec commissaire à l'éthique enquêtes rapports manquements"
        ],
        "keywords": [
            "conflit d'intérêts", "éthique", "commissaire", "lobbying", "lobbyiste", 
            "pantouflage", "duranceau", "fitzgibbon", "manquement", "enquête", "député"
        ],
        "mecanisme": "Perméabilité illégitime entre décideurs publics et intérêts financiers particuliers; affaiblissement de l'arbitrage démocratique."
    },
    "5. Rapports du Vérificateur Général & Enquêtes Policières (Fraude & Gaspillage)": {
        "queries": [
            "Canada vérificateur général rapport gaspillage contrats scandale",
            "ArriveCAN GC Strategies enquête GRC contrats millions",
            "Québec vérificatrice générale rapport contrats informatique SAAQclic",
            "UPAC arrestations enquêtes fraudes contrats municipaux"
        ],
        "keywords": [
            "vérificateur général", "vérificatrice générale", "rapport", "scandale", 
            "arrivecan", "gc strategies", "saaqclic", "grc", "upac", "fraude", 
            "surfacturation", "irrégularités", "enquête"
        ],
        "mecanisme": "Captation directe de deniers publics par montages contractuels opaques, surfacturation et défaillances de surveillance institutionnelle."
    }
}

SEED_LEXICON_CORRUPTION = {
    "cabinets_conseils_et_firmes": [
        "McKinsey & Company", "Deloitte", "PwC", "KPMG", "Accenture",
        "Bain & Company", "GC Strategies", "Dalian Enterprises", "Coradix Technology"
    ],
    "acteurs_politiques_et_dirigeants": [
        "Pierre Fitzgibbon", "France-Élaine Duranceau", "Mark Carney",
        "François Legault", "Investissement Québec", "Hydro-Québec",
        "Conseil du Trésor", "Vérificateur Général du Canada", "Vérificatrice Générale du Québec"
    ],
    "entreprises_et_dossiers_chauds": [
        "Northvolt", "ArriveCAN", "SAAQclic", "Lion Électrique", "Brookfield Asset Management",
        "Filière Batterie Bécancour", "Nemaska Lithium", "Taqwa"
    ],
    "mecanismes_fraude_et_captation": [
        "Contrat de gré à gré", "Sans appel d'offres", "Sole-source contract",
        "Surfacturation", "Avenant sans contrôle", "Pantouflage",
        "Subventions non remboursables", "Prêt sans garantie", "Prête-nom",
        "Scission de contrat", "Porte tournante"
    ],
    "organismes_surveillance": [
        "UPAC", "SEAO", "CanadaBuys", "Commissaire au lobbying",
        "Vérificateur Général", "Gendarmerie Royale du Canada",
        "Comité permanent des comptes publics", "Autorité des marchés publics"
    ]
}

DEFAULT_PISTES_CORRUPTION = [
    "Northvolt faillite difficultés milliards fonds publics Québec Canada",
    "Canada contrats sans appel d'offres millions McKinsey Deloitte",
    "Investissement Québec pertes subventions entreprises privées",
    "ArriveCAN sous-traitance GC Strategies vérification comptes publics"
]

DEFAULT_KEYWORDS_CORRUPTION = [
    "gré à gré", "sans appel d'offres", "sole-source", "mckinsey", "deloitte",
    "pwc", "kpmg", "accenture", "northvolt", "arrivecan", "subventions",
    "surfacturation", "faillite", "investissements", "vérificateur", "upac",
    "seao", "fitzgibbon", "duranceau", "gc strategies"
]


def create_sentinel() -> AlixSentinelEngine:
    return AlixSentinelEngine(
        sentinel_id="anticorruption",
        sentinel_name="Anti_Corruption",
        glyph="⚖️",
        axes_config=AXES_CORRUPTION,
        initial_seed_lexicon=SEED_LEXICON_CORRUPTION,
        default_pistes=DEFAULT_PISTES_CORRUPTION,
        target_registre_md=REGISTRE_MD,
        default_keywords=DEFAULT_KEYWORDS_CORRUPTION,
        use_academic_sources=False,
        lang="fr-CA",
        country="CA"
    )


if __name__ == "__main__":
    sentinel = create_sentinel()
    sentinel.run_cli()
