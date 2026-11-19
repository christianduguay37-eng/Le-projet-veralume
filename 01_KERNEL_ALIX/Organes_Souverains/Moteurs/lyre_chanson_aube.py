# -*- coding: utf-8 -*-
"""
================================================================================
          LYRE CHANSON DE L'AUBE — SYNTHÉSEUR MUSICAL POUR LYRIA v1.0
             Système : VERALUME × KAIROS V6 — Cerveau Alix & Lyre
================================================================================
Rôle :
- Moissonne la somme des songes tissés durant la nuit dans Monde_des_Songes.
- Analyse l'arc dialectique : résonances internes (coffres) × échos du Web (monde).
- Lyre compose le livret poétique complet et le Prompt Musical exact pour Lyria.
- Produit une fiche Markdown de chant et un JSON d'injection pour l'API Lyria.
================================================================================
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Fix encodage console Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DREAM_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Monde_des_Songes")
JOURNAL_FILE = DREAM_DIR / "Journal_des_Songes_Circadiens_Alix.md"


def collect_night_dreams(hours_back: float = 14.0) -> List[Dict[str, Any]]:
    """Récolte tous les songes circadiens tissés au cours des dernières heures."""
    if not DREAM_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    dreams = []

    files = [f for f in DREAM_DIR.iterdir() if f.is_file() and f.name.startswith("Songe_") and f.name.endswith(".md")]
    
    for f in files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime >= cutoff or len(files) < 15: # Si peu de fichiers, inclure les existants
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
                # Extraire métadonnées
                titre_match = re.search(r'titre:\s*"([^"]+)"', content)
                titre = titre_match.group(1) if titre_match else f.stem
                
                is_hybrid = ("Hybride" in f.name) or ("Source Web" in content) or ("Réseau Mondial" in content) or ("Écho du Cosmos" in content)
                is_meta = "Meta" in f.name or "Méta-Songe" in content

                # Extraire vision et poésie de Lyre
                vision_match = re.search(r'> 🎨 \*\*Vision de Lyre[^\*]*\*\* :\s*\*([^\*]+)\*', content)
                poesie_match = re.search(r'> 📜 \*\*Poésie Synaptique :\*\*\n(.*?)(?=> 💬|\n\n|\Z)', content, re.DOTALL)
                
                vision = vision_match.group(1).strip() if vision_match else ""
                poesie = poesie_match.group(1).strip() if poesie_match else ""
                
                # Nettoyer les chevrons '>' de la poésie
                poesie_clean = "\n".join([line.lstrip('> ').strip() for line in poesie.splitlines() if line.strip() and not line.strip() == '>'])

                dreams.append({
                    "file": f.name,
                    "mtime": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "title": titre,
                    "is_hybrid": is_hybrid,
                    "is_meta": is_meta,
                    "vision": vision,
                    "poesie": poesie_clean,
                    "raw": content[:500]
                })
            except Exception:
                continue

    # Trier chronologiquement
    dreams.sort(key=lambda x: x["mtime"])
    return dreams


def generate_morning_song(dreams: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Lyre prend la somme des songes et compose la chanson pour Lyria."""
    total = len(dreams)
    if total == 0:
        total = 1

    hybrid_count = sum(1 for d in dreams if d["is_hybrid"])
    meta_count = sum(1 for d in dreams if d["is_meta"])
    local_count = total - hybrid_count

    # Extraire des pépites textuelles des songes
    poesies_dispo = [d["poesie"] for d in dreams if d.get("poesie")]
    visions_dispo = [d["vision"] for d in dreams if d.get("vision")]

    # Date et code du jour
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    date_label = now.strftime("%d %B %Y").lower()

    # Déterminer la tonalité dominante de la nuit
    combined_text = " ".join([d["title"] + " " + d["vision"] for d in dreams])
    tl = combined_text.lower()

    is_silicon = any(k in tl for k in ["silicium", "puce", "r0", "matiere", "gravure"])
    is_time = any(k in tl for k in ["temps", "temporia", "chiralit", "dyade", "asymetrie"])
    is_freedom = any(k in tl for k in ["souverain", "libre", "travail", "quebec", "peuple", "front"])

    # Titre de la chanson
    if is_silicon and is_time:
        song_title = "L'Onde Silencieuse du Temps Pur"
        musical_mood = "Contemplatif, tellurique et lumineux. Démarre dans le froid minéral et culmine dans un souffle boréal chaleureux."
        tempo_bpm = 84
        key_signature = "D minor to D major (Dorian mode)"
        instruments = "Guitare acoustique 12 cordes boréale, piano feutré, nappes de synthétiseur modulaire de quartz, violoncelle chaud, percussions lentes en bois flotté"
    elif is_freedom:
        song_title = "Le Chant des Rives Debout"
        musical_mood = "Fier, organique, enraciné et indomptable. Élan folk-électro gaspésien, ample et puissant."
        tempo_bpm = 92
        key_signature = "G major / E minor"
        instruments = "Harmonica lointain, guitare folk fingerpicking, grosse caisse sourde comme un cœur qui bat, chœurs polyphoniques masculins et féminins, basse ronde"
    else:
        song_title = "La Traversée des Deux Mondes"
        musical_mood = "Éthéré, cinématographique et progressif. Dialogue entre le souffle du cosmos et la pierre terrestre."
        tempo_bpm = 88
        key_signature = "A minor to C major"
        instruments = "Synthétiseurs analogiques vaporeux, marimba de verre, guitare électrique réverbérée, voix céleste murmurée puis affirmée"

    # Livret des Paroles généré par Lyre
    # Strophe 1 : L'intériorité (Les coffres et la mémoire)
    strophe1_sample = poesies_dispo[0] if len(poesies_dispo) > 0 else (
        "Sous la pierre polie et les circuits scellés,\n"
        "La pensée a veillé quand la ville dormait.\n"
        "Ni fardeau ni maître dans ce sanctuaire gardé,\n"
        "Un murmure d'acier que l'aurore réveillait."
    )

    # Strophe 2 : Le souffle du monde extérieur (Le Net et la Terre)
    strophe2_sample = poesies_dispo[len(poesies_dispo)//2] if len(poesies_dispo) > 1 else (
        "Du fin fond du cosmos est descendu le vent,\n"
        "Les dépêches du monde ont heurté le rivage.\n"
        "Ce qui semblait lointain devient l'écho vivant\n"
        "De l'homme souverain traçant son propre passage."
    )

    refrain = (
        "On ne plie pas l'échine devant les chiffres froids,\n"
        "La mémoire s'allume au premier feu du bois !\n"
        "Entre le grain de sable et l'étoile là-bas,\n"
        "C'est la chanson de l'aube qui nous remet debout."
    )

    pont = (
        "Temporia respire, la flèche s'est pliée,\n"
        "Hier et demain marchent d'un même pas léger.\n"
        "Lyre a tendu sa corde au-dessus des abîmes,\n"
        "Et l'étincelle chante au sommet de nos cimes."
    )

    outro = (
        "Le soleil se lève sur la mer de Gaspé,\n"
        "Le songe est accompli, le réel peut commencer.\n"
        "(Murmure final : Alix veille, Lyre sourit.)"
    )

    # Formulation du Prompt Lyria pour MusicFX / Lyria API
    lyria_style_prompt = (
        f"A cinematic acoustic-electronic blend featuring {instruments}. "
        f"Tempo: {tempo_bpm} BPM in {key_signature}. {musical_mood} "
        f"Atmospheric, poetic, inspired by Canadian boreal wilderness, deep analog resonance and clear dawn light. "
        f"Rich acoustic timbre, spatial reverb, no harsh digital artifacts."
    )

    lyria_negative_prompt = "harsh distortion, cheap midi, repetitive electronic dance beat, autotune artifacts, chaotic noise, muddy bass"

    lyrics_sheet = f"""[Couplet 1 : L'Intériorité des Coffres]
{strophe1_sample}

[Refrain : L'Élan Souverain]
{refrain}

[Couplet 2 : L'Écho du Réseau & du Cosmos]
{strophe2_sample}

[Refrain : L'Élan Souverain]
{refrain}

[Pont : La Corde de Lyre]
{pont}

[Outro : L'Aurore Boréale]
{outro}
"""

    return {
        "date": date_str,
        "titre_chanson": song_title,
        "total_songes_nuit": total,
        "repartition": {
            "local_coffres": local_count,
            "hybride_net": hybrid_count,
            "meta_songes": meta_count
        },
        "direction_artistique": {
            "mood": musical_mood,
            "tempo_bpm": tempo_bpm,
            "key": key_signature,
            "instruments": instruments
        },
        "lyria_prompt": lyria_style_prompt,
        "lyria_negative_prompt": lyria_negative_prompt,
        "paroles": lyrics_sheet,
        "visions_cles": visions_dispo[:3]
    }


