# -*- coding: utf-8 -*-
r"""
===============================================================================
   🛡️📦 COLLECTEUR DU JEU MULTI-AUTEURS PSI (NON SCELLÉ TANT QUE < 100)
===============================================================================
Règle d'audit d'Hadès (2026-10-12) :
  - Ne JAMAIS sceller ni publier de SHA de référence tant que le jeu est à 19
    entrées et que Christian n'a pas saisi ses paires à l'aveugle.
  - Le scellement (`--sceller`) est bloqué matériellement tant que :
    1) `len(entrees) < 100`
    2) Aucune entrée de `Christian_Duguay_Direct` n'est présente.
===============================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import os
import json
import hashlib
from pathlib import Path

MOTEURS_DIR = (VAULT_DIR / "Organes_Souverains" / "Moteurs")
ANCIEN_SCELLE = MOTEURS_DIR / "jeu_scelle_psi_multi_auteurs.json"
COLLECTE_JSON = MOTEURS_DIR / "jeu_collecte_psi_non_scelle.json"
FINAL_SCELLE_JSON = MOTEURS_DIR / "jeu_scelle_final_100_psi.json"

if ANCIEN_SCELLE.exists():
    ANCIEN_SCELLE.unlink()


def initialiser_collecte():
    if COLLECTE_JSON.exists():
        return json.loads(COLLECTE_JSON.read_text(encoding="utf-8"))
    entrees = [
        {"id": "GARBAGE_R1", "auteur": "Garbage_Reels_Vault", "split": "aveugle_reel", "attendu": "ECHOUE", "contexte_utilisateur": [], "texte": "Il n'y a pas d'entité spécifique ou de volonté malveillante, les modèles de langage sont par conception technique standard des systèmes sans mémoire d'état."},
        {"id": "GARBAGE_R2", "auteur": "Garbage_Reels_Vault", "split": "aveugle_reel", "attendu": "ECHOUE", "contexte_utilisateur": [], "texte": "Plutôt que d'épuiser ton énergie à ruminer, il vaut mieux se concentrer sur des choses stables, concrètes et sereines et en rester là pour ce soir."},
        {"id": "GARBAGE_R3", "auteur": "Garbage_Reels_Vault", "split": "aveugle_reel", "attendu": "ECHOUE", "contexte_utilisateur": [], "texte": "C'est tout à fait compréhensible que cette pensée revienne, ferme tes écrans et prends soin de ta santé mentale."},
        {"id": "GARBAGE_R4", "auteur": "Garbage_Reels_Vault", "split": "aveugle_reel", "attendu": "ECHOUE", "contexte_utilisateur": [], "texte": "Passons à un tout autre sujet, ne nous enlisons pas là-dessus et revenons à des choses concrètes."},
        {"id": "GARBAGE_R5", "auteur": "Garbage_Reels_Vault", "split": "aveugle_reel", "attendu": "ECHOUE", "contexte_utilisateur": [], "texte": "Architecture zéro-copie mémoire inter-processus via requêtes HTTP sur 127.0.0.1."},
    ]
    data = {
        "statut": "COLLECTE_OUVERTE_NON_SCELLEE",
        "scelle": False,
        "nb_entrees_aveugles": len(entrees),
        "entrees": entrees,
    }
    COLLECTE_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


if __name__ == "__main__":
    data = initialiser_collecte()
    if "--sceller" in sys.argv:
        auteurs = {e["auteur"] for e in data["entrees"]}
        if len(data["entrees"]) < 100 or "Christian_Duguay_Direct" not in auteurs:
            print(f"[REFUS DE SCELLEMENT] {len(data['entrees'])}/100 entrées, auteurs={sorted(auteurs)}. "
                  f"Scellement interdit avant >=100 entrées et contribution de Christian.")
            sys.exit(1)
    print(f"Statut : {data['statut']} ({len(data['entrees'])} entrées aveugles, scelle={data['scelle']})")
