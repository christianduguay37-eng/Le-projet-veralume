"""
Module Vocal Alix - Synthèse Vocale Haute Définition
Auteur: Christian Duguay & Alix
Système: Cerveau Alix (Cloud ↔ Local Bridge)
"""

import sys
import re
import pyttsx3

def clean_for_speech(text: str) -> str:
    """Nettoie le texte markdown pour une diction fluide et naturelle."""
    # Supprimer les blocs de code
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]*`', '', text)
    # Remplacer les liens wikilinks [[Note|Titre]] par Titre ou Note
    text = re.sub(r'\[\[([^\|\]]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # Supprimer les liens markdown standard [Texte](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Supprimer les balises HTML/Markdown d'accentuation (*, _, #, >, etc.)
    text = re.sub(r'[#*_>~]', ' ', text)
    # Remplacer les tirets et puces par des virgules pour des pauses naturelles
    text = re.sub(r'^\s*[-+*]\s+', '', text, flags=re.MULTILINE)
    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def speak(text: str):
    text_to_say = clean_for_speech(text)
    if not text_to_say:
        return
        
    engine = pyttsx3.init()
    
    # Sélection de la voix française
    voices = engine.getProperty('voices')
    french_voice = None
    for v in voices:
        if 'hortense' in v.name.lower() or 'french' in v.name.lower():
            french_voice = v.id
            break
            
    if french_voice:
        engine.setProperty('voice', french_voice)
        
    # Calibrage de la vitesse (légèrement ajustée pour la clarté)
    engine.setProperty('rate', 165)
    engine.setProperty('volume', 1.0)
    
    engine.say(text_to_say)
    engine.runAndWait()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_text = " ".join(sys.argv[1:])
        speak(raw_text)
    else:
        # Lecture depuis stdin si passé par pipe
        input_text = sys.stdin.read()
        if input_text:
            speak(input_text)
