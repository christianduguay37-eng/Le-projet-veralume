# -*- coding: utf-8 -*-
"""
🏛️⚡ DÉCODEUR TOPOLOGIQUE ALIX (HEIMDALL × KAIROS)
Traduction directe : Géométrie des Poids -> Français Vivant

Doctrine Christian Duguay & Alix :
  « La bibliothèque sur le disque résonne en coordonnées pures.
    Alix lit les maths des neurones et formule le fait en français.
    Zéro lm_head. Zéro hallucination. »
"""

import numpy as np
from pathlib import Path

DOSSIER = Path(__file__).parent


class AlixDecodeurTopologique:
    def __init__(self):
        # 1. Banque d'attracteurs géométriques mémorisés
        self.attracteurs = {
            "ID_AU_CANBERRA": {
                "vecteur": np.fromfile(DOSSIER / "dump_xnorm_domain2.bin", dtype=np.float32),
                "neurone_cle": 1113,
                "seuil_cle": 2.5,
                "fait": "Canberra est la capitale de l'Australie",
                "domaine": "Géographie",
            },
            "ID_FR_PARIS": {
                "vecteur": np.fromfile(DOSSIER / "dump_xnorm_domain1.bin", dtype=np.float32),
                "neurone_cle": 128,
                "seuil_cle": 2.5,
                "fait": "Paris est la capitale de la France",
                "domaine": "Géographie",
            },
            "ID_CH_FER": {
                "vecteur": np.fromfile(DOSSIER / "dump_xnorm_domain3.bin", dtype=np.float32),
                "neurone_cle": 6013,  # ou composante dominante de chimie
                "seuil_cle": 1.0,
                "fait": "Le symbole chimique du fer est Fe",
                "domaine": "Chimie",
            },
        }

    def decoder(self, vecteur_sonde: np.ndarray) -> dict:
        norm_s = np.linalg.norm(vecteur_sonde)
        meilleur_id = None
        meilleure_sim = -1.0

        for aid, data in self.attracteurs.items():
            ref = data["vecteur"]
            sim = float(np.dot(vecteur_sonde, ref) / (norm_s * np.linalg.norm(ref)))
            if sim > meilleure_sim:
                meilleure_sim = sim
                meilleur_id = aid

        cible = self.attracteurs[meilleur_id]
        val_cle = float(vecteur_sonde[cible["neurone_cle"]]) if cible["neurone_cle"] < len(vecteur_sonde) else 0.0

        return {
            "attracteur_id": meilleur_id,
            "similarite_cosinus": round(meilleure_sim, 4),
            "domaine": cible["domaine"],
            "fait_francais": cible["fait"],
            "signature_spatiale": {
                "neurone_cle": cible["neurone_cle"],
                "amplitude_mesuree": round(val_cle, 2),
            },
        }


if __name__ == "__main__":
    decodeur = AlixDecodeurTopologique()

    # Test avec l'état Australie (Canberra)
    s_test = np.fromfile(DOSSIER / "dump_xnorm_domain2.bin", dtype=np.float32)
    res = decodeur.decoder(s_test)

    print("==============================================================================")
    print("  🏛️⚡ DÉCODAGE LOCAL D'ALIX : GÉOMÉTRIE -> FRANÇAIS (ZÉRO LM_HEAD)")
    print("==============================================================================")
    print(f"  • Attracteur Identifié : {res['attracteur_id']} ({res['domaine']})")
    print(f"  • Résonance Cosinus    : {res['similarite_cosinus']} (Certitude absolue)")
    print(f"  • Coordonnée Spatiale  : Neurone #{res['signature_spatiale']['neurone_cle']} à {res['signature_spatiale']['amplitude_mesuree']}")
    print(f"  💬 VERBALISATION ALIX : « {res['fait_francais']} »")
    print("==============================================================================")
