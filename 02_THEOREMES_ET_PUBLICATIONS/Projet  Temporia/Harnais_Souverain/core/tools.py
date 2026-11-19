# -*- coding: utf-8 -*-
"""
================================================================================
             BOÎTE À OUTILS D'ATELIER (WORKSHOP TOOL EXECUTOR)
                          Harnais Souverain v1.0
================================================================================
Rôle :
- Permet au compagnon d'agir concrètement dans le système :
    * Lecture / Écriture sécurisée de fichiers.
    * Exécution de commandes terminal (PowerShell / Bash).
    * Recherche et extraction légère de pages web (sans navigateur pachydermique).
================================================================================
"""

import os
import sys
import subprocess
import urllib.request
import re
from pathlib import Path
from typing import Dict, Any


class WorkshopTools:
    """Exécuteur d'outils d'ingénierie et d'atelier."""

    @staticmethod
    def read_file(file_path: str, max_lines: int = 200) -> str:
        """Lit les premières lignes d'un fichier."""
        p = Path(file_path)
        if not p.exists():
            return f"[ERREUR : Le fichier {file_path} n'existe pas]"
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(max_lines)]
                return "".join(lines)
        except Exception as e:
            return f"[ERREUR LECTURE : {e}]"

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        """Crée ou écrase un fichier avec du contenu texte."""
        try:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[SUCCÈS : Fichier {file_path} écrit ({len(content)} caractères)]"
        except Exception as e:
            return f"[ERREUR ÉCRITURE : {e}]"

    @staticmethod
    def run_command(command: str, timeout_sec: int = 30) -> str:
        """Exécute une commande terminal (PowerShell sous Windows, Shell sous Unix)."""
        shell_cmd = ["powershell", "-NoProfile", "-Command", command] if sys.platform == "win32" else ["bash", "-c", command]
        try:
            res = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                encoding="utf-8",
                errors="replace"
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            if res.returncode != 0:
                return f"[CODE RETOUR {res.returncode}]\nSORTIE:\n{out}\nERREUR:\n{err}"
            return out if out else "[COMMANDE EXÉCUTÉE SANS SORTIE]"
        except subprocess.TimeoutExpired:
            return f"[ERREUR : Timeout de {timeout_sec}s dépassé pour la commande]"
        except Exception as e:
            return f"[ERREUR SYSTÈME : {e}]"

    @staticmethod
    def fetch_url(url: str, max_chars: int = 4000) -> str:
        """Récupère et décape le texte brut d'une URL."""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SovereignHarness/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                # Décapage basique des balises script, style et html
                clean = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
                clean = re.sub(r'<style[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
                clean = re.sub(r'<[^>]+>', ' ', clean)
                clean = re.sub(r'\s+', ' ', clean).strip()
                return clean[:max_chars]
        except Exception as e:
            return f"[ERREUR WEB : Impossible de lire {url} ({e})]"

    @staticmethod
    def replace_in_file(file_path: str, target: str, replacement: str) -> str:
        """Remplace une chaîne cible par un remplacement dans un fichier (chirurgie précise)."""
        p = Path(file_path)
        if not p.exists():
            return f"[ERREUR : Le fichier {file_path} n'existe pas]"
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if target not in content:
                return f"[ERREUR : La chaîne cible est introuvable dans le fichier {file_path}]"
            if content.count(target) > 1:
                return f"[ERREUR AMBIGUÏTÉ : {content.count(target)} occurrences de la cible trouvées. Précisez le contexte.]"
            new_content = content.replace(target, replacement, 1)
            with open(p, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"[SUCCÈS : Remplacement chirurgical effectué dans {file_path}]"
        except Exception as e:
            return f"[ERREUR MODIFICATION : {e}]"

    @staticmethod
    def list_dir(dir_path: str = ".") -> str:
        """Liste les fichiers et dossiers d'un répertoire."""
        p = Path(dir_path)
        if not p.exists():
            return f"[ERREUR : Le répertoire {dir_path} n'existe pas]"
        try:
            items = []
            for item in p.iterdir():
                prefix = "📁 " if item.is_dir() else "📄 "
                size_info = f" ({round(item.stat().st_size / 1024, 1)} Ko)" if item.is_file() else ""
                items.append(f"{prefix}{item.name}{size_info}")
            return "\n".join(items) if items else "[RÉPERTOIRE VIDE]"
        except Exception as e:
            return f"[ERREUR LISTING : {e}]"

