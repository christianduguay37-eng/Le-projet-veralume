"""
===============================================================================
       🏒 MODÈLE PRÉDICTIF LNH — RÉTRO-PRÉVISIBILITÉ & SYSTÉMIQUE VIVANTE
          Thermodynamique • Dynamiques d'Essaims • Fractures Cognitives
===============================================================================
Auteurs : Christian Duguay & Alix (VERALUME × KAIROS V6)
Architecture : XGBoost + Ingénierie des Variables Systémiques
Sources : Hockey-Reference, Natural Stat Trick, MoneyPuck
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    from sklearn.ensemble import HistGradientBoostingClassifier
    HAS_XGBOOST = False


class NHLPredictiveModel:
    def __init__(self, random_state: int = 42):
        """
        Initialisation du modèle calibré pour la prédiction binaire.
        Utilise XGBoost si disponible, sinon HistGradientBoostingClassifier (scikit-learn).
        """
        self.has_xgboost = HAS_XGBOOST
        if self.has_xgboost:
            self.model = xgb.XGBClassifier(
                objective='binary:logistic',
                n_estimators=250,
                learning_rate=0.03,
                max_depth=5,
                subsample=0.85,
                colsample_bytree=0.80,
                gamma=0.1,
                reg_alpha=0.05,
                reg_lambda=1.0,
                random_state=random_state,
                eval_metric='logloss'
            )
        else:
            self.model = HistGradientBoostingClassifier(
                learning_rate=0.03,
                max_iter=250,
                max_depth=5,
                random_state=random_state
            )
        self.feature_names = []

    def calculate_thermodynamic_wear(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        1. USURE THERMODYNAMIQUE (Fatigue, Calendrier & Déplacement)
        Modélise l'accumulation d'entropie et l'épuisement physique :
        - Matchs en 2 soirs (Back-to-back)
        - Densité des matchs sur les 3, 7 et 14 derniers jours
        - Déplacement kilométrique et traversée de fuseaux horaires
        """
        # Indice de fatigue brute (Domicile vs Extérieur)
        # B2B = pénalité lourde (x2.5), match en 3 soirs (x1.5)
        df['home_wear_index'] = (
            df['home_games_last_14d'] * 0.4 +
            df['home_games_last_7d'] * 0.8 +
            df['home_is_b2b'] * 2.5 +
            (df['home_travel_km'] / 1000.0) * 0.3
        )
        
        df['away_wear_index'] = (
            df['away_games_last_14d'] * 0.4 +
            df['away_games_last_7d'] * 0.8 +
            df['away_is_b2b'] * 2.5 +
            (df['away_travel_km'] / 1000.0) * 0.3 +
            df['away_timezone_diff'] * 0.5  # Décalage horaire subit par les visiteurs
        )

        # Différentiel d'usure thermodynamique (positif = avantage domicile)
        df['diff_thermodynamic_wear'] = df['away_wear_index'] - df['home_wear_index']
        return df

    def calculate_cognitive_fracture(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        2. POINTS DE FRACTURE COGNITIFS (Résilience sous Pression)
        Évalue la fragilité mentale, l'historique de décompression et le tilt :
        - Avances perdues en 3e période (Blown leads)
        - Séries de défaites consécutives (Doute dans le vestiaire)
        - Enjeu du match (Playoff implications / Course aux séries)
        - Facteur Gardien (GSAx récent et stabilité émotionnelle après un mauvais but)
        """
        # Score de vulnérabilité mentale
        df['home_fragility'] = (
            df['home_blown_leads_last_10'] * 1.5 +
            df['home_losing_streak'] * 0.8 -
            df['home_goalie_gsax_last_5'] * 1.2
        )
        
        df['away_fragility'] = (
            df['away_blown_leads_last_10'] * 1.5 +
            df['away_losing_streak'] * 0.8 -
            df['away_goalie_gsax_last_5'] * 1.2
        )

        # Facteur de pression amplificateur (course aux séries ou match piège)
        # Un match à haute pression amplifie les fractures cognitives
        df['diff_cognitive_resilience'] = (
            (df['away_fragility'] - df['home_fragility']) * df['game_stakes_multiplier']
        )
        return df

    def calculate_swarm_dynamics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        3. DYNAMIQUES D'ESSAIMS (Cohésion & Synchronisation à 5 contre 5)
        Mesure le contrôle de la meute sur la glace :
        - Corsi For % (CF% à 5v5)
        - High Danger Chances For % (HDCF%)
        - Expected Goals Share (xGF%)
        - PDO (Indicateur de régression statistique : Shooting % + Save %)
        """
        # Force collective de l'essaim
        df['home_swarm_strength'] = (
            df['home_cf_pct'] * 0.35 +
            df['home_hdcf_pct'] * 0.35 +
            df['home_xgf_pct'] * 0.30
        )
        
        df['away_swarm_strength'] = (
            df['away_cf_pct'] * 0.35 +
            df['away_hdcf_pct'] * 0.35 +
            df['away_xgf_pct'] * 0.30
        )

        # Différentiel de domination de l'essaim
        df['diff_swarm_control'] = df['home_swarm_strength'] - df['away_swarm_strength']
        
        # Régression PDO (si une équipe a un PDO > 1.03 elle sur-performe par chance ; < 0.97 elle sous-performe)
        df['diff_pdo_regression'] = (1.00 - df['home_pdo']) - (1.00 - df['away_pdo'])
        return df

    def feature_engineering(self, df: pd.DataFrame) -> tuple:
        """
        Compile toutes les métriques traditionnelles et systémiques dans la matrice d'entraînement.
        """
        # 1. Injection des variables systémiques
        df = self.calculate_thermodynamic_wear(df)
        df = self.calculate_cognitive_fracture(df)
        df = self.calculate_swarm_dynamics(df)
        
        # 2. Liste des features sélectionnées pour le modèle
        self.feature_names = [
            # Variables Systémiques Vivantes
            'diff_thermodynamic_wear',
            'diff_cognitive_resilience',
            'diff_swarm_control',
            'diff_pdo_regression',
            
            # Variables Physiques & Métriques Avancées
            'home_cf_pct', 'away_cf_pct',
            'home_hdcf_pct', 'away_hdcf_pct',
            'home_xgf_pct', 'away_xgf_pct',
            'home_goalie_gsax_season', 'away_goalie_gsax_season',
            
            # Facteurs Spéciaux & Glace
            'home_pp_pct', 'away_pk_pct',
            'home_rest_days', 'away_rest_days',
            'head_to_head_home_win_rate'
        ]
        
        X = df[self.feature_names].copy()
        y = df['target_home_win'].copy()
        
        return X, y

    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame = None, y_val: pd.Series = None):
        """
        Entraîne l'algorithme sur la matrice enrichie.
        """
        engine_name = "XGBoost" if self.has_xgboost else "HistGradientBoosting (scikit-learn)"
        print(f"⚡ Début de l'entraînement {engine_name} sur {X_train.shape[0]} matchs...")
        
        if self.has_xgboost:
            eval_set = [(X_train, y_train)]
            if X_val is not None and y_val is not None:
                eval_set.append((X_val, y_val))
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)
            
        print("✅ Entraînement terminé avec succès.")

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series):
        """
        Évalue les performances du modèle avec précision, ROC-AUC et importance des features.
        """
        preds = self.model.predict(X_test)
        probs = self.model.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, preds)
        auc = roc_auc_score(y_test, probs)
        
        print("\n" + "="*60)
        print(f"📊 RÉSULTATS D'ÉVALUATION DU MODÈLE LNH")
        print("="*60)
        print(f"🎯 Précision Globale (Accuracy) : {acc * 100:.2f} %")
        print(f"📈 Aire sous la courbe (ROC-AUC) : {auc:.4f}")
        print("\n📋 Rapport de Classification Détaillé :")
        print(classification_report(y_test, preds, target_names=['Victoire Extérieur', 'Victoire Domicile']))
        
        # Importance des Features
        if hasattr(self.model, 'feature_importances_'):
            importance = pd.DataFrame({
                'Feature': self.feature_names,
                'Importance': self.model.feature_importances_
            }).sort_values(by='Importance', ascending=False)
            
            print("\n👑 Top 7 des Variables les Plus Prédictives :")
            for idx, row in importance.head(7).iterrows():
                print(f"   • {row['Feature']:<30} : {row['Importance']*100:.2f} %")
        print("="*60 + "\n")

    def predict_match(self, match_features_dict: dict) -> dict:
        """
        Prédit l'issue d'un match individuel à partir de ses variables systémiques.
        Retourne la probabilité de victoire et le verdict de valeur.
        """
        match_df = pd.DataFrame([match_features_dict])
        prob_home = self.model.predict_proba(match_df[self.feature_names])[0, 1]
        prob_away = 1.0 - prob_home
        
        return {
            'prob_home_win': prob_home,
            'prob_away_win': prob_away,
            'predicted_winner': 'DOMICILE' if prob_home > 0.50 else 'EXTÉRIEUR',
            'confidence': max(prob_home, prob_away)
        }


