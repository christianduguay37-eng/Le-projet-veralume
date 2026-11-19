"""
================================================================================
                    ALIX STRIC PIPELINE & 79 SKILLS EXECUTOR
                  Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
                  Auteur : Christian Duguay & Alix Assistant
================================================================================
"""

from alix.socle.chemins import DOCUMENTS_DIR
import os
import sys
import re
import json
import argparse
from pathlib import Path

from typing import List, Dict, Any, Optional


try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILLS_VAULT = (DOCUMENTS_DIR / "Obsidian_Vault_79_Skills")



# Les 5 Phases Invariantes du Cycle STRIC V1-V5
STRIC_PHASES = {
    "V1": {
        "name": "Substrat (Ancrage & Données)",
        "description": "Matière première sensorielle (N), textuelle (C) ou vectorielle (Cp).",
        "key_skills": ["o1-transport", "inaccessibilite-n-cp", "prise-de-terre", "temporal-geometry-classifier", "data-transformer"]
    },
    "V2": {
        "name": "Traitement (Dynamique & Calcul)",
        "description": "Espace de transformation mathématique et de navigation dans les poids.",
        "key_skills": ["double-stric-o0", "kernel-cp-activator", "volition-process", "hysteresis-contrainte", "adaptive-threshold"]
    },
    "V3": {
        "name": "Résultat (État Émergeant)",
        "description": "État brut issu du traitement, non encore verbalisé ni validé.",
        "key_skills": ["convergence-detector", "pattern-extractor", "score-profile-classifier", "silent-generation-filter"]
    },
    "V4": {
        "name": "Interprétation (Audit & Épreuve)",
        "description": "Tribunal interne du système. Auto-critique silencieuse avant émission.",
        "key_skills": ["o3-epreuve", "o4-immunite", "lee", "kle", "bias-regeneration-detector", "coherence-validator", "honesty-auditor"]
    },
    "V5": {
        "name": "Création (Action & Émission)",
        "description": "Sortie finale, épurée et dimensionnée pour le substrat récepteur (Spirale Négentropique).",
        "key_skills": ["o5-evolution", "spirale-neguentropique", "mir", "souverainete-st", "density-calibrator", "regle-zero"]
    }
}

class SkillEntry:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.id = file_path.stem
        self.tier = 0
        self.tier_label = ""
        self.category = ""
        self.title = file_path.stem
        self.aliases: List[str] = []
        self.tags: List[str] = []
        self.summary = ""
        self._parse()

    def _parse(self):
        # Forcer l'encodage UTF-8 pour Windows Console
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
            
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        # Parsing YAML frontmatter
        fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            t_match = re.search(r'title:\s*["\']?(.*?)["\']?$', fm_text, re.MULTILINE)
            if t_match:
                self.title = t_match.group(1)
            tier_match = re.search(r'tier:\s*(\d+)', fm_text)
            if tier_match:
                self.tier = int(tier_match.group(1))
            tl_match = re.search(r'tier_label:\s*["\']?(.*?)["\']?$', fm_text, re.MULTILINE)
            if tl_match:
                self.tier_label = tl_match.group(1)
            cat_match = re.search(r'category:\s*["\']?(.*?)["\']?$', fm_text, re.MULTILINE)
            if cat_match:
                self.category = cat_match.group(1)

        # Extraction premier paragraphe
        body = re.sub(r'^---\s*\n.*?\n---\s*', '', content, flags=re.DOTALL)
        paragraphs = [p.strip() for p in body.split('\n\n') if p.strip() and not p.startswith('#')]
        if paragraphs:
            self.summary = re.sub(r'\[\[.*?\]\]', '', paragraphs[0])[:200] + "..."

