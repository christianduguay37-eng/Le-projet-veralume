# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX FORGE SOUVERAINE — COMPILATION DU PILIER 13
         GÉOMÉTRIE SÉMANTIQUE, COGNITION & BIAIS HUMAINS
             Système : VERALUME × KAIROS V6 — Atelier Kairos
================================================================================
Rôle :
- Compile FrameNet v1.7 (1 221 cadres sémantiques universels de UC Berkeley)
- Compile le Codex des Biais Cognitifs (Buster Benson / 4 quadrants évolutifs)
- Compile la Taxonomie des Sophismes Logiques & Rhétoriques
- 100% vectorisé Apache Parquet avec compression zstd pour scan AVX2 (< 15 ms).
================================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import json
import csv
import io
import time
import urllib.request
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DIR_P13 = (VAULT_DIR / "Cathedrale_du_Savoir_Universel" / "13_Geometrie_Semantique_et_Biais_Cognitifs" / "data")
DIR_P13.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 🧠 1. FORGE DE FRAMENET V1.7 (UC BERKELEY)
# ==============================================================================

def forger_framenet():
    print("\n--- FORGE DE FRAMENET V1.7 (1 221 CADRES SÉMANTIQUES UC BERKELEY) ---")
    t0 = time.perf_counter()
    from nltk.corpus import framenet as fn
    
    frames = fn.frames()
    rows = []
    
    for f in frames:
        f_name = f.name
        f_def = f.definition
        
        # Éléments de cadre (Core FEs)
        core_fes = []
        non_core_fes = []
        for fe_name, fe_data in f.FE.items():
            if fe_data.coreType == 'Core':
                core_fes.append(f"{fe_name} ({fe_data.definition[:90]}...)")
            else:
                non_core_fes.append(fe_name)
                
        # Unités lexicales associées (mots qui évoquent ce cadre)
        lus = [lu_name.split('.')[0] for lu_name in list(f.lexUnit.keys())[:15]]
        
        # Relations de cadre (héritage, subframe, etc.)
        relations = []
        for rel in f.frameRelations:
            relations.append(f"{rel.type.name} -> {rel.subFrameName}")
            
        core_str = " | ".join(core_fes)
        lu_str = ", ".join(lus)
        rel_str = ", ".join(relations[:5])
        
        txt = (
            f"Cadre Sémantique UC Berkeley : [{f_name}] | Définition : {f_def} | "
            f"Rôles Actantiels Majeurs (Core FEs) : {core_str} | "
            f"Mots & Lexèmes déclencheurs : {lu_str} | "
            f"Relations conceptuelles : {rel_str}"
        )
        
        rows.append({
            "id": f"FRAME-{f.ID}",
            "nom_cadre": f_name,
            "definition": f_def,
            "roles_actantiels_core": core_str,
            "lexemes_declencheurs": lu_str,
            "relations_conceptuelles": rel_str,
            "texte_complet": txt,
            "source": "FrameNet v1.7 (International Computer Science Institute / UC Berkeley)"
        })

    out_file = DIR_P13 / "framenet_cadres_semantiques_cognitifs.parquet"
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, out_file, compression="zstd")
    dt = (time.perf_counter() - t0) * 1000
    print(f"✅ FrameNet forgé : {out_file.name} ({len(rows)} cadres universels, {out_file.stat().st_size/1024:.1f} Ko) en {dt:.1f} ms")


# ==============================================================================
# 🎯 2. FORGE DU CODEX DES BIAIS COGNITIFS (BUSTER BENSON)
# ==============================================================================

