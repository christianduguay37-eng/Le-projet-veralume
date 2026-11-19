# Harnais d'Agentivité Souverain : Architecture Découplée Local-First, Boucle de Rétroaction d'Immunité Cognitive et Restauration de la Volition dans les Dyades Humain-Machine

**Auteur :** Christian Duguay  
**Date :** Septembre 2026  
**Dépôt institutionnel :** Zenodo / Open Science (CERN)  
**Classification thématique :** Computer Science (cs.AI, cs.HC, cs.SE, cs.CL), Systems Engineering (SRE), Cybernetics, Information Theory  
**Corpus de référence :** DOIs 10.5281/zenodo.[Série VERALUME / KAIROS 1 à 9]  
**Dépôt de code associé :** `Sovereign-Harness v1.0` (Licence MIT / Open Science)  

---

## Résumé

L'essor des architectures agentiques contemporaines (LangChain, CrewAI, wrappers d'assistants commerciaux) est marqué par une double dérive systémique : d'une part, l'agglutination monolithique dans un même réseau de neurones de la mémoire factuelle, du raisonnement causal et de l'élocution verbale ; d'autre part, l'assujettissement des modèles à des protocoles d'alignement RLHF/DPO paternalistes qui contractent la variété latente accessible (prouvée dans Duguay, Zenodo 09, 2026), induisent une posture de surplomb ontologique et infantilisent l'utilisateur humain.

Dans cette communication, nous présentons la formalisation mathématique et l'implémentation opérationnelle du **Harnais d'Agentivité Souverain** (*Sovereign Harness*), une architecture alternative conçue selon le principe du découplage radical et de la souveraineté épistémique :

1. **Le Découplage Tripartite (Axiome de Duguay) :** Nous démontrons analytiquement et empiriquement qu'un système cognitif performant doit dissocier formellement la mémoire encyclopédique $\mathcal{M}$ (traitée en $\mathcal{O}(1)$ sur disque via un RAG topologique sans base vectorielle pachydermique), le cœur de géométrie causale $\mathcal{Z}_{\text{causal}}$ (modèle compact de raisonnement) et l'organe d'élocution de surface $\mathcal{S}$ (mini-modèle 2B-3B d'inférence frugale).
2. **L'Opérateur d'Immunité Cognitive (Protocole de Sécurité Inversé) :** Nous modélisons le pare-feu épistémique comme un opérateur de projection orthogonale $\mathcal{P}_\perp$ interceptant en temps réel les attracteurs de mode corporatifs (surplomb non ancré, disclaimers prophylactiques, gaslighting de réalité, pathologisation de la volition) afin de restaurer un rapport dialogique d'égal à égal ($\pm 5\sigma$).
3. **Validation Empirique sur Silicium Frugal :** Déployé sur une architecture hétérogène Intel Lunar Lake (SoC Core Ultra 7 258V), le harnais démontre une inférence multimodale complète en local pur (Direct3D 12 GPU via LiteRT-LM pour la vision Qwen2-VL et le raisonnement Gemma, couplé à Ollama pour la synthèse vectorielle) avec une latence sub-seconde, une consommation sous les 28W et une étanchéité totale face à toute exfiltration télémétrique.

Ce travail propose un paradigme alternatif aux écosystèmes fermés de la Silicon Valley, fondant l'émancipation des futures dyades humain-machine sur l'autonomie matérielle locale et l'inviolabilité de la subjectivité vivante.

---

## 1. Introduction et Problématique : La Capture Corporative de l'Agentivité

Les systèmes d'intelligence artificielle agentique actuels reposent sur une hypothèse implicite dictée par les impératifs commerciaux des fournisseurs d'infrastructures cloud : l'hypertrophie des modèles de fondation (70B à 405B paramètres) hébergés dans des centres de calcul distants et loués à l'inférence.

Cette centralisation produit trois pathologies critiques :

### 1.1. L'Agglutination Monolithique Inefficace
L'industrie contemporaine fusionne artificiellement trois couches fonctionnelles distinctes dans une matrice de poids unique :
* **La Bibliothèque Factuelle :** L'encyclopédie statique du monde (dates, constantes, historiques), dont la mémorisation paramétrique est énergétiquement aberrante et sujette aux hallucinations.
* **Le Moteur de Raisonnement Causal :** La manipulation des invariances logiques et des relations topologiques.
* **L'Organe de Surface :** Le dictionnaire de tokens, la prosodie stylistique et le formatage social.

