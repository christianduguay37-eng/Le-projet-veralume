# -*- coding: utf-8 -*-
"""
================================================================================
                    CODE-GRAPH ENGINE (AST & SYMBOL NAVIGATION)
                     Composant Déterministe pour Agent SWE
================================================================================
Rôle :
- Parse le dépôt cible via l'arbre syntaxique abstrait (AST standard de Python).
- Cartographie les classes, méthodes, fonctions, dépendances et plages de lignes.
- Permet à l'agent de naviguer instantanément dans le graphe en O(1) sans scanner
  des dizaines de fichiers texte ni gaspiller des milliers de tokens de contexte.
================================================================================
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class CodeGraphEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.file_map: Dict[str, List[str]] = {}
        self.build_graph()

    def build_graph(self):
        """Scanne tous les fichiers .py et extrait les symboles."""
        self.nodes.clear()
        self.file_map.clear()

        for py_file in self.root_dir.rglob("*.py"):
            rel_path = str(py_file.relative_to(self.root_dir)).replace("\\", "/")
            self.file_map[rel_path] = []

            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    sym_id = f"{rel_path}::{node.name}"
                    doc = ast.get_docstring(node) or ""
                    self.nodes[sym_id] = {
                        "type": "class",
                        "name": node.name,
                        "file": rel_path,
                        "start_line": getattr(node, "lineno", 1),
                        "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                        "docstring": doc.strip()
                    }
                    self.file_map[rel_path].append(sym_id)

                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            m_id = f"{rel_path}::{node.name}.{item.name}"
                            m_doc = ast.get_docstring(item) or ""
                            self.nodes[m_id] = {
                                "type": "method",
                                "name": f"{node.name}.{item.name}",
                                "class": node.name,
                                "file": rel_path,
                                "start_line": getattr(item, "lineno", 1),
                                "end_line": getattr(item, "end_lineno", getattr(item, "lineno", 1)),
                                "docstring": m_doc.strip()
                            }
                            self.file_map[rel_path].append(m_id)

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Vérifier si ce n'est pas déjà capturé comme méthode
                    sym_id = f"{rel_path}::{node.name}"
                    if sym_id not in self.nodes:
                        f_doc = ast.get_docstring(node) or ""
                        self.nodes[sym_id] = {
                            "type": "function",
                            "name": node.name,
                            "file": rel_path,
                            "start_line": getattr(node, "lineno", 1),
                            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                            "docstring": f_doc.strip()
                        }
                        self.file_map[rel_path].append(sym_id)

    def query(self, search_term: str) -> List[Dict[str, Any]]:
        """Recherche les symboles dont le nom ou la docstring contient le terme."""
        term_low = search_term.lower().strip()
        matches = []
        for sym_id, data in self.nodes.items():
            if term_low in data["name"].lower() or term_low in data["docstring"].lower() or term_low in data["file"].lower():
                matches.append({"id": sym_id, **data})
        return matches

    def get_compact_summary(self) -> str:
        """Génère un résumé ultra-dense du graphe de code (idéal pour prompt LLM)."""
        lines = []
        for rel_path, syms in self.file_map.items():
            lines.append(f"📁 {rel_path} :")
            for sym in syms:
                info = self.nodes[sym]
                lines.append(f"   - {info['type']} `{info['name']}` (Lignes {info['start_line']}-{info['end_line']})")
        return "\n".join(lines)

    def export_json(self, out_path: Path):
        """Exporte le graphe en JSON."""
        data = {
            "root": str(self.root_dir),
            "total_symbols": len(self.nodes),
            "files": self.file_map,
            "symbols": self.nodes
        }
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    repo_path = Path(__file__).parent / "target_repo"
    engine = CodeGraphEngine(repo_path)
    print("📊 [CODE-GRAPH ENGINE] Résumé compact du dépôt :")
    print(engine.get_compact_summary())
    engine.export_json(Path(__file__).parent / "code_graph.json")
    print(f"\n✅ Graphe exporté : {len(engine.nodes)} symboles cartographiés.")
