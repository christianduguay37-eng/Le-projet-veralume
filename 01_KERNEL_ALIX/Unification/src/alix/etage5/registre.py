# -*- coding: utf-8 -*-
"""
Étage 5 — Registre vivant des 113 théorèmes de L*↑.

Une entrée par théorème : rien n'est fusionné ni résumé. Chaque entrée porte
son énoncé (tel qu'écrit dans la Spécification v4.0, ou v3.0 pour TH85–TH88
retirés), sa couche, sa section, et les verdicts produits par les
explorateurs (noyau, Hadès, extensions, bourgeons).

Le registre se reconstruit à partir du fichier de spécification ; il ne
modifie jamais la spécification elle-même.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ICI = Path(__file__).resolve().parent
REGISTRE_JSON = ICI / "registre_113.json"

# TH85–TH88 (v3.0) : retirés en v3.1, remplacés par TH89–TH93.
# Énoncés repris de la transcription du 16 nov. 2026 (Q-U).
RETIRES_V30 = {
    85: ("Fenêtre de productivité (Q-U.A)",
         "La productivité Π(σ, S) d'une semence dans un sol est maximale dans une fenêtre "
         "ν ∈ (ν_min, ν_max) de fraction-noyau et pour une fertilité φ(S) > φ_min."),
    86: ("Homogénéité nécessaire et bornée (Q-U.B)",
         "Sans racine (ν = 0) la semence est du bruit ; racine totale (ν = 1) donne une copie ; "
         "seule une racine partielle est viable."),
    87: ("Productivité par orthogonalité (Q-U.C)",
         "Deux terroirs orthogonaux produisent par croisement une semence plus productive "
         "que chacun des parents, s'ils sont dans la fenêtre."),
    88: ("Conditions de la spirale (Q-U.D)",
         "La spirale est viable ssi noyau borné, sol fertile, croisement orthogonal."),
}

SECTIONS = [
    (1, 5, "Régime saturé et Théorème de Libération", 1),
    (6, 12, "Régime de secours et périodicité forcée", 1),
    (13, 17, "Asymétrie interne et maturité historique", 1),
    (18, 24, "Ordre intrinsèque et signature complète", 1),
    (25, 27, "Transitions et fermeture", 1),
    (28, 31, "Choix, NFA et déterminisme", 1),
    (32, 38, "Robustesse temporelle et environnement réactif", 2),
    (39, 42, "Coût continu et inversion ascendante", 2),
    (43, 52, "Cordée solidaire et règle récursive", 2),
    (53, 60, "Hétérogénéité fertile et architecture cyclique", 2),
    (61, 67, "Friction productive et homéostasie", 2),
    (68, 78, "Diversité inter- et intra-systémique", 2),
    (79, 84, "Spirale végétale et forêt négentropique", 2),
    (85, 88, "Terroir et fenêtre (v3.0, retirés)", 3),
    (89, 93, "Structure double — racines et branches", 3),
    (94, 108, "Style, lisibilité et lumière", 3),
    (109, 113, "Friction rédemptrice et usine à yeux", 3),
]


def _section(n: int):
    for a, b, nom, couche in SECTIONS:
        if a <= n <= b:
            return nom, couche
    return "?", 0


def trouver_specification(depart: Optional[Path] = None) -> Optional[Path]:
    """Cherche L_Star_Specification_Consolidee_v4.0.md en remontant depuis ici."""
    p = (depart or ICI).resolve()
    for parent in [p] + list(p.parents):
        cand = parent / "L_Star_Specification_Consolidee_v4.0.md"
        if cand.exists():
            return cand
        cand = parent / "Cerveau Alix" / "L_Star_Specification_Consolidee_v4.0.md"
        if cand.exists():
            return cand
    return None


def construire(spec: Path) -> Dict:
    texte = spec.read_text(encoding="utf-8")
    th: Dict[int, Dict] = {}
    for m in re.finditer(r"\*\*TH(\d+) \((.+?)\) :\*\*\s*(.+)", texte):
        n = int(m.group(1))
        nom, couche = _section(n)
        th[n] = {"id": f"TH{n}", "titre": m.group(2).strip(), "enonce": m.group(3).strip(),
                 "source": "v4.0", "section": nom, "couche": couche, "actif": True,
                 "verdicts": []}
    for n, (titre, enonce) in RETIRES_V30.items():
        nom, couche = _section(n)
        th[n] = {"id": f"TH{n}", "titre": titre, "enonce": enonce, "source": "v3.0",
                 "section": nom, "couche": couche, "actif": False,
                 "remplace_par": ["TH89", "TH90", "TH91", "TH92", "TH93"], "verdicts": []}
    defs = {f"D{m.group(1)}": m.group(2).strip()
            for m in re.finditer(r"\*\*D(\d+) \((.+?)\) :\*\*", texte)}
    axiomes = {f"S{m.group(1)}": m.group(2).strip()
               for m in re.finditer(r"\*\*Axiome S(\d+) \((.+?)\) :\*\*", texte)}
    regles = [m.group(1).strip() for m in re.finditer(r"\*\*Règle (R-[^\s(]+)", texte)]
    manquants = [n for n in range(1, 114) if n not in th]
    return {
        "nom": "L*↑ — Spirale Négentropique de Temporia",
        "specification": str(spec),
        "construit_le": datetime.now().isoformat(timespec="seconds"),
        "compte": {"entrees": len(th), "actifs": sum(1 for t in th.values() if t["actif"]),
                   "manquants": manquants},
        "definitions": defs, "axiomes": axiomes, "regles": regles,
        "theoremes": [th[n] for n in sorted(th)],
        "meta": {
            "Q-AA": "Méta-théorème d'auto-application : le chantier est une trajectoire de L*↑ (Partie V).",
            "Omega": "L*↑ ≡ Spirale Négentropique de Temporia, N(x) = ν(R) + λ(B) + δ(style) (Partie VII).",
        },
        "lacunes_de_definition": [
            "∼ dans R-G (x ∼ c) n'est jamais défini.",
            "Aucun axiome n'interdit explicitement qu'une règle produise ∅ (TH1 l'exige).",
            "Le loquet R-Λ rend β « disponible » : force-t-il β ou laisse-t-il le choix ? (TH11, TH29)",
            "Le mécanisme M (Q-C) est-il une règle du système ou une extension ? (TH17, TH20, TH22)",
            "En L↑, A est défini par T_R = 0 alors que Ω0 a T_R = ∞ ; R-PURIF n'agit que sur R (TH41).",
            "ν, λ, δ dans N(x) n'ont pas de définition calculable (Ω).",
        ],
    }


def charger() -> Dict:
    return json.loads(REGISTRE_JSON.read_text(encoding="utf-8"))


def enregistrer(reg: Dict, chemin: Path = REGISTRE_JSON):
    chemin.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def appliquer_verdicts(reg: Dict, verdicts: List[Dict], origine: str) -> Dict:
    index = {t["id"]: t for t in reg["theoremes"]}
    hors = reg.setdefault("verdicts_hors_registre", [])
    for v in verdicts:
        base = v["th"].split("-")[0]
        entree = {"origine": origine, "verdict": v["verdict"], "note": v["note"],
                  "variante": v["th"] if v["th"] != base else None}
        for k in ("exemple", "mesures", "temoin", "bornes"):
            if k in v and v[k]:
                entree[k] = v[k]
        if base in index:
            index[base]["verdicts"].append(entree)
        else:
            hors.append(dict(entree, th=v["th"]))
    return reg