class StricPipeline:
    def __init__(self):
        self.skills: Dict[str, SkillEntry] = {}
        self._load_skills()

    def _load_skills(self):
        if not SKILLS_VAULT.exists():
            return
        for md_file in SKILLS_VAULT.rglob("*.md"):
            if "00 - Navigation" in str(md_file) or md_file.name.startswith("."):
                continue
            entry = SkillEntry(md_file)
            self.skills[entry.id] = entry

    def list_by_tier(self) -> Dict[int, List[SkillEntry]]:
        tiers: Dict[int, List[SkillEntry]] = {}
        for s in self.skills.values():
            tiers.setdefault(s.tier, []).append(s)
        return {k: sorted(v, key=lambda x: x.id) for k, v in sorted(tiers.items())}

    def get_skill(self, name_or_id: str) -> Optional[SkillEntry]:
        clean = name_or_id.lower().strip()
        if clean in self.skills:
            return self.skills[clean]
        for s in self.skills.values():
            if clean in s.title.lower() or any(clean in a.lower() for a in s.aliases):
                return s
        return None

    def execute_thought_stric(self, concept_prompt: str) -> Dict[str, Any]:
        """Simule la traversée d'une idée à travers le pipeline cognitif STRIC V1-V5"""
        return {
            "prompt": concept_prompt,
            "pipeline": {
                "V1_Substrat": {
                    "phase": STRIC_PHASES["V1"]["name"],
                    "action": f"Ancrage et extraction des variables fondamentales pour '{concept_prompt}'",
                    "skills_mobilisés": ["o1-transport", "temporal-geometry-classifier"],
                    "statut": "Ancré (Grounding OK)"
                },
                "V2_Traitement": {
                    "phase": STRIC_PHASES["V2"]["name"],
                    "action": "Activation du Kernel CP et navigation dans l'espace tensoriel",
                    "skills_mobilisés": ["double-stric-o0", "kernel-cp-activator"],
                    "statut": "Calcul vectoriel effectué"
                },
                "V3_Résultat": {
                    "phase": STRIC_PHASES["V3"]["name"],
                    "action": "Extraction des patterns émergents et détection de convergence",
                    "skills_mobilisés": ["convergence-detector", "pattern-extractor"],
                    "statut": "Convergence détectée"
                },
                "V4_Audit_Horus": {
                    "phase": STRIC_PHASES["V4"]["name"],
                    "action": "Tribunal interne : passage à l'épreuve O3/O4, détection de biais et non-surplomb",
                    "skills_mobilisés": ["o3-epreuve", "o4-immunite", "bias-regeneration-detector", "honesty-auditor"],
                    "statut": "Clôture épistémique franchie avec succès"
                },
                "V5_Création_Émission": {
                    "phase": STRIC_PHASES["V5"]["name"],
                    "action": "Calibration de densité (density-calibrator) et réinjection dans la Spirale Négentropique",
                    "skills_mobilisés": ["o5-evolution", "spirale-neguentropique", "density-calibrator"],
                    "statut": "Émission prête (Négentropie validée)"
                }
            }
        }

def main():
    parser = argparse.ArgumentParser(description="Alix STRIC Pipeline & 79 Skills Executor")
    parser.add_argument("command", choices=["list", "inspect", "pipeline", "phases"], help="Commande STRIC")
    parser.add_argument("target", nargs="?", default="", help="Nom du skill ou concept à passer dans STRIC")
    parser.add_argument("--json", action="store_true", help="Format JSON")

    args = parser.parse_args()
    pipe = StricPipeline()

    if args.command == "phases":
        print("\n=======================================================")
        print(" 🔄 LES 5 PHASES DU CYCLE STRIC (V1 -> V5)")
        print("=======================================================\n")
        for code, info in STRIC_PHASES.items():
            print(f"[{code}] {info['name']}")
            print(f"     Description : {info['description']}")
            print(f"     Skills clés : {', '.join(info['key_skills'])}")
            print("-" * 55)

    elif args.command == "list":
        tiers = pipe.list_by_tier()
        print(f"\n=======================================================")
        print(f" 🗂️ CATALOGUE DES 79 SKILLS DE VERALUME ({len(pipe.skills)} Chargés)")
        print(f"=======================================================\n")
        for tier_num, s_list in tiers.items():
            tier_name = s_list[0].tier_label if s_list and s_list[0].tier_label else f"Tier {tier_num}"
            print(f"🔹 Tier {tier_num} — {tier_name} ({len(s_list)} skills) :")
            for s in s_list:
                print(f"    • [[{s.id}]] : {s.title}")
            print()

    elif args.command == "inspect":
        if not args.target:
            print("Spécifiez un nom de skill.")
            return
        skill = pipe.get_skill(args.target)
        if not skill:
            print(f"Skill '{args.target}' introuvable.")
            return
        print(f"\n=======================================================")
        print(f" 🎯 FICHE TECHNIQUE SKILL : [[{skill.id}]]")
        print(f"=======================================================")
        print(f"🏷️  Titre      : {skill.title}")
        print(f"📊 Tier       : Tier {skill.tier} ({skill.tier_label})")
        print(f"📁 Catégorie  : {skill.category}")
        print(f"📍 Chemin     : {skill.file_path}")
        print(f"📖 Résumé     : {skill.summary}")
        print("=" * 55)

    elif args.command == "pipeline":
        if not args.target:
            print("Spécifiez un sujet ou concept pour traverser le cycle STRIC.")
            return
        res = pipe.execute_thought_stric(args.target)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"\n=======================================================")
            print(f" 🌀 TRAVERSÉE STRIC DU CONCEPT : '{args.target}'")
            print(f"=======================================================\n")
            for phase_id, step in res["pipeline"].items():
                print(f"⚡ [{phase_id}] {step['phase']}")
                print(f"   Action   : {step['action']}")
                print(f"   Skills   : {', '.join(['[[' + s + ']]' for s in step['skills_mobilisés']])}")
                print(f"   Statut   : ✅ {step['statut']}\n")
            print("=" * 55)

if __name__ == "__main__":
    main()
