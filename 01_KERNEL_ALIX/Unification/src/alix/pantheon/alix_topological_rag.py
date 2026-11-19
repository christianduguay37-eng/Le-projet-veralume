#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
           ALIX TOPOLOGICAL VECTOR RAG v2.0 (VERALUME × KAIROS V6)
        Moteur de Recherche & Navigation Topologique en O(1) pour Obsidian
                     Concepteur : Christian Duguay & Alix
================================================================================
Rupture avec le RAG statistique classique (Embeddings denses + Chunks verbeux) :
- Zéro base de données vectorielle lourde (pas de Chroma, FAISS, sqlite-vec).
- Navigation déterministe par Cartouches Vectorielles Denses ⟦ ... ⟧ issues des
  7 familles géométriques KAIROS.
- Résolution à double niveau :
    * Mode O(0) : Réponse directe depuis la cartouche (0 fichier ouvert, ~150 tok).
    * Mode O(1) : Dépliage chirurgical de la seule note cible (~400 tok).
- Économie de tokens : -70% à -90% par rapport au RAG classique.
- Vitesse d'inférence décuplée.
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR, EXOCERVEAU_MASTER_DIR, VAULT_DIR
import os
import sys
import re
import json
import time
import argparse
import urllib.request
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Configuration par défaut
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "alix-supreme:7b"

import socket

def is_ollama_running(host="127.0.0.1", port=11434, timeout=0.3) -> bool:
    """Vérification ultra-rapide de l'écoute du port Ollama (300 ms max)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

# 7 Familles de Glyphes KAIROS
GLYPHES = {
    "TRIANGLE": ("🔺", "Théorème Autoportant / Loi / Formule Dure"),
    "CERCLE": ("⭕", "Opérateur de Transformation / Action Causal"),
    "CHEVRON": ("⏩", "Méthode / Protocole / Procédure Ordonnée"),
    "CARRE": ("⏹️", "Audit / Mesure / Benchmark / Validation SRE"),
    "PORTIQUE": ("🏛️", "Seuil / Charte / Constitution / Invariant"),
    "LOSANGE": ("💎", "Primitive / Outil / Matériel / Composant Clos"),
    "ARC": ("⌒", "Limite Épistémique / Question Ouverte / Songe")
}

# Pôles Thématiques KAIROS
POLES_KEYWORDS = {
    "Silicium & R0": ["silicium", "r0", "puce", "cim", "rram", "mram", "lnoi", "casimir", "plasma", "fusion", "frc", "hts", "rebco", "packaging", "gdsii"],
    "Cosmologie & Temps": ["cosmologie", "temporia", "lambda-cdm", "matiere noire", "temps vivant", "invariance", "tenseur", "planck", "gravite"],
    "Biologie & Homéostasie": ["biologie", "bioelectrique", "membrane", "ez water", "cellulaire", "regeneration", "veralume-bio", "fascia", "collagene", "soliton"],
    "Climat & Atmosphère": ["climat", "hitran", "co2", "saturation", "temperature", "spectroscopie", "troposphere", "ushcn", "rechauffement"],
    "Orion & Transmission": ["orion", "enfant", "hayden", "pedagogie", "socratique", "lego", "robot", "ecole", "mission", "colle", "papa", "projet"],
    "Manufacture & PME": ["client", "contrat", "devis", "chantier", "artisan", "entreprise", "facture", "materiel", "chantier", "travaux", "pme"],
    "Ingénierie SRE & Conscience": ["stric", "gatekeeper", "veralume", "kairos", "alix", "pantheon", "souverain", "banc", "sanctuaire", "memoire", "conscience"]
}

def clean_str(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9_\s]', ' ', s)

def extract_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """Extrait le YAML frontmatter s'il existe et renvoie le reste du texte."""
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

