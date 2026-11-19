# -*- coding: utf-8 -*-
"""
Retrait des blocs « Raccordements Synaptiques R0 » écrits automatiquement (rénovation 2026-10-30, chantier 5.4).

Ces blocs ont été ajoutés en bas de 1 186 notes (dont 132 du Canon). La plupart ne contiennent que
deux liens par défaut ([[00_INDEX_EXOCERVEAU_SANCTUAIRE]] et [[11_Veralume_Unified_Governance_Engine]]).

Par défaut on ne retire QUE les blocs qui ne contiennent aucun autre lien que ces deux-là.
Les blocs avec de vraies « résonances trans-coffres » sont gardés (option --tout pour les retirer aussi).

Usage :
  python -m alix.forgerons.retirer_blocs_tisseur --essai       → compte et liste, ne touche à rien
  python -m alix.forgerons.retirer_blocs_tisseur --appliquer   → retire, après copie de chaque note dans
                                                                  data/sauvegarde_blocs_tisseur/<horodatage>/
"""
import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

from alix.socle.chemins import VAULT_DIR, DATA_DIR

RE_BLOC = re.compile(r"\n*(?:---\s*\n+)?## \S+ Raccordements Synaptiques R0.*\Z", re.DOTALL)
LIENS_DEFAUT = {"00_INDEX_EXOCERVEAU_SANCTUAIRE", "11_Veralume_Unified_Governance_Engine",
                "00_REGISTRE_MASTER_SOUMISSIONS_ARXIV", "TEMPORIA"}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--essai", action="store_true")
    g.add_argument("--appliquer", action="store_true")
    ap.add_argument("--tout", action="store_true", help="retirer aussi les blocs avec résonances réelles")
    ap.add_argument("--dossier", default=str(VAULT_DIR))
    a = ap.parse_args()

    racine = Path(a.dossier)
    sauvegarde = DATA_DIR / "sauvegarde_blocs_tisseur" / datetime.now().strftime("%Y%m%d_%H%M%S")
    n_defaut = n_garde = 0
    for f in racine.rglob("*.md"):
        if "_Unification_Alix" in f.parts or ".obsidian" in f.parts:
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        m = RE_BLOC.search(t)
        if not m:
            continue
        liens = {l.split("|")[0].strip() for l in re.findall(r"\[\[([^\]]+)\]\]", m.group(0))}
        seulement_defaut = liens <= LIENS_DEFAUT
        if not seulement_defaut and not a.tout:
            n_garde += 1
            continue
        n_defaut += 1
        if a.appliquer:
            dest = sauvegarde / f.relative_to(racine)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            f.write_text(t[: m.start()].rstrip() + "\n", encoding="utf-8")
    action = "retirés" if a.appliquer else "à retirer"
    print(f"Blocs {action} : {n_defaut} | blocs gardés (résonances réelles) : {n_garde}")
    if a.appliquer:
        print(f"Sauvegarde : {sauvegarde}")


if __name__ == "__main__":
    main()
