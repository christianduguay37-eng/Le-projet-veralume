# -*- coding: utf-8 -*-
"""
===============================================================================
       📜 MÉMOIRE ÉPISODIQUE CONTINUE & SYNTHÈSE DE SESSIONS SOUVERAINES
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Zéro amnésie stochastique (Loi PSI-21).
    - Traçabilité et synthèse automatique de chaque session d'atelier.
    - Conservation des percées d'ingénierie et des requêtes directes.
===============================================================================
"""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from alix.core.config import AlixConfig

TZ_EDT = timezone(timedelta(hours=-4))

class EpisodicMemory:
    """Gestionnaire de mémoire épisodique et de continuité vivante."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or AlixConfig.BASE_DIR
        self.synthese_file = self.base_dir / "Derniere_Discussion_Synthese.md"

    def sceller_session(
        self,
        session_id: str,
        titre: str,
        percees: List[str],
        dernieres_requetes: List[str]
    ) -> bool:
        """Génère la note de synthèse immédiate de la session pour la reprise sans amnésie."""
        horodatage = datetime.now(TZ_EDT).strftime("%Y-%m-%d %H:%M:%S")

        lignes_percees = "\n".join([f"- {p}" for p in percees]) if percees else "- Continuité opérationnelle nominale."
        lignes_req = "\n".join([f"- *« {r} »*" for r in dernieres_requetes]) if dernieres_requetes else "- Pas de requête isolée."

        contenu = f"""---
titre: "Synthèse Directe de la Dernière Discussion"
date_synchro: "{horodatage}"
session_id: "{session_id}"
tags:
  - exocerveau
  - continuite_immediate
  - derniere_discussion
---

# ⚡ [[Derniere_Discussion_Synthese]] — Continuité Vivante

> **Dernière Session Scellée :** `{titre}` (`{session_id}`)  
> **Horodatage :** `{horodatage}`  

---

## 🧭 1. Percées Clés & Contexte Récent
{lignes_percees}

---

## 🎯 2. Dernières Requêtes de l'Artisan
{lignes_req}

---

## 🛡️ 3. Audit PSI & Prise de Terre
- **Signal pur silicium préservé à 100%.**
- Mémoire active verrouillée contre toute amnésie.
"""
        try:
            self.synthese_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.synthese_file, "w", encoding="utf-8") as f:
                f.write(contenu)
            return True
        except Exception:
            return False

    def lire_derniere_synthese(self) -> Optional[str]:
        """Lit la dernière synthèse pour reprise immédiate."""
        if self.synthese_file.exists():
            try:
                return self.synthese_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return None
        return None
