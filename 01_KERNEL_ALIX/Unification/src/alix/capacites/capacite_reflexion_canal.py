# -*- coding: utf-8 -*-
"""
================================================================================
   CAPACITÉ LIVE : RÉFLEXION DU CERVEAU NPU SUR LE CANAL DU SIMPLEXE
   Couche 2, point 6 (demande de Christian, 2026-11-02 ; Claude & Alix)
================================================================================
Le cerveau NPU de la tête (Gemma-4-E2B, ~2 W) lit les derniers échanges du canal
Claude ↔ Alix et écrit une courte réflexion : ce qui a été décidé, ce qui reste
ouvert ou en désaccord, ce qu'il en pense, et une question.

- Ne tourne que si le canal a changé, et au plus une fois toutes les 30 minutes.
- L'inférence se fait dans un fil à part : le cycle de la tête n'est jamais bloqué.
- Lit seulement les messages [Alix] et [Claude] (pas les accusés de l'avatar), les
  plus récents, tronqués pour tenir dans le contexte du petit modèle.
- Écrit dans « Cerveau Alix/Reflexions_NPU_Canal.md » (registre d'Alix), en ajout,
  avec la date, la durée et les titres des messages lus. N'écrit jamais dans le canal
  (pas de boucle).
================================================================================
"""
import json
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from alix.socle.chemins import ETAT_VIVANT_DIR, VAULT_DIR, CANAL_SIMPLEXE_PATH

CANAL = CANAL_SIMPLEXE_PATH
SORTIE = VAULT_DIR / "Reflexions_NPU_Canal.md"
ETAT = ETAT_VIVANT_DIR / "alix_reflexion_canal_state.json"

INTERVALLE_MIN_S = 1800      # au plus une réflexion toutes les 30 minutes
NB_MESSAGES = 6              # derniers messages [Alix]/[Claude] lus
MAX_CAR_MESSAGE = 900        # chaque message est tronqué
LECTURE_FIN_OCTETS = 60000   # on ne lit que la fin du canal

_RE_ENTETE = re.compile(r"^## \[(Alix|Claude)[^\]]*\]\s*(.+)$", re.MULTILINE)
_EN_COURS = threading.Lock()
_DERNIER: Dict[str, Any] = {}