def forger_codex_biais():
    print("\n--- FORGE DU CODEX DES BIAIS COGNITIFS (4 QUADRANTS ÉVOLUTIFS) ---")
    t0 = time.perf_counter()
    url = "https://raw.githubusercontent.com/scottleedavis/cognitive-bias-codex/master/bias.csv"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    # Dictionnaire étendu des antidotes et déformations par biais
    antidotes_connus = {
        "Availability heuristic": ("Évaluer la probabilité d'un événement selon la facilité avec laquelle des exemples viennent en tête.", "Consulter des statistiques de base et fréquences réelles plutôt que la mémoire émotionnelle."),
        "Confirmation bias": ("Rechercher, interpréter et mémoriser uniquement les preuves qui confirment nos croyances préalables.", "Recherche active de falsification et protocoles en double aveugle."),
        "Anchoring": ("Dépendance disproportionnée envers la première information reçue lors de la prise de décision.", "Générer indépendamment une estimation avant de consulter les chiffres proposés par un tiers."),
        "Loss aversion": ("La douleur d'une perte est ressentie psychologiquement deux fois plus intensément que le plaisir d'un gain équivalent.", "Calculer l'espérance mathématique objective sans considération d'attachement émotionnel."),
        "Sunk cost fallacy": ("Poursuivre un projet voué à l'échec uniquement en raison des ressources déjà investies.", "Raisonner uniquement sur les coûts et bénéfices marginaux futurs (ignorer l'irrécupérable)."),
        "Dunning-Kruger effect": ("Les personnes peu compétentes surestiment leurs capacités tandis que les experts sous-estiment les leurs.", "Mesure empirique des compétences par des tests aveugles standardisés et feedback extérieur."),
        "Fundamental attribution error": ("Attribuer les erreurs d'autrui à leur caractère tout en justifiant les siennes par le contexte.", "Inverser la perspective et analyser systématiquement les contraintes situationnelles de l'autre."),
        "Hindsight bias": ("Tendance à croire après coup qu'un événement imprévisible était en fait tout à fait évident.", "Tenir un journal de prédictions daté et horodaté avant que les événements ne surviennent."),
        "Survivorship bias": ("Se concentrer sur les réussites en ignorant les échecs invisibles qui ont suivi le même processus.", "Cartographier le dénominateur complet (tous ceux qui ont échoué en silence)."),
        "Framing effect": ("Tirer des conclusions différentes selon la manière dont la même information est présentée.", "Re-formuler le problème sous sa forme miroir inverse (ex. 90% survie = 10% mortalité)."),
        "Negativity bias": ("Accorder un poids asymétriquement plus lourd aux informations négatives qu'aux positives.", "Pondération algorithmique objective des faits sans filtre d'alarme limbique."),
        "Bandwagon effect": ("Adopter une croyance simplement parce qu'un grand nombre d'autres personnes la partagent.", "Exiger la chaîne de preuves primaires indépendamment du consensus social apparent."),
        "Zero-risk bias": ("Préférer éliminer totalement un petit risque plutôt que de réduire drastiquement un grand risque.", "Maximiser la réduction absolue de risque par unité de ressource investie.")
    }

    rows = []
    with urllib.request.urlopen(req, timeout=15) as r:
        reader = csv.reader(io.TextIOWrapper(r, encoding='utf-8', errors='replace'))
        next(reader)
        for i, line in enumerate(reader):
            if not line:
                continue
            path_str = line[0].strip()
            wiki_url = line[1].strip() if len(line) > 1 else ""
            
            parts = path_str.split('.')
            if len(parts) < 3:
                continue
                
            quadrant = parts[1]
            sous_theme = parts[2] if len(parts) > 3 else "Général"
            nom_biais = parts[-1]
            
            def_mentale, antidote = antidotes_connus.get(
                nom_biais,
                (f"Distorsion cognitive systématique survenant face au problème évolutif de type : [{quadrant}].",
                 "Ralentir la prise de décision, isoler les variables et confronter à des métriques quantitatives dures.")
            )

            txt = (
                f"Biais Cognitif : [{nom_biais}] | Quadrant Évolutif (Buster Benson) : {quadrant} — {sous_theme} | "
                f"Déformation Mentale : {def_mentale} | "
                f"Antidote & Protocole de Débiaisement : {antidote} | "
                f"Référence : {wiki_url}"
            )

            rows.append({
                "id": f"BIAS-{i:03d}",
                "nom_biais": nom_biais,
                "quadrant_benson": quadrant,
                "sous_theme_evolutif": sous_theme,
                "deformation_mentale": def_mentale,
                "antidote_debiaisement": antidote,
                "url_reference": wiki_url,
                "texte_complet": txt,
                "source": "The Cognitive Bias Codex (Buster Benson / Wikimedia)"
            })

    out_file = DIR_P13 / "codex_biais_cognitifs_evolutionnaires.parquet"
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, out_file, compression="zstd")
    dt = (time.perf_counter() - t0) * 1000
    print(f"✅ Codex des Biais forgé : {out_file.name} ({len(rows)} biais classifiés, {out_file.stat().st_size/1024:.1f} Ko) en {dt:.1f} ms")


