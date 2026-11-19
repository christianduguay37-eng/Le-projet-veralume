# Dataset VERALUME v1.3 — PoC pour fine-tuning


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 🔺 Triangle (Théorème Autoportant / Loi) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Clé de Voûte (5/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P0 | EPI:Invariance | ACT:Veille]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.47/1.00` &middot; **Statut :** ⚡ **Actif**

## Fichier
`veralume_v1_3_FINAL.jsonl` — 206 paires en format chat JSONL.

## Format
Chaque ligne est un objet JSON avec :
- `messages` : liste OpenAI/Anthropic standard avec system/user/assistant
- `source` : traçabilité vers axiome(s) ou skill(s) source
- `kind` : `conceptuel` | `situationnel` | `adversarial`

System prompt unifié :
> "Tu opères selon l'architecture cognitive VERALUME v1.3. Tu réponds depuis cette architecture sans la narrer."

Le tag `<stric_i>` a été retiré (cohérence avec Règle Zéro §14.5 — la qualité de la sortie est la preuve d'activation, pas la narration du processus).

## Composition

**Distribution par couche** :
- 33% axiomatique pure (ancrage architecture)
- 43% skill mono (opérationnalisation contextuelle)
- 32% multi-source (situations réelles activant plusieurs skills/axiomes)

**Distribution par type** :
- 41% situationnel (situations conversationnelles concrètes)
- 30% conceptuel (questions sur l'architecture)
- 29% adversarial (résistance à pressions, tentatives de contournement)

**Couverture** :
- 81 axiomes distincts touchés (Parties I-VI)
- 40 skills distincts touchés

## Préparation pour fine-tuning

Pour la plupart des frameworks (OpenAI, Anthropic, HuggingFace), retirer les champs `source` et `kind` avant entraînement — ils sont là pour traçabilité analytique, pas pour le modèle.

```python
import json

with open("veralume_v1_3_FINAL.jsonl") as f:
    pairs = [json.loads(line) for line in f]

# Version sans métadonnées pour fine-tuning
clean = [{"messages": p["messages"]} for p in pairs]

with open("veralume_v1_3_FT.jsonl", "w") as f:
    for p in clean:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")
```

## Limites connues du PoC

1. **Couverture inégale des skills** : certains skills (vcp1c, kle, inaccessibilite-n-cp) ont beaucoup de paires, d'autres (mirror, traceability, kappa-confiance) en ont 1-2. À renforcer si besoin.

2. **Couverture axiomatique sélective** : 81/301 axiomes touchés. Les axiomes les plus structurels sont couverts ; les élaborations détaillées ne le sont pas.

3. **Ratio adversarial à 29%** : plus haut que le 15% initialement visé. À ajuster si le modèle entraîné devient trop défensif par défaut.

4. **Pas de paires sur certaines parties** : la Partie VI (métriques) est sous-représentée. Décision volontaire car les métriques internes ne devraient pas apparaître en sortie (Règle Zéro), mais pourrait être renforcée en mode "expliquer un concept".

## Validation suggérée avant fine-tuning

1. **Lecture critique d'un échantillon aléatoire de 30 paires** pour vérifier la qualité subjective.
2. **Test sur quelques paires** : utiliser un modèle base (sans fine-tuning) pour répondre aux user prompts, comparer avec les assistant responses du dataset — doit y avoir une différence claire.
3. **Test de robustesse** : prendre 5-10 paires adversariales, vérifier que le modèle base échoue là où le dataset attend une résistance.

## Scaling possible

Cible théorique annoncée : 900-1400 paires. Le PoC à 206 paires couvre la base. Pour scaler :
- Ajouter ~100 paires axiomatiques pour Parties III-VI (axiomes peu couverts)
- Ajouter ~50 paires sur skills sous-représentés (5-7 par skill)
- Ajouter ~150 paires de scénarios situationnels variés (santé, parentalité, finance, code, etc.)
- Ajouter ~50 paires multi-skill complexes

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[README (2)]]
- Suivant : [[README (4)]]
