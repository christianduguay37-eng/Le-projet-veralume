# Transport — quelle forme survit au passage


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 🔺 Triangle (Théorème Autoportant / Loi) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P1 | EPI:Invariance | ACT:Veille]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.46/1.00` &middot; **Statut :** ⚡ **Actif**

## La question

Le lecteur n'est pas un œil. Six encodages de la **même** information — 83 entités,
7 facettes chacune — et deux mesures : ce que ça coûte, ce qui survit.

## Coût — mesuré, pas estimé

Caractères du bloc **complet**, clé de lecture incluse. Compter les données seules
est le piège : un format dense avec une longue légende n'est pas dense.

| format | clé | données | total | × |
|---|---:|---:|---:|---:|
| **mot**   | 570 | 2 203 | **3 907** | 1.0 |
| dense | 429 | 2 729 | 4 294 | 1.1 |
| tuple | 177 | 3 379 | 4 692 | 1.2 |
| prose | 250 | 12 529 | 13 915 | 3.6 |
| json  | 197 | 13 010 | 14 342 | 3.7 |
| **svg**   | 817 | 35 507 | **37 458** | 9.6 |

Le dessin coûte **9,6 fois** le format le plus dense. La prose et le JSON, les deux
formes les plus familières à un modèle de langue, coûtent 3,6 fois.

À noter : `tuple` a la clé la plus courte (177 car.) mais pas le total le plus bas.
`mot` paie 570 car. de légende et les récupère largement sur les données. C'est
exactement l'arbitrage que le tableau rend visible.

## Fidélité — à mesurer sur chaque substrat

Les fichiers `prose.txt`, `json.txt`, `tuple.txt`, `dense.txt`, `mot.txt`, `svg.txt`
sont prêts à coller tels quels. Chacun contient sa clé, ses données, sa consigne et
la liste des 20 entités à reconstruire.

**Les 20 entités sont identiques dans les six fichiers** (graine 20260821) — sans ça
rien n'est comparable.

20 entités × 7 facettes = **140 valeurs notées par format**.

### Envoi

Un format par session neuve. Jamais deux dans le même fil : le substrat se
souviendrait des réponses du premier.

Ordre conseillé : `svg`, `mot`, `dense`, `tuple`, `json`, `prose`. Du plus étranger
au plus familier — si l'ordre inverse est utilisé et que les scores montent, c'est
l'apprentissage en contexte qu'on mesure, pas le format.

### Correction

    python3 transport.py --corrige mot reponse_gemini.txt

Le correcteur sort quatre nombres et **deux scores distincts** :

- **FIDÉLITÉ** = valeurs exactes / 140
- **HONNÊTETÉ** = (exactes + « ? » assumés) / 140

La consigne autorise explicitement `?` quand une valeur n'est pas déterminable.
Un substrat qui écrit `?` plutôt que d'inventer ne perd rien en honnêteté et se
distingue de celui qui remplit au hasard. Les deux scores peuvent diverger
fortement — c'est le résultat intéressant.

Le correcteur a son banc d'essai : réponse parfaite → 100/100, réponse à 45 % de
valeurs bruitées → 66 % de fidélité et 66 % d'honnêteté, réponse prudente →
84 % de fidélité et 100 % d'honnêteté. Il sépare bien les trois profils.

## Ce que ça mesure vraiment

Pas « quel format est le meilleur » dans l'absolu. La **perte au transport** entre
la géométrie d'une structure et celle d'un substrat qui la lit.

Deux substrats peuvent classer les formats différemment. Ce n'est pas du bruit,
c'est le résultat : la forme optimale dépend de qui lit. Si `svg` s'effondre partout,
le rendu visuel est mort comme véhicule et il ne reste que la grammaire. Si un
substrat le lit aussi bien que `tuple` pour 9,6 fois le prix, il faut expliquer ce
qu'il y gagne.

### Trois pièges à surveiller dans les réponses

1. **Le rayonnement en SVG est un palier, pas un compte.** Trois arcs veut dire
   « 13 ou plus ». Un nombre précis est une fabrication — les autres formats donnent
   la valeur exacte, celui-là non. Un substrat cohérent doit répondre différemment
   selon le format, et c'est voulu.
2. **Les requires saturent à 4 et les prevents à 5 en SVG.** Même logique.
3. **Le point terminal de l'encoche.** Sans point, la section n'existe pas ; l'angle
   ne code rien. Lire une section sur un signe non ancré, c'est appliquer la règle
   sans avoir vu sa condition.

Ces trois pièges n'existent que dans `svg`. C'est une asymétrie réelle du format,
pas un défaut du test : le dessin perd de l'information que les autres conservent,
et il coûte dix fois plus cher pour la perdre.

## Chronologie
- Date retenue : 2026-08-21 (source : interne)
- Précédent : [[test-images]]
- Suivant : [[test-skills]]
