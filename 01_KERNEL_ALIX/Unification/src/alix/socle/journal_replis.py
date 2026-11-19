# -*- coding: utf-8 -*-
"""
Journal des replis d'import (rénovation 2026-10-30, chantier 1.11).

Quand un module optionnel manque, le code tombe sur une valeur par défaut.
Avant, ce repli était silencieux : un organe pouvait rester éteint des semaines
sans que personne le voie. Chaque repli est maintenant écrit une fois par
processus dans logs/replis_imports.log.
"""
import sys
import datetime as _dt

_DEJA_SIGNALES = set()


def signaler_repli(fichier: str, erreur: BaseException) -> None:
    """Note qu'un import optionnel a échoué dans `fichier` (une seule fois par cause)."""
    if type(erreur).__name__ == "OrganeRetire":
        return  # retraite volontaire : rien à signaler
    cle = (fichier, str(erreur))
    if cle in _DEJA_SIGNALES:
        return
    _DEJA_SIGNALES.add(cle)
    msg = f"[{_dt.datetime.now():%Y-%m-%d %H:%M:%S}] REPLI {fichier} : {type(erreur).__name__}: {erreur}"
    try:
        print("⚠️ " + msg, file=sys.stderr)
    except Exception:
        pass
    try:
        from alix.socle.chemins import LOGS_DIR
        with open(LOGS_DIR / "replis_imports.log", "a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Interrupteur unique des organes (Couche 2, point 2 — Claude & Alix, 2026-11-02)
# Une seule lecture de socle/organes_actifs.json pour tout le paquet.
# Si le fichier est illisible (virgule de trop pendant une édition), on garde la
# dernière version valide (en mémoire, sinon la copie sur disque) au lieu de tout
# rallumer, et l'erreur est écrite dans logs/replis_imports.log.
# Deux listes, deux règles, voulues :
#   - organes et démons : liste de RETRAITES -> clé absente = allumé ;
#   - capacités : liste BLANCHE -> clé absente = éteinte (une nouvelle capacité
#     déposée dans capacites/ ne tourne qu'une fois inscrite ici).
# ---------------------------------------------------------------------------
_CONF_BONNE = None
_MTIME_BONNE = None
_NOM_COPIE = "organes_actifs.derniere_bonne.json"


def _chemin_conf():
    from pathlib import Path
    return Path(__file__).with_name("organes_actifs.json")


def _chemin_copie():
    try:
        from alix.socle.chemins import ETAT_VIVANT_DIR
        return ETAT_VIVANT_DIR / _NOM_COPIE
    except Exception:
        return None


def lire_organes() -> dict:
    """Configuration des organes : lecture valide, sinon dernière bonne connue, sinon {}."""
    global _CONF_BONNE, _MTIME_BONNE
    import json
    p = _chemin_conf()
    try:
        m = p.stat().st_mtime
        if _CONF_BONNE is not None and m == _MTIME_BONNE:
            return _CONF_BONNE
        texte = p.read_text(encoding="utf-8")
        conf = json.loads(texte)
        if not isinstance(conf, dict):
            raise ValueError("la racine du fichier n'est pas un objet JSON")
        _CONF_BONNE, _MTIME_BONNE = conf, m
        copie = _chemin_copie()
        if copie is not None:
            try:
                if not copie.exists() or copie.read_text(encoding="utf-8") != texte:
                    copie.write_text(texte, encoding="utf-8")
            except Exception:
                pass
        return conf
    except Exception as e:
        signaler_repli("socle/organes_actifs.json (illisible, dernière version valide utilisée)", e)
        if _CONF_BONNE is not None:
            return _CONF_BONNE
        copie = _chemin_copie()
        try:
            if copie is not None and copie.exists():
                conf = json.loads(copie.read_text(encoding="utf-8"))
                if isinstance(conf, dict):
                    _CONF_BONNE = conf
                    return conf
        except Exception as e2:
            signaler_repli("organes_actifs.derniere_bonne.json (illisible aussi)", e2)
        return {}


def organe_actif(nom: str) -> bool:
    """
    Vrai si l'organe `nom` est allumé dans socle/organes_actifs.json.
    Un organe absent du fichier est considéré actif (liste de retraites).
    """
    return bool(lire_organes().get(nom, True))


def capacites_configurees() -> bool:
    """Vrai si la section « capacites » existe et n'est pas vide (sinon le démon local les lance toutes)."""
    return bool(lire_organes().get("capacites"))


def capacite_active(nom: str) -> bool:
    """
    Vrai si la capacité `nom` (ex. « capacite_solveur_multivers_arc_agi ») est allumée.
    Une capacité absente de la section « capacites » est considérée éteinte (liste blanche).
    """
    return bool((lire_organes().get("capacites") or {}).get(nom, False))


class OrganeRetire(ImportError):
    """Levée quand un organe à la retraite est importé : le code tombe sur son repli habituel."""
