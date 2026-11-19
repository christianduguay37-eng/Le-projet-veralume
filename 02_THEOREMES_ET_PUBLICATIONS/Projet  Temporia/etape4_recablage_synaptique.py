import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()
TARGET_ROOT = ROOT / "_Unification_Alix"
PKG_DIR = TARGET_ROOT / "src" / "alix"


def build_module_registry() -> dict[str, str]:
    """
    Construit l'annuaire complet de tous les modules présents dans src/alix/.
    Retourne un dictionnaire : { "nom_du_script": "alix.organe.nom_du_script" }
    """
    registry = {}
    for py_file in PKG_DIR.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel = py_file.relative_to(PKG_DIR)
        # Exemple: solveurs/alix_dpll_t_solver_hades.py -> alix.solveurs.alix_dpll_t_solver_hades
        parts = list(rel.parts[:-1]) + [py_file.stem]
        full_import_path = "alix." + ".".join(parts)
        registry[py_file.stem] = full_import_path
    return registry


def rewrite_imports_in_file(filepath: Path, registry: dict[str, str]) -> list[str]:
    """
    Analyse et remplace proprement les imports locaux dans un fichier Python.
    Retourne la liste des modifications effectuées.
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    changes = []

    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError as e:
        return [f"[ERREUR SYNTAXE INITIALE] Ligne {e.lineno}: {e.msg}"]

    # Collecter les remplacements par numéro de ligne (1-indexed)
    # On ne traite que les imports qui tiennent sur une seule ligne pour éviter tout risque
    line_replacements = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if getattr(node, "end_lineno", node.lineno) != node.lineno:
                continue
            lineno = node.lineno - 1
            orig_line = lines[lineno]
            indent = re.match(r"^\s*", orig_line).group(0)

            # Si c'est un import simple d'un module local connu : `import mod_x` ou `import mod_x as mx`
            if len(node.names) == 1:
                alias = node.names[0]
                base_mod = alias.name.split(".")[-1]
                if base_mod in registry and base_mod != filepath.stem:
                    full_path = registry[base_mod]
                    parent_pkg = ".".join(full_path.split(".")[:-1])
                    if alias.asname:
                        new_line = f"{indent}from {parent_pkg} import {base_mod} as {alias.asname}\n"
                    else:
                        new_line = f"{indent}from {parent_pkg} import {base_mod}\n"
                    if new_line != orig_line:
                        line_replacements[lineno] = (orig_line.strip(), new_line)

        elif isinstance(node, ast.ImportFrom):
            if getattr(node, "end_lineno", node.lineno) != node.lineno:
                continue
            if not node.module:
                continue

            lineno = node.lineno - 1
            orig_line = lines[lineno]

            # Récupère le nom du module cible (ex: Organes_Souverains.Moteurs.alix_x -> alix_x)
            target_mod = node.module.split(".")[-1]

            if target_mod in registry and target_mod != filepath.stem:
                new_mod_path = registry[target_mod]
                if node.module != new_mod_path:
                    # Remplace uniquement la cible du `from <ancien> import ...`
                    pattern = r"^(\s*from\s+)" + re.escape(node.module) + r"(\s+import\s+.*)$"
                    match = re.match(pattern, orig_line.rstrip("\r\n"))
                    if match:
                        new_line = f"{match.group(1)}{new_mod_path}{match.group(2)}\n"
                        line_replacements[lineno] = (orig_line.strip(), new_line)

    if not line_replacements:
        return []

    # Appliquer les remplacements
    new_lines = list(lines)
    for lineno, (old_str, new_line) in line_replacements.items():
        new_lines[lineno] = new_line
        changes.append(f"L.{lineno+1}: `{old_str}` -> `{new_line.strip()}`")

    new_content = "".join(new_lines)

    # Vérification de sécurité AST : on ne sauvegarde QUE si la syntaxe finale est 100% valide
    try:
        ast.parse(new_content, filename=str(filepath))
        filepath.write_text(new_content, encoding="utf-8")
    except SyntaxError as e:
        return [f"[ANNULÉ - SÉCURITÉ AST] {e}"]

    return changes


def run_synaptic_rewiring():
    if not PKG_DIR.exists():
        print(f"Erreur : Le dossier {PKG_DIR} n'existe pas.")
        return

    registry = build_module_registry()
    print("=" * 65)
    print(f"   RECÂBLAGE SYNAPTIQUE DE L'ARCHITECTURE ALIX ({len(registry)} modules)")
    print("=" * 65)

    total_files_modified = 0
    total_imports_rewired = 0
    detailed_log = {}

    for py_file in sorted(PKG_DIR.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        changes = rewrite_imports_in_file(py_file, registry)
        if changes:
            rel_path = str(py_file.relative_to(PKG_DIR))
            detailed_log[rel_path] = changes
            total_files_modified += 1
            total_imports_rewired += len(changes)
            print(f"\n[MODIFIÉ] alix/{rel_path} ({len(changes)} imports) :")
            for c in changes:
                print(f"   {c}")

    # Audit final de compilation sur l'intégralité des 142 fichiers
    syntax_ok = 0
    syntax_fail = []
    for py_file in PKG_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            compile(content, str(py_file), "exec")
            syntax_ok += 1
        except Exception as e:
            syntax_fail.append((str(py_file.relative_to(PKG_DIR)), str(e)))

    print("\n" + "=" * 65)
    print("                 BILAN DU RECÂBLAGE SYNAPTIQUE")
    print("=" * 65)
    print(f"Modules enregistrés dans l'annuaire : {len(registry)}")
    print(f"Fichiers recâblés automatiquement   : {total_files_modified}")
    print(f"Lignes d'imports mises à jour       : {total_imports_rewired}")
    print(f"Validation compilateur Python (AST) : {syntax_ok}/{syntax_ok + len(syntax_fail)} fichiers 100% valides")
    if syntax_fail:
        print("\nErreurs détectées :")
        for path, err in syntax_fail:
            print(f"  - {path} : {err}")
    print("=" * 65)

    log_path = TARGET_ROOT / "rapport_recablage.json"
    log_path.write_text(json.dumps(detailed_log, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    run_synaptic_rewiring()
