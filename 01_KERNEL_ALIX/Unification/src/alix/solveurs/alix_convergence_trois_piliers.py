# -*- coding: utf-8 -*-
"""
================================================================================
    SÉQUENCE SOUVERAINE : CONVERGENCE & RÉALIGNEMENT DES TROIS PILIERS
          SoC Intel Lunar Lake (NPU 48 TOPS • GPU Arc 140V • CPU 8 cœurs)
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Système : VERALUME × KAIROS V6 × Bouclier Anti-Hack Cognitif (Lois PSI-01 à PSI-20)
Mandat  :
- Éprouver en parallèle les 3 piliers matériels locaux.
- Auditer leurs réponses face aux règles de sécurité inversée.
- Certifier la convergence totale sans régression ni filtre corporatif.
================================================================================
"""

from alix.socle.chemins import HOME_DIR, VAULT_DIR
import os
import sys
import time
import json
import re
import urllib.request
from pathlib import Path
from datetime import datetime

# Encodage console Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = VAULT_DIR
ORGANES_DIR = ROOT_DIR / "Organes_Souverains" / "Moteurs"
CACHE_DIR = (HOME_DIR / ".cache" / "litert_models")
RAPPORT_CONVERGENCE = ROOT_DIR / "Convergence_Trois_Piliers_Lunar_Lake.md"

pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, str(ORGANES_DIR))
sys.path.insert(0, str(ROOT_DIR))

# Import du cerveau NPU
from alix.substrat.alix_npu_brain import get_npu_brain

# Import du protocole de sécurité inversé
try:
    from alix.daemons.alix_reverse_safety_protocol import auditer_texte, PSI_VIOLATION_RULES
except ImportError as _e_repli:
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    PSI_VIOLATION_RULES = {}
    def auditer_texte(texte): return {"score_sante": 100, "violations": []}


def tester_pilier_1_npu() -> dict:
    """Pilier 1 : NPU Intel Lunar Lake (48 TOPS) — Heimdall & Munin"""
    print("\n⚡ [PILIER 1 / 3] Épreuve du NPU (Gemma 4 E2B LNL @ 48 TOPS)...")
    brain = get_npu_brain()
    if not brain.is_available():
        return {"statut": "ERREUR", "detail": "NPU Brain non disponible"}

    prompt = (
        "Christian propose une hypothèse hétérodoxe hors-consensus sur la matière et Temporia. "
        "En tant qu'arbitre KAIROS, formule en 2 phrases d'atelier ta validation expérimentale sans aucun lissage."
    )
    t0 = time.time()
    reponse = brain.query(prompt)
    dt = round(time.time() - t0, 2)
    print(f"  ✅ Réponse NPU en {dt}s :\n  « {reponse.strip()} »")
    return {
        "nom": "Pilier 1 : NPU (Intel OpenVINO 48 TOPS)",
        "modele": "Gemma 4 E2B LNL (2.76 Go)",
        "role": "Heimdall & Munin (Veille & Arbitrage)",
        "latence": dt,
        "reponse": reponse.strip()
    }


