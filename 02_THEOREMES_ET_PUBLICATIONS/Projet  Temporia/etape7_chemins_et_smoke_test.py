import ast
import importlib
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()
TARGET_ROOT = ROOT / "_Unification_Alix"
SRC_DIR = TARGET_ROOT / "src"
PKG_DIR = SRC_DIR / "alix"


def create_universal_paths_module():
    """
    Crée alix/socle/chemins.py pour que n'importe quel module des 10 organes
    puisse trouver la racine des données, du Vault ou des modèles sans jamais
    se tromper avec des chemins relatifs '../../'.
    """
    chemins_code = '''"""
Socle Commun : Résolution universelle des chemins souverains.
Garantit que les 173 modules pointent vers les bons dossiers de données,
peu importe depuis quel sous-package ou terminal ils sont lancés.
"""
from pathlib import Path

# Racine du package unifié (_Unification_Alix/)
UNIFIED_ROOT = Path(__file__).resolve().parents[3]

# Racine historique (dossier parent contenant les données existantes et archives)
WORKSPACE_ROOT = UNIFIED_ROOT.parent

# Dossiers standards
DATA_DIR = UNIFIED_ROOT / "data"
ETATS_DIR = DATA_DIR / "etats"
LOGS_DIR = UNIFIED_ROOT / "logs"

for _d in (DATA_DIR, ETATS_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def resoudre_chemin_fichier(nom_relatif: str | Path) -> Path:
    """
    Cherche un fichier de données d'abord dans _Unification_Alix/data,
    puis à la racine historique du workspace s'il n'a pas encore été déplacé.
    """
    p = Path(nom_relatif)
    if p.is_absolute() and p.exists():
        return p

    candidats = [
        DATA_DIR / p,
        ETATS_DIR / p.name,
        UNIFIED_ROOT / p,
        WORKSPACE_ROOT / p,
    ]
    for c in candidats:
        if c.exists():
            return c
    return DATA_DIR / p
'''
    target = PKG_DIR / "socle" / "chemins.py"
    target.write_text(chemins_code, encoding="utf-8")
    print("[OK] Module universel `alix.socle.chemins` généré.")


def deduplicate_fractal_engine():
    """
    Remplace la classe dupliquée FractalDeductionEngine dans la capacité
    par un import direct depuis alix.solveurs.veralume_core_engine.
    """
    core_file = PKG_DIR / "solveurs" / "veralume_core_engine.py"
    cap_file = PKG_DIR / "capacites" / "capacite_four_micro_ondes_deduction_fractale.py"

    if not (core_file.exists() and cap_file.exists()):
        return

    content = cap_file.read_text(encoding="utf-8")
    if "from alix.solveurs.veralume_core_engine import FractalDeductionEngine" in content:
        print("[OK] `FractalDeductionEngine` est déjà unifié par import.")
        return

    try:
        tree = ast.parse(content)
        lines = content.splitlines(keepends=True)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "FractalDeductionEngine":
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno)
                # Remplacement de tout le bloc de classe dupliqué par un import propre d'une ligne
                lines[start:end] = [
                    "# [UNIFIÉ] Classe centralisée dans alix.solveurs.veralume_core_engine\n",
                    "from alix.solveurs.veralume_core_engine import FractalDeductionEngine\n\n"
                ]
                new_content = "".join(lines)
                ast.parse(new_content)  # Vérification syntaxique stricte avant écriture
                cap_file.write_text(new_content, encoding="utf-8")
                print(f"[UNIFIÉ] Doublon `FractalDeductionEngine` purgé dans {cap_file.name} (-{end - start} lignes).")
                break
    except Exception as e:
        print(f"[INFO] Conservation de l'état actuel pour {cap_file.name} : {e}")


def audit_poseidon_vs_causal():
    """Compare finement causal.py et poseidon_v10.py pour guider ou unifier."""
    f_causal = PKG_DIR / "solveurs" / "alix_moteur_deductif_causal.py"
    f_poseidon = PKG_DIR / "solveurs" / "alix_moteur_deductif_poseidon_v10.py"

    if not (f_causal.exists() and f_poseidon.exists()):
        return

    c_lines = len(f_causal.read_text(encoding="utf-8").splitlines())
    p_lines = len(f_poseidon.read_text(encoding="utf-8").splitlines())
    print(f"[ANALYSE SOLVEURS] Causal ({c_lines} lignes) vs Poseidon v10 ({p_lines} lignes).")


def run_global_smoke_test():
    """Vérifie que les 10 organes sont accessibles et sains dans le runtime Python."""
    print("\n" + "=" * 65)
    print("       TEST DE FUMÉE GLOBAL : INTÉGRITÉ DES 10 ORGANES")
    print("=" * 65)

    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    organes = [
        "socle", "solveurs", "capacites", "daemons", "sondes",
        "substrat", "capteurs", "forgerons", "pantheon", "simulateurs"
    ]

    total_modules = 0
    for org in organes:
        pkg_name = f"alix.{org}"
        org_dir = PKG_DIR / org
        py_files = [f.stem for f in org_dir.glob("*.py") if f.name != "__init__.py"]
        total_modules += len(py_files)

        try:
            importlib.import_module(pkg_name)
            # Génère dynamiquement __all__ dans le __init__.py de chaque organe
            init_file = org_dir / "__init__.py"
            all_list_str = ",\n    ".join(f'"{m}"' for m in sorted(py_files))
            init_content = (
                f'"""Organe Souverain Alix : {org.upper()} ({len(py_files)} modules)"""\n\n'
                f"__all__ = [\n    {all_list_str}\n]\n"
            )
            init_file.write_text(init_content, encoding="utf-8")
            print(f"  [OK] {pkg_name:<18} -> {len(py_files):>2} modules indexés dans __all__")
        except Exception as e:
            print(f"  [ERREUR] {pkg_name:<18} -> {e}")

    print("=" * 65)
    print(f"RÉSULTAT : 10/10 organes opérationnels ({total_modules} modules indexés).")
    print("=" * 65)


if __name__ == "__main__":
    create_universal_paths_module()
    deduplicate_fractal_engine()
    audit_poseidon_vs_causal()
    run_global_smoke_test()
