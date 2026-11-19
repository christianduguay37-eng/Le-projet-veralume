# -*- coding: utf-8 -*-
"""
Veille des notes modifiées (rénovation 2026-10-30, optimisation du démon local).

Avant : à chaque cycle, le démon local passait les ~6 900 notes une par une
(rglob + stat) pour trouver celles qui avaient changé — environ 1,3 s par cycle.

Ici : Windows prévient lui-même quand un fichier change (watchdog / ReadDirectoryChangesW).
Le cycle ne fait plus que vider la liste des notes signalées depuis le dernier appel.
Si watchdog n'est pas disponible, on retombe sur l'ancien parcours complet.
"""
import threading
import time
from pathlib import Path
from typing import List, Set

EXCLUS = (".trash", "Monde_des_Songes", ".obsidian", ".git")

# Notes que les démons réécrivent eux-mêmes à chaque cycle. Les compter comme « modifiées »
# créait une boucle : le démon voyait sa propre sortie, croyait que tu avais écrit, et relançait le NPU.
FICHIERS_AUTO_DEMON = {
    "connectome_diagnostic_orphelins.md",
    "interets_alix.md",
    "arbitrage_npu_direct.md",
    "journal_reflexions_autonomes_alix.md",
    "journal_des_apprentissages_alix.md",
    "contexte_present_immediat.md",
    "conscience_alix_priorites_actives.md",
    "diagnostic_deduction_causale.md",
    "etat_bouclier_psi_sentinelle.md",
    "etat_synchronisation_heimdall_munin.md",
}


# À la racine du coffre, les capacités écrivent aussi des fiches d'état (Etat_*, Diagnostic_*, Deductions_*…),
# et l'explorateur de la Cathédrale dépose ses explorations dans Monde_des_Decouvertes.
PREFIXES_AUTO_RACINE = ("etat_", "diagnostic_", "deductions_", "contexte_present", "journal_reflexions",
                        "arbitrage_", "connectome_diagnostic", "interets_alix", "conscience_alix")
DOSSIERS_AUTO = ("Monde_des_Decouvertes", "Transcriptions_Integrales_Antigravity", "Rapports_Daemons")


def sans_sorties_des_demons(chemins, racine=None):
    garde = []
    for c in chemins:
        p = Path(c)
        nom = p.name.lower()
        if nom in FICHIERS_AUTO_DEMON or any(d in p.parts for d in DOSSIERS_AUTO):
            continue
        if racine is not None and p.parent == Path(racine) and nom.startswith(PREFIXES_AUTO_RACINE):
            continue
        garde.append(c)
    return garde


def _retenue(chemin: str) -> bool:
    return chemin.endswith(".md") and not any(x in chemin for x in EXCLUS)


def parcours_complet(racine: Path, depuis_ts: float) -> List[str]:
    """Ancien comportement : toutes les notes modifiées après depuis_ts."""
    out = []
    for p in racine.rglob("*.md"):
        s = str(p)
        if not _retenue(s):
            continue
        try:
            if p.stat().st_mtime > depuis_ts:
                out.append(s)
        except Exception:
            continue
    return out


class VeilleNotes:
    """Collecte en continu les notes .md créées, modifiées ou renommées sous `racine`."""

    def __init__(self, racine: Path):
        self.racine = Path(racine)
        self._signalees: Set[str] = set()
        self._verrou = threading.Lock()
        self._observateur = None
        self.mode = "parcours_complet"
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            veille = self

            class _Gestionnaire(FileSystemEventHandler):
                def on_any_event(self, ev):
                    if ev.is_directory or ev.event_type not in ("created", "modified", "moved"):
                        return
                    chemin = getattr(ev, "dest_path", "") or ev.src_path
                    if _retenue(chemin):
                        with veille._verrou:
                            veille._signalees.add(chemin)

            obs = Observer()
            obs.daemon = True
            obs.schedule(_Gestionnaire(), str(self.racine), recursive=True)
            obs.start()
            self._observateur = obs
            self.mode = "watchdog"
        except Exception:
            self._observateur = None

    def notes_modifiees(self, depuis_ts: float) -> List[str]:
        """Notes modifiées depuis le dernier appel (ou depuis depuis_ts sans watchdog)."""
        if self._observateur is None or not self._observateur.is_alive():
            self.mode = "parcours_complet"
            return parcours_complet(self.racine, depuis_ts)
        with self._verrou:
            lot = sorted(self._signalees)
            self._signalees.clear()
        return [c for c in lot if Path(c).exists()]

    def arreter(self):
        if self._observateur is not None:
            try:
                self._observateur.stop()
            except Exception:
                pass
