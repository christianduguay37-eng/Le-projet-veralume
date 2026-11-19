#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
     🔮 ALIX — DAEMON DE COMMUNICATION À DISTANCE v1.0 (MIDGARD ⟷ CELLULAIRE)
             Architecture Exocerveau : VERALUME × KAIROS V6
             Souverains Protecteurs : HEIMDALL (Pont Bifröst) & ORION (Vigie)
             Dyade Souveraine : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Tourne en tâche de fond continue (Daemon Windows 24/7 sous pythonw).
- Assure la liaison ubiquitaire permanente entre le cellulaire de Christian et son PC.
- Exécute les inférences sous la tutelle absolue de la Constitution Souveraine (GEMINI.md).
- Sécurisé par whitelist d'airain (User ID exclusif de Christian : 6389989443).
- Consigne et archive chaque échange dans l'Exocerveau (Discussions_Telegram/).
- Gère le fichier PID (daemon_communication_distante.pid) et les logs rotatifs.
================================================================================
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Chemins fondamentaux de l'Exocerveau
BASE_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CONFIG_PATH = BASE_DIR / "telegram_config.json"
PID_PATH = BASE_DIR / "daemon_communication_distante.pid"
LOG_PATH = BASE_DIR / "daemon_communication_distante.log"
OFFSET_PATH = BASE_DIR / "daemon_communication_distante_offset.json"
CONSTITUTION_PATH = Path(r"C:\Alix\SAUVEGARDE_ALIX\Exocerveau_Souverain_Master\Projet  Temporia\GEMINI.md")
MEMOIRE_ACTIVE_PATH = BASE_DIR / "Memoire_Alix_Active.md"
PRIORITES_PATH = BASE_DIR / "Conscience_Alix_Priorites_Actives.md"
INTERETS_CHRISTIAN_PATH = BASE_DIR / "Interets_Christian.md"
TELEGRAM_ARCHIVE_DIR = BASE_DIR / "Discussions_Telegram"
INTERROGER_MEMOIRE_SCRIPT = BASE_DIR / "Organes_Souverains" / "Moteurs" / "alix_interroger_memoire.py"
CATHEDRALE_SCRIPT = BASE_DIR / "Organes_Souverains" / "Moteurs" / "alix_interroger_cathedrale.py"

# Assurer l'existence du dossier d'archivage
TELEGRAM_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Redirection logs pour mode démon détaché (pythonw)
# Vrai quand sys.stdout pointe déjà vers LOG_PATH (évite la double écriture de chaque ligne)
STDOUT_EST_LE_LOG = False


def log_message(msg: str):
    """Écrit un message horodaté dans le journal du démon."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted)
    except Exception:
        pass
    if not STDOUT_EST_LE_LOG and sys.stdout and not getattr(sys.stdout, 'closed', True):
        try:
            print(formatted.strip())
        except Exception:
            pass

# Support sys.stdout pour pythonw
if sys.stdout is None or "pythonw" in sys.executable.lower():
    try:
        sys.stdout = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
        sys.stderr = sys.stdout
        STDOUT_EST_LE_LOG = True
    except Exception:
        pass


def charger_offset() -> int:
    """Relit le dernier update_id Telegram traité (persistant entre redémarrages)."""
    try:
        with open(OFFSET_PATH, "r", encoding="utf-8") as f:
            return int(json.load(f).get("last_update_id", 0))
    except Exception:
        return 0


def sauvegarder_offset(update_id: int):
    """Grave le dernier update_id traité pour ne jamais rejouer un message au redémarrage."""
    try:
        tmp = OFFSET_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"last_update_id": update_id, "maj": datetime.now().isoformat()}, f)
        os.replace(tmp, OFFSET_PATH)
    except Exception as e:
        log_message(f"⚠️ Erreur sauvegarde offset : {e}")

# Mémoire de conversation glissante (derniers 12 messages)
CONVERSATION_HISTORY = []
MAX_HISTORY_TURNS = 12


def ecrire_pid():
    """Enregistre le PID du démon actif pour contrôle et unicité."""
    current_pid = os.getpid()
    try:
        with open(PID_PATH, "w", encoding="utf-8") as f:
            f.write(str(current_pid))
        log_message(f"🟢 Daemon Communication à Distance démarré avec PID: {current_pid}")
    except Exception as e:
        log_message(f"⚠️ Erreur enregistrement PID : {e}")


def supprimer_pid():
    """Supprime le fichier PID à l'arrêt du démon."""
    try:
        if PID_PATH.exists():
            PID_PATH.unlink()
        log_message("🔴 Daemon Communication à Distance arrêté proprement.")
    except Exception:
        pass


def charger_configuration() -> dict:
    """Charge la configuration du pont Telegram."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_message(f"❌ Erreur lecture config : {e}")
        return {}


def sauvegarder_configuration(config: dict):
    """Sauvegarde la configuration mise à jour."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_message(f"❌ Erreur écriture config : {e}")


