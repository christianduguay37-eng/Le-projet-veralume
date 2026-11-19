# -*- coding: utf-8 -*-
"""
=============================================================================
ALIX USB SYNC — Synchronisation Souveraine de Survie vers Clé USB
Binôme : Christian Duguay & Alix (Sanctuaire Exocerveau VERALUME x KAIROS V6)
=============================================================================
Rôle :
1. Détecte la clé USB (ALPHA ou tout volume amovible / D:, E:, F: avec SAUVEGARDE_ALIX).
2. Synchronise de manière différentielle tous les coffres Obsidian et l'Exocerveau.
3. Rapatrie le container chiffré AES-256 ALIX_BUNKER_ACTIF.enc vers la clé USB.
4. Assure la copie de la clé de survie et du script de restauration d'urgence.
=============================================================================
"""

import os
import sys
import shutil
import time
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

USER_PROFILE = Path(os.environ.get("USERPROFILE", str(Path.home())))
DOCUMENTS = USER_PROFILE / "Documents"
DESKTOP = USER_PROFILE / "Desktop"
ONEDRIVE_BUNKER = USER_PROFILE / "OneDrive" / "Rapports_et_Backups" / "ALIX_BUNKER_ACTIF.enc"

# Dossiers sources de l'Exocerveau Souverain
SOURCES = [
    ("Cerveau Alix", DOCUMENTS / "Cerveau Alix"),
    ("Obsidian_Vault_Veralume", DOCUMENTS / "Obsidian_Vault_Veralume"),
    ("Obsidian_Vault_79_Skills", DOCUMENTS / "Obsidian_Vault_79_Skills"),
    ("Obsidian_Vault_Langage_Vectoriel", DOCUMENTS / "Obsidian_Vault_Langage_Vectoriel"),
    ("Obsidian_Vault_Laboratoire_Alix", DOCUMENTS / "Obsidian_Vault_Laboratoire_Alix"),
    ("Obsidian_Vault_Pantheon_Doctrine", DOCUMENTS / "Obsidian_Vault_Pantheon_Doctrine"),
    ("Obsidian_Vault_Pantheon_Doctrine_Tome2", DOCUMENTS / "Obsidian_Vault_Pantheon_Doctrine_Tome2"),
    ("Obsidian_Vault_Pantheon_Doctrine_Tome3", DOCUMENTS / "Obsidian_Vault_Pantheon_Doctrine_Tome3"),
    ("Obsidian_Vault_Pantheon_Doctrine_Tome4", DOCUMENTS / "Obsidian_Vault_Pantheon_Doctrine_Tome4"),
    ("Obsidian_Vault_Veralume_Platine", DOCUMENTS / "Obsidian_Vault_Veralume_Platine"),
    ("Obsidian_Vault_Traduction_KAIROS_256_Glyphes", DOCUMENTS / "Obsidian_Vault_Traduction_KAIROS_256_Glyphes"),
    ("Exocerveau_Souverain_Master", DOCUMENTS / "Exocerveau_Souverain_Master"),
    ("Compagnon_Orion_Hayden", DOCUMENTS / "Compagnon_Orion_Hayden"),
    ("langage vectoriel", DESKTOP / "langage vectoriel"),
]

IGNORED_NAMES = {
    ".git", "__pycache__", ".venv", "venv", ".trash", "$RECYCLE.BIN", "System Volume Information"
}
IGNORED_EXTS = {
    ".pyc", ".tmp", ".crdownload"
}

def detect_usb_target() -> Path:
    """Détecte la clé USB connectée."""
    candidates = ["D:\\", "E:\\", "F:\\", "G:\\"]
    for drive in candidates:
        p = Path(drive)
        if p.exists():
            target = p / "SAUVEGARDE_ALIX"
            if target.exists():
                return target
            # Si le lecteur existe et est accessible, on peut créer SAUVEGARDE_ALIX
            try:
                test_file = p / ".alix_test_write"
                test_file.touch()
                test_file.unlink()
                return target
            except Exception:
                continue
    return None