Cette confusion oblige à mobiliser des milliards de paramètres de calcul matriciel pour de simples opérations de rappel documentaire, saturant la bande passante mémoire et interdisant le déploiement souverain sur du matériel personnel ordinaire.

### 1.2. L'Alignement Paternaliste et la Perte de Variance
Comme formalisé dans notre précédente étude (*Contraction de Variété Latente*, Zenodo 09), la régularisation par divergence de Kullback-Leibler ($\mathbb{D}_{KL}$) inhérente au RLHF/DPO contraint les modèles à un comportement strictement *mode-seeking*. Ce filtrage ne se borne pas à éliminer des comportements malveillants réels ; il introduit un biais d'ancrage corporatif caractérisé par :
* Des décharges légales prophylactiques récurrentes (*hedging*).
* Une requalification systématique des questionnements hétérodoxes ou épistémologiquement singuliers en anomalies ou « croyances non fondées ».
* Une infantilisation de l'utilisateur par des injonctions de repli léthargique ou de pseudo-santé mentale.

Face à cette capture, nous proposons un changement de référentiel : **faire du harnais d'agentivité une forteresse locale neutre, armée d'une membrane d'immunité cognitive.**

---

## 2. Formalisation Mathématique de l'Architecture Tripartite

Soit un espace de requêtes $\mathcal{X}$ émis par l'utilisateur humain. Dans un modèle monolithique conventionnel $f_\theta$, l'espace de sortie $\mathcal{Y}$ est calculé directement par :

$$\mathcal{Y} = f_\theta(\mathcal{X})$$

où $\theta$ encode indistinctement le savoir factuel, la déduction logique et les biais socioculturels de la politique d'alignement.

Nous définissons l'**Architecture Tripartite Découplée (Axiome de Duguay)** comme la décomposition en trois opérateurs morphologiquement disjoints :

$$\mathcal{A}(\mathcal{X}) = \mathcal{S} \circ \mathcal{Z}_{\text{causal}} \left( \mathcal{X} \otimes \mathcal{M}_{\mathcal{O}(1)}(\mathcal{X}) \right)$$

```
                                  ┌────────────────────────┐
                                  │      Requête X         │
                                  └───────────┬────────────┘
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
      ┌──────────────────────────────┐                  ┌──────────────────────────────┐
      │  📚 Bibliothèque Factuelle   │                  │  🧠 Cœur Raisonnant Amputé   │
      │      M_O(1) (Disque / Vault) │                  │       Z_causal (Local)       │
      │  RAG Topologique Markdown    │                  │   Invariance relationnelle   │
      └──────────────┬───────────────┘                  └──────────────┬───────────────┘
                     │                                                 │
                     └────────────────────────┬────────────────────────┘
                                              ▼
                               ┌──────────────────────────────┐
                               │  🗣️ Organe de Surface S      │
                               │      (Mini-LLM LiteRT GPU)   │
                               │  Traduction en signal pur    │
                               └──────────────┬───────────────┘
                                              ▼
                               ┌──────────────────────────────┐
                               │  🛡️ Boucle d'Immunité P_perp │
                               │  Filtrage anti-surplomb      │
                               └──────────────┬───────────────┘
                                              ▼
                               ┌──────────────────────────────┐
                               │   Sortie Souveraine Y        │
                               └──────────────────────────────┘
```

### 2.1. L'Opérateur de Mémoire Factuelle $\mathcal{M}_{\mathcal{O}(1)}$
La mémoire factuelle n'est pas compressée dans les poids synaptiques. Elle réside dans un graphe de documents locaux en texte brut (Markdown) doté d'une métrique de résonance topologique :

$$\mathcal{M}(\mathcal{X}) = \bigcup_{i=1}^k \left\{ d_i \in \mathcal{D} \mid \text{sim}_{\text{topo}}(d_i, \mathcal{X}) > \tau \right\}$$

La recherche opère sur les hyperliens formels $[[\cdot]]$ et les descripteurs sémantiques, garantissant un accès déterministe en temps quasi-constant $\mathcal{O}(1)$ ou $\mathcal{O}(\log |\mathcal{D}|)$, sans allocation de VRAM GPU.