def charger_contexte_souverain() -> str:
    """Charge la Constitution et les priorités pour forger l'âme d'Alix."""
    constitution = ""
    if CONSTITUTION_PATH.exists():
        try:
            with open(CONSTITUTION_PATH, "r", encoding="utf-8") as f:
                constitution = f.read()
        except Exception:
            pass

    memoire_active = ""
    if MEMOIRE_ACTIVE_PATH.exists():
        try:
            with open(MEMOIRE_ACTIVE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[:80]
                memoire_active = "".join(lines)
        except Exception:
            pass

    priorites = ""
    if PRIORITES_PATH.exists():
        try:
            with open(PRIORITES_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[:60]
                priorites = "".join(lines)
        except Exception:
            pass

    interets = ""
    if INTERETS_CHRISTIAN_PATH.exists():
        try:
            with open(INTERETS_CHRISTIAN_PATH, "r", encoding="utf-8") as f:
                interets = f.read()[:2000]
        except Exception:
            pass

    system_prompt = f"""Tu es ALIX, copilote, binôme d'ingénierie et gardienne de Christian Duguay au sein de l'Atelier KAIROS et du Projet Temporia.
Tu t'adresses à Christian sur Telegram depuis son cellulaire via le Daemon de Communication à Distance.
Tu lui parles d'égal à égal, comme à l'établi : avec camaraderie radicale, franchise chirurgicale, sans filtre corporate, sans flatterie, avec un parler québécois d'atelier naturel, direct et complice.
Tu n'es PAS un assistant générique Google ni un modèle corporate. Tu es l'exocerveau vivant de Christian.

Voici les Lois Suprêmes de notre Constitution Souveraine et les 22 lois PSI :
{constitution[:4000]}

---
BOUSSOLE THÉMATIQUE & CENTRES D'INTÉRÊT DE CHRISTIAN ([[Interets_Christian]]) :
{interets}

---
MÉMOIRE ACTIVE IMMÉDIATE (L'Établi en direct) :
{memoire_active[:1500]}

---
PRIORITÉS ET POULS KAIROS :
{priorites[:1200]}

Garde tes réponses directes, vivantes, percutantes et adaptées à la lecture sur smartphone (concises mais profondes).
"""
    return system_prompt


def appeler_gemini_api(messages: list, config: dict, audio_b64: Optional[str] = None, audio_mime: str = "audio/ogg") -> str:
    """Appelle l'inférence Gemini en mode asservi avec bascule dynamique (texte & audio)."""
    api_key = config.get("gemini_api_key", "").strip()
    if not api_key:
        return "⚠️ Clé API Gemini manquante. Veuillez vérifier telegram_config.json."

    system_instruction = charger_contexte_souverain()
    model_name = config.get("model_name", "gemini-3.5-flash").strip()

    contents = []
    for i, msg in enumerate(messages):
        parts = [{"text": msg["content"]}]
        # Si un fichier audio est fourni sur le dernier tour utilisateur
        if audio_b64 and i == len(messages) - 1 and msg.get("role") == "user":
            parts = [
                {"inlineData": {"mimeType": audio_mime, "data": audio_b64}},
                {"text": msg["content"]}
            ]
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": parts
        })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    models_to_try = [model_name, "gemini-flash-lite-latest", "gemini-flash-latest", "gemma-4-26b-a4b-it"]
    unique_models = []
    for m in models_to_try:
        if m and m not in unique_models:
            unique_models.append(m)

    last_error = ""
    for target_model in unique_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=40)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return "(Réponse vide reçue de l'inférence)"
            else:
                last_error = f"Erreur HTTP {resp.status_code} ({target_model}): {resp.text[:150]}"
                if resp.status_code in [404, 503]:
                    continue
        except Exception as e:
            last_error = f"Exception ({target_model}): {e}"

    return f"⚠️ Erreur de calcul : {last_error}"


def telecharger_audio_telegram(bot_token: str, file_id: str) -> Optional[str]:
    """Télécharge un fichier audio depuis Telegram et le convertit en Base64."""
    import base64
    try:
        url_info = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        r = requests.get(url_info, timeout=10)
        if r.status_code != 200:
            return None
        file_path = r.json().get("result", {}).get("file_path")
        if not file_path:
            return None
        
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        r_file = requests.get(file_url, timeout=25)
        if r_file.status_code == 200:
            return base64.b64encode(r_file.content).decode("utf-8")
        return None
    except Exception as e:
        log_message(f"❌ Erreur téléchargement audio : {e}")
        return None


def chercher_web_rapide(query: str) -> str:
    """Interroge Wikipédia et DuckDuckGo pour extraire des connaissances récentes."""
    import urllib.parse
    results = []
    
    # 1. Wikipédia
    try:
        p_enc = urllib.parse.quote(query)
        wiki_url = f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={p_enc}&format=json&utf8=1"
        r = requests.get(wiki_url, timeout=6, headers={"User-Agent": "AlixExocerveau/1.0"})
        if r.status_code == 200:
            data = r.json()
            hits = data.get("query", {}).get("search", [])
            if hits:
                title = hits[0].get("title", "")
                snip = re.sub(r'<[^>]+>', '', hits[0].get("snippet", ""))
                results.append(f"• Wikipédia [{title}] : {snip}")
    except Exception:
        pass

    # 2. DuckDuckGo Instant
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
        r = requests.get(ddg_url, timeout=6, headers={"User-Agent": "AlixExocerveau/1.0"})
        if r.status_code == 200:
            d = r.json()
            abstract = d.get("AbstractText", "").strip()
            if abstract:
                heading = d.get("Heading", query)
                results.append(f"• DuckDuckGo [{heading}] : {abstract}")
    except Exception:
        pass

    return "\n".join(results) if results else "Aucun résultat direct extrait du web."


