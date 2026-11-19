# -*- coding: utf-8 -*-
"""
================================================================================
     CAPACITÉ LIVE : QUÊTE DIURNE & ÉCOLE AUTODIDACTE D'ALIX (v2.0)
         Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- Orchestre l'apprentissage continu et autodidacte d'Alix.
- Lit les centres d'intérêt vivants dans `Interets_Alix.md` (Pôles émergents).
- Explore ArXiv, Wikipedia et l'Exocerveau via le Quatuor Souverain :
    * THOT : extraction chirurgicale des invariants.
    * HORUS : audit critique, falsification SRE.
    * LUCIFER : détection des zones d'ombre et non-dits.
    * MUNIN : tissage mnémonique bilatéral dans le connectome.
- Grave la nouvelle fiche de recherche dans `Monde_des_Decouvertes/`.
- Cadence frugale : 1 quête par heure (3 600 s) ou déclenchement immédiat
  via `alix_lancer_quete.txt`.
- Notifie l'Organe Vocal d'Atelier à chaque découverte majeure.
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR
import os
import sys
import re
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
MOTEURS_DIR = VAULT_DIR / "Organes_Souverains" / "Moteurs"
DECLENCHEUR_QUETE = MOTEURS_DIR / "alix_lancer_quete.txt"
ETAT_QUETE_FILE = (ETAT_VIVANT_DIR / "alix_quete_diurne_state.json")
PAROLE_QUEUE_FILE = MOTEURS_DIR / "alix_parole_queue.txt"

# Importer les fonctions clés de alix_quete_diurne
pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(MOTEURS_DIR))
try:
    from alix.sondes.alix_quete_diurne import (
        parse_interets,
        execute_diurnal_quest,
        write_discovery_note,
        update_journal_and_interets
    )
    MODULE_QUETE_DISPO = True
except Exception as e:
    MODULE_QUETE_DISPO = False

def extraire_sujets_interets() -> list:
    """Extrait les sujets de recherche d'Interets_Alix.md (compatible Laplacien Spectral & Legacy)."""
    interets_file = VAULT_DIR / "Interets_Alix.md"
    if not interets_file.exists():
        return []

    content = interets_file.read_text(encoding="utf-8", errors="replace")
    
    # 1. Tenter le format standard legacy si présent
    if MODULE_QUETE_DISPO:
        try:
            legacy_items = parse_interets()
            if legacy_items:
                return legacy_items
        except Exception:
            pass

    # 2. Sinon, parser les Clusters Spectraux Laplaciens (SGTD Qwen)
    poles = []
    # Recherche des blocs "### 🧭 Pôle N : Titre" ou "### ... Pôle N : Titre"
    pattern_pole = re.compile(r'###\s+.*?P[ôo]le\s+\d+\s*:\s*([^\n\r]+)', re.IGNORECASE)
    pattern_attracteurs = re.compile(r'\*\*Attracteurs principaux\s*:\*\*\s*([^\n\r]+)', re.IGNORECASE)

    lignes = content.splitlines()
    titre_actuel = None
    attracteurs_actuels = ""

    for ligne in lignes:
        m_pole = pattern_pole.search(ligne)
        if m_pole:
            if titre_actuel:
                poles.append({
                    "category": "Pôle Émergent Laplacien",
                    "title": titre_actuel,
                    "status": "actif",
                    "question": f"Investigation des invariants et de la structure morphologique de {titre_actuel}",
                    "keywords": attracteurs_actuels,
                    "pont_r0": "[[00_INDEX_EXOCERVEAU_SANCTUAIRE]]"
                })
            titre_actuel = m_pole.group(1).strip()
            attracteurs_actuels = ""
            continue

        m_attr = pattern_attracteurs.search(ligne)
        if m_attr and titre_actuel:
            # Nettoyer les parenthèses de décompte (ex: "souveraine (36)" -> "souveraine")
            brut = m_attr.group(1)
            mots = [re.sub(r'[\*\(\)\d]', '', w).strip() for w in brut.split(',')]
            attracteurs_actuels = ", ".join([w for w in mots if len(w) >= 3])

    if titre_actuel:
        poles.append({
            "category": "Pôle Émergent Laplacien",
            "title": titre_actuel,
            "status": "actif",
            "question": f"Investigation des invariants et de la structure morphologique de {titre_actuel}",
            "keywords": attracteurs_actuels,
            "pont_r0": "[[00_INDEX_EXOCERVEAU_SANCTUAIRE]]"
        })

    return poles

