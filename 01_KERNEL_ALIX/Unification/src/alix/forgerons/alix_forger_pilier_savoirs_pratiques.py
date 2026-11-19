# -*- coding: utf-8 -*-
"""
================================================================================
   FORGERON DU PILIER 09 — CATHÉDRALE DU SAVOIR UNIVERSEL SOUVERAIN
        « Connaissances Pratiques, Métiers d'Artisan & Savoirs Traditionnels »
               Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Compile et scelle le 9e Pilier de la Cathédrale du Savoir :
    1. Bushcraft, Survie & Autonomie de Terrain (HuggingFace TB CoT + Distilled Knowledge).
    2. Agriculture Régénératrice, Compostage & Maraîchage Vivrier.
    3. Savoirs Traditionnels Boréaux du Québec :
       - Travail du bois, fuste, équarrissage, abattage, séchage.
       - Forge d'atelier, trempe, recuit, affûtage des tranchants.
       - Bétonnage de chantier, maçonnerie et résistance au gel/dégel.
       - Conservation des aliments (fumage, salaison, cellier d'hiver, autoclave).
       - Pharmacopée boréale (gomme d'épinette, thé du Labrador, saule, thuya).
       - Énergie autonome hors-réseau (solaire hivernal, MPPT, LiFePO4, poêle de masse).
- Format Parquet zstd pour interrogation SIMD instantanée (< 25 ms).
================================================================================
"""

from alix.socle.chemins import HOME_DIR, VAULT_DIR
import os
import sys
import time
import json
import shutil
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"
DIR_P9 = CATHEDRALE_DIR / "09_Savoirs_Pratiques_et_Traditions"
DIR_DATA = DIR_P9 / "data"