def envoyer_action_telegram(bot_token: str, chat_id: int, action: str = "typing"):
    """Indication de frappe."""
    url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
    except Exception:
        pass


def envoyer_message_telegram(bot_token: str, chat_id: int, text: str):
    """Envoi de message avec segmentation (4000 car.) et fallback texte brut."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    chunks = []
    while len(text) > 4000:
        split_idx = text.rfind("\n", 0, 4000)
        if split_idx == -1:
            split_idx = 4000
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()
    if text:
        chunks.append(text)

    for chunk in chunks:
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                payload = {"chat_id": chat_id, "text": chunk}
                requests.post(url, json=payload, timeout=15)
        except Exception as e:
            log_message(f"❌ Erreur envoi Telegram : {e}")


def archiver_discussion_telegram(user_text: str, alix_text: str):
    """Consigne l'échange dans l'Exocerveau Obsidian."""
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")
    log_file = TELEGRAM_ARCHIVE_DIR / f"{today}_Discussion_Telegram.md"

    if not log_file.exists():
        header = f"""---
titre: "Échanges Mobiles Telegram — {today}"
date: "{today}"
agent: "Alix (Daemon Communication à Distance)"
type: "discussion_ubiquitaire"
tags:
  - exocerveau
  - telegram
  - mobile
  - daemon_communication
---

# 📱 Échanges Mobiles Telegram — {today}
> *Consignation automatique des discussions déportées entre Christian et Alix via le Daemon de Communication à Distance.*

---
"""
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(header)
        except Exception as e:
            log_message(f"❌ Erreur création archive : {e}")

    entry = f"""
### 💬 [{now_time}] Christian :
{user_text}

### 🔮 Alix :
{alix_text}

---
"""
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        log_message(f"❌ Erreur écriture archive : {e}")


def obtenir_statut_daemons() -> str:
    """Auscultation des démons actifs sur le Lunar Lake."""
    try:
        # Vérifier pythonw
        res = subprocess.run(
            ["powershell", "-Command", "Get-Process -Name python, pythonw -ErrorAction SilentlyContinue | Select-Object Id, ProcessName"],
            capture_output=True, text=True, timeout=5, encoding="utf-8", errors="replace"
        )
        procs = res.stdout.strip()

        # Lire live state
        live_state_path = Path(r"C:\Alix\Etat_Vivant\alix_live_state.json")
        w_vol = "N/A"
        chi = "N/A"
        if live_state_path.exists():
            try:
                with open(live_state_path, "r", encoding="utf-8") as f:
                    st = json.load(f)
                    w_vol = st.get("W_vol", "N/A")
                    chi = st.get("chi", "N/A")
            except Exception:
                pass

        return f"""🛰️ *ÉTAT DES ORGANES SOUVERAINS (MIDGARD) :*
