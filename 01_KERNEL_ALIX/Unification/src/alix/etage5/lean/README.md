# L*↑ en Lean 4 — preuves générales

## `LStar/Formule.lean` — la formule d'origine L*(x) = G ⊕ H ⊕ T ⊕ D ⊕ B

| Théorème Lean | Résultat |
|---|---|
| `coherente` | Les cinq clauses sont cohérentes, même dans un univers où toutes leurs hypothèses se déclenchent |
| `G_independante` … `B_independante` | Aucune clause ne découle des quatre autres : les cinq sont nécessaires |
| `D_ne_bannit_pas_le_vide` | D seule ne bannit pas l'écrasement : une dérivation peut atteindre ∅ dans un univers qui satisfait L*(x) |
| `B_n_interdit_pas_la_boucle` | B seule n'interdit pas la boucle : une dérivation peut revenir au même objet |
| `fontaine_blanche_boucle` | La branche α de G (fontaine blanche) donne un 2-cycle ; seule β fait sortir |
| `liberation` | La libération (TH5) est prouvée en AJOUTANT R-A (croissance stricte) et « aucun pas ne mène à ∅ » |

## `LStar/Couche1.lean` — la couche 1 complète (TH1 à TH31)

Modèle généralisé : loquet (n_Λ ou aucun, forçant ou non), politique au point
de choix (β ou α), univers fini ou non borné, et ∅ comme objet du langage.
Chaque théorème vaut pour toutes les interprétations qu'il ne restreint pas.

| Théorème | Résultat |
|---|---|
| TH1 (et TH6) | prouvé : jamais ∅, pour toute interprétation et tout environnement |
| TH2, TH3, TH4, TH5 | prouvés (régime saturé pur, univers non borné) |
| TH7, TH13, TH18 | prouvés : α ne change pas D_β, β ajoute un indice neuf |
| TH8 | prouvé pour toute politique |
| TH9 | prouvé pour toute interprétation avec n_Λ ≥ 2 ou sans loquet |
| TH10, TH12 | prouvés |
| TH11 | prouvé avec deux conditions : n_Λ ≥ 1 et **univers non borné** ; dans un univers fini épuisé, le loquet ne sauve plus (`TH11_exige_univers_ouvert`) |
| TH15, TH16 | prouvés : principe des tiroirs, univers de taille N, toute interprétation |
| TH17, TH20, TH22 | réfutés au sens « sans retour » : tout mécanisme qui revient sur le passé produit un retour (`TH17_revisite`) |
| TH23 | prouvé : T_R, R et D_β ne décroissent jamais |
| TH25, TH26 | prouvés : quitter A est irréversible ; le point de non-retour est fermé |
| TH28 | prouvé |
| TH29 | prouvé avec la politique β ; faux avec α (`TH29_politique_alpha`) |
| TH30 | prouvé si le loquet ne force pas : T_R(toujours β) ≤ T_R(α), tout environnement |
| TH31 | prouvé et renforcé : **un seul** pas bloqué suffit à perdre A |

Restent hors Lean dans la couche 1 : TH14 (compte des clauses, pas une propriété de trajectoire),
TH19 (énoncé méta), TH24 et TH27 (redisent les définitions de la classification).

## `LStar/Noyau.lean` — le noyau de la v4.0 (premier modèle, cas particulier)

Lean 4.15, sans Mathlib. Même sémantique que `../noyau.py` (un attracteur c1,
politique « toujours β », loquet R-Λ qui force β, univers non borné) ; les deux
moteurs donnent des trajectoires identiques.

Ici, contrairement à l'explorateur et à Hadès, rien n'est borné : chaque
théorème vaut pour tout horizon, toute histoire, tout n_Λ concerné.

| Théorème Lean | Énoncé v4.0 | Résultat |
|---|---|---|
| `TH3` | Régime saturé : pas de retour identique | prouvé |
| `TH8` | Secours pur sans loquet : période 2 | prouvé |
| `TH9`, `TH9_trajectoire` | n_Λ ≥ 2 : retour dès le 2e pas de secours | prouvé, après n'importe quel préfixe |
| `TH11_depuis_init` | Le loquet borne l'excursion par n_Λ | prouvé avec la borne **max(n_Λ, 1)** : avec n_Λ = 0, l'excursion dure quand même un pas |
| `B0_existe` | TH21 retire la classe B0 | **réfuté** : B0 habité pour tout n_Λ |
| `TH41_refute` | En L↑, A atteignable depuis Ω0 | **réfuté** tel qu'écrit : depuis un état de secours, T_R ≥ 1 et A exige T_R = 0 |
| `atteignable_bienForme` | (invariant) | tout état atteignable en régime saturé a son compteur de secours à 0 |

Aucune preuve n'utilise `sorry` : `#print axioms` ne montre que `propext` et `Quot.sound`.

Compiler :

```
lake build
```

(ou `lean LStar/Noyau.lean` avec Lean 4.15 installé par elan.)

À faire ensuite : la non-répétition de B0 après une histoire quelconque, TH16 (tiroirs,
univers fini), puis la classification TH21–TH24 complète.
