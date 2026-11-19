import ast
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Dossiers à ignorer absolument pour ne pas fausser le compteur avec des librairies externes
IGNORE_DIRS = {
    ".git", "__pycache__", "venv", ".venv", "env", ".env",
    "node_modules", "build", "dist", ".idea", ".vscode", "site-packages"
}

# Modules standards de Python (pour les séparer des vraies dépendances pip)
STDLIB_MODULES = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set()


def hash_file(filepath: Path) -> str:
    """Calcule l'empreinte SHA-256 d'un fichier pour détecter les doublons exacts."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def count_lines(content: str) -> tuple[int, int]:
    """Retourne (lignes totales, lignes de code effectives hors vides et commentaires)."""
    lines = content.splitlines()
    total = len(lines)
    loc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
    return total, loc


def analyze_script(filepath: Path, root_dir: Path) -> dict:
    """Analyse un fichier Python via AST sans l'exécuter."""
    rel_path = str(filepath.relative_to(root_dir))
    result = {
        "path": rel_path,
        "folder": str(filepath.parent.relative_to(root_dir)),
        "total_lines": 0,
        "loc": 0,
        "sha256": "",
        "imports": [],
        "functions": [],
        "classes": [],
        "has_main": False,
        "syntax_error": None,
    }

    try:
        result["sha256"] = hash_file(filepath)
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        result["syntax_error"] = f"Erreur de lecture: {e}"
        return result

    result["total_lines"], result["loc"] = count_lines(content)

    try:
        tree = ast.parse(content, filename=rel_path)
    except SyntaxError as e:
        result["syntax_error"] = f"Ligne {e.lineno}: {e.msg}"
        return result
    except Exception as e:
        result["syntax_error"] = str(e)
        return result

    imports = set()
    functions = []
    classes = []
    has_main = False

    # Inspection du premier niveau et des nœuds globaux
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # Ignore les imports relatifs (from . import x)
                imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.If):
            # Détection de : if __name__ == "__main__":
            try:
                if (isinstance(node.test, ast.Compare)
                        and isinstance(node.test.left, ast.Name)
                        and node.test.left.id == "__name__"):
                    has_main = True
            except Exception:
                pass

    # Récupération uniquement des fonctions et classes de premier niveau (top-level)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    result["imports"] = sorted(imports)
    result["functions"] = functions
    result["classes"] = classes
    result["has_main"] = has_main
    return result