# Corpus 1 : Les Savoirs Traditionnels Boréaux & d'Artisan du Québec
SAVOIRS_BOREAUX = [
    {
        "id": "PRAT-01",
        "domaine": "Travail du Bois & Fuste Boréale",
        "titre": "Charpente Traditionnelle, Pièce-sur-Pièce et Fuste en Bois Rond",
        "region_tradition": "Québec / Forêt Boréale",
        "mots_cles": "fuste, bois rond, piece sur piece, equarrissage, hachette, godendart, queue daronde, chene, epinette, sechage",
        "texte": (
            "La construction en pièce-sur-pièce ou en fuste scandinave adaptée au Québec utilise l'épinette noire ou le pin blanc. "
            "L'abattage s'effectue traditionnellement au cœur de l'hiver lorsque la sève est redescendue, garantissant une teneur en eau "
            "minimale et limitant les fentes de retrait. L'écorçage se fait immédiatement au printemps avant que les insectes xylophages "
            "ne pénètrent le cambium. Pour l'équarrissage à la hachette et à la cognée, on trace au cordeau noir puis on coche les flancs "
            "tous les deux pieds avant de dresser les faces au fil du bois. Les assemblages d'angle privilégient la queue d'aronde ou le "
            "mi-bois avec chevilles de bois dur (chêne ou frêne) sans clous métalliques qui créent des ponts thermiques et condensent l'humidité. "
            "L'isolation entre les rondins s'opère à la mousse de sphaigne séchée ou à l'étoupe de chanvre imprégnée d'huile de lin, offrant une "
            "respirabilité hygrométrique parfaite qui empêche le pourrissement."
        ),
        "invariant_pratique": "L'hygrométrie du bois commande sa stabilité dimensionnelle : travailler au fil du bois avec des assemblages souples qui absorbent le retrait naturel sans fissurer."
    },
    {
        "id": "PRAT-02",
        "domaine": "Forge & Métallurgie d'Atelier",
        "titre": "Forge au Charbon, Traitements Thermiques et Affûtage des Tranchants",
        "region_tradition": "Métallurgie d'Atelier Traditionnelle",
        "mots_cles": "forge, acier carbone, trempe, recuit, revenu, enclume, marteau, affutage, pierre a eau, durete rockwell",
        "texte": (
            "Le travail de l'acier au carbone (types XC75, 1095, 5160) repose sur le contrôle rigoureux des températures de transformation "
            "de phase cristalline (austénite, martensite, perlite). Le forgeage s'opère au rouge cerise clair (850°C - 950°C) sans jamais "
            "frapper l'acier en dessous du rouge sombre pour éviter les micro-fissures internes. La trempe s'effectue après normalisation "
            "(3 cycles de chauffe au rouge sombre puis refroidissement lent à l'air pour affiner le grain). L'acier est chauffé jusqu'au point "
            "non-magnétique (testé à l'aimant vers 770°C) puis plongé immédiatement dans une huile tiède à 50°C (huile de colza ou minérale). "
            "Le métal devient cassant comme du verre ; il exige un revenu immédiat de 2 heures au four à 200°C-230°C (couleur jaune paille "
            "pour les couteaux et outils à bois, bleu sombre vers 290°C pour les haches et burins absorbant les chocs). L'affûtage se termine "
            "sur pierres à eau japonaises grain 1000 puis 6000 et polissage au cuir imprégné de pâte à polir d'oxyde de chrome."
        ),
        "invariant_pratique": "L'équilibre dureté/ténacité : un outil trop dur s'ébrèche au choc, un outil trop mou s'émousse. Le revenu thermique ajuste la contrainte interne du réseau de fer."
    },
    {
        "id": "PRAT-03",
        "domaine": "Maçonnerie & Bétonnage de Chantier",
        "titre": "Formulation du Béton, Ferraillage et Prise par Temps Froid Québécois",
        "region_tradition": "Génie Civil & Chantier du Bas-Saint-Laurent",
        "mots_cles": "beton, ciment portland, gravier, sable, rapport eau ciment, ferraillage, gel degel, temps froid, cure, adjuvants",
        "texte": (
            "La formulation universelle d'un béton robuste de chantier non armé ou armé repose sur la règle volumétrique 1-2-3 : "
            "1 volume de ciment Portland (type 10 ou HE), 2 volumes de sable propre de carrière (granulométrie 0-5 mm exempt de terre et d'argile), "
            "et 3 volumes de pierre concassée (granulométrie 10-20 mm). Le facteur critique absolu est le rapport Eau/Ciment (E/C) : il ne doit jamais "
            "dépasser 0,45 à 0,50 en poids. Tout ajout excessif d'eau pour rendre le béton 'plus liquide' crée des pores capillaires qui réduisent "
            "la résistance de 50 % et provoquent l'éclatement lors du premier gel hivernal québécois. En bétonnage par temps froid (< 5°C), "
            "l'eau de gâchage doit être tiède (30°C-40°C), le granulat dégelé, et l'emploi d'un accélérateur de prise sans chlorure est recommandé. "
            "Le béton frais doit être immédiatement protégé par des bâches isolantes en polyéthylène à bulles pour conserver sa propre chaleur "
            "d'hydratation exothermique pendant les premières 72 heures. Le ferraillage (barres d'armature 10M ou 15M) doit respecter un enrobage "
            "minimal de 50 mm pour empêcher l'oxydation par l'eau d'infiltration."
        ),
        "invariant_pratique": "La résistance du béton réside dans la compacité granulaire et le minimum d'eau d'hydratation : l'eau fait prendre le ciment mais l'eau en trop crée la ruine par le gel."
    },
    {
        "id": "PRAT-04",
        "domaine": "Conservation des Aliments & Résilience",
        "titre": "Cellier d'Hiver, Fumage à l'Érable, Salaison et Autoclave Domestique",
        "region_tradition": "Savoirs de Terroir & Autonomie Québécoise",
        "mots_cles": "cellier, conservation, fumage, salaison, autoclave, botulisme, lacto-fermentation, hiver, sphaigne, sable",
        "texte": (
            "L'autonomie hivernale québécoise repose sur la combinaison de quatre méthodes complémentaires de conservation : "
            "1. Le cellier d'hiver (chambre froide semi-enterrée) : température maintenue entre 2°C et 4°C avec une humidité relative de 85-90%. "
            "Les légumes racines (carottes, betteraves, panais) sont enfouis dans des bacs de sable légèrement humide sans se toucher, les pommes "
            "de terre conservées dans le noir total sur claies ajourées pour éviter la solanine, et les courges stockées en hauteur au sec (10°C). "
            "2. La mise en conserve sous pression à l'autoclave (canner) : obligatoire pour tous les aliments peu acides (pH > 4,6 tels que viandes, "
            "volailles, poissons, bouillons et légumes non marinés). Seule une température de 116°C à 121°C maintenue sous 10 à 15 livres de pression "
            "détruit les spores thermorésistantes de Clostridium botulinum. "
            "3. La salaison et le fumage traditionnel : salage au gros sel de mer (tirage d'eau osmotique abaissant l'activité de l'eau Aw < 0,85) "
            "suivi d'un fumage à froid (< 25°C) au bois d'érable à sucre ou de merisier pendant 12 à 48 heures, déposant des composés phénoliques "
            "antioxydants et antimicrobiens. "
            "4. La lacto-fermentation : immersion des légumes dans une saumure à 2,5 % de sel. Les bactéries lactiques anaérobies produisent "
            "de l'acide lactique, faisant chuter le pH sous 4,0 en quelques jours et stabilisant le produit pour des mois sans énergie."
        ),
        "invariant_pratique": "L'inactivation biologique par abaissement de l'activité de l'eau (Aw), acidification sous pH 4.0 ou stérilisation thermique sous pression : les trois verrous anti-décomposition."
    },
    {
        "id": "PRAT-05",
        "domaine": "Pharmacopée & Médecine Traditionnelle Boréale",
        "titre": "Plantes Médicinales Boréales : Épinette, Thé du Labrador, Saule et Thuya",
        "region_tradition": "Premières Nations & Herboristerie Boréale du Québec",
        "mots_cles": "herboristerie, pharmacopee boreale, gomme depinette, the du labrador, saule blanc, thuya, salicine, terpènes, antiscorbutique",
        "texte": (
            "La forêt boréale recèle une pharmacopée de survie et de santé éprouvée par des siècles de pratique : "
            "1. La résine d'épinette noire (Picea mariana) : puissant antibactérien, cicatrisant et antifongique naturel grâce à ses diterpènes "
            "et acides résiniques. Chauffée doucement au bain-marie avec du suif d'orignal ou de l'huile de tournesol et de la cire d'abeille, "
            "elle forme un onguent souverain pour les coupures de chantier, les plaies infectées et les crevasses d'hiver. "
            "2. Le Thé du Labrador (Rhododendron groenlandicum) : les feuilles cueillies en été contiennent des tanins, des flavonoïdes et du "
            "lédon (huile essentielle hépatoprotectrice et sédative). L'infusion doit se faire dans une eau frémissante non bouillie (< 85°C) "
            "pendant 10 minutes maximum pour éviter de volatiliser les composés actifs ou de libérer des alcaloïdes irritants en excès. "
            "3. L'écorce de Saule blanc (Salix alba) : récoltée sur de jeunes branches au printemps, sa teneur en salicoside (salicine) est le "
            "précurseur naturel de l'aspirine (acide acétylsalicylique). En décoction lente de 15 minutes, elle soulage les douleurs articulaires, "
            "la fièvre et les migraines sans provoquer d'irritation gastrique majeure. "
            "4. Le Cèdre blanc / Thuya occidental (Thuja occidentalis) : les jeunes rameaux en décoction légère constituent le remède antiscorbutique "
            "légendaire transmis à Jacques Cartier à l'hiver 1535 (l'Annedda). Richesse extrême en vitamine C et en thuyone antiseptique (usage à "
            "doses modérées en cure courte)."
        ),
        "invariant_pratique": "La chimie végétale boréale comme pharmacie résiliente : extraction douce respectant les températures limites de dégradation moléculaire."
    },
    {
        "id": "PRAT-06",
        "domaine": "Énergie Autonome & Systèmes Hors-Réseau",
        "titre": "Dimensionnement Solaire Hivernal Québécois, Batteries LiFePO4 et Poêle de Masse",
        "region_tradition": "Autonomie Énergétique Réelle (Off-Grid)",
        "mots_cles": "solaire autonome, lifepo4, mppt, hiver quebecois, angle 60 degres, albedo, poele de masse, rocket stove, inertie thermique",
        "texte": (
            "L'autonomie énergétique en climat boréal nord-américain exige un dimensionnement thermique et électrique adapté aux conditions extrêmes : "
            "1. Le parc photovoltaïque d'hiver : au Québec en décembre/janvier, la course du soleil est basse (15° à 20° au zénith) et les heures d'ensoleillement "
            "réduites à 4h par jour. Les panneaux solaires doivent être inclinés à 60° ou 65° face au sud vrai. Cet angle aigu remplit un triple rôle : "
            "capter l'incidence perpendiculaire du soleil bas, évacuer spontanément la neige par gravité, et tirer parti de l'albédo réfléchi par le manteau "
            "neigeux au sol (+15 à +25 % de gain de courant). "
            "2. Stockage LiFePO4 (Lithium Fer Phosphate) : les cellules LiFePO4 possèdent une longévité de 4000+ cycles mais ne doivent JAMAIS être chargées "
            "en dessous de 0°C (risque de placage de lithium métallique irréversible et destruction de la cellule). Le parc de batteries doit impérativement "
            "résider dans l'enveloppe thermique chauffée de l'habitation ou dans un caisson isolé avec film chauffant thermostatique basse puissance. "
            "3. Le chauffage par poêle de masse (Rocket Mass Heater / Poêle à inertie) : la combustion à haute température (> 950°C dans la chambre réfractaire) "
            "brûle la totalité des gaz et suies (zéro créosote, rendement > 90%). Les fumées traversent un banc de masse en briques réfractaires ou argile "
            "de 1 à 2 tonnes qui accumule les calories et les restitue par rayonnement infrarouge doux pendant 18 à 24 heures après seulement 2 heures de flambée."
        ),
        "invariant_pratique": "La captation d'énergie intermittente exige une double gestion de l'inertie : inertie électrochimique tempérée pour le courant, inertie minérale de masse pour la chaleur."
    }
]

