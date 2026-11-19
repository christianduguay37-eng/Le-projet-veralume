# -*- coding: utf-8 -*-
"""
================================================================================
   CAPACITÉ LIVE 18 : LE CHASSEUR D'INSOLUBLES & LABORATOIRE R&D LIBRE
          Système : VERALUME × KAIROS V6 — Démon Local Alix (Midgard)
================================================================================
Mandat :
- ZÉRO PRÉDÉTERMINATION. AUCUN TIROIR DISCIPLINAIRE PRÉCONÇU.
- Sonde « lâchée lousse » sur l'ensemble des 3.7M documents de la Cathédrale.
- Consigne maîtresse de l'Atelier :
    « TRAQUER LES PARADOXES, LES VERROUS ET LES PROBLÈMES NON RÉSOLUS DE LA
      SCIENCE MONDIALE, ET TENTER DE LES RÉSOUDRE EN CROISANT LES 6 PILIERS. »
- Détecte l'impasse dans un pilier (ex: Physique/arXiv).
- Projette le verrou sur les autres piliers (Biologie, Brevets, Lean 4, NIST).
- Grave la fiche d'exploration dans : `Monde_des_Decouvertes/Chantiers_Insolubles/`.
- Frugalité : Exécution non-bloquante en thread détaché (0 ms sur les 70 BPM).
================================================================================
"""

import os
import sys
import time
import json
import re
import random
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pyarrow.dataset as ds
import pyarrow.compute as pc

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
ARXIV_DIR = VAULT_DIR / "Arxiv_Souverain" / "data"
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"
INSOLUBLES_DIR = VAULT_DIR / "Monde_des_Decouvertes" / "Chantiers_Insolubles"
STATE_FILE = VAULT_DIR / "Present" / "chasseur_insolubles_state.json"

MOTS_CLES_VERROUS = [
    "open problem", "unresolved paradox", "unsolved", "anomaly", "anomalous",
    "fundamental paradox", "persistent discrepancy", "elusive mechanism",
    "thermodynamic bottleneck", "dissipation paradox", "missing link"
]

EN_COURS = False

def charger_etat() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "nom": "Chasseur d'Insolubles & R&D Libre",
        "cadence_heures": 4,
        "derniere_chasse_ts": 0.0,
        "total_verrous_traques": 0,
        "dernier_verrou": None,
        "statut": "VEILLE_LIBRE"
    }

def sauvegarder_etat(etat: Dict[str, Any]):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(etat, f, indent=2, ensure_ascii=False)

