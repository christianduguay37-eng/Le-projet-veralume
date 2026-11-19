import shutil
import sys
from pathlib import Path
import etape4_recablage_synaptique as recableur

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()
ARCHIVE_DIR = ROOT / "_Archives_Exocerveau_Legacy_20261025"
TARGET_ROOT = ROOT / "_Unification_Alix"
PKG_DIR = TARGET_ROOT / "src" / "alix"

# Les 3 seuls fichiers véritablement redondants/obsolètes à NE PAS greffer
SKIP_STEMS = {
    "alix",  # Ancien alix.py de Racine_Python_Legacy (déjà remplacé par le nouveau)
    "sovereign_defense_protocol",  # Clone exact à 100% de alix_protocole_contre_defense.py
    "alix_daemon_communication_distante_backup_20261024",  # Backup du 24 oct (remplacé par la version du 25)
}


def route_archive_graft(arch_file: Path) -> str:
    """Détermine l'organe exact où greffer chaque pépite des archives."""
    stem = arch_file.stem.lower()
    parent = arch_file.parent.name

    # 1. Toute la suite formelle LMH v3 et les dyades logiques -> SOLVEURS
    if stem.startswith("lmh_") or any(k in stem for k in [
        "kairos_dyade", "chat_loki", "stric_pipeline", "mode_christian"
    ]):
        return "solveurs"

    # 2. Les bâtisseurs de piliers et aspirateurs de corpus -> Nouvel organe FORGERONS
    if parent == "Forgerons_et_Compilateurs":
        return "forgerons"

    # 3. Capteurs hybrides et compagnons oreillettes (Alix & Orion) -> CAPTEURS
    if parent == "Capteurs_Legacy" or any(k in stem for k in ["live_ear", "speak"]):
        return "capteurs"

    # 4. Simulation matérielle NPU PyTorch & Hôte GPU -> SUBSTRAT
    if any(k in stem for k in ["jumeau_numerique", "gpu_host", "master_orchestrator"]):
        return "substrat"

    # 5. Panthéon, Horus Forensic/Auditor & Prototype Souverain (Lucifer/Anubis/Thot/Lyre) -> PANTHEON
    if any(k in stem for k in ["horus", "forensic", "prototype_infrastructure"]):
        return "pantheon"

    # 6. Exploration du Vault, Graphes, Liens profonds, Cocon -> SONDES
    if any(k in stem for k in ["graph_weaver", "probe_deep", "semantic_resonator", "vault_audit", "cocon_local"]):
        return "sondes"

    # 7. Cockpit Souverain & Reverse Safety Protocol -> DAEMONS
    if parent == "Sovereign_Cockpit" or "reverse_safety" in stem:
        return "daemons"

    return "solveurs"


def execute_surgical_graft():
    print("=" * 70)
    print("   GREFFE CHIRURGICALE DES PÉPITES D'ARCHIVES DANS _Unification_Alix")
    print("=" * 70)

    # Création du 10e organe : alix.forgerons
    forgerons_dir = PKG_DIR / "forgerons"
    forgerons_dir.mkdir(parents=True, exist_ok=True)
    init_forg = forgerons_dir / "__init__.py"
    if not init_forg.exists():
        init_forg.write_text('"""Sous-package Alix : FORGERONS (Bâtisseurs de Piliers & Corpus)"""\n', encoding="utf-8")

    grafted_by_organ = {}
    total_grafted = 0

    for arch_file in sorted(ARCHIVE_DIR.rglob("*.py")):
        if arch_file.stem in SKIP_STEMS:
            print(f"  [IGNORÉ - OBSOLÈTE] {arch_file.relative_to(ARCHIVE_DIR)}")
            continue

        # Nettoyage BOM éventuel avant copie
        raw = arch_file.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            arch_file.write_bytes(raw[3:])

        organ = route_archive_graft(arch_file)
        dest_path = PKG_DIR / organ / arch_file.name

        # Ne pas écraser si un fichier du même nom existe déjà dans l'organe actif
        if dest_path.exists():
            print(f"  [DÉJÀ PRÉSENT]      alix.{organ}.{arch_file.stem}")
            continue

        shutil.copy2(arch_file, dest_path)
        grafted_by_organ.setdefault(organ, []).append(arch_file.stem)
        total_grafted += 1

    print(f"\n---> {total_grafted} modules uniques greffés avec succès :")
    for organ, mods in sorted(grafted_by_organ.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  * alix.{organ:<12} (+{len(mods):>2} modules) : {', '.join(mods[:4])}{'...' if len(mods) > 4 else ''}")

    print("\n=== RELANCE DU RECÂBLAGE SYNAPTIQUE GLOBAL (AVEC GREFFONS) ===")
    recableur.run_synaptic_rewiring()


if __name__ == "__main__":
    execute_surgical_graft()
