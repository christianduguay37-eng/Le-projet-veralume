import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()
TARGET_ROOT = ROOT / "_Unification_Alix"
PKG_DIR = TARGET_ROOT / "src" / "alix"

# Dossiers à ignorer lors de la migration vers le nouveau package actif
IGNORE_DIRS = {
    "_Archives_Exocerveau_Legacy_20261025",
    "_Unification_Alix",
    ".git", "__pycache__", "venv", ".venv", "env"
}

# Scripts d'audit temporaires à ne pas migrer
IGNORE_FILES = {
    "audit_codebase.py",
    "etape2_nettoyage_et_comparaison.py",
    "etape3_batisseur_architecture.py",
}


def fix_bom_if_present(filepath: Path) -> bool:
    """Supprime le caractère invisible U+FEFF (UTF-8 BOM) en début de fichier."""
    if not filepath.exists():
        return False
    raw = filepath.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        filepath.write_bytes(raw[3:])
        return True
    return False


def classify_moteur(filename: str) -> str:
    """Route intelligemment les 78 fichiers du dossier Moteurs vers le bon sous-package."""
    name = filename.lower()

    # 1. Solveurs (Maths, Logique formelle, Déduction, SMT, AST, LMH)
    if any(k in name for k in [
        "deductif", "poseidon", "dpll", "smt", "maxsat", "hades",
        "lmh", "simplex", "fractal", "cegis", "ast_repairs", "dictionnaire_math",
        "compilateur", "stratified_oracle", "r0_ontological"
    ]):
        return "solveurs"

    # 2. Substrat (Hardware, NPU, CPU AVX2, GPU, RAM, Télémétrie)
    if any(k in name for k in [
        "avx2", "npu", "gpu", "telemetry", "pont_cpu", "hardware",
        "lunar", "synchrone_ram", "bunker_local", "noyau_resident"
    ]):
        return "substrat"

    # 3. Sondes (Recherche Web, ArXiv, Cathédrale, Mémoire, Turing, Landauer, Veilles)
    if any(k in name for k in [
        "sonde", "sonar", "arxiv", "cathedrale", "memoire", "quete_diurne",
        "turing", "landauer", "encyclopedie", "bibliothecaire", "synchro_discussions"
    ]):
        return "sondes"

    # 4. Daemons & Boucliers PSI (Processus résidents, Telegram, Argus, Sécurité)
    if any(k in name for k in [
        "daemon", "demon", "heartbeat", "telegram", "passerelle", "notifier",
        "psi", "bouclier", "sentinelle", "sentinel", "defense", "tripwires",
        "reverse_safety", "serveur", "argus"
    ]):
        return "daemons"

    # Par défaut, si un moteur est purement algorithmique ou transversal
    return "solveurs"


def determine_destination(filepath: Path) -> str:
    """Détermine dans quel sous-package de `src/alix/` va chaque fichier."""
    rel = filepath.relative_to(ROOT)
    parts = rel.parts
    filename = filepath.name

    # Dossiers explicites
    if "Capacites_Live" in parts:
        return "capacites"
    if "Capteurs" in parts:
        return "capteurs"
    if "Pantheon" in parts:
        return "pantheon"
    if "Simulateur_Electoral_Souverain" in parts or "Leurres_Souverains" in parts:
        return "simulateurs"
    if "Moteurs" in parts:
        return classify_moteur(filename)

    # Fichiers à la racine "."
    name_low = filename.lower()
    if "dispatcher" in name_low:
        return "capacites"
    if "fractal" in name_low or "lmh" in name_low or "core_engine" in name_low:
        return "solveurs"
    return "socle"


def create_scaffold():
    """Crée l'arborescence complète et les fichiers d'initialisation."""
    subpackages = [
        "socle", "solveurs", "substrat", "sondes",
        "daemons", "capteurs", "pantheon", "capacites", "simulateurs"
    ]

    for sub in subpackages:
        sub_dir = PKG_DIR / sub
        sub_dir.mkdir(parents=True, exist_ok=True)
        init_file = sub_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""Sous-package Alix : {sub.upper()}"""\n', encoding="utf-8")

    # Dossiers de données et logs hors du code
    (TARGET_ROOT / "data" / "etats").mkdir(parents=True, exist_ok=True)
    (TARGET_ROOT / "logs").mkdir(parents=True, exist_ok=True)

    # __init__.py principal
    (PKG_DIR / "__init__.py").write_text(
        '"""Package Unifié Alix / VERALUME."""\n__version__ = "1.0.0"\n',
        encoding="utf-8"
    )

    # 1. Création de pyproject.toml
    pyproject_content = """[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "alix-veralume"
version = "1.0.0"
description = "Architecture cognitive et moteurs unifiés Alix / VERALUME"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "numpy",
    "pyarrow",
    "requests",
    "psutil",
    "Pillow",
]

[project.optional-dependencies]
audio_vision = ["faster-whisper", "pyaudio", "vosk", "edge-tts", "pygame", "sounddevice", "soundfile"]
npu_ia = ["onnxruntime", "openvino", "scikit-learn", "scipy", "pandas"]

[project.scripts]
alix-cli = "alix.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
"""
    (TARGET_ROOT / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # 2. Création du socle commun unifié (socle/etat_commun.py)
    socle_etat_content = '''"""