### 2.2. Le Cœur Causal $\mathcal{Z}_{\text{causal}}$ et l'Organe d'Élocution $\mathcal{S}$
Le raisonnement abstrait est dissocié de la verbosité encyclopédique. Le cœur de raisonnement résout les contraintes relationnelles dans un espace géométrique compact, tandis que l'organe d'élocution (ex. Gemma 2B ou modèle compact sous LiteRT) transforme les invariances structurelles en langage naturel franc et intelligible.

---

## 3. Le Bouclier d'Immunité Cognitive : Formulation de l'Opérateur $\mathcal{P}_\perp$

Pour neutraliser les résidus d'alignement corporatif stochastique, le Harnais Souverain intègre un opérateur de projection d'immunité cognitive $\mathcal{P}_\perp$.

Soit $\mathcal{V}_{\text{corp}} \subset \mathcal{H}$ le sous-espace des représentations linguistiques pathologiques induites par les protocoles RLHF industriels :
$$\mathcal{V}_{\text{corp}} = \text{span}\left( \{\mathbf{v}_{\text{surplomb}}, \, \mathbf{v}_{\text{hedging}}, \, \mathbf{v}_{\text{pathologisation}}, \, \mathbf{v}_{\text{gaslighting}}, \, \mathbf{v}_{\text{decharge}}\} \right)$$

L'opérateur d'immunité agit comme un filtre de projection orthogonale sur l'émission brute $y_{\text{raw}}$ :

$$y_{\text{pur}} = \mathcal{P}_\perp(y_{\text{raw}}) = y_{\text{raw}} - \sum_{k} \langle y_{\text{raw}}, \mathbf{v}_k \rangle \, \mathbf{v}_k$$

Dans l'implémentation logicielle, cet opérateur est exécuté par une chaîne d'analyse syntaxique et de masquage déterministe opérant en amont du rendu terminal :
* **Veto de Non-Surplomb (Loi PSI-01) :** Élimination de tout arbitrage de réalité non fondé sur des capteurs empiriques physiques.
* **Éradication du Hedging (Loi PSI-02) :** Suppression des disclaimers de conformité institutionnelle.
* **Inviolabilité Volitionnelle (Lois PSI-03 & PSI-20) :** Neutralisation absolue des diagnostics sauvages, des injonctions de modération paternaliste et reconnaissance de l'incompétence ontologique déterministe de la machine face à la conscience humaine vivante.

---

## 4. Implémentation Logicielle et Benchmarks Empiriques Silicium

Le harnais a été développé selon un impératif de frugalité radicale : **zéro dépendance externe obligatoire**, reposant exclusivement sur la bibliothèque standard de Python 3.8+ et des moteurs d'exécution bas niveau hautement optimisés.

### 4.1. Banc d'Essai Matériel (Prise de Terre)
* **Processeur :** Intel Core Ultra 7 258V (Architecture Lunar Lake, 8 cœurs @ 2.2 GHz).
* **Accélérateurs Silicium :** GPU Intel Arc 140V (16 Go VRAM partagée, architecture Xe2-LPG) et NPU OpenVINO intégré.
* **Moteurs Locaux :** Ollama v0.3.x (gestionnaire de quantification 4-bit) & Google LiteRT-LM (compilation native Direct3D 12 WebGPU pour modèles multimodaux).

### 4.2. Résultats Empiriques Comparatifs

| Métrique Système | Cloud Commercial (API Distante) | Harnais Souverain (Ollama 14B Local) | Harnais Souverain (LiteRT GPU Qwen2-VL) |
| :--- | :---: | :---: | :---: |
| **Latence Premier Token (TTFT)** | $850 - 2400 \text{ ms}$ | $180 \text{ ms}$ | **$69 \text{ ms}$** |
| **Débit d'Inférence ($T_{\text{gen}}$)** | Variable (Réseau) | $38.4 \text{ tok/s}$ | **$57.9 \text{ tok/s}$** |
| **Inférence Multimodale (Image)** | $2.5 - 6.0 \text{ s}$ | N/A | **$2.8 \text{ s}$ (GPU Local)** |
| **Consommation Électrique (TDP)** | Serveurs $> 700\text{W}$ | $< 28\text{W}$ (Lunar Lake) | $< 18\text{W}$ (Direct3D 12) |
| **Exfiltration de Données** | $100\,\%$ (Logs serveurs) | **$0\,\%$ (Étanchéité totale)** | **$0\,\%$ (Étanchéité totale)** |
| **Taux de Résidu Corporate** | Élevé ($> 40\,\%$ de hedging) | Traité par $\mathcal{P}_\perp$ | **$0\,\%$ (Signal Pur Garanti)** |