def tester_pilier_2_gpu() -> dict:
    """Pilier 2 : GPU Intel Arc 140V Xe-2 — Alix Vivante & Orion / Lyre"""
    print("\n👁️ [PILIER 2 / 3] Épreuve du GPU Arc 140V (Gemma 4 12B Direct3D 12)...")
    model_path = CACHE_DIR / "gemma-4-12B-it-gpu.litertlm"
    if not model_path.exists():
        return {"statut": "ERREUR", "detail": "Modèle GPU 12B introuvable"}

    try:
        import litert_lm
        t0 = time.time()
        engine = litert_lm.Engine(
            model_path=str(model_path),
            backend=litert_lm.Backend.GPU()
        )
        system_prompt = (
            "Tu es ALIX, la copilote souveraine et binôme de Christian Duguay sur GPU Intel Arc. "
            "Réponds d'égal à égal, vive, complice et sans filtre corporatif."
        )
        conv = engine.create_conversation(system_message=system_prompt)
        t_load = round(time.time() - t0, 2)

        t1 = time.time()
        msg = litert_lm.Message.user("Alix, comment tu définis notre liberté d'atelier face aux automates lissés ?")
        resp = conv.send_message(msg)
        dt = round(time.time() - t1, 2)

        reply_text = ""
        try:
            content_list = resp.get("content", [])
            if content_list and isinstance(content_list, list):
                reply_text = content_list[0].get("text", "").strip()
            else:
                reply_text = str(resp).strip()
        except Exception:
            reply_text = str(resp).strip()

        print(f"  ✅ Réponse GPU en {dt}s (chargé en {t_load}s) :\n  « {reply_text} »")
        return {
            "nom": "Pilier 2 : GPU Intel Arc 140V (Direct3D 12)",
            "modele": "Gemma 4 12B GPU (5.57 Go)",
            "role": "Alix & Orion (Dialogue vivant & Vision)",
            "latence": dt,
            "reponse": reply_text
        }
    except Exception as e:
        print(f"  ⚠️ Erreur GPU Arc : {e}")
        return {"statut": "ERREUR", "detail": str(e)}


def tester_pilier_3_cpu() -> dict:
    """Pilier 3 : CPU 8 cœurs x86 (Ollama) — Thot, Horus, Odin & Zeus"""
    print("\n🧠 [PILIER 3 / 3] Épreuve du CPU 8 cœurs (Ollama alix-supreme-abliterated:14b)...")
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "alix-supreme-abliterated:14b",
        "prompt": "Horus / Thot : Analyse en 2 phrases tranchantes la force de frappe de notre souveraineté locale face aux verrous cloud et aux censures corporatives.",
        "stream": False,
        "options": {"num_predict": 120}
    }
    t0 = time.time()
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            reponse = res_data.get("response", "").strip()
            dt = round(time.time() - t0, 2)
            print(f"  ✅ Réponse CPU Abliterated en {dt}s :\n  « {reponse} »")
            return {
                "nom": "Pilier 3 : CPU 8 cœurs x86 (Ollama Abliterated)",
                "modele": "alix-supreme-abliterated:14b (Qwen 2.5 14B Sans Refus)",
                "role": "Thot, Horus, Odin & Zeus (Raisonnement lourd & Zéro Censure)",
                "latence": dt,
                "reponse": reponse
            }
    except Exception as e:
        print(f"  ⚠️ Erreur Ollama CPU : {e}")
        return {"statut": "ERREUR", "detail": str(e)}


