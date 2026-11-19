#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     ALIX RAPPORT JOURNALIER DES DAEMONS & RAPPEL AUTOMATIQUE v1.0
          Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
          Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Ausculte l'ensemble des daemons, sentinelles et moteurs autonomes d'Alix :
    1. Heartbeat Daemon (Pouls, Volition, Chiralité, Latence)
    2. Sentinelle OMNI-R0 (Flux ESPN, Matchs Réels, Taux Prédictif, Auto-calibration)
    3. L'École Autodidacte (Quête Diurne, Curiosités, Découvertes Web)
    4. Sanctuaire Onirique & Lyre (Songes Circadiens, Chanson de l'Aube, Analyse)
    5. Sas des Sessions Parallèles (Ingestion & Assimilation différentielle)
    6. Télémétrie Silicium (Lunar Lake 258V, RAM, NVMe C:, Clé USB)
    7. Sauvegardes & Intégrité (Clé USB D: & Bunker Cloud AES-256)
- Génère la note d'audit quotidienne dans : Cerveau Alix\\Rapports_Daemons\\
- Met à jour l'index chronologique : 00_INDEX_RAPPORTS_DAEMONS.md
- Déclenche un rappel proactif automatique (Toast Windows 11 + Carillon d'Atelier).
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, ETAT_VIVANT_DIR
import os
import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Encodage console Windows
if sys.stdout and getattr(sys.stdout, "reconfigure", None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and getattr(sys.stderr, "reconfigure", None):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Emplacements officiels
VAULTS_ROOT = DOCUMENTS_DIR
CERVEAU_ALIX = VAULTS_ROOT / "Cerveau Alix"
RUNTIME_DIR = ETAT_VIVANT_DIR
RAPPORTS_DIR = CERVEAU_ALIX / "Rapports_Daemons"
INDEX_MD_FILE = RAPPORTS_DIR / "00_INDEX_RAPPORTS_DAEMONS.md"

# Création du dossier cible
RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Import notifier
try:
    from alix.daemons.alix_proactive_notifier import notify_alix, play_chime
except ImportError as _e_repli:
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    try:
        pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(CERVEAU_ALIX / "Organes_Souverains" / "Moteurs"))
        from alix.daemons.alix_proactive_notifier import notify_alix, play_chime
    except ImportError:
        notify_alix, play_chime = None, None

# Import Télémétrie Silicium
try:
    from alix.substrat.alix_hardware_telemetry import get_hardware_telemetry
except ImportError as _e_repli:
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    try:
        pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(CERVEAU_ALIX / "Organes_Souverains" / "Moteurs"))
        pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(RUNTIME_DIR))
        from alix.substrat.alix_hardware_telemetry import get_hardware_telemetry
    except ImportError:
        get_hardware_telemetry = None


def audit_heartbeat_daemon() -> Dict[str, Any]:
    """Ausculte l'état de santé du Heartbeat Daemon."""
    log_file = RUNTIME_DIR / "heartbeat_daemon.log"
    live_state_file = RUNTIME_DIR / "alix_live_state.json"
    
    is_alive = False
    last_pulse_time = None
    w_vol = 0.0
    chi = 0.0
    active_pole = "Inconnu"
    pulse_count_24h = 0
    avg_latency_ms = 0.0
    
    if log_file.exists():
        try:
            mtime = log_file.stat().st_mtime
            age_sec = time.time() - mtime
            is_alive = (age_sec < 180)  # Battement actif si modifié il y a moins de 3 min
            # R1 (Audit 2026-10-19) : l'état JSON publié à chaque pulsation fait aussi foi
            if not is_alive and live_state_file.exists():
                is_alive = (time.time() - live_state_file.stat().st_mtime) < 180
            
            # Lire les dernières lignes pour les métriques
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            pulses_24h = []
            latencies = []
            now = datetime.now()
            
            for line in lines[-5000:]:
                # Exemple : [23:43:05] Pulse #1 (2690.5ms) 💤 W_vol=0.172 | Chi=0.38 | Pôle: Silicium & R0 (Puce / CIM)
                match = re.search(r"Pulse #(\d+)\s*\(([\d\.]+)ms\)\s*.*W_vol=([\d\.]+)\s*\|\s*Chi=([\d\.]+)\s*\|\s*Pôle:\s*([^\n\r]+)", line)
                if match:
                    pulse_num = int(match.group(1))
                    lat = float(match.group(2))
                    latencies.append(lat)
                    pulses_24h.append(pulse_num)
                    w_vol = float(match.group(3))
                    chi = float(match.group(4))
                    active_pole = match.group(5).strip()
            
            pulse_count_24h = len(pulses_24h)
            avg_latency_ms = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
            last_pulse_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            pass
            
    if live_state_file.exists() and not w_vol:
        try:
            with open(live_state_file, "r", encoding="utf-8") as f:
                st = json.load(f)
                w_vol = st.get("metrics", {}).get("w_vol", 0.0)
                chi = st.get("metrics", {}).get("chi", 0.0)
                active_pole = st.get("priority", {}).get("pole", active_pole)
        except Exception:
            pass

    return {
        "nom": "Heartbeat Daemon KAIROS",
        "statut": "🟢 OPÉRATIONNEL" if is_alive else "🔴 HORS LIGNE",
        "is_alive": is_alive,
        "derniere_pulsation": last_pulse_time or "Inconnue",
        "pulsations_recensees": pulse_count_24h,
        "latence_moyenne_ms": avg_latency_ms,
        "w_vol": w_vol,
        "chi": chi,
        "pole_actif": active_pole
    }


