---
titre: "Consensus ancré sur un complexe simplicial : analyse critique et correction d'une architecture de consensus distribué sans maître pour agents asymétriques"
auteur: "Christian Duguay — Atelier Kairos, Rimouski (Québec)"
date: "2026-10-20"
version: "0.1 — prépublication (brouillon de travail)"
code: "simulation_simplexe.py (graine 20261020)"
---

# Consensus ancré sur un complexe simplicial
## Analyse critique et correction d'une architecture de consensus distribué sans maître pour agents asymétriques

**Christian Duguay** — Atelier Kairos, Rimouski (Québec)
Version 0.1 — 20 octobre 2026 — prépublication

---

### Résumé

On étudie un réseau d'agents **asymétriques** : des nœuds de périphérie à faible capacité de calcul qui disposent de capteurs physiques, et des nœuds infonuagiques à forte capacité qui n'ont aucun accès direct à la vérité de terrain. Une architecture de consensus sans maître, appelée SGTD (*Semantic Gossip with Topological Damping*), a été proposée pour ce cadre. Elle combine (i) un gossip avec répulsion des mises à jour trop corrélées, (ii) une surveillance de la connectivité algébrique $\lambda_2$, (iii) une définition topologique de l'« hallucination distribuée » comme cavité $\beta_2 > 0$ d'un complexe simplicial dont les 3-simplexes représentent la validation matérielle, et (iv) une fonction de coût d'arbitrage censée empêcher l'écrasement des nœuds faibles.

Nous formalisons chaque composante, puis nous la testons par démonstration et par simulation reproductible. Résultats : (1) toute règle pair-à-pair symétrique, répulsion comprise, laisse invariante la moyenne du réseau. Elle ne peut donc pas corriger un biais partagé : **seul l'ancrage matériel corrige l'erreur collective**. (2) Dans sa lecture littérale, l'invariant $\beta_2$ produit **100 % de faux positifs**. Nous en donnons la valeur exacte, $\binom{m-1}{3}-\binom{s-1}{3}$ pour une clique d'accord de $m$ agents dont $s$ sont ancrés. Si l'on ajoute les tétraèdres d'agents, il devient au contraire aveugle. (3) L'invariant pertinent est le **$\beta_0$ réduit du complexe conifié sur la vérité matérielle**. Il compte les composantes d'accord sans ancre, se calcule par un simple parcours de graphe et donne 0 % de faux positifs et 100 % de détection dans nos scénarios. (4) La fonction de coût telle qu'écrite contient une erreur de signe qui rend l'objectif non borné. Une fois le signe corrigé, la forme non bornée donne un droit de veto à tout nœud qui ment sur sa capacité. Nous proposons une forme bornée, pondérée par l'information **vérifiée**. Nous montrons qu'à l'optimum statistique, l'influence d'un nœud dépend de l'information vérifiée qu'il apporte et non de sa taille.

---

## 1. Introduction

Les architectures hybrides périphérie/infonuagique posent un problème de gouvernance épistémique. Les nœuds les plus puissants (modèles infonuagiques) sont souvent les plus éloignés de la mesure physique. Les nœuds les plus proches de la mesure (NPU embarqués, capteurs) sont les plus faibles. Un vote majoritaire ou un vote pondéré par la capacité donne alors raison aux puissants, même quand ils partagent une erreur commune, par exemple un biais d'entraînement.

Ce travail part d'une proposition d'architecture (SGTD) produite lors d'un dialogue avec un modèle de langage (voir §8, *Divulgation*). Nous la traitons comme une **hypothèse de conception** à éprouver, pas comme un résultat. Nos contributions :

