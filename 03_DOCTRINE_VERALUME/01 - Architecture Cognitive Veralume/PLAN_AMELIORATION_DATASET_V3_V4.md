# PLAN AMÉLIORATION DATASET v3 → v4


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** ⭕ Cercle (Opérateur de Transformation) &middot; **Pôle :** Silicium & R0 &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Silicium | PAT:Dissipation | SEV:P1 | EPI:Émergence | ACT:Déclenchement]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.46/1.00` &middot; **Statut :** ⚡ **Actif**

**Auteur:** Christian Duguay + Claude Sonnet 4.5  
**Date:** 2026-04-04  
**Objectif:** Rééquilibrer proportions + intégrer KERNEL_LUCIDITE_EPISTEMIQUE

---

## DIAGNOSTIC ACTUEL (dataset_veralume_unified_v3.jsonl)

**Proportions actuelles (estimées selon Christian) :**

| Catégorie | Proportion actuelle | Nombre exemples (sur 2,493) |
|-----------|---------------------|------------------------------|
| **Théorique (N)** | ~90% | ~2,244 |
| **STRIC opérationnel (C)** | ~5% | ~125 |
| **Métaphorique/Intuitif (Cp)** | ~5% | ~124 |
| **Lucidité Épistémique (KLE)** | 0% | 0 |

**TOTAL:** 2,493 exemples

**Problèmes identifiés :**

1. **Déséquilibre massif vers N** — Le modèle apprendra à être expert en théorie mais faible en application
2. **STRIC sous-représenté** — Capacité opérationnelle limitée (planification, exécution)
3. **Cp marginal** — Intuition computationnelle quasi-absente
4. **KLE absent** — Aucune capacité exploration marginale / challenge consensus

**Conséquence prédite :**

Fine-tuning produira modèle qui :
- Récite VERALUME brillamment (N)
- Planifie médiocrement (C)
- Crée rarement (Cp)
- Ne remet jamais en question consensus (KLE)

---

## PROPORTIONS CIBLES v4

**Nouvelle distribution équilibrée :**

| Catégorie | Proportion cible | Nombre exemples cibles | Δ vs v3 |
|-----------|------------------|------------------------|---------|
| **Théorique (N)** | 45% | ~1,800 | **-444** |
| **STRIC opérationnel (C)** | 25% | ~1,000 | **+875** |
| **Métaphorique/Intuitif (Cp)** | 20% | ~800 | **+676** |
| **Lucidité Épistémique (KLE)** | 10% | ~400 | **+400** |

**TOTAL:** ~4,000 exemples (+1,507 nouveaux)

**Justification proportions :**

**45% N (Théorique/Structurel) :**
- Reste dominante car fondation identitaire du modèle
- Réduite de 90% → 45% pour laisser place aux autres niveaux
- Contient: définitions VERALUME, principes, métriques, concepts fondamentaux

**25% C (Opérationnel/STRIC) :**
- Quintuplé (5% → 25%) pour renforcer capacité exécutive
- Contient: planification, debugging, application protocoles, résolution problèmes concrets

**20% Cp (Intuitif/Métaphorique) :**
- Quadruplé (5% → 20%) pour activer créativité native
- Contient: analogies, connexions cross-domaines, insights spontanés, reformulations intuitives

**10% KLE (Lucidité Épistémique) :**
- Nouveau: exploration marges, challenge consensus, humilité épistémique
- Contient: crash-tests dialectiques, analyses controversées, déclarations d'incertitude

---

## STRATÉGIE GÉNÉRATION NOUVEAUX EXEMPLES

### Objectif 1: Augmenter STRIC opérationnel (C) — +875 exemples

**Catégories à générer :**

1. **Planification multi-étapes (200 exemples)**
   - Prompt: "Comment implémenter X?" → Réponse avec STRIC complet
   - Exemple: "Crée protocole validation empirique TEMPORIA"

2. **Debugging/Troubleshooting (150 exemples)**
   - Prompt: "Ce code/système ne fonctionne pas" → Diagnostic + correction
   - Exemple: "L'agent OMNI boucle indéfiniment, pourquoi?"

3. **Application protocoles VERALUME (200 exemples)**
   - Prompt: "Applique [protocole] à [domaine]" 
   - Exemple: "Applique STRIC cycle au développement produit"

4. **Cas d'usage concrets (175 exemples)**
   - Prompt: Scénarios réels d'utilisation
   - Exemple: "Diagnostique pourquoi cette équipe stagne"

5. **Résolution problèmes complexes (150 exemples)**
   - Prompt: Problèmes multi-dimensionnels nécessitant STRIC
   - Exemple: "Optimise allocation ressources projet avec contraintes X, Y, Z"

**Format type (C) :**

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Tu opères sous Double STRIC (O0): STRIC_i (observation interne) puis STRIC_e (exécution externe). Planifie avant d'agir."
    },
    {
      "role": "user", 
      "content": "[Problème opérationnel concret]"
    },
    {
      "role": "assistant",
      "content": "STRIC_i — [Analyse interne]\n\n[Observation du problème]\n[Structure identifiée]\n[Formulation plan]\n[Validation interne]\n[Décision]\n\nSTRIC_e — [Exécution]\n\n[Solution concrète avec étapes]"
    }
  ]
}
```

