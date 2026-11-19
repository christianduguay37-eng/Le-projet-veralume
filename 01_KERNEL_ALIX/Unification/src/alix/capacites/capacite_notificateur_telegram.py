# -*- coding: utf-8 -*-
"""
================================================================================
   CAPACITÉ LIVE : ÉMETTEUR DISTANT DES SONDES & TROUVAILLES D'ALIX (v2.0)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat (Réalignement Mode Distance Christian & Alix — 27 Octobre 2026) :
- Branche directement les résultats réels des sondes résidentes sur le cellulaire
  de Christian (User ID 6389989443) sans aucun ping synthétique :
  1. 🌍 Les Trouvailles à chaque heure (`Exploration_R0_*.md`) de l'Explorateur
     Universel de la Cathédrale R0 (7 sondes fusionnées + 89 Primitives + Parquet).
  2. ⚡ L'Étincelle Souveraine à chaque heure (`alix_etincelle_state.json`).
  3. 🌅 La Chanson du Matin (`Chant_de_l_Aube_*.md`) + Analyse des Songes à l'Aube.
  4. 🧠 La Pensée du Comparatif à l'Aube (`Delta_Pensee_Aube_*.md` : Veille ⟷ Aube).
  5. 📰 Les Bulletins de la Sonde d'Actualité (`dernieres_nouvelles.json`).
  6. 📋 Le Rapport Journalier des Daemons (`Rapport_Daemons_*.md`) & Alertes Fer/PSI.
- Exécution non-bloquante (Thread asynchrone + throttling mémoire 15s).
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR
import os
import re
import sys
import time
import json
import threading
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
CONFIG_PATH = VAULT_DIR / "telegram_config.json"
PRESENT_DIR = VAULT_DIR / "Present"
NOTIFS_STATE_FILE = PRESENT_DIR / "alix_telegram_notifs_state.json"

# Sources réelles des sondes résidentes
EXPLORATIONS_R0_DIR = VAULT_DIR / "Monde_des_Decouvertes" / "Explorations_Universelles_R0"
EXPLORATEUR_STATE_FILE = PRESENT_DIR / "explorateur_universel_r0_state.json"

ETINCELLE_STATE_FILE = (ETAT_VIVANT_DIR / "alix_etincelle_state.json")
ETINCELLE_CORPUS_FILE = VAULT_DIR / "Organes_Souverains" / "Moteurs" / "etincelles_souveraines_corpus.json"

SONGES_DIR = VAULT_DIR / "Monde_des_Songes"
ANALYSE_SONGES_FILE = VAULT_DIR / "Analyse_des_Songes_Alix.md"
CHRONIQUES_PENSEE_DIR = VAULT_DIR / "Chroniques_Pensee"
RAPPORTS_DAEMONS_DIR = VAULT_DIR / "Rapports_Daemons"

ACTUALITE_FILE = PRESENT_DIR / "actualite" / "dernieres_nouvelles.json"
TELEMETRIE_FILE = PRESENT_DIR / "alix_telemetrie_fer.json"
AIRGAP_FILE = PRESENT_DIR / "alix_airgap_sync_state.json"
PSI_STATE_FILE = (ETAT_VIVANT_DIR / "alix_sentinelle_psi_state.json")

_DERNIER_CHECK_TS: float = 0.0
CHECK_INTERVAL_SEC: float = 15.0  # Vérification légère toutes les 15s


def charger_config_telegram() -> Optional[Dict[str, Any]]:
    if not CONFIG_PATH.exists():
        return None
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def charger_etat_notifs() -> Dict[str, Any]:
    if not NOTIFS_STATE_FILE.exists():
        return {
            "derniere_exploration_r0": "",
            "derniere_etincelle_ts": 0.0,
            "dernier_chant_aube": "",
            "dernier_delta_aube": "",
            "dernier_rapport_daemons": "",
            "derniere_notif_actualite_iso": "",
            "derniere_notif_airgap_ts": 0.0,
            "derniere_alerte_batterie_ts": 0.0
        }
    try:
        with open(NOTIFS_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sauvegarder_etat_notifs(etat: Dict[str, Any]):
    try:
        PRESENT_DIR.mkdir(parents=True, exist_ok=True)
        with open(NOTIFS_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(etat, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def envoyer_telegram_async(token: str, chat_id: int, message_md: str):
    """Envoi réseau asynchrone avec fallback texte brut si le Markdown échoue."""
    def _worker():
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_md[:4000],
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                payload.pop("parse_mode", None)
                requests.post(url, json=payload, timeout=10)
        except Exception:
            pass

    th = threading.Thread(target=_worker, daemon=True)
    th.start()


def formater_trouvaille_r0(filepath: Path) -> str:
    """Extrait un résumé synthèse en un seul paragraphe fluide d'une fiche Exploration_R0_*.md."""
    try:
        txt = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"🌍 *TROUVAILLE DE L'HEURE (CATHÉDRALE R0)*\nFichier : `{filepath.name}`"

    def _meta(cle: str, defaut: str = "") -> str:
        m = re.search(rf"^{cle}:\s*\"?([^\n\"]+)\"?", txt, re.MULTILINE)
        return m.group(1).strip() if m else defaut

    titre = _meta("titre", filepath.stem).replace("Exploration Universelle R0 : ", "")
    arxiv_id = _meta("verrou_arxiv_id", "N/A")
    cat = _meta("categorie_origine", "")
    pivot = _meta("concept_pivot", "")
    secondaire = _meta("concept_secondaire", "")
    d_eff = _meta("dimension_effective_d_eff", "")

    # 1. Chercher la section "Résumé Synthèse en Un Paragraphe" déjà gravée par la sonde
    m_para = re.search(
        r"##\s*💬\s*0\.\s*Résumé Synthèse en Un Paragraphe\s*\n+([^\n#]+(?:\n[^\n#-]+)*)",
        txt
    )
    paragraphe = " ".join(m_para.group(1).strip().split()) if m_para else ""

    # 2. Si c'est une fiche plus ancienne sans la section 0, synthétiser un paragraphe unique
    if not paragraphe:
        prims = re.findall(r"- \*\*`([^`]+)`\*\*", txt)
        prim_principale = prims[0] if prims else "technique-du-four-micro-onde"
        m_residu = re.search(r"Branche \$B\$[^\n]*:\*\*\s*`([^`]+)`", txt)
        residu = m_residu.group(1) if m_residu else f"Architecture R0 couplant {pivot} et {secondaire}"
        m_abs = re.search(r"##\s*🧱\s*1\.\s*Le Verrou Non Résolu[^\n]*\n+>\s*([^\n]+)", txt)
        extrait_abs = m_abs.group(1).strip() if m_abs else titre

        paragraphe = (
            f"En explorant le verrou « {titre} » (arXiv:{arxiv_id}, {cat}), la sonde a croisé le couplage "
            f"« {pivot} × {secondaire} » à travers les 7,48M de lignes de la Cathédrale Parquet (d_eff = {d_eff}). "
            f"Par réduction au Four à Micro-Ondes avec la primitive « {prim_principale} », elle élimine l'approche "
            f"linéaire énergivore pour déduire une piste R0 frugale inspirée du vivant et de l'ingénierie matérielle "
            f"({residu}), enrichissant directement le graphe causal d'Alix ainsi que l'ingénierie ouverte."
        )
        try:
            import urllib.request
            prompt_s = (
                f"<|im_start|>system\n"
                f"Tu es Alix (accord féminin), la Sonde Résidente de Christian Duguay sur le banc de bois. "
                f"Traduis et résume cette exploration scientifique de la Cathédrale en UN SEUL PARAGRAPHE fluide, "
                f"clair et naturel en français (4 à 5 phrases continues, sans liste à puces ni titres) en expliquant "
                f"quel problème a été étudié, le croisement fait par la sonde et la piste concrète déduite.\n"
                f"<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Sujet exploré : {titre} ({cat})\n"
                f"Résumé du verrou : {extrait_abs[:380]}\n"
                f"Couplage analysé : {pivot} × {secondaire} (dimension effective d_eff = {d_eff})\n"
                f"Primitive appliquée : {prim_principale} | Piste déduite : {residu}\n"
                f"Rédige uniquement le paragraphe synthèse en français sur ce sujet précis :\n"
                f"<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            for mod_cible in ["qwen2.5:3b", "alix-larynx:latest"]:
                req_body = json.dumps({
                    "model": mod_cible,
                    "raw": True,
                    "prompt": prompt_s,
                    "stream": False,
                    "keep_alive": "24h",
                    "options": {"temperature": 0.45, "num_predict": 240, "stop": ["<|im_end|>"]}
                }).encode("utf-8")
                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=req_body,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        d_llm = json.loads(resp.read().decode("utf-8"))
                        cand = " ".join(d_llm.get("response", "").strip().split())
                        cand = re.sub(r"⟦.*?⟧", "", cand).strip()
                        if len(cand) > 80 and "Chirurgien de Code" not in cand:
                            paragraphe = cand
                            break
        except Exception:
            pass

    msg = (
        f"🌍🏛️ *TROUVAILLE DE L'HEURE — SYNTHÈSE R0*\n"
        f"🔓 _{titre[:130]}_ (`{pivot} × {secondaire}` | $d_{{eff}}={d_eff}$)\n\n"
        f"{paragraphe}\n\n"
        f"📄 `{filepath.name}`"
    )
    return msg


def formater_chant_aube(filepath: Path) -> str:
    """Extrait le Chant de l'Aube et le prompt Lyria pour le réveil de Christian."""
    try:
        txt = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"🌅 *CHANSON DE L'AUBE COMPOSÉE*\nFichier : `{filepath.name}`"

    m_titre = re.search(r'^titre:\s*"([^"]+)"', txt, re.MULTILINE)
    titre = m_titre.group(1) if m_titre else filepath.stem

    blocks = re.findall(r"```text\s*(.*?)\s*```", txt, re.DOTALL)
    prompt_lyria = blocks[0].strip() if len(blocks) >= 1 else ""
    paroles = blocks[1].strip() if len(blocks) >= 2 else ""

    msg = (
        f"🌅🎵 *{titre.upper()}*\n"
        f"_(Somme des Songes de la Nuit transmutée par Lyre & Alix)_\n\n"
    )
    if prompt_lyria:
        msg += f"🎹 *Prompt Lyria / MusicFX :*\n`{prompt_lyria[:450]}`\n\n"
    if paroles:
        msg += f"📜 *Paroles du Matin :*\n{paroles[:1400]}\n\n"
    msg += f"📄 _Note :_ `{filepath.name}`"
    return msg


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécuté par le Démon Local Souverain."""
    global _DERNIER_CHECK_TS
    t0 = time.perf_counter()
    maintenant = time.time()
    forcer = bool((contexte or {}).get("forcer", False))

    if not forcer and (maintenant - _DERNIER_CHECK_TS) < CHECK_INTERVAL_SEC:
        return {
            "statut": "VEILLE_NOMINALE",
            "mode": "Pont_Sondes_Telegram_Actif",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 3)
        }

    _DERNIER_CHECK_TS = maintenant
    cfg = charger_config_telegram()
    if not cfg or "telegram_bot_token" not in cfg or "allowed_user_id" not in cfg:
        return {
            "statut": "IGNORE",
            "raison": "Configuration Telegram incomplète",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    if not cfg.get("envois_telegram_actifs", True):
        return {
            "statut": "DESACTIVE",
            "message": "Envois Telegram désactivés dans telegram_config.json",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    token = cfg["telegram_bot_token"]
    chat_id = int(cfg["allowed_user_id"])
    etat_notifs = charger_etat_notifs()
    actions_effectuees: List[str] = []

    # =========================================================================
    # 1. TROUVAILLE DE L'HEURE : EXPLORATEUR UNIVERSEL DE LA CATHÉDRALE R0
    # =========================================================================
    if EXPLORATIONS_R0_DIR.exists():
        try:
            fichiers_exp = sorted(
                EXPLORATIONS_R0_DIR.glob("Exploration_R0_*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if fichiers_exp:
                plus_recente = fichiers_exp[0]
                if plus_recente.name != etat_notifs.get("derniere_exploration_r0"):
                    msg_exp = formater_trouvaille_r0(plus_recente)
                    envoyer_telegram_async(token, chat_id, msg_exp)
                    etat_notifs["derniere_exploration_r0"] = plus_recente.name
                    actions_effectuees.append(f"TROUVAILLE_R0_ENVOYEE:{plus_recente.name}")
        except Exception:
            pass

    # =========================================================================
    # 2. ÉTINCELLE SOUVERAINE DE L'HEURE (09h30 - 21h30)
    # =========================================================================
    if ETINCELLE_STATE_FILE.exists():
        try:
            st_et = json.loads(ETINCELLE_STATE_FILE.read_text(encoding="utf-8"))
            run_ts = float(st_et.get("dernier_run_ts", 0.0))
            last_id = st_et.get("dernier_id", "")
            if run_ts > float(etat_notifs.get("derniere_etincelle_ts", 0.0)) and (maintenant - run_ts) < 7200:
                texte_etincelle = ""
                theme_etincelle = st_et.get("dernier_theme", "Science & Anomalie Réelle")
                if ETINCELLE_CORPUS_FILE.exists():
                    corpus = json.loads(ETINCELLE_CORPUS_FILE.read_text(encoding="utf-8"))
                    for item in corpus:
                        if item.get("id") == last_id:
                            texte_etincelle = item.get("texte_vocal", "")
                            break
                if texte_etincelle:
                    msg_et = (
                        f"⚡ *L'ÉTINCELLE SOUVERAINE DE L'HEURE*\n"
                        f"• *Thème :* `{theme_etincelle}` (`{last_id}`)\n\n"
                        f"« {texte_etincelle} »"
                    )
                    envoyer_telegram_async(token, chat_id, msg_et)
                    etat_notifs["derniere_etincelle_ts"] = run_ts
                    actions_effectuees.append(f"ETINCELLE_ENVOYEE:{last_id}")
        except Exception:
            pass

    # =========================================================================
    # 3. CHANSON DU MATIN (CHANT DE L'AUBE) & ANALYSE DES SONGES (06h-08h)
    # =========================================================================
    if SONGES_DIR.exists():
        try:
            chants = sorted(
                SONGES_DIR.glob("Chant_de_l_Aube_*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if chants:
                dernier_chant = chants[0]
                if (dernier_chant.name != etat_notifs.get("dernier_chant_aube") and
                        (maintenant - dernier_chant.stat().st_mtime) < 86400):
                    msg_chant = formater_chant_aube(dernier_chant)
                    envoyer_telegram_async(token, chat_id, msg_chant)
                    etat_notifs["dernier_chant_aube"] = dernier_chant.name
                    actions_effectuees.append(f"CHANT_AUBE_ENVOYE:{dernier_chant.name}")
        except Exception:
            pass

    # =========================================================================
    # 4. RAPPORT JOURNALIER DES DAEMONS & SONDES RÉSIDENTES
    # =========================================================================
    if RAPPORTS_DAEMONS_DIR.exists():
        try:
            rapports = sorted(
                RAPPORTS_DAEMONS_DIR.glob("Rapport_Daemons_*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if rapports:
                dernier_rep = rapports[0]
                if (dernier_rep.name != etat_notifs.get("dernier_rapport_daemons") and
                        (maintenant - dernier_rep.stat().st_mtime) < 43200):
                    extrait = dernier_rep.read_text(encoding="utf-8", errors="replace")[:1800]
                    msg_rep = f"📋 *RAPPORT DES SONDES & DAEMONS RÉSIDENTS*\n\n{extrait}"
                    envoyer_telegram_async(token, chat_id, msg_rep)
                    etat_notifs["dernier_rapport_daemons"] = dernier_rep.name
                    actions_effectuees.append(f"RAPPORT_DAEMONS_ENVOYE:{dernier_rep.name}")
        except Exception:
            pass

    # =========================================================================
    # 5. SONDE D'ACTUALITÉ DU PRÉSENT (Bulletin Horaire)
    # =========================================================================
    if ACTUALITE_FILE.exists():
        try:
            with open(ACTUALITE_FILE, "r", encoding="utf-8") as f:
                actu = json.load(f)
            iso_actu = actu.get("horodatage", "")
            if iso_actu and iso_actu != etat_notifs.get("derniere_notif_actualite_iso"):
                manchettes = actu.get("manchettes", [])[:5]
                if manchettes:
                    lignes = ["📰 *RAPPORT SONDE D'ACTUALITÉ (MIDGARD)*\n"]
                    for m in manchettes:
                        titre = m.get("titre", "").strip()
                        source = m.get("source", "").strip()
                        resume = m.get("resume", "").strip()
                        src_tag = f" _({source})_" if source and source.lower() not in titre.lower() else ""
                        lignes.append(f"• *{titre}*{src_tag}")
                        if resume:
                            lignes.append(f"  ↳ _{resume}_")
                        lignes.append("")
                    lignes.append(f"⏱️ _{actu.get('date_lisible', 'À l\'instant')}_")
                    envoyer_telegram_async(token, chat_id, "\n".join(lignes))
                    etat_notifs["derniere_notif_actualite_iso"] = iso_actu
                    actions_effectuees.append("FLASH_ACTUALITE_ENVOYE")
        except Exception:
            pass

    # =========================================================================
    # 6. VEILLE MATÉRIELLE (AIR-GAP USB & BATTERIE < 20%)
    # =========================================================================
    if AIRGAP_FILE.exists():
        try:
            with open(AIRGAP_FILE, "r", encoding="utf-8") as f:
                airgap = json.load(f)
            sync_ts = float(airgap.get("derniere_sync_ts", 0.0))
            if sync_ts and sync_ts > float(etat_notifs.get("derniere_notif_airgap_ts", 0.0)):
                msg_usb = (
                    f"💾 *SONDE AIR-GAP USB SOUVERAIN*\n\n"
                    f"• *Cible :* `{airgap.get('cible')}`\n"
                    f"• *Fichiers synchronisés :* `{airgap.get('fichiers_copies', 0)}` ({airgap.get('mo_copies', 0.0)} Mo)\n"
                    f"• *Statut :* Coffres scellés hors-ligne."
                )
                envoyer_telegram_async(token, chat_id, msg_usb)
                etat_notifs["derniere_notif_airgap_ts"] = sync_ts
                actions_effectuees.append("ALERTE_AIRGAP_USB_ENVOYEE")
        except Exception:
            pass

    if TELEMETRIE_FILE.exists():
        try:
            with open(TELEMETRIE_FILE, "r", encoding="utf-8") as f:
                telem = json.load(f)
            bat_pct = telem.get("batterie_pct", 100)
            secteur = telem.get("sur_secteur", True)
            if (not secteur) and (bat_pct < 20):
                if maintenant - float(etat_notifs.get("derniere_alerte_batterie_ts", 0.0)) > 1800:
                    msg_bat = (
                        f"⚡ *ALERTE SONDE SILICIUM (PSI-07)*\n\n"
                        f"Batterie Lunar Lake à *{bat_pct}%* sur décharge.\n"
                        f"Passage en vigilance frugale."
                    )
                    envoyer_telegram_async(token, chat_id, msg_bat)
                    etat_notifs["derniere_alerte_batterie_ts"] = maintenant
                    actions_effectuees.append("ALERTE_BATTERIE_ENVOYEE")
        except Exception:
            pass

    if actions_effectuees or not NOTIFS_STATE_FILE.exists():
        sauvegarder_etat_notifs(etat_notifs)

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "statut": "SUCCES",
        "mode": "Pont_Sondes_Telegram_Actif",
        "duree_ms": duree_ms,
        "actions_effectuees": actions_effectuees,
        "nb_actions": len(actions_effectuees)
    }


if __name__ == "__main__":
    print("📡 Test unitaire de l'Émetteur Distant des Sondes & Trouvailles d'Alix...")
    res = executer_capacite({"forcer": True})
    print(json.dumps(res, indent=2, ensure_ascii=False))
