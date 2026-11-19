"""
================================================================================
                    ALIX SYNAPTIC GRAPH WEAVER & BRIDGE GENERATOR
                  Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
                  Auteur : Christian Duguay & Alix Assistant
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from alix.socle.alix_engine import AlixEngine

class GraphWeaver:
    def __init__(self, engine: AlixEngine):
        self.engine = engine

    def discover_bridges(self, min_similarity: float = 0.18, max_bridges: int = 25) -> List[Dict[str, Any]]:
        notes = self.engine.notes
        note_keys = self.engine.note_names
        sim_matrix = cosine_similarity(self.engine.tfidf_matrix)
        feature_names = self.engine.vectorizer.get_feature_names_out()

        n = len(note_keys)
        candidates = []

        # Étape 1 : Filtrage rapide des paires sans calculs superflus
        for i in range(n):
            doc_a = notes[note_keys[i]]
            for j in range(i + 1, n):
                doc_b = notes[note_keys[j]]
                
                if doc_a.title == doc_b.title:
                    continue

                # Vérifier si un lien direct existe déjà
                is_linked = (doc_b.title in doc_a.wikilinks) or (doc_a.title in doc_b.wikilinks)
                if is_linked:
                    continue

                sim = float(sim_matrix[i, j])
                if sim >= min_similarity:
                    is_cross_vault = doc_a.vault_name != doc_b.vault_name
                    candidates.append((i, j, sim, is_cross_vault))

        # Étape 2 : Trier d'abord les ponts inter-coffres les plus forts
        candidates.sort(key=lambda x: (1 if x[3] else 0, x[2]), reverse=True)
        top_candidates = candidates[:max_bridges]

        # Étape 3 : Extraire les concepts partagés UNIQUEMENT pour les gagnants retenus
        bridges = []
        for i, j, sim, is_cross_vault in top_candidates:
            doc_a = notes[note_keys[i]]
            doc_b = notes[note_keys[j]]

            row_a = self.engine.tfidf_matrix[i].toarray()[0]
            row_b = self.engine.tfidf_matrix[j].toarray()[0]
            prod = row_a * row_b
            non_zero_idx = np.where(prod > 0)[0]
            if len(non_zero_idx) > 0:
                top_local = non_zero_idx[np.argsort(prod[non_zero_idx])[-4:][::-1]]
                top_kw = [feature_names[idx] for idx in top_local]
            else:
                top_kw = []

            bridges.append({
                "note_a": doc_a.title,
                "vault_a": doc_a.vault_name,
                "path_a": doc_a.rel_path,
                "note_b": doc_b.title,
                "vault_b": doc_b.vault_name,
                "path_b": doc_b.rel_path,
                "similarity": round(sim, 4),
                "cross_vault": is_cross_vault,
                "shared_concepts": top_kw
            })

        return bridges

    def export_markdown_map(self, bridges: List[Dict[str, Any]], target_path: Path):
        content = [
            "# 🌌 Cartographie des Ponts Synaptiques Découverts (Cerveau Alix)",
            "",
            "> Généré automatiquement par **Alix Graph Weaver** — Système VERALUME × KAIROS V6.",
            f"> Date : 2026-08-31 · Total ponts trans-coffres identifiés : **{len(bridges)}**",
            "",
            "---",
            "",
            "## 🌉 Ponts Synaptiques Inter-Coffres (Connexions Cachées Révélées)",
            ""
        ]

        for idx, b in enumerate(bridges, 1):
            badge = "🌌 **[INTER-COFFRES]**" if b["cross_vault"] else "📁 [Intra-Coffre]"
            content.append(f"### {idx}. [[{b['note_a']}]] ⟷ [[{b['note_b']}]]")
            content.append(f"- **Statut** : {badge}")
            content.append(f"- **Coffres** : `{b['vault_a']}` ⟷ `{b['vault_b']}`")
            content.append(f"- **Score de Résonance** : `{b['similarity']}`")
            if b["shared_concepts"]:
                content.append(f"- **Pivots Partagés** : {', '.join(b['shared_concepts'])}")
            content.append("")

        content.append("---")
        content.append("*Note : Ce document établit les liaisons sémantiques entre vos 4 coffres Obsidian pour enrichir votre vue graphique globale.*")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

def main():
    parser = argparse.ArgumentParser(description="Alix Synaptic Graph Weaver & Bridge Generator")
    parser.add_argument("command", choices=["scan", "export"], help="Action Graph Weaver")
    parser.add_argument("--min-sim", type=float, default=0.20, help="Similarité minimale (défaut: 0.20)")
    parser.add_argument("--max", type=int, default=15, help="Nombre max de ponts")
    parser.add_argument("--out", type=str, default=str((VAULT_DIR / "PONT_SYNAPTIQUE_VERALUME.md")), help="Fichier de sortie MD")
    parser.add_argument("--json", action="store_true", help="Format JSON")

    args = parser.parse_args()

    t0 = time.time()
    engine = AlixEngine()
    weaver = GraphWeaver(engine)

    bridges = weaver.discover_bridges(min_similarity=args.min_sim, max_bridges=args.max)

    if args.command == "scan":
        if args.json:
            print(json.dumps(bridges, indent=2, ensure_ascii=False))
        else:
            print("\n=======================================================")
            print(f" 🌐 DÉCOUVERTE DE PONTS SYNAPTIQUES ({len(bridges)} Identifiés)")
            print("=======================================================")
            for i, b in enumerate(bridges, 1):
                cross = "🌌 [INTER-COFFRES]" if b['cross_vault'] else "📁 [Intra-Coffre]"
                print(f"[{i}] [[{b['note_a']}]] ({b['vault_a']})")
                print(f"    ⟷ [[{b['note_b']}]] ({b['vault_b']})")
                print(f"    Proximité : {b['similarity']} | {cross}")
                if b['shared_concepts']:
                    print(f"    Pivots    : {', '.join(b['shared_concepts'])}")
                print("-" * 55)
            print(f"Temps de calcul : {(time.time() - t0)*1000:.1f} ms")

    elif args.command == "export":
        out_file = Path(args.out)
        weaver.export_markdown_map(bridges, out_file)
        print(f"\n✅ Cartographie synaptique exportée avec succès dans : {out_file}")
        print(f"Temps de calcul : {(time.time() - t0)*1000:.1f} ms")

if __name__ == "__main__":
    main()