def main():
    print("==========================================================================")
    print(" 🛠️ FORGE DU PILIER 09 : CONNAISSANCES PRATIQUES & SAVOIRS DE TERRAIN ✨")
    print("==========================================================================")
    t0 = time.perf_counter()
    DIR_DATA.mkdir(parents=True, exist_ok=True)
    
    cache_base = (HOME_DIR / ".cache" / "huggingface" / "hub")
    
    # 1. Rapatriement du dataset CoT Bushcraft & Survival
    cot_src = cache_base / "datasets--HuggingFaceTB--CoT_Reasoning_Bushcraft_Survival" / "snapshots" / "7cd8d6df38b6fcd6cb776be56f83f54baef47024" / "data" / "train-00000-of-00001.parquet"
    if cot_src.exists():
        dst_cot = DIR_DATA / "bushcraft_cot_raisonnement_survie.parquet"
        shutil.copy2(cot_src, dst_cot)
        print(f"✅ CoT Bushcraft & Survival Parquet copié : {dst_cot.name} ({dst_cot.stat().st_size / 1024:.1f} Ko)")
        
    # 2. Conversion du dataset Bushcraft Distilled JSONL en Parquet
    jsonl_src = cache_base / "datasets--hardrave--bushcraft_survival_gpt_oss_data_distilled" / "snapshots" / "7aab6a4a84618ab40cf70e0d164f3d209e367e54" / "bushcraft_survival_gpt_oss_data_distilled.jsonl"
    if jsonl_src.exists():
        records_b = []
        with open(jsonl_src, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    # Extraction robuste selon le schéma jsonl
                    prompt = d.get("prompt", "") or d.get("instruction", "") or d.get("input", "")
                    reponse = d.get("response", "") or d.get("output", "") or d.get("completion", "")
                    if prompt or reponse:
                        records_b.append({
                            "sujet": prompt[:120].strip(),
                            "instruction": prompt,
                            "reponse_pratique": reponse
                        })
                except Exception:
                    pass
        if records_b:
            df_b = pd.DataFrame(records_b)
            dst_distilled = DIR_DATA / "bushcraft_survie_autonomie_distillee.parquet"
            table_b = pa.Table.from_pandas(df_b)
            pq.write_table(table_b, dst_distilled, compression="zstd")
            print(f"✅ Bushcraft Distillé Parquet compilé : {dst_distilled.name} ({len(df_b)} techniques de survie, {dst_distilled.stat().st_size / 1024:.1f} Ko)")

    # 3. Agriculture Régénératrice & Composting JSON en Parquet
    farm_src = cache_base / "datasets--CopyleftCultivars--SemiSynthetic_Data_For_Regenerative_Farming_Agriculture" / "snapshots" / "38adc4428f73149af2e29887c23f547ca144fabf" / "SemiSynthetic_Data_For_Regenerative_Farming_Agriculture.json"
    if farm_src.exists():
        with open(farm_src, "r", encoding="utf-8", errors="ignore") as f:
            d_farm = json.load(f)
        if isinstance(d_farm, list):
            df_farm = pd.DataFrame(d_farm)
            dst_farm = DIR_DATA / "agriculture_regeneratrice_souveraine.parquet"
            table_f = pa.Table.from_pandas(df_farm)
            pq.write_table(table_f, dst_farm, compression="zstd")
            print(f"✅ Agriculture Régénératrice Parquet compilé : {dst_farm.name} ({len(df_farm)} pratiques vivrières)")

    # 4. Compilation du Corpus Boréal & Savoirs de Métier Québécois
    df_boreal = pd.DataFrame(SAVOIRS_BOREAUX)
    dst_boreal = DIR_DATA / "savoirs_traditionnels_quebec_boreal.parquet"
    table_bor = pa.Table.from_pandas(df_boreal)
    pq.write_table(table_bor, dst_boreal, compression="zstd")
    print(f"✅ Savoirs Traditionnels Boréaux compilés : {dst_boreal.name} ({len(df_boreal)} traités de maîtrise de matière)")

    duree = (time.perf_counter() - t0) * 1000
    print("==========================================================================")
    print(f" 🚀 PILIER 09 INTÉGRÉ AVEC SUCCÈS DANS LA CATHÉDRALE EN {duree:.1f} ms !")
    print("==========================================================================")

if __name__ == "__main__":
    main()
