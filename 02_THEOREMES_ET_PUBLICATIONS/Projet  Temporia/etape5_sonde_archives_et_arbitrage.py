import ast
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()
ACTIVE_DIR = ROOT / "_Unification_Alix" / "src" / "alix"
ARCHIVE_DIR = ROOT / "_Archives_Exocerveau_Legacy_20261025"

# Fonctions génériques à ignorer pour ne pas fausser la détection d'unicité
GENERIC_NAMES = {
    "main", "__init__", "run", "start", "stop", "test", "setup",
    "charger_etat", "sauvegarder_etat", "log_message", "charger_configuration",
    "sauvegarder_configuration"
}


def extract_signatures(filepath: Path) -> dict:
    """Extrait les classes, méthodes et fonctions d'un fichier Python avec leur taille (LOC)."""
    info = {"classes": {}, "functions": {}, "loc": 0, "error": None}
    if not filepath.exists():
        info["error"] = "Fichier introuvable"
        return info

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        # Nettoyage BOM éventuel en mémoire
        if content.startswith("\ufeff"):
            content = content[1:]
        info["loc"] = sum(1 for line in content.splitlines() if line.strip() and not line.strip().startswith("#"))
        tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        info["error"] = str(e)
        return info

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_") and node.name not in GENERIC_NAMES:
                end_line = getattr(node, "end_lineno", node.lineno)
                info["functions"][node.name] = end_line - node.lineno + 1
        elif isinstance(node, ast.ClassDef):
            end_line = getattr(node, "end_lineno", node.lineno)
            methods = [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_")
            ]
            info["classes"][node.name] = {
                "lines": end_line - node.lineno + 1,
                "methods": methods
            }
    return info


def scan_archives_for_grafts():
    print("=" * 70)
    print("  1. SONDE DES ARCHIVES : DÉTECTION DES PÉPITES À GREFFER")
    print("=" * 70)

    if not ACTIVE_DIR.exists() or not ARCHIVE_DIR.exists():
        print("Erreur : Dossier _Unification_Alix ou _Archives_Exocerveau_Legacy introuvable.")
        return None

    # 1.Construire le catalogue ADN du système actif (142 fichiers)
    active_classes = {}
    active_functions = {}
    active_stems = set()

    for py_file in ACTIVE_DIR.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        active_stems.add(py_file.stem)
        sig = extract_signatures(py_file)
        rel = str(py_file.relative_to(ACTIVE_DIR))
        for cls_name in sig["classes"]:
            active_classes[cls_name] = rel
        for fn_name in sig["functions"]:
            active_functions[fn_name] = rel

    # 2. Analyser chaque fichier des archives par rapport à l'ADN actif
    pure_gems = []        # 100% inédit (aucun équivalent dans l'actif)
    partial_grafts = []   # Fichier remplacé mais contient des fonctions/classes uniques
    fully_obsolete = []   # 100% déjà présent dans l'actif

    for arch_file in sorted(ARCHIVE_DIR.rglob("*.py")):
        rel_arch = str(arch_file.relative_to(ARCHIVE_DIR))
        sig = extract_signatures(arch_file)

        if sig["error"]:
            continue

        unique_cls = [c for c in sig["classes"] if c not in active_classes]
        shared_cls = [c for c in sig["classes"] if c in active_classes]

        unique_fns = [f for f in sig["functions"] if f not in active_functions]
        shared_fns = [f for f in sig["functions"] if f in active_functions]

        total_items = len(sig["classes"]) + len(sig["functions"])
        unique_items = len(unique_cls) + len(unique_fns)

        entry = {
            "path": rel_arch,
            "stem": arch_file.stem,
            "loc": sig["loc"],
            "unique_classes": unique_cls,
            "unique_functions": unique_fns,
            "shared_classes": shared_cls,
            "shared_functions": shared_fns,
        }

        if arch_file.stem in active_stems or (unique_items == 0 and total_items > 0):
            fully_obsolete.append(entry)
        elif unique_items == total_items and sig["loc"] > 20:
            pure_gems.append(entry)
        elif unique_items > 0:
            partial_grafts.append(entry)
        else:
            fully_obsolete.append(entry)

    print(f"\n[A] PÉPITES ISOLÉES (100% absentes de l'architecture active : {len(pure_gems)} fichiers)")
    print("    Ces scripts contiennent une logique qui n'a été reprise nulle part ailleurs :")
    for gem in sorted(pure_gems, key=lambda x: x["loc"], reverse=True):
        cls_str = f"Classes: {', '.join(gem['unique_classes'][:4])}" if gem["unique_classes"] else ""
        fn_str = f"Fonctions: {', '.join(gem['unique_functions'][:5])}" if gem["unique_functions"] else ""
        sep = " | " if cls_str and fn_str else ""
        print(f"  * {gem['path']:<58} ({gem['loc']:>4} LOC)")
        if cls_str or fn_str:
            print(f"      -> {cls_str}{sep}{fn_str}")

    print(f"\n[B] GREFFONS PARTIELS ({len(partial_grafts)} fichiers)")
    print("    Anciennes versions qui possèdent encore des fonctions/classes uniques non migrées :")
    for pg in sorted(partial_grafts, key=lambda x: len(x["unique_classes"]) + len(x["unique_functions"]), reverse=True):
        u_items = pg["unique_classes"] + pg["unique_functions"]
        print(f"  * {pg['path']:<58} ({pg['loc']:>4} LOC)")
        print(f"      -> Inédit à récupérer : {', '.join(u_items[:6])}")

    print(f"\n[C] ARCHIVES 100% OBSOLÈTES ({len(fully_obsolete)} fichiers déjà remplacés ou doublons purs)")

    return {"pure_gems": pure_gems, "partial_grafts": partial_grafts, "obsolete": fully_obsolete}


