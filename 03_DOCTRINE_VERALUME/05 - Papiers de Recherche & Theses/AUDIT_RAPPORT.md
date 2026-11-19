# AUDIT & PURGE — DATASET OMNI VERALUME

### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** ⭕ Cercle (Opérateur de Transformation) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Clé de Voûte (5/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P0 | EPI:Émergence | ACT:Déclenchement]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.32/1.00` &middot; **Statut :** ⚡ **Actif**

## Rapport de nettoyage

### Sources
| Fichier | Entrées brutes |
|---|---|
| data_set_shynthese.groovy | 15 |
| omni_data_set | 137 |
| omni_dataset_v2_complete.jsonl | 227 |
| **Total brut** | **379** |

### Opérations effectuées
1. **Déduplication** : 47 doublons retirés
2. **Purge méta-projet** : 9 entrées retirées (questions sur le processus de fine-tuning)
3. **Purge qualité** : 16 entrées retirées (< 40 mots ou < 60 mots sans vocabulaire VERALUME)
4. **Harmonisation format** : Tout converti en chat format (system/user/assistant)
5. **System prompt unifié** : Un seul system prompt pour toutes les entrées
6. **<think> tags** : Retirés (14 sur 307 = inconsistant, polluerait l'apprentissage)

### Résultat
| Métrique | Valeur |
|---|---|
| Entrées finales | 307 |
| Format | Chat (messages) unifié |
| Longueur réponse min | 28 mots |
| Longueur réponse médiane | 112 mots |
| Longueur réponse max | 860 mots |

### Distribution estimée par registre
| Registre | Estimation | Cible pour entraînement optimal |
|---|---|---|
| Théorie / définitions | ~25% | ~15% |
| R1 Diagnostic (cartographie) | ~3% | **25%** ← CRITIQUE |
| R2 Tension / superposition | ~7% | **20%** ← MANQUE |
| R3 Auto-observation | ~6% | **20%** ← MANQUE |
| R4 Application à autrui | ~3% | **15%** ← MANQUE |
| R5 Edge cases / résistance | ~4% | **20%** ← MANQUE |
| Multi-IA / protocoles / autre | ~52% | ~5% |

### Problèmes restants à résoudre
1. **Déséquilibre critique** : R1, R3, R4, R5 sont sous-représentés. ~200 paires à générer.
2. **Réponses courtes** : 25% < 70 mots. Risque que le modèle apprenne à répondre court.
3. **Densité VERALUME** : 22% des réponses ont 0-1 termes VERALUME.

### Prochaine étape
Générer ~200 paires ciblées pour combler les registres manquants.

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[CPC_v11_INJECTION_DIRECTE]]
- Suivant : [[Chapitre_0_Transition]]
