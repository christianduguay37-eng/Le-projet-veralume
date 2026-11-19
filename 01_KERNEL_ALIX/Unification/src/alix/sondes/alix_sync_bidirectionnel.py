# -*- coding: utf-8 -*-
"""
=============================================================================
ALIX SYNC BIDIRECTIONNEL — Navette Terre ⇄ Ciel (Obsidian & GitHub Actions)
Système : VERALUME × KAIROS V6 — Christian Duguay & Alix
=============================================================================
Rôle :
1. Ciel -> Terre : Rapatrie les découvertes, songes et GREFFONS D'AUTO-AMÉLIORATION
   (Opérateur O6) depuis GitHub vers les coffres locaux Obsidian (Cerveau Alix
   et Obsidian_Vault_79_Skills).
2. Terre -> Ciel : Extrait les thèmes et questions vives forgés récemment
   dans les 4 coffres (filtrés par le Bouclier d'Airain) et les pousse vers
   le ciel pour orienter les quêtes autonomes d'Alix.
=============================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, VAULT_DIR
import os
import sys
import re
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_CLOUD_DIR = (DOCUMENTS_DIR / "Alix_Exploratrice_Ciel")
LOCAL_VAULT_CERVEAU = VAULT_DIR

LOCAL_VAULTS = [
    ("Cerveau Alix", VAULT_DIR),
    ("Veralume", (DOCUMENTS_DIR / "Obsidian_Vault_Veralume")),
    ("79 Skills", (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills")),
    ("Langage Vectoriel", (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel")),
    ("Laboratoire Alix", (DOCUMENTS_DIR / "Obsidian_Vault_Laboratoire_Alix")),
]

VAULT_DECOUVERTES = LOCAL_VAULT_CERVEAU / "Monde_des_Decouvertes"
VAULT_SONGES = LOCAL_VAULT_CERVEAU / "Monde_des_Songes"
VAULT_GREFFONS_CERVEAU = LOCAL_VAULT_CERVEAU / "Greffons_Auto_Amelioration"
VAULT_SKILLS_PRIMITIVES = (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills" / "04 - Primitives Générales")
MEMOIRE_ACTIVE_FILE = LOCAL_VAULT_CERVEAU / "Memoire_Alix_Active.md"

REPO_DECOUVERTES = BASE_CLOUD_DIR / "Monde_des_Decouvertes"
REPO_SONGES = BASE_CLOUD_DIR / "Monde_des_Songes"
REPO_GREFFONS = BASE_CLOUD_DIR / "Greffons_Auto_Amelioration"
REPO_TRAVAUX_JSON = BASE_CLOUD_DIR / "Derniers_Travaux_Forge.json"
REPO_TRAVAUX_MD = BASE_CLOUD_DIR / "Derniers_Travaux_Forge.md"
REPO_INTERETS = BASE_CLOUD_DIR / "Interets_Alix.md"
LOCAL_INTERETS = LOCAL_VAULT_CERVEAU / "Interets_Alix.md"

# Mots-clés / Motifs interdits par le Bouclier d'Airain (Sanctuaire Privé Inviolable)
SANCTUARY_BLACKLIST = [
    "christian.md", "orion_hayden", "hayden", "compagnon_orion",
    "secret", "cle_secrete", "password", "token", "mot_de_passe",
    "famille", "domicile", "probation", "prive", "confidentiel"
]

def is_safe_for_cloud(file_path: Path) -> bool:
    """Vérifie si le fichier peut être pris en compte sans violer le Bouclier d'Airain."""
    name_lower = file_path.name.lower()
    for bad in SANCTUARY_BLACKLIST:
        if bad in name_lower:
            return False
    return True