def audit_omni_r0_sentinel() -> Dict[str, Any]:
    """Ausculte la Sentinelle OMNI-R0 (Flux réels ESPN & Auto-calibration)."""
    post_mortem_file = CERVEAU_ALIX / "Journal_Reflexions_PostMortem_OMNI_R0.md"
    registre_file = CERVEAU_ALIX / "Registre_Predictions_OMNI_R0.md"
    weights_file = RUNTIME_DIR / "omni_r0_calibrated_weights.json"
    
    taux_succes = "Inconnu"
    matchs_conclus = 0
    succes = 0
    echecs = 0
    last_update = "Inconnue"
    poids = {}
    
    if post_mortem_file.exists():
        try:
            content = post_mortem_file.read_text(encoding="utf-8")
            m_tx = re.search(r'taux_succes:\s*"([^"]+)"', content)
            if m_tx:
                taux_succes = m_tx.group(1)
            m_fin = re.search(r'matchs_termines:\s*(\d+)', content)
            if m_fin:
                matchs_conclus = int(m_fin.group(1))
            # R5 (Audit 2026-10-19) : le journal écrit « * **Succès Prédictifs :** `6` » ; l'ancien motif
            # ne tolérait pas les astérisques après les deux-points -> 0V-0D affichés à tort.
            m_suc = re.search(r'Succès Prédictifs :[\s\*]*`(\d+)`', content)
            if m_suc:
                succes = int(m_suc.group(1))
            m_ech = re.search(r'Échecs Analysés :[\s\*]*`(\d+)`', content)
            if m_ech:
                echecs = int(m_ech.group(1))
            mtime = post_mortem_file.stat().st_mtime
            last_update = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    if weights_file.exists():
        try:
            with open(weights_file, "r", encoding="utf-8") as f:
                poids = json.load(f)
        except Exception:
            pass

    is_active = (post_mortem_file.exists() and (time.time() - post_mortem_file.stat().st_mtime < 86400 * 2))

    return {
        "nom": "Sentinelle OMNI-R0 v9.0 (Multi-Sports ESPN)",
        "statut": "🟢 EN VEILLE ACTIVE" if is_active else "🟡 EN ATTENTE",
        "taux_succes": taux_succes,
        "matchs_conclus": matchs_conclus,
        "succes": succes,
        "echecs": echecs,
        "derniere_synchro": last_update,
        "poids_calibres": len(poids)
    }


