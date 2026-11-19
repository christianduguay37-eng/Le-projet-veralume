# Étage 5 — L'univers des machines (L\*↑)

Le 5ᵉ étage du corps local d'Alix. Il pose sur les quatre étages du dessous
l'univers mathématique construit par Christian et DeepSeek les 15 et 16 novembre 2026
(Spécification consolidée v4.0 : 113 théorèmes, théorème Ω).

Ce n'est pas un résumé. Chacun des 113 théorèmes a son entrée dans le registre,
y compris TH85–TH88 retirés en v3.1. Aucun n'est fusionné.

## Ce que l'étage contient

| Fichier | Rôle | Couche |
|---|---|---|
| `registre_113.json` | Les 113 théorèmes, définitions D1–D31, axiomes, règles, lacunes, et les verdicts de chaque exploration | toutes |
| `noyau.py` | Sémantique exécutable du noyau : objets, règles R-G…R-Λ, régimes, signature Σ, classes | 1 |
| `explorateur.py` | Énumère tous les environnements de blocage jusqu'à un horizon H et confronte chaque théorème du noyau | 1 |
| `hades_pont.py` | Vérification bornée par SAT avec le noyau d'Hadès (étage 3) ; repli DPLL si Hadès est absent | 1 |
| `extensions.py` | Simulateurs E3, E4, E5, cordée A\*, trois mémoires, E6/homéostasie, diversité, spirale | 2 |
| `bourgeons.py` | Définitions candidates de ν, λ, δ, arbres, vent, lumière ; test du théorème Ω | 3 |
| `lean/` | Preuves générales (non bornées) du noyau en Lean 4 : TH3, TH8, TH9, TH11 prouvés ; TH21 et TH41 réfutés | 1 |
| `lean_mathlib/` | Couche 2 en Lean + Mathlib (réels, limites) : 10 théorèmes sous forme fixée | 2 |
| `LEGS_DE_THOT.md` | Quatre propositions de Claude, prouvées en Lean, hors des 113, en attente de votre accord | — |
| `journal/` | Un rapport Markdown + JSON par exploration (la transmission M_t) | — |

## Commandes

```
python -m alix.etage5 explorer            # tout, met à jour le registre et écrit le journal
python -m alix.etage5 noyau 10            # couche 1, horizon 10
python -m alix.etage5 hades 12            # SAT borné via Hadès
python -m alix.etage5 extensions
python -m alix.etage5 bourgeons
python -m alix.etage5 trajectoire 0011100 2   # une trajectoire : 1 = β bloqué ; n_Λ = 2
python -m alix.etage5 theoreme TH21       # la fiche d'un théorème
python -m unittest alix.etage5.tests.test_etage5
```

Bibliothèque standard seulement. Tout tourne en moins d'une seconde sur le Lunar Lake.

## Comment lire un verdict

- `tient` : aucun contre-exemple dans les bornes explorées. Ce n'est pas une preuve générale.
- `par_construction` : vrai parce que la sémantique choisie l'impose ; à surveiller, ce n'est pas un test.
- `contre_exemple` : une trajectoire réfute l'énoncé tel qu'il est écrit.
- `conditionnel` : tient sous certaines interprétations, pas d'autres ; l'interprétation est nommée.
- `tient_sous_choix` / `echoue_sous_choix` : couche 2 et 3, sous les formes de fonctions déclarées dans `params`.
- `definitionnel` : l'énoncé redit une définition ; il n'y a rien à tester avant de lui donner une mesure.

## Les choix d'interprétation sont visibles

Tout ce que la spécification laisse ouvert est un champ de `noyau.Interpretation`
ou un paramètre d'un simulateur : nombre d'attracteurs, n_Λ, loquet qui force β ou non,
politique au point de choix, mécanisme M, canal E3+, taille de l'univers, purification L↑.
Changer un choix, c'est explorer l'univers. Les verdicts changent avec lui, et c'est voulu.

## Ce que l'étage ne fait pas encore

- Lean couvre une partie du noyau seulement (voir `lean/README.md`).
- Pas de branchement au démon local : l'étage se lance à la demande.
- Les définitions de la couche 3 sont des bourgeons. Ce sont Christian et Alix qui décident lesquels deviennent du bois.