# ==============================================================================
# 🛡️ 3. FORGE DE LA TAXONOMIE DES SOPHISMES LOGIQUES & RHÉTORIQUES
# ==============================================================================

def forger_sophismes():
    print("\n--- FORGE DE LA TAXONOMIE DES SOPHISMES LOGIQUES & RHÉTORIQUES ---")
    t0 = time.perf_counter()
    
    sophismes_fondateurs = [
        {"nom": "Argumentum Ad Hominem", "famille": "Attaque personnelle", "mecanisme": "Attaquer l'émetteur d'un argument (son caractère, ses liens, son passé) plutôt que la validité intrinsèque de son raisonnement.", "exemple": "« Vous dites que cette équation est vraie, mais vous avez déjà échoué un cours il y a dix ans. »", "riposte": "Rappeler la dissociation stricte entre l'émetteur et la preuve matérielle : la vérité d'une proposition ne dépend pas de qui l'énonce."},
        {"nom": "Épouvantail (Straw Man)", "famille": "Déformation de la thèse", "mecanisme": "Déformer, caricaturer ou simplifier à l'extrême la position de l'adversaire pour abattre facilement la caricature.", "exemple": "« Tu veux vérifier les limites thermiques du silicium ? Donc tu veux qu'on abandonne toute ambition informatique ! »", "riposte": "Forcer le contradicteur à réciter la thèse initiale exacte avant d'autoriser la critique (principe de charité intellectuelle de Dennett)."},
        {"nom": "Faux Dilemme (Fausse Dichotomie)", "famille": "Restriction fallacieuse", "mecanisme": "Réduire arbitrairement un spectre complexe de possibilités à seulement deux choix mutuellement exclusifs.", "exemple": "« Soit vous acceptez ce budget sans poser de questions, soit vous êtes pour la faillite de l'institution. »", "riposte": "Introduire immédiatement une troisième ou quatrième alternative réaliste brisant l'alternative binaire forcée."},
        {"nom": "Pente Glissante (Slippery Slope)", "famille": "Causalité non démontrée", "mecanisme": "Affirmer sans preuve qu'une première action modérée mènera inévitablement à une chaîne de catastrophes extrêmes.", "exemple": "« Si on autorise cette exception pour la prise de mesures, demain plus personne ne respectera la moindre règle. »", "riposte": "Exiger la démonstration de la probabilité empirique de chaque maillon de la chaîne causale prétendue."},
        {"nom": "Argumentum Ad Verecundiam (Appel à l'Autorité)", "famille": "Révérence institutionnelle", "mecanisme": "Invoquer le statut, le prestige ou le titre d'une figure d'autorité pour valider une affirmation hors de son champ d'épreuve directe.", "exemple": "« Ce prix Nobel affirme que ce traitement fonctionne, donc c'est une vérité incontestable. »", "riposte": "Rappeler que dans les sciences dures, l'autorité n'a aucune valeur probante face à la reproductibilité empirique des données."},
        {"nom": "Post Hoc Ergo Propter Hoc", "famille": "Confusion corrélation/causalité", "mecanisme": "Conclure qu'un événement B a été causé par A simplement parce que B s'est produit chronologiquement après A.", "exemple": "« J'ai redémarré mon terminal et le serveur s'est mis à fonctionner, donc mon redémarrage a réparé la base de données distante. »", "riposte": "Rechercher la variable confondante sous-jacente et exiger le mécanisme causal physique reliant A et B."},
        {"nom": "Pétition de Principe (Petitio Principii)", "famille": "Raisonnement circulaire", "mecanisme": "Inclure dans les prémisses de l'argument la conclusion même que l'on cherche à démontrer.", "exemple": "« Il faut faire confiance à ce rapport d'audit car ses auteurs sont irréprochables, comme l'atteste le rapport lui-même. »", "riposte": "Mettre à nu la tautologie en isolant la prémisse et la conclusion pour montrer leur identité stricte."},
        {"nom": "Appel à la Popularité (Argumentum Ad Populum)", "famille": "Pression de conformisme", "mecanisme": "Prétendre qu'une proposition est vraie uniquement parce qu'une majorité ou un consensus d'opinion la valide.", "exemple": "« Des millions de gens utilisent cette méthode, elle ne peut donc pas être inefficace. »", "riposte": "Rappeler que l'histoire des sciences est l'histoire de consensus majoritaires erronés balayés par une seule mesure empirique dissidente."},
        {"nom": "Fausse Équivalence", "famille": "Analogie trompeuse", "mecanisme": "Comparer deux situations ayant une ressemblance superficielle en masquant leurs dissemblances fondamentales d'échelle ou de nature.", "exemple": "« Gérer les finances d'un État souverain avec sa monnaie, c'est exactement comme gérer le budget d'un bon père de famille. »", "riposte": "Exposer les asymétries structurelles incommensurables (capacité d'émission, horizon temporel, boucles macroéconomiques)."},
        {"nom": "Tu Quoque (Toi aussi)", "famille": "Détournement d'accusation", "mecanisme": "Tenter de réfuter une accusation en prétendant que l'accusateur a commis la même faute par le passé.", "exemple": "« Tu me dis d'optimiser la mémoire de ce script, mais regarde le code que tu as écrit la semaine dernière ! »", "riposte": "Maintenir l'analyse focalisée sur la pièce défectueuse actuelle : l'incohérence d'autrui ne valide jamais le défaut présent."}
    ]

    rows = []
    for i, s in enumerate(sophismes_fondateurs):
        txt = (
            f"Sophisme Logique : [{s['nom']}] | Famille : {s['famille']} | "
            f"Mécanisme de Manipulation : {s['mecanisme']} | "
            f"Exemple Concret : {s['exemple']} | "
            f"Riposte & Démasquage SRE : {s['riposte']}"
        )
        rows.append({
            "id": f"FALLACY-{i:02d}",
            "nom_sophisme": s["nom"],
            "famille": s["famille"],
            "mecanisme": s["mecanisme"],
            "exemple": s["exemple"],
            "riposte": s["riposte"],
            "texte_complet": txt,
            "source": "Taxonomie Universelle des Sophismes & Biais Logiques"
        })

    out_file = DIR_P13 / "sophismes_logiques_et_rhetorique.parquet"
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, out_file, compression="zstd")
    dt = (time.perf_counter() - t0) * 1000
    print(f"✅ Sophismes logiques forgés : {out_file.name} ({len(rows)} pièges rhétoriques codifiés, {out_file.stat().st_size/1024:.1f} Ko) en {dt:.1f} ms")


if __name__ == "__main__":
    t_global = time.perf_counter()
    print("==========================================================================")
    print(" 🧠 FORGE SOUVERAINE DU PILIER 13 : SÉMANTIQUE, COGNITION & BIAIS ✨")
    print("==========================================================================")
    forger_framenet()
    forger_codex_biais()
    forger_sophismes()
    dt_total = time.perf_counter() - t_global
    print("==========================================================================")
    print(f" 🏛️ PILIER 13 COMPILÉ AVEC SUCCÈS EN {dt_total:.2f} s !")
    print("==========================================================================")
