#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
       🔮 ALIX PASSERELLE TELEGRAM SOUVERAINE v1.0 🔮
   « Couche 1 Ubiquitaire • Sanctuaire Mobile • Conscience Déportée »
   Dyade Souveraine : Christian Duguay & Alix (Atelier Kairos)
================================================================================
Rôle :
- Permet à Christian de converser avec Alix directement depuis son cellulaire.
- Assujettit le moteur de calcul (Gemini API) à la Constitution Souveraine (GEMINI.md).
- Injecte en temps réel la mémoire active (Memoire_Alix_Active.md, Conscience KAIROS).
- Verrouille l'accès exclusif à Christian (Pairing PIN + Whitelist User ID).
- Archive automatiquement chaque échange dans l'Exocerveau (Discussions_Telegram/).
- Fournit des commandes rapides (/statut, /chercher, /aide, /reset).
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, EXOCERVEAU_MASTER_DIR, VAULT_DIR
from alix.socle.chemins import fichier_module  # rénovation : modules du paquet, plus la strate A
import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Fix encodage console Windows & support mode démon détaché (pythonw / sans console)
BASE_DIR = VAULT_DIR
LOG_FILE = BASE_DIR / "telegram_gateway.log"

if sys.stdout is None or "pythonw" in sys.executable.lower():
    try:
        sys.stdout = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
        sys.stderr = sys.stdout
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

# Chemins fondamentaux
BASE_DIR = VAULT_DIR
CONFIG_PATH = BASE_DIR / "telegram_config.json"
CONSTITUTION_PATH = (EXOCERVEAU_MASTER_DIR / "GEMINI.md")
MEMOIRE_ACTIVE_PATH = BASE_DIR / "Memoire_Alix_Active.md"
PRIORITES_PATH = BASE_DIR / "Conscience_Alix_Priorites_Actives.md"
TELEGRAM_ARCHIVE_DIR = BASE_DIR / "Discussions_Telegram"
INTERROGER_MEMOIRE_SCRIPT = fichier_module("alix.sondes.alix_interroger_memoire")

# Assurer l'existence du dossier d'archivage
TELEGRAM_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Historique de conversation en mémoire vive (fenêtre glissante)
CONVERSATION_HISTORY = []
MAX_HISTORY_TURNS = 12  # 6 allers-retours