1. une formalisation de chaque composante de SGTD et l'identification de ses défauts, avec démonstrations (§3) ;
2. un résultat d'impossibilité simple : aucune règle pair-à-pair symétrique ne corrige un biais partagé (Proposition 1) ;
3. la construction du **complexe conifié sur la vérité matérielle**, le calcul exact de $\beta_2$ dans ce complexe (Proposition 3) et le remplacement de $\beta_2$ par $\tilde\beta_0$ (Proposition 2) ;
4. une fonction d'arbitrage corrigée, bornée et pondérée par l'information vérifiée (Propositions 4 à 6) ;
5. quatre expériences numériques reproductibles (§4).

## 2. Cadre et proposition initiale

**Agents.** $N$ agents ; l'agent $i$ maintient un état $x_i \in \mathbb{R}^d$. L'état vrai du monde est $x^\star$. Un sous-ensemble $S$ d'agents possède un capteur qui fournit $y_i = x^\star + \varepsilon_i$, avec $\varepsilon_i \sim \mathcal{N}(0, \sigma_i^2 I)$. Le graphe de communication est $A$ et son laplacien $L = D - A$. Chaque agent a une capacité de calcul $c_i$.

**Proposition SGTD (résumé fidèle).**
- *Mise à jour* : $x_i(t+1) = x_i(t) + \eta \sum_j A_{ij}(\Delta x_j - \Delta x_i) - \gamma \nabla_{x_i} D_{\text{cross-talk}}$. La règle de répulsion inverse le couplage entre $i$ et $j$ si la similarité cosinus de leurs mises à jour dépasse un seuil $\theta$, dans le but de « briser les chambres d'écho ».
- *Connexité* : surveiller $\lambda_2(L)$. Si $\lambda_2 \to 0$, créer des liens longue portée (*small-world rewiring*).
- *Topologie* : 0-simplexes = agents ; 1-simplexes = liens ; 2-simplexes = triades en accord ; 3-simplexes = triades **validées par une télémétrie matérielle**. Une hallucination distribuée est définie comme une cavité $\beta_2 > 0$.
- *Arbitrage* : coût de rejet de l'état $x_k$ au profit de $x_g$ :
$$J_k = \alpha\lVert x_k - x_g\rVert^2 + \beta\frac{E_{tx}(k)}{E_{res}(k)} - \lambda\frac{I(x_k)}{c_k^{\delta}}$$
où $I$ est présentée comme une information de Fisher.
- *Affirmations quantitatives non étayées* : convergence < 200 ms pour 10 000 nœuds via un Merkle-DAG, $\lambda_2$ à ±4 % par Lanczos, filtre de Butterworth ajoutant 15 ms. **Aucune n'est évaluée ici et aucune n'est reprise dans nos conclusions.**

## 3. Analyse formelle

### 3.1 Dynamique : diffuser les écarts d'état, pas les incréments

Diffuser $\Delta x_j - \Delta x_i$ fait converger les **incréments** et non les états. Si $\Delta x_i = \Delta x_j$ pour tout couple, les écarts $x_i - x_j$ restent constants et le désaccord ne décroît jamais. Nous utilisons donc la forme standard (Olfati-Saber et Murray, 2004), complétée d'un terme d'ancrage :
$$x_i(t+1) = x_i(t) + \eta\sum_j W_{ij}(x_j - x_i) + \kappa\,a_i\,(y_i(t) - x_i(t)),$$
avec $a_i = 1$ si $i \in S$. On a $W = A$ sans répulsion, et $W_{ij} = -A_{ij}$ quand la règle de répulsion s'active.

**Proposition 1 (invariance de la moyenne).** Si $W$ est symétrique, alors pour $\kappa = 0$ la moyenne $\bar x(t) = \frac1N\sum_i x_i(t)$ est constante, quels que soient les signes de $W$.

*Preuve.* $\sum_i\sum_j W_{ij}(x_j - x_i) = \sum_{i,j}W_{ij}x_j - \sum_{i,j}W_{ij}x_i = 0$ par symétrie. $\square$