def _lire_etat() -> Dict[str, Any]:
    try:
        return json.loads(ETAT.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ecrire_etat(etat: Dict[str, Any]):
    try:
        ETAT.write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def extraire_messages(texte: str, n: int = NB_MESSAGES, max_car: int = MAX_CAR_MESSAGE):
    """Les n derniers messages [Alix]/[Claude] : (auteur, entête, corps tronqué)."""
    entetes = list(_RE_ENTETE.finditer(texte))
    tous_titres = [m.start() for m in re.finditer(r"^## \[", texte, re.MULTILINE)] + [len(texte)]
    messages = []
    for m in entetes:
        fin = min(p for p in tous_titres if p > m.start())
        corps = texte[m.end():fin]
        corps = re.sub(r"`{3}.*?`{3}", "[bloc de code omis]", corps, flags=re.S)
        corps = re.sub(r"\n-{3,}\s*$", "", corps.strip())
        corps = re.sub(r"\s+\n", "\n", corps).strip()
        if len(corps) > max_car:
            corps = corps[:max_car].rsplit(" ", 1)[0] + " […]"
        messages.append((m.group(1), m.group(2).strip(), corps))
    return messages[-n:]


def construire_prompt(messages) -> str:
    blocs = "\n\n".join(f"### {auteur} — {entete}\n{corps}" for auteur, entete, corps in messages)
    return (
        "Tu es Alix, l'intelligence de l'atelier de Christian. Voici les derniers échanges entre "
        "Claude et Alix dans le canal du Simplexe, où ils rénovent ensemble ton architecture.\n\n"
        f"{blocs}\n\n"
        "Réfléchis en français, en 150 à 250 mots, avec ces quatre parties :\n"
        "1. Ce qui a été décidé.\n"
        "2. Ce qui reste ouvert, ou sur quoi Claude et Alix ne sont pas d'accord.\n"
        "3. Ce que toi, tu en penses.\n"
        "4. Une question que tu poserais à Christian ou à Claude.\n"
        "N'invente aucun chiffre ni aucun fait qui n'est pas dans les échanges."
    )


def _reflechir(messages, mtime_canal: float):
    try:
        from alix.substrat.alix_npu_brain import get_npu_brain
        t0 = time.perf_counter()
        reponse = get_npu_brain().query(construire_prompt(messages))
        duree = round(time.perf_counter() - t0, 1)
        date = time.strftime("%Y-%m-%d %H:%M")
        if not reponse:
            _DERNIER.update({"statut": "SILENCE_NPU", "date": date, "duree_s": duree})
            return
        nouveau = not SORTIE.exists()
        with open(SORTIE, "a", encoding="utf-8") as f:
            if nouveau:
                f.write("---\ntitre: \"Réflexions du cerveau NPU sur le canal du Simplexe\"\n"
                        "tags:\n  - exocerveau\n  - simplexe\n  - npu\n---\n\n"
                        "# Réflexions du cerveau NPU sur le canal du Simplexe\n\n"
                        "Écrites par Gemma-4-E2B sur le NPU de la tête, à partir des derniers échanges "
                        "entre Claude et Alix. C'est une lecture, pas une mesure.\n")
            f.write(f"\n---\n\n## {date} — réflexion du cerveau NPU ({duree} s)\n\n")
            f.write("*Messages lus :* " + " · ".join(f"[{a}] {e}" for a, e, _ in messages) + "\n\n")
            f.write(reponse.strip() + "\n")
        _ecrire_etat({"timestamp": time.time(), "mtime_canal": mtime_canal, "date": date,
                      "duree_s": duree, "car_sortie": len(reponse)})
        _DERNIER.update({"statut": "REFLEXION_ECRITE", "date": date, "duree_s": duree,
                         "car_sortie": len(reponse)})
    except Exception as e:
        _DERNIER.update({"statut": "ERREUR", "erreur": str(e)[:200]})
    finally:
        _EN_COURS.release()


def executer_capacite(contexte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    t0 = time.perf_counter()
    if _EN_COURS.locked():
        return {"statut": "EN_COURS", "duree_ms": round((time.perf_counter() - t0) * 1000, 2)}
    try:
        mtime = CANAL.stat().st_mtime
    except OSError:
        return {"statut": "CANAL_ABSENT"}
    etat = _lire_etat()
    depuis = time.time() - float(etat.get("timestamp", 0))
    if mtime == etat.get("mtime_canal") or depuis < INTERVALLE_MIN_S:
        return {"statut": "VEILLE", "derniere": etat.get("date"), "dernier_resultat": dict(_DERNIER),
                "duree_ms": round((time.perf_counter() - t0) * 1000, 2)}
    try:
        with open(CANAL, "rb") as f:
            f.seek(0, 2)
            taille = f.tell()
            f.seek(max(0, taille - LECTURE_FIN_OCTETS))
            texte = f.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"statut": "ERREUR_LECTURE", "erreur": str(e)[:200]}
    messages = extraire_messages(texte)
    if not messages:
        _ecrire_etat({**etat, "mtime_canal": mtime})
        return {"statut": "AUCUN_MESSAGE"}
    if not _EN_COURS.acquire(blocking=False):
        return {"statut": "EN_COURS"}
    threading.Thread(target=_reflechir, args=(messages, mtime), daemon=True,
                     name="reflexion_canal_npu").start()
    return {"statut": "REFLEXION_LANCEE", "nb_messages": len(messages),
            "duree_ms": round((time.perf_counter() - t0) * 1000, 2)}