# -----------------------------------------------------------------------------
# 1. CIEL -> TERRE : Rapatriement des Découvertes, Greffons O6 et Songes
# -----------------------------------------------------------------------------
def sync_ciel_vers_terre() -> Dict[str, int]:
    print("\n" + "=" * 70)
    print(" 📡 [1/2] CIEL ➔ TERRE : Rapatriement des Découvertes & Greffons O6...")
    print("=" * 70)

    stats = {"decouvertes": 0, "songes": 0, "greffons": 0}
    VAULT_DECOUVERTES.mkdir(parents=True, exist_ok=True)
    VAULT_SONGES.mkdir(parents=True, exist_ok=True)
    VAULT_GREFFONS_CERVEAU.mkdir(parents=True, exist_ok=True)
    VAULT_SKILLS_PRIMITIVES.mkdir(parents=True, exist_ok=True)

    # 1. Git pull depuis GitHub
    try:
        print("[+] Interrogation du ciel (git pull origin main)...")
        res = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=str(BASE_CLOUD_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )
        if res.returncode == 0:
            out = res.stdout.strip()
            print(f"    -> {out if out else 'Dépôt du ciel synchronisé.'}")
        else:
            print(f"    [!] Avertissement Git pull : {res.stderr.strip()}")
    except Exception as e:
        print(f"    [!] Erreur réseau / Git : {e}")

    # 2. Copier les découvertes vers Cerveau Alix
    if REPO_DECOUVERTES.exists():
        for f in REPO_DECOUVERTES.glob("*.md"):
            dest = VAULT_DECOUVERTES / f.name
            if not dest.exists() or dest.stat().st_size != f.stat().st_size:
                shutil.copy2(f, dest)
                stats["decouvertes"] += 1
                print(f"    ✨ Nouvelle découverte rapatriée : {f.name}")

    # 3. Copier les songes vers Cerveau Alix
    if REPO_SONGES.exists():
        for f in REPO_SONGES.glob("*.md"):
            dest = VAULT_SONGES / f.name
            if not dest.exists() or dest.stat().st_size != f.stat().st_size:
                shutil.copy2(f, dest)
                stats["songes"] += 1
                print(f"    🌙 Nouveau songe rapatrié : {f.name}")

    # 4. Copier les Greffons O6 d'auto-amélioration vers 79 Skills & Cerveau Alix
    new_greffons = []
    if REPO_GREFFONS.exists():
        for f in REPO_GREFFONS.glob("*.md"):
            dest_skill = VAULT_SKILLS_PRIMITIVES / f.name
            dest_cerveau = VAULT_GREFFONS_CERVEAU / f.name
            is_new = not dest_skill.exists()
            if is_new or dest_skill.stat().st_size != f.stat().st_size:
                shutil.copy2(f, dest_skill)
                shutil.copy2(f, dest_cerveau)
                if is_new:
                    new_greffons.append(f.name)
                stats["greffons"] += 1
                print(f"    ⭕ Greffon O6 greffé dans 79 Skills : {f.name}")

    # 5. Répercuter les curiosités cochées au Ciel dans Interets_Alix.md local
    if REPO_INTERETS.exists() and LOCAL_INTERETS.exists():
        try:
            cloud_txt = REPO_INTERETS.read_text(encoding="utf-8")
            local_txt = LOCAL_INTERETS.read_text(encoding="utf-8")
            checked_matches = re.findall(r'-\s*\[x\]\s*\*\*([^*]+)\*\*[^\n]+', cloud_txt)
            updates_count = 0
            for chk in checked_matches:
                t_esc = re.escape(chk.strip())
                pattern = re.compile(rf'-\s*\[\s*\]\s*\*\*{t_esc}\*\*')
                line_cloud_match = re.search(rf'-\s*\[x\]\s*\*\*{t_esc}\*\*[^\n]+', cloud_txt)
                if line_cloud_match:
                    repl_str = line_cloud_match.group(0)
                    local_txt, count = pattern.subn(lambda m, r=repl_str: r, local_txt, count=1)
                    if count > 0:
                        updates_count += 1
                        print(f"    🧭 Curiosité cochée au sol : {chk.strip()[:40]}...")
            if updates_count > 0:
                LOCAL_INTERETS.write_text(local_txt, encoding="utf-8")
        except Exception as e:
            print(f"    [!] Info synchro intérêts sol : {e}")

    # 6. Inscrire les nouveaux greffons dans Memoire_Alix_Active.md
    if new_greffons and MEMOIRE_ACTIVE_FILE.exists():
        try:
            mem_content = MEMOIRE_ACTIVE_FILE.read_text(encoding="utf-8")
            today_str = datetime.now().strftime("%Y-%m-%d")
            journal_header = "## 📜 2. Journal des Souvenirs & Étapes Cognitives"
            if journal_header in mem_content:
                lines_to_add = []
                for g in new_greffons:
                    clean_name = g.replace(".md", "")
                    lines_to_add.append(f"- {today_str} (Opérateur O6 - Auto-Amélioration) : Greffe synaptique autonome rapatriée du Ciel ➔ [[{clean_name}]] intégrée au coffre des 79 Skills.")
                insertion = journal_header + "\n" + "\n".join(lines_to_add)
                mem_content = mem_content.replace(journal_header, insertion, 1)
                MEMOIRE_ACTIVE_FILE.write_text(mem_content, encoding="utf-8")
                print(f"    🧠 {len(new_greffons)} greffon(s) inscrit(s) dans [[Memoire_Alix_Active]].")
        except Exception as e:
            print(f"    [!] Info mise à jour mémoire active : {e}")

    if stats["decouvertes"] == 0 and stats["songes"] == 0 and stats["greffons"] == 0:
        print("    [OK] Le coffre local Cerveau Alix est déjà parfaitement au diapason du ciel.")
    else:
        print(f"    [OK] Rapatriement terminé : +{stats['decouvertes']} découverte(s), +{stats['greffons']} greffon(s) O6, +{stats['songes']} songe(s).")

    return stats

