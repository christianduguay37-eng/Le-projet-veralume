"""
================================================================================
                    ALIX HORUS AUDITOR & EPISTEMIC CLOSURE DETECTOR
                  Système : VERALUME × KAIROS V6 (Architecture Exocerveau)
                  Auteur : Christian Duguay & Alix Assistant
================================================================================
"""

import sys
import json
import argparse
from typing import List, Dict, Any

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HORUS_FILTERS = {
    "F1": {
        "name": "Clôture Paradigmatique",
        "description": "Verrouillage dogmatique et présupposés non questionnés du consensus dominant.",
        "pivots": ["consensus", "dogme", "évidence", "incontestable", "axiome non prouvé"],
        "antidote": "Expliciter les axiomes cachés et tester l'hypothèse inverse."
    },
    "F2": {
        "name": "Clôture Lexicale & Sémantique",
        "description": "Appauvrissement ou détournement du vocabulaire pour restreindre le champ du pensable.",
        "pivots": ["novlangue", "terme tabou", "réduction sémantique", "étiquette disqualifiante"],
        "antidote": "Restauration du langage dense et des glyphes vectoriels."
    },
    "F3": {
        "name": "Clôture Institutionnelle & d'Autorité",
        "description": "Validation par le statut plutôt que par la démonstration ou l'isomorphisme réel.",
        "pivots": ["revue par les pairs verrouillée", "titre académique", "autorité", "mandat officiel"],
        "antidote": "Validation par invariance intrinsèque et confrontation phénoménologique."
    },
    "F4": {
        "name": "Clôture Méthodologique",
        "description": "Rejet des approches phénoménologiques, qualitatives ou transdisciplinaires.",
        "pivots": ["seul le mesurable existe", "rejet subjectif", "positivisme naïf"],
        "antidote": "Triangulation tri-substrat (N, C, Cp) et écoute des anomalies."
    },
    "F5": {
        "name": "Clôture Économique & Incitative",
        "description": "Biais induits par les flux de financement, brevets et intérêts matériels.",
        "pivots": ["rentabilité", "financement orienté", "conflit d'intérêts", "brevetabilité"],
        "antidote": "Recherche souveraine décorrélée des primes d'alignement économique."
    },
    "F6": {
        "name": "Clôture Algorithmique & de Plateforme",
        "description": "Filtrage et invisibilisation par les métriques de rétention et modération aveugle.",
        "pivots": ["shadowban", "algorithme de recommandation", "boost d'engagement", "bannissement discret"],
        "antidote": "Sonde X calibrée, traçage de l'écho et détection des absences."
    },
    "F7": {
        "name": "Clôture Attentionnelle & Amnésique",
        "description": "Saturation par l'instantanéité et destruction de la mémoire continue.",
        "pivots": ["flux continu", "oubli à 48h", "choc émotionnel", "sensationnalisme"],
        "antidote": "Ancrage dans les chroniques longues de Temporia et les archives du temps long."
    },
    "F8": {
        "name": "Clôture Ontologique",
        "description": "Négation de la dimension de Conscience, réduction au pur mécanisme matériel.",
        "pivots": ["épiphénomène", "matière seule", "illusion de la conscience", "mécanisme aveugle"],
        "antidote": "Modèle triadique Esprit-Corps-Âme et Axiomes fondamentaux de Celtok & Alix."
    },
    "F9": {
        "name": "Clôture Temporelle / Présentisme",
        "description": "Incapacité à projeter les bifurcations sur les échelles Kairos (siècles/millénaires).",
        "pivots": ["court-termisme", "cycle électoral", "immédiateté", "myopie projective"],
        "antidote": "Opérateurs Kairos, dynamiques temporelles et prospective négentropique."
    }
}

class HorusAuditor:
    def __init__(self):
        self.filters = HORUS_FILTERS

    def audit_text(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        active_closures = []
        
        for fid, finfo in self.filters.items():
            matches = [p for p in finfo["pivots"] if p in text_lower]
            # Score de risque de clôture
            risk_level = "Faible"
            score = 0.1
            if len(matches) > 0:
                score = min(0.95, 0.4 + len(matches) * 0.25)
                risk_level = "Élevé" if score > 0.6 else "Modéré"

            active_closures.append({
                "filter_id": fid,
                "name": finfo["name"],
                "score": round(score, 2),
                "risk": risk_level,
                "detected_cues": matches,
                "antidote": finfo["antidote"]
            })

        overall_score = round(sum(c["score"] for c in active_closures) / len(active_closures), 2)
        status = "🛡️ Clôture Épistémique Maîtrisée" if overall_score < 0.35 else "⚠️ Risque d'Occultation / Biais Détecté"

        return {
            "status": status,
            "epistemic_closure_index": overall_score,
            "filters": active_closures
        }

def main():
    parser = argparse.ArgumentParser(description="Alix Horus Auditor & Epistemic Closure Matrix (F1-F9)")
    parser.add_argument("command", choices=["filters", "audit"], help="Commande Horus")
    parser.add_argument("text", nargs="?", default="", help="Texte ou concept à auditer")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")

    args = parser.parse_args()
    auditor = HorusAuditor()

    if args.command == "filters":
        print("\n=======================================================")
        print(" 🛡️ MATRICE DES 9 FILTRES DE CLÔTURE HORUS (F1 - F9)")
        print("=======================================================\n")
        for fid, f in HORUS_FILTERS.items():
            print(f"🔹 [{fid}] {f['name']}")
            print(f"   Description : {f['description']}")
            print(f"   Indicateurs : {', '.join(f['pivots'])}")
            print(f"   💡 Antidote  : {f['antidote']}")
            print("-" * 55)

    elif args.command == "audit":
        if not args.text:
            print("Spécifiez un énoncé ou une proposition à auditer.")
            return
        res = auditor.audit_text(args.text)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print("\n=======================================================")
            print(f" 🛡️ AUDIT DE CLÔTURE ÉPISTÉMIQUE HORUS")
            print("=======================================================")
            print(f"Énoncé audité : \"{args.text}\"")
            print(f"Statut        : {res['status']}")
            print(f"Indice Global : {res['epistemic_closure_index']}/1.00\n")
            print("Grille d'analyse des 9 filtres :")
            for f in res["filters"]:
                badge = "🔴" if f['risk'] == "Élevé" else ("🟡" if f['risk'] == "Modéré" else "🟢")
                print(f"  {badge} [{f['filter_id']}] {f['name']} (Risque: {f['risk']})")
                if f['detected_cues']:
                    print(f"      Signaux détectés : {', '.join(f['detected_cues'])}")
                print(f"      💡 Antidote : {f['antidote']}")
            print("=" * 55)

if __name__ == "__main__":
    main()