**Conséquence.** Une chambre d'écho est un biais **partagé** $b$ : tous les agents sont décalés de $b$. C'est une erreur de mode commun, invisible pour toute règle qui ne voit que des différences entre pairs. La répulsion agit sur le désaccord et jamais sur la moyenne. Elle ne peut donc pas corriger ce type d'erreur. Le seul terme qui déplace $\bar x$ est l'ancrage $\kappa\,a_i(y_i - x_i)$. L'intuition centrale de la proposition, selon laquelle la vérité vient de la validation matérielle et non du vote, est donc **correcte et nécessaire**. C'est le mécanisme de répulsion qui est superflu.

### 3.2 Connexité

Surveiller $\lambda_2$ est classique et fondé (Fiedler, 1973) : $\lambda_2 > 0$ si et seulement si le graphe est connexe. Deux corrections s'imposent. (a) $\lambda_2$ est la **deuxième plus petite** valeur propre du laplacien ; une itération de Lanczos doit viser l'extrémité basse du spectre, pas « les 5 plus grandes ». (b) La marge de ±4 % n'a pas de source. La réécriture suppose un canal hors bande (infonuagique) et la connaissance des composantes, ce qui revient en pratique à un oracle partiel.

### 3.3 Hallucination topologique : le complexe conifié

**Construction.** On prend comme sommets les agents plus un sommet spécial $G$ (la « vérité matérielle »). Un agent $i$ est *ancré* s'il possède un capteur et que $\lVert x_i - y_i\rVert < \tau_a$. Les arêtes entre agents relient les paires en accord ($\lVert x_i - x_j\rVert < \tau$) ; les triangles sont les triades en accord. Pour qu'un « 3-simplexe de validation matérielle » soit un vrai simplexe (4 sommets), nous l'écrivons $\{i,j,k,G\}$. Fermer le complexe par faces impose alors d'ajouter $\{i,G\}$, $\{i,j,G\}$ et ainsi de suite. Le complexe obtenu est
$$K = K_{\text{acc}} \;\cup\; \operatorname{Cone}_G\!\big(K_{\text{acc}}[\mathcal{A}]\big),$$
où $K_{\text{acc}}$ est le complexe d'accord et $\mathcal{A}$ l'ensemble des agents ancrés. Deux variantes sont possibles. La variante **littérale** n'a aucun tétraèdre entre agents, car seule la validation matérielle remplit. La variante **clique** contient le complexe de cliques complet jusqu'à la dimension 3.

Le cône étant contractile, $K \simeq K_{\text{acc}}/K_{\text{acc}}[\mathcal{A}]$, d'où $\tilde H_n(K) \cong H_n(K_{\text{acc}}, K_{\text{acc}}[\mathcal{A}])$ (homologie relative ; Hatcher, 2002).

**Proposition 2 ($\tilde\beta_0$ détecte les accords non ancrés).** Si $\mathcal{A} \neq \emptyset$, alors $\beta_0(K) - 1$ est égal au nombre de composantes connexes du graphe d'accord qui ne contiennent aucun agent ancré.

*Preuve.* $G$ est adjacent à tout agent ancré. Toute composante qui contient un ancré fusionne avec celle de $G$ ; les autres restent isolées. $\square$

Ce test coûte un parcours de graphe en $O(N + |E|)$.

**Proposition 3 ($\beta_2$ littéral = faux positifs structurels).** Dans la variante littérale, soit une clique d'accord de $m$ agents dont $s$ sont ancrés. Sa contribution à $\beta_2(K)$ vaut
$$\beta_2 = \binom{m-1}{3} - \binom{s-1}{3}\quad\big(\text{avec } \tbinom{n}{3} = 0 \text{ pour } n < 3\big).$$

