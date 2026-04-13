"""
OMNI AGENT — Outil Filesystem
Lecture, écriture, listing de fichiers.
"""

import os
from pathlib import Path
from typing import Any
from tools.base import Tool


class FilesystemTool(Tool):
    
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def description(self) -> str:
        return "Opérations fichiers: read, write, list, exists. Pour manipuler des fichiers et répertoires."
    
    @property
    def parameters(self) -> dict:
        return {
            "operation": {"type": "string", "enum": ["read", "write", "list", "exists", "mkdir"]},
            "path": {"type": "string", "description": "Chemin du fichier/répertoire"},
            "content": {"type": "string", "description": "Contenu à écrire (pour write)"},
        }
    
    async def execute(self, operation: str = "", path: str = "", 
                      content: str = "", **kwargs) -> Any:
        if not operation or not path:
            return {"error": "operation et path requis"}
        
        p = Path(path).expanduser()
        
        try:
            match operation:
                case "read":
                    if not p.exists():
                        return {"error": f"Fichier introuvable: {path}"}
                    text = p.read_text(encoding="utf-8", errors="replace")
                    return {"content": text[:50000], "size": p.stat().st_size}
                
                case "write":
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(content, encoding="utf-8")
                    return {"written": len(content), "path": str(p)}
                
                case "list":
                    if not p.is_dir():
                        return {"error": f"Pas un répertoire: {path}"}
                    entries = []
                    for item in sorted(p.iterdir()):
                        entries.append({
                            "name": item.name,
                            "type": "dir" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None,
                        })
                    return {"entries": entries[:200], "total": len(entries)}
                
                case "exists":
                    return {"exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir()}
                
                case "mkdir":
                    p.mkdir(parents=True, exist_ok=True)
                    return {"created": str(p)}
                
                case _:
                    return {"error": f"Opération inconnue: {operation}"}
        
        except PermissionError:
            return {"error": f"Permission refusée: {path}"}
        except Exception as e:
            return {"error": str(e)}