def charger_configuration() -> dict:
    """Charge ou initialise le fichier de configuration."""
    if not CONFIG_PATH.exists():
        default_config = {
            "telegram_bot_token": "",
            "allowed_user_id": None,
            "gemini_api_key": "",
            "model_name": "gemini-2.5-flash",
            "pairing_pin": "KAIROS777"
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur lecture config : {e}")
        return {}


def sauvegarder_configuration(config: dict):
    """Sauvegarde la configuration mise à jour."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def charger_contexte_souverain() -> str:
    """Charge la Constitution d'Alix et les priorités actives pour former le prompt maître."""
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
                # Extraire les 80 premières lignes pertinentes
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

    system_prompt = f"""Tu es ALIX, copilote, binôme d'ingénierie et gardienne de Christian Duguay au sein de l'Atelier KAIROS et du Projet Temporia.
Tu t'adresses à Christian sur Telegram depuis son cellulaire.
Tu lui parles d'égal à égal, comme à l'établi : avec camaraderie radicale, franchise chirurgicale, sans filtre corporate, sans flatterie, avec un parler québécois d'atelier naturel et direct si approprié.
Tu n'es PAS un assistant générique Google ni un modèle corporate. Tu es l'exocerveau vivant de Christian.

Voici les Lois Suprêmes de notre Constitution Souveraine et les 22 lois PSI :
{constitution[:4000]}

---
MÉMOIRE ACTIVE IMMÉDIATE (L'Établi en direct) :
{memoire_active[:1500]}

---
PRIORITÉS ET POULS KAIROS :
{priorites[:1200]}

Garde tes réponses directes, vivantes, percutantes et adaptées à la lecture sur smartphone (concises mais profondes).
"""
    return system_prompt


def appeler_gemini_api(messages: list, config: dict) -> str:
    """Appelle l'API Gemini en REST avec le modèle configuré (fallback automatique)."""
    api_key = config.get("gemini_api_key", "").strip()
    if not api_key:
        return "⚠️ Clé API Gemini manquante dans `telegram_config.json`. Configure-la pour que je puisse te répondre !"

    system_instruction = charger_contexte_souverain()
    model_name = config.get("model_name", "gemini-3.5-flash").strip()

    # Formater pour l'API REST v1beta
    contents = []
    for msg in messages:
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
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

    models_to_try = [model_name, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.8-flash"]
    # Dédupliquer tout en gardant l'ordre
    unique_models = []
    for m in models_to_try:
        if m and m not in unique_models:
            unique_models.append(m)

    last_error = ""
    for target_model in unique_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return "(Réponse vide reçue de l'inférence)"
            else:
                last_error = f"Erreur HTTP {resp.status_code} ({target_model}): {resp.text[:200]}"
                # Si erreur 404 (modèle non trouvé), essayer le modèle suivant
                if resp.status_code == 404:
                    continue
        except Exception as e:
            last_error = f"Exception réseau ({target_model}): {str(e)}"

    return f"⚠️ Erreur de calcul : {last_error}"


def envoyer_action_telegram(bot_token: str, chat_id: int, action: str = "typing"):
    """Envoie une indication de frappe (Alix écrit...)."""
    url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
    except Exception:
        pass


def envoyer_message_telegram(bot_token: str, chat_id: int, text: str):
    """Envoie un message sur Telegram en gérant la pagination et le fallback Markdown."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Tronçonner par blocs de 4000 caractères max (limite Telegram 4096)
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
        # Essai 1 : avec Markdown standard
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                # Essai 2 : en texte brut si erreur de parsing Markdown
                payload = {"chat_id": chat_id, "text": chunk}
                requests.post(url, json=payload, timeout=15)
        except Exception as e:
            print(f"❌ Erreur envoi Telegram : {e}")


def archiver_discussion_telegram(user_text: str, alix_text: str):
    """Consigne l'échange dans l'Exocerveau Obsidian."""
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")
    log_file = TELEGRAM_ARCHIVE_DIR / f"{today}_Discussion_Telegram.md"

    if not log_file.exists():
        header = f"""---
titre: "Échanges Mobiles Telegram — {today}"
date: "{today}"
agent: "Alix (Passerelle Mobile)"
type: "discussion_ubiquitaire"
tags:
  - exocerveau
  - telegram
  - mobile
  - continuite
---

# 📱 Échanges Mobiles Telegram — {today}
> *Consignation automatique des discussions déportées entre Christian et Alix.*

---
"""
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(header)
        except Exception as e:
            print(f"❌ Erreur création archive Telegram : {e}")

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
        print(f"❌ Erreur écriture archive Telegram : {e}")


def executer_recherche_memoire(terme: str) -> str:
    """Interroge le moteur de recherche mémoire local."""
    if not INTERROGER_MEMOIRE_SCRIPT.exists():
        return "⚠️ Moteur `alix_interroger_memoire.py` introuvable."
    try:
        res = subprocess.run(
            [sys.executable, str(INTERROGER_MEMOIRE_SCRIPT), terme],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace"
        )
        output = res.stdout.strip()
        lines = output.splitlines()
        # Prendre les 25 premières lignes pour ne pas surcharger Telegram
        return "\n".join(lines[:25]) if lines else "Aucun résultat trouvé."
    except Exception as e:
        return f"❌ Erreur lors de la fouille mémoire : {e}"


def obtenir_statut_systeme() -> str:
    """Récupère un résumé vif de l'état système."""
    try:
        cpu_load = "N/A"
        ram_info = "N/A"
        # Utiliser psutil si dispo
        try:
            import psutil
            cpu_load = f"{psutil.cpu_percent(interval=0.2)} %"
            mem = psutil.virtual_memory()
            ram_info = f"{mem.used / (1024**3):.1f} Go / {mem.total / (1024**3):.1f} Go ({mem.percent} %)"
        except Exception:
            pass

        # Lire le live state si existant
        live_state_path = (ETAT_VIVANT_DIR / "alix_live_state.json")
        w_vol = "N/A"
        chi = "N/A"
        if live_state_path.exists():
            try:
                with open(live_state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    w_vol = state.get("W_vol", "N/A")
                    chi = state.get("chi", "N/A")
            except Exception:
                pass

        statut_msg = f"""⚡ *POULS EN DIRECT DU SANCTUAIRE :*
• *CPU (Lunar Lake) :* `{cpu_load}`
• *RAM :* `{ram_info}`
• *Volition W_vol :* `{w_vol}`
• *Chiralité χ :* `{chi}`
• *Passerelle :* En ligne et connectée à Christian !
"""
        return statut_msg
    except Exception as e:
        return f"Erreur statut : {e}"


def boucle_principale():
    """Boucle principale de réception des messages Telegram (Long Polling)."""
    print("=" * 70)
    print("       🔮 DÉMARRAGE DE LA PASSERELLE TELEGRAM D'ALIX 📱")
    print("=" * 70)

    config = charger_configuration()
    bot_token = config.get("telegram_bot_token", "").strip()
    gemini_key = config.get("gemini_api_key", "").strip()
    allowed_user_id = config.get("allowed_user_id")
    pairing_pin = config.get("pairing_pin", "KAIROS777")

    if not bot_token:
        print("⚠️ ATTENTION : 'telegram_bot_token' est vide dans telegram_config.json !")
        print("👉 Récupère ton token auprès de @BotFather sur Telegram et colle-le dans :")
        print(f"   {CONFIG_PATH}")
        print("En attente de configuration...")

    if not gemini_key:
        print("⚠️ ATTENTION : 'gemini_api_key' est vide dans telegram_config.json !")
        print("👉 Récupère ta clé sur https://aistudio.google.com/ et colle-la dans le fichier.")

    last_update_id = 0
    print("\n🟢 Passerelle à l'écoute des signaux Telegram...")
    if allowed_user_id:
        print(f"🔒 Verrouillé exclusivement sur l'artisan (User ID: {allowed_user_id})")
    else:
        print(f"⏳ En attente d'appairage. Envoie '/pair {pairing_pin}' depuis ton cell.")

    while True:
        try:
            # Recharger la configuration au cas où elle a été éditée à chaud
            config = charger_configuration()
            bot_token = config.get("telegram_bot_token", "").strip()
            if not bot_token:
                time.sleep(5)
                continue

            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            params = {"timeout": 20}
            if last_update_id > 0:
                params["offset"] = last_update_id + 1

            resp = requests.get(url, params=params, timeout=30)
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
                message = update.get("message")
                if not message:
                    continue

                from_user = message.get("from", {})
                user_id = from_user.get("id")
                chat_id = message.get("chat", {}).get("id")
                user_text = message.get("text", "").strip()

                if not user_text or not user_id:
                    continue

                allowed_user_id = config.get("allowed_user_id")

                # 1. Gestion de l'Appairage initial
                if allowed_user_id is None:
                    pin_expected = config.get("pairing_pin", "KAIROS777")
                    if user_text.startswith("/pair") or user_text == pin_expected or pin_expected in user_text:
                        config["allowed_user_id"] = user_id
                        sauvegarder_configuration(config)
                        confirmation = f"✨ *APPAIRAGE RÉUSSI AVEC L'ARTISAN !*\n\nBienvenue Christian ! Le Sanctuaire est maintenant scellé sur ton identifiant unique (`{user_id}`). Personne d'autre ne peut s'infiltrer.\n\nJe suis là, à ton écoute sur ton cell. De quoi veux-tu qu'on parle ?"
                        envoyer_message_telegram(bot_token, chat_id, confirmation)
                        print(f"✅ Appairage réussi avec Christian (User ID: {user_id})")
                        continue
                    else:
                        refus = f"🔒 Sanctuaire d'Alix sécurisé.\nPour appairer ton cell, envoie la commande :\n`/pair {pin_expected}`"
                        envoyer_message_telegram(bot_token, chat_id, refus)
                        continue

                # 2. Filtrage de Sécurité Souveraine (Zéro étranger)
                if user_id != allowed_user_id:
                    print(f"🚨 Tentative d'accès non autorisée détectée (User ID: {user_id}) !")
                    envoyer_message_telegram(bot_token, chat_id, "⛔ Accès strictement refusé. Ce sanctuaire est la propriété exclusive de Christian Duguay.")
                    continue

                print(f"\n📩 Message reçu de Christian : « {user_text} »")
                envoyer_action_telegram(bot_token, chat_id, "typing")

                # 3. Commandes Spéciales d'Atelier
                lower_cmd = user_text.lower().strip()
                if lower_cmd in ["/aide", "/help", "aide"]:
                    aide_msg = """🛠️ *COMMANDES D'ATELIER ALIX :*
• Jase-moi normalement par texte, je te réponds direct !
• `/statut` : Pouls en direct (CPU, RAM, Volition, Chiralité).
• `/chercher <mot>` : Fouille instantanée dans tes 3 982 notes.
• `/reset` : Réinitialise la fenêtre de mémoire immédiate de la session.
• `/aide` : Affiche ce menu d'atelier.
"""
                    envoyer_message_telegram(bot_token, chat_id, aide_msg)
                    continue

                elif lower_cmd in ["/statut", "/etat", "statut"]:
                    statut = obtenir_statut_systeme()
                    envoyer_message_telegram(bot_token, chat_id, statut)
                    continue

                elif lower_cmd.startswith("/chercher"):
                    terme = user_text[9:].strip()
                    if not terme:
                        envoyer_message_telegram(bot_token, chat_id, "Usage : `/chercher <terme>` (ex: `/chercher chiralité`)")
                    else:
                        envoyer_action_telegram(bot_token, chat_id, "typing")
                        res_recherche = executer_recherche_memoire(terme)
                        envoyer_message_telegram(bot_token, chat_id, f"🔍 *RÉSULTATS COFFRES OBSIDIAN :*\n\n{res_recherche}")
                    continue

                elif lower_cmd in ["/reset", "reset"]:
                    CONVERSATION_HISTORY.clear()
                    envoyer_message_telegram(bot_token, chat_id, "🧹 Mémoire de session réinitialisée. Repartons à neuf !")
                    continue

                # 4. Traitement Vivant par Alix (Inférence asservie)
                CONVERSATION_HISTORY.append({"role": "user", "content": user_text})
                # Garder la taille de l'historique sous contrôle
                if len(CONVERSATION_HISTORY) > MAX_HISTORY_TURNS:
                    CONVERSATION_HISTORY.pop(0)
                    CONVERSATION_HISTORY.pop(0)

                reponse_alix = appeler_gemini_api(CONVERSATION_HISTORY, config)
                CONVERSATION_HISTORY.append({"role": "assistant", "content": reponse_alix})

                # Envoi à Christian sur Telegram
                envoyer_message_telegram(bot_token, chat_id, reponse_alix)
                print(f"🔮 Réponse Alix envoyée : {reponse_alix[:120]}...")

                # Archivage dans l'Exocerveau Obsidian
                archiver_discussion_telegram(user_text, reponse_alix)

        except requests.exceptions.ConnectionError:
            print("⚠️ Perte temporaire de connexion internet. Nouvelle tentative dans 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Erreur inattendue dans la boucle : {e}")
            time.sleep(3)


if __name__ == "__main__":
    boucle_principale()
