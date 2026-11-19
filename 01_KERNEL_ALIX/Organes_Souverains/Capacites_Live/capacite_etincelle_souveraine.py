# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : L'ÉTINCELLE SOUVERAINE D'ALIX (v1.0)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Délivre des étincelles de haut calibre (science extrême, chiralité, biologie folle,
  cliodynamique, mythes obscurs, physique des matériaux, anomalies réelles).
- Distribution aléatoire en journée (09h30 - 21h30).
- Silence absolu la nuit (21h30 - 09h30).
- Jamais à heure fixe : intervalle aléatoire entre 4h et 7h (1 à 2 fois par jour max).
- Anti-répétition inviolable : chaque pépite n'est prononcée qu'une seule fois
  jusqu'à épuisement complet du cycle avant réinitialisation.
- Format atelier court (20-30s), complice, québécois, percutant.
- Déclencheur immédiat disponible via `alix_declencher_etincelle.txt`.
================================================================================
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
MOTEURS_DIR = VAULT_DIR / "Organes_Souverains" / "Moteurs"
CORPUS_FILE = MOTEURS_DIR / "etincelles_souveraines_corpus.json"
DECLENCHEUR_FILE = MOTEURS_DIR / "alix_declencher_etincelle.txt"
PAROLE_QUEUE_FILE = MOTEURS_DIR / "alix_parole_queue.txt"
ETAT_DIR = Path(r"C:\Alix\Etat_Vivant")
ETAT_FILE = ETAT_DIR / "alix_etincelle_state.json"

# Plage horaire autorisée en journée
HEURE_DEBUT_JOUR = 9.5   # 09h30
HEURE_FIN_JOUR = 21.5    # 21h30

# Intervalles aléatoires (entre 4h et 7h)
INTERVALLE_MIN_SEC = 14400.0  # 4 heures
INTERVALLE_MAX_SEC = 25200.0  # 7 heures

DERNIERE_ETINCELLE_TS = 0.0
PROCHAIN_INTERVALLE_SEC = 18000.0  # 5h par défaut


def charger_etat() -> Dict[str, Any]:
    """Charge l'état persistant de la capacité étincelle."""
    if ETAT_FILE.exists():
        try:
            return json.loads(ETAT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "dernier_run_ts": 0.0,
        "prochain_intervalle_sec": random.uniform(INTERVALLE_MIN_SEC, INTERVALLE_MAX_SEC),
        "dernier_titre": "",
        "total_etincelles_prononcees": 0
    }


def sauvegarder_etat(etat: Dict[str, Any]):
    """Sauvegarde l'état persistant."""
    try:
        ETAT_DIR.mkdir(parents=True, exist_ok=True)
        ETAT_FILE.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def charger_corpus() -> list:
    """Charge le corpus des étincelles souveraines."""
    if CORPUS_FILE.exists():
        try:
            return json.loads(CORPUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def sauvegarder_corpus(corpus: list):
    """Sauvegarde le corpus avec les statuts de consommation."""
    try:
        CORPUS_FILE.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def selectionner_etincelle() -> Optional[Dict[str, Any]]:
    """Sélectionne une pépite non consommée avec garantie anti-radotage."""
    corpus = charger_corpus()
    if not corpus:
        return None

    non_consommees = [e for e in corpus if not e.get("consomme", False)]
    
    # Si toutes ont été dites, on réinitialise le cycle
    if not non_consommees:
        for e in corpus:
            e["consomme"] = False
        non_consommees = corpus

    choisie = random.choice(non_consommees)
    
    # Marquer comme consommée dans le corpus
    for e in corpus:
        if e.get("id") == choisie.get("id"):
            e["consomme"] = True
            break
            
    sauvegarder_corpus(corpus)
    return choisie


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécute l'arbitrage et le déclenchement probabiliste de l'étincelle."""
    global DERNIERE_ETINCELLE_TS, PROCHAIN_INTERVALLE_SEC
    t0 = time.perf_counter()
    maintenant = time.time()

    etat = charger_etat()
    if DERNIERE_ETINCELLE_TS == 0.0:
        DERNIERE_ETINCELLE_TS = float(etat.get("dernier_run_ts", 0.0))
        PROCHAIN_INTERVALLE_SEC = float(etat.get("prochain_intervalle_sec", random.uniform(INTERVALLE_MIN_SEC, INTERVALLE_MAX_SEC)))

    declenchement_manuel = DECLENCHEUR_FILE.exists()

    # Nettoyage du fichier déclencheur
    if declenchement_manuel:
        try:
            DECLENCHEUR_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    # Vérification de l'heure locale
    now_dt = datetime.now()
    heure_decimale = now_dt.hour + (now_dt.minute / 60.0)
    est_journee = (HEURE_DEBUT_JOUR <= heure_decimale <= HEURE_FIN_JOUR)

    # Condition de sommeil nocturne (respecté sauf commande manuelle)
    if not est_journee and not declenchement_manuel:
        return {
            "statut": "SOMMEIL_NOCTURNE",
            "mode": "Silence_Nocturne_21h30_09h30",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    temps_ecoule = maintenant - DERNIERE_ETINCELLE_TS
    doit_declencher = declenchement_manuel or (temps_ecoule >= PROCHAIN_INTERVALLE_SEC)

    if not doit_declencher:
        heures_restantes = round(max(0.0, (PROCHAIN_INTERVALLE_SEC - temps_ecoule) / 3600.0), 2)
        return {
            "statut": "VEILLE_NOMINALE",
            "mode": "Distribution_Poissonienne",
            "prochaine_etincelle_dans_heures": heures_restantes,
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    # Sélection et émission de l'étincelle
    etincelle = selectionner_etincelle()
    if not etincelle:
        return {
            "statut": "CORPUS_VIDE",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    texte_vocal = etincelle.get("texte_vocal", "")
    if texte_vocal:
        try:
            PAROLE_QUEUE_FILE.write_text(texte_vocal, encoding="utf-8")
        except Exception:
            pass

    # Mise à jour de l'état
    nouveau_prochain_intervalle = random.uniform(INTERVALLE_MIN_SEC, INTERVALLE_MAX_SEC)
    DERNIERE_ETINCELLE_TS = maintenant
    PROCHAIN_INTERVALLE_SEC = nouveau_prochain_intervalle

    etat["dernier_run_ts"] = maintenant
    etat["date"] = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    etat["dernier_id"] = etincelle.get("id")
    etat["dernier_theme"] = etincelle.get("theme")
    etat["prochain_intervalle_sec"] = nouveau_prochain_intervalle
    etat["total_etincelles_prononcees"] = int(etat.get("total_etincelles_prononcees", 0)) + 1
    sauvegarder_etat(etat)

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "statut": "SUCCES_ETINCELLE",
        "declenchement": "MANUEL" if declenchement_manuel else "PROBABILISTE",
        "theme": etincelle.get("theme"),
        "id": etincelle.get("id"),
        "duree_ms": duree_ms
    }


if __name__ == "__main__":
    print("🔬 Test unitaire de la Capacité Étincelle Souveraine...")
    res = executer_capacite()
    print("Résultat :", res)

