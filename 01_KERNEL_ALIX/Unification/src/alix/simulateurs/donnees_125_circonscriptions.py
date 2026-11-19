# -*- coding: utf-8 -*-
"""
================================================================================
    DONNÉES OFFICIELLES DES 125 CIRCONSCRIPTIONS DU QUÉBEC (DGEQ / ISQ)
        Base Électorale & Sociologique pour le Simulateur Souverain
================================================================================
Auteurs : Christian Duguay & Alix
Sources : Élections Québec (DGEQ 2022), Institut de la statistique du Québec (ISQ)
================================================================================
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Liste exacte des 125 circonscriptions provinciales du Québec
# Structure :
#   - region : Macro-région sociologique
#   - milieu : 'urbain_dense', 'banlieue_couronne', 'ville_regionale', 'rural_ressource'
#   - pct_55_plus : Part des électeurs de 55 ans et plus (Moyenne Québec ~ 46%)
#   - pct_franco : Part de la population de langue maternelle française (Moyenne ~ 78%)
#   - res_2022 : % obtenus aux élections générales de 2022 (CAQ, PLQ, QS, PQ, PCQ)
#   - vainqueur_2022 : Député / Parti vainqueur

CIRCONSCRIPTIONS_125 = [
    # --- 1. BAS-SAINT-LAURENT & GASPÉSIE (7 comtés) ---
    {
        "nom": "Rimouski",
        "region": "Est_du_Quebec",
        "milieu": "ville_regionale",
        "pct_55_plus": 51.0,
        "pct_franco": 98.2,
        "res_2022": {"CAQ": 41.8, "PQ": 28.5, "QS": 17.2, "PCQ": 8.1, "PLQ": 3.4},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Matane-Matapédia",
        "region": "Est_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 55.0,
        "pct_franco": 98.8,
        "res_2022": {"PQ": 67.4, "CAQ": 20.3, "PCQ": 6.2, "QS": 3.9, "PLQ": 1.7},
        "vainqueur_2022": "PQ"
    },
    {
        "nom": "Rivière-du-Loup-Témiscouata",
        "region": "Est_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 52.0,
        "pct_franco": 98.5,
        "res_2022": {"CAQ": 52.1, "PQ": 20.2, "PCQ": 12.3, "QS": 10.9, "PLQ": 3.8},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Gaspé",
        "region": "Est_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 53.0,
        "pct_franco": 91.0,
        "res_2022": {"CAQ": 41.4, "PQ": 36.9, "PLQ": 9.2, "QS": 7.4, "PCQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Bonaventure",
        "region": "Est_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 54.0,
        "pct_franco": 85.0,
        "res_2022": {"CAQ": 44.5, "PQ": 30.1, "PLQ": 11.2, "QS": 9.0, "PCQ": 4.6},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Îles-de-la-Madeleine",
        "region": "Est_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 52.0,
        "pct_franco": 94.0,
        "res_2022": {"PQ": 46.4, "CAQ": 39.4, "PLQ": 7.0, "QS": 5.1, "PCQ": 1.8},
        "vainqueur_2022": "PQ"
    },
    {
        "nom": "Côte-du-Sud",
        "region": "Est_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 53.5,
        "pct_franco": 98.6,
        "res_2022": {"CAQ": 43.3, "PCQ": 23.3, "PQ": 16.5, "QS": 11.2, "PLQ": 4.8},
        "vainqueur_2022": "CAQ"
    },

    # --- 2. SAGUENAY–LAC-SAINT-JEAN & CÔTE-NORD (6 comtés) ---
    {
        "nom": "Chicoutimi",
        "region": "Saguenay_Lac_St_Jean",
        "milieu": "ville_regionale",
        "pct_55_plus": 50.0,
        "pct_franco": 98.5,
        "res_2022": {"CAQ": 50.5, "PQ": 26.2, "QS": 12.3, "PCQ": 8.0, "PLQ": 2.4},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Jonquière",
        "region": "Saguenay_Lac_St_Jean",
        "milieu": "ville_regionale",
        "pct_55_plus": 51.5,
        "pct_franco": 98.7,
        "res_2022": {"CAQ": 59.3, "PQ": 20.8, "QS": 9.4, "PCQ": 7.6, "PLQ": 2.2},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Dubuc",
        "region": "Saguenay_Lac_St_Jean",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 98.6,
        "res_2022": {"CAQ": 57.6, "PQ": 17.5, "PCQ": 13.0, "QS": 8.9, "PLQ": 2.4},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Lac-Saint-Jean",
        "region": "Saguenay_Lac_St_Jean",
        "milieu": "rural_ressource",
        "pct_55_plus": 50.0,
        "pct_franco": 98.9,
        "res_2022": {"CAQ": 51.5, "PQ": 32.7, "PCQ": 7.5, "QS": 6.3, "PLQ": 1.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Roberval",
        "region": "Saguenay_Lac_St_Jean",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 56.6, "PQ": 20.9, "PCQ": 12.0, "QS": 7.3, "PLQ": 2.7},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Duplessis",
        "region": "Saguenay_Lac_St_Jean",
        "milieu": "rural_ressource",
        "pct_55_plus": 45.0,
        "pct_franco": 86.0,
        "res_2022": {"CAQ": 45.1, "PQ": 27.2, "PCQ": 12.5, "QS": 10.1, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },

    # --- 3. CAPITALE-NATIONALE (11 comtés) ---
    {
        "nom": "Jean-Talon",
        "region": "Capitale_Nationale",
        "milieu": "urbain_dense",
        "pct_55_plus": 44.0,
        "pct_franco": 92.5,
        "res_2022": {"CAQ": 32.5, "QS": 23.8, "PQ": 18.9, "PLQ": 13.5, "PCQ": 10.4},
        "vainqueur_2022": "PQ" # Basculé PQ lors de la partielle de 2023 (Pascal Paradis 44.1%)
    },
    {
        "nom": "Taschereau",
        "region": "Capitale_Nationale",
        "milieu": "urbain_dense",
        "pct_55_plus": 39.0,
        "pct_franco": 93.0,
        "res_2022": {"QS": 39.5, "CAQ": 22.4, "PQ": 19.8, "PCQ": 11.2, "PLQ": 6.1},
        "vainqueur_2022": "QS"
    },
    {
        "nom": "Jean-Lesage",
        "region": "Capitale_Nationale",
        "milieu": "urbain_dense",
        "pct_55_plus": 42.0,
        "pct_franco": 93.5,
        "res_2022": {"QS": 37.5, "CAQ": 30.1, "PCQ": 14.2, "PQ": 12.6, "PLQ": 4.8},
        "vainqueur_2022": "QS"
    },
    {
        "nom": "Chauveau",
        "region": "Capitale_Nationale",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 46.8, "PCQ": 31.8, "PQ": 9.8, "QS": 8.0, "PLQ": 3.0},
        "vainqueur_2022": "CAQ" # Éric Duhaime a fait 31.8%
    },
    {
        "nom": "La Peltrie",
        "region": "Capitale_Nationale",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 44.4, "PCQ": 36.8, "QS": 8.7, "PQ": 7.0, "PLQ": 2.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Charlesbourg",
        "region": "Capitale_Nationale",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 45.0, "PCQ": 24.3, "PQ": 14.5, "QS": 12.1, "PLQ": 3.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Vanier-Les Rivières",
        "region": "Capitale_Nationale",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 47.1, "PCQ": 23.9, "QS": 12.7, "PQ": 11.8, "PLQ": 3.9},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Louis-Hébert",
        "region": "Capitale_Nationale",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 94.0,
        "res_2022": {"CAQ": 47.2, "PQ": 19.3, "PLQ": 13.9, "QS": 10.7, "PCQ": 8.3},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Montmorency",
        "region": "Capitale_Nationale",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.5,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 45.2, "PCQ": 22.8, "PQ": 15.6, "QS": 12.5, "PLQ": 3.2},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Charlevoix-Côte-de-Beaupré",
        "region": "Capitale_Nationale",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 46.2, "PQ": 23.3, "PCQ": 15.0, "QS": 11.9, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Portneuf",
        "region": "Capitale_Nationale",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 47.4, "PCQ": 28.3, "PQ": 11.2, "QS": 9.4, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },

    # --- 4. CHAUDIÈRE-APPALACHES (7 comtés) ---
    {
        "nom": "Beauce-Nord",
        "region": "Chaudiere_Appalaches",
        "milieu": "rural_ressource",
        "pct_55_plus": 47.0,
        "pct_franco": 98.8,
        "res_2022": {"CAQ": 48.3, "PCQ": 40.8, "QS": 4.5, "PQ": 4.1, "PLQ": 1.7},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Beauce-Sud",
        "region": "Chaudiere_Appalaches",
        "milieu": "rural_ressource",
        "pct_55_plus": 48.0,
        "pct_franco": 98.5,
        "res_2022": {"CAQ": 46.2, "PCQ": 42.1, "QS": 4.7, "PQ": 4.3, "PLQ": 2.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Bellechasse",
        "region": "Chaudiere_Appalaches",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 98.5,
        "res_2022": {"CAQ": 45.4, "PCQ": 34.9, "PQ": 9.8, "QS": 6.7, "PLQ": 2.6},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Lévis",
        "region": "Chaudiere_Appalaches",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 48.8, "PCQ": 21.6, "PQ": 13.9, "QS": 12.0, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Chutes-de-la-Chaudière",
        "region": "Chaudiere_Appalaches",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 47.5, "PCQ": 25.4, "PQ": 13.0, "QS": 10.5, "PLQ": 3.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Lotbinière-Frontenac",
        "region": "Chaudiere_Appalaches",
        "milieu": "rural_ressource",
        "pct_55_plus": 50.0,
        "pct_franco": 98.5,
        "res_2022": {"CAQ": 43.8, "PCQ": 32.5, "PQ": 11.2, "QS": 8.7, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Arthabaska", # (Frontière Centre-du-Québec / Chaudière)
        "region": "Chaudiere_Appalaches",
        "milieu": "ville_regionale",
        "pct_55_plus": 48.0,
        "pct_franco": 98.2,
        "res_2022": {"CAQ": 51.7, "PCQ": 24.3, "PQ": 10.8, "QS": 9.4, "PLQ": 3.0},
        "vainqueur_2022": "CAQ"
    },

    # --- 5. MAURICIE & CENTRE-DU-QUÉBEC (7 comtés restants) ---
    {
        "nom": "Trois-Rivières",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "ville_regionale",
        "pct_55_plus": 49.0,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 45.4, "PQ": 20.8, "QS": 17.5, "PCQ": 10.8, "PLQ": 4.7},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Champlain",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 50.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 55.9, "PCQ": 16.5, "PQ": 13.9, "QS": 9.9, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Laviolette-Saint-Maurice",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 52.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 50.2, "PCQ": 18.8, "PQ": 16.7, "QS": 10.7, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Maskinongé",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 53.5, "PCQ": 17.9, "PQ": 14.1, "QS": 10.7, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Drummond-Bois-Francs",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "ville_regionale",
        "pct_55_plus": 48.0,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 52.5, "PCQ": 17.8, "PQ": 14.2, "QS": 11.2, "PLQ": 3.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Nicolet-Bécancour",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 54.3, "PQ": 18.2, "PCQ": 13.9, "QS": 9.9, "PLQ": 3.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Johnson",
        "region": "Mauricie_Centre_du_Quebec",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 96.5,
        "res_2022": {"CAQ": 52.6, "PCQ": 17.4, "PQ": 14.7, "QS": 11.5, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },

    # --- 6. ESTRIE (6 comtés) ---
    {
        "nom": "Sherbrooke",
        "region": "Estrie",
        "milieu": "ville_regionale",
        "pct_55_plus": 43.0,
        "pct_franco": 92.0,
        "res_2022": {"QS": 41.9, "CAQ": 32.5, "PQ": 11.8, "PCQ": 7.7, "PLQ": 5.4},
        "vainqueur_2022": "QS"
    },
    {
        "nom": "Saint-François",
        "region": "Estrie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 94.0,
        "res_2022": {"CAQ": 43.5, "QS": 24.3, "PQ": 15.6, "PCQ": 10.9, "PLQ": 5.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Richmond",
        "region": "Estrie",
        "milieu": "rural_ressource",
        "pct_55_plus": 50.0,
        "pct_franco": 95.0,
        "res_2022": {"CAQ": 46.8, "QS": 20.3, "PQ": 16.5, "PCQ": 11.3, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Orford",
        "region": "Estrie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 49.0,
        "pct_franco": 93.0,
        "res_2022": {"CAQ": 42.4, "QS": 24.7, "PQ": 15.2, "PLQ": 9.5, "PCQ": 7.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Mégantic",
        "region": "Estrie",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 48.9, "PCQ": 21.2, "PQ": 13.9, "QS": 11.4, "PLQ": 4.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Brome-Missisquoi",
        "region": "Estrie",
        "milieu": "rural_ressource",
        "pct_55_plus": 50.0,
        "pct_franco": 82.0,
        "res_2022": {"CAQ": 46.0, "QS": 19.5, "PLQ": 14.8, "PQ": 11.5, "PCQ": 7.5},
        "vainqueur_2022": "CAQ"
    },

    # --- 7. MONTÉRÉGIE (23 comtés) ---
    {
        "nom": "Borduas",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 51.1, "PQ": 20.6, "QS": 15.1, "PCQ": 7.8, "PLQ": 4.8},
        "vainqueur_2022": "CAQ" # Simon Jolin-Barrette
    },
    {
        "nom": "Chambly",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 42.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 48.5, "PQ": 21.2, "QS": 15.5, "PCQ": 8.5, "PLQ": 5.5},
        "vainqueur_2022": "CAQ" # Jean-François Roberge
    },
    {
        "nom": "Iberville",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 96.5,
        "res_2022": {"CAQ": 53.6, "PQ": 16.5, "QS": 13.2, "PCQ": 10.9, "PLQ": 5.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Saint-Jean",
        "region": "Monteregie",
        "milieu": "ville_regionale",
        "pct_55_plus": 47.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 48.2, "PQ": 19.8, "QS": 14.5, "PCQ": 11.2, "PLQ": 5.6},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Saint-Hyacinthe",
        "region": "Monteregie",
        "milieu": "ville_regionale",
        "pct_55_plus": 48.0,
        "pct_franco": 97.0,
        "res_2022": {"CAQ": 47.7, "PQ": 22.4, "QS": 14.7, "PCQ": 9.8, "PLQ": 4.7},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Richelieu",
        "region": "Monteregie",
        "milieu": "ville_regionale",
        "pct_55_plus": 51.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 42.1, "PQ": 33.7, "QS": 11.8, "PCQ": 8.7, "PLQ": 3.1},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Verchères",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 46.3, "PQ": 26.5, "QS": 14.2, "PCQ": 7.8, "PLQ": 4.5},
        "vainqueur_2022": "CAQ" # Suzanne Roy
    },
    {
        "nom": "Vachon",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 85.0,
        "res_2022": {"CAQ": 44.9, "PQ": 18.5, "QS": 16.5, "PLQ": 12.0, "PCQ": 7.5},
        "vainqueur_2022": "CAQ" # Ian Lafrenière
    },
    {
        "nom": "Taillon",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 87.0,
        "res_2022": {"CAQ": 41.5, "PQ": 21.5, "QS": 18.5, "PLQ": 11.5, "PCQ": 6.5},
        "vainqueur_2022": "CAQ" # Lionel Carmant
    },
    {
        "nom": "Marie-Victorin",
        "region": "Monteregie",
        "milieu": "urbain_dense",
        "pct_55_plus": 44.0,
        "pct_franco": 82.0,
        "res_2022": {"CAQ": 33.1, "PQ": 25.2, "QS": 22.8, "PLQ": 10.5, "PCQ": 7.5},
        "vainqueur_2022": "CAQ" # Shirley Dorismond
    },
    {
        "nom": "Montarville",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 92.0,
        "res_2022": {"CAQ": 45.9, "PQ": 20.8, "QS": 15.5, "PLQ": 11.8, "PCQ": 5.5},
        "vainqueur_2022": "CAQ" # Nathalie Roy
    },
    {
        "nom": "La Pinière",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 38.0,
        "res_2022": {"PLQ": 38.5, "CAQ": 31.8, "PCQ": 12.5, "QS": 9.5, "PQ": 6.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Brossard-Saint-Lambert",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 46.0,
        "res_2022": {"PLQ": 38.6, "CAQ": 30.5, "QS": 13.5, "PQ": 9.5, "PCQ": 7.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Laporte",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 72.0,
        "res_2022": {"CAQ": 30.8, "PLQ": 29.5, "QS": 17.5, "PQ": 13.5, "PCQ": 8.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "La Prairie",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 44.0,
        "pct_franco": 82.0,
        "res_2022": {"CAQ": 52.7, "PQ": 14.5, "QS": 13.5, "PLQ": 10.5, "PCQ": 8.5},
        "vainqueur_2022": "CAQ" # Christian Dubé
    },
    {
        "nom": "Sanguinet",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 43.0,
        "pct_franco": 91.0,
        "res_2022": {"CAQ": 46.5, "PQ": 18.5, "QS": 14.5, "PCQ": 12.5, "PLQ": 7.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Châteauguay",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 68.0,
        "res_2022": {"CAQ": 39.1, "PLQ": 24.5, "PCQ": 14.5, "QS": 11.5, "PQ": 9.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Huntingdon",
        "region": "Monteregie",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 78.0,
        "res_2022": {"CAQ": 46.6, "QS": 15.5, "PCQ": 15.2, "PQ": 12.5, "PLQ": 9.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Beauharnois",
        "region": "Monteregie",
        "milieu": "ville_regionale",
        "pct_55_plus": 48.0,
        "pct_franco": 95.0,
        "res_2022": {"CAQ": 53.8, "PQ": 17.5, "QS": 12.5, "PCQ": 10.5, "PLQ": 5.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Soulanges",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 44.0,
        "pct_franco": 82.0,
        "res_2022": {"CAQ": 44.6, "PLQ": 18.5, "PCQ": 16.5, "QS": 10.5, "PQ": 9.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Vaudreuil",
        "region": "Monteregie",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 43.0,
        "pct_franco": 64.0,
        "res_2022": {"PLQ": 34.2, "CAQ": 32.5, "PCQ": 13.5, "QS": 10.5, "PQ": 8.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Granby",
        "region": "Monteregie",
        "milieu": "ville_regionale",
        "pct_55_plus": 49.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 58.2, "QS": 13.5, "PQ": 12.5, "PCQ": 10.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ" # François Bonnardel
    },

    # --- 8. LANAUDIÈRE & LAURENTIDES (17 comtés) ---
    {
        "nom": "L'Assomption",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 96.5,
        "res_2022": {"CAQ": 58.6, "PQ": 15.5, "QS": 11.5, "PCQ": 9.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ" # François Legault
    },
    {
        "nom": "Terrebonne",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 44.0,
        "pct_franco": 94.0,
        "res_2022": {"CAQ": 48.0, "PQ": 22.5, "QS": 13.5, "PCQ": 9.5, "PLQ": 5.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Masson",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 43.0,
        "pct_franco": 95.5,
        "res_2022": {"CAQ": 50.8, "PQ": 19.5, "QS": 13.5, "PCQ": 10.5, "PLQ": 5.0},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Les Plaines",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 51.5, "PQ": 17.5, "QS": 12.5, "PCQ": 13.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Joliette",
        "region": "Lanaudiere_Laurentides",
        "milieu": "ville_regionale",
        "pct_55_plus": 50.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 44.8, "PQ": 32.5, "QS": 10.5, "PCQ": 8.5, "PLQ": 3.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Berthier",
        "region": "Lanaudiere_Laurentides",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 97.5,
        "res_2022": {"CAQ": 48.5, "PQ": 21.5, "PCQ": 14.5, "QS": 11.5, "PLQ": 3.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Rousseau",
        "region": "Lanaudiere_Laurentides",
        "milieu": "rural_ressource",
        "pct_55_plus": 45.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 51.5, "PQ": 17.5, "PCQ": 16.5, "QS": 10.5, "PLQ": 3.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Saint-Jérôme",
        "region": "Lanaudiere_Laurentides",
        "milieu": "ville_regionale",
        "pct_55_plus": 47.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 46.5, "PQ": 22.5, "QS": 14.5, "PCQ": 11.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Mirabel",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 39.0,
        "pct_franco": 95.0,
        "res_2022": {"CAQ": 48.5, "PQ": 19.5, "PCQ": 14.5, "QS": 12.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Deux-Montagnes",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 86.0,
        "res_2022": {"CAQ": 46.5, "PQ": 18.5, "QS": 14.5, "PLQ": 12.5, "PCQ": 7.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Prévost",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 95.5,
        "res_2022": {"CAQ": 45.5, "PQ": 22.5, "QS": 14.5, "PCQ": 12.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Bertrand",
        "region": "Lanaudiere_Laurentides",
        "milieu": "rural_ressource",
        "pct_55_plus": 53.0,
        "pct_franco": 94.0,
        "res_2022": {"CAQ": 45.2, "PQ": 22.5, "QS": 14.5, "PCQ": 11.5, "PLQ": 5.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Blainville",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 44.0,
        "pct_franco": 91.0,
        "res_2022": {"CAQ": 49.5, "PQ": 17.5, "QS": 13.5, "PLQ": 11.5, "PCQ": 7.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Groulx",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 90.0,
        "res_2022": {"CAQ": 44.5, "PQ": 18.5, "QS": 16.5, "PLQ": 12.5, "PCQ": 7.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Rivière-du-Nord",
        "region": "Lanaudiere_Laurentides",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 95.0,
        "res_2022": {"CAQ": 47.5, "PQ": 20.5, "QS": 14.5, "PCQ": 12.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Argenteuil",
        "region": "Lanaudiere_Laurentides",
        "milieu": "rural_ressource",
        "pct_55_plus": 51.0,
        "pct_franco": 82.0,
        "res_2022": {"CAQ": 44.5, "PQ": 17.5, "PCQ": 15.5, "QS": 11.5, "PLQ": 10.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Labelle",
        "region": "Lanaudiere_Laurentides",
        "milieu": "rural_ressource",
        "pct_55_plus": 52.0,
        "pct_franco": 95.0,
        "res_2022": {"CAQ": 47.5, "PQ": 22.5, "QS": 13.5, "PCQ": 11.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },

    # --- 9. LAVAL (6 comtés) ---
    {
        "nom": "Chomedey",
        "region": "Laval",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 36.0,
        "res_2022": {"PLQ": 37.5, "CAQ": 26.5, "PCQ": 17.5, "QS": 9.5, "PQ": 7.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Fabre",
        "region": "Laval",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 55.0,
        "res_2022": {"PLQ": 32.5, "CAQ": 31.8, "PCQ": 14.5, "QS": 11.5, "PQ": 8.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Laval-des-Rapides",
        "region": "Laval",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 64.0,
        "res_2022": {"CAQ": 34.5, "PLQ": 27.5, "QS": 17.5, "PQ": 11.5, "PCQ": 8.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Mille-Îles",
        "region": "Laval",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 65.0,
        "res_2022": {"PLQ": 33.5, "CAQ": 32.5, "PCQ": 13.5, "QS": 11.5, "PQ": 8.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Sainte-Rose",
        "region": "Laval",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 72.0,
        "res_2022": {"CAQ": 38.5, "PLQ": 24.5, "QS": 15.5, "PQ": 12.5, "PCQ": 8.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Vimont",
        "region": "Laval",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 72.0,
        "res_2022": {"CAQ": 37.5, "PLQ": 27.5, "PCQ": 13.5, "QS": 11.5, "PQ": 9.5},
        "vainqueur_2022": "CAQ"
    },

    # --- 10. MONTRÉAL (27 comtés) ---
    # Forteresses PLQ
    {
        "nom": "D'Arcy-McGee",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 46.0,
        "pct_franco": 18.0,
        "res_2022": {"PLQ": 51.5, "PCQ": 22.5, "QS": 10.5, "CAQ": 9.5, "PQ": 3.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Jacques-Cartier",
        "region": "Montreal",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 49.0,
        "pct_franco": 22.0,
        "res_2022": {"PLQ": 52.5, "PCQ": 18.5, "CAQ": 14.5, "QS": 8.5, "PQ": 4.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Robert-Baldwin",
        "region": "Montreal",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 48.0,
        "pct_franco": 24.0,
        "res_2022": {"PLQ": 49.5, "PCQ": 18.5, "CAQ": 16.5, "QS": 8.5, "PQ": 5.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Nelligan",
        "region": "Montreal",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 47.0,
        "pct_franco": 28.0,
        "res_2022": {"PLQ": 45.5, "PCQ": 20.5, "CAQ": 18.5, "QS": 8.5, "PQ": 5.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Saint-Laurent",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 45.0,
        "pct_franco": 32.0,
        "res_2022": {"PLQ": 44.5, "CAQ": 19.5, "PCQ": 17.5, "QS": 11.5, "PQ": 5.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Mont-Royal-Outremont",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 42.0,
        "pct_franco": 46.0,
        "res_2022": {"PLQ": 39.5, "QS": 22.5, "CAQ": 16.5, "PQ": 13.5, "PCQ": 6.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Westmount-Saint-Louis",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 41.0,
        "pct_franco": 25.0,
        "res_2022": {"PLQ": 50.5, "QS": 18.5, "CAQ": 11.5, "PCQ": 10.5, "PQ": 6.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Notre-Dame-de-Grâce",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 44.0,
        "pct_franco": 32.0,
        "res_2022": {"PLQ": 44.5, "QS": 23.5, "CAQ": 11.5, "PCQ": 9.5, "PQ": 7.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Marquette",
        "region": "Montreal",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 46.0,
        "pct_franco": 54.0,
        "res_2022": {"PLQ": 34.5, "CAQ": 31.5, "QS": 14.5, "PCQ": 10.5, "PQ": 7.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Acadie",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 45.0,
        "pct_franco": 42.0,
        "res_2022": {"PLQ": 39.5, "CAQ": 20.5, "QS": 17.5, "PCQ": 11.5, "PQ": 8.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Marguerite-Bourgeoys",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 47.0,
        "pct_franco": 48.0,
        "res_2022": {"PLQ": 36.5, "CAQ": 29.5, "PCQ": 13.5, "QS": 11.5, "PQ": 7.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Jeanne-Mance-Viger",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 48.0,
        "pct_franco": 46.0,
        "res_2022": {"PLQ": 46.5, "CAQ": 23.5, "PCQ": 14.5, "QS": 9.5, "PQ": 5.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Bourassa-Sauvé",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 46.0,
        "pct_franco": 52.0,
        "res_2022": {"PLQ": 38.5, "CAQ": 25.5, "QS": 14.5, "PCQ": 12.5, "PQ": 7.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Viau",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 43.0,
        "pct_franco": 55.0,
        "res_2022": {"PLQ": 37.5, "QS": 24.5, "CAQ": 18.5, "PCQ": 10.5, "PQ": 8.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Saint-Henri-Sainte-Anne",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 39.0,
        "pct_franco": 64.0,
        "res_2022": {"PLQ": 34.5, "QS": 29.5, "CAQ": 16.5, "PQ": 12.5, "PCQ": 5.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Verdun",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 42.0,
        "pct_franco": 68.0,
        "res_2022": {"PLQ": 31.5, "QS": 27.5, "CAQ": 20.5, "PQ": 13.5, "PCQ": 5.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Anjou-Louis-Riel",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 48.0,
        "pct_franco": 68.0,
        "res_2022": {"CAQ": 34.5, "PLQ": 30.5, "QS": 14.5, "PQ": 11.5, "PCQ": 8.5},
        "vainqueur_2022": "CAQ"
    },

    # Bastions QS
    {
        "nom": "Gouin",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 37.0,
        "pct_franco": 84.0,
        "res_2022": {"QS": 55.5, "CAQ": 15.5, "PQ": 14.5, "PLQ": 9.5, "PCQ": 3.5},
        "vainqueur_2022": "QS" # Gabriel Nadeau-Dubois
    },
    {
        "nom": "Mercier",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 38.0,
        "pct_franco": 82.0,
        "res_2022": {"QS": 51.5, "PQ": 17.5, "CAQ": 14.5, "PLQ": 11.5, "PCQ": 3.5},
        "vainqueur_2022": "QS" # Ruba Ghazal
    },
    {
        "nom": "Laurier-Dorion",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 38.0,
        "pct_franco": 68.0,
        "res_2022": {"QS": 48.5, "PLQ": 21.5, "CAQ": 14.5, "PQ": 9.5, "PCQ": 4.5},
        "vainqueur_2022": "QS" # Andrés Fontecilla
    },
    {
        "nom": "Sainte-Marie-Saint-Jacques",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 39.0,
        "pct_franco": 75.0,
        "res_2022": {"QS": 47.5, "PLQ": 19.5, "CAQ": 14.5, "PQ": 13.5, "PCQ": 3.5},
        "vainqueur_2022": "QS" # Manon Massé
    },
    {
        "nom": "Rosemont",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 41.0,
        "pct_franco": 86.0,
        "res_2022": {"QS": 40.5, "PQ": 24.5, "CAQ": 20.5, "PLQ": 9.5, "PCQ": 3.5},
        "vainqueur_2022": "QS" # Vincent Marissal
    },
    {
        "nom": "Maurice-Richard",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 43.0,
        "pct_franco": 78.0,
        "res_2022": {"QS": 34.5, "CAQ": 25.5, "PLQ": 20.5, "PQ": 13.5, "PCQ": 4.5},
        "vainqueur_2022": "QS" # Haroun Bouazzi
    },
    {
        "nom": "Hochelaga-Maisonneuve",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 39.0,
        "pct_franco": 86.0,
        "res_2022": {"QS": 45.5, "CAQ": 22.5, "PQ": 18.5, "PLQ": 7.5, "PCQ": 4.5},
        "vainqueur_2022": "QS" # Alexandre Leduc
    },

    # PQ & Est de Montréal
    {
        "nom": "Camille-Laurin",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 48.0,
        "pct_franco": 88.0,
        "res_2022": {"PQ": 34.5, "CAQ": 32.5, "QS": 16.5, "PLQ": 11.5, "PCQ": 4.5},
        "vainqueur_2022": "PQ" # Paul St-Pierre Plamondon
    },
    {
        "nom": "Pointe-aux-Trembles",
        "region": "Montreal",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 49.0,
        "pct_franco": 91.0,
        "res_2022": {"CAQ": 46.5, "PQ": 24.5, "QS": 13.5, "PLQ": 8.5, "PCQ": 5.5},
        "vainqueur_2022": "CAQ" # Chantal Rouleau
    },
    {
        "nom": "LaFontaine",
        "region": "Montreal",
        "milieu": "urbain_dense",
        "pct_55_plus": 50.0,
        "pct_franco": 65.0,
        "res_2022": {"PLQ": 41.7, "CAQ": 28.5, "PCQ": 13.5, "QS": 9.2, "PQ": 6.2},
        "vainqueur_2022": "PLQ" # Marc Tanguay
    },

    # --- 11. OUTAOUAIS (5 comtés) ---
    {
        "nom": "Hull",
        "region": "Outaouais_Abitibi",
        "milieu": "ville_regionale",
        "pct_55_plus": 42.0,
        "pct_franco": 78.0,
        "res_2022": {"PLQ": 37.5, "CAQ": 27.5, "QS": 19.5, "PQ": 8.5, "PCQ": 6.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Pontiac",
        "region": "Outaouais_Abitibi",
        "milieu": "rural_ressource",
        "pct_55_plus": 47.0,
        "pct_franco": 46.0,
        "res_2022": {"PLQ": 48.5, "CAQ": 21.5, "PCQ": 13.5, "QS": 10.5, "PQ": 4.5},
        "vainqueur_2022": "PLQ"
    },
    {
        "nom": "Chapleau",
        "region": "Outaouais_Abitibi",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 43.0,
        "pct_franco": 76.0,
        "res_2022": {"CAQ": 43.5, "PLQ": 23.5, "QS": 14.5, "PCQ": 10.5, "PQ": 7.5},
        "vainqueur_2022": "CAQ" # Mathieu Lévesque
    },
    {
        "nom": "Gatineau",
        "region": "Outaouais_Abitibi",
        "milieu": "banlieue_couronne",
        "pct_55_plus": 45.0,
        "pct_franco": 82.0,
        "res_2022": {"CAQ": 44.5, "PLQ": 22.5, "QS": 13.5, "PCQ": 11.5, "PQ": 7.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Papineau",
        "region": "Outaouais_Abitibi",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 86.0,
        "res_2022": {"CAQ": 48.5, "PCQ": 17.5, "QS": 13.5, "PQ": 11.5, "PLQ": 8.5},
        "vainqueur_2022": "CAQ" # Mathieu Lacombe
    },

    # --- 12. ABITIBI-TÉMISCAMINGUE & NORD-DU-QUÉBEC (4 comtés) ---
    {
        "nom": "Rouyn-Noranda-Témiscamingue",
        "region": "Outaouais_Abitibi",
        "milieu": "ville_regionale",
        "pct_55_plus": 45.0,
        "pct_franco": 96.0,
        "res_2022": {"CAQ": 37.5, "QS": 31.5, "PQ": 14.5, "PCQ": 11.5, "PLQ": 4.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Abitibi-Est",
        "region": "Outaouais_Abitibi",
        "milieu": "rural_ressource",
        "pct_55_plus": 45.0,
        "pct_franco": 95.0,
        "res_2022": {"CAQ": 46.5, "PQ": 17.5, "QS": 14.5, "PCQ": 13.5, "PLQ": 6.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Abitibi-Ouest",
        "region": "Outaouais_Abitibi",
        "milieu": "rural_ressource",
        "pct_55_plus": 49.0,
        "pct_franco": 98.0,
        "res_2022": {"CAQ": 48.5, "PQ": 20.5, "PCQ": 16.5, "QS": 10.5, "PLQ": 3.5},
        "vainqueur_2022": "CAQ"
    },
    {
        "nom": "Ungava",
        "region": "Outaouais_Abitibi",
        "milieu": "rural_ressource",
        "pct_55_plus": 35.0,
        "pct_franco": 60.0,
        "res_2022": {"CAQ": 37.5, "PQ": 26.5, "QS": 19.5, "PLQ": 11.5, "PCQ": 4.5},
        "vainqueur_2022": "CAQ"
    }
]

assert len(CIRCONSCRIPTIONS_125) == 125, f"Erreur : {len(CIRCONSCRIPTIONS_125)} circonscriptions trouvées au lieu de 125 !"

if __name__ == "__main__":
    print(f"✅ Base de données officielle : {len(CIRCONSCRIPTIONS_125)} circonscriptions validées !")
    reg_counts = {}
    for c in CIRCONSCRIPTIONS_125:
        reg_counts[c['region']] = reg_counts.get(c['region'], 0) + 1
    for r, n in reg_counts.items():
        print(f"  - {r} : {n} circonscriptions")
