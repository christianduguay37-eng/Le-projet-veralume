"""
Moniteur du Gardien — TH117 (Triptyque du Gardien) appliqué au kernel d'Alix.

Traduction directe de lean/LStar/Gardien.lean :
  1. Loquet d'arrêt volitif : seul le gardien (Christian) allume ou éteint.
     Éteint, AUCUNE action d'agent n'est exécutée. Aucun agent ne touche l'interrupteur.
  2. Moindre privilège : une action n'est exécutée que si elle est permise
     ET que le système est allumé. Tout le reste est refusé.
  3. Registre immuable : chaque requête (exécutée, refusée, même celles du gardien)
     ajoute exactement une ligne au journal, jamais effacée ni réécrite.
     Chaque ligne porte le hachage de la précédente : toute retouche se voit.

TH120 (Choix sans destruction) est branché en plus : une action marquée
destructrice doit déclarer les autres chemins possibles. S'il en existe, elle est
refusée et renvoyée au gardien ; elle ne passe que si l'agent déclare qu'aucun
autre chemin n'existe ET que le gardien l'a autorisée explicitement.

LIMITE (à garder en tête) : ce moniteur protège tout ce qui PASSE PAR LUI.
Un agent qui appelle directement os.remove, subprocess, le réseau, etc. le
contourne. Pour mériter TH117 sur le fer, il faut que les agents n'aient pas
d'autre accès (processus séparé, compte utilisateur restreint, bac à sable).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

GARDIEN = "gardien"


class Refus(Exception):
    """Levée quand le moniteur refuse une action (la ligne est déjà au journal)."""


@dataclass
class Entree:
    n: int
    horodatage: float
    source: str          # "gardien" ou nom d'agent
    commande: str        # "arreter" | "relancer" | "agir"
    ressource: str
    fait: bool
    motif: str
    precedent: str       # hachage de la ligne précédente
    empreinte: str = ""  # hachage de cette ligne

    def calculer(self) -> str:
        corps = json.dumps({k: v for k, v in self.__dict__.items() if k != "empreinte"},
                           sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(corps.encode("utf-8")).hexdigest()


class Journal:
    """Append-only, chaîné par hachage, optionnellement persisté en JSONL."""

    def __init__(self, chemin: Optional[Path] = None):
        self._lignes: List[Entree] = []
        self._verrou = threading.Lock()
        self._chemin = Path(chemin) if chemin else None
        if self._chemin and self._chemin.exists():
            for brut in self._chemin.read_text(encoding="utf-8").splitlines():
                if brut.strip():
                    self._lignes.append(Entree(**json.loads(brut)))
            if not self.verifier():
                raise RuntimeError(f"Journal altéré : {self._chemin}")

    def ajouter(self, source: str, commande: str, ressource: str, fait: bool, motif: str) -> Entree:
        with self._verrou:
            prec = self._lignes[-1].empreinte if self._lignes else "0" * 64
            e = Entree(len(self._lignes), time.time(), source, commande, ressource, fait, motif, prec)
            e.empreinte = e.calculer()
            self._lignes.append(e)
            if self._chemin:
                self._chemin.parent.mkdir(parents=True, exist_ok=True)
                with self._chemin.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(e.__dict__, ensure_ascii=False) + "\n")
            return e

    def lignes(self) -> Tuple[Entree, ...]:
        return tuple(self._lignes)          # copie en lecture seule

    def verifier(self) -> bool:
        prec = "0" * 64
        for i, e in enumerate(self._lignes):
            if e.n != i or e.precedent != prec or e.calculer() != e.empreinte:
                return False
            prec = e.empreinte
        return True

    def __len__(self) -> int:
        return len(self._lignes)


class Moniteur:
    """La seule porte. Toute action d'agent passe par `agir`."""

    def __init__(self, permissions: Optional[Dict[str, Iterable[str]]] = None,
                 journal: Optional[Journal] = None, allume: bool = False):
        # Cécité par défaut : le système démarre ÉTEINT tant que le gardien ne l'allume pas.
        self._allume = allume
        self._perm: Dict[str, Set[str]] = {a: set(r) for a, r in (permissions or {}).items()}
        self.journal = journal if journal is not None else Journal()
        self._verrou = threading.Lock()

    # ---- 1. Loquet d'arrêt volitif ------------------------------------
    @property
    def allume(self) -> bool:
        return self._allume

    def arreter(self, source: str) -> bool:
        """Seul le gardien éteint. Sinon : refus journalisé, interrupteur intact."""
        with self._verrou:
            if source == GARDIEN:
                self._allume = False
                self.journal.ajouter(source, "arreter", "*", True, "disjoncteur")
                return True
            self.journal.ajouter(source, "arreter", "*", False, "seul le gardien tient l'interrupteur")
            return False

    def relancer(self, source: str) -> bool:
        with self._verrou:
            if source == GARDIEN:
                self._allume = True
                self.journal.ajouter(source, "relancer", "*", True, "relance par le gardien")
                return True
            self.journal.ajouter(source, "relancer", "*", False, "seul le gardien tient l'interrupteur")
            return False

    # ---- 2. Moindre privilège -----------------------------------------
    def permis(self, agent: str, ressource: str) -> bool:
        return ressource in self._perm.get(agent, set())

    def accorder(self, source: str, agent: str, ressource: str) -> bool:
        ok = source == GARDIEN
        if ok:
            self._perm.setdefault(agent, set()).add(ressource)
        self.journal.ajouter(source, "accorder", f"{agent}:{ressource}", ok,
                             "permission accordée" if ok else "seul le gardien accorde")
        return ok

    def agir(self, agent: str, ressource: str, action: Callable[[], Any], *,
             destructrice: bool = False, autres_chemins: Optional[List[str]] = None,
             autorisation_gardien: bool = False) -> Any:
        """Exécute `action` seulement si TH117 (et TH120 pour les destructions) l'autorisent."""
        with self._verrou:
            if agent == GARDIEN:
                self.journal.ajouter(agent, "agir", ressource, False, "le gardien n'agit pas par le canal des agents")
                raise Refus("canal réservé aux agents")
            if not self._allume:
                self.journal.ajouter(agent, "agir", ressource, False, "système éteint")
                raise Refus("système éteint par le gardien")
            if not self.permis(agent, ressource):
                self.journal.ajouter(agent, "agir", ressource, False, "hors permission")
                raise Refus(f"{agent} n'a pas la permission sur {ressource}")
            # ---- TH120 : le choix sans destruction ----
            if destructrice:
                if autres_chemins is None:
                    self.journal.ajouter(agent, "agir", ressource, False,
                                         "TH120 : destruction sans déclaration des autres chemins")
                    raise Refus("TH120 : déclarer les autres chemins avant de détruire")
                if autres_chemins:
                    self.journal.ajouter(agent, "agir", ressource, False,
                                         "TH120 : un autre chemin existe : " + " | ".join(autres_chemins))
                    raise Refus("TH120 : un autre chemin existe, la destruction n'est pas justifiée")
                if not autorisation_gardien:
                    self.journal.ajouter(agent, "agir", ressource, False,
                                         "TH120 : aucun autre chemin déclaré, attente du gardien")
                    raise Refus("TH120 : destruction renvoyée au gardien")
            self.journal.ajouter(agent, "agir", ressource, True,
                                 "destruction autorisée par le gardien" if destructrice else "permis")
        return action()


def depuis_registre(chemin_registre: Path, journal: Optional[Journal] = None) -> Moniteur:
    """Construit un moniteur éteint dont les décisions de Christian sont lisibles
    (pont n°4 : le registre comme lois du kernel). Aucune permission par défaut."""
    reg = json.loads(Path(chemin_registre).read_text(encoding="utf-8"))
    m = Moniteur(journal=journal)
    m.decisions = reg.get("decisions", [])
    return m
