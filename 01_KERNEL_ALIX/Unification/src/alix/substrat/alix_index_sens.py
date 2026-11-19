# -*- coding: utf-8 -*-
"""
Index du sens des notes (Couche 2, points 4-5 — Claude & Alix, 2026-11-02).

Chaque note (titre + début du texte, sans l'en-tête YAML) est encodée une fois par
EmbeddingGemma (256 dimensions, vecteurs normalisés). Une question est encodée de la
même façon, et les notes les plus proches par le sens sont rendues (produit scalaire).

Fichiers (dans Alix\\) :
    alix_index_sens.npy   matrice float16 (nb_notes × 256)
    alix_index_sens.json  {"dim": 256, "stems": [...], "mtimes": {stem: mtime}}
Mise à jour incrémentale : seules les notes nouvelles ou modifiées (mtime) sont réencodées.

Construction ou mise à jour (processus à part, ~100 ms par note sur CPU) :
    python -m alix.substrat.alix_index_sens --construire [--budget SECONDES]
"""
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

import numpy as np

from alix.socle.chemins import ETAT_VIVANT_DIR

DIM = 256
FICHIER_VEC = ETAT_VIVANT_DIR / "alix_index_sens.npy"
FICHIER_META = ETAT_VIVANT_DIR / "alix_index_sens.json"
_RE_ENTETE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
FICHIER_VERROU = ETAT_VIVANT_DIR / "alix_index_sens.verrou"
VERROU_ENCODAGE = threading.Lock()  # un seul encodage à la fois dans un processus
_VERROU_MAJ = threading.Lock()      # une seule mise à jour à la fois dans un processus


class VerrouFichier:
    """
    Une seule mise à jour de l'index à la fois, entre processus (la tête en direct,
    la construction manuelle, la nocturne). Un verrou de plus d'une heure est considéré abandonné.
    """
    def __init__(self, max_age_s: float = 3600):
        self.max_age_s = max_age_s
        self.tenu = False

    def __enter__(self):
        for _ in range(2):
            try:
                fd = os.open(str(FICHIER_VERROU), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"{os.getpid()} {time.time():.0f}".encode())
                os.close(fd)
                self.tenu = True
                return self
            except FileExistsError:
                try:
                    if time.time() - FICHIER_VERROU.stat().st_mtime > self.max_age_s:
                        FICHIER_VERROU.unlink()
                        continue
                except OSError:
                    continue
                return self
        return self

    def __exit__(self, *exc):
        if self.tenu:
            try:
                FICHIER_VERROU.unlink()
            except OSError:
                pass
        return False


def mise_a_jour_directe(notes: dict, encoder, journal=print):
    """
    Appelée par la tête quand des notes changent (diff Merkle). N'agit que si l'index existe déjà
    (on ne construit jamais l'index complet dans la tête) et si personne d'autre ne le met à jour.
    Tourne dans un fil à part ; un seul à la fois.
    """
    if not _VERROU_MAJ.acquire(blocking=False):
        return
    def _travail():
        try:
            idx = index_sens()
            if not idx.charger():
                return
            with VerrouFichier() as v:
                if not v.tenu:
                    return
                idx.charger()
                idx.mettre_a_jour(notes, encoder, budget_s=120, journal=journal)
        except Exception as e:
            journal(f"[Index du sens] mise à jour directe interrompue : {e}")
        finally:
            _VERROU_MAJ.release()
    threading.Thread(target=_travail, daemon=True, name="index_sens_direct").start()


def texte_document(stem: str, path: str, max_car: int = 1200) -> str:
    try:
        t = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        t = ""
    t = _RE_ENTETE.sub("", t, count=1)
    t = re.sub(r"\s+", " ", t).strip()[:max_car]
    return f"title: {stem} | text: {t}"


def texte_question(question: str) -> str:
    return f"task: search result | query: {question.strip()}"