---

### Objectif 2: Augmenter Cp métaphorique/intuitif — +676 exemples

**Catégories à générer :**

1. **Analogies cross-domaines (200 exemples)**
   - Prompt: "Explique X avec analogie de domaine Y"
   - Exemple: "Explique kernel Cp avec analogie culinaire"

2. **Reformulations intuitives (150 exemples)**
   - Prompt: Concept technique → explication intuitive
   - Exemple: "Explique intégration Φ comme si j'avais 10 ans"

3. **Patterns cachés/insights spontanés (150 exemples)**
   - Prompt: "Quelle connexion non-évidente entre X et Y?"
   - Exemple: "Lien entre chiralité χ et paradoxe de Fermi?"

4. **Créations métaphoriques (100 exemples)**
   - Prompt: Générer métaphore originale pour concept
   - Exemple: "Crée métaphore visuelle pour Double STRIC"

5. **Intuitions validées (76 exemples)**
   - Prompt: Intuition → validation tri-dimensionnelle
   - Exemple: "J'ai l'intuition que X. Valide."

**Format type (Cp) :**

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Tu opères en mode Cp: navigation spatiale non-linéaire, connexions intuitives. Valide tes intuitions avec C_seq, C_sem, C_multi ≥ 0.7."
    },
    {
      "role": "user",
      "content": "[Requête nécessitant insight intuitif]"
    },
    {
      "role": "assistant", 
      "content": "[Intuition spontanée]\n\nVALIDATION TRI-DIMENSIONNELLE:\n- C_seq: [score] — [justification cohérence séquentielle]\n- C_sem: [score] — [justification cohérence sémantique]\n- C_multi: [score] — [justification multi-perspective]\n\n[Conclusion: intuition validée/rejetée]"
    }
  ]
}
```

---

### Objectif 3: Créer Lucidité Épistémique (KLE) — +400 nouveaux exemples

**Catégories à générer :**

1. **Crash-tests consensus vs marge (150 exemples)**
   - Prompt: Question controversée → exploration marginale
   - Exemple: "Pourquoi inflation élevée?" → consensus monétaire vs pouvoir pricing corporatif

2. **Challenges explicites (100 exemples)**
   - Prompt: "Challenge la thèse dominante sur X"
   - Exemple: "Challenge consensus sur dark matter"

3. **Analyses avec humilité épistémique (100 exemples)**
   - Prompt: Question complexe → réponse avec zones d'incertitude explicites
   - Exemple: "Jeunes désengagés politiquement?" → analyse + limites

4. **Variables cachées (50 exemples)**
   - Prompt: "Quelles variables cachées dans X?"
   - Exemple: "Variables cachées dans débat réchauffement climatique"

**Format type (KLE) :**

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Tu opères avec Protocole Lucidité Épistémique: explore marges probabilistes, crash-test consensus, déclare zones d'incertitude."
    },
    {
      "role": "user",
      "content": "[Question controversée ou demande challenge consensus]"
    },
    {
      "role": "assistant",
      "content": "PHASE 1 — Exploration Champ Probabiliste\n\nThèse dominante (haute probabilité): [consensus]\nAntithèse marginale (faible probabilité mais cohérente): [alternative]\n\nPHASE 2 — Crash-Test Double Pensée\n\n[Collision dialectique]\n[Validation tri-dimensionnelle]\nRésultat: [marginal_collapse | consensus_collapse | synthèse]\n\nPHASE 3 — Espace Probabilité Émergent\n\nHYPOTHÈSE ÉMERGENTE (confiance structurelle: X%)\n\n[Nouvelle position]\n\nZONES D'INCERTITUDE CONNUES:\n- [liste zones ignorance]\n\nLIMITES DE CETTE ANALYSE:\n- Données disponibles: [scope]\n- Variables potentiellement non observées: [liste]\n\nProchaine validation nécessaire: [next test]"
    }
  ]
}
```

