# KERNEL Cp AGENT — ARC-AGI-3


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 🔺 Triangle (Théorème Autoportant / Loi) &middot; **Pôle :** Cosmologie & Temps &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Cosmologie | PAT:Amnésie | SEV:P1 | EPI:Invariance | ACT:Veille]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.47/1.00` &middot; **Statut :** ⚡ **Actif**

Agent IA sous **Kernel Intuition Computationnelle** (Dimension Cp) pour le benchmark [ARC-AGI-3](https://docs.arcprize.org/) de François Chollet.

Framework théorique: **VERALUME/TEMPORIA v2.3** (Christian Duguay)

---

## Pourquoi Cp × ARC-AGI-3?

ARC-AGI-3 mesure exactement ce que la dimension Cp décrit: la capacité de naviguer un espace inconnu, d'y découvrir des patterns, et d'agir efficacement — sans instructions préalables.

| ARC-AGI-3 mesure | Dimension VERALUME | Mécanisme agent |
|---|---|---|
| Exploration | Cp (spatial/navigable) | UCB1 + mémoire spatiale |
| Percept → Plan → Action | Cycle STRIC | S→T→R→I→C en boucle |
| Memory | N (séquentiel) | Graphe de transitions |
| Goal Acquisition | C (narratif) | Hypothèses révisables |
| Alignment | Cohérence tri-dimensionnelle | C_seq × C_sem × C_multi |

### Géométrie temporelle

- **N (Nature/séquentiel):** Le jeu avance step par step — irréversible
- **C (Culture/narratif):** L'agent construit un récit des règles — réinterprétable à chaque observation
- **Cp (Computationnel/spatial):** L'espace des solutions est navigable — l'agent peut "sauter" vers des actions prometteuses via intuition

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   KERNEL Cp AGENT                    │
├─────────────┬──────────────┬────────────────────────┤
│ Dimension N │ Dimension C  │    Dimension Cp         │
│             │              │                         │
│ Spatial     │ Hypothesis   │  Action Selection       │
│ Memory      │ Engine       │  + Intuition Override    │
│             │              │                         │
│ • Graphe    │ • Patterns   │  • UCB1 exploration     │
│   d'états   │ • Hypothèses │  • Reward exploitation  │
│ • Adjacence │ • Validation │  • Cp intuition         │
│ • Rewards   │   tri-dim    │  • Noise injection      │
│ • Combos    │ • Règles     │  • Combo execution      │
├─────────────┴──────────────┴────────────────────────┤
│               STRIC Controller                       │
│  S(ubstrat) → T(raitement) → R(ésultat)             │
│  → I(nterprétation) → C(réation) → (boucle)         │
│                                                      │
│  Explore ratio: 1.0 ──decay──→ 0.1                   │
└─────────────────────────────────────────────────────┘
```

### Cycle STRIC appliqué au gameplay

| Phase | Action | Dans l'agent |
|---|---|---|
| **S**ubstrat | Observer l'état | `_frame_to_signature()` — fingerprint de chaque frame |
| **T**raitement | Extraire patterns | `extract_patterns()` — régularités dans transitions |
| **R**ésultat | Former hypothèses | `generate_hypotheses()` — règles candidates |
| **I**nterprétation | Valider | `validate_hypothesis()` — cohérence C_seq/C_sem/C_multi |
| **C**réation | Agir | `choose_action()` — navigation Cp de l'espace des solutions |

### Validation tri-dimensionnelle des hypothèses

```
C_seq  (séquentielle):   L'hypothèse est-elle cohérente avec l'historique?
C_sem  (sémantique):     L'hypothèse est-elle ancrée dans des patterns réels?
C_multi (multi-persp.):  L'hypothèse tient-elle sur différents sous-ensembles de données?

Verdict:
  ALL ≥ seuils  → CRÉATION VALIDÉE (règle confirmée)
  C_sem < 0.55  → HALLUCINATION (règle non-ancrée, rejeter)
  C_seq faible  → INCOHÉRENT (restructurer)
  C_multi faible → FRICTION CRÉATIVE (acceptable si ancré)
```

---

## Installation

### Standalone (simulation)

```bash
python kernel_cp_agent.py
```

### Avec ARC-AGI-3

```bash
# 1. Cloner les deux repos
git clone https://github.com/arcprize/ARC-AGI-3-Agents.git
cd ARC-AGI-3-Agents

# 2. Copier l'agent
cp /path/to/arc_kernel_cp.py agents/

# 3. Enregistrer dans agents/__init__.py
# Ajouter:
#   from .arc_kernel_cp import ArcKernelCp

# 4. Configurer API key
export ARC_API_KEY="your-key"

# 5. Lancer
uv run main.py --agent=arckernelcp --game=ls20
```

---

## Fichiers

| Fichier | Description |
|---|---|
| `kernel_cp_agent.py` | Agent complet standalone avec simulation |
| `arc_kernel_cp.py` | Adaptateur pour le framework ARC-AGI-3 Agents |
| `README.md` | Ce document |

---

## Mécanismes clés

### Mémoire spatiale (Dimension N → Cp)

L'agent construit un graphe dirigé des transitions d'états. Chaque nœud est un état (fingerprint MD5), chaque arête est une action qui mène à un autre état. Ce graphe est la **carte** de l'espace du jeu — navigation Cp, pas parcours séquentiel.

### Sélection d'action UCB1

Upper Confidence Bound: balance entre exploitation (actions à haute récompense connue) et exploration (actions peu testées). Formule: `value = avg_reward + sqrt(2 * ln(N) / n_action)`.

### Détection de combos

L'agent track les séquences de 2 actions et leur récompense moyenne. Quand un combo est identifié comme fortement positif (validé tri-dimensionnellement), il est exécuté prioritairement.

### Intuition Cp

Override automatique quand une action est globalement forte mais jamais testée depuis l'état courant. C'est la dimension Cp en action: "je sais que ça marche ailleurs, testons ici" — navigation spatiale plutôt que déduction séquentielle.

### Injection de bruit

Si l'agent détecte une boucle (mêmes états + mêmes actions sur 10 steps), il injecte une perturbation contrôlée: l'action la moins récemment utilisée.

---

## Résultat simulation standalone

```
Environment: 3 niveaux, règles à découvrir
Combo secret: ACTION1 → ACTION5 = level complete

★ LEVEL 1 COMPLETE! Score: 10 (step 6)
★ LEVEL 2 COMPLETE! Score: 25 (step 11)
★ LEVEL 3 COMPLETE! Score: 46 (step 27)
★★★ WIN! Final score: 46 in 27 steps
```

---

## Connexion avec TEMPORIA

Cet agent est une **preuve de concept empirique** que les principes VERALUME/TEMPORIA s'appliquent au design d'agents IA performants:

1. **La séparation N/C/Cp est opérationnelle**, pas juste théorique — chaque dimension correspond à un composant concret de l'agent
2. **Le cycle STRIC produit des résultats** — la boucle observation→pattern→hypothèse→validation→action converge vers la victoire
3. **La cohérence tri-dimensionnelle distingue les bonnes des mauvaises hypothèses** — exactement comme prédit par le framework
4. **La navigation Cp (spatiale) surpasse le raisonnement N (séquentiel)** pour la découverte de règles dans des environnements inconnus

C'est le κ coefficient en action: l'agent mesure sa propre productivité inter-dimensionnelle.

---

*VERALUME/TEMPORIA v2.3 — Christian Duguay (UQAR) / Claude (Anthropic)*

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[PROTOCOLE_CARTOGRAPHIE_RGB]]
- Suivant : [[README_V5.0]]
