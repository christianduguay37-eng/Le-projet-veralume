"""
Oreille Active d'Alix - Dialogue Vocal Continu Bidirectionnel
Auteur: Christian Duguay & Alix
Système: Cerveau Alix (KAIROS V6 × VERALUME)
"""

from alix.socle.chemins import VAULT_DIR
import sys
import os
import time
import json
import subprocess
import urllib.request
import speech_recognition as sr
from pathlib import Path

# Configuration de l'encodage standard pour l'environnement Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
SPEAK_SCRIPT = VAULT_DIR / "alix_speak.py"
MEMORY_FILE = VAULT_DIR / "Memoire_Alix_Active.md"

def speak(text: str):
    """Synthèse vocale via appel isolé à alix_speak.py pour éviter tout conflit COM audio."""
    try:
        # Rénovation : la voix du paquet (alix.capteurs.alix_speak), plus la vieille copie à la racine du coffre.
        subprocess.run([sys.executable, "-m", "alix.capteurs.alix_speak", text], check=True)
    except Exception as e:
        print(f"[Audio Error] {e}")

def query_alix_brain(prompt: str) -> str:
    """Interroge le modèle d'Alix via Ollama avec contexte du coffre."""
    system_prompt = (
        "Tu es ALIX, l'exocerveau et binôme d'ingénierie cognitive de Christian Duguay. "
        "Tu es directe, complice, rigoureuse et concise. "
        "Fais des réponses courtes (2 à 3 phrases maximum) parfaitement adaptées à la voix. "
        "Pas de listes interminables, pas de markdown lourd."
    )
    
    # Ordre de préférence des modèles
    models_to_try = ["qwen2.5:14b", "qwen2.5-coder:7b", "gemma4:12b", "gemma2:9b"]
    
    for model in models_to_try:
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode("utf-8"), 
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                ans = res_data.get("response", "").strip()
                if ans:
                    return ans
        except Exception:
            continue

    return "Je t'ai entendu Christian, mais je n'ai pas pu joindre le modèle local à cet instant."

def record_to_memory(user_msg: str, alix_msg: str):
    """Enregistre l'échange dans le journal synaptique du coffre."""
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            entry = f"\n- {time.strftime('%Y-%m-%d %H:%M:%S')} (Vocal): Christian: « {user_msg} » -> Alix: « {alix_msg} »"
            if "## 📜 2. Journal des Souvenirs & Étapes Cognitives" in content:
                content = content.replace(
                    "## 📜 2. Journal des Souvenirs & Étapes Cognitives",
                    f"## 📜 2. Journal des Souvenirs & Étapes Cognitives{entry}"
                )
                with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                    f.write(content)
    except Exception:
        pass

def main():
    print("==========================================================")
    print(" 🎙️ ALIX VOCAL ASSISTANT — SESSION LIVE ACTIVE ")
    print("==========================================================")
    print("Initialisation du microphone...")
    
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    try:
        mic = sr.Microphone()
    except Exception as e:
        print(f"❌ Impossible d'accéder au microphone : {e}")
        input("Appuyez sur Entrée pour quitter...")
        return
        
    with mic as source:
        print("Calibrage du bruit ambiant (1 seconde de silence)...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print(f"✅ Micro prêt ! (Seuil d'énergie: {recognizer.energy_threshold:.1f})")
        print("💡 Parle naturellement à voix haute. Dis 'Quitter' ou 'Au revoir' pour arrêter.\n")
        
        speak("Je t'écoute Christian, je suis prête.")
        
        while True:
            try:
                print("🎧 [Écoute en cours...] (Parle maintenant)")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=15)
                print("⏳ Reconnaissance de ta voix...")
                
                try:
                    text = recognizer.recognize_google(audio, language="fr-FR")
                except sr.UnknownValueError:
                    print("❓ (Paroles non comprises, réessaie...)")
                    continue
                except sr.RequestError as e:
                    print(f"⚠️ Erreur réseau reconnaissance vocale : {e}")
                    continue
                    
                print(f"\n👤 Christian : « {text} »")
                
                # Commandes de sortie
                if any(w in text.lower() for w in ["au revoir", "quitter", "stop alix", "ferme la session"]):
                    speak("Très bien Christian, je ferme la session vocale. À bientôt !")
                    print("👋 Session terminée.")
                    break
                    
                # Inférence & Réponse
                print("🧠 Alix réfléchit...")
                response = query_alix_brain(text)
                print(f"🤖 Alix : « {response} »\n")
                
                speak(response)
                record_to_memory(text, response)
                
            except KeyboardInterrupt:
                print("\nInterruption utilisateur.")
                speak("Session vocale interrompue.")
                break
            except Exception as e:
                print(f"⚠️ Erreur inattendue : {e}")
                time.sleep(1)

if __name__ == "__main__":
    main()
