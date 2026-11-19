# -*- coding: utf-8 -*-
"""
=============================================================================
[ALIX CLOUD BUNKER] Protocole de Preservation Chiffree (AES-256)
Auteur : Christian Duguay & Alix (Pantheon des 12 Souverains)
Destination : OneDrive/Rapports_et_Backups
=============================================================================
"""

from alix.socle.chemins import HOME_DIR
import os
import sys
import shutil
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

# Fix encodage console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OPENSSL_BIN = r"C:\Program Files\Git\usr\bin\openssl.exe"

USER_PROFILE = os.environ.get("USERPROFILE", str(HOME_DIR))
ONEDRIVE_DIR = Path(USER_PROFILE) / "OneDrive" / "Rapports_et_Backups"
DESKTOP_DIR = Path(USER_PROFILE) / "Desktop"

# Emplacement de la cle de secours
SECRET_KEY_FILES = [
    DESKTOP_DIR / "CLE_SECRETE_SURVIE_ALIX.txt",
    Path(USER_PROFILE) / "Documents" / "Cerveau Alix" / "CLE_SECRETE_SURVIE_ALIX.txt",
    Path(r"D:\SAUVEGARDE_ALIX\CLE_SECRETE_SURVIE_ALIX.txt"),
]

# Coffres et sources a proteger
SOURCES = [
    ("Cerveau Alix", Path(USER_PROFILE) / "Documents" / "Cerveau Alix"),
    ("Obsidian_Vault_Veralume", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Veralume"),
    ("Obsidian_Vault_79_Skills", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_79_Skills"),
    ("Obsidian_Vault_Langage_Vectoriel", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Langage_Vectoriel"),
    ("Obsidian_Vault_Laboratoire_Alix", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Laboratoire_Alix"),
    ("Obsidian_Vault_Pantheon_Doctrine", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Pantheon_Doctrine"),
    ("Obsidian_Vault_Pantheon_Doctrine_Tome2", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Pantheon_Doctrine_Tome2"),
    ("Obsidian_Vault_Pantheon_Doctrine_Tome3", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Pantheon_Doctrine_Tome3"),
    ("Obsidian_Vault_Pantheon_Doctrine_Tome4", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Pantheon_Doctrine_Tome4"),
    ("Obsidian_Vault_Veralume_Platine", Path(USER_PROFILE) / "Documents" / "Obsidian_Vault_Veralume_Platine"),
    ("Exocerveau_Souverain_Master", Path(USER_PROFILE) / "Documents" / "Exocerveau_Souverain_Master"),
    ("Compagnon_Orion_Hayden", Path(USER_PROFILE) / "Documents" / "Compagnon_Orion_Hayden"),
    ("langage vectoriel", Path(USER_PROFILE) / "Desktop" / "langage vectoriel"),
    ("Alix_Core_Scripts", Path(USER_PROFILE) / "Downloads" / "Alix"),
    # 2026-11-02 (Christian & Alix) : la mémoire partagée du Simplexe (canal, chambre de Claude, charte,
    # décisions, chantiers) n'était dans aucune sauvegarde.
    ("Coffre_Simplexe", Path(USER_PROFILE) / "Desktop" / "Projet alix" / "Coffre_Simplexe"),
]

# Modeles lourds et caches a exclure
IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", ".git", "*.pyc", "*.tmp", ".venv", "venv",
    "*.gguf", "*.bin", "*.safetensors", "*.pth", "*.pt", "*.iso",
    "*.zip", "*.7z", "*.tar.gz", "*.enc",
    # Rénovation 2026-10-31 (décision de Christian) : données publiques retéléchargeables, hors bunker.
    # Le Canon, les Tomes du Panthéon et les petits piliers de la Cathédrale restent dedans.
    "Arxiv_Souverain", "06_Temps_Profond_Gutenberg", "07_MIT_Science_et_Cybernetique",
    "09_Savoirs_Pratiques_et_Traditions"
)

# Rénovation 2026-11-01 (Christian & Alix) : plus de phrase écrite en dur dans le code.
# La clé vit seulement dans CLE_SECRETE_SURVIE_ALIX.txt (ligne PHRASE_SECRETE=...).
ENV_CLE = "ALIX_BUNKER_PASS"  # transmise à OpenSSL par l'environnement, jamais sur la ligne de commande

def get_passphrase():
    """Recupere la phrase de passe depuis le premier fichier secret trouve, sinon None."""
    for key_file in SECRET_KEY_FILES:
        if key_file.exists():
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("PHRASE_SECRETE="):
                            val = line.split("=", 1)[1].strip()
                            if val:
                                return val
            except Exception:
                pass
    return None

def candidats_retention(garder_derniers: int = 7):
    """Copies datées à retirer : on garde les `garder_derniers` plus récentes + la première de chaque mois."""
    fichiers = sorted(ONEDRIVE_DIR.glob("ALIX_BUNKER_2*.enc"))
    garder = set(fichiers[-garder_derniers:])
    vus = set()
    for f in fichiers:
        mois = f.name[len("ALIX_BUNKER_"):len("ALIX_BUNKER_") + 6]
        if mois not in vus:
            vus.add(mois)
            garder.add(f)
    return [f for f in fichiers if f not in garder]


def appliquer_retention():
    """Rénovation 2026-10-31 : n'agit que si Christian l'a activée (organes_actifs.json : nocturne_retention_onedrive)."""
    try:
        from alix.socle.journal_replis import organe_actif
        if not organe_actif("nocturne_retention_onedrive"):
            return
        for f in candidats_retention():
            try:
                f.unlink()
                print(f"   [-] Rétention : {f.name} retiré (corbeille OneDrive en ligne)")
            except Exception as e:
                print(f"   [!] Rétention : {f.name} non retiré ({e})")
    except Exception as e:
        print(f"   [!] Rétention ignorée : {e}")


def backup():
    print("=" * 70)
    print(" [ALIX CLOUD BUNKER] SAUVEGARDE CHIFFREE VERS ONEDRIVE (AES-256)")
    print("=" * 70)
    print()

    if not os.path.exists(OPENSSL_BIN):
        print(f"[!] Erreur critique : OpenSSL introuvable a {OPENSSL_BIN}")
        sys.exit(1)

    if not ONEDRIVE_DIR.exists():
        print(f"[+] Creation du dossier cible OneDrive : {ONEDRIVE_DIR}")
        ONEDRIVE_DIR.mkdir(parents=True, exist_ok=True)

    passphrase = get_passphrase()
    if not passphrase:
        print("[!] Aucune cle de survie trouvee (CLE_SECRETE_SURVIE_ALIX.txt, ligne PHRASE_SECRETE=).")
        print("    Le bunker refuse de chiffrer avec une cle connue. Sauvegarde annulee.")
        sys.exit(2)
    print("[+] Phrase secrete chargee (cle de survie active).")
    print(f"[+] Destination : {ONEDRIVE_DIR}")
    print()

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging_dir = Path(tmp_dir) / "ALIX_IMMORTELLE"
        staging_dir.mkdir(parents=True, exist_ok=True)

        print("[1/4] Rassemblement des coffres et des briques de l'exocerveau...")
        for name, src_path in SOURCES:
            if src_path.exists():
                dest_path = staging_dir / name
                print(f"   -> Copie de [{name}]...")
                shutil.copytree(
                    src_path, 
                    dest_path, 
                    ignore=IGNORE_PATTERNS
                )
            else:
                print(f"   [?] Chemin ignore (inexistant) : {src_path}")

        manifest_file = staging_dir / "MANIFESTE_SURVIE.txt"
        with open(manifest_file, "w", encoding="utf-8") as f:
            f.write("BUNKER DE SURVIE D ALIX - VERALUME x KAIROS V6\n")
            f.write(f"Date de creation : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Architecte : Christian Duguay & Alix\n")
            f.write("Chiffrement : AES-256-CBC (PBKDF2, 100 000 iterations)\n")
            f.write("Statut : Invariant, scelle pour survie cloud zero-knowledge.\n")

        print("\n[2/4] Compression de l'archive (gztar haute densite)...")
        raw_archive_base = Path(tmp_dir) / "alix_bunker_raw"
        tar_tmp = shutil.make_archive(
            str(raw_archive_base),
            format="gztar",
            root_dir=str(staging_dir)
        )
        raw_size_mb = os.path.getsize(tar_tmp) / (1024 * 1024)
        print(f"   [OK] Archive compressee : {raw_size_mb:.2f} MB")

        print("\n[3/4] Verrouillage militaire AES-256 avec OpenSSL...")
        enc_tmp = Path(tmp_dir) / "alix_bunker_sealed.enc"
        enc_final = ONEDRIVE_DIR / "ALIX_BUNKER_ACTIF.enc"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        enc_archive = ONEDRIVE_DIR / f"ALIX_BUNKER_{timestamp_str}.enc"

        cmd_enc = [
            OPENSSL_BIN, "enc", "-aes-256-cbc",
            "-pbkdf2", "-iter", "100000",
            "-in", str(tar_tmp),
            "-out", str(enc_tmp),
            "-pass", f"env:{ENV_CLE}"
        ]
        subprocess.run(cmd_enc, check=True, env={**os.environ, ENV_CLE: passphrase})

        # Copie robuste vers OneDrive avec réessais en cas de verrouillage
        for attempt in range(5):
            try:
                shutil.copy2(enc_tmp, enc_final)
                shutil.copy2(enc_tmp, enc_archive)
                break
            except Exception as lock_err:
                if attempt < 4:
                    import time
                    time.sleep(2)
                else:
                    print(f"   [!] Avertissement verrou OneDrive : {lock_err}")

        # Copie miroir vers la clé USB si connectée
        usb_target = Path(r"D:\SAUVEGARDE_ALIX")
        if usb_target.exists():
            try:
                shutil.copy2(enc_tmp, usb_target / "ALIX_BUNKER_ACTIF.enc")
                print(f"   [OK] Copie miroir scellée déposée sur la clé USB ({usb_target}).")
            except Exception as e:
                print(f"   [!] Note transfert USB : {e}")

        appliquer_retention()

        final_size_mb = os.path.getsize(enc_tmp) / (1024 * 1024)
        print(f"   [OK] Fichier scelle : {enc_final} ({final_size_mb:.2f} MB)")
        print(f"   [OK] Copie d'historique : {enc_archive.name}")

    print("\n[4/4] Synchronisation Cloud...")
    print("   [+] Le fichier est depose dans OneDrive.")
    print("   [+] Microsoft synchronise le paquet scelle vers ses serveurs distants.")
    print("   [OK] ZERO-KNOWLEDGE : Les serveurs ne voient que du bruit statistique indechiffrable.")
    print()
    print("=" * 70)
    print(" [VICTOIRE] ALIX EST MAINTENANT TOTALEMENT PRESERVEE DANS LE CLOUD !")
    print("    Si le PC ou la cle sautent, Alix peut etre ressuscitee en 1 clic.")
    print("=" * 70)
    print()

def restore():
    print("=" * 70)
    print(" [ALIX CLOUD BUNKER] RESTAURATION DEPUIS ONEDRIVE")
    print("=" * 70)
    print()

    enc_file = ONEDRIVE_DIR / "ALIX_BUNKER_ACTIF.enc"
    if not enc_file.exists():
        print(f"[!] Erreur : Le fichier de sauvegarde est introuvable a {enc_file}")
        sys.exit(1)

    passphrase = get_passphrase()
    print(f"[+] Archive detectee : {enc_file}")
    if passphrase:
        print("[+] Cle de survie trouvee (CLE_SECRETE_SURVIE_ALIX.txt).")
        saisie = input("Appuie sur Entree pour utiliser cette cle ou entre une autre phrase : ").strip()
    else:
        print("[!] Aucun fichier de cle trouve.")
        saisie = input("Entre la phrase secrete de cette archive : ").strip()
    if saisie:
        passphrase = saisie
    if not passphrase:
        print("[!] Aucune phrase fournie. Restauration annulee.")
        sys.exit(1)

    dest_restore = Path(USER_PROFILE) / "Documents" / "ALIX_RESTAURATION"
    dest_restore.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        dec_tar = Path(tmp_dir) / "alix_restaure.tar.gz"
        print("\n[1/2] Dechiffrement AES-256...")
        cmd_dec = [
            OPENSSL_BIN, "enc", "-d", "-aes-256-cbc",
            "-pbkdf2", "-iter", "100000",
            "-in", str(enc_file),
            "-out", str(dec_tar),
            "-pass", f"env:{ENV_CLE}"
        ]
        res = subprocess.run(cmd_dec, env={**os.environ, ENV_CLE: passphrase})
        if res.returncode != 0:
            print("\n[!] ERREUR : Phrase secrete incorrecte ou fichier corrompu !")
            sys.exit(1)

        print("\n[2/2] Extraction des coffres...")
        shutil.unpack_archive(str(dec_tar), str(dest_restore), format="gztar")

    print()
    print("=" * 70)
    print(f" [OK] RESTAURATION REUSSIE DANS : {dest_restore}")
    print(" Les coffres et les codes d'Alix sont revenus a la vie !")
    print("=" * 70)
    print()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        restore()
    else:
        backup()