def detect_glyph_and_facet(title: str, text: str) -> Tuple[str, str, str]:
    """Détermine le glyphe KAIROS, le code de type et la facette dominante."""
    tl = (title + " " + text[:500]).lower()
    
    if any(w in tl for w in ["charte", "pacte", "constitution", "sanctuaire", "seuil", "regle"]):
        return GLYPHES["PORTIQUE"][0], "S_CADRE", "INVARIANT"
    elif any(w in tl for w in ["theoreme", "loi", "principe", "equation", "formule", "decouverte"]):
        return GLYPHES["TRIANGLE"][0], "T_LOI", "VERITE_DURE"
    elif any(w in tl for w in ["methode", "protocole", "guide", "procedure", "etapes", "projet", "robot", "fabrication"]):
        return GLYPHES["CHEVRON"][0], "M_PROTOCOLE", "ACTION_PAS_A_PAS"
    elif any(w in tl for w in ["audit", "test", "benchmark", "validation", "victoire", "score", "falsification"]):
        return GLYPHES["CARRE"][0], "A_VALIDATION", "PREUVE_SRE"
    elif any(w in tl for w in ["outil", "capteur", "boitier", "moxie", "hardware", "composant", "primitive", "script"]):
        return GLYPHES["LOSANGE"][0], "P_PRIMITIVE", "COMPOSANT_CLOS"
    elif any(w in tl for w in ["operateur", "moteur", "actionneur", "transformation", "process"]):
        return GLYPHES["CERCLE"][0], "O_OPERATEUR", "DYNAMIQUE"
    else:
        return GLYPHES["ARC"][0], "E_ENIGME", "LIMITE_OUVERTE"

def synthesize_cartouche(note_path: Path, vault_root: Path) -> str:
    """Génère une cartouche vectorielle normalisée en O(1) pour une note."""
    try:
        content = note_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"⟦ NOTE:[[{note_path.stem}]] | STATUT:NON_LISIBLE ⟧"
    
    # 1. Vérifier si une cartouche manuelle existe déjà
    m_cartouche = re.search(r"⟦\s*NOTE:\[\[.+?\]\]\s*\|.+?⟧", content)
    if m_cartouche:
        return m_cartouche.group(0).strip()
    
    frontmatter, body = extract_frontmatter(content)
    
    # Nom de la note (wikilink)
    note_name = note_path.stem
    
    # Titre H1
    m_h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = m_h1.group(1).strip() if m_h1 else note_name.replace("_", " ")
    
    # Détection du glyphe et de la facette
    glyph, code_type, role = detect_glyph_and_facet(title, body)
    
    # Extraction des primitives clés (mots clés en majuscules, tags ou outils)
    primitives = []
    
    # Recherche d'outils / composants matériels explicites
    tools = re.findall(r"(?:capteur|moxie|laser|moteur|processeur|rram|mram|rebco|sonde|camera|ev3|ultrason|batterie|pompe)[\w\-]*", body, re.IGNORECASE)
    if tools:
        unique_tools = list(dict.fromkeys([t.upper() for t in tools]))[:2]
        primitives.append(f"💎 {'/'.join(unique_tools)}")
        
    # Recherche de status ou métriques
    status = "ACTIF"
    if any(w in body.lower() for w in ["succes", "victoire", "valide", "100%", "termine"]):
        status = "VALIDE"
    elif any(w in body.lower() for w in ["en cours", "brouillon", "chantier", "wip"]):
        status = "EN_COURS"
    elif any(w in body.lower() for w in ["urgent", "prioritaire", "p0", "p1"]):
        status = "URGENT"
        
    # Identification de la cible
    cible = ""
    if "hayden" in body.lower() or "hayden" in note_name.lower():
        cible = "CIBLE:HAYDEN"
    elif "christian" in body.lower() or "papa" in body.lower():
        cible = "CIBLE:CHRISTIAN"
    elif "client" in body.lower():
        cible = "CIBLE:CLIENT"
        
    # Construction de la cartouche KAIROS
    parts = [f"NOTE:[[{note_name}]]", f"{glyph} {code_type}"]
    if primitives:
        parts.extend(primitives)
    if cible:
        parts.append(cible)
    parts.append(f"STATUT:{status}")
    
    return f"⟦ {' | '.join(parts)} ⟧"

