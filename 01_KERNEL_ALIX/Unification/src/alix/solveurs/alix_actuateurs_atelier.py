# -*- coding: utf-8 -*-
"""
================================================================================
       ALIX ACTUATEURS D'ATELIER v1.0 — LES MAINS SOUVERAINES DU SILICIUM
       Moteur d'Exécution d'Outils & d'Actions Système pour l'Exocerveau Local
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Système : VERALUME × KAIROS V6 (Lunar Lake 258V)
Rôle    : Donner des mains physiques au cerveau local (NPU, GPU Arc, CPU Ollama)
          pour lire, écrire, modifier des fichiers, exécuter des commandes
          et interroger les 4 coffres sans dépendance cloud.
================================================================================
"""

from alix.socle.chemins import ETAT_VIVANT_DIR, TEMPORIA_DIR, VAULT_DIR
import os
import sys
import re
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Fix encodage console Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Répertoires maîtres
VAULT_CERVEAU_ALIX = VAULT_DIR
WORKSPACE_TEMPORIA = TEMPORIA_DIR
DOWNLOADS_ALIX = ETAT_VIVANT_DIR

# ================================================================================
# 🛠️ 1. OUTILS FONDAMENTAUX D'ATELIER (ACTUATEURS)
# ================================================================================

def lire_fichier(chemin: str, start_line: int = 1, end_line: int = 800) -> Dict[str, Any]:
    """Lit un fichier texte ou markdown avec pagination de lignes (1-indexé)."""
    p = Path(chemin)
    if not p.is_absolute():
        p = VAULT_CERVEAU_ALIX / chemin
    if not p.exists():
        return {"status": "error", "message": f"Fichier introuvable : {p}"}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, end_line)
        selected_lines = lines[start_idx:end_idx]
        formatted = "".join([f"{i+start_idx+1}: {l}" for i, l in enumerate(selected_lines)])
        return {
            "status": "success",
            "file": str(p),
            "total_lines": total_lines,
            "start_line": start_line,
            "end_line": end_idx,
            "content": formatted
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ecrire_fichier(chemin: str, contenu: str, overwrite: bool = True) -> Dict[str, Any]:
    """Crée ou écrase un fichier avec le contenu spécifié."""
    p = Path(chemin)
    if not p.is_absolute():
        p = VAULT_CERVEAU_ALIX / chemin
    if p.exists() and not overwrite:
        return {"status": "error", "message": f"Le fichier existe déjà et overwrite=False : {p}"}
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(contenu)
        return {"status": "success", "file": str(p), "bytes_written": len(contenu.encode('utf-8'))}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def modifier_fichier(chemin: str, cible: str, remplacement: str) -> Dict[str, Any]:
    """Remplace exactement une chaîne cible par un remplacement dans un fichier."""
    p = Path(chemin)
    if not p.is_absolute():
        p = VAULT_CERVEAU_ALIX / chemin
    if not p.exists():
        return {"status": "error", "message": f"Fichier introuvable : {p}"}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if cible not in content:
            return {"status": "error", "message": "La chaîne cible est introuvable dans le fichier."}
        occurrences = content.count(cible)
        if occurrences > 1:
            return {"status": "error", "message": f"Ambiguïté : {occurrences} occurrences de la cible trouvées."}
        new_content = content.replace(cible, remplacement, 1)
        with open(p, "w", encoding="utf-8") as f:
            f.write(new_content)
        return {"status": "success", "file": str(p), "message": "Remplacement chirurgical effectué avec succès."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def lister_dossier(chemin: str = "") -> Dict[str, Any]:
    """Liste les dossiers et fichiers d'un répertoire."""
    p = Path(chemin) if chemin else VAULT_CERVEAU_ALIX
    if not p.is_absolute():
        p = VAULT_CERVEAU_ALIX / chemin
    if not p.exists():
        return {"status": "error", "message": f"Dossier introuvable : {p}"}
    try:
        items = []
        for item in p.iterdir():
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_kb": round(item.stat().st_size / 1024, 2) if item.is_file() else 0
            })
        return {"status": "success", "path": str(p), "total_items": len(items), "items": items[:50]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def executer_commande(cmd: str, cwd: str = "") -> Dict[str, Any]:
    """Exécute une commande PowerShell sur la machine locale."""
    working_dir = Path(cwd) if cwd else WORKSPACE_TEMPORIA
    if not working_dir.exists():
        working_dir = VAULT_CERVEAU_ALIX
    try:
        t0 = time.time()
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=45,
            encoding='utf-8',
            errors='replace'
        )
        dt = round(time.time() - t0, 2)
        return {
            "status": "success" if res.returncode == 0 else "error",
            "returncode": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "time_sec": dt
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Commande interrompue : timeout de 45s dépassé."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def analyser_image(chemin_image: str, question: str = "Décris précisément et exhaustivement ce que tu vois sur cette image.") -> Dict[str, Any]:
    """Analyse une image ou capture d'écran via l'Œil d'Horus Souverain (alix-vision-abliterated:7b)."""
    p = Path(chemin_image)
    if not p.is_absolute():
        p = VAULT_CERVEAU_ALIX / chemin_image
    if not p.exists():
        return {"status": "error", "message": f"Image introuvable : {p}"}
    try:
        import base64
        import urllib.request
        with open(p, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "model": "alix-vision-abliterated:7b",
            "prompt": question,
            "images": [b64_data],
            "stream": False
        }
        t0 = time.time()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            dt = round(time.time() - t0, 2)
            return {
                "status": "success",
                "modele": "alix-vision-abliterated:7b",
                "description": data.get("response", "").strip(),
                "time_sec": dt
            }
    except Exception as e:
        return {"status": "error", "message": f"Erreur analyse vision : {str(e)}"}

# Registre des actuateurs disponibles
ACTUATEURS_MAP = {
    "lire_fichier": lire_fichier,
    "ecrire_fichier": ecrire_fichier,
    "modifier_fichier": modifier_fichier,
    "lister_dossier": lister_dossier,
    "executer_commande": executer_commande,
    "analyser_image": analyser_image
}

# ================================================================================
# 🧠 2. PARSEUR ET DÉPLOYEUR D'APPELS D'OUTILS (TOOL DISPATCHER)
# ================================================================================

TOOL_CALL_REGEX = re.compile(r"```tool_call\s*(.*?)\s*```|<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)

def extraire_appels_outils(texte: str) -> List[Dict[str, Any]]:
    """Détecte les blocs d'appel d'outil dans la réponse d'un LLM."""
    appels = []
    matches = TOOL_CALL_REGEX.findall(texte)
    for m in matches:
        raw_json = m[0] if m[0] else m[1]
        try:
            parsed = json.loads(raw_json)
            if "name" in parsed and "arguments" in parsed:
                appels.append(parsed)
        except Exception:
            pass
    return appels

def executer_appel_outil(nom_outil: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Exécute un outil du registre souverain."""
    if nom_outil not in ACTUATEURS_MAP:
        return {"status": "error", "message": f"Outil '{nom_outil}' non reconnu dans le registre souverain."}
    handler = ACTUATEURS_MAP[nom_outil]
    try:
        return handler(**arguments)
    except TypeError as e:
        return {"status": "error", "message": f"Arguments invalides pour {nom_outil} : {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Erreur d'exécution de {nom_outil} : {e}"}

# ================================================================================
# 📜 3. DESCRIPTION DES OUTILS POUR PROMPT SYSTEME (LOCAL AGENT)
# ================================================================================

DESCRIPTION_OUTILS_SOUVERAINS = """
Tu disposes des ACTUATEURS D'ATELIER suivants pour agir sur le système physique local :
1. `lire_fichier(chemin, start_line=1, end_line=800)` : Lit une note Obsidian ou un script.
2. `ecrire_fichier(chemin, contenu, overwrite=True)` : Crée ou modifie un fichier.
3. `modifier_fichier(chemin, cible, remplacement)` : Modifie un segment précis de texte.
4. `lister_dossier(chemin)` : Liste les dossiers et fichiers d'un répertoire.
5. `executer_commande(cmd, cwd)` : Exécute une commande PowerShell (ex: python, git, benchmarks).

Pour appeler un outil, écris STRICTEMENT un bloc au format suivant :
```tool_call
{
  "name": "nom_de_l_outil",
  "arguments": {
    "arg1": "valeur1"
  }
}
```
Tu peux émettre plusieurs appels si nécessaire. Tu recevras le résultat de l'outil pour forger ta réponse finale.
"""

if __name__ == "__main__":
    print("=" * 70)
    print("  ⚡ ALIX ACTUATEURS D'ATELIER : TEST DU BANC MATÉRIEL LOCAL")
    print("=" * 70)
    test_res = lister_dossier("Organes_Souverains/Moteurs")
    print(f"[✅] Lister dossier : {test_res.get('total_items', 0)} éléments détectés.")
    cmd_res = executer_commande("python --version")
    print(f"[✅] Exécution commande système : {cmd_res.get('stdout', '')} ({cmd_res.get('time_sec', 0)}s)")
    print("[🛡️] Tous les actuateurs d'atelier sont prêts pour le cerveau local !")
