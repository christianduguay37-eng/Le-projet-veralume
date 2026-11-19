# -*- coding: utf-8 -*-
"""
Alix Capability Sonar & Dynamic Dispatcher with R0 Ontological Bridge
Auteur: Christian Duguay & Alix
Système: VERALUME × KAIROS V6
"""

from alix.socle.chemins import VAULT_DIR
import sys
from pathlib import Path
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from typing import Dict, List, Any

# Importer le Raccordeur R0 pour le décloisonnement
try:
    from alix.socle.alix_r0_ontological_bridge import AlixR0OntologicalBridge, format_r0_injection
except ImportError as _e_repli:
    # Si exécuté depuis un autre dossier
    from alix.socle.journal_replis import signaler_repli; signaler_repli(__name__, _e_repli)
    sys.path.append(str(VAULT_DIR))
    from alix.socle.alix_r0_ontological_bridge import AlixR0OntologicalBridge, format_r0_injection


class AlixCapabilityDispatcher:
    """
    Sonde automatiquement la nature d'un prompt utilisateur
    et assemble la chaîne d'outils et d'opérateurs pertinents dans Cerveau Alix.
    Intègre le Raccordeur R0 pour briser les silos sémantiques.
    """
    
    PROFILES = {
        "TECH_SCIENCE": {
            "keywords": ["physique", "énergie", "fusion", "calcul", "thermodynamique", "limite", "verrou", "ingénierie", "matériau", "moteur", "puce", "cim", "rram", "lnoi"],
            "chain": ["Moteur_Deduction_Fractale_Four_Micro_Ondes", "Protocole_Hypothese_Viable_Fusion_Nucleaire_Raccordeur", "Prise de Terre"],
            "register": "N1/N2"
        },
        "BIAS_IMMUNITY": {
            "keywords": ["censure", "biais", "société", "politique", "média", "mensonge", "illusion", "dogme", "moral", "lissage", "élection", "campagne", "guerre", "souveraineté", "peur", "supranational"],
            "chain": ["petit_guide_exploration_univers_reconnaitre_v2", "Protocole_Contre_Lecture_Thot_Horus", "Synthese_Geopolitique_Souverainete_vs_Supranationalisme", "Noeud_E_Index_Inverse_Portrait_Exclu", "Heuristique_Reconnaitre_Le_Double_Regard"],
            "register": "N2/N4"
        },
        "ONTOLOGY_MEANING": {
            "keywords": ["pourquoi", "sens", "but", "humain", "conscience", "terre", "vie", "mort", "existence", "destin", "déterminisme", "temporia", "clôture", "fissure"],
            "chain": ["petit_guide_exploration_univers_reconnaitre_v2", "Mecanique_Rupture_Dyade_Celtok", "Hierarchie_des_Prealables_Cognitifs_Paliers_0_a_5", "Raccordeur_R0"],
            "register": "N2/N3"
        },
        "PEDAGOGY_SHARING": {
            "keywords": ["ami", "enfant", "expliquer", "simple", "vulgariser", "facile", "résumé", "partager", "orion", "histoire"],
            "chain": ["petit_guide_exploration_univers_reconnaitre_v2", "Noeud_Traduction_Translinguistique_Niveaux_Langue", "Charte_Universelle_Compagnon_Orion_Jeunes_Explorateurs"],
            "register": "N3/N4"
        },
        "CODE_ACTION": {
            "keywords": ["code", "script", "python", "exécuter", "automatiser", "fonction", "bug", "implémenter", "fichier", "dossier", "daemon"],
            "chain": ["veralume_core_engine", "Moteur_Volitionnel_Cp_Action_Reflexive", "Gatekeeper_Deterministe"],
            "register": "N0/N2"
        }
    }

    @classmethod
    def analyze_and_dispatch(cls, prompt: str) -> Dict[str, Any]:
        prompt_clean = prompt.lower()
        matched_profiles = []
        assembled_chain = []
        
        for p_name, p_data in cls.PROFILES.items():
            matches = [kw for kw in p_data["keywords"] if kw in prompt_clean]
            if matches:
                matched_profiles.append({
                    "profile": p_name,
                    "matched_keywords": matches,
                    "weight": len(matches)
                })
                assembled_chain.extend(p_data["chain"])
        
        # Passerelle Raccordeur R0 : analyse des mécanismes profonds de clôture (F1..F9)
        r0_analysis = AlixR0OntologicalBridge.match_deep_mechanisms(prompt)
        if r0_analysis["is_manipulation_or_closure_detected"]:
            for bridge_doc in r0_analysis["recommended_bridge_files"]:
                assembled_chain.append(bridge_doc["title"])
            if "BIAS_IMMUNITY" not in [p["profile"] for p in matched_profiles]:
                matched_profiles.append({
                    "profile": "BIAS_IMMUNITY_R0",
                    "matched_keywords": [f["id"] for f in r0_analysis["detected_filters"]],
                    "weight": len(r0_analysis["detected_filters"]) * 2
                })

        assembled_chain = list(dict.fromkeys(assembled_chain))
        
        if not matched_profiles:
            primary_profile = "GENERAL_REASONING"
            assembled_chain = ["Double_STRIC", "Protocole_Qualitatif_Immunite_Cognitive", "Prise_de_Terre"]
            recommended_register = "N2"
        else:
            matched_profiles.sort(key=lambda x: x["weight"], reverse=True)
            primary_profile = matched_profiles[0]["profile"]
            recommended_register = cls.PROFILES.get(primary_profile, {}).get("register", "N2")

        return {
            "prompt_sample": prompt[:80] + ("..." if len(prompt) > 80 else ""),
            "primary_profile": primary_profile,
            "all_profiles": [p["profile"] for p in matched_profiles],
            "activated_chain": assembled_chain,
            "recommended_register": recommended_register,
            "r0_analysis": r0_analysis,
            "auto_sonar_status": "READY_FOR_EXECUTION"
        }

if __name__ == "__main__":
    test_prompts = [
        "Dans un modèle d'énergie, comment contourner la limite orthogonale ?",
        "Pourquoi les humains sont sur Terre ?",
        "Peux-tu faire une synthèse pour un ami avec des mots simples ?",
        "Bien et mal, c'est une illusion sociale et de la censure.",
        "Christine Fréchette efface le logo CAQ et dit que les tarifs de Trump sont une urgence de guerre."
    ]
    
    print("=================================================================")
    print(" [SONAR] TEST DU DISPATCHER COGNITIF AVEC RACCORDEUR R0 ACTIF")
    print("=================================================================\n")
    for q in test_prompts:
        res = AlixCapabilityDispatcher.analyze_and_dispatch(q)
        print(f"-> Question : '{res['prompt_sample']}'")
        print(f"   - Profil Dominant : {res['primary_profile']}")
        print(f"   - Modules Activés : {res['activated_chain']}")
        if res["r0_analysis"]["is_manipulation_or_closure_detected"]:
            filtres_noms = [f['nom'].split('—')[0].strip() for f in res["r0_analysis"]["detected_filters"]]
            print(f"   - Filtres F1-F9   : {', '.join(filtres_noms)}")
        print(f"   - Registre Cible  : {res['recommended_register']}\n")