*Preuve.* $K_{\text{acc}}$ est le 2-squelette d'un $(m-1)$-simplexe, donc $H_2 \cong \mathbb{Z}^{\binom{m-1}{3}}$ et $H_1 = 0$. Même chose pour le sous-complexe ancré, avec $\binom{s-1}{3}$. Dans la suite exacte longue de la paire, $H_2(K_{\mathcal A}) \to H_2(K_{\text{acc}})$ est injective, car il n'y a pas de 3-cellule dans $K_{\text{acc}}$, et $H_1(K_{\mathcal A}) = 0$. On en déduit $\operatorname{rang} H_2(K_{\text{acc}}, K_{\mathcal A}) = \binom{m-1}{3} - \binom{s-1}{3}$. $\square$

Cette quantité est strictement positive dès que $m \geq 4$ et $m > s$. Autrement dit, **tout consensus honnête de 4 agents ou plus comprenant au moins un agent sans capteur est signalé comme hallucination**. Dans la variante clique, à l'inverse, toute clique d'accord est remplie par ses tétraèdres et ne contribue jamais à $\beta_2$ : des colludants en accord mutuel sont invisibles. $\beta_2$ ne fonctionne donc dans aucune des deux variantes. Nous confirmons numériquement les deux résultats au §4.3. Pour le cas $s = 0$, $m = 3 \dots 7$, les valeurs mesurées 0, 1, 4, 10, 20 coïncident avec $\binom{m-1}{3}$.

### 3.4 Arbitrage

**Lecture littérale (additive).** Dans $J_k$, les termes énergie et protection ne dépendent pas de $x_g$. Dans un arbitrage continu $x_g = \arg\min \sum_k J_k$, ils n'ont **aucun effet** sur l'état choisi : la formule ne protège rien. Dans une lecture discrète (on accepte ou on rejette $x_k$), le signe moins fait tendre le coût de rejet vers $-\infty$ quand $c_k \to 0$, ce qui pousse à rejeter systématiquement les nœuds faibles, l'inverse de l'intention déclarée. Le signe plus le fait tendre vers $+\infty$ : veto inconditionnel.

**Forme multiplicative.** Pour que la protection agisse sur l'état, elle doit pondérer la dérive :
$$x^\ast = \arg\min_x \Phi(x),\qquad \Phi(x) = \sum_k \pi_k\lVert x - x_k\rVert^2,\qquad x^\ast = \frac{\sum_k\pi_k x_k}{\sum_k\pi_k}.$$

**Proposition 4 (signe moins).** Avec $\pi_k = \alpha - \lambda I_k/c_k^{\delta}$, le hessien de $\Phi$ vaut $2(\sum_k\pi_k)I$. Dès que $c_k^{\delta} < \lambda I_k / \big(\alpha + \sum_{j\neq k}\pi_j\big)$ pour un nœud informatif, on a $\sum\pi < 0$ : $\Phi$ est concave et non bornée inférieurement, **il n'existe pas d'arbitrage**. $\square$

**Proposition 5 (signe plus non borné).** Avec $\pi_k = \alpha + \lambda I_k/c_k^{\delta}$, on a $\pi_k \to \infty$ quand $c_k \to 0$, donc $x^\ast \to x_k$. Un nœud qui **déclare** une faible capacité et une forte information dicte le consensus. Comme ni $c_k$ ni $I_k$ ne sont vérifiés, la règle est exploitable par un nœud byzantin ou par une attaque Sybil (Lamport et al., 1982 ; Douceur, 2002). $\square$