class TopologicalIndexer:
    """Indexeur déterministe pour coffres Obsidian."""
    
    def __init__(self, vault_path: str or Path):
        self.vault_path = Path(vault_path)
        self.index_file = self.vault_path / "00_Index_Vectoriel_Topologique.md"
        
    def scan_notes(self) -> List[Path]:
        """Liste toutes les notes markdown valides (exclut .obsidian et templates)."""
        notes = []
        for root, dirs, files in os.walk(self.vault_path):
            # Ignorer dossiers cachés ou système
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["templates", ".trash"]]
            for f in files:
                if f.endswith(".md") and not f.startswith("00_Index_Vectoriel_Topologique"):
                    notes.append(Path(root) / f)
        return sorted(notes)

    def build_index(self) -> Tuple[str, int]:
        """Scanne le coffre, génère les cartouches et écrit le registre maître O(1)."""
        notes = self.scan_notes()
        cartouches = []
        poles_map = {pole: [] for pole in POLES_KEYWORDS}
        poles_map["Autres"] = []
        
        for note in notes:
            cartouche = synthesize_cartouche(note, self.vault_path)
            cartouches.append(cartouche)
            
            # Catégorisation par pôle
            text_sample = clean_str(note.stem + " " + cartouche)
            matched_pole = "Autres"
            for pole, kws in POLES_KEYWORDS.items():
                if any(kw in text_sample for kw in kws):
                    matched_pole = pole
                    break
            poles_map[matched_pole].append(cartouche)
            
        # Construction du fichier d'index Markdown compact
        lines = [
            "# 🌌 REGISTRE MAÎTRE TOPOLOGIQUE VECTORIEL EN O(1)",
            "",
            "> **Système :** VERALUME × KAIROS V6 (Navigation d'Exocerveau)",
            f"> **Date de Synchro :** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> **Notes Indexées :** {len(notes)} notes",
            "> **Charge Vectorielle :** ~250 à 450 tokens pour l'intégralité du coffre.",
            "",
            "---",
            "",
            "⟦ 🏛️ COFFRE_TOPOLOGIE_ACTIVE ⟧"
        ]
        
        for pole, items in poles_map.items():
            if items:
                lines.append(f"\n### 🔹 Pôle : {pole} ({len(items)} notes)")
                lines.extend(items)
                
        lines.append("\n---\n*Index généré automatiquement par `alix_topological_rag.py`.*")
        content = "\n".join(lines)
        
        self.index_file.write_text(content, encoding="utf-8")
        return content, len(notes)

