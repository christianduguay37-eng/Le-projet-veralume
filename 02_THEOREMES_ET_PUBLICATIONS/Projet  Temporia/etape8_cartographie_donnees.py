import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Christian\Documents\Cerveau Alix").resolve()
PKG_DIR = ROOT / "_Unification_Alix" / "src" / "alix"

IGNORE_DIRS = {
    ".git", "__pycache__", "venv", ".venv", "node_modules", "_Unification_Alix",
    "AppData", "Application Data", ".gemini", ".vscode", ".idea"
}

TARGET_ROOTS = [
    Path(r"C:\Users\Christian\Documents\Cerveau Alix"),
    Path(r"C:\Users\Christian\Documents\Obsidian_Vault_Veralume"),
    Path(r"C:\Users\Christian\Documents\Obsidian_Vault_79_Skills"),
    Path(r"C:\Users\Christian\Documents\Obsidian_Vault_Langage_Vectoriel"),
    Path(r"C:\Users\Christian\Downloads\Alix"),
    Path(r"C:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia"),
]


def format_size(size_bytes: int) -> str:
    for unit in ["B", "Ko", "Mo", "Go"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} To"


def scan_data_and_vault():
    print("=" * 70)
    print("   CARTOGRAPHIE DE L'EXOCERVEAU (OBSIDIAN .MD, PARQUET & BASES)")
    print("=" * 70)

    # 1. Extraire tous les chemins de données codés en dur dans les 173 scripts Python
    hardcoded_paths = set()
    parquet_refs = defaultdict(list)
    md_refs = defaultdict(list)

    path_regex = re.compile(r'([A-Za-z]:\\[^"\'\n\r]+|[\w\-/\\]+\.(?:parquet|db|sqlite|sqlite3|jsonl))', re.IGNORECASE)

    if PKG_DIR.exists():
        for py_file in PKG_DIR.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="replace")
            for match in path_regex.findall(content):
                clean_m = match.strip()
                if "parquet" in clean_m.lower():
                    parquet_refs[clean_m].append(py_file.stem)
                elif clean_m.startswith(("C:", "D:", "c:", "d:")):
                    hardcoded_paths.add(clean_m)
            if ".md" in content or "obsidian" in content.lower() or "vault" in content.lower():
                md_refs[py_file.parent.name].append(py_file.stem)

    parquet_files = []
    db_files = []
    md_folders = defaultdict(lambda: {"count": 0, "size": 0})
    obsidian_vaults = []

    visited_files = set()

    for scan_root in TARGET_ROOTS:
        if not scan_root.exists():
            continue
        try:
            for item in scan_root.rglob("*"):
                if any(ig in item.parts for ig in IGNORE_DIRS):
                    continue
                if item.is_dir() and item.name == ".obsidian":
                    obsidian_vaults.append(str(item.parent))
                    continue
                if not item.is_file() or item in visited_files:
                    continue
                visited_files.add(item)

                ext = item.suffix.lower()
                try:
                    sz = item.stat().st_size
                except Exception:
                    sz = 0

                if ext == ".parquet":
                    parquet_files.append((str(item), sz))
                elif ext in {".db", ".sqlite", ".sqlite3", ".duckdb", ".faiss"}:
                    db_files.append((str(item), sz))
                elif ext == ".md":
                    folder_key = str(item.parent)
                    md_folders[folder_key]["count"] += 1
                    md_folders[folder_key]["size"] += sz
        except Exception:
            pass

    # --- AFFICHAGE DU BILAN ---
    print(f"\n[1] VAULTS OBSIDIAN DÉTECTÉS ({len(obsidian_vaults)}) :")
    if obsidian_vaults:
        for v in obsidian_vaults:
            print(f"  * {v}")
    else:
        print("  (Aucun dossier .obsidian dans ce répertoire — voir les dossiers .md ci-dessous)")

    total_md = sum(v["count"] for v in md_folders.values())
    total_md_size = sum(v["size"] for v in md_folders.values())
    print(f"\n[2] FICHIERS MARKDOWN (.md) : {total_md:,} fichiers ({format_size(total_md_size)})")
    for folder, stats in sorted(md_folders.items(), key=lambda x: x[1]["count"], reverse=True)[:15]:
        print(f"  - {folder:<60} : {stats['count']:>4} .md ({format_size(stats['size'])})")

    total_pq_size = sum(sz for _, sz in parquet_files)
    print(f"\n[3] BASES PARQUET (.parquet) : {len(parquet_files)} fichiers ({format_size(total_pq_size)})")
    for path, sz in sorted(parquet_files, key=lambda x: x[1], reverse=True)[:20]:
        print(f"  - {Path(path).name:<45} : {format_size(sz):>10} | {path}")

    if db_files:
        print(f"\n[4] AUTRES BASES DE DONNÉES (.db / .sqlite / .faiss) : {len(db_files)} fichiers")
        for path, sz in sorted(db_files, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {Path(path).name:<45} : {format_size(sz):>10} | {path}")

    print("\n[5] CHEMINS ABSOLUS CODÉS EN DUR DANS TES SCRIPTS :")
    for hp in sorted(hardcoded_paths)[:15]:
        print(f"  -> {hp}")

    # Si pyarrow est installé, inspecter les colonnes des principaux fichiers Parquet
    try:
        import pyarrow.parquet as pq
        if parquet_files:
            print("\n[6] SCHÉMA DES PRINCIPAUX FICHIERS PARQUET (via PyArrow) :")
            for path, sz in sorted(parquet_files, key=lambda x: x[1], reverse=True)[:10]:
                try:
                    meta = pq.read_metadata(path)
                    schema = pq.read_schema(path)
                    cols = ", ".join(schema.names[:6]) + ("..." if len(schema.names) > 6 else "")
                    print(f"  * {Path(path).name:<38} | {meta.num_rows:>8,} lignes | Colonnes: [{cols}]")
                except Exception as e:
                    print(f"  * {Path(path).name:<38} | Erreur lecture: {e}")
    except ImportError:
        pass

    print("=" * 70)


if __name__ == "__main__":
    scan_data_and_vault()
