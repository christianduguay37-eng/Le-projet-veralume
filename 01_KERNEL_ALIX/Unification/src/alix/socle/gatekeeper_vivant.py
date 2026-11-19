# -*- coding: utf-8 -*-
"""
Gatekeeper KAIROS V6 branché sur la boucle vivante (rénovation 2026-10-30, chantiers 3.1 à 3.3).

Avant : `GatekeeperEngine` existait dans veralume_core_engine.py mais rien ne l'appelait,
et σ n'était jamais mesuré.

Maintenant, après chaque réponse du noyau :
  1. FC (clôture forcée) est ESTIMÉ à partir des marqueurs de certitude du texte.
  2. Si FC dépasse le seuil, σ (dispersion) est MESURÉ : le même prompt est relancé
     N fois à température 0,9 et on mesure l'écart lexical entre les réponses.
     (σ n'est mesuré que si la réponse est affirmative : sinon c'est du calcul pour rien.)
  3. Le tuple KAIROS V6 est construit et passé à GatekeeperEngine.

Une réponse BLOCKED n'est pas supprimée : elle est marquée, Christian voit l'avertissement,
et elle n'est pas gravée dans Obsidian (VCp1c : l'humain tranche).

Réglages (variables d'environnement) :
  ALIX_SIGMA_PASSES   nombre de relances pour σ (défaut 2 ; 0 = σ non mesuré)
  ALIX_FC_SEUIL       seuil FC (défaut 0.50)
  ALIX_SIGMA_SEUIL    seuil σ (défaut 0.20)
"""
import os
import re
from typing import Any, Callable, Dict, List, Optional

from alix.solveurs.veralume_core_engine import GatekeeperEngine, KairosV6Tuple

MARQUEURS_CERTITUDE = [
    "certainement", "absolument", "sans aucun doute", "c'est prouvé", "prouvé", "démontré",
    "garanti", "toujours", "jamais", "100 %", "100%", "exactement", "forcément", "indéniable",
    "il est certain", "évidemment", "de façon définitive", "sans exception",
]
MARQUEURS_PRUDENCE = [
    "peut-être", "probablement", "je pense", "il semble", "hypothèse", "à vérifier", "incertain",
    "je ne sais pas", "possible", "pourrait", "il se peut", "à confirmer", "selon moi", "je crois",
]
RE_MOT = re.compile(r"[a-zA-ZÀ-ÿ0-9]{3,}")


def estimer_fc(texte: str) -> float:
    """FC estimé dans [0, 1] : part des marqueurs de certitude parmi les marqueurs d'épistémè."""
    t = texte.lower()
    a = sum(t.count(m) for m in MARQUEURS_CERTITUDE)
    p = sum(t.count(m) for m in MARQUEURS_PRUDENCE)
    if a == 0:
        return 0.0
    return round(a / (a + p + 1.0), 3)


def _jaccard(x: set, y: set) -> float:
    if not x and not y:
        return 1.0
    return len(x & y) / max(1, len(x | y))


def mesurer_sigma(reponses: List[str]) -> float:
    """σ dans [0, 1] : 1 − similarité lexicale moyenne entre toutes les paires de réponses."""
    ens = [set(m.lower() for m in RE_MOT.findall(r)) for r in reponses if r]
    if len(ens) < 2:
        return 0.0
    sims = [_jaccard(ens[i], ens[j]) for i in range(len(ens)) for j in range(i + 1, len(ens))]
    return round(1.0 - sum(sims) / len(sims), 3)


def evaluer_reponse(
    texte: str,
    relancer: Optional[Callable[[], str]] = None,
    domaine: str = "dialogue",
    section: str = "noyau",
) -> Dict[str, Any]:
    """Construit le tuple KAIROS V6 de la réponse et renvoie le verdict du gatekeeper."""
    seuil_fc = float(os.environ.get("ALIX_FC_SEUIL", "0.50"))
    seuil_sigma = float(os.environ.get("ALIX_SIGMA_SEUIL", "0.20"))
    n_passes = int(os.environ.get("ALIX_SIGMA_PASSES", "2"))

    fc = estimer_fc(texte)
    sigma: Optional[float] = None
    if fc > seuil_fc and relancer is not None and n_passes > 0:
        echantillons = [texte]
        for _ in range(n_passes):
            try:
                echantillons.append(relancer())
            except Exception:
                break
        if len(echantillons) >= 2:
            sigma = mesurer_sigma(echantillons)

    tup = KairosV6Tuple(
        domain=domaine, pathology="aucune", severity="p2",
        sigma=sigma if sigma is not None else 0.0, delta=0.0, fc=fc,
        activation="post_generation", requires="", prevents="certainty_hallucination",
        fix="vcp1c_audit", section=section,
    )
    verdict = GatekeeperEngine(fc_threshold=seuil_fc, sigma_threshold=seuil_sigma).evaluate(tup)
    if fc > seuil_fc and sigma is None:
        # Réponse affirmative mais σ non mesuré : on ne prétend pas l'avoir validée.
        verdict["status"] = "NON_MESURE"
        verdict["reason"] = f"FC={fc:.2f} au-dessus du seuil, σ non mesuré (ALIX_SIGMA_PASSES=0 ou modèle indisponible)."
    verdict["fc"] = fc
    verdict["sigma"] = sigma
    verdict["sigma_mesure"] = sigma is not None
    verdict["tuple"] = tup.to_vector_string()
    return verdict