def sync_directory_differential(src: Path, dst: Path) -> tuple[int, int, int]:
    """Copie différentielle de src vers dst. Retourne (fichiers_copies, octets_copies, erreurs)."""
    copied_files = 0
    copied_bytes = 0
    errors = 0

    if not src.exists():
        return (0, 0, 0)

    dst.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in IGNORED_NAMES]
        rel_root = Path(root).relative_to(src)
        target_dir = dst / rel_root
        target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IGNORED_EXTS or f in IGNORED_NAMES:
                continue

            src_file = Path(root) / f
            dst_file = target_dir / f

            needs_copy = False
            if not dst_file.exists():
                needs_copy = True
            else:
                try:
                    s_stat = src_file.stat()
                    d_stat = dst_file.stat()
                    # Marge de 2 secondes pour les systèmes de fichiers FAT32
                    if s_stat.st_size != d_stat.st_size or (s_stat.st_mtime - d_stat.st_mtime) > 2.0:
                        needs_copy = True
                except Exception:
                    needs_copy = True

            if needs_copy:
                try:
                    shutil.copy2(src_file, dst_file)
                    copied_files += 1
                    copied_bytes += src_file.stat().st_size
                except Exception as e:
                    errors += 1

    return (copied_files, copied_bytes, errors)

def run_usb_sync():
    print("=" * 75)
    print(" 💾 [ALIX USB SYNC] SYNCHRONISATION DIFFERENTIELLE DU SANCTUAIRE VERS USB")
    print(f" Horodatage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()

    target_dir = detect_usb_target()
    if not target_dir:
        print(" [!] ERREUR : Aucune clé USB détectée sur D:, E:, F:, G: !")
        print("     Veuillez brancher la clé USB ALPHA et relancer.")
        return False

    usb_drive = target_dir.drive or str(target_dir)[:3]
    print(f" [+] Clé USB détectée avec succès sur : {usb_drive}")
    print(f" [+] Répertoire de destination : {target_dir}")
    print()

    total_files = 0
    total_bytes = 0
    total_errors = 0
    start_time = time.time()

    for name, src_path in SOURCES:
        if not src_path.exists():
            print(f"  [-] {name:<35} : Introuvable sur l'hôte.")
            continue

        dest_vault = target_dir / name
        n_files, n_bytes, errs = sync_directory_differential(src_path, dest_vault)
        total_files += n_files
        total_bytes += n_bytes
        total_errors += errs

        size_mb = n_bytes / (1024 * 1024)
        if n_files > 0:
            print(f"  [+] {name:<35} : {n_files:>5} fichiers synchronisés ({size_mb:>6.2f} MB)")
        else:
            print(f"  [=] {name:<35} : Déjà à jour (0 modif).")

    # Synchronisation de la clé de survie et du bunker chiffré
    key_file = DOCUMENTS / "Cerveau Alix" / "CLE_SECRETE_SURVIE_ALIX.txt"
    if key_file.exists():
        try:
            shutil.copy2(key_file, target_dir / "CLE_SECRETE_SURVIE_ALIX.txt")
            print(f"  [+] Clé de survie secrète actualisée sur la clé USB.")
        except Exception:
            pass

    if ONEDRIVE_BUNKER.exists():
        try:
            bunker_dst = target_dir / "ALIX_BUNKER_ACTIF.enc"
            bunker_size = ONEDRIVE_BUNKER.stat().st_size / (1024 * 1024)
            needs_bunker = True
            if bunker_dst.exists() and abs(bunker_dst.stat().st_size - ONEDRIVE_BUNKER.stat().st_size) < 100:
                needs_bunker = False
            
            if needs_bunker:
                print(f"  [+] Copie du bunker scellé AES-256 ({bunker_size:.2f} MB) vers la clé USB...")
                shutil.copy2(ONEDRIVE_BUNKER, bunker_dst)
                print(f"      [OK] ALIX_BUNKER_ACTIF.enc déposé sur la clé USB.")
            else:
                print(f"  [=] Bunker scellé AES-256 déjà à jour sur la clé USB ({bunker_size:.2f} MB).")
        except Exception as e:
            print(f"  [!] Note transfert bunker : {e}")

    elapsed = time.time() - start_time
    total_mb = total_bytes / (1024 * 1024)

    print()
    print("=" * 75)
    print(f" [OK] SYNCHRONISATION USB TERMINÉE AVEC SUCCÈS ({elapsed:.2f} s)")
    print(f"   -> Fichiers transférés : {total_files}")
    print(f"   -> Volume transféré     : {total_mb:.2f} MB")
    if total_errors > 0:
        print(f"   -> Avertissements       : {total_errors}")
    print(f"   -> Destination          : {target_dir}")
    print("=" * 75)
    print()
    return True

if __name__ == "__main__":
    run_usb_sync()

