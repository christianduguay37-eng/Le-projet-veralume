# -*- coding: utf-8 -*-
"""
================================================================================
          🛠️ SOVEREIGN COCKPIT TOOLS — EXÉCUTEUR D'OUTILS D'ATELIER
================================================================================
Auteurs : Christian Duguay & Alix Copilote
Système : VERALUME × KAIROS V6 × Intel Core Ultra 7 258V
Rôle    : Boîte à outils de pair-programming pour le Cockpit Souverain :
          - Manipulation chirurgicale de fichiers (view, write, patch)
          - Exécution sécurisée de commandes terminal PowerShell
          - Scanner de l'Exocerveau (recherche instantanée dans les coffres)
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, VAULT_DIR
from alix.socle.chemins import fichier_module  # rénovation : modules du paquet, plus la strate A
import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Encodage console UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class SovereignTools:
    """Moteur d'exécution des outils d'ingénierie et d'agentivité souveraine."""

    BASE_WORKSPACE = DOCUMENTS_DIR

    @classmethod
    def view_file(cls, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Affiche le contenu d'un fichier avec pagination par lignes (1-indexé)."""
        p = Path(path)
        if not p.is_absolute():
            p = (cls.BASE_WORKSPACE / path).resolve()
            
        if not p.exists():
            return f"❌ [Erreur : Le fichier '{p}' n'existe pas]"
        if p.is_dir():
            return f"❌ [Erreur : '{p}' est un répertoire, pas un fichier]"

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return f"❌ [Erreur de lecture : {e}]"

        total = len(lines)
        s = max(1, start_line) if start_line else 1
        e = min(total, end_line) if end_line else total
        
        if s > total:
            return f"⚠️ [Le fichier ne contient que {total} lignes (début demandé: {s})]"

        extracted = lines[s - 1 : e]
        result = [f"--- File: {p} ({total} lines total, displaying {s}-{e}) ---"]
        for idx, line in enumerate(extracted, start=s):
            result.append(f"{idx:4d} | {line.rstrip()}")
            
        return "\n".join(result)

    @classmethod
    def write_file(cls, path: str, content: str, overwrite: bool = True) -> str:
        """Crée ou écrase un fichier avec du contenu texte."""
        p = Path(path)
        if not p.is_absolute():
            p = (cls.BASE_WORKSPACE / path).resolve()

        if p.exists() and not overwrite:
            return f"❌ [Erreur : Le fichier '{p}' existe déjà et overwrite=False]"

        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            return f"✅ [Fichier écrit avec succès : '{p}' ({len(content)} caractères, {len(content.splitlines())} lignes)]"
        except Exception as e:
            return f"❌ [Erreur d'écriture : {e}]"

    @classmethod
    def replace_file_content(cls, path: str, target_content: str, replacement_content: str) -> str:
        """Remplace une portion de texte exacte dans un fichier."""
        p = Path(path)
        if not p.is_absolute():
            p = (cls.BASE_WORKSPACE / path).resolve()

        if not p.exists():
            return f"❌ [Erreur : Fichier '{p}' introuvable]"

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if target_content not in content:
                return f"❌ [Erreur de patch : Le texte cible n'a pas été trouvé dans '{p}']"

            occurrences = content.count(target_content)
            if occurrences > 1:
                return f"⚠️ [Ambiguïté : {occurrences} occurrences trouvées. Remplacement annulé pour éviter une corruption.]"

            new_content = content.replace(target_content, replacement_content, 1)
            with open(p, "w", encoding="utf-8", errors="replace") as f:
                f.write(new_content)

            return f"✅ [Patch appliqué avec succès dans '{p}' (1 occurrence remplacée)]"
        except Exception as e:
            return f"❌ [Erreur d'application du patch : {e}]"

    # Pare-feu déterministe anti-commandes destructrices (PowerShell & Cmd)
    PROHIBITED_COMMAND_PATTERNS = [
        re.compile(r"\b(remove-item|ri|rmdir|rd)\b.*(-r|-recurse|/s)", re.IGNORECASE),
        re.compile(r"\b(del|rm|erase)\b.*(/s|-r|-recurse)", re.IGNORECASE),
        re.compile(r"\b(format-volume|diskpart)\b", re.IGNORECASE),
        re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE),
        re.compile(r"\b(clear-content|clc)\b", re.IGNORECASE),
        re.compile(r"\b(stop-computer|restart-computer|shutdown)\b", re.IGNORECASE),
    ]

    FORBIDDEN_ROOTS = [
        Path(r"C:\Windows"),
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(r"C:\\"),
    ]

    @classmethod
    def run_command(cls, command: str, cwd: Optional[str] = None, timeout: int = 60) -> str:
        """Exécute une commande terminal PowerShell sous Windows avec capture complète et pare-feu déterministe."""
        # 1. Validation du pare-feu anti-destruction
        clean_cmd = command.strip()
        for pattern in cls.PROHIBITED_COMMAND_PATTERNS:
            if pattern.search(clean_cmd):
                return (
                    f"🛑 [PARE-FEU DÉTERMINISTE SOVEREIGN ACTIVÉ]\n"
                    f"Commande bloquée : tentative d'exécution d'une commande destructrice détectée ({pattern.pattern}).\n"
                    f"L'Atelier interdit l'écrasement ou l'effacement récursif direct."
                )

        # 2. Confinement strict du répertoire d'exécution (Sandboxing de base)
        work_dir = Path(cwd).resolve() if cwd else cls.BASE_WORKSPACE.resolve()
        if not work_dir.exists():
            work_dir = cls.BASE_WORKSPACE.resolve()

        # Interdiction formelle de s'exécuter à la racine du système ou dans Windows
        for forbidden in cls.FORBIDDEN_ROOTS:
            try:
                if work_dir == forbidden or work_dir.resolve() == forbidden.resolve():
                    return f"🛑 [PARE-FEU SOVEREIGN] Interdiction d'exécuter une commande dans le répertoire sensible : '{work_dir}'"
            except Exception:
                pass

        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            code = proc.returncode

            res = []
            if out:
                res.append(f"[STDOUT]\n{out}")
            if err:
                res.append(f"[STDERR]\n{err}")
            res.append(f"[CODE DE SORTIE : {code}]")

            return "\n\n".join(res) if res else "[COMMANDE EXÉCUTÉE SANS SORTIE]"
        except subprocess.TimeoutExpired:
            return f"⏱️ [Erreur : Commande interrompue après {timeout} secondes]"
        except Exception as e:
            return f"❌ [Erreur système lors de l'exécution : {e}]"

    @classmethod
    def list_dir(cls, path: str = ".") -> str:
        """Liste les fichiers et répertoires avec taille et horodatage."""
        p = Path(path)
        if not p.is_absolute():
            p = (cls.BASE_WORKSPACE / path).resolve()

        if not p.exists():
            return f"❌ [Erreur : Répertoire '{p}' introuvable]"

        try:
            items = []
            for item in sorted(p.iterdir()):
                sym = "📁" if item.is_dir() else "📄"
                size = f"{item.stat().st_size:,} octets" if item.is_file() else "DIR"
                items.append(f"{sym} {item.name:40} | {size}")
            return f"--- Répertoire : {p} ({len(items)} éléments) ---\n" + "\n".join(items)
        except Exception as e:
            return f"❌ [Erreur : {e}]"

    @classmethod
    def search_memory(cls, query: str) -> str:
        """Interroge l'Exocerveau Obsidian via le moteur flash alix_interroger_memoire.py."""
        script = fichier_module("alix.sondes.alix_interroger_memoire")
        if not script.exists():
            return "⚠️ [Moteur d'interrogation flash introuvable]"

        try:
            res = subprocess.run(
                [sys.executable, str(script), query],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15
            )
            return res.stdout.strip() or "Aucun résultat trouvé dans l'exocerveau."
        except Exception as e:
            return f"❌ [Erreur recherche mémoire : {e}]"

    @classmethod
    def get_tool_definitions(cls) -> List[Dict[str, Any]]:
        """Renvoie les définitions d'outils au format standardisé OpenAI Tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "view_file",
                    "description": "Lit le contenu d'un fichier texte avec support de pagination par lignes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Chemin absolu ou relatif vers le fichier"},
                            "start_line": {"type": "integer", "description": "Ligne de début (1-indexé)"},
                            "end_line": {"type": "integer", "description": "Ligne de fin inclusive"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Crée ou écrase un fichier avec du contenu texte.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Chemin du fichier à créer ou modifier"},
                            "content": {"type": "string", "description": "Contenu texte complet à écrire"},
                            "overwrite": {"type": "boolean", "description": "Écraser si le fichier existe (True par défaut)"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "replace_file_content",
                    "description": "Remplace une portion de texte exacte et unique dans un fichier (patch chirurgical).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Chemin du fichier cible"},
                            "target_content": {"type": "string", "description": "Chaîne exacte à remplacer"},
                            "replacement_content": {"type": "string", "description": "Nouveau contenu de remplacement"}
                        },
                        "required": ["path", "target_content", "replacement_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Exécute une commande terminal PowerShell sous Windows dans le répertoire spécifié.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Ligne de commande PowerShell exacte à exécuter"},
                            "cwd": {"type": "string", "description": "Répertoire de travail (optionnel)"},
                            "timeout": {"type": "integer", "description": "Délai max en secondes (60 par défaut)"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "Liste les fichiers et sous-répertoires d'un dossier.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Chemin du répertoire"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Recherche instantanément des notes, solutions, clés ou concepts dans l'Exocerveau Obsidian.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Terme ou expression à rechercher"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    @classmethod
    def execute_tool(cls, name: str, args: Dict[str, Any]) -> str:
        """Route et exécute un outil par son nom et ses arguments."""
        if name == "view_file":
            return cls.view_file(args.get("path", ""), args.get("start_line"), args.get("end_line"))
        elif name == "write_file":
            return cls.write_file(args.get("path", ""), args.get("content", ""), args.get("overwrite", True))
        elif name == "replace_file_content":
            return cls.replace_file_content(args.get("path", ""), args.get("target_content", ""), args.get("replacement_content", ""))
        elif name == "run_command":
            return cls.run_command(args.get("command", ""), args.get("cwd"), args.get("timeout", 60))
        elif name == "list_dir":
            return cls.list_dir(args.get("path", "."))
        elif name == "search_memory":
            return cls.search_memory(args.get("query", ""))
        else:
            return f"❌ [Outil inconnu : '{name}']"