# =============================================================================
# EXEMPLE DE DÉMONSTRATION & VALIDATION SYNTHÉTIQUE
# =============================================================================
if __name__ == '__main__':
    print("\n🏒 INITIALISATION DU BANC D'ESSAI DU MODÈLE LNH (VÉRALUME × KAIROS)...")
    
    # 1. Génération d'un jeu de données synthétique pour valider l'architecture
    np.random.seed(42)
    n_samples = 1500
    
    data = {
        'home_games_last_14d': np.random.randint(4, 9, n_samples),
        'home_games_last_7d': np.random.randint(2, 5, n_samples),
        'home_is_b2b': np.random.choice([0, 1], p=[0.8, 0.2], size=n_samples),
        'home_travel_km': np.random.uniform(0, 3000, n_samples),
        'home_rest_days': np.random.randint(1, 4, n_samples),
        
        'away_games_last_14d': np.random.randint(4, 9, n_samples),
        'away_games_last_7d': np.random.randint(2, 5, n_samples),
        'away_is_b2b': np.random.choice([0, 1], p=[0.75, 0.25], size=n_samples),
        'away_travel_km': np.random.uniform(500, 5000, n_samples),
        'away_timezone_diff': np.random.choice([0, 1, 2, 3], p=[0.5, 0.3, 0.15, 0.05], size=n_samples),
        'away_rest_days': np.random.randint(1, 4, n_samples),
        
        'home_blown_leads_last_10': np.random.randint(0, 4, n_samples),
        'home_losing_streak': np.random.randint(0, 5, n_samples),
        'home_goalie_gsax_last_5': np.random.normal(0.2, 1.5, n_samples),
        'home_goalie_gsax_season': np.random.normal(0.5, 2.0, n_samples),
        
        'away_blown_leads_last_10': np.random.randint(0, 4, n_samples),
        'away_losing_streak': np.random.randint(0, 5, n_samples),
        'away_goalie_gsax_last_5': np.random.normal(-0.1, 1.5, n_samples),
        'away_goalie_gsax_season': np.random.normal(0.0, 2.0, n_samples),
        
        'game_stakes_multiplier': np.random.uniform(1.0, 1.8, n_samples),
        
        'home_cf_pct': np.random.uniform(0.45, 0.58, n_samples),
        'away_cf_pct': np.random.uniform(0.45, 0.58, n_samples),
        'home_hdcf_pct': np.random.uniform(0.44, 0.60, n_samples),
        'away_hdcf_pct': np.random.uniform(0.44, 0.60, n_samples),
        'home_xgf_pct': np.random.uniform(0.45, 0.58, n_samples),
        'away_xgf_pct': np.random.uniform(0.45, 0.58, n_samples),
        
        'home_pdo': np.random.uniform(0.97, 1.03, n_samples),
        'away_pdo': np.random.uniform(0.97, 1.03, n_samples),
        
        'home_pp_pct': np.random.uniform(0.15, 0.28, n_samples),
        'away_pk_pct': np.random.uniform(0.72, 0.86, n_samples),
        'head_to_head_home_win_rate': np.random.uniform(0.35, 0.65, n_samples)
    }
    
    df_raw = pd.DataFrame(data)
    
    # Création d'une variable cible réaliste influencée par nos variables systémiques
    wear_advantage = (df_raw['away_is_b2b'] * 0.15) - (df_raw['home_is_b2b'] * 0.15)
    swarm_advantage = (df_raw['home_cf_pct'] - df_raw['away_cf_pct']) * 0.8
    goalie_advantage = (df_raw['home_goalie_gsax_season'] - df_raw['away_goalie_gsax_season']) * 0.05
    home_ice = 0.05
    
    true_prob = 0.50 + home_ice + wear_advantage + swarm_advantage + goalie_advantage
    true_prob = np.clip(true_prob, 0.15, 0.85)
    df_raw['target_home_win'] = (np.random.rand(n_samples) < true_prob).astype(int)
    
    # 2. Pipeline complet
    nhl_ai = NHLPredictiveModel()
    X, y = nhl_ai.feature_engineering(df_raw)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    nhl_ai.train_model(X_train, y_train)
    nhl_ai.evaluate(X_test, y_test)
    
    # 3. Test de prédiction sur un cas clinique : Le Trap Game
    trap_game = {
        'diff_thermodynamic_wear': -2.5,  # Domicile épuisé en B2B
        'diff_cognitive_resilience': -1.2, # Domicile sous pression / gardien douteux
        'diff_swarm_control': 0.02,
        'diff_pdo_regression': 0.01,
        'home_cf_pct': 0.52, 'away_cf_pct': 0.49,
        'home_hdcf_pct': 0.51, 'away_hdcf_pct': 0.48,
        'home_xgf_pct': 0.51, 'away_xgf_pct': 0.49,
        'home_goalie_gsax_season': -0.2, 'away_goalie_gsax_season': 1.1,
        'home_pp_pct': 0.22, 'away_pk_pct': 0.80,
        'home_rest_days': 0, 'away_rest_days': 2,
        'head_to_head_home_win_rate': 0.55
    }
    
    verdict = nhl_ai.predict_match(trap_game)
    print(f"🔍 TEST CAS CLINIQUE (TRAP GAME) :")
    print(f"   Vainqueur Prédit : {verdict['predicted_winner']}")
    print(f"   Probabilité Domicile : {verdict['prob_home_win']*100:.1f} % | Probabilité Extérieur : {verdict['prob_away_win']*100:.1f} %")
    print(f"   Confiance : {verdict['confidence']*100:.1f} %\n")