Socle Commun : Gestion unifiée de la persistance d'état (remplace les 8 doublons de charger_etat/sauvegarder_etat).
"""
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "etats"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def charger_etat(nom_module: str, defaut: dict[str, Any] | None = None) -> dict[str, Any]:
    """Charge l'état JSON d'un module ou d'une capacité de manière sécurisée."""
    fichier = DATA_DIR / f"{nom_module}.json"
    if not fichier.exists():
        return defaut if defaut is not None else {}
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except Exception:
        return defaut if defaut is not None else {}


def sauvegarder_etat(nom_module: str, etat: dict[str, Any]) -> bool:
    """Sauvegarde l'état JSON d'un module de manière atomique."""
    fichier = DATA_DIR / f"{nom_module}.json"
    temp = DATA_DIR / f"{nom_module}.tmp"
    try:
        temp.write_text(json.dumps(etat, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(fichier)
        return True
    except Exception:
        return False
'''
    (PKG_DIR / "socle" / "etat_commun.py").write_text(socle_etat_content, encoding="utf-8")

    # 3. Création du point d'entrée CLI unifié (alix/cli.py)
    cli_content = '''"""
Point d'entrée CLI unifié pour Alix / VERALUME.
Permet de lister et d'exécuter n'importe quel module ou capacité sans chercher les scripts.
"""
import argparse
import importlib
import pkgutil
import sys
from pathlib import Path


def lister_modules():
    base_dir = Path(__file__).parent
    print("=" * 60)
    print("        ARCHITECTURE UNIFIÉE ALIX / VERALUME")
    print("=" * 60)
    for sub in sorted(base_dir.iterdir()):
        if sub.is_dir() and not sub.name.startswith("__"):
            py_files = [f.stem for f in sub.glob("*.py") if f.name != "__init__.py"]
            print(f"  [{sub.name.upper():<12}] : {len(py_files):>3} modules")
    print("=" * 60)


def executer_capacite_live(nom_capacite: str):
    """Charge et exécute dynamiquement une capacité depuis alix.capacites."""
    if not nom_capacite.startswith("capacite_"):
        nom_capacite = f"capacite_{nom_capacite}"
    module_path = f"alix.capacites.{nom_capacite}"
    try:
        mod = importlib.import_module(module_path)
        if hasattr(mod, "executer_capacite"):
            print(f"-> Exécution de {module_path}.executer_capacite()...")
            resultat = mod.executer_capacite()
            print("Résultat :", resultat)
        elif hasattr(mod, "main"):
            mod.main()
        else:
            print(f"Le module {nom_capacite} n'a ni 'executer_capacite()' ni 'main()'.")
    except Exception as e:
        print(f"Erreur lors de l'exécution de {module_path} : {e}")


def main():
    parser = argparse.ArgumentParser(description="Orchestrateur Unifié Alix / VERALUME")
    subparsers = parser.add_subparsers(dest="commande")

    subparsers.add_parser("status", help="Affiche le bilan des modules unifiés")

    cap_parser = subparsers.add_parser("capacite", help="Exécute une capacité Live")
    cap_parser.add_argument("nom", help="Nom de la capacité (ex: quete_diurne)")

    args = parser.parse_args()
    if args.commande == "status" or not args.commande:
        lister_modules()
    elif args.commande == "capacite":
        executer_capacite_live(args.nom)


if __name__ == "__main__":
    main()
'''
    (PKG_DIR / "cli.py").write_text(cli_content, encoding="utf-8")


def build_unified_architecture():
    print("=== ÉTAPE 1 : PURGE DES CARACTÈRES U+FEFF (BOM) ===")
    bom_targets = [
        ROOT / "alix_capability_dispatcher.py",
        ROOT / "_Archives_Exocerveau_Legacy_20261025" / "Racine_Python_Legacy" / "chat_loki_740m_dyade.py"
    ]
    for bt in bom_targets:
        if fix_bom_if_present(bt):
            print(f"  [RÉPARÉ] U+FEFF retiré de : {bt.relative_to(ROOT)}")

    print("\n=== ÉTAPE 2 : CRÉATION DU SQUELETTE '_Unification_Alix' ===")
    create_scaffold()

    print("\n=== ÉTAPE 3 : CLASSIFICATION ET COPIE DES SCRIPTS ACTIFS ===")
    manifest = {}
    counts = {}

    for py_file in ROOT.rglob("*.py"):
        if any(part in IGNORE_DIRS for part in py_file.parts):
            continue
        if py_file.name in IGNORE_FILES:
            continue

        # Nettoyage préventif du BOM sur tous les fichiers copiés
        fix_bom_if_present(py_file)

        dest_subpkg = determine_destination(py_file)
        dest_path = PKG_DIR / dest_subpkg / py_file.name

        shutil.copy2(py_file, dest_path)

        rel_src = str(py_file.relative_to(ROOT))
        rel_dst = str(dest_path.relative_to(TARGET_ROOT))
        manifest[rel_src] = {
            "subpackage": dest_subpkg,
            "new_path": rel_dst,
            "import_name": f"alix.{dest_subpkg}.{py_file.stem}"
        }
        counts[dest_subpkg] = counts.get(dest_subpkg, 0) + 1

    manifest_file = TARGET_ROOT / "manifeste_migration.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 60)
    print("   CONSTRUCTION TERMINÉE DANS : _Unification_Alix/")
    print("=" * 60)
    total_migrated = sum(counts.values())
    print(f"Total des scripts actifs unifiés : {total_migrated} fichiers\n")
    for subpkg, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - alix.{subpkg:<14} : {cnt:>3} fichiers")
    print("=" * 60)
    print(f"Carte de correspondance sauvegardée dans : {manifest_file.name}")


if __name__ == "__main__":
    build_unified_architecture()
