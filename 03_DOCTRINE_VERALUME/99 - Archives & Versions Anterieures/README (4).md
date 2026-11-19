# Sonde-Observatrice — Étape 1


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** ⏩ Double Chevron (Méthode / Protocole) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P1 | EPI:Émergence | ACT:Déclenchement]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.30/1.00` &middot; **Statut :** ⚡ **Actif**

Première donnée empirique du protocole sonde-probabiliste (voir sonde-probabiliste.md).

## Ce que ça teste

- **H-a** : la carte de résonance existe (les activations ont une géographie, pas un plat)
- **H-b** : simple résonne local, dur résonne large
- **H-c** : la fourchette allume la cuisine (même domaine → même région)

## Lancement

```bash
pip install torch transformers numpy
python sonde_observatrice.py --model google/gemma-2-2b-it --questions questions.json --out resultats/
```

Marche avec n'importe quel modèle Hugging Face causal. Commencer petit (2B) — le 2B
suffit pour tester les hypothèses, pis ça roule sur une carte modeste.

**Attention** : llama-server / GGUF n'expose pas les hidden states. Faut la version
HF du modèle (transformers + PyTorch). C'est la seule contrainte.

## Lecture des résultats

`resultats/verdict.txt` donne le verdict des trois hypothèses direct.
`resultats/resume.json` donne le détail par question.
`resultats/activations.npz` garde les empreintes brutes pour analyse plus fine.

## Si les verdicts sont faibles

Le script mesure au niveau **couche** — la granularité la plus grossière.
Si H-a ou H-c sortent plats, ça réfute pas la thèse : ça dit que la géographie
fine vit plus bas (têtes d'attention, neurones MLP). L'étape suivante serait
de sonder à cette granularité-là. Un signal même faible au niveau couche
serait déjà remarquable.

## Dataset

60 questions : 6 domaines × (5 simples + 5 dures). Les domaines incluent
"cuisine" exprès — pour que la fourchette puisse allumer la cuisine littéralement.

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[README (3)]]
- Suivant : [[README (5)]]