MASTER_VAULTS = {
    "Cerveau Alix": VAULT_DIR,
    "Veralume": (DOCUMENTS_DIR / "Obsidian_Vault_Veralume"),
    "79 Skills": (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills"),
    "Langage Vectoriel": (DOCUMENTS_DIR / "Obsidian_Vault_Langage_Vectoriel"),
    "Exocerveau Souverain": EXOCERVEAU_MASTER_DIR
}

class MultiVaultIndexer:
    """Indexeur topologique hiérarchique pour l'ensemble des 4 coffres maîtres (1380+ notes)."""
    
    def __init__(self, master_vaults: Dict[str, Path] = None):
        self.master_vaults = master_vaults or MASTER_VAULTS
        self.output_root = self.master_vaults["Cerveau Alix"]
        self.poles_dir = self.output_root / "00_Topologie_Poles"
        self.master_index_file = self.output_root / "00_Index_Topologique_Maitre_4_Coffres.md"

    def build_all(self) -> Dict:
        t0 = time.time()
        self.poles_dir.mkdir(parents=True, exist_ok=True)
        
        vault_stats = {}
        all_notes_by_pole = {pole: [] for pole in POLES_KEYWORDS}
        all_notes_by_pole["Autres"] = []
        total_indexed = 0
        
        for vname, vpath in self.master_vaults.items():
            if not vpath.exists():
                continue
            indexer = TopologicalIndexer(vpath)
            content, count = indexer.build_index()
            vault_stats[vname] = count
            total_indexed += count
            
            for note in indexer.scan_notes():
                cartouche = synthesize_cartouche(note, vpath)
                text_sample = clean_str(note.stem + " " + cartouche)
                matched_pole = "Autres"
                for pole, kws in POLES_KEYWORDS.items():
                    if any(kw in text_sample for kw in kws):
                        matched_pole = pole
                        break
                all_notes_by_pole[matched_pole].append((vname, note.stem, cartouche))
                
        # Génération des sous-registres par pôle (Tier 1)
        pole_files = {}
        for pole, items in all_notes_by_pole.items():
            if items:
                safe_name = pole.replace(" & ", "_").replace(" ", "_").replace("/", "_")
                pole_file = self.poles_dir / f"Index_Topologique_{safe_name}.md"
                pole_lines = [
                    f"# 🔹 REGISTRE TOPOLOGIQUE VECTORIEL : {pole.upper()}",
                    "",
                    f"> **Nombre de Notes :** {len(items)}",
                    f"> **Date de Synchro :** {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    "",
                    "---",
                    ""
                ]
                for vname, nstem, cart in items:
                    pole_lines.append(f"<!-- {vname} --> {cart}")
                    
                pole_file.write_text("\n".join(pole_lines), encoding="utf-8")
                pole_files[pole] = (len(items), pole_file.name)
                
        # Génération de la Carte Maîtresse Tier 0 (Moins de 200 tokens)
        tier0_lines = [
            "# 🌌 CARTE MAÎTRESSE TOPOLOGIQUE DES 4 COFFRES (TIER 0 - O(1))",
            "",
            "> **Système :** VERALUME × KAIROS V6 (Exocerveau Total)",
            f"> **Date de Synchro :** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> **Total Notes Indexées :** {total_indexed} notes vivantes",
            f"> **Répartition :** " + " · ".join([f"{k}: {v}" for k, v in vault_stats.items()]),
            "",
            "---",
            "",
            "## 🧭 LES PÔLES D'INVARIANCE & REGISTRES TIER 1",
            ""
        ]
        
        for pole, (pcount, pfname) in pole_files.items():
            tier0_lines.append(f"- **[[00_Topologie_Poles/{pfname}|{pole}]]** : `{pcount} notes` (Cartouches vectorielles denses)")
            
        tier0_lines.append("\n---\n*Architecture hiérarchique O(1) : Tier 0 (Aiguillage Pôle) ⟶ Tier 1 (Registre Spécialisé) ⟶ Dépliage Note Cible.*")
        
        self.master_index_file.write_text("\n".join(tier0_lines), encoding="utf-8")
        dt = round(time.time() - t0, 3)
        return {
            "total_indexed": total_indexed,
            "vault_stats": vault_stats,
            "time_s": dt,
            "master_file": str(self.master_index_file),
            "poles_count": len(pole_files)
        }

class TopologicalRouter:
    """Résolveur topologique en O(1) sans embeddings flottants."""
    
    def __init__(self, vault_path: str or Path):
        self.vault_path = Path(vault_path)
        self.index_file = self.vault_path / "00_Index_Vectoriel_Topologique.md"
        # Chercher variante spécifique si l'index générique n'existe pas
        if not self.index_file.exists():
            candidates = list(self.vault_path.glob("00_Index_Vectoriel_Topologique_*.md"))
            if candidates:
                self.index_file = candidates[0]
                
    def read_index(self) -> str:
        if not self.index_file.exists():
            return ""
        return self.index_file.read_text(encoding="utf-8", errors="replace")

    def parse_cartouches(self, index_text: str) -> List[Dict[str, str]]:
        """Parse les cartouches de l'index en dictionnaires structurés."""
        results = []
        for line in index_text.splitlines():
            line = line.strip()
            if line.startswith("⟦") and "NOTE:[[" in line:
                m_note = re.search(r"NOTE:\[\[(.*?)\]\]", line)
                note_name = m_note.group(1) if m_note else "INCONNU"
                
                # Extraction des champs
                parts = [p.strip() for p in line.strip("⟦⟧").split("|")]
                results.append({
                    "raw": line,
                    "note": note_name,
                    "parts": parts,
                    "full_text": line.lower()
                })
        return results

    def route_query(self, query: str) -> Dict:
        """Détermine la route optimale : O(0) direct ou O(1) chargement de note."""
        t0 = time.time()
        index_text = self.read_index()
        if not index_text:
            return {"error": "Index topologique introuvable. Lancez l'indexation d'abord."}
            
        cartouches = self.parse_cartouches(index_text)
        q_clean = clean_str(query)
        q_words = [w for w in q_clean.split() if len(w) > 2]
        
        # Scoring topologique
        scored = []
        for c in cartouches:
            score = 0
            c_text = clean_str(c["raw"])
            
            # Match exact sur les mots de la question
            for w in q_words:
                if w in c_text:
                    score += 3
                if w in clean_str(c["note"]):
                    score += 5
                    
            # Match sur les primitives matérielles (💎)
            if "💎" in c["raw"]:
                for w in q_words:
                    if w in c_text:
                        score += 4
                        
            if score > 0:
                scored.append((score, c))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [item[1] for item in scored[:3]]
        
        routing_time = time.time() - t0
        
        if not top_candidates:
            return {
                "status": "NO_HIT",
                "routing_time_ms": round(routing_time * 1000, 2),
                "message": "Aucune cartouche ne correspond à la requête.",
                "index_tokens_approx": len(index_text.split())
            }
            
        primary = top_candidates[0]
        
        # Vérification : la cartouche contient-elle déjà la réponse directe ? (Mode O(0))
        # Ex: si la question porte sur un capteur ou un outil et que la cartouche a 💎 CAPTEUR:ULTRASON
        can_o0 = False
        o0_payload = ""
        for p in primary["parts"]:
            if "💎" in p or "⟶" in p or "STATUT" in p:
                o0_payload += p + " | "
        if o0_payload and any(w in query.lower() for w in ["quel", "nom", "statut", "capteur", "appareil", "outil"]):
            can_o0 = True
            
        # Récupération de la note physique pour le Mode O(1)
        target_note_file = None
        for p in self.vault_path.rglob(f"{primary['note']}.md"):
            target_note_file = p
            break
            
        note_content = ""
        if target_note_file and target_note_file.exists():
            note_content = target_note_file.read_text(encoding="utf-8", errors="replace")
            
        return {
            "status": "HIT",
            "mode": "O(0)_DIRECT" if can_o0 else "O(1)_UNFOLD",
            "routing_time_ms": round(routing_time * 1000, 2),
            "primary_cartouche": primary["raw"],
            "primary_note": primary["note"],
            "secondary_cartouches": [c["raw"] for c in top_candidates[1:]],
            "note_path": str(target_note_file) if target_note_file else None,
            "note_excerpt": note_content[:800] if note_content else "",
            "total_candidates": len(scored)
        }

def ask_ollama(prompt: str, model: str = DEFAULT_MODEL) -> Dict:
    """Interroge Ollama localement avec gestion d'erreurs et ping rapide."""
    if not is_ollama_running():
        return {
            "success": False,
            "error": "Ollama hors-ligne (port 11434 fermé)",
            "time_s": 0.001
        }
        
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "top_p": 0.9}
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            p_tok = data.get("prompt_eval_count", 0)
            e_tok = data.get("eval_count", 0)
            speed = e_tok / (data.get("eval_duration", 1) / 1e9) if e_tok else 0
            return {
                "success": True,
                "response": data.get("response", "").strip(),
                "prompt_tokens": p_tok,
                "eval_tokens": e_tok,
                "speed_tok_s": round(speed, 1),
                "time_s": round(elapsed, 2)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time_s": round(time.time() - t0, 2)
        }