def compare_active_duplicates():
    print("\n" + "=" * 70)
    print("  2. ARBITRAGE DES DOUBLONS DANS LE SYSTÈME ACTIF (_Unification_Alix)")
    print("=" * 70)

    pairs = [
        (
            "Moteur Déductif Causal vs Poseidon v10",
            ACTIVE_DIR / "solveurs" / "alix_moteur_deductif_causal.py",
            ACTIVE_DIR / "solveurs" / "alix_moteur_deductif_poseidon_v10.py",
        ),
        (
            "Moteur Fractal (veralume_core_engine vs capacité four_micro_ondes)",
            ACTIVE_DIR / "solveurs" / "veralume_core_engine.py",
            ACTIVE_DIR / "capacites" / "capacite_four_micro_ondes_deduction_fractale.py",
        ),
        (
            "Organismes Vocaux (Fusion vs V4)",
            ACTIVE_DIR / "capteurs" / "alix_vocal_organism_fusion.py",
            ACTIVE_DIR / "capteurs" / "alix_vocal_organism_v4.py",
        ),
        (
            "Communication Telegram (Daemon vs Passerelle)",
            ACTIVE_DIR / "daemons" / "alix_daemon_communication_distante.py",
            ACTIVE_DIR / "daemons" / "alix_passerelle_telegram.py",
        ),
        (
            "Sondes Scientifiques (Turing vs Landauer)",
            ACTIVE_DIR / "sondes" / "alix_sonde_auto_organisation_turing.py",
            ACTIVE_DIR / "sondes" / "alix_sonde_transversale_landauer.py",
        ),
    ]

    for title, file_a, file_b in pairs:
        print(f"\n---> {title} :")
        sig_a = extract_signatures(file_a)
        sig_b = extract_signatures(file_b)

        if sig_a["error"] or sig_b["error"]:
            print(f"     Un des fichiers n'est pas à cet emplacement ({file_a.name} / {file_b.name})")
            continue

        set_a = set(sig_a["classes"].keys()) | set(sig_a["functions"].keys())
        set_b = set(sig_b["classes"].keys()) | set(sig_b["functions"].keys())

        common = set_a & set_b
        only_a = set_a - set_b
        only_b = set_b - set_a

        print(f"  [1] {file_a.name:<45} : {sig_a['loc']:>4} LOC | {len(set_a)} composants")
        print(f"  [2] {file_b.name:<45} : {sig_b['loc']:>4} LOC | {len(set_b)} composants")
        print(f"      - En commun          : {len(common)} ({', '.join(list(common)[:5])}...)")
        print(f"      - Exclusif à [1]     : {', '.join(only_a) if only_a else 'Rien (100% inclus dans [2])'}")
        print(f"      - Exclusif à [2]     : {', '.join(only_b) if only_b else 'Rien (100% inclus dans [1])'}")


if __name__ == "__main__":
    arch_report = scan_archives_for_grafts()
    compare_active_duplicates()

    out_file = ROOT / "_Unification_Alix" / "rapport_greffons_archives.json"
    if arch_report and out_file.parent.exists():
        out_file.write_text(json.dumps(arch_report, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n" + "=" * 70)
        print(f"Rapport complet sauvegardé dans : {out_file}")
        print("=" * 70)
