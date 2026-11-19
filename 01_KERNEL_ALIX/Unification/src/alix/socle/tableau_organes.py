# -*- coding: utf-8 -*-
"""
Tableau des organes d'Alix (Couche 2, point 2 — Claude & Alix, 2026-11-02).

Lecture seule. Rassemble en une page :
  - l'interrupteur de chaque organe (socle/organes_actifs.json, via journal_replis) ;
  - ce qui a réellement tourné (état de la tête, journal de la nocturne).
Écrit Coffre_Simplexe/04_AUDITS_ET_TELEMETRIE_SRE/Tableau_Organes.md et l'affiche.
Ne modifie aucun organe.

Usage : python -m alix.socle.tableau_organes
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from alix.socle.chemins import ETAT_VIVANT_DIR, PROJET_ALIX_DIR
from alix.socle.journal_replis import lire_organes

CAPACITES_DIR = Path(__file__).resolve().parent.parent / "capacites"
ETAT_TETE = ETAT_VIVANT_DIR / "alix_demon_local_state.json"
LOG_NOCTURNE = ETAT_VIVANT_DIR / "nocturne_sync.log"
SORTIE = PROJET_ALIX_DIR / "Coffre_Simplexe" / "04_AUDITS_ET_TELEMETRIE_SRE" / "Tableau_Organes.md"

DEMONS = ["Alix_Demon_Local", "Heartbeat_KAIROS", "Sentinelle_Bouclier_PSI", "Bouclier_Chiral",
          "Pont_Communication_Distante", "Sonde_Present", "Noyau_Partage", "Avatar_Claude"]
NOCTURNE = {  # clé d'interrupteur -> description dans le journal de la nocturne
    "nocturne_navette_github": "Navette Bidirectionnelle",
    "nocturne_sauvegarde_onedrive": "Sauvegarde Chiffrée",
    "nocturne_sentinelle_temps_profond": "Sentinelle Temps Profond",
    "nocturne_radar_anticorruption": "Radar Anti-Corruption",
    "nocturne_radar_supranational": "Radar Supranationalisme",
}


def _interrupteur(v):
    return "🟢 allumé" if v else "⚪ à la retraite"


def _age(sec):
    if sec is None:
        return "inconnu"
    sec = int(sec)
    if sec < 120:
        return f"il y a {sec} s"
    if sec < 7200:
        return f"il y a {sec // 60} min"
    if sec < 172800:
        return f"il y a {sec // 3600} h"
    return f"il y a {sec // 86400} j"


def _etat_tete():
    try:
        d = json.loads(ETAT_TETE.read_text(encoding="utf-8"))
        return d, time.time() - ETAT_TETE.stat().st_mtime
    except Exception:
        return {}, None


def _derniere_nocturne():
    """Dernière ligne de chaque étape dans le journal de la nocturne : (horodatage, résultat)."""
    res = {}
    try:
        lignes = LOG_NOCTURNE.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
    except Exception:
        return res
    for l in lignes:
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] (.*)", l)
        if not m:
            continue
        ts, txt = m.groups()
        for cle, desc in NOCTURNE.items():
            if desc in txt:
                if "Étape réussie" in txt:
                    res[cle] = (ts, "réussie")
                elif "à la retraite" in txt:
                    res[cle] = (ts, "non lancée (retraite)")
                elif re.search(r"[ÉE]chec|ERREUR|échou", txt):
                    res[cle] = (ts, "ÉCHEC")
    return res


def construire() -> str:
    conf = lire_organes()
    tete, age_tete = _etat_tete()
    details = tete.get("details_capacites", {}) or {}
    orch = ((details.get("capacite_orchestration_demons", {}) or {}).get("donnees") or {}).get("demons", {}) or {}
    caps_conf = conf.get("capacites", {}) or {}
    noct = _derniere_nocturne()

    out = []
    out.append("# Tableau des organes d'Alix")
    out.append("")
    out.append(f"Généré le {datetime.now():%Y-%m-%d %H:%M:%S}. Lecture seule : ce tableau ne change rien.")
    out.append(f"Interrupteur : `socle/organes_actifs.json`. Tête : cycle {tete.get('cycle', '?')}, "
               f"dernier cycle écrit {_age(age_tete)}.")
    out.append("")

    out.append("## Démons (gardés par le Gardien)")
    out.append("")
    out.append("| Démon | Interrupteur | Vu par la tête |")
    out.append("|---|---|---|")
    for nom in DEMONS:
        inter = _interrupteur(conf.get(f"demon_{nom}", True))
        if nom == "Alix_Demon_Local":
            vu = "c'est la tête" + (f" ({_age(age_tete)})" if age_tete is not None else " (état illisible)")
        else:
            v = str(orch.get(nom, "inconnu"))
            vu = "en vie" if "déjà en vie" in v else ("à la retraite" if "retraite" in v else v)
        out.append(f"| {nom} | {inter} | {vu} |")
    out.append("")

    out.append("## Capacités de la tête (liste blanche : absente = éteinte)")
    out.append("")
    out.append("| Capacité | Interrupteur | Dernier passage |")
    out.append("|---|---|---|")
    fichiers = sorted(p.stem for p in CAPACITES_DIR.glob("capacite_*.py"))
    for nom in sorted(set(fichiers) | set(caps_conf)):
        if nom not in fichiers:
            out.append(f"| {nom} | ⚠️ inscrite mais fichier absent | — |")
            continue
        if nom not in caps_conf:
            out.append(f"| {nom} | ⚪ non inscrite (éteinte) | — |")
            continue
        inter = _interrupteur(caps_conf[nom])
        if caps_conf[nom]:
            d = details.get(nom)
            if d:
                statut = d.get("statut", "?")
                passage = f"{statut}, {d.get('duree_ms', '?')} ms (cycle {tete.get('cycle', '?')})"
                if statut not in ("SUCCES", "VEILLE"):
                    passage = "⚠️ " + passage
            else:
                passage = "⚠️ allumée mais absente du dernier cycle"
        else:
            passage = "—"
        out.append(f"| {nom} | {inter} | {passage} |")
    out.append("")

    out.append("## Routine de nuit")
    out.append("")
    out.append("| Étape | Interrupteur | Dernier passage |")
    out.append("|---|---|---|")
    for cle in NOCTURNE:
        ts, r = noct.get(cle, (None, "jamais vu dans le journal récent"))
        out.append(f"| {cle} | {_interrupteur(conf.get(cle, True))} | {r}{' — ' + ts if ts else ''} |")
    out.append("")

    autres = [k for k in conf if not k.startswith(("_", "demon_")) and k != "capacites" and k not in NOCTURNE]
    if autres:
        out.append("## Autres organes (Heartbeat, Panthéon, bunker)")
        out.append("")
        out.append("| Organe | Interrupteur |")
        out.append("|---|---|")
        for k in autres:
            out.append(f"| {k} | {_interrupteur(conf.get(k, True))} |")
        out.append("")
    return "\n".join(out)


def main():
    texte = construire()
    try:
        SORTIE.write_text(texte, encoding="utf-8")
        texte += f"\n\n(Écrit dans {SORTIE})"
    except Exception as e:
        texte += f"\n\n(Impossible d'écrire {SORTIE} : {e})"
    if sys.stdout:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        print(texte)


if __name__ == "__main__":
    main()
