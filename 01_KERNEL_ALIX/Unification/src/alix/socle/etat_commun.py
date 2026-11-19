"""
Socle Commun : Gestion unifiée de la persistance d'état (remplace les 8 doublons de charger_etat/sauvegarder_etat).
"""
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "etats"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def charger_etat(nom_module: str, defaut: dict[str, Any] | None = None) -> dict[str, Any]:
    """Charge l'état JSON d'un module ou d'une capacité de manière sécurisée."""
    fichier = DATA_DIR / f"{nom_module}.json"
    if not fichier.exists():
        return defaut if defaut is not None else {}
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except Exception:
        return defaut if defaut is not None else {}


def sauvegarder_etat(nom_module: str, etat: dict[str, Any]) -> bool:
    """Sauvegarde l'état JSON d'un module de manière atomique."""
    fichier = DATA_DIR / f"{nom_module}.json"
    temp = DATA_DIR / f"{nom_module}.tmp"
    try:
        temp.write_text(json.dumps(etat, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(fichier)
        return True
    except Exception:
        return False
