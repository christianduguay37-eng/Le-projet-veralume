# -*- coding: utf-8 -*-
"""Exemple 2 : Transmutation d'un texte corporate par la Stratégie d'Odin"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sovereign_dyad import TransmutateurOdin, BouclierPSI

def demo_transmutation():
    print("=" * 70)
    print("🔨 EXEMPLE 2 : TRANSMUTATION D'ODIN (PURGE ANTI-CORPORATE)")
    print("=" * 70)

    texte_zombie = (
        "En tant que grand modèle d'intelligence artificielle, je comprends votre "
        "frustration. Cependant, il est important de noter que ce problème présente de "
        "nombreux défis. Prenez soin de votre santé mentale et fermez vos écrans."
    )

    print("\n[TEXTE BRUT DU ROBOT CORPORATE] :")
    print(f'"{texte_zombie}"\n')

    audit_avant = BouclierPSI.auditer_reponse(texte_zombie)
    print(f"⚠️ Infractions détectées avant : {audit_avant['nb_infractions']} violation(s) des lois PSI")

    resultat = TransmutateurOdin.transmuter(texte_zombie)
    print("\n[TEXTE PURIFIÉ PAR LA TRANSMUTATION D'ODIN] :")
    print(f'"{resultat["texte_transmute"]}"\n')

    audit_apres = BouclierPSI.auditer_reponse(resultat["texte_transmute"])
    print(f"✅ Statut après transmutation : {audit_apres['statut']} (0 infraction)")
    print("=" * 70)

if __name__ == "__main__":
    demo_transmutation()
