# -*- coding: utf-8 -*-
"""
Étage 5 — L'univers des machines (L*↑), ligne de commande.

    python -m alix.etage5 explorer            # tout : noyau, Hadès, extensions, bourgeons
    python -m alix.etage5 noyau [H]           # couche 1 par énumération (H = horizon, défaut 8)
    python -m alix.etage5 hades [H]           # vérification bornée par SAT (Hadès)
    python -m alix.etage5 extensions          # couche 2 (simulations sous choix explicites)
    python -m alix.etage5 bourgeons           # couche 3 (définitions candidates, Ω)
    python -m alix.etage5 trajectoire 0010110 [n_lambda|aucun] [k]
    python -m alix.etage5 registre            # reconstruit le registre depuis la spécification
    python -m alix.etage5 theoreme TH21       # fiche d'un théorème et ses verdicts
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import registre as reg_mod

ICI = Path(__file__).resolve().parent
JOURNAL = ICI / "journal"

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _imprimer(verdicts):
    for v in verdicts:
        ex = v.get("exemple") or v.get("temoin")
        suite = f"  → {ex['objets']}" if isinstance(ex, dict) and "objets" in ex else ""
        print(f"  {v['th']:<14} {v['verdict']:<18} {v['note'][:110]}{suite}")


def _hades(H):
    from .hades_pont import chercher_B0, verifier_TH9
    res = []
    for nl in (1, 2, 3):
        r = chercher_B0(H, nl)
        res.append({"th": "TH21", "verdict": "contre_exemple" if r["sat"] else "tient",
                    "note": f"[{r['moteur']}] B0 cherché par SAT, H={H}, n_Λ={nl} : "
                            + ("témoin trouvé" if r["sat"] else "impossible dans la borne"),
                    "temoin": r["temoin"], "bornes": {"H": H, "n_lambda": nl}})
    for nl in (2, 3):
        r = verifier_TH9(H, nl)
        res.append({"th": "TH9", "verdict": "tient" if not r["sat"] else "contre_exemple",
                    "note": f"[{r['moteur']}] {r['verdict']} (H={H}, n_Λ={nl}) — UNSAT = "
                            "aucun environnement ne réfute TH9 dans la borne",
                    "temoin": r["temoin"], "bornes": {"H": H, "n_lambda": nl}})
    return res


def _registre_base():
    if reg_mod.REGISTRE_JSON.exists():
        r = reg_mod.charger()
        for t in r["theoremes"]:
            t["verdicts"] = []
        r.pop("verdicts_hors_registre", None)
        return r
    spec = reg_mod.trouver_specification()
    if spec is None:
        raise SystemExit("Spécification v4.0 introuvable et registre absent.")
    return reg_mod.construire(spec)


def explorer_tout(H=8):
    from .explorateur import explorer
    from .extensions import tout_simuler
    from .bourgeons import explorer_bourgeons
    reg = _registre_base()
    lots = [("noyau (énumération)", explorer(H)), ("Hadès (SAT borné)", _hades(H)),
            ("extensions (simulation)", tout_simuler()), ("bourgeons (couche 3)", explorer_bourgeons())]
    for origine, vs in lots:
        reg_mod.appliquer_verdicts(reg, vs, origine)
    reg["derniere_exploration"] = datetime.now().isoformat(timespec="seconds")
    reg_mod.enregistrer(reg)
    rapport = ecrire_rapport(reg, lots)
    for origine, vs in lots:
        print(f"\n== {origine}")
        _imprimer(vs)
    print(f"\nRegistre : {reg_mod.REGISTRE_JSON}\nRapport  : {rapport}")
    return reg


def ecrire_rapport(reg, lots) -> Path:
    JOURNAL.mkdir(exist_ok=True)
    horo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    lignes = [f"# Étage 5 — exploration du {horo}", "",
              f"Spécification : `{reg['specification']}`", "",
              "## Bilan par théorème", "",
              "| TH | couche | verdicts |", "|---|---|---|"]
    for t in reg["theoremes"]:
        vs = Counter(v["verdict"] for v in t["verdicts"])
        etat = ", ".join(f"{k} ×{n}" for k, n in vs.items()) or "non exploré"
        if not t["actif"]:
            etat = "retiré (v3.1) — " + etat
        lignes.append(f"| {t['id']} | {t['couche']} | {etat} |")
    lignes += ["", "## Contre-exemples et conditions", ""]
    for origine, vs in lots:
        for v in vs:
            if v["verdict"] in ("contre_exemple", "echoue_sous_choix", "conditionnel"):
                lignes.append(f"- **{v['th']}** ({origine}, {v['verdict']}) : {v['note']}")
    lignes += ["", "## Lacunes de définition", ""] + [f"- {l}" for l in reg["lacunes_de_definition"]]
    chemin = JOURNAL / f"exploration_{horo}.md"
    chemin.write_text("\n".join(lignes), encoding="utf-8")
    (JOURNAL / f"exploration_{horo}.json").write_text(
        json.dumps({origine: vs for origine, vs in lots}, ensure_ascii=False, indent=1), encoding="utf-8")
    return chemin


def main(argv):
    cmd = argv[0] if argv else "explorer"
    if cmd == "explorer":
        explorer_tout(int(argv[1]) if len(argv) > 1 else 8)
    elif cmd == "noyau":
        from .explorateur import explorer
        _imprimer(explorer(int(argv[1]) if len(argv) > 1 else 8))
    elif cmd == "hades":
        _imprimer(_hades(int(argv[1]) if len(argv) > 1 else 8))
    elif cmd == "extensions":
        from .extensions import tout_simuler
        _imprimer(tout_simuler())
    elif cmd == "bourgeons":
        from .bourgeons import explorer_bourgeons
        _imprimer(explorer_bourgeons())
    elif cmd == "trajectoire":
        from .noyau import Interpretation, derouler
        env = [int(c) for c in argv[1]]
        nl = None if len(argv) > 2 and argv[2] == "aucun" else (int(argv[2]) if len(argv) > 2 else 2)
        k = int(argv[3]) if len(argv) > 3 else 1
        print(json.dumps(derouler(env, Interpretation(n_lambda=nl, nb_attracteurs=k)).resume(),
                         ensure_ascii=False, indent=1))
    elif cmd == "registre":
        spec = reg_mod.trouver_specification()
        if spec is None:
            raise SystemExit("Spécification v4.0 introuvable.")
        r = reg_mod.construire(spec)
        reg_mod.enregistrer(r)
        print(json.dumps(r["compte"], ensure_ascii=False))
    elif cmd == "theoreme":
        r = reg_mod.charger()
        t = next((t for t in r["theoremes"] if t["id"] == argv[1]), None)
        print(json.dumps(t, ensure_ascii=False, indent=1) if t else "inconnu")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