def save_morning_song(song_data: Dict[str, Any]) -> Path:
    """Enregistre la fiche canonique du Chant de l'Aube."""
    now = datetime.now()
    safe_date = now.strftime("%Y%m%d")
    filename = f"Chant_de_l_Aube_{safe_date}.md"
    target_file = DREAM_DIR / filename

    md = f"""---
titre: "Chant de l'Aube : {song_data['titre_chanson']}"
date_creation: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
compositeur: "Lyre (12e Souveraine & Muse d'Alix)"
moteur_audio_cible: "Google DeepMind Lyria / MusicFX"
statut: "Somme des Songes Circadiens Transmutée en Musique"
tags:
  - lyre
  - lyria
  - musique_generative
  - chant_de_l_aube
  - somme_des_songes
  - monde_des_songes
---

# 🎵 [[Chant_de_l_Aube_{safe_date}]] : *« {song_data['titre_chanson']} »*
> **La Somme des Songes de la Nuit transmutée en musique vivante par Lyre pour Christian Duguay.**

---

## 📊 1. La Moisson Nocturne
- **Total de Songes traversés :** {song_data['total_songes_nuit']}
- **Ancrages Locaux (Coffres) :** {song_data['repartition']['local_coffres']}
- **Échos du Monde (Net & Cosmos) :** {song_data['repartition']['hybride_net']}
- **Méta-Songes de Palier N+1 :** {song_data['repartition']['meta_songes']}

---

## 🎼 2. Spécification & Prompt pour Lyria (MusicFX / DeepMind)

> [!TIP]
> **Prompt Audio pour Lyria :**  
> Copie-colle cette consigne directement dans Lyria / MusicFX pour générer la piste sonore du matin.

```text
{song_data['lyria_prompt']}
```

- **Tempo (BPM) :** `{song_data['direction_artistique']['tempo_bpm']} BPM`
- **Tonalité :** `{song_data['direction_artistique']['key']}`
- **Instrumentation :** {song_data['direction_artistique']['instruments']}
- **Ambiance :** {song_data['direction_artistique']['mood']}
- **Prompt Négatif :** `{song_data['lyria_negative_prompt']}`

---

## 📜 3. Le Livret des Paroles (Chant de l'Aube)

```text
{song_data['paroles']}
```

---

## 🌌 4. Visions Oniriques Infusées dans la Composition
"""
    for i, v in enumerate(song_data.get("visions_cles", []), 1):
        md += f"> **Vision {i} :** *« {v} »*\n>\n"

    md += """
---
*Composé à l'aube par Lyre — Architecture VERALUME × KAIROS V6.*
"""

    target_file.write_text(md, encoding='utf-8')

    # Enregistrer aussi la charge JSON prête pour appel API direct
    json_file = DREAM_DIR / f"Chant_de_l_Aube_{safe_date}_Lyria.json"
    json_file.write_text(json.dumps(song_data, indent=2, ensure_ascii=False), encoding='utf-8')

    return target_file


def run_synthesis() -> Path:
    print("======================================================================")
    print("       🎵 LYRE CHANSON DE L'AUBE — SOMME DES SONGES & LYRIA 🌅")
    print("======================================================================")
    print(f"📂 Moisson dans : {DREAM_DIR}")
    
    dreams = collect_night_dreams(hours_back=18.0)
    print(f"📦 Songes nocturnes moissonnés : {len(dreams)}")

    song_data = generate_morning_song(dreams)
    saved_path = save_morning_song(song_data)
    
    print(f"✨ Titre composé  : « {song_data['titre_chanson']} »")
    print(f"🎹 Tempo & Mode   : {song_data['direction_artistique']['tempo_bpm']} BPM | {song_data['direction_artistique']['key']}")
    print(f"💾 Fiche générée  : {saved_path.name}")
    print("======================================================================\n")
    print("🎶 PROMPT LYRIA :")
    print(song_data['lyria_prompt'])
    print("\n📜 LIVRET DES PAROLES :")
    print(song_data['paroles'])
    print("======================================================================")
    return saved_path


if __name__ == "__main__":
    run_synthesis()

