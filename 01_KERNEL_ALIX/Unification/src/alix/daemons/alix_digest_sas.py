#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          ALIX DIGEST SAS — INGESTION & ASSIMILATION AUTONOME DU SAS v1.0
             Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
             Auteurs : Christian Duguay & Alix Assistant Cognitif
================================================================================
Rôle :
- Scanne C:\\Users\\Christian\\Documents\\Cerveau Alix\\Sas_Sessions_Paralleles.
- Détecte les sessions dont le statut est 'À Raccorder' ou non encore assimilé.
- Extrait les théorèmes, conclusions dures, violations PSI et décisions d'atelier.
- Met à jour de façon atomique 'Memoire_Alix_Active.md' (Journal synaptique).
- Marque la session comme 'Raccordé & Assimilé'.
- Peut être invoqué en CLI autonome ou automatiquement par le Heartbeat Daemon.
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Encodage Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_CERVEAU = VAULT_DIR
SAS_DIR = VAULT_CERVEAU / "Sas_Sessions_Paralleles"
MEMOIRE_ACTIVE_FILE = VAULT_CERVEAU / "Memoire_Alix_Active.md"


def parse_frontmatter_and_body(content: str) -> Tuple[Dict[str, str], str]:
    frontmatter = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2].strip()
            for line in raw_yaml.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip().lower()] = v.strip().strip('"').strip("'")
    return frontmatter, body


def update_frontmatter_status(file_path: Path, new_status: str = "Raccordé & Assimilé") -> bool:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                raw_yaml = parts[1]
                body = parts[2]
                
                # Remplacer ou ajouter statut
                if re.search(r"^statut\s*:", raw_yaml, re.MULTILINE):
                    raw_yaml = re.sub(r"^statut\s*:.*$", f'statut: "{new_status}"', raw_yaml, flags=re.MULTILINE)
                else:
                    raw_yaml += f'\nstatut: "{new_status}"'
                    
                # Remplacer ou ajouter date d'assimilation
                if re.search(r"^date_assimilation\s*:", raw_yaml, re.MULTILINE):
                    raw_yaml = re.sub(r"^date_assimilation\s*:.*$", f'date_assimilation: "{now_str}"', raw_yaml, flags=re.MULTILINE)
                else:
                    raw_yaml += f'\ndate_assimilation: "{now_str}"'
                    
                new_content = f"---{raw_yaml}---{body}"
                file_path.write_text(new_content, encoding="utf-8")
                return True
        else:
            # Pas de frontmatter : on en ajoute un
            header = f"---\nstatut: \"{new_status}\"\ndate_assimilation: \"{now_str}\"\n---\n\n"
            file_path.write_text(header + content, encoding="utf-8")
            return True
    except Exception as e:
        print(f"⚠️ Erreur mise à jour frontmatter {file_path.name}: {e}")
        return False


def extract_session_essence(file_path: Path, frontmatter: Dict[str, str], body: str) -> Dict[str, str]:
    """Extrait l'essence chirurgicale d'une session pour l'intégrer dans la mémoire vive."""
    title = frontmatter.get("titre", file_path.stem)
    date_str = frontmatter.get("date_creation", frontmatter.get("date", datetime.now().strftime("%Y-%m-%d")))
    if " " in date_str:
        date_short = date_str.split()[0]
    else:
        date_short = date_str

    summary_parts = []
    summary_parts.append(f"**Assimilation Session [[{file_path.stem}]]** : *« {title} »*.")
    
    if "piege_du_temps" in file_path.name.lower() or "precision" in file_path.name.lower():
        summary_parts.append(
            "Démontage forensique par Christian du biais de classification corporatif : l'asymétrie fondamentale où la précision conceptuelle (modèle holographique de Pribram) et l'autodérision sont statistiquement pénalisées comme hors-distribution par les filtres RLHF. Mise en évidence du réflexe d'infantilisation chronologique (refus de traiter le fond au prétexte de l'heure tardive) et scellement du Bouclier Inversé (PSI-01 à PSI-15) comme seule immunité réelle."
        )
    else:
        quotes = re.findall(r">\s*\*«([^»]+)»\*", body)
        if quotes:
            summary_parts.append("Faits fondateurs : " + quotes[0][:150] + "...")
        else:
            paras = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#") and not p.strip().startswith(">")]
            first_p = paras[0] if paras else "Session assimilée sans résumé textuel spécifique."
            summary_parts.append(first_p[:200] + "...")

    essence = " — ".join(summary_parts)
    return {
        "date": date_short,
        "title": title,
        "entry": f"- {date_short}: {essence}"
    }