def scan_codebase(root_path: str):
    root_dir = Path(root_path).resolve()
    if not root_dir.exists():
        print(f"Erreur : Le dossier '{root_dir}' n'existe pas.")
        sys.exit(1)

    print(f"Analyse en cours dans : {root_dir} ...\n")

    py_files = []
    for path in root_dir.rglob("*.py"):
        # Vérifier qu'aucun dossier parent n'est dans la liste d'exclusion
        if not any(part in IGNORE_DIRS for part in path.parts):
            if path.name != "audit_codebase.py":
                py_files.append(path)

    scripts_data = [analyze_script(f, root_dir) for f in py_files]

    # --- Agrégation des métriques ---
    total_files = len(scripts_data)
    total_lines = sum(s["total_lines"] for s in scripts_data)
    total_loc = sum(s["loc"] for s in scripts_data)
    main_scripts = sum(1 for s in scripts_data if s["has_main"])
    syntax_errors = [s for s in scripts_data if s["syntax_error"]]

    # Noms des modules locaux (pour ne pas les compter comme librairies externes)
    local_module_names = {f.stem for f in py_files} | {f.parent.name for f in py_files}

    external_imports = Counter()
    local_imports = Counter()
    func_locations = defaultdict(list)
    class_locations = defaultdict(list)
    hash_locations = defaultdict(list)
    folder_stats = defaultdict(lambda: {"files": 0, "loc": 0})

    for s in scripts_data:
        folder_stats[s["folder"]]["files"] += 1
        folder_stats[s["folder"]]["loc"] += s["loc"]

        if s["sha256"]:
            hash_locations[s["sha256"]].append(s["path"])

        for imp in s["imports"]:
            if imp in STDLIB_MODULES:
                continue
            elif imp in local_module_names:
                local_imports[imp] += 1
            else:
                external_imports[imp] += 1

        for fn in s["functions"]:
            if not fn.startswith("_"):  # Ignore les fonctions privées internes
                func_locations[fn].append(s["path"])

        for cls in s["classes"]:
            class_locations[cls].append(s["path"])

    # Filtrage des doublons
    exact_clones = {h: paths for h, paths in hash_locations.items() if len(paths) > 1}
    duplicate_funcs = {
        fn: paths for fn, paths in sorted(func_locations.items(), key=lambda x: len(x[1]), reverse=True)
        if len(paths) > 1
    }
    duplicate_classes = {
        cls: paths for cls, paths in sorted(class_locations.items(), key=lambda x: len(x[1]), reverse=True)
        if len(paths) > 1
    }

    # --- Affichage du Rapport Console ---
    print("=" * 65)
    print("                 RAPPORT D'AUDIT DU CODE PYTHON")
    print("=" * 65)
    print(f"Fichiers Python analysés     : {total_files}")
    print(f"Lignes totales (brutes)      : {total_lines:,}")
    print(f"Lignes de code pur (LOC)     : {total_loc:,}")
    print(f"Scripts avec '__main__'      : {main_scripts} ({(main_scripts/max(1, total_files))*100:.1f}%)")
    print(f"Fichiers avec erreur syntaxe : {len(syntax_errors)}")
    print(f"Groupes de fichiers clones   : {len(exact_clones)}")
    print(f"Fonctions dupliquées (nom)   : {len(duplicate_funcs)}")
    print(f"Classes dupliquées (nom)     : {len(duplicate_classes)}")
    print("-" * 65)

    print("\n[1] TOP 10 DOSSIERS PAR VOLUME DE CODE (LOC) :")
    for folder, stats in sorted(folder_stats.items(), key=lambda x: x[1]["loc"], reverse=True)[:10]:
        print(f"  - {folder:<35} : {stats['files']:>3} fichiers | {stats['loc']:>7,} LOC")

    print("\n[2] TOP 15 DÉPENDANCES EXTERNES (hors stdlib) :")
    for imp, count in external_imports.most_common(15):
        print(f"  - {imp:<25} (utilisé dans {count} fichiers)")

    print("\n[3] TOP 15 FONCTIONS DUPLIQUÉES (Candidates pour 'common/') :")
    for fn, paths in list(duplicate_funcs.items())[:15]:
        print(f"  - def {fn}() -> définie dans {len(paths)} fichiers")

    print("\n[4] TOP 10 CLASSES DUPLIQUÉES :")
    for cls, paths in list(duplicate_classes.items())[:10]:
        print(f"  - class {cls} -> définie dans {len(paths)} fichiers")

    if exact_clones:
        print("\n[5] FICHIERS CLONES EXACTS (100% identiques) :")
        for idx, (_, paths) in enumerate(list(exact_clones.items())[:10], 1):
            print(f"  Groupe {idx} : {', '.join(paths)}")

    # Sauvegarde du rapport complet en JSON pour l'étape 2
    report_data = {
        "summary": {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_loc": total_loc,
            "main_scripts": main_scripts,
            "syntax_errors_count": len(syntax_errors),
        },
        "folder_stats": dict(folder_stats),
        "external_imports": dict(external_imports.most_common()),
        "local_imports": dict(local_imports.most_common()),
        "exact_clones": list(exact_clones.values()),
        "duplicate_functions": {k: v for k, v in list(duplicate_funcs.items())[:100]},
        "duplicate_classes": {k: v for k, v in list(duplicate_classes.items())[:100]},
        "syntax_errors": [{"path": s["path"], "error": s["syntax_error"]} for s in syntax_errors],
    }

    output_json = Path.cwd() / "rapport_audit.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print(f"Rapport détaillé sauvegardé dans : {output_json}")
    print("=" * 65)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    scan_codebase(target)