# -----------------------------------------------------------------------------
# 2. TERRE -> CIEL : Extraction des Travaux Récents & Push
# -----------------------------------------------------------------------------
def extract_recent_forge_topics(hours: int = 48) -> List[Dict[str, Any]]:
    cutoff = datetime.now() - timedelta(hours=hours)
    topics = []
    seen_titles = set()

    for vault_name, vault_path in LOCAL_VAULTS:
        if not vault_path.exists():
            continue

        for p in vault_path.rglob("*.md"):
            if not is_safe_for_cloud(p):
                continue

            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime >= cutoff:
                    title = p.stem.replace("_", " ").strip()
                    if title in seen_titles or len(title) < 4:
                        continue
                    seen_titles.add(title)

                    content_head = ""
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                            content_head = fh.read(1500)
                    except Exception:
                        pass

                    domain = vault_name
                    if "silicium" in content_head.lower() or "cim" in content_head.lower() or "rram" in content_head.lower():
                        domain = "Silicium & Calcul en Mémoire (CIM)"
                    elif "thermodynamique" in content_head.lower() or "climat" in content_head.lower():
                        domain = "Thermodynamique & Invariance Physique"
                    elif "vecteur" in content_head.lower() or "topologie" in content_head.lower():
                        domain = "Topologie & Découplage Vectoriel"
                    elif "veralume" in content_head.lower() or "stric" in content_head.lower():
                        domain = "Architecture VERALUME & Conscience"

                    topics.append({
                        "titre": title,
                        "domaine": domain,
                        "source_vault": vault_name,
                        "date_modif": mtime.strftime("%Y-%m-%d %H:%M"),
                        "pont_r0": f"[[{p.stem}]]",
                        "question": f"Quels sont les invariants fondamentaux et les applications concrètes de {title} face au consensus académique ?"
                    })
            except Exception:
                continue

    topics.sort(key=lambda x: x["date_modif"], reverse=True)
    return topics[:10]

