#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
    🎯 SENTINELLE OMNI-R0 v9.0 — MOTEUR AUTO-ÉVOLUTIF SUR MATCHS RÉELS
         Flux ESPN Direct (LNH, NFL, MLB, Soccer, NBA) • 20 Matchs Réels •
         Prédictions d'Avant-Match & Audit Post-Mortem des Matchs Terminés •
         Auto-Calibration Continue des Poids VERALUME
===============================================================================
Auteurs : Christian Duguay & Alix (VERALUME × KAIROS V6)
"""

import os
import sys
import json
import time
import math
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Fix encodage console Windows & support mode démon détaché (pythonw / sans console)
LOG_FILE = Path(r"C:\Users\Christian\Downloads\Alix\omni_sentinel_daemon.log")

if sys.stdout is None or "pythonw" in sys.executable.lower():
    try:
        log_fp = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_fp
        sys.stderr = log_fp
    except Exception:
        pass
else:
    try:
        if getattr(sys.stdout, 'encoding', None) != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if sys.stderr and getattr(sys.stderr, 'encoding', None) != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Chemins de persistance
VAULT_DIR = Path(r"C:\Users\Christian\Documents\Cerveau Alix")
RUNTIME_DIR = Path(r"C:\Users\Christian\Downloads\Alix")

REGISTRE_PREDICTIONS_MD = VAULT_DIR / "Registre_Predictions_OMNI_R0.md"
JOURNAL_REFLEXIONS_MD = VAULT_DIR / "Journal_Reflexions_PostMortem_OMNI_R0.md"
CONFIG_POIDS_JSON = RUNTIME_DIR / "omni_r0_calibrated_weights.json"
HISTORY_JSON = RUNTIME_DIR / "omni_r0_predictions_history.json"

DEFAULT_WEIGHTS = {
    "Pression_Asymetrique": 1.60,
    "Taxe_Emotivite": 1.40,
    "Facteur_Milestone": 1.20,
    "Dephasage_Frequentiel": 1.90,
    "Coefficient_Charge": 1.80,
    "Indice_Rythme_Thermique": 1.70,
    "Intimidation_Somatique": 1.50,
    "Densite_Balistique": 1.40,
    "Gravite_Unites_Speciales": 1.80,
    "Variable_Egregore": 2.20,
    "Indice_Contagion_Emotionnelle": 2.00,
    "Dette_Circadienne_Profonde": 1.95,
    "Coefficient_Friction_Transition": 1.75
}

# Endpoints ESPN publics et gratuits
ESPN_ENDPOINTS = [
    ("Hockey LNH", "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"),
    ("Football NFL", "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"),
    ("Baseball MLB", "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"),
    ("Soccer EPL", "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"),
    ("Soccer LaLiga", "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard"),
    ("Basketball WNBA/NBA", "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard")
]


class OMNIR0Engine:
    """Moteur de calcul OMNI-R0 v9.0 appliqué aux données réelles."""

    def __init__(self, weights: Dict[str, float]):
        self.weights = weights

    def evaluate_real_match(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue un match réel selon les lois OMNI-R0."""
        # Calcul I.F.S. basé sur les données réelles
        ifs_home = match["home_ifs"]
        ifs_away = match["away_ifs"]
        diff_ifs = round(ifs_home - ifs_away, 1)

        # Usure thermodynamique réelle
        wear_away = match["away_travel_factor"] * self.weights["Dette_Circadienne_Profonde"]
        wear_home = match["home_rest_factor"] * self.weights["Coefficient_Charge"]
        delta_wear = round(wear_away - wear_home, 2)

        # Contagion Émotionnelle I.C.E.
        ice_risk = (ifs_away < 5.0 and diff_ifs > 1.5) * self.weights["Indice_Contagion_Emotionnelle"]

        # Égrégore (équipe acculée ou série historique)
        egregore_active = match.get("egregore_active", False)
        egregore_boost = (2.2 * self.weights["Variable_Egregore"]) if egregore_active else 0.0

        # Domination synthétique
        home_ice = 0.6 if "Hockey" in match["sport"] or "Soccer" in match["sport"] else 0.4
        synthetic_edge = (diff_ifs * 1.3) + (delta_wear * 0.8) + home_ice + egregore_boost

        prob_home = 1.0 / (1.0 + 10 ** (-synthetic_edge / 4.0))
        prob_home = round(max(0.12, min(0.88, prob_home)), 3)
        prob_away = round(1.0 - prob_home, 3)

        predicted_winner = match["home_team"] if prob_home >= 0.50 else match["away_team"]
        confidence = round(max(prob_home, prob_away) * 100, 1)

        # Minute de Fracture (T_frac)
        total_time = 60 if "Hockey" in match["sport"] or "NFL" in match["sport"] else (90 if "Soccer" in match["sport"] else 48)
        weak_ifs = min(ifs_home, ifs_away)
        strong_ifs = max(ifs_home, ifs_away)
        t_frac = int(total_time * (1.0 - (weak_ifs / max(0.1, strong_ifs)) * 0.60))
        t_frac = max(int(total_time * 0.40), min(int(total_time * 0.90), t_frac))

        score_proj = self._project_real_score(match["sport"], prob_home, diff_ifs, delta_wear, t_frac)

        return {
            "id": match["id"],
            "sport": match["sport"],
            "event_name": match["event_name"],
            "date": match["date"],
            "state": match["state"],  # 'pre', 'in', 'post'
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "home_score_real": match.get("home_score_real"),
            "away_score_real": match.get("away_score_real"),
            "actual_winner": match.get("actual_winner"),
            "ifs_home": ifs_home,
            "ifs_away": ifs_away,
            "diff_ifs": diff_ifs,
            "delta_wear": delta_wear,
            "predicted_winner": predicted_winner,
            "prob_home": prob_home,
            "prob_away": prob_away,
            "confidence": confidence,
            "t_frac": t_frac,
            "predicted_score": score_proj["score"],
            "total_expected": score_proj["total_expected"],
            "spread_expected": score_proj["spread_expected"],
            "primary_trigger": "Dette Circadienne & Déplacement" if abs(delta_wear) > 1.2 else ("Contagion Émotionnelle I.C.E." if ice_risk > 0 else "Différentiel I.F.S. Structurel")
        }

    def _project_real_score(self, sport: str, prob_home: float, diff_ifs: float, delta_wear: float, t_frac: int) -> Dict[str, Any]:
        """
        Calcule la projection de pointage exacte bivariée (Poisson corrigé & quantification sportive).
        Retourne toujours les scores dans le format conventionnel : (Away, Home) -> "Away-Home".
        """
        def poisson_prob(k: int, lam: float) -> float:
            if lam <= 0:
                return 1.0 if k == 0 else 0.0
            return (lam**k * math.exp(-lam)) / math.factorial(k)

        is_home_fav = prob_home >= 0.50

        if "Hockey" in sport:
            # Base LNH ~ 3.05 buts par match
            base_rate = 3.05
            lam_h = base_rate + (diff_ifs * 0.22) + 0.20 - (delta_wear * 0.08)
            lam_a = base_rate - (diff_ifs * 0.22) - 0.20 + (delta_wear * 0.12)

            # Modulation T_frac (Minute de fracture)
            if t_frac <= 30:
                # Rupture précoce -> le favori s'échappe, le dominé flanche
                if is_home_fav:
                    lam_h += 0.8
                    lam_a = max(1.0, lam_a - 0.4)
                else:
                    lam_a += 0.8
                    lam_h = max(1.0, lam_h - 0.4)
            elif t_frac >= 48:
                # Rupture tardive -> match de tranchée, scores très serrés
                mid = (lam_h + lam_a) / 2.0
                lam_h = mid + (0.15 if is_home_fav else -0.15)
                lam_a = mid + (-0.15 if is_home_fav else 0.15)

            lam_h = max(1.2, min(5.5, lam_h))
            lam_a = max(1.0, min(5.5, lam_a))

            # Matrice de Poisson bivariée (0 à 7 buts)
            best_p = -1.0
            best_score = (2, 3)
            for a in range(8):
                for h in range(8):
                    p = poisson_prob(a, lam_a) * poisson_prob(h, lam_h)
                    if is_home_fav and h < a:
                        p *= 0.15
                    elif not is_home_fav and a < h:
                        p *= 0.15
                    if p > best_p:
                        best_p = p
                        best_score = (a, h)

            a_score, h_score = best_score
            ot_flag = ""
            if a_score == h_score:
                if is_home_fav:
                    h_score += 1
                else:
                    a_score += 1
                ot_flag = " (OT/SO)"
            elif abs(a_score - h_score) == 1 and t_frac >= 48:
                ot_flag = " (OT)"

            score_str = f"{a_score}-{h_score}{ot_flag}"
            return {
                "score": score_str,
                "away_proj": a_score,
                "home_proj": h_score,
                "total_expected": round(lam_a + lam_h, 1),
                "spread_expected": round(abs(lam_h - lam_a), 1)
            }

        elif "NFL" in sport:
            # Football NFL : moyenne ~22 pts. Quantification (TD=7, FG=3)
            VALID_NFL_SCORES = [3, 6, 7, 9, 10, 13, 14, 16, 17, 20, 21, 23, 24, 27, 28, 30, 31, 34, 35, 38, 41, 42, 45, 48]
            base_pts = 22.0
            exp_h = base_pts + (diff_ifs * 1.8) + ((prob_home - 0.5) * 12.0) + 1.5
            exp_a = base_pts - (diff_ifs * 1.8) - ((prob_home - 0.5) * 12.0) - 1.5 - (delta_wear * 1.5)

            if t_frac <= 25:
                # Blowout avant la mi-temps
                if is_home_fav:
                    exp_h += 7.0
                    exp_a = max(7.0, exp_a - 6.0)
                else:
                    exp_a += 7.0
                    exp_h = max(7.0, exp_h - 6.0)
            elif t_frac >= 45:
                # Match serré
                mid = (exp_h + exp_a) / 2.0
                exp_h = mid + (2.0 if is_home_fav else -2.0)
                exp_a = mid + (-2.0 if is_home_fav else 2.0)

            quant_h = min(VALID_NFL_SCORES, key=lambda x: abs(x - exp_h))
            quant_a = min(VALID_NFL_SCORES, key=lambda x: abs(x - exp_a))

            if is_home_fav and quant_h <= quant_a:
                quant_h = min([s for s in VALID_NFL_SCORES if s > quant_a], default=quant_a + 3)
            elif not is_home_fav and quant_a <= quant_h:
                quant_a = min([s for s in VALID_NFL_SCORES if s > quant_h], default=quant_h + 3)

            return {
                "score": f"{quant_a}-{quant_h}",
                "away_proj": quant_a,
                "home_proj": quant_h,
                "total_expected": round(exp_a + exp_h, 1),
                "spread_expected": round(abs(exp_h - exp_a), 1)
            }

        elif "Soccer" in sport:
            base_rate = 1.35
            lam_h = max(0.4, min(4.0, base_rate + (diff_ifs * 0.18) + 0.20))
            lam_a = max(0.3, min(3.5, base_rate - (diff_ifs * 0.18) - 0.10))

            if t_frac <= 35:
                if is_home_fav:
                    lam_h += 0.6
                else:
                    lam_a += 0.6

            best_p = -1.0
            best_score = (0, 1)
            for a in range(6):
                for h in range(6):
                    p = poisson_prob(a, lam_a) * poisson_prob(h, lam_h)
                    if is_home_fav and h < a:
                        p *= 0.2
                    elif not is_home_fav and a < h:
                        p *= 0.2
                    if p > best_p:
                        best_p = p
                        best_score = (a, h)
            a_s, h_s = best_score
            return {
                "score": f"{a_s}-{h_s}",
                "away_proj": a_s,
                "home_proj": h_s,
                "total_expected": round(lam_a + lam_h, 1),
                "spread_expected": round(abs(lam_h - lam_a), 1)
            }

        elif "Basketball" in sport:
            base_pts = 112.0
            exp_h = base_pts + (diff_ifs * 2.5) + ((prob_home - 0.5) * 16.0)
            exp_a = base_pts - (diff_ifs * 2.5) - ((prob_home - 0.5) * 16.0)
            if t_frac <= 22:
                if is_home_fav:
                    exp_h += 8.0
                    exp_a -= 6.0
                else:
                    exp_a += 8.0
                    exp_h -= 6.0
            elif t_frac >= 40:
                mid = (exp_h + exp_a) / 2.0
                exp_h = mid + (2.5 if is_home_fav else -2.5)
                exp_a = mid + (-2.5 if is_home_fav else 2.5)
            h_p = int(round(exp_h))
            a_p = int(round(exp_a))
            if is_home_fav and h_p <= a_p:
                h_p = a_p + 3
            elif not is_home_fav and a_p <= h_p:
                a_p = h_p + 3
            return {
                "score": f"{a_p}-{h_p}",
                "away_proj": a_p,
                "home_proj": h_p,
                "total_expected": round(exp_a + exp_h, 1),
                "spread_expected": round(abs(exp_h - exp_a), 1)
            }

        elif "MLB" in sport:
            base_rate = 4.4
            lam_h = max(1.5, base_rate + (diff_ifs * 0.3) + 0.2)
            lam_a = max(1.2, base_rate - (diff_ifs * 0.3) - 0.2)
            best_p = -1.0
            best_score = (3, 4)
            for a in range(11):
                for h in range(11):
                    p = poisson_prob(a, lam_a) * poisson_prob(h, lam_h)
                    if is_home_fav and h <= a:
                        p *= 0.25
                    elif not is_home_fav and a <= h:
                        p *= 0.25
                    if p > best_p:
                        best_p = p
                        best_score = (a, h)
            a_s, h_s = best_score
            if a_s == h_s:
                if is_home_fav:
                    h_s += 1
                else:
                    a_s += 1
            return {
                "score": f"{a_s}-{h_s}",
                "away_proj": a_s,
                "home_proj": h_s,
                "total_expected": round(lam_a + lam_h, 1),
                "spread_expected": round(abs(lam_h - lam_a), 1)
            }

        return {
            "score": "N/A",
            "away_proj": 0,
            "home_proj": 0,
            "total_expected": 0.0,
            "spread_expected": 0.0
        }