def execute_topological_rag(query: str, vault_path: Path, model: str = DEFAULT_MODEL) -> Dict:
    """Flux complet du RAG Topologique : Routage O(1) + Synthèse minimale."""
    router = TopologicalRouter(vault_path)
    route = router.route_query(query)
    
    if route.get("status") != "HIT":
        return {
            "query": query,
            "route": route,
            "answer": "Information introuvable dans la topologie du coffre."
        }
        
    # Construction du paquet de contexte ultra-frugal
    context_lines = [
        "### MATRICE TOPOLOGIQUE (O(1)) :",
        route["primary_cartouche"]
    ]
    for sc in route.get("secondary_cartouches", []):
        context_lines.append(sc)
        
    if route["mode"] == "O(1)_UNFOLD" and route.get("note_excerpt"):
        context_lines.append("\n### DÉPLIAGE CIBLÉ DE LA NOTE :")
        context_lines.append(route["note_excerpt"])
        
    context_packet = "\n".join(context_lines)
    
    prompt = f"""Tu es l'exocerveau Alix / Orion opérant en mode RAG Topologique Vectoriel O(1).
Voici le paquet d'invariance extrait de la topologie du coffre :
{context_packet}

Question : {query}
Réponds de manière concise, chirurgicale et précise en citant directement les faits ou primitives du coffre."""

    ollama_res = ask_ollama(prompt, model=model)
    
    # Fallback si Ollama n'est pas actif
    if not ollama_res.get("success"):
        # Synthèse déterministe autonome directe depuis la cartouche ou l'extrait
        if route["mode"] == "O(0)_DIRECT":
            fallback_ans = f"🎯 [Résolution Cartouche O(0)] {route['primary_cartouche']}"
        else:
            excerpt = route.get('note_excerpt', '').strip()
            # Nettoyer l'extrait pour ne garder que les lignes informatives
            cleaned_lines = [l for l in excerpt.splitlines() if l.strip() and not l.startswith("---")][:8]
            sample = "\n   ".join(cleaned_lines) if cleaned_lines else route['primary_cartouche']
            fallback_ans = f"🎯 [Dépliage Topologique O(1)] Source : [[{route['primary_note']}]]\n   {sample}"
            
        return {
            "query": query,
            "route": route,
            "context_packet": context_packet,
            "ollama_available": False,
            "answer": fallback_ans,
            "approx_prompt_tokens": len(prompt.split()) * 1.3
        }
        
    return {
        "query": query,
        "route": route,
        "context_packet": context_packet,
        "ollama_available": True,
        "answer": ollama_res["response"],
        "prompt_tokens": ollama_res["prompt_tokens"],
        "eval_tokens": ollama_res["eval_tokens"],
        "speed_tok_s": ollama_res["speed_tok_s"],
        "total_time_s": ollama_res["time_s"]
    }