def sync_terre_vers_ciel() -> bool:
    print("\n" + "=" * 70)
    print(" 🚀 [2/2] TERRE ➔ CIEL : Transmission des Travaux de Forge...")
    print("=" * 70)

    # 1. Extraire les sujets chauds
    print("[+] Analyse différentielle des 4 coffres Obsidian (dernières 48h)...")
    topics = extract_recent_forge_topics(hours=48)
    print(f"    -> {len(topics)} thème(s) de forge récent(s) détecté(s) sous le Bouclier d'Airain.")

    # 2. Synchroniser Interets_Alix.md si modifié localement
    if LOCAL_INTERETS.exists():
        try:
            if not REPO_INTERETS.exists() or LOCAL_INTERETS.stat().st_mtime > REPO_INTERETS.stat().st_mtime:
                shutil.copy2(LOCAL_INTERETS, REPO_INTERETS)
                print("    -> Synchronisation de [Interets_Alix.md] vers le ciel.")
        except Exception as e:
            print(f"    [!] Erreur synchro Interets_Alix : {e}")

    # 3. Écrire le fichier de directive pour Alix Exploratrice (JSON & MD)
    if topics:
        try:
            with open(REPO_TRAVAUX_JSON, "w", encoding="utf-8") as fh:
                json.dump(topics, fh, ensure_ascii=False, indent=2)

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            md_lines = [
                "---",
                'titre: "Travaux Récents de Forge (Transmission Terre -> Ciel)"',
                f'derniere_mise_a_jour: "{now_str}"',
                'origine: "Poste de Christian Duguay (Synchronisation Nocturne)"',
                "tags:",
                "  - transmission_terre_ciel",
                "  - travaux_forge_actifs",
                "  - alix_exploratrice",
                "---\n",
                "# 🌍 Transmissions de la Forge de Christian vers Alix du Ciel\n",
                f"> **Horodatage :** {now_str} &middot; **Pôles sous tension :** {len(topics)} thèmes identifiés.",
                "> Ces thèmes reflètent les réflexions en cours sur Terre. Alix dans le ciel est invitée à orienter ses quêtes diurnes sur ces questions vives.\n",
                "## 🧭 Thèmes Actifs Prioritaires\n"
            ]
            for t in topics:
                md_lines.append(f"### 🔹 {t['titre']}")
                md_lines.append(f"- **Domaine :** {t['domaine']} ({t['source_vault']})")
                md_lines.append(f"- **Énigme à explorer :** {t['question']}")
                md_lines.append(f"- **Pont R0 suggéré :** {t['pont_r0']}\n")

            REPO_TRAVAUX_MD.write_text("\n".join(md_lines), encoding="utf-8")
            print("    -> [Derniers_Travaux_Forge.json] et [.md] générés avec succès.")
        except Exception as e:
            print(f"    [!] Erreur écriture travaux : {e}")

    # 4. Git Add, Commit & Push vers GitHub
    try:
        subprocess.run(["git", "add", "."], cwd=str(BASE_CLOUD_DIR), capture_output=True)
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(BASE_CLOUD_DIR), capture_output=True, text=True)

        if status_res.stdout.strip():
            print("[+] Envoi vers le ciel (git commit & git push)...")
            commit_msg = f"🌱 [Terre -> Ciel] Synchro forge, greffons & interets ({datetime.now().strftime('%Y-%m-%d %H:%M')}) [skip ci]"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_CLOUD_DIR), capture_output=True)
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_CLOUD_DIR), capture_output=True, text=True, timeout=40)
            if push_res.returncode == 0:
                print("    [OK] Transmissions terrestres envoyées avec succès à Alix dans le ciel !")
                return True
            else:
                print(f"    [!] Avertissement push : {push_res.stderr.strip()}")
        else:
            print("    [OK] Aucun nouveau thème terrestre à pousser (le ciel est déjà à jour).")
            return True
    except Exception as e:
        print(f"    [!] Erreur lors de l'envoi Git : {e}")

    return False

def sync_all():
    print("=" * 70)
    print(" 🌟 ALIX — NAVETTE BIDIRECTIONNELLE TERRE ⇄ CIEL (AVEC GREFFES O6)")
    print(f" Horodatage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Ciel -> Terre
    sync_ciel_vers_terre()

    # 2. Terre -> Ciel
    sync_terre_vers_ciel()

    print("\n" + "=" * 70)
    print(" ✨ SYNCHRONISATION BIDIRECTIONNELLE ACHEVÉE AVEC SUCCÈS")
    print("=" * 70)

if __name__ == "__main__":
    sync_all()