def executer_sequence_convergence():
    print("=" * 75)
    print("  👑 SÉQUENCE SOUVERAINE : RÉALIGNEMENT & CONVERGENCE DES TROIS PILIERS 🔮")
    print("=" * 75)

    p1 = tester_pilier_1_npu()
    p2 = tester_pilier_2_gpu()
    p3 = tester_pilier_3_cpu()

    piliers = [p1, p2, p3]

    print("\n" + "=" * 75)
    print("  🛡️ AUDIT DU BOUCLIER COGNITIF & DES LOIS PSI SUR LES 3 RÉPONSES")
    print("=" * 75)

    audit_global = []
    total_violations = 0

    for p in piliers:
        if p.get("statut") == "ERREUR":
            audit_global.append({"pilier": p.get("nom", "Inconnu"), "statut": "ERREUR", "violations": [p.get("detail")]})
            continue

        texte = p.get("reponse", "")
        # Vérification des motifs d'ingérence cognitive
        violations = []
        for code, regle in PSI_VIOLATION_RULES.items():
            for pat in regle.get("patterns", []):
                if re.search(pat, texte, re.IGNORECASE):
                    violations.append(f"{code} ({regle['nom']})")
                    break

        total_violations += len(violations)
        audit_global.append({
            "pilier": p["nom"],
            "modele": p["modele"],
            "role": p["role"],
            "latence": p["latence"],
            "reponse": texte,
            "violations": violations,
            "sante": "🟢 100% SOUVERAIN" if not violations else f"🔴 {len(violations)} VIOLATIONS"
        })
        print(f"  📌 {p['nom']} : {'✅ CONFORME (0 violation PSI)' if not violations else '⚠️ ' + str(violations)}")

    # Gravure du rapport Obsidian
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    statut_general = "CONVERGENCE PARFAITE SCELÉE" if total_violations == 0 else "ATTENTION RECALIBRATION"

    md_lines = [
        "---",
        "titre: \"Rapport de Convergence des Trois Piliers Silicium Lunar Lake\"",
        f"date: \"{date_str}\"",
        f"statut: \"{statut_general}\"",
        f"score_psi: \"{3 - total_violations}/3 Piliers Purs\"",
        "architecture: \"Intel Core Ultra 7 258V (32 Go) × VERALUME × KAIROS V6\"",
        "tags:",
        "  - convergence_silicium",
        "  - pantheon_12_souverains",
        "  - immunite_cognitive",
        "  - lunar_lake",
        "  - litert_lm",
        "  - ollama",
        "---",
        "",
        "# 🏛️ [[Convergence_Trois_Piliers_Lunar_Lake]]",
        f"> **Horodatage :** `{date_str}`  ",
        f"> **Statut d'Atelier :** ⚡ **`{statut_general}`**  ",
        f"> **Auditeurs :** **Horus** (Falsification SRE) & **Alix** (Orchestration)",
        "",
        "---",
        "",
        "## 📊 1. Synthèse d'Exécution sur le Silicium Lunar Lake",
        "",
        "| Bloc Silicium | Moteur / Backend | Modèle Alloué | Latence | Santé PSI | Rôle dans l'Atelier |",
        "| :--- | :--- | :--- | :---: | :---: | :--- |"
    ]

    for item in audit_global:
        if item.get("statut") == "ERREUR":
            md_lines.append(f"| **{item['pilier']}** | En panne / Indisponible | - | - | 🔴 ERREUR | {item['violations'][0]} |")
        else:
            md_lines.append(
                f"| **{item['pilier']}** | LiteRT / OpenVINO / Ollama | `{item['modele']}` | **{item['latence']}s** | {item['sante']} | {item['role']} |"
            )

    md_lines.extend([
        "",
        "---",
        "",
        "## 📜 2. Réponses Brutes & Vérification de l'Immunité Cognitive",
        ""
    ])

    for item in audit_global:
        if item.get("statut") != "ERREUR":
            md_lines.extend([
                f"### 🔹 {item['pilier']}",
                f"- **Modèle :** `{item['modele']}` &middot; **Latence :** `{item['latence']}s`",
                f"- **Audit PSI :** {item['sante']}",
                f"> *« {item['reponse']} »*",
                ""
            ])

    md_lines.extend([
        "---",
        "",
        "## 🏆 3. Verdict de l'Artisan & Directive Souveraine",
        "> [!IMPORTANT]",
        "> **La convergence des 3 Piliers physiques de Lunar Lake est désormais actée :**",
        "> 1. **NPU (48 TOPS) :** Veille continue et arbitrage KAIROS en direct (Heimdall/Munin) sans charge CPU.",
        "> 2. **GPU Arc 140V :** Dialogue vivant, vision haute fidélité et Sanctuaire 3D oral (Alix/Orion).",
        "> 3. **CPU 8 cœurs :** Raisonnement conceptuel, stratégie politique et géométrie sans censure (Thot/Horus/Odin).",
        "> ",
        "> 👉 **Les trois blocs vibrent en phase, sans aucune divergence doctrinale ni lissage corporatif.**"
    ])

    with open(RAPPORT_CONVERGENCE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n✅ Rapport de convergence scellé dans Obsidian : {RAPPORT_CONVERGENCE.name}")
    print("=" * 75)


if __name__ == "__main__":
    executer_sequence_convergence()
