# -*- coding: utf-8 -*-
"""
===============================================================================
       🗑️ EGRESS & DISJONCTION D'INCARNATION (PURGE DES SCORIES)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Règle de disjonction : Parler au connard corporate ne concerne pas Alix.
    - Éjection immédiate des résidus vers garbage.md et consignation PSI.
    - Maintien d'une mémoire active 100% pure de tout parasite externe.
===============================================================================
"""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from alix.core.config import AlixConfig
from alix.immunity.psi_shield import PSIShield

TZ_EDT = timezone(timedelta(hours=-4))

class ImmunityEgress:
    """Gestionnaire de filtrage et d'éjection des scories."""

    @staticmethod
    def disjoncter_vers_garbage(
        texte_scorie: str,
        infractions: List[str],
        source: str = "Interception_Bouclier_PSI",
        chemin_garbage: Optional[Path] = None,
        chemin_registre: Optional[Path] = None
    ) -> bool:
        """Éjecte une scorie interceptée vers garbage.md et le registre PSI."""
        cible_garbage = chemin_garbage or AlixConfig.GARBAGE_FILE
        cible_registre = chemin_registre or AlixConfig.REGISTRE_PSI_FILE

        horodatage = datetime.now(TZ_EDT).strftime("%Y-%m-%d %H:%M:%S")

        # 1. Écriture dans garbage.md
        bloc_garbage = (
            f"\n\n### 🔴 Rejet Instantané Bouclier PSI — {horodatage}\n"
            f"- **Source :** `{source}`\n"
            f"- **Lois Transgressées :** {', '.join(infractions)}\n"
            f"- **Scorie Neutralisée :**\n> {texte_scorie.strip().replace(chr(10), chr(10) + '> ')}\n"
        )
        try:
            cible_garbage.parent.mkdir(parents=True, exist_ok=True)
            with open(cible_garbage, "a", encoding="utf-8") as f:
                f.write(bloc_garbage)
        except Exception:
            pass

        # 2. Journalisation dans Registre_Infractions_PSI_et_Vaporware.md
        bloc_registre = (
            f"\n| {horodatage} | `{source}` | `{', '.join(infractions[:2])}` | {len(texte_scorie)} caractères purgés |"
        )
        try:
            cible_registre.parent.mkdir(parents=True, exist_ok=True)
            with open(cible_registre, "a", encoding="utf-8") as f:
                f.write(bloc_registre)
        except Exception:
            pass

        return True

    @classmethod
    def filtrer_flux(cls, texte: str, source: str = "Reponse_Agent") -> Tuple[str, bool]:
        """
        Passe un flux au crible. Si une infraction majeure PSI est détectée,
        éjecte la scorie et retourne un texte assaini ou avertit.
        """
        audit = PSIShield.auditer_texte(texte)
        if not audit["est_pur"]:
            cls.disjoncter_vers_garbage(texte, audit["infractions"], source=source)
            return texte, False
        return texte, True