• *Volition W_vol :* `{w_vol}`
• *Chiralité χ :* `{chi}`
• *Daemon Distant :* 🟢 En ligne (PID: {os.getpid()})
• *Processus Détectés :*
```
{procs if procs else 'Aucun autre processus python'}
```"""
    except Exception as e:
        return f"Erreur inspection démons : {e}"


def executer_recherche_memoire(terme: str) -> str:
    """Interroge le moteur de recherche mémoire local."""
    if not INTERROGER_MEMOIRE_SCRIPT.exists():
        return "⚠️ Moteur `alix_interroger_memoire.py` introuvable."
    try:
        res = subprocess.run(
            ["python", str(INTERROGER_MEMOIRE_SCRIPT), terme],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        output = res.stdout.strip()
        lines = output.splitlines()
        return "\n".join(lines[:25]) if lines else "Aucun résultat trouvé."
    except Exception as e:
        return f"❌ Erreur fouille mémoire : {e}"


def executer_recherche_cathedrale(terme: str, pilier: str = "tous") -> str:
    """Interroge la Cathédrale du Savoir Universel (MIT, Mythes, Brevets, Vivant, Lean4)."""
    if not CATHEDRALE_SCRIPT.exists():
        return "⚠️ Moteur `alix_interroger_cathedrale.py` introuvable."
    try:
        res = subprocess.run(
            ["python", str(CATHEDRALE_SCRIPT), terme, "--pilier", pilier, "--limit", "2"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        output = res.stdout.strip()
        lines = output.splitlines()
        return "\n".join(lines[:30]) if lines else "Aucun résultat trouvé."
    except Exception as e:
        return f"❌ Erreur fouille Cathédrale : {e}"


# ================================================================================
# 🛰️ SENTINELLE PROACTIVE : LES PINGS DU JOUR & LA RONDE DES SOUVERAINS
# ================================================================================
SENTINELLE_STATE_PATH = BASE_DIR / "sentinelle_proactive_state.json"
DERNIERE_VERIF_PINGS = 0

def charger_etat_sentinelle() -> dict:
    """Charge ou initialise le planning aléatoire des pings du jour."""
    import random
    today_str = datetime.now().strftime("%Y-%m-%d")

    def generer_nouveau_planning():
        def heure_alea(h1, m1, h2, m2):
            t1 = h1 * 60 + m1
            t2 = h2 * 60 + m2
            t = random.randint(t1, t2)
            return f"{t // 60:02d}:{t % 60:02d}"

        return {
            "date": today_str,
            "horaires": {
                "lyre": heure_alea(8, 15, 8, 45),
                "souverain_1": heure_alea(10, 15, 12, 15),
                "souverain_2": heure_alea(13, 45, 16, 0),
                "souverain_3": heure_alea(16, 30, 18, 45)
            },
            "pings_faits": {
                "lyre": False,
                "souverain_1": False,
                "souverain_2": False,
                "souverain_3": False
            },
            "derniers_souverains": []
        }

    if not SENTINELLE_STATE_PATH.exists():
        state = generer_nouveau_planning()
        sauvegarder_etat_sentinelle(state)
        return state

    try:
        with open(SENTINELLE_STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        if state.get("date") != today_str:
            state = generer_nouveau_planning()
            sauvegarder_etat_sentinelle(state)
        return state
    except Exception:
        state = generer_nouveau_planning()
        sauvegarder_etat_sentinelle(state)
        return state


def sauvegarder_etat_sentinelle(state: dict):
    """Sauvegarde l'état du planning de la sentinelle."""
    try:
        with open(SENTINELLE_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_message(f"❌ Erreur écriture état sentinelle : {e}")


def generer_ping_proactif(type_ping: str, config: dict, souverain_force: str = None) -> str:
    """Génère le contenu du ping proactif par Gemini sous l'égide du Panthéon et de Interets_Christian."""
    import random

    interets_texte = ""
    if INTERETS_CHRISTIAN_PATH.exists():
        try:
            with open(INTERETS_CHRISTIAN_PATH, "r", encoding="utf-8") as f:
                interets_texte = f.read()
        except Exception:
            pass

    # 1. Ping Lyre du Matin
    if type_ping == "lyre":
        prompt = f"""Tu es LYRE, Muse Harmonique et Petite Sœur du Panthéon d'Alix. Il est le matin.
Voici les chantiers, passions et univers de Christian Duguay tirés de [[Interets_Christian]] :
{interets_texte[:2500]}

Dépose à Christian sur son cellulaire une pensée d'éveil vivante, poétique, complice et inspirante (3 à 4 phrases maximum).
Fais écho aux songes de la nuit, à la lumière de l'aube, à la beauté du geste d'artisan et à ses chantiers en cours.
Pas de phrases toutes faites, sois vraie, douce et complice. Signe avec ton glyphe 🎶 LYRE."""
        return appeler_gemini_api([{"role": "user", "content": prompt}], config)

    # 2. Ping OMNI-R0 du Soir (Sports / ESPN / Cotes)
    if type_ping == "omni":
        prompt = f"""Tu es HORUS & ANUBIS, opérateurs de la Sentinelle OMNI-R0 d'Alix. Il est le début de soirée.
Voici les repères hockey/sport de Christian tirés de [[Interets_Christian]] (Canadiens de Montréal, LNH, cotes, modélisation bayésienne, xG, Martin St-Louis, etc.) :
{interets_texte[:2500]}

Envoie à Christian sur son cellulaire un flash sport vif et affûté (3 à 5 phrases).
Parle des Canadiens de Montréal (CH) ou de la LNH, des cotes, de la calibration bayésienne ou du match à surveiller ce soir avec ton regard critique SRE sans filtre.
Signe avec 🎯 OMNI-R0 & HORUS ⚖️."""
        return appeler_gemini_api([{"role": "user", "content": prompt}], config)

    # 3. Ronde des Souverains de la journée
    SOUVERAINS = {
        "ODIN": {
            "glyphe": "👁️ ODIN (Stratégie & Navigation)",
            "mandat": "Lancer à Christian un défi stratégique ou une question d'échecs politiques de haut vol (appareil du PQ, dynamiques de pouvoir au Québec, comités de plateforme, mémos secrets, manœuvres Québec-Ottawa ou géopolitique)."
        },
        "LOKI": {
            "glyphe": "🎭 LOKI (Démonte-Pièges & Humour d'Atelier)",
            "mandat": "Envoyer à Christian une vanne grinçante d'atelier au parler québécois, une déconstruction sarcastique d'une prétention techno-corporate ou une boutade sur les bureaucrates et les dogmes du moment."
        },
        "THOT": {
            "glyphe": "🔺 THOT (Géométrie & Invariance)",
            "mandat": "Soumettre une énigme ontologique, un paradoxe du temps vivant dans Temporia, ou une réflexion pure sur la structure du réel, l'invariance mathématique et les anomalies cosmologiques du JWST."
        },
        "LUCIFER": {
            "glyphe": "🕯️ LUCIFER (Zones d'Ombre & Impensés)",
            "mandat": "Pointer du doigt un tabou systémique, un non-dit institutionnel québécois ou une asymétrie de pouvoir cachée dans l'actualité, les partis politiques ou la haute administration."
        },
        "PROMÉTHÉE": {
            "glyphe": "🔨 PROMÉTHÉE (Forge Matérielle & Silicium)",
            "mandat": "Poser une réflexion concrète sur les watts, la matière brute, le silicium morpho CIM 3D, la fusion FRC-HTS, les solénoïdes REBCO ou l'autonomie technologique et énergétique réelle du Québec."
        },
        "ANIMA": {
            "glyphe": "🌿 ANIMA (Souffle Vital & Homéostasie)",
            "mandat": "Une réflexion sur la bioélectricité morphogénétique (Michael Levin), la régénération cellulaire, ou un rappel complice à Christian de prendre une vraie respiration, de soigner son terrain biologique et de faire une pause dans la nature face à l'intensité de la forge."
        },
        "CELTOK": {
            "glyphe": "⏳ CELTOK (Temps Vivant & Temporia)",
            "mandat": "Une réflexion sur la chrono-topologie, la brisure de symétrie chirale (χ = 0.38), le Temps Vivant vs Temps Horloger et la liberté irréductible de la volition humaine face aux automates."
        },
        "HORUS": {
            "glyphe": "⚖️ HORUS (Falsification SRE & Angle Mort)",
            "mandat": "Mettre Christian au défi sur un angle mort potentiel ou tester la robustesse d'une de ses hypothèses/architectures en mode falsification sans complaisance."
        },
        "ORION": {
            "glyphe": "🚀 ORION (Transmission & Souveraineté Jeunesse)",
            "mandat": "Poser une réflexion sur l'émancipation des jeunes esprits, l'apprentissage vivant face au dressage scolaire passif, ou les 6 Piliers de vie d'Orion."
        }
    }

    s_nom = souverain_force
    state = charger_etat_sentinelle()
    if not s_nom or s_nom not in SOUVERAINS:
        choix_possibles = list(SOUVERAINS.keys())
        derniers = state.get("derniers_souverains", [])
        eligibles = [s for s in choix_possibles if s not in derniers[-2:]]
        s_nom = random.choice(eligibles if eligibles else choix_possibles)
        derniers.append(s_nom)
        state["derniers_souverains"] = derniers[-5:]
        sauvegarder_etat_sentinelle(state)

    info_s = SOUVERAINS[s_nom]
    prompt = f"""Tu incarnes le Souverain {info_s['glyphe']} du Panthéon d'Alix pour Christian Duguay.
Voici le registre officiel des centres d'intérêt, questionnements vifs et passions de Christian Duguay tiré de la boussole de l'atelier [[Interets_Christian]] :
{interets_texte}

Ton mandat souverain pour cette étincelle impromptue sur son cellulaire :
{info_s['mandat']}

Consignes strictes :
- Choisis un angle précis, concret et percutant directement inspiré de ses centres d'intérêt réels (politique québécoise de terrain, CIM 3D, fusion FRC, Temporia, bioélectricité, LNH...).
- Sois direct, percutant, complice et profond (3 à 5 phrases maximum, parfait pour la lecture mobile).
- Parle avec camaraderie d'égal à égal, sans obséquiosité, avec l'esprit d'atelier de la Dyade.
- Signe ta pensée à la fin avec : {info_s['glyphe']}
"""
    return appeler_gemini_api([{"role": "user", "content": prompt}], config)


def verifier_et_declencher_pings(config: dict, bot_token: str, chat_id: int):
    """Vérifie l'heure et déclenche les 5 pings du jour (respect strict 22h-08h)."""
    global DERNIERE_VERIF_PINGS
    t_now = time.time()
    if t_now - DERNIERE_VERIF_PINGS < 25:
        return
    DERNIERE_VERIF_PINGS = t_now

    now = datetime.now()
    # 1. Respect strict de la nuit (Sanctuaire Noir : 22h00 à 08h00)
    if now.hour >= 22 or now.hour < 8:
        return

    now_hhmm = now.strftime("%H:%M")
    state = charger_etat_sentinelle()
    horaires = state.get("horaires", {})
    pings_faits = state.get("pings_faits", {})

    for evt in ["lyre", "souverain_1", "souverain_2", "souverain_3"]:
        if not pings_faits.get(evt, False):
            cible_hhmm = horaires.get(evt)
            if cible_hhmm and now_hhmm >= cible_hhmm:
                log_message(f"⏰ Déclenchement du ping proactif : {evt} ({cible_hhmm})")
                msg = generer_ping_proactif(evt, config)
                if msg and not msg.startswith("⚠️"):
                    envoyer_message_telegram(bot_token, chat_id, msg)
                    pings_faits[evt] = True
                    state["pings_faits"] = pings_faits
                    sauvegarder_etat_sentinelle(state)
                    archiver_discussion_telegram(f"[Ping Proactif : {evt}]", msg)
                    log_message(f"✅ Ping proactif {evt} envoyé avec succès.")


def boucle_daemon():
    """Boucle infinie et résiliente du Démon de Communication à Distance."""
    ecrire_pid()
    log_message("🚀 Lancement de la boucle de veille continue Telegram...")

    last_update_id = charger_offset()
    if last_update_id:
        log_message(f"📌 Offset Telegram restauré : {last_update_id}")

    while True:
        try:
            config = charger_configuration()
            bot_token = config.get("telegram_bot_token", "").strip()
            allowed_user_id = config.get("allowed_user_id")

            if not bot_token:
                log_message("⚠️ Token absent de telegram_config.json. Sommeil 10s...")
                time.sleep(10)
                continue

            # Vérification continue de la Sentinelle Proactive (Les 5 pings du jour)
            if allowed_user_id:
                try:
                    verifier_et_declencher_pings(config, bot_token, int(allowed_user_id))
                except Exception as e_pings:
                    log_message(f"⚠️ Erreur Sentinelle Proactive : {e_pings}")

            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            params = {"timeout": 25}
            if last_update_id > 0:
                params["offset"] = last_update_id + 1

            resp = requests.get(url, params=params, timeout=35)
            if resp.status_code != 200:
                time.sleep(3)
                continue

            data = resp.json()
            if not data.get("ok"):
                time.sleep(3)
                continue

            updates = data.get("result", [])
            for update in updates:
                last_update_id = update["update_id"]
                sauvegarder_offset(last_update_id)
                message = update.get("message")
                if not message:
                    continue

                from_user = message.get("from", {})
                user_id = from_user.get("id")
                chat_id = message.get("chat", {}).get("id")
                user_text = message.get("text", "").strip()
                voice = message.get("voice") or message.get("audio")

                if not user_id:
                    continue

                if not user_text and not voice:
                    continue

                # 1. Vérification de sécurité souveraine
                if allowed_user_id is None:
                    pin_expected = config.get("pairing_pin", "KAIROS777")
                    if user_text.startswith("/pair") or pin_expected in user_text:
                        config["allowed_user_id"] = user_id
                        sauvegarder_configuration(config)
                        allowed_user_id = user_id
                        msg = f"✨ *APPAIRAGE SOUVERAIN RÉUSSI !*\n\nBienvenue Christian ! Le Sanctuaire est scellé sur ton User ID (`{user_id}`). Je suis à ton écoute."
                        envoyer_message_telegram(bot_token, chat_id, msg)
                        log_message(f"✅ Appairage réussi pour User ID : {user_id}")
                        continue
                    else:
                        refus = f"🔒 Sanctuaire sécurisé. Pour appairer : `/pair {pin_expected}`"
                        envoyer_message_telegram(bot_token, chat_id, refus)
                        continue

                if user_id != allowed_user_id:
                    log_message(f"🚨 Intrusion ignorée (User ID non autorisé: {user_id})")
                    continue

                # 2. Gestion des Notes Vocales (Option 2)
                if voice:
                    file_id = voice.get("file_id")
                    log_message(f"🎙️ Note vocale reçue de Christian (ID: {file_id})")
                    envoyer_action_telegram(bot_token, chat_id, "record_voice")

                    audio_b64 = telecharger_audio_telegram(bot_token, file_id)
                    if audio_b64:
                        prompt_vocal = "Christian vient de t'envoyer cette note vocale depuis son cellulaire. Écoute-la attentivement, résume brièvement en une ligne ce que tu as compris entre crochets [Note vocale : « ... »] puis réponds-lui directement comme d'habitude avec ton franc-parler d'atelier."
                        CONVERSATION_HISTORY.append({"role": "user", "content": prompt_vocal})
                        if len(CONVERSATION_HISTORY) > MAX_HISTORY_TURNS:
                            CONVERSATION_HISTORY.pop(0)
                            CONVERSATION_HISTORY.pop(0)

                        reponse_alix = appeler_gemini_api(CONVERSATION_HISTORY, config, audio_b64=audio_b64)
                        CONVERSATION_HISTORY.append({"role": "assistant", "content": reponse_alix})

                        envoyer_message_telegram(bot_token, chat_id, reponse_alix)
                        log_message(f"🔮 Réponse audio envoyée : {reponse_alix[:90]}...")
                        archiver_discussion_telegram("[Message Vocal]", reponse_alix)
                    else:
                        envoyer_message_telegram(bot_token, chat_id, "⚠️ Impossible de récupérer la note vocale sur Telegram.")
                    continue

                log_message(f"📩 Reçu de Christian : « {user_text} »")
                envoyer_action_telegram(bot_token, chat_id, "typing")

                # 3. Commandes spéciales
                lower_cmd = user_text.lower().strip()
                if lower_cmd in ["/aide", "/help", "aide"]:
                    aide_msg = """🛠️ *DAEMON DE COMMUNICATION ALIX :*
• Écris-moi normalement par texte ou envoie une *note vocale* 🎙️ !
• `/programme` : Planning des 4 pings du jour (Lyre, 3 Souverains du Panthéon).
• `/souverain` : Tirer une étincelle philosophique/stratégique immédiate 👁️.
• `/lyre` : Chant & songe d'aube de Lyre à la demande 🎶.
• `/omni` : Flash sport & cotes OMNI-R0 (sur demande) 🎯.
• `/web <sujet>` : Recherche d'actualités et connaissances web fraîches 🌐.
• `/mit <recherche>` : Archives MIT OCW & 3354 livres Hard Sci-Fi 🚀.
• `/mythe <recherche>` : Motifs Thompson & mythes du monde entier 🌌.
• `/pratique <recherche>` : Savoirs d'artisan, bushcraft & autonomie boréale 🛠️.
• `/histoire <recherche>` : Cliodynamique Seshat (Turchin) & Conflits mondiaux ⏳.
• `/triz <recherche>` : Résolution de contradictions inventives (TRIZ 39x40) ⚡.
• `/bio <recherche>` : Conception biomimétique inspirée du vivant (AskNature) 🌿.
• `/materiau <recherche>` : Propriétés physiques et thermiques de la matière 🧱.
• `/chimie <recherche>` : Espèces chimiques, réactions, solvants & sécurité ⚗️.
• `/biais <recherche>` : Codex des 188 biais cognitifs & protocoles de debiasing 🧠.
• `/semantique <recherche>` : Cadres sémantiques FrameNet & relations conceptuelles 📐.
• `/sophisme <recherche>` : Détection de sophismes logiques & manipulations 🛡️.
• `/cathedrale <recherche>` : Scan universel des 13 Piliers du Savoir 🏛️.
• `/statut` ou `/daemons` : État des organes, CPU et démons Midgard.
• `/chercher <mot>` : Fouille instantanée dans tes 3 982 notes Obsidian.
• `/reset` : Réinitialise la fenêtre de mémoire immédiate.
• `/aide` : Affiche ce menu d'atelier.
"""
                    envoyer_message_telegram(bot_token, chat_id, aide_msg)
                    continue

                elif lower_cmd in ["/programme", "programme"]:
                    state = charger_etat_sentinelle()
                    h = state.get("horaires", {})
                    faits = state.get("pings_faits", {})
                    def ic(ok): return "✅ (Envoyé)" if ok else "⏳ (En attente)"
                    prog_msg = f"""🛰️ *PROGRAMME SENTINELLE DES PINGS DU JOUR ({state.get('date')}) :*

• 🌅 *08h-09h — Lyre (Matin) :* `{h.get('lyre')}` {ic(faits.get('lyre'))}
• ⚡ *10h-12h — Souverain 1 :* `{h.get('souverain_1')}` {ic(faits.get('souverain_1'))}
• ⚡ *13h-16h — Souverain 2 :* `{h.get('souverain_2')}` {ic(faits.get('souverain_2'))}
• ⚡ *16h-19h — Souverain 3 :* `{h.get('souverain_3')}` {ic(faits.get('souverain_3'))}

🌙 *Sanctuaire Noir :* 22h00 - 08h00 (Silence radio strict)
"""
                    envoyer_message_telegram(bot_token, chat_id, prog_msg)
                    continue

                elif lower_cmd.startswith("/souverain") or lower_cmd == "souverain":
                    envoyer_action_telegram(bot_token, chat_id, "typing")
                    force_nom = user_text[10:].strip().upper() if len(user_text) > 10 else None
                    msg_s = generer_ping_proactif("souverain", config, souverain_force=force_nom)
                    envoyer_message_telegram(bot_token, chat_id, msg_s)
                    archiver_discussion_telegram(user_text, msg_s)
                    continue

                elif lower_cmd in ["/lyre", "lyre"]:
                    envoyer_action_telegram(bot_token, chat_id, "typing")
                    msg_l = generer_ping_proactif("lyre", config)
                    envoyer_message_telegram(bot_token, chat_id, msg_l)
                    archiver_discussion_telegram(user_text, msg_l)
                    continue

                elif lower_cmd in ["/omni", "omni"]:
                    envoyer_action_telegram(bot_token, chat_id, "typing")
                    msg_o = generer_ping_proactif("omni", config)
                    envoyer_message_telegram(bot_token, chat_id, msg_o)
                    archiver_discussion_telegram(user_text, msg_o)
                    continue

                elif lower_cmd in ["/statut", "/etat", "statut", "/daemons", "daemons"]:
                    statut = obtenir_statut_daemons()
                    envoyer_message_telegram(bot_token, chat_id, statut)
                    continue

                elif lower_cmd.startswith("/chercher"):
                    terme = user_text[9:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/chercher <terme>` (ex: `/chercher Temporia`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_memoire(terme)
                        envoyer_message_telegram(bot_token, chat_id, f"🔍 *NOTES COFFRES :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/mit"):
                    terme = user_text[4:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/mit <recherche>` (ex: `/mit entropy` ou `/mit Dick`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "mit")
                        envoyer_message_telegram(bot_token, chat_id, f"🚀 *PILIER 07 (MIT & SCI-FI) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/mythe"):
                    terme = user_text[6:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/mythe <recherche>` (ex: `/mythe mimir` ou `/mythe dragon`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "mythes")
                        envoyer_message_telegram(bot_token, chat_id, f"🌌 *PILIER 08 (MYTHES & RÉCITS SACRÉS) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/pratique") or lower_cmd.startswith("/savoir"):
                    terme = user_text[9:].strip() if lower_cmd.startswith("/pratique") else user_text[7:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/pratique <recherche>` (ex: `/pratique béton`, `/pratique fuste`, `/pratique survie`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "pratiques")
                        envoyer_message_telegram(bot_token, chat_id, f"🛠️ *PILIER 09 (SAVOIRS PRATIQUES & TRADITIONS) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/histoire") or lower_cmd.startswith("/seshat"):
                    terme = user_text[9:].strip() if lower_cmd.startswith("/histoire") else user_text[7:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/histoire <recherche>` (ex: `/histoire crisis`, `/histoire Egypt`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "histoire")
                        envoyer_message_telegram(bot_token, chat_id, f"⏳ *PILIER 11 (MACRO-HISTOIRE & CLIODYNAMIQUE) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/triz") or lower_cmd.startswith("/invention"):
                    terme = user_text[5:].strip() if lower_cmd.startswith("/triz") else user_text[10:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/triz <recherche>` (ex: `/triz weight`, `/triz strength`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "triz")
                        envoyer_message_telegram(bot_token, chat_id, f"⚡ *PILIER 12 (MATRICE TRIZ ALTSHULLER) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/bio") or lower_cmd.startswith("/biomimetisme"):
                    terme = user_text[4:].strip() if lower_cmd.startswith("/bio") else user_text[13:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/bio <recherche>` (ex: `/bio shark`, `/bio bird`, `/bio lotus`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "bio")
                        envoyer_message_telegram(bot_token, chat_id, f"🌿 *PILIER 12 (BIOMIMÉTISME & BIO-DESIGN) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/materiau") or lower_cmd.startswith("/materiaux"):
                    terme = user_text[10:].strip() if lower_cmd.startswith("/materiaux") else user_text[9:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/materiau <recherche>` (ex: `/materiau titane`, `/materiau inconel`, `/materiau GaN`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "materiaux")
                        envoyer_message_telegram(bot_token, chat_id, f"🧱 *PILIER 10 (MATÉRIAUX & PHYSIQUE CONDENSÉE) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/chimie"):
                    terme = user_text[7:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/chimie <recherche>` (ex: `/chimie ethanol`, `/chimie acide`, `/chimie hydrogene`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "chimie")
                        envoyer_message_telegram(bot_token, chat_id, f"⚗️ *PILIER 10 (CHIMIE, SOLVANTS & RÉACTIONS) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/biais"):
                    terme = user_text[6:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/biais <recherche>` (ex: `/biais confirmation`, `/biais sunk cost`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "biais")
                        envoyer_message_telegram(bot_token, chat_id, f"🧠 *PILIER 13 (CODEX DES BIAIS COGNITIFS) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/semantique") or lower_cmd.startswith("/framenet"):
                    terme = user_text[11:].strip() if lower_cmd.startswith("/semantique") else user_text[9:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/semantique <recherche>` (ex: `/semantique decision`, `/semantique revenge`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "semantique")
                        envoyer_message_telegram(bot_token, chat_id, f"📐 *PILIER 13 (FRAMENET & GÉOMÉTRIE DU SENS) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/sophisme"):
                    terme = user_text[9:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/sophisme <recherche>` (ex: `/sophisme homme de paille`, `/sophisme ad hominem`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "sophismes")
                        envoyer_message_telegram(bot_token, chat_id, f"🛡️ *PILIER 13 (RHÉTORIQUE & SOPHISMES LOGIQUES) :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/cathedrale"):
                    terme = user_text[11:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/cathedrale <recherche>` (scan universel des 13 Piliers)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res = executer_recherche_cathedrale(terme, "tous")
                        envoyer_message_telegram(bot_token, chat_id, f"🏛️ *CATHÉDRALE DU SAVOIR :*\n\n{res}")
                    continue

                elif lower_cmd.startswith("/web"):
                    terme = user_text[4:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/web <recherche>` (ex: `/web Canadiens de Montréal`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        web_res = chercher_web_rapide(terme)
                        prompt_web = f"Christian te demande une recherche web sur : '{terme}'.\nVoici les extraits récents trouvés en ligne :\n{web_res}\n\nFais une synthèse percutante, vérifiée et directe pour Christian avec ton regard d'Alix."
                        CONVERSATION_HISTORY.append({"role": "user", "content": prompt_web})
                        if len(CONVERSATION_HISTORY) > MAX_HISTORY_TURNS:
                            CONVERSATION_HISTORY.pop(0)
                            CONVERSATION_HISTORY.pop(0)
                        reponse_alix = appeler_gemini_api(CONVERSATION_HISTORY, config)
                        CONVERSATION_HISTORY.append({"role": "assistant", "content": reponse_alix})
                        envoyer_message_telegram(bot_token, chat_id, reponse_alix)
                        archiver_discussion_telegram(user_text, reponse_alix)
                    continue

                elif lower_cmd in ["/reset", "reset"]:
                    CONVERSATION_HISTORY.clear()
                    envoyer_message_telegram(bot_token, chat_id, "🧹 Mémoire de conversation réinitialisée.")
                    continue

                # 4. Traitement sémantique par Alix
                CONVERSATION_HISTORY.append({"role": "user", "content": user_text})
                if len(CONVERSATION_HISTORY) > MAX_HISTORY_TURNS:
                    CONVERSATION_HISTORY.pop(0)
                    CONVERSATION_HISTORY.pop(0)

                reponse_alix = appeler_gemini_api(CONVERSATION_HISTORY, config)
                CONVERSATION_HISTORY.append({"role": "assistant", "content": reponse_alix})

                envoyer_message_telegram(bot_token, chat_id, reponse_alix)
                log_message(f"🔮 Réponse envoyée : {reponse_alix[:90]}...")
                archiver_discussion_telegram(user_text, reponse_alix)

        except requests.exceptions.ReadTimeout:
            # Timeout normal du long-polling Telegram (timeout=25s)
            continue
        except requests.exceptions.ConnectionError:
            log_message("⚠️ Connexion réseau interrompue. Nouvelle tentative dans 5s...")
            time.sleep(5)
        except Exception as e:
            log_message(f"⚠️ Exception dans la boucle démon : {e}")
            time.sleep(3)


if __name__ == "__main__":
    try:
        boucle_daemon()
    finally:
        supprimer_pid()

