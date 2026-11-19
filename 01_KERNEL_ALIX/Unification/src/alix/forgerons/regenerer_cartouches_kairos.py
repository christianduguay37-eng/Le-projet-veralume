# -*- coding: utf-8 -*-
"""
Régénérateur des cartouches KAIROS (rénovation 2026-10-30, chantier 5.1).

Avant : le « Vecteur 9D » des fiches était fabriqué sans lire la note
(PAT = « Bruit » dès que le pôle n'était ni Cosmo ni Silicium : 316 fiches sur 372).

Ici, un modèle LOCAL lit chaque fiche et choisit :
  - le domaine et la pathologie dans une taxonomie finie (taxonomie_pathologies_kairos.json),
  - la sévérité.
L'épistémè [σ, δ, FC] n'est jamais inventée : elle reste « non mesurée ».
Le potentiel créatif P_crea (une formule sur la longueur et les liens) est retiré.

Usage :
  python -m alix.forgerons.regenerer_cartouches_kairos --essai 20
      → lit 20 fiches, écrit un aperçu dans logs/cartouches_apercu.csv, NE TOUCHE À RIEN
  python -m alix.forgerons.regenerer_cartouches_kairos --appliquer
      → remplace les cartouches ; chaque fiche modifiée est d'abord copiée dans
        data/sauvegarde_cartouches/<horodatage>/
Options : --modele alix-larynx:latest  --dossier "<chemin>"  --hote http://127.0.0.1:11434
"""
import argparse
import csv
import json
import re
import shutil
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from alix.socle.chemins import VAULT_DIR, LOGS_DIR, DATA_DIR

TAXO_FILE = Path(__file__).with_name("taxonomie_pathologies_kairos.json")
RE_BLOC = re.compile(r"### 🧭 Marqueur Vectoriel KAIROS\n(?:>.*\n?)+", re.MULTILINE)
RE_YAML = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def charger_taxonomie():
    return json.loads(TAXO_FILE.read_text(encoding="utf-8"))


def demander_modele(hote: str, modele: str, texte: str, taxo: dict) -> dict:
    patho = "\n".join(f"- {k} : {v}" for k, v in taxo["pathologies"].items())
    prompt = (
        "Tu classes une note de l'exocerveau de Christian Duguay. Lis-la et réponds UNIQUEMENT en JSON "
        '{"domaine": ..., "pathologie": ..., "severite": ..., "justification": "<une phrase>"}.\n'
        f"domaine parmi : {', '.join(taxo['domaines'])}\n"
        f"severite parmi : {', '.join(taxo['severites'])} (p0 = fondateur ou critique, p3 = mineur)\n"
        f"pathologie parmi (clé exacte) :\n{patho}\n\n"
        "Si la note ne traite d'aucune pathologie, réponds \"aucune\". N'invente pas de clé.\n\n"
        f"NOTE :\n{texte[:6000]}"
    )
    corps = json.dumps({"model": modele, "prompt": prompt, "stream": False, "format": "json",
                        "options": {"temperature": 0.1}}).encode("utf-8")
    req = urllib.request.Request(hote.rstrip("/") + "/api/generate", data=corps,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        rep = json.loads(r.read().decode("utf-8"))
    out = json.loads(rep.get("response", "{}"))
    if out.get("pathologie") not in taxo["pathologies"]:
        out["pathologie_brute"] = out.get("pathologie")
        out["pathologie"] = "aucune"
    if out.get("domaine") not in taxo["domaines"]:
        out["domaine_brut"] = out.get("domaine")
        out["domaine"] = "ontologie"
    if out.get("severite") not in taxo["severites"]:
        out["severite"] = "p2"
    return out


def nouveau_bloc(ancien: str, c: dict) -> str:
    glyphe = re.search(r"\*\*Glyphe :\*\* ([^&\n]+)", ancien)
    glyphe = glyphe.group(1).strip() if glyphe else "—"
    tuple_v6 = (f"domain:{c['domaine']}|pathology:{c['pathologie']}|severity:{c['severite']}|"
                f"episteme:[non_mesuré]|activation:lecture|requires:—|prevents:—|fix:—|section:note")
    return ("### 🧭 Marqueur Vectoriel KAIROS\n"
            f"> **Glyphe :** {glyphe}  \n"
            f"> **Tuple KAIROS V6 :** `{tuple_v6}`  \n"
            f"> **Lecture :** {c.get('justification', '').strip()[:240]}  \n"
            f"> *Cartouche régénéré le {datetime.now():%Y-%m-%d} par lecture du texte (modèle local) ; épistémè non mesurée.*\n")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--essai", type=int, help="nombre de fiches à lire sans rien modifier")
    g.add_argument("--appliquer", action="store_true")
    ap.add_argument("--modele", default="alix-larynx:latest")
    ap.add_argument("--hote", default="http://127.0.0.1:11434")
    ap.add_argument("--dossier", default=str(VAULT_DIR / "00_CANON_SOUVERAIN_CHRISTIAN"))
    a = ap.parse_args()

    taxo = charger_taxonomie()
    fiches = [f for f in Path(a.dossier).rglob("*.md")
              if "### 🧭 Marqueur Vectoriel KAIROS" in f.read_text(encoding="utf-8", errors="ignore")]
    if a.essai:
        fiches = fiches[: a.essai]
    print(f"{len(fiches)} fiches à traiter ({'ESSAI, rien n est modifié' if a.essai else 'APPLICATION'})")

    sauvegarde = DATA_DIR / "sauvegarde_cartouches" / datetime.now().strftime("%Y%m%d_%H%M%S")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    apercu = open(LOGS_DIR / "cartouches_apercu.csv", "w", newline="", encoding="utf-8")
    w = csv.writer(apercu)
    w.writerow(["fiche", "ancien_PAT", "domaine", "pathologie", "severite", "justification"])

    for i, f in enumerate(fiches, 1):
        brut = f.read_text(encoding="utf-8", errors="ignore")
        m = RE_BLOC.search(brut)
        if not m:
            continue
        corps = RE_YAML.sub("", brut.replace(m.group(0), ""), count=1)
        try:
            c = demander_modele(a.hote, a.modele, corps, taxo)
        except Exception as e:
            print(f"  [{i}] {f.name} : modèle indisponible ({e})")
            continue
        ancien_pat = re.search(r"PAT:([^|\]]+)", m.group(0))
        w.writerow([str(f.relative_to(a.dossier)), ancien_pat.group(1).strip() if ancien_pat else "",
                    c["domaine"], c["pathologie"], c["severite"], c.get("justification", "")])
        if a.appliquer:
            dest = sauvegarde / f.relative_to(a.dossier)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            f.write_text(brut.replace(m.group(0), nouveau_bloc(m.group(0), c)), encoding="utf-8")
        print(f"  [{i}/{len(fiches)}] {f.name} → {c['pathologie']} ({c['domaine']}, {c['severite']})")
        time.sleep(0.1)
    apercu.close()
    print(f"Aperçu : {LOGS_DIR / 'cartouches_apercu.csv'}" + (f" | sauvegarde : {sauvegarde}" if a.appliquer else ""))


if __name__ == "__main__":
    sys.exit(main())