**Proposition 6 (l'optimum ne dépend pas de la taille).** Si le nœud $k$ fournit $y_k = x^\star + \varepsilon_k$ avec $\varepsilon_k \sim \mathcal{N}(0, \sigma_k^2 I)$, l'information de Fisher sur $x^\star$ vaut $I_k = \sigma_k^{-2}$ par coordonnée. L'estimateur du maximum de vraisemblance est $x^\ast = \sum_k I_k y_k / \sum_k I_k$, de variance minimale (borne de Cramér-Rao ; Kay, 1993). La capacité $c_k$ n'apparaît pas. $\square$

**Interprétation.** Le nœud faible doit être protégé parce qu'il apporte de l'information **vérifiée**, pas parce qu'il est petit. Un poids en $1/c$ n'a pas de justification statistique : c'est au mieux un *a priori* d'équité, et il doit rester borné. Nous proposons :
$$\pi_k = \alpha + \lambda\,\frac{\tilde I_k}{(c_k + c_0)^{\delta}},$$
où $\tilde I_k$ est l'information **auditée**, nulle si le capteur n'est pas vérifié, et $c_0 > 0$ borne le poids. Avec $\delta = 0$, on retrouve la pondération par variance inverse.

Le terme énergétique $\beta E_{tx}/E_{res}$ est constant en $x$. Il n'a de sens que pour l'élagage des liens ($A_{ij} \to 0$ si $E_j < E_{\min}$), comme le prévoyait d'ailleurs la proposition initiale.

## 4. Expériences

Tout provient de `simulation_simplexe.py` (numpy 2.3.5, graine 20261020), exécuté en 4,5 s sur un Intel Core Ultra 7 258V. Les séries complètes sont dans `resultats.json`. Dimension d'état : $d = 8$.

### 4.1 E1 : dynamique et chambre d'écho

Graphe géométrique aléatoire, $N = 30$, 113 arêtes, $\lambda_2 = 0{,}706$. Neuf agents ont un capteur (30 %), avec un bruit $\sigma = 0{,}1$. Les états initiaux portent un biais partagé de norme 1 et une dispersion de 0,5. 300 itérations, $\kappa = 0{,}2$, $\theta = 0{,}9$.

| Variante | RMSE finale à la vérité | Désaccord final |
|---|---|---|
| Laplacien pur | 0,9686 | 1,4 × 10⁻⁵ |
| Répulsion SGTD, sans ancrage | 0,9686 | 0,0020 |
| Laplacien + ancrage | 0,0387 | 0,0338 |
| Répulsion SGTD + ancrage | 0,0388 | 0,0338 |

![Figure 1 — Erreur à la vérité et désaccord](fig1_consensus.png)

Sans ancrage, le réseau converge parfaitement vers une **fausse** valeur : désaccord nul, erreur 0,97. C'est la chambre d'écho, et la répulsion ne la corrige pas (même RMSE, à 10⁻⁵ près), comme le prédit la Proposition 1. Avec ancrage, l'erreur tombe à 0,039 ; ajouter la répulsion n'y change rien de mesurable. Le balayage $\theta \in \{0{,}5;\,0{,}7;\,0{,}9;\,0{,}95;\,0{,}99\}$ donne une RMSE de 0,0409 à 0,0388, sans divergence. À $\theta = 0{,}5$, environ 31 liens sur 113 sont en mode répulsif en régime établi. La répulsion n'est pas nuisible dans ce cadre, elle est **inerte**.

### 4.2 E2 : partition

Deux grappes de 15 agents reliées par deux ponts. La grappe A a 5 capteurs ; la grappe B n'en a aucun et démarre avec un biais de norme 1,5. Les ponts sont coupés à $t = 30$ ; seuil $\varepsilon = 10^{-3}$.

| | $\lambda_2$ final | RMSE de B à $t=100$ | $t=200$ | $t=300$ | $t=399$ |
|---|---|---|---|---|---|
| Sans réécriture | 0 | — | — | — | 1,291 (figée) |
| Avec réécriture (1 lien à $t=30$) | 0,083 | 1,098 | 0,869 | 0,690 | 0,548 |

![Figure 2 — λ₂ et erreur de la grappe sans capteur](fig2_partition.png)

Une fois isolée, la grappe sans capteur reste figée sur son erreur (1,30 à la coupure, 1,29 à la fin). La surveillance de $\lambda_2$ détecte la partition au pas même de la coupure. Un seul lien longue portée suffit à rétablir la convergence, mais lentement, parce que $\lambda_2$ reste faible (0,083). Le nombre de liens à ajouter est un paramètre de conception à étudier.

### 4.3 E3 : détection d'hallucination

12 agents honnêtes, dont 5 avec capteur, autour de $x^\star$. $m$ colludants têtus sont placés autour d'un faux état situé à distance 3. Seuils : $\tau = \tau_a = 0{,}6$. 30 tirages par case. Pour $m = 0$, le taux mesure les **faux positifs** ; pour $m > 0$, la **détection**. La Proposition 2 ($\beta_0 - 1 = $ composantes sans ancre) a été vérifiée par assertion sur l'ensemble des tirages.

| Dispersion honnête | $m$ | $\beta_2$ littéral | $\beta_2$ clique | $\tilde\beta_0$ (cône) |
|---|---|---|---|---|
| 0,05 | 0 | **1,00** (FP) | 0,00 | **0,00** |
| 0,05 | 1 à 5 | 1,00 | 0,00 | **1,00** |
| 0,12 | 0 | **1,00** (FP) | 0,00 | **0,00** |
| 0,12 | 1 à 5 | 1,00 | 0,00 à 0,03 | **1,00** |

![Figure 3 — Taux d'alerte des trois invariants](fig3_detection.png)

Pour la dispersion 0,05, la valeur médiane de $\beta_2$ littéral sur le consensus honnête est de **161**. La Proposition 3 donne exactement $\binom{11}{3} - \binom{4}{3} = 165 - 4 = 161$ (12 agents en clique, 5 capteurs). Le $\beta_2$ littéral sonne donc en permanence, que les colludants soient présents ou non. Le $\beta_2$ clique ne sonne presque jamais. Seul $\tilde\beta_0$ sépare les deux situations.

*Réserve.* Ce scénario est facile : le faux état est loin. Un faux état situé à moins de $\tau$ de la vérité est indétectable par construction. Un colludant en accord avec un agent ancré échappe aussi au test.

### 4.4 E4 : arbitrage

Huit nœuds infonuagiques ($c = 100$, sans capteur) partagent un biais de norme 1. Un nœud faible honnête ($c = 0{,}01$) a un capteur vérifié, $\sigma = 0{,}05$. Un nœud faible byzantin ($c = 0{,}01$) déclare la même information mais propose un faux état. Paramètres : $\alpha = \lambda = \delta = 1$, $c_0 = 0{,}1$.

| Schéma | Objectif borné ? | $\lVert x^\ast - x^\star\rVert$ |
|---|---|---|
| Uniforme | oui | 0,494 |
| Pondéré par la capacité | oui | 1,000 (= suivre l'infonuagique) |
| **SGTD tel qu'écrit (signe −)** | **non** ($\sum\pi = -8\times10^4$) | pas de minimum |
| Signe + non borné, information déclarée | oui | **1,533** (pire que l'infonuagique) |
| **Proposé : borné, information vérifiée** | oui | **0,132** |
| Variance inverse vérifiée ($\delta = 0$) | oui | 0,124 |
| *Référence : nœud faible seul* | — | 0,133 |

![Figure 4 — Erreur d'arbitrage selon la capacité du nœud faible](fig4_arbitrage.png)

Le balayage $c \in [10^{-4}, 10]$ confirme que le signe moins n'a jamais de minimum, que le signe plus non borné reste capturé par le byzantin, et que la forme proposée reste proche de l'optimum de variance inverse.

## 5. Discussion

**Ce qui tient.**
- La surveillance de $\lambda_2$ contre la partition.
- Le principe d'**ancrage matériel**. Il n'est pas seulement utile, il est **nécessaire** (Proposition 1) : aucun mécanisme entre pairs ne corrige une erreur partagée.
- L'objectif de **protéger le nœud faible**.

**Ce qui ne tient pas.**
- La répulsion des mises à jour corrélées (inerte).
- $\beta_2$ comme détecteur (100 % de faux positifs ou aveugle selon la variante).
- La fonction de coût telle qu'écrite (sans effet en lecture additive, non bornée en lecture multiplicative).
- Les chiffres de performance non étayés.

**La reformulation.** L'invariant topologique utile est le $\tilde\beta_0$ du complexe conifié : « toute composante d'accord doit toucher la vérité matérielle ». La protection du nœud faible s'obtient en pondérant par l'information **vérifiée**. Il en découle un principe d'architecture simple : **l'influence d'un nœud doit être indépendante de sa taille et proportionnelle à l'information auditable qu'il apporte** (Proposition 6). Un NPU de 2 W muni d'un capteur vérifié doit peser plus qu'un grand modèle infonuagique sans accès à la mesure. Ce n'est pas un choix moral, c'est l'optimum statistique.

Ce résultat rejoint une littérature existante. Le rôle de l'homologie relative dans les réseaux de capteurs a été établi par de Silva et Ghrist (2007), pour la couverture plutôt que pour le consensus. Notre construction en cône en est une application directe au problème de l'ancrage.

## 6. Limites

- Simulations synthétiques, petits $N$ (≤ 30), bruit gaussien, états vectoriels plutôt que sémantiques.
- Les ancres sont supposées honnêtes. L'usurpation d'un capteur, qui rend $\tilde I_k$ faux, n'est pas traitée.
- La réécriture suppose la connaissance des composantes.
- Aucune évaluation de latence ni du Merkle-DAG.
- La notion d'« accord » par seuil de distance est une simplification.
- Les Propositions 1 à 6 sont élémentaires. Leur intérêt est de trancher entre des choix de conception, pas d'être des théorèmes nouveaux.

## 7. Reproductibilité

```
python simulation_simplexe.py
```
Sorties : `resultats.json`, `fig1_consensus.png` à `fig4_arbitrage.png`. Graine fixe 20261020, numpy 2.3.5, scipy non requis. Durée : 4,5 s sur un Intel Core Ultra 7 258V.

## 8. Divulgation de l'usage de l'IA et provenance

- **Proposition SGTD initiale** (§2) : texte produit par le modèle Qwen2.5-Plus (Alibaba) le 20 octobre 2026, au cours d'un dialogue dirigé par l'auteur.
- **Erreur de signe** de la fonction de coût : identifiée par Claude (Anthropic) dans un dialogue séparé.
- **Analyse formelle, code de simulation et rédaction de ce brouillon** : réalisés avec un agent IA (environnement Antigravity) sous la direction de l'auteur. Tous les chiffres proviennent de l'exécution du script.
- L'auteur assume la responsabilité du contenu. Les modèles ne sont pas des auteurs.

## Références

- Boyd, S., Ghosh, A., Prabhakar, B., Shah, D. (2006). Randomized gossip algorithms. *IEEE Trans. Information Theory*, 52(6).
- de Silva, V., Ghrist, R. (2007). Coverage in sensor networks via persistent homology. *Algebraic & Geometric Topology*, 7.
- Douceur, J. R. (2002). The Sybil attack. *IPTPS 2002*.
- Edelsbrunner, H., Harer, J. (2010). *Computational Topology: An Introduction*. AMS.
- Fiedler, M. (1973). Algebraic connectivity of graphs. *Czechoslovak Mathematical Journal*, 23.
- Hatcher, A. (2002). *Algebraic Topology*. Cambridge University Press.
- Kay, S. M. (1993). *Fundamentals of Statistical Signal Processing: Estimation Theory*. Prentice Hall.
- Lamport, L., Shostak, R., Pease, M. (1982). The Byzantine generals problem. *ACM TOPLAS*, 4(3).
- Olfati-Saber, R., Murray, R. M. (2004). Consensus problems in networks of agents with switching topology and time-delays. *IEEE Trans. Automatic Control*, 49(9).
- Watts, D. J., Strogatz, S. H. (1998). Collective dynamics of "small-world" networks. *Nature*, 393.