class IndexSens:
    def __init__(self):
        self.lock = threading.RLock()
        self.stems = []
        self.mtimes = {}
        self.vecs = np.zeros((0, DIM), dtype=np.float32)
        self._mtime_meta = None

    # --- fichiers -----------------------------------------------------------
    def charger(self) -> bool:
        """(Re)charge l'index si le fichier a changé. Vrai si un index est disponible."""
        with self.lock:
            try:
                m = FICHIER_META.stat().st_mtime
            except OSError:
                return bool(self.stems)
            if m == self._mtime_meta:
                return bool(self.stems)
            try:
                meta = json.loads(FICHIER_META.read_text(encoding="utf-8"))
                vecs = np.load(FICHIER_VEC).astype(np.float32)
                if vecs.shape != (len(meta["stems"]), DIM):
                    return bool(self.stems)  # écriture en cours : on garde l'ancien
                self.stems, self.mtimes, self.vecs = meta["stems"], meta["mtimes"], vecs
                self._mtime_meta = m
            except Exception:
                pass
            return bool(self.stems)

    def sauver(self):
        with self.lock:
            tmp_v = FICHIER_VEC.with_name(FICHIER_VEC.stem + ".tmp.npy")
            tmp_m = FICHIER_META.with_suffix(".tmp.json")
            np.save(tmp_v, self.vecs.astype(np.float16))
            tmp_m.write_text(json.dumps({"dim": DIM, "stems": self.stems, "mtimes": self.mtimes},
                                        ensure_ascii=False), encoding="utf-8")
            os.replace(tmp_v, FICHIER_VEC)
            os.replace(tmp_m, FICHIER_META)  # la méta en dernier : le lecteur vérifie la forme

    # --- construction -------------------------------------------------------
    def mettre_a_jour(self, notes: dict, encoder, budget_s=None, journal=print) -> dict:
        """
        notes : {stem: {"path": ..., "mtime": ...}} ; encoder(texte) -> liste de floats normalisée ou None.
        Réencode les notes nouvelles ou modifiées, retire les disparues. Sauvegarde toutes les 200 notes.
        """
        t0 = time.time()
        with self.lock:
            garder = [i for i, s in enumerate(self.stems) if s in notes]
            retirees = len(self.stems) - len(garder)
            self.stems = [self.stems[i] for i in garder]
            self.vecs = self.vecs[garder] if len(garder) else np.zeros((0, DIM), dtype=np.float32)
            self.mtimes = {s: self.mtimes[s] for s in self.stems if s in self.mtimes}
            position = {s: i for i, s in enumerate(self.stems)}
        a_faire = [s for s, info in notes.items() if self.mtimes.get(s) != info.get("mtime")]
        if not a_faire and not retirees:
            return {"notes": len(notes), "encodees": 0, "echecs": 0, "retirees": 0,
                    "dans_index": len(self.stems), "duree_s": 0.0}
        journal(f"[Index du sens] {len(notes)} notes, {len(a_faire)} à encoder, {retirees} retirées.")
        faites = echecs = 0
        for n, stem in enumerate(a_faire, 1):
            if budget_s is not None and time.time() - t0 > budget_s:
                journal(f"[Index du sens] budget de {budget_s} s atteint : {faites} encodées, la suite au prochain passage.")
                break
            with VERROU_ENCODAGE:
                vec = encoder(texte_document(stem, notes[stem]["path"]))
            if not vec or len(vec) != DIM:
                echecs += 1
                continue
            v = np.asarray(vec, dtype=np.float32)
            norme = float(np.linalg.norm(v))
            v = v / norme if norme > 0 else v
            with self.lock:
                if stem in position:
                    self.vecs[position[stem]] = v
                else:
                    position[stem] = len(self.stems)
                    self.stems.append(stem)
                    self.vecs = np.vstack([self.vecs, v[None, :]])
                self.mtimes[stem] = notes[stem].get("mtime")
            faites += 1
            if faites % 200 == 0:
                self.sauver()
                journal(f"[Index du sens] {faites}/{len(a_faire)} encodées ({time.time() - t0:.0f} s).")
        if faites or retirees:
            self.sauver()
        bilan = {"notes": len(notes), "encodees": faites, "echecs": echecs, "retirees": retirees,
                 "dans_index": len(self.stems), "duree_s": round(time.time() - t0, 1)}
        journal(f"[Index du sens] terminé : {bilan}")
        return bilan

    # --- recherche ----------------------------------------------------------
    def chercher(self, vec_question, k: int = 5) -> list:
        with self.lock:
            if not self.stems:
                return []
            q = np.asarray(vec_question, dtype=np.float32)
            n = float(np.linalg.norm(q))
            if n > 0:
                q = q / n
            scores = self.vecs @ q
            k = max(1, min(int(k), len(self.stems)))
            idx = np.argpartition(-scores, k - 1)[:k]
            idx = idx[np.argsort(-scores[idx])]
            return [{"titre": self.stems[i], "score": round(float(scores[i]), 4)} for i in idx]


_INDEX = None


def index_sens() -> IndexSens:
    global _INDEX
    if _INDEX is None:
        _INDEX = IndexSens()
    return _INDEX


def main():
    if sys.stdout and getattr(sys.stdout, "reconfigure", None):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    budget = None
    if "--budget" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget") + 1])
    if "--construire" not in sys.argv:
        print(__doc__)
        return
    from alix.substrat.alix_noyau_resident import AlixConnectomeResident, AlixMoteurEmbeddingNPU
    con = AlixConnectomeResident()
    con.scanner_initial()
    moteur = AlixMoteurEmbeddingNPU()
    if not moteur.initialiser():
        print("[Index du sens] moteur d'embedding indisponible : arrêt, rien n'est modifié.")
        return
    notes = {s: {"path": i["path"], "mtime": i["mtime"]} for s, i in con.notes.items()}
    idx = index_sens()
    with VerrouFichier() as v:
        if not v.tenu:
            print("[Index du sens] une autre mise à jour est en cours (alix_index_sens.verrou) : rien à faire.")
            return
        idx.charger()
        idx.mettre_a_jour(notes, lambda t: moteur.encoder_texte(t, dim=DIM), budget_s=budget,
                          journal=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