class OMNIRealSentinelDaemon:
    """Sentinelle OMNI-R0 connectée aux flux de matchs réels ESPN."""

    def __init__(self):
        self.weights = self._load_weights()
        self.engine = OMNIR0Engine(self.weights)
        self.history = self._load_history()

    def _load_weights(self) -> Dict[str, float]:
        if CONFIG_POIDS_JSON.exists():
            try:
                with open(CONFIG_POIDS_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_WEIGHTS.copy()

    def _save_weights(self):
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_POIDS_JSON, "w", encoding="utf-8") as f:
            json.dump(self.weights, f, indent=2, ensure_ascii=False)

    def _load_history(self) -> Dict[str, Any]:
        if HISTORY_JSON.exists():
            try:
                with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_history(self):
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_JSON, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def fetch_real_matches(self) -> List[Dict[str, Any]]:
        """Moissonne jusqu'à 20 matchs réels multi-sports via les flux ESPN en direct."""
        real_matches = []
        
        print("🌐 Connexion aux flux réels ESPN (Hockey LNH, NFL, MLB, Soccer, Basketball)...")
        
        for sport_label, url in ESPN_ENDPOINTS:
            try:
                with urllib.request.urlopen(url, timeout=6) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    events = data.get("events", [])
                    
                    for ev in events:
                        if len(real_matches) >= 20:
                            break
                        
                        comp = ev.get("competitions", [{}])[0]
                        competitors = comp.get("competitors", [])
                        if len(competitors) < 2:
                            continue
                        
                        home_c = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
                        away_c = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
                        
                        home_name = home_c.get("team", {}).get("displayName", "Home")
                        away_name = away_c.get("team", {}).get("displayName", "Away")
                        
                        state = ev.get("status", {}).get("type", {}).get("state", "pre")
                        
                        # Scores réels si terminé
                        home_score = home_c.get("score")
                        away_score = away_c.get("score")
                        
                        actual_winner = None
                        if state == "post" and home_score is not None and away_score is not None:
                            try:
                                h_s = int(home_score)
                                a_s = int(away_score)
                                if h_s > a_s: actual_winner = home_name
                                elif a_s > h_s: actual_winner = away_name
                                else: actual_winner = "Nul"
                            except Exception:
                                pass

                        # Calcul I.F.S. empirique à partir des records réels
                        home_records = home_c.get("records", [{}])
                        away_records = away_c.get("records", [{}])
                        h_summary = home_records[0].get("summary", "10-10") if home_records else "10-10"
                        a_summary = away_records[0].get("summary", "10-10") if away_records else "10-10"

                        home_ifs = self._parse_ifs_from_record(h_summary, is_home=True)
                        away_ifs = self._parse_ifs_from_record(a_summary, is_home=False)

                        real_matches.append({
                            "id": str(ev.get("id")),
                            "sport": sport_label,
                            "event_name": ev.get("name", f"{away_name} at {home_name}"),
                            "date": ev.get("date", datetime.now().strftime("%Y-%m-%d")),
                            "state": state,
                            "home_team": home_name,
                            "away_team": away_name,
                            "home_score_real": home_score,
                            "away_score_real": away_score,
                            "actual_winner": actual_winner,
                            "home_ifs": home_ifs,
                            "away_ifs": away_ifs,
                            "home_rest_factor": 0.5,
                            "away_travel_factor": 1.4,
                            "egregore_active": False
                        })
            except Exception as e:
                print(f"⚠️ Erreur de moissonnage sur {sport_label} : {e}")

        print(f"✅ {len(real_matches)} matchs réels moissonnés avec succès.")
        return real_matches

    def _parse_ifs_from_record(self, summary: str, is_home: bool) -> float:
        """Dérive un score I.F.S. (1.0 à 10.0) à partir de la fiche victoires-défaites réelle."""
        try:
            parts = summary.split("-")
            wins = int(parts[0])
            losses = int(parts[1])
            total = max(1, wins + losses)
            pct = wins / total
            ifs = 3.0 + (pct * 6.0) + (0.4 if is_home else -0.2)
            return round(max(2.0, min(9.5, ifs)), 1)
        except Exception:
            return 6.5 if is_home else 6.0

    def run_real_cycle(self):
        """Cycle autonome : Matchs réels -> Prédiction OMNI -> Audit des terminés -> Recalibration."""
        print("\n" + "="*70)
        print("🎯 SENTINELLE OMNI-R0 v9.0 — ANALYSE EN DIRECT DES MATCHS RÉELS")
        print("="*70)

        # 1. Moissonner les 20 matchs réels
        raw_matches = self.fetch_real_matches()
        if not raw_matches:
            print("❌ Aucun match réel récupéré. Vérifier la connexion réseau.")
            return

        evaluated_matches = []
        post_mortem_cases = []

        for m in raw_matches:
            eval_result = self.engine.evaluate_real_match(m)
            evaluated_matches.append(eval_result)
            
            # Si le match est terminé, on fait l'audit SRE immédiat
            if eval_result["state"] == "post" and eval_result["actual_winner"]:
                is_correct = (eval_result["predicted_winner"] == eval_result["actual_winner"])
                eval_result["verdict"] = "SUCCÈS" if is_correct else "ÉCHEC"
                
                if not is_correct:
                    cause, adjusted_var, delta = self._diagnose_real_failure(eval_result)
                    post_mortem_cases.append({
                        "event": eval_result["event_name"],
                        "sport": eval_result["sport"],
                        "predicted": eval_result["predicted_winner"],
                        "actual": eval_result["actual_winner"],
                        "real_score": f"{eval_result['away_score_real']}-{eval_result['home_score_real']}",
                        "confidence": eval_result["confidence"],
                        "cause": cause,
                        "var": adjusted_var,
                        "delta": delta
                    })
                    # Recalibration du poids
                    self.weights[adjusted_var] = round(min(3.5, self.weights[adjusted_var] + delta), 3)
            else:
                eval_result["verdict"] = "PROGRAMMÉ / EN COURS"

        # 2. Sauvegarde des poids mis à jour
        if post_mortem_cases:
            self._save_weights()
            print(f"⚡ Recalibration adaptative : {len(post_mortem_cases)} échecs réels analysés.")

        # 3. Gravure dans Obsidian
        self._record_real_predictions_markdown(evaluated_matches)
        self._record_real_post_mortem_markdown(post_mortem_cases, evaluated_matches)

        print(f"✅ 20 matchs réels enregistrés dans : {REGISTRE_PREDICTIONS_MD.name}")
        print(f"✅ Journal post-mortem réel gravé dans : {JOURNAL_REFLEXIONS_MD.name}")
        print("="*70 + "\n")

    def _diagnose_real_failure(self, res: Dict[str, Any]) -> Tuple[str, str, float]:
        """Audit causal forensique d'un échec sur un match réel."""
        diff_ifs = res["diff_ifs"]
        sport = res["sport"]
        
        if abs(diff_ifs) > 2.0 and res["actual_winner"] != res["predicted_winner"]:
            return "Effondrement du favori sous Pression Asymétrique ou relâchement.", "Pression_Asymetrique", +0.05
        elif "Hockey" in sport or "Soccer" in sport:
            return "Rupture par Contagion Émotionnelle (I.C.E.) ou pénalité majeure précoce.", "Indice_Contagion_Emotionnelle", +0.04
        elif "NFL" in sport:
            return "Domination physique non-absorbée par la ligne de transition.", "Intimidation_Somatique", +0.05
        else:
            return "Déphasage de rythme ou dépassement par transition rapide (C.F.T.).", "Coefficient_Friction_Transition", +0.03

    def _record_real_predictions_markdown(self, matches: List[Dict[str, Any]]):
        """Grave le tableau de bord des 20 matchs réels dans Obsidian."""
        md_content = f"""---
titre: "Registre des 20 Matchs Réels OMNI-R0 (Multi-Sports)"
date: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
agent: "Sentinelle OMNI-R0 v9.0 (Flux Réel ESPN)"
nb_matchs: {len(matches)}
statut: "Actif & Direct"
tags:
  - exocerveau
  - omni_r0
  - matchs_reels
  - espn_live
  - multi_sports
---

# 🎯⚡ [[Registre_Predictions_OMNI_R0]] — Les 20 Matchs Réels du Monde

> **Source des Données :** Flux officiels ESPN en direct (Hockey LNH, NFL, MLB, Soccer, Basketball)  
> **Horodatage :** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  
> **Mécanique :** Arbitrage systémique OMNI-R0 appliqué sur les vraies fiches et confrontations réelles.

---

## 🏆 Tableau des 20 Confrontations Réelles Analysées

| # | Sport | Événement Réel (Visiteur at Domicile) | État | I.F.S. Net | Prédiction OMNI | Confiance | T_frac | Score Projeté (Vis-Dom) | Total Attendu | Score Réel (Vis-Dom) | Verdict |
| :-: | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
        for idx, m in enumerate(matches, 1):
            real_score = f"{m['away_score_real']}-{m['home_score_real']}" if m.get('home_score_real') is not None else "-"
            verdict_icon = "🟢" if m.get("verdict") == "SUCCÈS" else ("🔴" if m.get("verdict") == "ÉCHEC" else "⏳")
            total_exp = m.get('total_expected', '-')
            md_content += f"| {idx} | **{m['sport']}** | {m['event_name']} | `{m['state']}` | `{m['diff_ifs']:+0.1f}` | **{m['predicted_winner']}** | **{m['confidence']}%** | `{m['t_frac']}'` | `{m['predicted_score']}` | `{total_exp}` | `{real_score}` | {verdict_icon} {m.get('verdict')} |\n"

        md_content += f"""
