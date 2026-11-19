"""
Alix Vault Topology & Health Auditor
Système: VERALUME × KAIROS V6
Auteur: Christian Duguay & Alix
"""

from alix.socle.chemins import VAULT_DIR
import os
import re
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configuration de l'encodage standard pour l'environnement Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VAULT_PATH = VAULT_DIR

def extract_wikilinks(content: str) -> List[str]:
    """Extrait tous les liens de type [[Cible]] ou [[Cible|Titre]] du contenu markdown."""
    pattern = r"\[\[(.*?)\]\]"
    matches = re.findall(pattern, content)
    targets = []
    for match in matches:
        # Si le lien est au format [[Cible|Texte Affiché]]
        target = match.split("|")[0].split("#")[0].strip()
        if target:
            targets.append(target)
    return targets

def audit_vault(vault_dir: Path):
    md_files = [f for f in vault_dir.glob("*.md") if not f.name.startswith(".")]
    note_names = {f.stem: f for f in md_files}
    
    in_links: Dict[str, Set[str]] = {name: set() for name in note_names}
    out_links: Dict[str, Set[str]] = {name: set() for name in note_names}
    broken_links: Dict[str, List[str]] = {}
    
    for name, file_path in note_names.items():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
                
        targets = extract_wikilinks(content)
        for target in targets:
            if target in note_names:
                out_links[name].add(target)
                in_links[target].add(name)
            else:
                if name not in broken_links:
                    broken_links[name] = []
                broken_links[name].append(target)
                
    # Statistiques
    total_notes = len(note_names)
    total_links = sum(len(links) for links in out_links.values())
    
    # Nœuds orphelins (aucune note ne pointe vers eux, sauf TABLEAU_DE_BORD)
    orphans = [name for name, links in in_links.items() if len(links) == 0 and name != "TABLEAU_DE_BORD"]
    
    # Nœuds culs-de-sac (ne pointent vers aucune autre note)
    dead_ends = [name for name, links in out_links.items() if len(links) == 0]
    
    # Top Hubs (les plus connectés)
    sorted_by_in = sorted(in_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    sorted_by_out = sorted(out_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    
    # Matrice d'adjacence pour calcul Phi
    node_list = sorted(list(note_names.keys()))
    node_idx = {name: i for i, name in enumerate(node_list)}
    adj_matrix = np.zeros((total_notes, total_notes), dtype=float)
    for src, targets in out_links.items():
        i = node_idx[src]
        for tgt in targets:
            j = node_idx[tgt]
            adj_matrix[i, j] = 1.0
            adj_matrix[j, i] = 1.0 # Graphe non-orienté pour la cohérence globale
            
    density = (2 * total_links) / (total_notes * (total_notes - 1) + 1e-9) if total_notes > 1 else 0

    print("==========================================================")
    print(" 📊 RAPPORT D'AUDIT TOPOLOGIQUE DU CERVEAU ALIX ")
    print("==========================================================")
    print(f"📁 Emplacement : {vault_dir}")
    print(f"📄 Total Notes Markdown : {total_notes}")
    print(f"🔗 Total Liens Internes Actifs : {total_links}")
    print(f"🌐 Densité du Graphe Synaptique : {density:.4f}")
    print("----------------------------------------------------------")
    print(f"⚠️  Nœuds Orphelins (0 lien entrant) : {len(orphans)}")
    if orphans:
        for o in orphans[:8]:
            print(f"   - [[{o}]]")
        if len(orphans) > 8:
            print(f"   ... et {len(orphans) - 8} autres.")
            
    print(f"\n🔍 Liens Bruns / Cibles Inexistantes : {sum(len(v) for v in broken_links.values())}")
    for src, targets in list(broken_links.items())[:5]:
        print(f"   Dans [[{src}]] -> {targets}")
        
    print("\n👑 Top 5 Pôles d'Attraction (Liens Entrants) :")
    for name, links in sorted_by_in:
        print(f"   - [[{name}]] : {len(links)} références")
        
    print("\n⚡ Top 5 Pôles d'Émission (Liens Sortants) :")
    for name, links in sorted_by_out:
        print(f"   - [[{name}]] : {len(links)} connexions sortantes")
    print("==========================================================\n")
    
    # Génération de la note de synthèse dans le coffre
    report_md = f"""---
titre: "Audit Topologique & Santé du Graphe Synaptique"
date: "{np.datetime64('now')}"
systeme: "VERALUME × KAIROS V6"
tags:
  - exocerveau
  - audit_topologique
  - sante_graphe
  - alix
---

# 📊 [[Audit_Topologique_Cerveau_Alix]]

> **Statut du Coffre :** Opérationnel  
> **Nombre Total de Notes :** `{total_notes}`  
> **Nombre de Liens Internes :** `{total_links}`  
> **Densité du Réseau :** `{density:.4f}`

---

## 👑 Pôles Majeurs d'Attraction (Nœuds Piliers)
{chr(10).join([f"- [[{name}]] ({len(links)} liens entrants)" for name, links in sorted_by_in])}

## ⚡ Pôles Majeurs d'Émission (Cartographies & Hubs)
{chr(10).join([f"- [[{name}]] ({len(links)} liens sortants)" for name, links in sorted_by_out])}

---

## 🧩 Nœuds Orphelins à Raccorder ({len(orphans)})
{chr(10).join([f"- [[{o}]]" for o in orphans]) if orphans else "_Aucun nœud orphelin : le graphe est totalement connexe._"}

---

## 🔍 Liens Pointant vers des Notes Non-Créées ({sum(len(v) for v in broken_links.values())})
{chr(10).join([f"- Dans [[{src}]] : " + ", ".join([f"`{t}`" for t in targets]) for src, targets in broken_links.items()]) if broken_links else "_Aucun lien brisé._"}

---
*Généré automatiquement par `alix_vault_audit.py`.*
"""
    report_path = vault_dir / "Audit_Topologique_Cerveau_Alix.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"✅ Note d'audit générée : {report_path.name}")

if __name__ == "__main__":
    audit_vault(VAULT_PATH)