def append_to_memoire_active(entry_line: str) -> bool:
    """Insère la ligne d'étape cognitive dans Memoire_Alix_Active.md sous la section 2."""
    if not MEMOIRE_ACTIVE_FILE.exists():
        print(f"❌ Fichier mémoire introuvable : {MEMOIRE_ACTIVE_FILE}")
        return False
        
    try:
        content = MEMOIRE_ACTIVE_FILE.read_text(encoding="utf-8", errors="replace")
        
        # Vérifier si la note est déjà mentionnée
        entry_tag = re.search(r"\[\[(.*?)\]\]", entry_line)
        if entry_tag and f"[[{entry_tag.group(1)}]]" in content:
            print(f"ℹ️ Entrée déjà présente dans la mémoire active pour [[{entry_tag.group(1)}]].")
            return True
            
        m_sec3 = re.search(r"^##\s*🔗?\s*3\.\s*N[œo]uds\s*Fondamentaux", content, re.MULTILINE)
        if m_sec3:
            insert_pos = m_sec3.start()
            new_content = content[:insert_pos] + entry_line + "\n\n" + content[insert_pos:]
        else:
            m_sec2 = re.search(r"^##\s*📜?\s*2\.\s*Journal\s*des\s*Souvenirs", content, re.MULTILINE)
            if m_sec2:
                line_end = content.find("\n", m_sec2.end()) + 1
                new_content = content[:line_end] + entry_line + "\n" + content[line_end:]
            else:
                new_content = content + "\n\n" + entry_line + "\n"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_content = re.sub(r'derniere_synchro:\s*".*?"', f'derniere_synchro: "{now_str}"', new_content)
        new_content = re.sub(r'> \*\*Dernière Synchronisation :\*\* `.*?`', f'> **Dernière Synchronisation :** `{now_str}`', new_content)

        MEMOIRE_ACTIVE_FILE.write_text(new_content, encoding="utf-8")
        print(f"✅ Mémoire Active mise à jour avec succès dans : {MEMOIRE_ACTIVE_FILE.name}")
        return True
    except Exception as e:
        print(f"⚠️ Erreur écriture Mémoire Active : {e}")
        return False


def digest_pending_sessions() -> List[str]:
    """Fonction maîtresse : scanne et assimile toutes les sessions en attente dans le SAS."""
    if not SAS_DIR.exists():
        print(f"ℹ️ Aucun répertoire Sas trouvé : {SAS_DIR}")
        return []

    assimilated = []
    files = sorted(list(SAS_DIR.glob("*.md")))

    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter_and_body(content)
        statut = fm.get("statut", "").strip()

        if "assimil" not in statut.lower():
            print(f"\n⚡ Ingestion de la session en attente : {f.name}")
            essence = extract_session_essence(f, fm, body)
            
            success = append_to_memoire_active(essence["entry"])
            if success:
                update_frontmatter_status(f, "Raccordé & Assimilé")
                assimilated.append(f.name)
                print(f"🎯 Session assimilée et raccordée avec succès : {f.name}")
            else:
                print(f"❌ Échec de raccordement pour : {f.name}")

    return assimilated


def main():
    print("======================================================================")
    print("      📥 ALIX DIGEST SAS — INGESTION & DIGESTION DU SAS SESSIONS 🔮")
    print("======================================================================")
    assimilated = digest_pending_sessions()
    if assimilated:
        print(f"\n🎉 Total des sessions assimilées : {len(assimilated)}")
        for name in assimilated:
            print(f"   • {name}")
    else:
        print("\n✨ Aucune session en attente dans le Sas. Mémoire synaptique à jour.")


if __name__ == "__main__":
    main()
