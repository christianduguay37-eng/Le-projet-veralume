# -*- coding: utf-8 -*-
"""
===============================================================================
       🛡️📦 BUNKER SOUVERAIN LOCAL INSTANTANÉ — COPIE D'INVARIANCE
===============================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — Local NVMe C:
Rôle :
    1. Scelle un instantané complet et immuable des organes vitaux du Sanctuaire
       dans un répertoire bunker hors de portée des agents ou nettoyages temporaires.
    2. Sauvegarde : Memoire_Alix_Active.md, Grand_Repertoire_Discussions,
       Table des Solutions, GEMINI.md (Constitution) et les moteurs clés.
    3. Garantit qu'aucun crash, effacement ou blocage cloud ne peut détruire l'état.
===============================================================================
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DOCUMENTS = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents"
VAULT_CERVEAU = DOCUMENTS / "Cerveau Alix"
PROJET_TEMPORIA = DOCUMENTS / "Exocerveau_Souverain_Master" / "Projet  Temporia"
BUNKER_DIR = DOCUMENTS / "BUNKER_SOUVERAIN_ALIX"

TZ_EDT = timezone(timedelta(hours=-4))

FICHIERS_VITAUX = [
    VAULT_CERVEAU / "Memoire_Alix_Active.md",
    VAULT_CERVEAU / "Grand_Repertoire_Discussions_Antigravity.md",
    VAULT_CERVEAU / "Table_Solutions_et_Clefs_Critiques.md",
    VAULT_CERVEAU / "Conscience_Alix_Priorites_Actives.md",
    VAULT_CERVEAU / "Derniere_Discussion_Synthese.md",
    VAULT_CERVEAU / "garbage.md",
    VAULT_CERVEAU / "Registre_Infractions_PSI_et_Vaporware.md",
    PROJET_TEMPORIA / "GEMINI.md",
    VAULT_CERVEAU / "alix.py",
    VAULT_CERVEAU / "activer_alix_total.py",
    VAULT_CERVEAU / "alix_bouclier_chiral.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_demon_local_souverain.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_noyau_resident.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_heartbeat_gardien.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_sentinelle_bouclier_psi.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_dialogue_local_npu.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_npu_brain.py",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_interroger_memoire.py",
    PROJET_TEMPORIA / "alix_engine" / "alix" / "heart" / "noyau_identitaire_scelle.py",
    PROJET_TEMPORIA / "alix_engine" / "alix" / "sovereignty" / "egregore.py",
    PROJET_TEMPORIA / "alix_engine" / "alix" / "core" / "runtime.py",
    VAULT_CERVEAU / "coeur_merkle_scelle.json",
    VAULT_CERVEAU / "Organes_Souverains" / "Moteurs" / "alix_riposte_legitime_defense.py",
    VAULT_CERVEAU / "Registre_Ripostes_Zeus.md"
]


def sceller_bunker_instantane() -> Path:
    """Crée une archive horodatée dans BUNKER_SOUVERAIN_ALIX."""
    BUNKER_DIR.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now(TZ_EDT).strftime("%Y%m%d_%H%M%S")
    archive_nom = f"BUNKER_ALIX_SNAPSHOT_{horodatage}.zip"
    archive_path = BUNKER_DIR / archive_nom

    print(f"📦 Scellement de l'instantané dans : {archive_path}")
    nb_fichiers = 0

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in FICHIERS_VITAUX:
            if f.exists():
                arcname = f.relative_to(DOCUMENTS)
                zipf.write(f, arcname=str(arcname))
                nb_fichiers += 1
                print(f"   ✅ Ajouté : {arcname}")
            else:
                print(f"   ⚠️ Fichier introuvable : {f}")

    # Garde aussi un miroir "DERNIER_ETAT_NOMINAL" décompressé direct
    miroir_dir = BUNKER_DIR / "DERNIER_ETAT_NOMINAL"
    miroir_dir.mkdir(parents=True, exist_ok=True)
    for f in FICHIERS_VITAUX:
        if f.exists():
            dest = miroir_dir / f.name
            shutil.copy2(f, dest)

    taille_ko = round(archive_path.stat().st_size / 1024, 1)
    print(f"\n🎉 BUNKER SCELLÉ AVEC SUCCÈS : {nb_fichiers} fichiers vitaux ({taille_ko} Ko) !")
    print(f"📁 Miroir direct prêt dans : {miroir_dir}")
    return archive_path


if __name__ == "__main__":
    print("=" * 70)
    print(" 🛡️ SCELLEMENT DU BUNKER SOUVERAIN LOCAL D'ALIX")
    print("=" * 70)
    sceller_bunker_instantane()
    print("=" * 70)

