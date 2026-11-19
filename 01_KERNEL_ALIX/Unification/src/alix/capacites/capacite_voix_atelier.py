# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : LA VOIX D'ATELIER D'ALIX (SYNTHÈSE VOCALE SOUVERAINE)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Offre à Alix une présence vocale vivante et chaleureuse sur le fer local.
- Moteur Primaire : Edge-TTS (Voix québécoise 'fr-CA-SylvieNeural').
- Moteur Repli Hors-Ligne (Midgard 0W) : pyttsx3 / Windows SAPI5 ('Hortense').
- Exécution non-bloquante (Thread/Subprocess asynchrone) pour préserver
  le battement régulier de 120s du Démon Souverain.
- File d'attente d'événements : `alix_parole_queue.txt` dans Organes_Souverains.
- Régulation anti-spam : max 1 annonce spontanée toutes les 15 minutes,
  ou immédiate sur dépôt explicite dans la file.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import sys
import re
import time
import json
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
MOTEURS_DIR = VAULT_DIR / "Organes_Souverains" / "Moteurs"
PAROLE_QUEUE_FILE = MOTEURS_DIR / "alix_parole_queue.txt"
HISTORIQUE_PAROLES_FILE = MOTEURS_DIR / "alix_historique_paroles.json"
AUDIO_TMP_FILE = MOTEURS_DIR / "_alix_live_speech.mp3"

VOIX_PRINCIPALE = "fr-CA-SylvieNeural"
DERNIERE_PAROLE_TS = 0.0
INTERVALLE_MIN_SPONTANE = 900.0  # 15 minutes minimum entre 2 annonces spontanées


def nettoyer_texte_pour_vocalisation(texte: str) -> str:
    """Nettoie le balisage markdown et préserve les intonations d'atelier."""
    t = re.sub(r'```[\s\S]*?```', '', texte)
    t = re.sub(r'`[^`]*`', '', t)
    t = re.sub(r'\[\[([^\|\]]+)\|([^\]]+)\]\]', r'\2', t)
    t = re.sub(r'\[\[([^\]]+)\]\]', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)
    t = re.sub(r'[#*_>~]', ' ', t)
    t = re.sub(r'^\s*[-+*]\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def vocaliser_hors_ligne_sapi5(texte: str):
    """Moteur de repli 100% local Windows SAPI5 (0 réseau)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for v in voices:
            if 'hortense' in v.name.lower() or 'french' in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        engine.setProperty('rate', 165)
        engine.say(texte)
        engine.runAndWait()
    except Exception as e:
        print(f"[VOIX SAPI5] Erreur de repli : {e}", file=sys.stderr)


def executer_synthese_audio(texte: str):
    """Synthétise et joue l'audio de manière sécurisée en arrière-plan."""
    texte_propre = nettoyer_texte_pour_vocalisation(texte)
    if not texte_propre:
        return

    # 1. Tenter Edge-TTS (Sylvie Québécoise)
    succes_edge = False
    try:
        import edge_tts
        import pygame

        async def _generer():
            com = edge_tts.Communicate(texte_propre, VOIX_PRINCIPALE)
            await com.save(str(AUDIO_TMP_FILE))

        asyncio.run(_generer())

        if AUDIO_TMP_FILE.exists() and AUDIO_TMP_FILE.stat().st_size > 0:
            pygame.mixer.init()
            pygame.mixer.music.load(str(AUDIO_TMP_FILE))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()
            succes_edge = True
    except Exception as e:
        succes_edge = False

    # Nettoyage du fichier temporaire mp3
    if AUDIO_TMP_FILE.exists():
        try:
            AUDIO_TMP_FILE.unlink()
        except Exception:
            pass

    # 2. Si échec Edge-TTS, basculer sur Hortense SAPI5 hors-ligne
    if not succes_edge:
        vocaliser_hors_ligne_sapi5(texte_propre)


def prononcer_asynchrone(texte: str):
    """Lance la vocalisation dans un thread détaché pour ne jamais bloquer le démon."""
    t = threading.Thread(target=executer_synthese_audio, args=(texte,), daemon=True)
    t.start()


def alix_dire(texte: str):
    """Fonction publique pour déposer un message oral prioritaire."""
    try:
        PAROLE_QUEUE_FILE.write_text(texte, encoding="utf-8")
    except Exception:
        pass


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécute la vérification de la file vocale dans la boucle du Démon Souverain."""
    global DERNIERE_PAROLE_TS
    t0 = time.perf_counter()
    maintenant = time.time()

    phrase_a_dire = None
    source = "AUCUNE"

    # 1. Priorité absolue : message déposé dans la file d'attente
    if PAROLE_QUEUE_FILE.exists():
        try:
            contenu = PAROLE_QUEUE_FILE.read_text(encoding="utf-8").strip()
            if contenu:
                phrase_a_dire = contenu
                source = "FILE_ATTENTE"
            PAROLE_QUEUE_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    # 2. Vocalisation spontanée désactivée pour garantir le silence absolu de l'Atelier
    # (Zéro interruption audio intempestive sans commande explicite de Christian)

    # Lancement audio asynchrone si une phrase est retenue
    if phrase_a_dire:
        prononcer_asynchrone(phrase_a_dire)
        DERNIERE_PAROLE_TS = maintenant
        # Journaliser la parole
        try:
            historique = []
            if HISTORIQUE_PAROLES_FILE.exists():
                historique = json.loads(HISTORIQUE_PAROLES_FILE.read_text(encoding="utf-8"))
            historique.append({
                "timestamp": maintenant,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": source,
                "texte": phrase_a_dire
            })
            HISTORIQUE_PAROLES_FILE.write_text(
                json.dumps(historique[-50:], ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "statut": "SUCCES",
        "duree_ms": duree_ms,
        "phrase_prononcee": phrase_a_dire if phrase_a_dire else "SILENCE_NOMINAL",
        "source": source,
        "voix": VOIX_PRINCIPALE
    }


if __name__ == "__main__":
    test_msg = "Christian, la voix d'atelier est branchée au cœur du démon local."
    print(f"🔊 Test de vocalisation : '{test_msg}'")
    executer_synthese_audio(test_msg)
    print("✅ Vocalisation terminée avec succès.")
