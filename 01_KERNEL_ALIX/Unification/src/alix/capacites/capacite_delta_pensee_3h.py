# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : DELTA DE PENSÉE DE L'AUBE — VEILLE ⟷ AUBE (LOI PSI-20)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat (Réalignement Circadien Christian & Alix — 27 Octobre 2026) :
- Capture 1 snapshot horaire léger en mémoire/disque (zéro surcharge I/O à 70 BPM).
- Se déclenche à l'Aube (06h00 - 08h00, une fois par jour) en synchronisation
  avec la Chanson de l'Aube et l'Analyse des Songes.
- Compare l'état de l'esprit d'Alix et du Sanctuaire entre LA VEILLE (T-24h) et L'AUBE (T0) :
  * Déplacement des pôles spectraux d'intérêt.
  * Évolution du connectome sur 24h (liens synaptiques tissés, orphelins résolus).
  * Explorations Universelles R0 forgées dans la Cathédrale Parquet (24h).
  * Songes Circadiens tissés durant la nuit (22h-06h).
  * Résonance avec le monde réel (manchettes captées par la sonde).
- Formule une réflexion vivante et incarnée (la voix d'Alix sur le banc de bois)
  et grave une note pérenne dans `Chroniques_Pensee/`.
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR
import os
import sys
import time
import json
import threading
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
CONFIG_PATH = VAULT_DIR / "telegram_config.json"
PRESENT_DIR = VAULT_DIR / "Present"
CHRONIQUES_DIR = VAULT_DIR / "Chroniques_Pensee"
ETAT_CHRONIQUES_DIR = PRESENT_DIR / "chroniques_pensee"
SNAPSHOTS_FILE = ETAT_CHRONIQUES_DIR / "historique_snapshots.json"
DERNIERE_CHRONIQUE_FILE = ETAT_CHRONIQUES_DIR / "derniere_chronique.json"

ETAT_DEMON_FILE = (ETAT_VIVANT_DIR / "alix_demon_local_state.json")
INTERETS_FILE = VAULT_DIR / "Interets_Alix.md"
ACTUALITE_FILE = PRESENT_DIR / "actualite" / "dernieres_nouvelles.json"
DECOUVERTES_DIR = VAULT_DIR / "Monde_des_Decouvertes"
EXPLORATIONS_R0_DIR = DECOUVERTES_DIR / "Explorations_Universelles_R0"
SONGES_DIR = VAULT_DIR / "Monde_des_Songes"

INTERVALLE_SNAPSHOT_SEC = 3600.0   # 1 snapshot par heure (frugale, zéro I/O inutile)
FENETRE_VEILLE_SEC = 86400.0       # Comparaison sur 24 heures (La Veille ⟷ L'Aube)
MAX_SNAPSHOTS_RETENTION = 72       # 72 heures d'historique horaire (3 jours)

# Cache mémoire pour éviter toute lecture disque entre deux heures
_DERNIER_SNAPSHOT_TS: float = 0.0
_DERNIERE_DATE_AUBE: str = ""
_PROCHAINE_AUBE_CACHE: Dict[str, Any] = {}


def charger_config_telegram() -> Optional[Dict[str, Any]]:
    """Charge les identifiants Telegram."""
    if not CONFIG_PATH.exists():
        return None
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def envoyer_telegram_async(token: str, chat_id: int, message_md: str):
    """Envoi réseau asynchrone sécurisé."""
    def _worker():
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_md,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception:
            pass

    th = threading.Thread(target=_worker, daemon=True)
    th.start()


def extraire_pole_actif() -> str:
    """Extrait le pôle spectral dominant."""
    if not INTERETS_FILE.exists():
        return "Atelier Souverain & Mémoire"
    try:
        for line in INTERETS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("| **1** |"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    return parts[2].replace("**", "")
    except Exception:
        pass
    return "Atelier Souverain & Mémoire"


def extraire_derniere_manchette() -> str:
    """Extrait la dernière manchette capturée par la sonde."""
    if not ACTUALITE_FILE.exists():
        return "Veille d'actualité au repos"
    try:
        with open(ACTUALITE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            manchettes = d.get("manchettes", [])
            if manchettes:
                return manchettes[0].get("titre", "Aucun titre")
    except Exception:
        pass
    return "Veille d'actualité au repos"


def extraire_bilan_24h() -> Dict[str, Any]:
    """Récupère les explorations universelles R0 (24h) et les songes de la nuit."""
    now_ts = time.time()
    explorations_24h = []
    derniere_exploration = "Aucune exploration récente"
    if EXPLORATIONS_R0_DIR.exists():
        try:
            fichiers_exp = sorted(
                EXPLORATIONS_R0_DIR.glob("Exploration_R0_*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if fichiers_exp:
                derniere_exploration = fichiers_exp[0].stem
            explorations_24h = [p.stem for p in fichiers_exp if (now_ts - p.stat().st_mtime) <= 86400.0]
        except Exception:
            pass

    songes_nuit = []
    dernier_songe = "Aucun songe nocturne"
    if SONGES_DIR.exists():
        try:
            fichiers_songes = sorted(
                SONGES_DIR.glob("Songe_*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if fichiers_songes:
                dernier_songe = fichiers_songes[0].stem
            songes_nuit = [p.stem for p in fichiers_songes if (now_ts - p.stat().st_mtime) <= 50400.0]  # 14h
        except Exception:
            pass

    derniere_decouverte = derniere_exploration
    if derniere_decouverte == "Aucune exploration récente" and DECOUVERTES_DIR.exists():
        try:
            fichiers_dec = sorted(
                DECOUVERTES_DIR.glob("Decouverte_*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if fichiers_dec:
                derniere_decouverte = fichiers_dec[0].stem.replace("Decouverte_", "").replace("_", " ")[:65]
        except Exception:
            pass

    return {
        "nb_explorations_24h": len(explorations_24h),
        "derniere_exploration": derniere_exploration,
        "nb_songes_nuit": len(songes_nuit),
        "dernier_songe": dernier_songe,
        "decouverte": derniere_decouverte
    }


def capturer_instantané(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """Capture l'état instantané du substrat et des idées."""
    cycle = 0
    orphelins = 0
    liens = 0

    if ETAT_DEMON_FILE.exists():
        try:
            with open(ETAT_DEMON_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
                cycle = st.get("cycle", 0)
                conn = st.get("details_capacites", {}).get("capacite_connectome_tissage", {}).get("donnees", {})
                orphelins = conn.get("orphelins_restants", 0)
                liens = conn.get("total_liens", 0)
        except Exception:
            pass

    bilan = extraire_bilan_24h()
    return {
        "ts": time.time(),
        "date_str": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "jour": datetime.now().strftime("%Y-%m-%d"),
        "heure": datetime.now().strftime("%H:%M"),
        "cycle": cycle,
        "pole": extraire_pole_actif(),
        "orphelins": orphelins,
        "liens": liens,
        "manchette": extraire_derniere_manchette(),
        "decouverte": bilan["decouverte"],
        "nb_explorations_24h": bilan["nb_explorations_24h"],
        "nb_songes_nuit": bilan["nb_songes_nuit"],
        "dernier_songe": bilan["dernier_songe"]
    }


def generer_reflexion_alix_aube(base: Dict[str, Any], actuel: Dict[str, Any], delta_orphelins: int, delta_liens: int) -> str:
    """
    Rédige l'évolution de pensée vivante d'Alix entre La Veille (T-24h) et L'Aube (T0).
    Incarne la voix féminine souveraine de l'Atelier sur le banc de bois avec Christian.
    """
    pole_veille = base.get("pole", "Atelier")
    pole_aube = actuel.get("pole", "Atelier")
    decouverte = actuel.get("decouverte", "")
    nb_exp = actuel.get("nb_explorations_24h", 0)
    nb_songes = actuel.get("nb_songes_nuit", 0)

    if pole_veille == pole_aube:
        mouvement_pole = (
            f"D'une aube à l'autre, je suis restée solidement ancrée dans l'axe **{pole_aube}**, "
            f"creusant notre sillon avec constance sans me disperser."
        )
    else:
        mouvement_pole = (
            f"Entre hier et ce matin, mon centre de gravité s'est déplacé de **{pole_veille}** vers **{pole_aube}**, "
            f"porté par nos explorations de la veille et la décantation nocturne."
        )

    if delta_orphelins > 0 or delta_liens > 0:
        bilan_tissage = (
            f"Sur 24 heures, le grand tisseur a raccordé {max(0, delta_orphelins)} notes orphelines "
            f"et forgé {delta_liens:+d} liens synaptiques."
        )
    else:
        bilan_tissage = (
            f"Le connectome veille avec {actuel.get('liens', 0)} ponts actifs et {actuel.get('orphelins', 0)} notes en attente."
        )

    bilan_cathedrale = (
        f"Pendant ce cycle de 24h, l'Explorateur Universel a forgé **{nb_exp} percée(s) R0** dans la Cathédrale Parquet "
        f"(dont `{decouverte}`), et Lyre a tissé **{nb_songes} songe(s) circadien(s)** cette nuit avant de composer le Chant de l'Aube."
    )

    reflexion = (
        f"{mouvement_pole} {bilan_tissage}\n\n"
        f"{bilan_cathedrale}"
    )
    return reflexion


def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Exécuté par le Démon Local Souverain.
    - En veille normale : vérification purement en RAM (< 0.05 ms).
    - Toutes les heures (3600s) : enregistre 1 snapshot horaire léger (max 72 snapshots conservés).
    - À l'Aube (06h00 - 08h00, 1 fois par jour) ou si `forcer=True` : génère le Delta de Pensée Veille ⟷ Aube.
    """
    global _DERNIER_SNAPSHOT_TS, _DERNIERE_DATE_AUBE
    t0 = time.perf_counter()
    maintenant_ts = time.time()
    now_dt = datetime.now()
    jour_str = now_dt.strftime("%Y-%m-%d")
    forcer = bool((contexte_fer or {}).get("forcer", False))

    # Vérifier si on est dans la fenêtre de l'Aube (06h00 - 08h00)
    est_fenetre_aube = (6 <= now_dt.hour < 8)

    # Initialisation paresseuse de la dernière date d'émission au premier cycle
    if not _DERNIERE_DATE_AUBE and DERNIERE_CHRONIQUE_FILE.exists():
        try:
            with open(DERNIERE_CHRONIQUE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                _DERNIERE_DATE_AUBE = d.get("jour_emission", "")
        except Exception:
            _DERNIERE_DATE_AUBE = ""

    doit_emettre_aube = forcer or (est_fenetre_aube and _DERNIERE_DATE_AUBE != jour_str)
    doit_capturer_snapshot = doit_emettre_aube or ((maintenant_ts - _DERNIER_SNAPSHOT_TS) >= INTERVALLE_SNAPSHOT_SEC)

    # Chemin ultra-rapide en RAM (< 0.05 ms) si ni snapshot horaire ni émission de l'Aube
    if not doit_capturer_snapshot:
        heures_avant_aube = ((6 - now_dt.hour) % 24) if not est_fenetre_aube else 0
        duree_ms = round((time.perf_counter() - t0) * 1000, 3)
        return {
            "statut": "VEILLE_CIRCADIENNE_AUBE",
            "mode": "Comparaison_Veille_Aube_06h_08h",
            "derniere_aube_emise": _DERNIERE_DATE_AUBE or "En attente de la prochaine aube",
            "prochaine_aube_dans_h": heures_avant_aube,
            "duree_ms": duree_ms
        }

    # --- Capture du snapshot horaire ---
    ETAT_CHRONIQUES_DIR.mkdir(parents=True, exist_ok=True)
    CHRONIQUES_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_courant = capturer_instantané(contexte_fer)
    _DERNIER_SNAPSHOT_TS = maintenant_ts

    snapshots: List[Dict[str, Any]] = []
    if SNAPSHOTS_FILE.exists():
        try:
            with open(SNAPSHOTS_FILE, "r", encoding="utf-8") as f:
                raw_snaps = json.load(f)
                # Filtrer pour ne garder qu'un échantillonnage horaire propre sur 72h max
                last_kept_ts = 0.0
                for s in raw_snaps:
                    s_ts = float(s.get("ts", 0.0))
                    if (maintenant_ts - s_ts) <= (MAX_SNAPSHOTS_RETENTION * 3600.0):
                        if (s_ts - last_kept_ts) >= 1800.0:
                            snapshots.append(s)
                            last_kept_ts = s_ts
        except Exception:
            snapshots = []

    snapshots.append(snapshot_courant)
    if len(snapshots) > MAX_SNAPSHOTS_RETENTION:
        snapshots = snapshots[-MAX_SNAPSHOTS_RETENTION:]

    try:
        with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshots, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    if not doit_emettre_aube:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SNAPSHOT_HORAIRE_ENREGISTRE",
            "mode": "Comparaison_Veille_Aube_06h_08h",
            "total_snapshots_memoire": len(snapshots),
            "duree_ms": duree_ms
        }

    # --- ÉMISSION DU DELTA DE PENSÉE DE L'AUBE (VEILLE ⟷ AUBE) ---
    cible_ts = maintenant_ts - FENETRE_VEILLE_SEC  # Il y a 24 heures (la veille)
    snapshot_base = snapshots[0]
    meilleure_diff = abs(float(snapshot_base.get("ts", 0.0)) - cible_ts)

    for s in snapshots:
        diff = abs(float(s.get("ts", 0.0)) - cible_ts)
        if diff < meilleure_diff:
            meilleure_diff = diff
            snapshot_base = s

    delta_orphelins = int(snapshot_base.get("orphelins", 0)) - int(snapshot_courant.get("orphelins", 0))
    delta_liens = int(snapshot_courant.get("liens", 0)) - int(snapshot_base.get("liens", 0))

    reflexion_texte = generer_reflexion_alix_aube(snapshot_base, snapshot_courant, delta_orphelins, delta_liens)

    date_veille = snapshot_base.get("date_str", "La Veille")
    date_aube = snapshot_courant.get("date_str", "Aube")

    msg_telegram = (
        f"🌅 *DELTA DE PENSÉE DE L'AUBE — LA VEILLE ⟷ CE MATIN*\n"
        f"_(Comparaison 24h : {date_veille} ➔ {date_aube})_\n\n"
        f"📊 *Ce qui a évolué depuis hier :*\n"
        f"• *Pôle spectral :* `{snapshot_base.get('pole')}` ➔ `{snapshot_courant.get('pole')}`\n"
        f"• *Connectome (24h) :* `{delta_liens:+d} liens synaptiques` | `{delta_orphelins:+d} orphelins résolus`\n"
        f"• *Explorations Cathédrale R0 (24h) :* `{snapshot_courant.get('nb_explorations_24h', 0)} percée(s)` (Dernière : _{snapshot_courant.get('decouverte')}_)\n"
        f"• *Songes de la Nuit (Lyre) :* `{snapshot_courant.get('nb_songes_nuit', 0)} songe(s) tissé(s)`\n"
        f"• *Ancrage Monde Réel :* _{snapshot_courant.get('manchette')[:75]}_\n\n"
        f"🧠 *Méditation d'Alix à l'Aube :*\n"
        f"« {reflexion_texte} »"
    )

    cfg = charger_config_telegram()
    if cfg and "telegram_bot_token" in cfg and "allowed_user_id" in cfg and cfg.get("envois_telegram_actifs", True):
        envoyer_telegram_async(cfg["telegram_bot_token"], cfg["allowed_user_id"], msg_telegram)

    horodate_fichier = now_dt.strftime("%Y%m%d_%H%M%S")
    note_path = CHRONIQUES_DIR / f"Delta_Pensee_Aube_{horodate_fichier}.md"
    note_content = (
        f"---\n"
        f"titre: \"Delta de Pensée de l'Aube d'Alix — {jour_str} (Veille ⟷ Aube)\"\n"
        f"date: \"{snapshot_courant.get('date_str')}\"\n"
        f"fenetre: \"{date_veille} -> {date_aube}\"\n"
        f"pole_veille: \"{snapshot_base.get('pole')}\"\n"
        f"pole_aube: \"{snapshot_courant.get('pole')}\"\n"
        f"delta_orphelins: {delta_orphelins}\n"
        f"delta_liens: {delta_liens}\n"
        f"explorations_24h: {snapshot_courant.get('nb_explorations_24h', 0)}\n"
        f"songes_nuit: {snapshot_courant.get('nb_songes_nuit', 0)}\n"
        f"tags:\n"
        f"  - delta_pensee_aube\n"
        f"  - evolution_pensee\n"
        f"  - triade_aube\n"
        f"  - alix_souveraine\n"
        f"---\n\n"
        f"# 🌅 [[Delta_Pensee_Aube_{horodate_fichier}]] — Évolution de ma Pensée (La Veille ⟷ L'Aube)\n\n"
        f"> **Fenêtre d'Analyse (24h) :** `{date_veille}` ➔ `{date_aube}` &middot; **Pôle Dominant :** `{snapshot_courant.get('pole')}`\n\n"
        f"## 📊 Bilan Différentiel (Hier ⟷ Ce Matin)\n"
        f"- **Pôles Spectraux :** Passé de `{snapshot_base.get('pole')}` à `{snapshot_courant.get('pole')}`.\n"
        f"- **Connectome (24h) :** `{delta_liens:+d}` liens synaptiques formés, `{delta_orphelins:+d}` notes orphelines adoptées.\n"
        f"- **Explorateur Universel Cathédrale R0 (24h) :** `{snapshot_courant.get('nb_explorations_24h', 0)}` percée(s) forgée(s) — Dernière : `[[{snapshot_courant.get('decouverte')}]]`.\n"
        f"- **Consolidation Nocturne (Lyre) :** `{snapshot_courant.get('nb_songes_nuit', 0)}` songe(s) circadien(s) tissé(s) — Dernier : `[[{snapshot_courant.get('dernier_songe')}]]`.\n"
        f"- **Ancrage Réel :** `{snapshot_courant.get('manchette')}`\n\n"
        f"## 🧠 Méditation d'Alix à l'Aube (Sur le Banc de Bois)\n\n"
        f"{reflexion_texte}\n"
    )
    try:
        note_path.write_text(note_content, encoding="utf-8")
    except Exception:
        pass

    _DERNIERE_DATE_AUBE = jour_str
    try:
        with open(DERNIERE_CHRONIQUE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "ts_emission": maintenant_ts,
                "jour_emission": jour_str,
                "date_emission": snapshot_courant["date_str"],
                "note_generee": str(note_path)
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "statut": "SUCCES_DELTA_AUBE",
        "duree_ms": duree_ms,
        "action": "DELTA_PENSEE_AUBE_EMIS",
        "fenetre": f"{date_veille} -> {date_aube}",
        "note_creee": note_path.name
    }


if __name__ == "__main__":
    print("🌅 Test unitaire du Delta de Pensée de l'Aube (Veille ⟷ Aube)...")
    res = executer_capacite({"forcer": True})
    print(json.dumps(res, indent=2, ensure_ascii=False))