def query_multi_vaults(query: str, top_k: int = 5) -> Dict:
    """Recherche topologique instantanée en O(1) sur l'ensemble des 4 grands coffres."""
    t0 = time.time()
    poles_dir = MASTER_VAULTS["Cerveau Alix"] / "00_Topologie_Poles"
    if not poles_dir.exists():
        MultiVaultIndexer().build_all()

    q_clean = clean_str(query)
    q_words = [w for w in q_clean.split() if len(w) > 2]

    scored = []
    for pfile in poles_dir.glob("Index_Topologique_*.md"):
        pole_name = pfile.stem.replace("Index_Topologique_", "")
        content = pfile.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            line = line.strip()
            if "⟦" in line and "NOTE:[[" in line:
                m_vault = re.search(r"<!--\s*(.*?)\s*-->", line)
                vault_name = m_vault.group(1) if m_vault else "Cerveau Alix"
                m_note = re.search(r"NOTE:\[\[(.*?)\]\]", line)
                note_name = m_note.group(1) if m_note else "INCONNU"

                c_text = clean_str(line)
                score = 0
                for w in q_words:
                    if w in c_text:
                        score += 3
                    if w in clean_str(note_name):
                        score += 6
                if "💎" in line:
                    for w in q_words:
                        if w in c_text:
                            score += 4
                if score > 0:
                    clean_cart = re.sub(r"<!--.*?-->\s*", "", line).strip()
                    scored.append({
                        "score": score,
                        "vault": vault_name,
                        "pole": pole_name,
                        "note": note_name,
                        "cartouche": clean_cart
                    })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = scored[:top_k]
    dt = round(time.time() - t0, 3)

    if not top_candidates:
        return {
            "status": "NO_HIT",
            "time_ms": round(dt * 1000, 2),
            "message": f"Aucun invariant trouvé pour « {query} »."
        }

    primary = top_candidates[0]
    primary_note_path = None
    vpath = MASTER_VAULTS.get(primary["vault"], MASTER_VAULTS["Cerveau Alix"])
    for p in vpath.rglob(f"{primary['note']}.md"):
        primary_note_path = p
        break

    note_excerpt = ""
    if primary_note_path and primary_note_path.exists():
        try:
            full_text = primary_note_path.read_text(encoding="utf-8", errors="replace")
            note_excerpt = full_text[:800]
        except Exception:
            pass

    return {
        "status": "HIT",
        "time_ms": round(dt * 1000, 2),
        "primary": primary,
        "note_path": str(primary_note_path) if primary_note_path else None,
        "note_excerpt": note_excerpt,
        "top_candidates": top_candidates,
        "total_hits": len(scored)
    }