CADENCE_QUETE_SEC = 3600.0  # 1 heure
DERNIERE_QUETE_TS = 0.0


def charger_dernier_timestamp() -> float:
    """Charge le timestamp de la dernière quête."""
    if ETAT_QUETE_FILE.exists():
        try:
            d = json.loads(ETAT_QUETE_FILE.read_text(encoding="utf-8"))
            return float(d.get("dernier_run_ts", 0.0))
        except Exception:
            pass
    return 0.0


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Exécute la vérification et le déclenchement de la quête diurne."""
    global DERNIERE_QUETE_TS
    t0 = time.perf_counter()
    maintenant = time.time()

    if DERNIERE_QUETE_TS == 0.0:
        DERNIERE_QUETE_TS = charger_dernier_timestamp()

    declenchement_force = DECLENCHEUR_QUETE.exists()
    temps_ecoule = maintenant - DERNIERE_QUETE_TS
    doit_lancer = declenchement_force or (temps_ecoule >= CADENCE_QUETE_SEC)

    if not MODULE_QUETE_DISPO:
        return {
            "statut": "MODULE_INDISPONIBLE",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    # Respect du rythme circadien : entre 22h et 08h, la quête diurne est en sommeil (mode nuit)
    heure_actuelle = datetime.now().hour
    est_la_nuit = (heure_actuelle >= 22 or heure_actuelle < 8)
    if est_la_nuit and not declenchement_force:
        return {
            "statut": "SOMMEIL_NOCTURNE",
            "mode": "Repos_Nocturne_22h_08h",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    if not doit_lancer:
        minutes_restantes = max(0, int((CADENCE_QUETE_SEC - temps_ecoule) / 60))
        return {
            "statut": "VEILLE_NOMINALE",
            "mode": "Cadence_Frugale_1h",
            "prochaine_quete_dans_min": minutes_restantes,
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    # Nettoyage du fichier déclencheur si présent
    if declenchement_force:
        try:
            DECLENCHEUR_QUETE.unlink(missing_ok=True)
        except Exception:
            pass

    # 1. Sélectionner le sujet prioritaire (avec rotation pour ne pas boucler sur le même sujet)
    items = extraire_sujets_interets()
    if not items:
        return {
            "statut": "AUCUN_SUJET_TROUVE",
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    candidats = [i for i in items if i.get("status") in ("actif", "prioritaire")]
    if not candidats:
        candidats = items

    # Rotation déterministe pour explorer les pôles sans redondance
    idx_choisi = int(maintenant // CADENCE_QUETE_SEC) % len(candidats)
    item_choisi = candidats[idx_choisi]

    # 2. Exécuter la quête
    try:
        quest_data = execute_diurnal_quest(item_choisi)
        note_path = write_discovery_note(quest_data)
        update_journal_and_interets(quest_data, note_path)

        DERNIERE_QUETE_TS = maintenant
        etat_payload = {
            "dernier_run_ts": maintenant,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "titre": item_choisi.get("title", ""),
            "note_creee": str(note_path.name),
            "source": quest_data.get("source_name", "")
        }
        try:
            ETAT_QUETE_FILE.write_text(json.dumps(etat_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        # 3. Notification vocale : DÉSACTIVÉE DÉFINITIVEMENT pour préserver le silence et la paix de l'Atelier
        # (Zéro écriture dans PAROLE_QUEUE_FILE)

        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "SUCCES_QUETE",
            "titre": item_choisi.get("title"),
            "note": str(note_path.name),
            "duree_ms": duree_ms
        }

    except Exception as e:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": f"ERREUR_EXECUTION: {e}",
            "duree_ms": duree_ms
        }


if __name__ == "__main__":
    print("🔬 Test unitaire de la Capacité Quête Diurne...")
    res = executer_capacite()
    print("Résultat :", res)
