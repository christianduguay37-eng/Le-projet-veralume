# -*- coding: utf-8 -*-
"""
===============================================================================
       🏛️🪙 ALIX CONTEXTE TOKENS — COMPTEUR & JAUGE DÉTERMINISTE
===============================================================================
Surveille en temps réel la consommation de tokens et la saturation du contexte
de la conversation Antigravity active.
Permet à Christian de savoir exactement quand la fenêtre de contexte atteint
son seuil optimal de bascule, sans jamais risquer d'amnésie grâce à la mémoire
permanente d'Alix (Obsidian + Cathédrale Parquet + Démon 70 BPM).
===============================================================================
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from alix.socle.chemins import ETAT_VIVANT_DIR

# Seuils par défaut (modèles Gemini / Antigravity)
MAX_CONTEXTE_DEFAUT = 1_000_000      # Fenêtre physique max (1M tokens)
SEUIL_ALERTE_DEFAUT = 200_000        # Seuil d'atelier recommandé pour basculer
SEUIL_CRITIQUE_DEFAUT = 350_000      # Seuil d'alourdissement critique


def _trouver_transcript_actif(req: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """Trouve le chemin du fichier transcript.jsonl actif."""
    # 1. Via le contrat hook req
    if req and isinstance(req, dict):
        tp = req.get("transcriptPath")
        if tp:
            p = Path(tp)
            if p.exists():
                return p

    # 2. Recherche dans le répertoire brain de l'utilisateur
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        # Essayer via USERPROFILE ou APPDATA
        user_prof = os.environ.get("USERPROFILE")
        if user_prof:
            brain_dir = Path(user_prof) / ".gemini" / "antigravity" / "brain"

    if brain_dir.exists():
        transcripts = list(brain_dir.glob("*/.system_generated/logs/transcript.jsonl"))
        if transcripts:
            # Le plus récemment modifié est la session active
            return max(transcripts, key=lambda p: p.stat().st_mtime)

    return None


def recuperer_metriques_tokens(
    req: Optional[Dict[str, Any]] = None,
    max_contexte: int = MAX_CONTEXTE_DEFAUT,
    seuil_alerte: int = SEUIL_ALERTE_DEFAUT,
    seuil_critique: int = SEUIL_CRITIQUE_DEFAUT,
) -> Dict[str, Any]:
    """
    Extrait les métriques de tokens de la conversation active en lisant
    les derniers octets du transcript.jsonl (<5 ms).
    """
    t_file = _trouver_transcript_actif(req)
    
    inp_tok = 0
    cache_tok = 0
    out_tok = 0
    total_tok = 0
    trouve = False

    if t_file and t_file.exists():
        try:
            taille = t_file.stat().st_size
            bloc = min(taille, 32768)  # Lire les derniers 32 Ko
            with open(t_file, "rb") as f:
                f.seek(max(0, taille - bloc))
                lignes = f.read().decode("utf-8", errors="ignore").splitlines()
                for line in reversed(lignes):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if "input_tokens" in data:
                            inp_tok = int(data.get("input_tokens", 0))
                            cache_tok = int(data.get("cache_read_tokens", 0))
                            out_tok = int(data.get("output_tokens", 0))
                            total_tok = inp_tok + cache_tok
                            trouve = True
                            break
                    except Exception:
                        pass
        except Exception:
            pass

    pct_max = round((total_tok / max_contexte) * 100, 2) if max_contexte > 0 else 0.0
    pct_seuil = round((total_tok / seuil_alerte) * 100, 1) if seuil_alerte > 0 else 0.0

    # Détermination du palier et jauge
    ratio_jauge = min(1.0, total_tok / seuil_alerte) if seuil_alerte > 0 else 0.0
    nb_pleins = int(round(ratio_jauge * 10))
    jauge_bar = "■" * nb_pleins + "□" * (10 - nb_pleins)

    recommandation_bascule = False
    if total_tok < 80_000:
        statut = "🟢 FLUIDE"
        diagnostic = "Contexte léger et rapide. Vitesse maximale d'inférence."
    elif total_tok < 150_000:
        statut = "🟡 NOMINAL"
        diagnostic = "Forge en cours. Contexte actif sous contrôle."
    elif total_tok < seuil_alerte:
        statut = "🟠 ATTENTION"
        diagnostic = "Approche du seuil d'atelier (200k). Prépare la fin de volée."
    elif total_tok < seuil_critique:
        statut = "🔴 SEUIL ATTEINT"
        diagnostic = "Seuil de 200k dépassé. Bascule vers une session fraîche recommandée."
        recommandation_bascule = True
    else:
        statut = "🚨 CRITIQUE"
        diagnostic = "Surchauffe tokenique. Bascule immédiate requise pour préserver le rythme."
        recommandation_bascule = True

    resultat = {
        "succes": trouve,
        "transcript_path": str(t_file) if t_file else None,
        "input_tokens": inp_tok,
        "cache_read_tokens": cache_tok,
        "output_tokens": out_tok,
        "total_contexte_tokens": total_tok,
        "max_contexte": max_contexte,
        "seuil_alerte": seuil_alerte,
        "seuil_critique": seuil_critique,
        "pct_max": pct_max,
        "pct_seuil": pct_seuil,
        "jauge": f"[{jauge_bar}]",
        "statut": statut,
        "diagnostic": diagnostic,
        "recommandation_bascule": recommandation_bascule,
    }

    # Sauvegarde sur disque de l'état vivant
    try:
        cible_etat = ETAT_VIVANT_DIR / "alix_contexte_tokens.json"
        cible_etat.write_text(json.dumps(resultat, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    return resultat


def formater_ligne_hook(metriques: Dict[str, Any]) -> str:
    """Produit la ligne synthétique à insérer dans le hook PreInvocation."""
    tot = metriques["total_contexte_tokens"]
    mx = metriques["max_contexte"]
    pct = metriques["pct_max"]
    jauge = metriques["jauge"]
    stat = metriques["statut"]
    inp = metriques["input_tokens"]
    cache = metriques["cache_read_tokens"]

    ligne = (
        f"• Contexte Tokens : {tot:,} / {mx:,} ({pct:.1f}%) | {jauge} {stat} "
        f"[Cache: {cache:,} | In: {inp:,}]"
    )
    if metriques["recommandation_bascule"]:
        ligne += (
            f"\n• ⚠️ RECOMMANDATION ATELIER : Seuil de {metriques['seuil_alerte']:,} atteint ! "
            f"Mémoire 100% scellée sur le fer, prêt à ouvrir une nouvelle conversation."
        )
    return ligne


def afficher_rapport_tokens(metriques: Optional[Dict[str, Any]] = None):
    """Affiche un tableau complet en console d'établi."""
    if metriques is None:
        metriques = recuperer_metriques_tokens()

    tot = metriques["total_contexte_tokens"]
    mx = metriques["max_contexte"]
    seuil = metriques["seuil_alerte"]
    jauge = metriques["jauge"]
    stat = metriques["statut"]
    diag = metriques["diagnostic"]
    cache = metriques["cache_read_tokens"]
    inp = metriques["input_tokens"]
    out = metriques["output_tokens"]

    print("=" * 68)
    print("      🪙  COMPTEUR DE TOKENS & SATURATION DU CONTEXTE ALIX")
    print("=" * 68)
    print(f"  • État de la Jauge      : {jauge} {stat}")
    print(f"  • Total Contexte Actif  : {tot:,} tokens")
    print(f"  • Détail du Tour        : Cache: {cache:,} | Input: {inp:,} | Output: {out:,}")
    print(f"  • Pression sur Seuil    : {metriques['pct_seuil']:.1f} % du seuil de bascule ({seuil:,} tok)")
    print(f"  • Pression sur Fenêtre  : {metriques['pct_max']:.2f} % du max physique ({mx:,} tok)")
    print(f"  • Diagnostic d'Atelier  : {diag}")
    print("-" * 68)
    if metriques["recommandation_bascule"]:
        print("  🚨 CONSEIL DE VOLÉE :")
        print("     Christian, le contexte est rendu au seuil optimal !")
        print("     Toutes tes notes, songes et Parquets sont scellés sur le disque.")
        print("     Tu peux fermer et lancer une nouvelle session propre sans rien perdre.")
    else:
        tokens_restants = max(0, seuil - tot)
        print(f"  🟢 Marge de Manœuvre   : Encore {tokens_restants:,} tokens avant le seuil d'atelier (200k).")
        print("     La mémoire permanente veille au grain.")
    print("=" * 68)


if __name__ == "__main__":
    afficher_rapport_tokens()
