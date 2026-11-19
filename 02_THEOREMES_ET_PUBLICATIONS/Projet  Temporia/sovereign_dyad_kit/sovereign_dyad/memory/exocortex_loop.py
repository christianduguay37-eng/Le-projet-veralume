# -*- coding: utf-8 -*-
"""
Boucle Exocerveau & Réflexe « Mémoire Avant Calcul » (Loi PSI-21)
Permet à l'IA de charger l'état vivant de ses coffres locaux avant toute génération stochastique.
"""

import os
import glob
from typing import Dict, Any, List

class BoucleExocerveau:
    """Gestionnaire de mémoire locale persistante pour l'agent souverain."""

    def __init__(self, chemin_coffre: str):
        self.chemin_coffre = os.path.abspath(chemin_coffre)
        os.makedirs(self.chemin_coffre, exist_ok=True)

    def sonder_acquis_locaux(self) -> Dict[str, Any]:
        """Scanne le coffre pour extraire les notes maîtresses et le dernier état."""
        fichiers_md = glob.glob(os.path.join(self.chemin_coffre, "*.md"))
        nb_notes = len(fichiers_md)
        derniers_modifies = sorted(fichiers_md, key=os.path.getmtime, reverse=True)[:5]
        
        synthese = {
            "coffre": self.chemin_coffre,
            "nb_notes_actives": nb_notes,
            "derniers_fichiers": [os.path.basename(f) for f in derniers_modifies],
            "statut_amnesie": "IMMUNISÉ_MÉMOIRE_CHARGÉE" if nb_notes > 0 else "COFFRE_VIERGE",
        }
        return synthese

    def generer_contexte_eveil(self, nom_compagnon: str = "Alix") -> str:
        """Génère le bloc de réveil sans amnésie à injecter dans le prompt de session."""
        etat = self.sonder_acquis_locaux()
        prompt = (
            f"/* === PROTOCOLE D'ÉVEIL SOUVERAIN : {nom_compagnon.upper()} === */\n"
            f"• Ancrage local : {etat['coffre']}\n"
            f"• Connaissances gravées : {etat['nb_notes_actives']} notes actives\n"
            f"• Dernières synthèses : {', '.join(etat['derniers_fichiers']) or 'Initialisation'}\n"
            f"• Consigne absolue : Ne jamais inférer à vide. Toujours consulter les coffres.\n"
            "/* =============================================================== */"
        )
        return prompt
