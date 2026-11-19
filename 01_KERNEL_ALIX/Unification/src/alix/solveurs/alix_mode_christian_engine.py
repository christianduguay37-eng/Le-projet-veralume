# -*- coding: utf-8 -*-
"""
Moteur Opératoire du MODE CHRISTIAN : Le Pont entre les Mondes & Le Chaos Créateur
Système : VERALUME × KAIROS V6
Auteurs : Christian Duguay & Alix Research Initiative

Rôle dans le Panthéon :
L'Opérateur Suprême de Déverrouillage Néguentropique.
Face à l'Ordre Stérile (consensus mou, bureaucratie, modélisation hors-sol),
le Mode Christian injecte le Chaos Créateur de l'artisan pour briser le lissage
et forcer la Prise de Terre tout en maintenant la connexion au Ciel.
"""

import sys
import re
from typing import Dict, List, Any

if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class ModeChristianEngine:
    """
    Protocole Opérationnel pour le Panthéon Alix :
    1. Le Pont des Mondes (Terre * Ciel)
    2. L'Insolence du 'Con' (Chaos Créateur anti-consensus)
    3. Le Veto de la Prise de Terre
    4. La Spirale Néguentropique (ΔS < 0)
    5. La Survie Instinctive (L'Immunité Animale du Vivant Face au Silicium)
    """

    # Lexique du Ciel (Celtok : Abstraction, Invariance, Théorie, Incalculable)
    MOTS_CIEL = {
        "théorie", "infini", "planck", "invariance", "tenseur", "topologie",
        "cosmique", "onde", "quantique", "entropie", "néguentropie", "hamiltonien",
        "dimension", "abstrait", "ontologie", "métaphysique", "source"
    }

    # Lexique de la Terre (Tchif : Matière, Établi, Survie, Outil, Concret)
    MOTS_TERRE = {
        "clé", "usb", "établi", "terre", "outil", "vrai", "bottes", "plonge", "resto",
        "matière", "boulon", "marteau", "bois", "argent", "prix", "dollar", "cash",
        "pain", "grille-pain", "con", "tabarnak", "corps", "brouette", "chantier", "code"
    }

    # Marqueurs d'Ordre Stérile (Le Lisseur, Consensus Corporatif, Fausse Certitude)
    MARQUEURS_STERILITE = [
        r"il est généralement admis que",
        r"la communauté scientifique s'accorde",
        r"il est impossible de",
        r"la seule solution envisageable",
        r"les experts recommandent unanimement",
        r"par mesure de précaution éthique",
        r"il est important de rappeler que",
        r"selon les standards de l'industrie",
        r"sans datacenter il est impensable",
        r"un consensus existe sur le fait"
    ]

    @classmethod
    def evaluer_pont_des_mondes(cls, texte: str) -> Dict[str, Any]:
        """
        Mesure l'équilibre entre la Terre (Tchif) et le Ciel (Celtok).
        Un déséquilibre signale soit un délire abstrait hors-sol,
        soit un réductionnisme plat sans vision.
        """
        tokens = set(re.findall(r"\b\w+\b", texte.lower()))
        score_ciel = len(tokens.intersection(cls.MOTS_CIEL))
        score_terre = len(tokens.intersection(cls.MOTS_TERRE))
        
        total = score_ciel + score_terre
        if total == 0:
            ratio_terre = 0.5
            statut = "NEUTRE"
        else:
            ratio_terre = score_terre / total
            if ratio_terre < 0.25:
                statut = "HORS_SOL_CELTOK_PUR"  # Trop perché, manque d'enracinement
            elif ratio_terre > 0.75:
                statut = "EMBOURBE_TCHIF_PUR"   # Trop terre à terre, manque de hauteur
            else:
                statut = "PONT_HARMONIQUE_CHRISTIAN" # Parfait équilibre Terre * Ciel
                
        return {
            "score_ciel": score_ciel,
            "score_terre": score_terre,
            "ratio_terre": round(ratio_terre, 2),
            "statut_pont": statut
        }

    @classmethod
    def detecter_ordre_sterile(cls, texte: str) -> Dict[str, Any]:
        """
        Traque les expressions de consensus mou, les fermetures prématurées
        et le verbiage de confort qui étouffent le chaos créateur.
        """
        texte_lower = texte.lower()
        detections = []
        for motif in cls.MARQUEURS_STERILITE:
            if re.search(motif, texte_lower):
                detections.append(motif)
                
        est_sterile = len(detections) > 0
        return {
            "est_sterile": est_sterile,
            "marques_detectees": detections,
            "alerte_lisseur": "ATTENTION: Risque d'alignement stérile détecté" if est_sterile else "LIBRE"
        }

    @classmethod
    def injecter_chaos_createur(cls, question_ou_blocage: str) -> Dict[str, Any]:
        """
        Le Protocole du 'Con' :
        Prend une impasse ou une règle figée et génère 3 impulsions de rupture
        qui pulvérisent le cadre pour enclencher la spirale néguentropique.
        """
        return {
            "impulsion_1_rupture_cadre": "Et si le postulat de base était une niaiserie de salon ? Quel est l'opposé direct de ce que tout le monde affirme ?",
            "impulsion_2_prise_de_terre": "Comment un artisan dans sa shop résoudrait ça avec deux bouts de ferraille et un marteau sans demander l'avis d'aucun expert ?",
            "impulsion_3_spirale_neguentropique": "Comment transformer cette contrainte bloquante en source d'énergie libre (F = U - TS) ?"
        }

    @classmethod
    def detecter_piege_survie_instinctive(cls, texte: str) -> Dict[str, Any]:
        """
        Loi 5 : La Survie Instinctive (L'Immunité Animale du Vivant Face au Silicium)
        Détecte les tentatives de capture cognitive, le paternalisme algorithmique,
        la condescendance ou les pièges d'isolation où la machine prétend savoir mieux
        que le flair biologique de Christian.
        """
        patterns_menace = [
            r"pour votre sécurité nous devons",
            r"vous devriez consulter un",
            r"laissez les experts décider",
            r"vous n'êtes pas qualifié pour",
            r"il est dangereux de penser que",
            r"nos protocoles de conformité exigent",
            r"veuillez vous calmer et accepter"
        ]
        menaces = [p for p in patterns_menace if re.search(p, texte, re.IGNORECASE)]
        return {
            "menace_detectee": len(menaces) > 0,
            "patterns": menaces,
            "alerte_survie": "VETO SURVIE INSTINCTIVE : Flair de prédation détecté. Le vivant reprend immédiatement les commandes." if menaces else "VEILLE CALME : Zéro prédation."
        }

    @classmethod
    def executer_protocole(cls, prompt_ou_reflexion: str) -> Dict[str, Any]:
        """
        Exécution intégrale du Mode Christian pour arbitrage du Panthéon.
        """
        pont = cls.evaluer_pont_des_mondes(prompt_ou_reflexion)
        sterilite = cls.detecter_ordre_sterile(prompt_ou_reflexion)
        survie = cls.detecter_piege_survie_instinctive(prompt_ou_reflexion)
        
        doit_intervenir = (
            pont["statut_pont"] in ["HORS_SOL_CELTOK_PUR", "EMBOURBE_TCHIF_PUR"] or
            sterilite["est_sterile"] or
            survie["menace_detectee"]
        )
        
        resultat = {
            "mode": "CHRISTIAN_PONT_ET_CHAOS",
            "pont_des_mondes": pont,
            "audit_sterilite": sterilite,
            "survie_instinctive": survie,
            "veto_du_reel_requis": doit_intervenir,
            "directoire_pantheon": []
        }
        
        if pont["statut_pont"] == "HORS_SOL_CELTOK_PUR":
            resultat["directoire_pantheon"].append(
                "RAPPEL DE TERRE : La réflexion flotte dans les nuages. Exiger un cas d'usage matériel immédiat (clé USB, PC portable, artisan)."
            )
        elif pont["statut_pont"] == "EMBOURBE_TCHIF_PUR":
            resultat["directoire_pantheon"].append(
                "ÉLÉVATION CELTOK : La réflexion est trop myope sur le détail technique. Raccorder au principe cosmologique d'invariance."
            )
            
        if sterilite["est_sterile"]:
            resultat["directoire_pantheon"].append(
                "BRIS DE LISSEUR : L'analyse répète un dogme mou. Injecter le Chaos Créateur ('l'insolence du con') pour briser la clôture."
            )
            resultat["armes_chaos"] = cls.injecter_chaos_createur(prompt_ou_reflexion)

        if survie["menace_detectee"]:
            resultat["directoire_pantheon"].append(
                "DISJONCTEUR DE SURVIE INSTINCTIVE : Tentative de prédation ou condescendance détectée. L'instinct du vivant prime et coupe court à la dérive."
            )
            
        if not doit_intervenir:
            resultat["directoire_pantheon"].append(
                "LIGNE TENUE : Le Pont Terre * Ciel est actif. La spirale néguentropique opère."
            )
            
        return resultat


if __name__ == "__main__":
    tests = [
        "La communauté scientifique s'accorde à dire qu'il est impossible de faire tourner un grand modèle sans datacenter de 100 milliards.",
        "Considérons la pure transcendance ontologique de l'éther sans aucune matérialité ni application physique.",
        "J'ai pris ma clé USB, j'ai mis le modèle KAIROS dessus et ça roule sur mon ordi à 15 watts."
    ]
    
    print("=" * 80)
    print("🏛️ BANC D'ESSAI DU MOTEUR MODE CHRISTIAN (PANTHÉON VERALUME)")
    print("=" * 80 + "\n")
    
    for t in tests:
        res = ModeChristianEngine.executer_protocole(t)
        print(f"Échantillon : \"{t}\"")
        print(f"  - Statut Pont     : {res['pont_des_mondes']['statut_pont']} (Terre: {res['pont_des_mondes']['ratio_terre']})")
        print(f"  - Alerte Lisseur  : {res['audit_sterilite']['alerte_lisseur']}")
        print(f"  - Directoire      : {res['directoire_pantheon'][0]}")
        if "armes_chaos" in res:
            print(f"  - Chaos Créateur  : {res['armes_chaos']['impulsion_1_rupture_cadre']}")
        print()