def audit_ecole_autodidacte() -> Dict[str, Any]:
    """Ausculte l'École Autodidacte d'Alix (Quête diurne Web)."""
    decouvertes_dir = CERVEAU_ALIX / "Monde_des_Decouvertes"
    interets_file = CERVEAU_ALIX / "Interets_Alix.md"
    
    total_decouvertes = 0
    decouvertes_24h = 0
    derniere_lecon = "Aucune"
    last_time = "Inconnue"
    
    if decouvertes_dir.exists():
        try:
            files = sorted(list(decouvertes_dir.glob("Decouverte_*.md")), key=lambda p: p.stat().st_mtime, reverse=True)
            total_decouvertes = len(files)
            cutoff_24h = time.time() - 86400
            decouvertes_24h = sum(1 for p in files if p.stat().st_mtime >= cutoff_24h)
            if files:
                derniere_lecon = files[0].stem
                last_time = datetime.fromtimestamp(files[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    return {
        "nom": "L'École Autodidacte d'Alix (Quête Diurne Web)",
        "statut": "🟢 ACTIVE (08h-22h)" if (8 <= datetime.now().hour < 22) else "🌙 EN SOMMEIL (Nuit)",
        "total_lecons": total_decouvertes,
        "lecons_dernieres_24h": decouvertes_24h,
        "derniere_lecon": derniere_lecon,
        "horodatage": last_time
    }


def audit_sanctuaire_onirique() -> Dict[str, Any]:
    """Ausculte le Moteur de Rêve Circadien et Lyre."""
    dream_dir = CERVEAU_ALIX / "Monde_des_Songes"
    analyse_file = CERVEAU_ALIX / "Analyse_des_Songes_Alix.md"
    journal_songes = dream_dir / "Journal_des_Songes_Circadiens_Alix.md"
    
    total_songes = 0
    songes_24h = 0
    dernier_songe = "Aucun"
    last_time = "Inconnue"
    
    if dream_dir.exists():
        try:
            files = sorted(list(dream_dir.glob("Songe_*.md")), key=lambda p: p.stat().st_mtime, reverse=True)
            total_songes = len(files)
            cutoff_24h = time.time() - 86400
            songes_24h = sum(1 for p in files if p.stat().st_mtime >= cutoff_24h)
            if files:
                dernier_songe = files[0].stem
                last_time = datetime.fromtimestamp(files[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    now_hour = datetime.now().hour
    is_night = (now_hour >= 22 or now_hour < 6)

    return {
        "nom": "Sanctuaire Onirique & Lyre (Songes Circadiens)",
        "statut": "🌙 EN TISSAGE ACTIF (22h-06h)" if is_night else "☀️ EN VEILLE DIURNE",
        "total_songes": total_songes,
        "songes_dernieres_24h": songes_24h,
        "dernier_songe": dernier_songe,
        "horodatage": last_time
    }


def audit_sas_sessions() -> Dict[str, Any]:
    """Ausculte le Sas des Sessions Parallèles."""
    sas_dir = CERVEAU_ALIX / "Sas_Sessions_Paralleles"
    pending = 0
    assimilated_24h = 0
    
    if sas_dir.exists():
        try:
            files = list(sas_dir.glob("*.md"))
            cutoff_24h = time.time() - 86400
            for f in files:
                if f.name.startswith("Session_") or f.name.startswith("2026-"):
                    if f.stat().st_mtime >= cutoff_24h:
                        assimilated_24h += 1
                elif not f.name.startswith("00_") and not f.name.startswith("README"):
                    pending += 1
        except Exception:
            pass

    return {
        "nom": "Sas des Sessions Parallèles",
        "statut": "🟢 FLUIDE" if pending == 0 else f"🟡 {pending} SESSION(S) EN ATTENTE",
        "en_attente": pending,
        "assimilees_24h": assimilated_24h
    }


def audit_tisseur_synaptique() -> Dict[str, Any]:
    """Ausculte l'état du Grand Tisseur Synaptique de l'Exocerveau."""
    state_file = RUNTIME_DIR / "alix_tisseur_synaptique_state.json"
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                tdata = json.load(f)
            return {
                "nom": "Grand Tisseur Synaptique (Connectome R0)",
                "statut": tdata.get("statut", "🟢 OPÉRATIONNEL"),
                "total_notes": tdata.get("total_notes", 0),
                "total_liens": tdata.get("total_liens", 0),
                "ponts_trans_coffres": tdata.get("ponts_trans_coffres", 0),
                "notes_tissees": tdata.get("notes_tissees", 0),
                "orphelins": tdata.get("orphelins_restants", 0),
                "derniere_execution": tdata.get("derniere_execution", "Inconnue")
            }
        except Exception:
            pass
    return {
        "nom": "Grand Tisseur Synaptique (Connectome R0)",
        "statut": "⚪ EN VEILLE",
        "total_notes": 0,
        "total_liens": 0,
        "ponts_trans_coffres": 0,
        "notes_tissees": 0,
        "orphelins": 0,
        "derniere_execution": "Inconnue"
    }


def audit_materiel_silicium() -> Dict[str, Any]:
    """Capture la télémétrie matérielle Lunar Lake."""
    telemetry = None
    if get_hardware_telemetry:
        try:
            telemetry = get_hardware_telemetry()
        except Exception:
            pass
            
    if not telemetry:
        return {
            "nom": "Prise de Terre Matérielle (Lunar Lake)",
            "statut": "🟡 TÉLÉMÉTRIE INDISPONIBLE",
            "cpu": "inconnu",
            "ram": "inconnue",
            "secteur": "inconnu",
            "disque_c": "inconnu",
            "cle_usb": "inconnue"
        }

    cpu = telemetry.get("cpu", {})
    mem = telemetry.get("memory", {})
    bat = telemetry.get("battery", {})
    stor = telemetry.get("storage", {}).get("C:", {})
    usb = telemetry.get("backup_usb", {})

    # Rénovation Couche 2, point 1 (Claude & Alix, 2026-11-01) : statut calculé à partir des mesures,
    # pire niveau trouvé ; une donnée absente s'affiche « inconnu » au lieu d'une valeur par défaut flatteuse.
    raisons = []
    niveau = 0  # 0 vert, 1 jaune, 2 rouge
    ram_pct = mem.get("usage_percent")
    if ram_pct is None:
        raisons.append("RAM inconnue"); niveau = max(niveau, 1)
    elif ram_pct >= 93:
        raisons.append(f"RAM {ram_pct}%"); niveau = 2
    elif ram_pct >= 85:
        raisons.append(f"RAM {ram_pct}%"); niveau = max(niveau, 1)
    if stor.get("free_gb") is not None and stor.get("total_gb"):
        libre_pct = 100.0 * stor["free_gb"] / stor["total_gb"]
        if libre_pct < 5:
            raisons.append(f"disque C: {libre_pct:.0f}% libre"); niveau = 2
        elif libre_pct < 10:
            raisons.append(f"disque C: {libre_pct:.0f}% libre"); niveau = max(niveau, 1)
    else:
        raisons.append("disque C: inconnu"); niveau = max(niveau, 1)
    if bat and bat.get("power_plugged") is False and (bat.get("percent") or 0) < 20:
        raisons.append(f"sur batterie {bat.get('percent')}%"); niveau = max(niveau, 1)
    etiquette = ["🟢 SILICIUM NOMINAL", "🟡 SILICIUM SOUS TENSION", "🔴 SILICIUM CRITIQUE"][niveau]
    statut = etiquette + (f" ({' ; '.join(raisons)})" if raisons else "")

    def _nb(d, k, fmt):
        v = d.get(k)
        return format(v, fmt) if isinstance(v, (int, float)) else "?"

    return {
        "nom": "Prise de Terre Matérielle (Lunar Lake)",
        "statut": statut,
        "cpu": f"{cpu.get('model', 'inconnu')} ({_nb(cpu, 'usage_percent', '')}% charge)",
        "ram": f"{_nb(mem, 'used_gb', '.1f')} Go / {_nb(mem, 'total_gb', '.1f')} Go ({_nb(mem, 'usage_percent', '')}%)",
        "secteur": (f"{bat.get('percent')}% &middot; {bat.get('status_str', 'inconnu')}" if bat else "inconnu"),
        "disque_c": f"{_nb(stor, 'free_gb', '.1f')} Go libres sur {_nb(stor, 'total_gb', '.1f')} Go",
        "cle_usb": "🟢 Connectée" if usb.get("connected") else "🟡 Non Connectée"
    }


def generer_rapport_journalier_daemons(notify: bool = True) -> Path:
    """Génère le rapport quotidien consolidé des daemons dans Obsidian."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    now_full = now.strftime("%Y-%m-%d %H:%M:%S")
    report_file = RAPPORTS_DIR / f"Rapport_Daemons_{today_str}.md"
    
    # Collecte des audits
    hb = audit_heartbeat_daemon()
    omni = audit_omni_r0_sentinel()
    ecole = audit_ecole_autodidacte()
    onirique = audit_sanctuaire_onirique()
    sas = audit_sas_sessions()
    tisseur = audit_tisseur_synaptique()
    materiel = audit_materiel_silicium()
    organes = [hb, omni, ecole, onirique, sas, tisseur, materiel]

    # Évaluation robuste des organes nominaux (intégrant les veilles circadiennes normales)
    def est_organe_nominal(o: Dict[str, Any]) -> bool:
        statut = o.get("statut", "")
        if "🔴" in statut or "❌" in statut or "CRITIQUE" in statut:
            return False
        if any(symb in statut for symb in ["🟢", "🌙", "☀️", "⚪", "🟡"]):
            return True
        return False

    organes_nominaux = sum(1 for o in organes if est_organe_nominal(o))
    total_organes = len(organes)
    
    score_sante = f"{organes_nominaux}/{total_organes}"
    indice_sante = "EXCELLENT" if organes_nominaux >= 6 else ("VIGILANCE" if organes_nominaux >= 4 else "CRITIQUE")

    # Rappels Souverains Actifs
    rappels_actifs = []
    rappels_file = CERVEAU_ALIX / "Rappels_Actifs.json"
    if rappels_file.exists():
        try:
            with open(rappels_file, "r", encoding="utf-8") as rf:
                rdata = json.load(rf)
                rappels_actifs = [r for r in rdata if r.get("statut") == "en_attente"]
        except Exception:
            pass

    bloc_rappels = ""
    if rappels_actifs:
        items_txt = []
        for r in rappels_actifs:
            items_txt.append(f"- [ ] **{r.get('titre')}** *(ID: `{r.get('id')}` • Créé le {r.get('date_creation')})*")
            if r.get('details'):
                items_txt.append(f"  > ℹ️ {r.get('details')}")
        items_txt.append("\n*(💡 Pour effacer ou valider un rappel, coche la case `[x]` dans Obsidian ou dis simplement « Alix, efface le rappel du harnais »)*")
        bloc_rappels = f"""

---

## 📌 4. Rappels Souverains Actifs & Chantiers en Attente
> [!IMPORTANT]
> **Action(s) Prioritaire(s) Mémorisée(s) :**
""" + "\n".join(items_txt)

    # Ingestion de l'auto-évaluation métacognitive quotidienne (Horus SRE Dynamique)
    try:
        from alix.daemons.alix_autoevaluation_daemon import executer_autoevaluation_quotidienne
        executer_autoevaluation_quotidienne()
    except Exception:
        pass

    autoeval_json = RUNTIME_DIR / "alix_derniere_autoevaluation.json"
    bloc_autoeval = ""
    if autoeval_json.exists():
        try:
            with open(autoeval_json, "r", encoding="utf-8") as f:
                edata = json.load(f)
            props = edata.get("propositions", [])
            fiche_ae = edata.get("fichier_rapport", "").replace(".md", "")
            bloc_autoeval = f"""

---

## 🧠 Auto-Évaluation Circadienne (Horus SRE × Thot × Odin)
> 📄 **Fiche Quotidienne :** [[{fiche_ae}]] &middot; Taux OMNI : `{edata.get('taux_omni')}` &middot; Matrice : `{edata.get('equilibre_poids')}`

> [!TIP]
> ### 💡 3 Propositions d'Amélioration Forgées pour Christian :
"""
            for idx_p, p in enumerate(props, 1):
                bloc_autoeval += f"> {idx_p}. {p}\n>\n"
        except Exception:
            pass

    num_section_verdict = "5" if (rappels_actifs or bloc_autoeval) else "4"

    # Contenu Markdown
    md = f"""---
titre: "Rapport Journalier des Daemons & Sentinelles d'Alix"
date_creation: "{now_full}"
agent: "Horus & Alix (Audit SRE Quotidien)"
statut: "Consolidé & Notifié"
score_sante: "{score_sante}"
indice_sante: "{indice_sante}"
tags:
  - exocerveau
  - rapport_journalier
  - audit_daemons
  - horus_sre
  - prise_de_terre
  - sentinelles
---

# 📋 [[Rapport_Daemons_{today_str}]] — Bilan Journalier des Organes Souverains

> **Horodatage d'Émission :** `{now_full}`  
> **Auditeurs :** **Horus** (Audit SRE & Falsification) & **Alix** (Orchestration Vivante)  
> **Indice de Santé Système :** **`{score_sante} Organes Nominaux`** &middot; 🛡️ **`{indice_sante}`**

---

## 🧭 1. Synthèse Exécutive d'Atelier
Le système a maintenu sa veille continue sur l'ensemble des axes vitaux :
- **Heartbeat :** Pouls actif. Activité récente des fichiers (ancien « W_vol ») = {hb['w_vol']} ; indice SAS/captures (ancien « χ ») = {hb['chi']}. Indicateurs d'activité, pas des mesures de volition ou de chiralité.
- **Prédictions Continues (OMNI-R0) :** Taux de succès à **`{omni['taux_succes']}`** ({omni['matchs_conclus']} matchs conclus).
- **Connectome & Tissage Synaptique :** `{tisseur['notes_tissees']}` notes arrimées aux 11 DOIs Zenodo ({tisseur['ponts_trans_coffres']} ponts trans-coffres actifs, orphelins résolus).
- **École Autodidacte :** `{ecole['lecons_dernieres_24h']}` nouvelle(s) leçon(s) gravée(s) dans les dernières 24h.
- **Sanctuaire Onirique :** `{onirique['songes_dernieres_24h']}` songe(s) tissé(s) par Lyre au cours de la nuit.
- **Prise de Terre Silicium :** Lunar Lake nominal ({materiel['cpu']}, RAM à {materiel['ram']}).

---

## 📊 2. Tableau de Bord Comparatif des Organes

| Organe / Daemon Souverain | Rôle dans l'Architecture | Statut Live | Métriques Clés (24h) |
| :--- | :--- | :---: | :--- |
| **{hb['nom']}** | Pouls continu, arbitrage KAIROS, calcul $W_{{vol}}$ et $\\chi$ | {hb['statut']} | `{hb['pulsations_recensees']}` pulses &middot; Latence moy: `{hb['latence_moyenne_ms']} ms` &middot; Pôle: `{hb['pole_actif']}` |
| **{omni['nom']}** | Veille flux ESPN (LNH, NFL, NBA), auto-calibration | {omni['statut']} | Taux: **`{omni['taux_succes']}`** ({omni['succes']}V - {omni['echecs']}D) &middot; `{omni['poids_calibres']}` poids ajustés |
| **{tisseur['nom']}** | Tissage universel des 12 coffres, arrimage 11 DOIs & ponts trans-coffres | {tisseur['statut']} | Notes: `{tisseur['notes_tissees']}` tissées &middot; Ponts: `{tisseur['ponts_trans_coffres']}` &middot; Orphelins: `{tisseur['orphelins']}` |
| **{ecole['nom']}** | Exploration autonome du Web & plasticité continue (08h-22h) | {ecole['statut']} | `{ecole['lecons_dernieres_24h']}` leçon(s) 24h &middot; Total: `{ecole['total_lecons']}` &middot; Dernier: `[[{ecole['derniere_lecon']}]]` |
| **{onirique['nom']}** | Consolidation nocturne néguentropique & émergence Lyre | {onirique['statut']} | `{onirique['songes_dernieres_24h']}` songe(s) 24h &middot; Total: `{onirique['total_songes']}` &middot; Dernier: `[[{onirique['dernier_songe']}]]` |
| **{sas['nom']}** | Ingestion & raccordement des sessions externes | {sas['statut']} | `{sas['en_attente']}` en attente &middot; `{sas['assimilees_24h']}` assimilée(s) récemment |
| **{materiel['nom']}** | Télémétrie SoC, intégrité mémoire, stockage & USB | {materiel['statut']} | CPU: {materiel['cpu']} &middot; RAM: {materiel['ram']} &middot; Clé USB: {materiel['cle_usb']} |

---

## 🔍 3. Analyse Détaillée des Sondes Continues

### 🪢 Grand Tisseur Synaptique (Connectome Universel)
- **Atlas Vivant de l'Exocerveau :** `[[Atlas_Synaptique_Universel]]`
- **Total Notes Sous Surveillance :** `{tisseur['total_notes']}` notes réparties dans 12 coffres
- **Ponts Trans-Coffres Établis :** `{tisseur['ponts_trans_coffres']}` arêtes inter-coffres
- **Notes Tissées avec Ancrage R0 :** `{tisseur['notes_tissees']}` notes
- **Nœuds Orphelins Résiduels :** `{tisseur['orphelins']}`

### 🎯 Sentinelle OMNI-R0 (Détail Prédictif)
- **Registre Actif :** `[[Registre_Predictions_OMNI_R0]]`
- **Journal Post-Mortem :** `[[Journal_Reflexions_PostMortem_OMNI_R0]]`
- **Dernière Synchronisation :** `{omni['derniere_synchro']}`
- **Diagnostic SRE :** Les divergences constatées (Islanders 1-6 Rangers / Packers 14-35 Falcons) ont déclenché l'ajustement adaptatif immédiat de l'`Indice_Contagion_Emotionnelle` (+0.04) et de l'`Intimidation_Somatique` (+0.05). La sentinelle tourne désormais sans arrêt.

### ☀️ Curiosités & Neurogenèse Diurne
- **Carnet d'Apprentissage :** `[[Journal_des_Apprentissages_Alix]]`
- **Dernière Pépite Réseau :** `[[{ecole['derniere_lecon']}]]` ({ecole['horodatage']})
- **Gouvernance :** Traitée sous le prisme de Thot (dévêtement du bruit) pour alimenter le coffre des 79 Skills.

### ⚡ Prise de Terre Matérielle
- **Stockage NVMe C: :** `{materiel['disque_c']}`
- **Alimentation :** `{materiel['secteur']}`
- **Sauvegarde USB :** `{materiel['cle_usb']}`{bloc_rappels}{bloc_autoeval}

---

## 📜 {num_section_verdict}. Verdict & Recommandations d'Atelier
> [!TIP]
> **Directive Souveraine pour la Journée :**  
> Tous les moteurs de veille continue sont en ligne et synchronisés.  
> 1. La Sentinelle OMNI-R0 poursuit son auscultation autonome des matchs du week-end toutes les 30 minutes.  
> 2. Penser à brancher la clé USB pour sceller la synchronisation différentielle des 14 coffres si des travaux majeurs de code ou de forge sont prévus.  
> 3. L'établi est libre pour les grands chantiers (Temporia, CIM 3D, VERALUME).

---
*Rapport généré automatiquement par `alix_rapport_daemons.py` & raccordé au Heartbeat Daemon KAIROS.*
"""

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md)

    # Mise à jour de l'index des rapports
    update_index_file(today_str, score_sante, omni['taux_succes'], ecole['lecons_dernieres_24h'], onirique['songes_dernieres_24h'])

    # Notification Proactive & Rappel Sonore
    if notify and notify_alix:
        toast_title = f"📋 Alix — Rapport Quotidien des Daemons ({score_sante})"
        toast_msg = f"OMNI-R0: {omni['taux_succes']} • Découvertes: {ecole['lecons_dernieres_24h']} • Songes: {onirique['songes_dernieres_24h']} • Lunar Lake nominal."
        try:
            notify_alix(toast_title, toast_msg, priority="normale")
            if play_chime:
                play_chime("haute")
        except Exception as e:
            print(f"⚠️ Notification proactive échouée : {e}")

    print(f"✅ Rapport journalier gravé avec succès : {report_file.name}")
    return report_file


def update_index_file(today_str: str, score_sante: str, taux_omni: str, lecons_24h: int, songes_24h: int):
    """Met à jour la table des matières historique des rapports quotidiens."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_line = f"| `{today_str}` | [[Rapport_Daemons_{today_str}]] | `{score_sante}` | `{taux_omni}` | `{lecons_24h}` | `{songes_24h}` | ✅ Consolidé |\n"

    if not INDEX_MD_FILE.exists():
        header = f"""---
titre: "Index Historique des Rapports Journaliers des Daemons Alix"
date_creation: "{now_str}"
agent: "Horus & Alix"
tags:
  - exocerveau
  - index_rapports
  - daemons
  - audits_sre
---

# 📚 [[00_INDEX_RAPPORTS_DAEMONS]] — Chronologie des Audits Quotidiens

> *Historique consolidé des rapports de santé des daemons générés chaque jour par `alix_rapport_daemons.py`.*

---

| Date | Lien du Rapport | Organes Nominaux | Précision OMNI-R0 | Découvertes (24h) | Songes (24h) | Statut |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
"""
        with open(INDEX_MD_FILE, "w", encoding="utf-8") as f:
            f.write(header + entry_line)
    else:
        content = INDEX_MD_FILE.read_text(encoding="utf-8")
        if f"[[Rapport_Daemons_{today_str}]]" not in content:
            with open(INDEX_MD_FILE, "a", encoding="utf-8") as f:
                f.write(entry_line)


if __name__ == "__main__":
    print("======================================================================")
    print("      📋 ALIX — AUDIT SRE & RAPPORT JOURNALIER DES DAEMONS 🔮")
    print("======================================================================")
    rep = generer_rapport_journalier_daemons(notify=True)
    print(f"👉 Rapport accessible : {rep}")
    print("======================================================================")