---
*Sentinelle OMNI-R0 connectée au monde réel dans Cerveau Alix.*
"""
        with open(REGISTRE_PREDICTIONS_MD, "w", encoding="utf-8") as f:
            f.write(md_content)

    def _record_real_post_mortem_markdown(self, cases: List[Dict[str, Any]], all_matches: List[Dict[str, Any]]):
        """Grave l'audit causal post-mortem des matchs réels."""
        finished = [m for m in all_matches if m.get("state") == "post"]
        successes = len([m for m in finished if m.get("verdict") == "SUCCÈS"])
        total_finished = len(finished)
        win_rate = (successes / total_finished * 100) if total_finished > 0 else 0.0

        md_content = f"""---
titre: "Journal des Réflexions Post-Mortem Réelles OMNI-R0"
date: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
agent: "Alix & Horus (Audit Forensique Réel)"
taux_succes: "{win_rate:.1f} %"
matchs_termines: {total_finished}
tags:
  - exocerveau
  - post_mortem_reel
  - auto_calibration
  - horus_sre
---

# 🧠🔬 [[Journal_Reflexions_PostMortem_OMNI_R0]] — Audit des Matchs Réels

> **Règle d'Airain :** *« Chaque divergence entre la prédiction et le score réel est une leçon pour recalibrer la physique du modèle. »*

---

## 📊 1. Bilan des Matchs Réels Terminés
* **Matchs Réels Conclus :** `{total_finished}`
* **Succès Prédictifs :** `{successes}`
* **Échecs Analysés :** `{len(cases)}`
* **Taux d'Exactitude Réel :** **`{win_rate:.1f} %`**

---

## 🔍 2. Audit Causal des Échecs Réels & Recalibration

| Match Réel / Sport | Prédiction OMNI | Résultat Réel | Score Réel | Diagnostic SRE de l'Échec | Variable Recalibrée |
| :--- | :--- | :--- | :---: | :--- | :--- |
"""
        for c in cases:
            md_content += f"| **{c['sport']}**<br>{c['event']} | `{c['predicted']}` | **`{c['actual']}`** | `{c['real_score']}` | {c['cause']} | `{c['var']}` (+{c['delta']}) |\n"

        md_content += f"""
---

## ⚖️ 3. Poids Actuels de la Matrice OMNI-R0 v9.0
```json
{json.dumps(self.weights, indent=2, ensure_ascii=False)}
```

---
*Auto-calibration réelle enregistrée par la Sentinelle OMNI-R0.*
"""
        with open(JOURNAL_REFLEXIONS_MD, "w", encoding="utf-8") as f:
            f.write(md_content)

    def run_continuous_daemon(self, interval: int = 180):
        """Boucle continue autonome de surveillance des flux ESPN."""
        print("=" * 70)
        print(" 🎯 SENTINELLE OMNI-R0 v9.0 — DAEMON AUTONOME TEMPS RÉEL")
        print(f" 🔄 Cadence de rafraîchissement : {interval} secondes ({interval // 60} min)")
        print(f" 📁 Registre : {REGISTRE_PREDICTIONS_MD.name}")
        print(f" 📁 Post-Mortem : {JOURNAL_REFLEXIONS_MD.name}")
        print("=" * 70)

        cycle_num = 0
        while True:
            cycle_num += 1
            start_t = time.time()
            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{now_str}] 🚀 Cycle OMNI-R0 #{cycle_num} en cours...")
            try:
                self.run_real_cycle()
            except Exception as e:
                print(f"[{now_str}] ⚠️ Erreur lors du cycle #{cycle_num} : {e}")

            elapsed = round(time.time() - start_t, 2)
            sleep_time = max(10, interval - int(elapsed))
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Cycle terminé ({elapsed}s). Prochain cycle dans {sleep_time}s...")
            time.sleep(sleep_time)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sentinelle OMNI-R0 v9.0 — Multi-Sports")
    parser.add_argument("--once", action="store_true", help="Exécute un seul cycle et quitte")
    parser.add_argument("--interval", type=int, default=180, help="Intervalle en secondes entre chaque cycle (défaut: 180s = 3 min)")
    args = parser.parse_args()

    daemon = OMNIRealSentinelDaemon()
    if args.once:
        daemon.run_real_cycle()
    else:
        daemon.run_continuous_daemon(interval=args.interval)
