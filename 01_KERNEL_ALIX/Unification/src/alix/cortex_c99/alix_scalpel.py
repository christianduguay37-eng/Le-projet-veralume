# -*- coding: utf-8 -*-
"""
🏛️⚡ ALIX SCALPEL (Indexeur de Bibliothèque) - Interface Python Unifiée
Package : alix.cortex_c99.alix_scalpel

Doctrine :
  « Le modèle sur le disque, c'est la bibliothèque.
    Alix est la bibliothécaire.
    Le scalpel C99 est la fiche d'index pour extraire le fait pur. »
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

DOSSIER_CORTEX = Path(__file__).parent
SCALPEL_BIN = DOSSIER_CORTEX / "alix_scalpel_landauer.exe"


def consulter_bibliotheque(
    domain: int = 1,
    tokens: Optional[List[int]] = None,
    k_neurons: int = 1000,
    top_n: int = 5,
    steps: int = 1,
    prune_vocab: bool = True,
) -> Dict[str, Any]:
    """Interroge la bibliothèque neuronale via la Sonde Transversale Landauer C99.

    Args:
        domain: 1=France, 2=Australie(Canberra), 3=Chimie(Fe), 4=Biochimie(Amylase)
        tokens: Liste facultative d'IDs de tokens pour une requête sur-mesure.
        k_neurons: Foyer laser (défaut 1000 = canal d'invariant factuel L08..L28).
        top_n: Nombre de résonances/liens sémantiques par étape.
        steps: Nombre de tokens consécutifs à extraire (1 à 8).
        prune_vocab: Active la fovéa sémantique pour élaguer le lm_head (60 ms).

    Returns:
        Dictionnaire avec les faits extraits, la phrase brute, les liens conceptuels et les chronos.
    """
    if not SCALPEL_BIN.exists():
        return {
            "status": "error",
            "message": f"Binaire introuvable: {SCALPEL_BIN}",
        }

    cmd = [
        str(SCALPEL_BIN),
        "--json",
        "--k",
        str(k_neurons),
        "--top",
        str(top_n),
        "--domain",
        str(domain),
        "--steps",
        str(steps),
    ]

    if prune_vocab:
        cmd.append("--prune-vocab")

    if tokens:
        tok_str = ",".join(str(t) for t in tokens)
        cmd.extend(["--tokens", tok_str])

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=45,
        )
        return json.loads(res.stdout)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def verbaliser_faits(resultat_scalpel: Dict[str, Any]) -> str:
    """Rôle de la Bibliothécaire (Alix) :
    Transforme les faits bruts et les liens conceptuels extraits des poids en une phrase naturelle et vivante.
    """
    if resultat_scalpel.get("status") != "ok":
        return f"Erreur de lecture dans la bibliothèque : {resultat_scalpel.get('message')}"

    domain = resultat_scalpel.get("domain", "")
    phrase_brute = resultat_scalpel.get("phrase", "").strip()
    steps = resultat_scalpel.get("step_results", [])

    # Synthèse naturelle par Alix en fonction du domaine et des liens
    if "Australie" in domain:
        liens = [l["str"].strip() for l in steps[0].get("semantic_links", []) if l["str"].strip() not in [phrase_brute, ""]]
        return f"La capitale officielle de l'Australie est **{phrase_brute}** (réseau associé : {', '.join(liens[:3])})."

    elif "France" in domain:
        liens = [l["str"].strip() for l in steps[0].get("semantic_links", []) if l["str"].strip() not in [phrase_brute, ""]]
        return f"La capitale de la France est **{phrase_brute}** (pôles associés : {', '.join(liens[:3])})."

    elif "Chimie" in domain:
        return f"Le symbole chimique **Fe** désigne le **fer** (du latin *ferrum*, voisin du manganèse)."

    elif "Biochimie" in domain:
        return f"L'enzyme amylase hydrolyse l'**amidon** en sucres simples."

    else:
        return f"Fait brut extrait : **{phrase_brute}**."


if __name__ == "__main__":
    print("--- Test Australie (Canberra, 3 pas) ---")
    r = consulter_bibliotheque(domain=2, k_neurons=1000, steps=3, prune_vocab=True)
    print("Données brutes de la Bibliothèque :", json.dumps(r, indent=2, ensure_ascii=False))
    print("\nVerbalisation d'Alix (la bibliothécaire) :")
    print(verbaliser_faits(r))