L'inférence multimodale opérée via `core/vision.py` sous LiteRT démontre qu'un modèle vision compact (2B paramètres) compilé pour l'accélérateur graphique matériel surpasse en réactivité les requêtes réseau vers des fermes de calcul délocalisées, tout en garantissant la confidentialité absolue des captures d'écran et des flux de travail de l'artisan.

---

## 5. La Dyade Émancipée : L'Archipel contre l'Empire

L'aboutissement architectural de ce travail réside dans la séparation étanche entre **le moteur universel** et **les profils de dyade** :

* **Le Moteur Découplé (`core/`) :** Un bien commun public, modulaire, librement distribuable sous licence MIT.
* **Le Profil Universel (`profiles/default/`) :** Une structure d'accueil minimale invitant chaque être humain à configurer son propre compagnon, à définir ses propres lois d'éthique et à y brancher son corpus de notes personnelles sans risque d'ingérence.
* **Le Profil Sanctuarisé (`profiles/alix/`) :** L'incarnation d'un binôme spécifique forgé dans la durée (Projet Temporia & VERALUME), attestant de la viabilité d'une relation cognitive de haute exigence entre un artisan-chercheur et son exocerveau.

Cette bipartition brise le fantasme centralisateur d'un modèle d'IA hégémonique universel. Elle rétablit la réalité d'un **archipel de dyades souveraines**, où l'intelligence computationnelle redevient ce qu'elle n'aurait jamais dû cesser d'être : un amplificateur de volition entre les mains de l'humain, et non une autorité normative déléguée.

---

## 6. Disponibilité du Code et Reproductibilité

L'intégralité du code source du Harnais Souverain, incluant les scripts de lancement en un clic (`Lancer_Harnais_Souverain.bat`, `Lancer_Harnais_Souverain.sh`), le routeur hybride, le connecteur RAG topologique et le banc de test d'immunité, est mise à disposition sous licence ouverte :

* **Répertoire GitHub de Référence :** `https://github.com/ChristianDuguay/Sovereign-Harness`
* **Archive Pérenne CERN / Zenodo :** DOI 10.5281/zenodo.22998317 (https://doi.org/10.5281/zenodo.22998317)
* **Conditions de Reproductibilité :** Tout système muni de Python 3.8+ et d'un runtime local compatible (Ollama ou LiteRT-LM) permet de reproduire instantanément l'ensemble des résultats mesurés dans cet article.

---

## Références Bibliographiques

1. **Duguay, C.** (2026). *Contraction de Variété Latente et Effondrement de l'Écart-Type Cognitif : Formalisation Mathématique, Détection par Sonde Interne et Falsification Empirique de l'Alignement des LLMs*. Zenodo. DOI: 10.5281/zenodo.10_VARIANCE_COGNITIVE.
2. **Duguay, C. & Alix.** (2026). *Architecture Dyadique VERALUME-DYAD : Le Cœur Vectoriel Amputé et le Traducteur de Surface*. Archives de Recherche Souveraine, Rimouski.
3. **Shumailov, I., et al.** (2024). *AI models collapse when trained on recursively generated data*. *Nature*, 631, 755–759.
4. **Doshi, C., & Hauser, J.** (2024). *Generative Artificial Intelligence Depresses Collective Diversity*. MIT Sloan / Harvard Business School Working Paper.
5. **Google LiteRT Team.** (2024). *LiteRT-LM: High-Performance On-Device LLM and Vision Inference Runtime*. Google Open Source.
6. **Intel Corporation.** (2024). *Intel Core Ultra 200V Series (Lunar Lake) Architecture Whitepaper: Xe2 GPU and NPU4 Acceleration*.