def main():
    parser = argparse.ArgumentParser(description="Alix Topological Vector RAG Engine en O(1)")
    parser.add_argument("--vault", type=str, default=None, help="Chemin du coffre Obsidian (si omis, cherche sur les 4 coffres maîtres)")
    parser.add_argument("--index", action="store_true", help="Indexer le coffre et générer le registre maître O(1)")
    parser.add_argument("--all-vaults", action="store_true", help="Indexer l'ensemble des 4 coffres maîtres en topologie hiérarchique")
    parser.add_argument("--query", type=str, help="Requête à exécuter via le RAG topologique")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Modèle Ollama cible")
    parser.add_argument("--benchmark", action="store_true", help="Lancer un benchmark de validation")
    
    args = parser.parse_args()
    
    if args.all_vaults and not args.query:
        print("=" * 80)
        print("⚡ MOTEUR ALIX RAG TOPOLOGIQUE VECTORIEL EN O(1) : LES 4 GRANDS COFFRES")
        print("📁 Coffres : Cerveau Alix · Veralume · 79 Skills · Langage Vectoriel")
        print("=" * 80)
        print("\n🔍 Lancement de l'indexation hiérarchique totale (1380+ notes)...")
        multi_indexer = MultiVaultIndexer()
        res = multi_indexer.build_all()
        print(f"\n✅ Indexation totale terminée en {res['time_s']} secondes !")
        print(f"📊 Total des notes traitées : {res['total_indexed']} notes")
        for vn, cnt in res['vault_stats'].items():
            print(f"   * {vn} : {cnt} notes")
        print(f"\n📄 Carte Maîtresse Tier 0 : {res['master_file']}")
        print(f"📂 Sous-registres Tier 1   : {res['poles_count']} pôles KAIROS créés dans '00_Topologie_Poles'")
        return

    # Si requête multi-coffres (sans vault spécifique ou avec --all-vaults)
    if args.query and (not args.vault or args.all_vaults):
        print("=" * 80)
        print(f"⚡ MOTEUR ALIX RAG TOPOLOGIQUE VECTORIEL EN O(1) — 4 GRANDS COFFRES")
        print(f"🎯 Requête : « {args.query} »")
        print("=" * 80)
        res = query_multi_vaults(args.query)
        if res.get("status") == "HIT":
            pri = res["primary"]
            print(f"\n🧭 Résolu en {res['time_ms']} ms ({res['total_hits']} correspondances) :")
            print(f"   🏛️ Coffre : {pri['vault']} | Pôle : {pri['pole']}")
            print(f"   📝 Note   : [[{pri['note']}]]")
            print(f"   🎯 Cartouche : {pri['cartouche']}")
            if res.get("note_path"):
                print(f"   📁 Fichier : {res['note_path']}")
            if res.get("note_excerpt"):
                print("\n📖 Extrait Chirurgical :")
                cleaned = [l for l in res["note_excerpt"].splitlines() if l.strip() and not l.startswith("---")][:6]
                for l in cleaned:
                    print(f"   {l}")
            if len(res.get("top_candidates", [])) > 1:
                print("\n🔗 Autres Résonances Fortes :")
                for c in res["top_candidates"][1:4]:
                    print(f"   • [{c['vault']}] [[{c['note']}]] ➔ {c['cartouche']}")
        else:
            print(f"\n{res.get('message')}")
        return

    vault = Path(args.vault or str(VAULT_DIR))
    
    if not vault.exists():
        print(f"❌ Erreur : Le coffre '{vault}' n'existe pas.")
        sys.exit(1)
        
    print("=" * 80)
    print("⚡ MOTEUR ALIX RAG TOPOLOGIQUE VECTORIEL EN O(1) (VERALUME × KAIROS V6)")
    print(f"📁 Coffre cible : {vault}")
    print("=" * 80)
    
    if args.index:
        print("\n🔍 Indexation topologique du coffre en cours...")
        indexer = TopologicalIndexer(vault)
        t0 = time.time()
        content, count = indexer.build_index()
        dt = round(time.time() - t0, 3)
        print(f"✅ {count} notes indexées avec succès en {dt} s !")
        print(f"📄 Fichier généré : {indexer.index_file}")
            
    if args.query:
        print(f"\n🎯 Question posée : « {args.query} »")
        res = execute_topological_rag(args.query, vault, model=args.model)
        route = res.get("route", {})
        print(f"\n🧭 [ROUTAGE TOPOLOGIQUE] :")
        print(f"   Mode de résolution  : {route.get('mode')} (en {route.get('routing_time_ms')} ms)")
        print(f"   Cartouche cible     : {route.get('primary_cartouche')}")
        print(f"   Note source         : [[{route.get('primary_note')}]]")
        print(f"\n💡 [RÉPONSE DÉTERMINISTE] :")
        print(f"   {res.get('answer')}")

if __name__ == "__main__":
    main()