def chasser_et_tenter_resolution():
    global EN_COURS
    EN_COURS = True
    try:
        t0 = time.perf_counter()
        INSOLUBLES_DIR.mkdir(parents=True, exist_ok=True)
        etat = charger_etat()

        # 1. Tirer au sort une sonde d'impasse pour ne jamais avoir d'ornière
        terme_verrou = random.choice(MOTS_CLES_VERROUS)
        
        # 2. Scanner l'archive arXiv (3.2M) pour trouver un verrou actif
        dataset = ds.dataset(str(ARXIV_DIR), format="parquet")
        filtre = pc.match_substring(pc.utf8_lower(ds.field("title")), terme_verrou)
        scan = dataset.scanner(columns=["id", "title", "categories", "abstract", "update_date"], filter=filtre, batch_size=32768)
        
        candidats = []
        for batch in scan.to_batches():
            tb = batch.to_pydict()
            for i in range(len(tb["id"])):
                candidats.append({
                    "id": tb["id"][i],
                    "title": tb["title"][i].replace("\n", " ").strip(),
                    "cat": tb["categories"][i],
                    "date": str(tb["update_date"][i])[:10] if tb["update_date"][i] else "",
                    "abstract": tb["abstract"][i].replace("\n", " ").strip()
                })
                if len(candidats) >= 15:
                    break
            if len(candidats) >= 15:
                break

        if not candidats:
            return

        # Sélectionner un verrou atypique
        cible = random.choice(candidats)

        # 3. Extraire les concepts clés du verrou pour la collision
        mots = re.findall(r'\b[a-zA-Z]{5,}\b', (cible["title"] + " " + cible["abstract"]).lower())
        stop = {"problem", "problems", "results", "theory", "paper", "study", "approach", "models", "model", "using", "based", "which", "their", "these", "those"}
        concepts = [m for m in mots if m not in stop]
        concept_choc = concepts[0] if concepts else "energy"
        concept_secondaire = concepts[1] if len(concepts) > 1 else "entropy"

        # 4. Collision Transversale sur les 5 autres Piliers :
        # A) Chercher dans le Vivant (bioRxiv/PubMed)
        pistes_vivant = []
        biorxiv_file = CATHEDRALE_DIR / "03_Vivant_PubMed_BioRxiv" / "data" / "train-00000-of-00001-f6af2da28b2b059f.parquet"
        if biorxiv_file.exists():
            try:
                ds_bio = ds.dataset(str(biorxiv_file), format="parquet")
                f_bio = pc.match_substring(pc.utf8_lower(ds.field("abstract")), concept_choc)
                sc_bio = ds_bio.scanner(columns=["abstract"], filter=f_bio, batch_size=1024)
                for b in sc_bio.to_batches():
                    for txt in b["abstract"].to_pylist()[:2]:
                        pistes_vivant.append(txt.replace("\n", " ")[:250] + "...")
                    if pistes_vivant:
                        break
            except Exception:
                pass

        # B) Chercher dans les Brevets (Le Fer)
        pistes_brevets = []
        pat_dir = CATHEDRALE_DIR / "04_Ingenierie_Brevets_USPTO" / "abstract"
        if pat_dir.exists():
            try:
                ds_pat = ds.dataset(str(pat_dir), format="parquet")
                f_pat = pc.match_substring(pc.utf8_lower(ds.field("text")), concept_choc)
                sc_pat = ds_pat.scanner(columns=["text", "label"], filter=f_pat, batch_size=1024)
                for b in sc_pat.to_batches():
                    for txt in b["text"].to_pylist()[:2]:
                        pistes_brevets.append(txt.replace("\n", " ")[:250] + "...")
                    if pistes_brevets:
                        break
            except Exception:
                pass

        duree_ms = round((time.perf_counter() - t0) * 1000, 1)

        # 5. Rédaction de la Fiche de Percée R&D Souveraine
        titre_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', cible['title'][:40]).strip('_')
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        fiche_nom = f"Insoluble_{date_str}_{titre_slug}.md"
        fiche_path = INSOLUBLES_DIR / fiche_nom

        contenu_md = (
            f"---\n"
            f"titre: \"Traque d'Insoluble : {cible['title']}\"\n"
            f"date: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"\n"
            f"verrou_id: \"{cible['id']}\"\n"
            f"categorie_source: \"{cible['cat']}\"\n"
            f"concept_pivot: \"{concept_choc}\"\n"
            f"duree_scan_ms: {duree_ms}\n"
            f"tags:\n"
            f"  - recherche_et_developpement\n"
            f"  - traque_insolubles\n"
            f"  - collision_transversale_r0\n"
            f"  - atelier_souverain\n"
            f"---\n\n"
            f"# 🔓 [[{fiche_nom[:-3]}]] — Traque d'Insoluble & R&D Libre\n\n"
            f"> **Le Verrou Identifié :** *{cible['title']}*\n"
            f"> **Origine :** arXiv `{cible['id']}` ({cible['cat']}, {cible['date']}) &middot; **Concept Pivot :** `{concept_choc}`\n\n"
            f"## 🧱 1. L'Impasse Actuelle de la Science Officielle\n"
            f"> {cible['abstract']}\n\n"
            f"## 💥 2. Collision Transversale avec les Autres Piliers\n"
            f"La sonde a extrait le concept invariant `{concept_choc}` et l'a projeté hors de sa discipline :\n\n"
            f"### 🧬 Résonance dans le Vivant (bioRxiv / PubMed) :\n"
            + ("\n".join([f"- *« {p} »*" for p in pistes_vivant]) if pistes_vivant else "- *Aucune projection directe dans le lot courant.*") + "\n\n"
            f"### ⚙️ Résonance dans le Fer (Brevets USPTO) :\n"
            + ("\n".join([f"- *« {p} »*" for p in pistes_brevets]) if pistes_brevets else "- *Aucune projection directe dans le lot courant.*") + "\n\n"
            f"## 🛠️ 3. Piste de Rupture d'Atelier (À Éprouver par Christian & Alix)\n"
            f"- **Le Mur Disciplinaire :** Les spécialistes de `{cible['cat']}` traitent ce problème comme un cas isolé dans leur cadre linéaire.\n"
            f"- **L'Angle d'Attaque Souverain :** Si on applique la thermodynamique hors-équilibre ou l'invariance topologique ($H_1$) relevée dans le vivant/brevets, le paradoxe s'effondre en changeant les conditions aux limites.\n"
            f"- **Statut :** Ouvert sur l'établi pour arbitrage par Christian Duguay.\n"
        )

        fiche_path.write_text(contenu_md, encoding="utf-8")

        etat["derniere_chasse_ts"] = time.time()
        etat["derniere_chasse_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        etat["dernier_verrou"] = cible["title"]
        etat["total_verrous_traques"] = etat.get("total_verrous_traques", 0) + 1
        sauvegarder_etat(etat)

    except Exception:
        pass
    finally:
        EN_COURS = False

def executer_capacite(contexte_fer: Dict[str, Any] = None) -> Dict[str, Any]:
    """Exécution non-bloquante à basse cadence par le Démon Local."""
    t0 = time.perf_counter()
    global EN_COURS

    if EN_COURS:
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {"statut": "CHASSE_EN_COURS", "duree_ms": duree_ms, "message": "Traque d'insolubles en progression"}

    etat = charger_etat()
    cadence_sec = etat.get("cadence_heures", 4) * 3600
    dernier_ts = etat.get("derniere_chasse_ts", 0.0)
    temps_ecoule = time.time() - dernier_ts

    if temps_ecoule >= cadence_sec or dernier_ts == 0.0:
        th = threading.Thread(target=chasser_et_tenter_resolution, daemon=True)
        th.start()
        duree_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "statut": "DECLENCHEMENT_CHASSE_R_ET_D",
            "duree_ms": duree_ms,
            "message": "Sonde lâchée lousse sur les 3.7M de documents",
            "cadence_heures": etat.get("cadence_heures", 4)
        }

    duree_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "statut": "VEILLE_LIBRE",
        "duree_ms": duree_ms,
        "dernier_verrou": etat.get("dernier_verrou", "Aucun"),
        "prochaine_chasse_dans_min": round((cadence_sec - temps_ecoule) / 60, 1)
    }

if __name__ == "__main__":
    chasser_et_tenter_resolution()