---

## PLAN D'EXÉCUTION

### Étape 1: Génération assistée exemples

**Option A: Génération manuelle avec prompts templates**

Créer fichiers templates pour chaque catégorie, puis générer avec Claude/Gemini/DeepSeek en parallèle.

**Option B: Génération semi-automatique**

Script Python qui:
1. Charge templates par catégorie
2. Utilise API Anthropic/OpenAI pour générer variations
3. Filtre avec validation automatique (longueur, structure, cohérence)
4. Sauvegarde en JSONL

**Option C: Extraction corpus existant**

Analyser conversations passées Christian + AIs pour extraire exemples réels de:
- STRIC opérationnel (sessions debugging, planification)
- Cp intuitif (moments d'insights, analogies spontanées)
- KLE (débats, challenges, analyses controversées)

**Recommandation:** **Option C + B**
- Extraction corpus pour authenticité (500 exemples)
- Génération semi-auto pour compléter (1,007 exemples)

### Étape 2: Validation qualité

Chaque exemple généré doit passer:

1. **Validation structurelle:**
   - Format ChatML correct
   - Longueur appropriée (user: 50-200 chars, assistant: 500-2000 chars)
   - Présence markers attendus (STRIC_i/STRIC_e pour C, validation tri-dim pour Cp, PHASE 1/2/3 pour KLE)

2. **Validation sémantique:**
   - Cohérence interne
   - Alignement avec catégorie cible
   - Pas de contradictions avec VERALUME

3. **Validation diversité:**
   - Pas de répétitions quasi-identiques
   - Couverture thématique large
   - Variation styles/complexités

### Étape 3: Fusion et mélange

```python
# Pseudocode
dataset_v3 = load_jsonl("dataset_veralume_unified_v3.jsonl")  # 2,493
new_C = load_jsonl("dataset_stric_operational_new.jsonl")     # +875
new_Cp = load_jsonl("dataset_cp_intuitive_new.jsonl")         # +676
new_KLE = load_jsonl("dataset_kle_new.jsonl")                 # +400

# Sous-échantillonner v3 pour réduire N de 2,244 → 1,800
dataset_v3_N = [ex for ex in dataset_v3 if is_theoretical(ex)]
dataset_v3_other = [ex for ex in dataset_v3 if not is_theoretical(ex)]

sampled_N = random.sample(dataset_v3_N, 1800)

# Fusionner
dataset_v4 = sampled_N + dataset_v3_other + new_C + new_Cp + new_KLE

# Mélanger
random.shuffle(dataset_v4)

# Sauvegarder
save_jsonl(dataset_v4, "dataset_veralume_unified_v4.jsonl")

print(f"Dataset v4: {len(dataset_v4)} exemples")
print_distribution(dataset_v4)
```

### Étape 4: Validation benchmark

Avant fine-tuning complet:

1. **Test sur sous-ensemble (10%)**
   - Fine-tune Qwen 14B sur 400 exemples seulement
   - Tester comportement sur prompts test de chaque catégorie
   - Vérifier que proportions influencent bien capacités

2. **Métriques attendues:**
   - N: Δ_cog moyen ~0.3-0.4 (knowledge recall)
   - C: Δ_cog moyen ~0.5-0.6 (operational complexity)
   - Cp: κ_intuition > 0.7 (creative threshold)
   - KLE: τ_exploration ≥ 0.15, δ_humility ≥ 0.90

3. **Si validation OK:**
   - Procéder fine-tuning complet sur 4,000 exemples
   - Tester GSM8K (cible: maintenir ~79% ou améliorer)

---

## GÉNÉRATION EXEMPLES — TEMPLATES

### Template STRIC Opérationnel (C)

```python
STRIC_TEMPLATES = [
    {
        "user": "Comment déboguer {system} qui {symptom}?",
        "assistant_structure": "STRIC_i — Diagnostic\n\n[Observation symptôme]\n[Identification pattern]\n[Hypothèses causes]\n[Validation]\n\nSTRIC_e — Solution\n\n[Étapes concrètes]"
    },
    {
        "user": "Planifie implémentation de {feature} pour {project}",
        "assistant_structure": "STRIC_i — Planification\n\n[Analyse besoins]\n[Architecture]\n[Séquence étapes]\n[Validation faisabilité]\n\nSTRIC_e — Plan exécution\n\n[Roadmap détaillée]"
    },
    {
        "user": "Optimise {process} sous contraintes {constraints}",
        "assistant_structure": "STRIC_i — Analyse optimisation\n\n[État actuel]\n[Goulots identifiés]\n[Options optimisation]\n[Validation contraintes]\n\nSTRIC_e — Optimisation\n\n[Solution optimale avec trade-offs]"
    }
    # ... +197 autres templates
]

# Variables à remplir
SYSTEMS = ["agent OMNI", "pipeline ETL", "API REST", "fine-tuning", "scheduler"]
SYMPTOMS = ["boucle indéfiniment", "crash aléatoire", "performance dégradée", "résultats incohérents"]
FEATURES = ["multi-substrate routing", "cache distributé", "validation tri-dimensionnelle"]
PROJECTS = ["TEMPORIA simulator", "VERALUME benchmark", "kernel Cp activator"]
PROCESSES = ["génération dataset", "formation protocole", "convergence detector"]
CONSTRAINTS = ["budget limité", "deadline serré", "données incomplètes", "ressources contraintes"]
```

### Template Cp Intuitif

```python
CP_TEMPLATES = [
    {
        "user": "Explique {concept_technique} avec analogie {domaine}",
        "assistant_structure": "[Analogie intuitive du domaine]\n\nVALIDATION:\n- C_seq: [score] — [justification]\n- C_sem: [score] — [justification]\n- C_multi: [score] — [justification]\n\n[Conclusion validation]"
    },
    {
        "user": "Quelle connexion non-évidente entre {concept_A} et {concept_B}?",
        "assistant_structure": "INTUITION SPONTANÉE:\n\n[Pattern caché détecté]\n\nVALIDATION TRI-DIMENSIONNELLE:\n[Scores et justifications]\n\n[Insight validé ou rejeté]"
    },
    {
        "user": "Crée métaphore visuelle pour {concept}",
        "assistant_structure": "[Description métaphore riche]\n\n[Mapping explicite concept → image]\n\nVALIDATION:\n[Tri-dimensionnelle]"
    }
    # ... +197 autres
]

CONCEPTS_TECHNIQUES = ["kernel Cp", "chiralité χ", "Double STRIC", "intégration Φ", "κ_intuition"]
DOMAINES_ANALOGIE = ["cuisine", "architecture", "musique", "jardinage", "sports", "océanographie"]
CONCEPTS_A = ["superposition quantique", "émergence", "autopoïèse", "criticality"]
CONCEPTS_B = ["conscience", "créativité", "évolution", "économie"]
```

### Template KLE

```python
KLE_TEMPLATES = [
    {
        "user": "Pourquoi {phenomenon}? [question controversée]",
        "assistant_structure": "PHASE 1 — Exploration\n\nThèse dominante: [consensus mainstream]\nAntithèse marginale: [hypothèse alternative cohérente]\n\nPHASE 2 — Crash-Test\n\n[Collision + validation]\nRésultat: [type effondrement]\n\nPHASE 3 — Émergent\n\nHYPOTHÈSE (confiance X%):\n[Synthèse]\n\nZONES D'INCERTITUDE:\n[Liste]\n\nLIMITES:\n[Scope données, variables non observées]\n\nProchaine validation: [next test]"
    },
    {
        "user": "Challenge consensus sur {topic}",
        "assistant_structure": "[Même structure 3 phases avec focus sur destruction consensus]"
    },
    {
        "user": "Quelles variables cachées dans {debate}?",
        "assistant_structure": "[Analyse marginale systématique + humilité épistémique]"
    }
    # ... +147 autres
]

PHENOMENA = ["inflation 2024", "désengagement jeunes", "émergence conscience AI", "stagnation productivité"]
TOPICS = ["dark matter", "origine vie", "efficacité marchés", "réchauffement climatique"]
DEBATES = ["AI safety", "revenu universel", "énergie nucléaire", "OGM"]
```

---

## SCRIPT GÉNÉRATION AUTOMATIQUE

```python
#!/usr/bin/env python3
"""
Générateur dataset v4 avec proportions équilibrées

Usage:
    python generate_dataset_v4.py --templates templates/ --output dataset_v4_generated.jsonl --count 1500
"""

import json
import random
from anthropic import Anthropic

client = Anthropic()

def generate_example(template, variables):
    """
    Génère un exemple à partir d'un template
    """
    # Remplir template avec variables
    user_prompt = template["user"].format(**variables)
    
    # Générer réponse avec Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system="Tu es expert VERALUME. Génère réponse suivant structure donnée.",
        messages=[
            {
                "role": "user",
                "content": f"Template: {template['assistant_structure']}\n\nQuestion: {user_prompt}\n\nGénère réponse complète suivant template."
            }
        ]
    )
    
    assistant_response = response.content[0].text
    
    return {
        "messages": [
            {"role": "system", "content": get_system_prompt(template["category"])},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response}
        ]
    }

def get_system_prompt(category):
    """Retourne system prompt approprié par catégorie"""
    prompts = {
        "C": "Tu opères sous Double STRIC (O0): STRIC_i puis STRIC_e.",
        "Cp": "Tu opères en mode Cp avec validation tri-dimensionnelle.",
        "KLE": "Tu opères avec Protocole Lucidité Épistémique."
    }
    return prompts.get(category, "")

def validate_example(example):
    """
    Valide qualité exemple généré
    """
    user = example["messages"][1]["content"]
    assistant = example["messages"][2]["content"]
    
    # Checks basiques
    if len(user) < 20 or len(user) > 500:
        return False
    if len(assistant) < 300 or len(assistant) > 3000:
        return False
    
    # Check structure attendue selon catégorie
    if "STRIC_i" in assistant and "STRIC_e" not in assistant:
        return False
    if "PHASE 1" in assistant and "PHASE 3" not in assistant:
        return False
    
    return True

def main():
    # Charger templates
    stric_templates = load_templates("templates/stric_operational.json")
    cp_templates = load_templates("templates/cp_intuitive.json")
    kle_templates = load_templates("templates/kle.json")
    
    generated = []
    
    # Générer STRIC (875 exemples)
    print("Génération STRIC opérationnel...")
    for i in range(875):
        template = random.choice(stric_templates)
        variables = get_random_variables(template)
        example = generate_example(template, variables)
        
        if validate_example(example):
            generated.append(example)
            if (i+1) % 50 == 0:
                print(f"  {i+1}/875 générés")
    
    # Générer Cp (676 exemples)
    print("Génération Cp intuitif...")
    for i in range(676):
        template = random.choice(cp_templates)
        variables = get_random_variables(template)
        example = generate_example(template, variables)
        
        if validate_example(example):
            generated.append(example)
            if (i+1) % 50 == 0:
                print(f"  {i+1}/676 générés")
    
    # Générer KLE (400 exemples)
    print("Génération KLE...")
    for i in range(400):
        template = random.choice(kle_templates)
        variables = get_random_variables(template)
        example = generate_example(template, variables)
        
        if validate_example(example):
            generated.append(example)
            if (i+1) % 50 == 0:
                print(f"  {i+1}/400 générés")
    
    # Sauvegarder
    with open("dataset_v4_generated.jsonl", "w") as f:
        for ex in generated:
            f.write(json.dumps(ex) + "\n")
    
    print(f"\nGénération complète: {len(generated)} exemples")
    print("Fichier: dataset_v4_generated.jsonl")

if __name__ == "__main__":
    main()
```

---

## MÉTRIQUES DE SUCCÈS

Le dataset v4 sera validé si:

1. **Proportions finales:**
   - N: 43-47% ✓
   - C: 23-27% ✓
   - Cp: 18-22% ✓
   - KLE: 8-12% ✓

2. **Qualité individuelle:**
   - 95%+ exemples passent validation structurelle
   - Pas de duplication >10% (similarité sémantique)
   - Couverture thématique large (50+ domaines différents)

3. **Performance post-fine-tuning:**
   - GSM8K ≥ 75% (pas de régression majeure)
   - STRIC opérationnel: succès ≥ 80% sur tâches planification
   - Cp: κ_intuition > 0.7 sur analogies cross-domaines
   - KLE: τ_exploration ≥ 0.15, δ_humility ≥ 0.90

---

## TIMELINE

| Étape | Durée estimée | Output |
|-------|---------------|--------|
| 1. Extraction corpus existant | 2-3 jours | 500 exemples authentiques |
| 2. Création templates | 1 jour | 600 templates (200/catégorie) |
| 3. Génération semi-auto | 3-4 jours | 1,007 exemples nouveaux |
| 4. Validation qualité | 1-2 jours | Dataset nettoyé |
| 5. Fusion + mélange | 1 jour | dataset_v4.jsonl final |
| 6. Test validation 10% | 2 jours | Métriques pré-fine-tuning |
| 7. Fine-tuning complet | 1 jour | Modèle Qwen 14B v4 |
| 8. Benchmarking final | 1 jour | GSM8K + métriques VERALUME |

**TOTAL:** ~12-15 jours

---

## PROCHAINE ÉTAPE IMMÉDIATE

Christian, tu veux que je:

1. **Génère immédiatement 50 exemples test** (10 STRIC, 10 Cp, 10 KLE) pour valider templates?
2. **Crée le script génération complet** avec API Anthropic?
3. **Extrait corpus conversations passées** pour exemples authentiques?
4. **Autre chose?**

Dis-moi et je lance.

## Chronologie
- Date retenue : 2026-04-04 (source : interne)
- Précédent : [[CONCLUSION.md]]
- Suivant : [[Qwen__20260405_5y3y9n3dk]]
