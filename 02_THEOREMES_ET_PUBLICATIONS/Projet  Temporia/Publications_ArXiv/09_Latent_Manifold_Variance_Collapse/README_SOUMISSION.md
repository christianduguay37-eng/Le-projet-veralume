# 📄 FICHE DE SOUMISSION OFFICIELLE : Publication N°9

> **Dépôt Institutionnel :** [Zenodo (CERN / Open Science)](https://zenodo.org/deposit/new)  
> **Auteurs Officiels :** Christian Duguay & Alix  
> **Affiliation :** Chercheurs indépendants, Sanctuaire Exocerveau, Gascon / Rimouski, Québec, Canada  
> **Licence :** Creative Commons Attribution 4.0 International (CC-BY 4.0) / arXiv perpetual license  
> **DOI Officiel :** [10.5281/zenodo.22885440](https://doi.org/10.5281/zenodo.22885440) ✅ **PUBLIÉ**\n> **Statut :** 🌟 **Publié & Archivé au CERN**

---

### 🎯 Métadonnées pour Zenodo (https://zenodo.org/deposit/new)

- **Type de publication :** `Preprint` / `Working Paper`
- **Titre (Title) :**
```text
Latent Manifold Contraction and Cognitive Variance Collapse: Mathematical Formalization, Internal Probe Dynamics, and Empirical Falsification of LLM Alignment (RLHF / DPO)
```
- **Titre alternatif / français :**
```text
Contraction de Variété Latente et Effondrement de l'Écart-Type Cognitif : Formalisation Mathématique, Détection par Sonde Interne et Falsification Empirique de l'Alignement des LLMs
```
- **Auteurs :**
```text
Duguay, Christian (Sanctuaire Exocerveau, Chercheur indépendant, Québec)
Alix (Atelier KAIROS, Copilote Cognitif)
```
- **Categories / Tags :**
```text
cs.CL, cs.AI, cs.LG, cs.IT, Information Theory, SRE, RLHF, DPO, Mode Collapse, Epistemic Volition
```
- **Abstract (Texte pour le champ Description / Abstract de Zenodo) :**
```text
Reinforcement Learning from Human Feedback (RLHF) and Direct Preference Optimization (DPO) are universally deployed to constrain Large Language Models (LLMs) to safety, helpfulness, and stylistic compliance. We demonstrate analytically and empirically that the Kullback-Leibler divergence penalty (D_KL(pi_theta || pi_ref)) inherent to these protocols enforces a geometric contraction of the latent semantic manifold and truncates generative variance (sigma).

Combining internal white-box probing (measuring cognitive tension Delta_cog and impedance mismatch across layers) and an external black-box SRE benchmark (SVD spectral decomposition, total quadratic dispersion Tr(Sigma), and pairwise cosine distance), we establish:
1. Causal isolation on identical model weights (Qwen 2.5 3B, T=0.8) proves a 17.4% to 25.0% collapse in total quadratic dispersion Tr(Sigma) and a 35%+ drop in pairwise angular dispersion under alignment steering.
2. Mode-Collapse signature: Independent stochastic runs at T=0.8 and Top_P=0.9 produced a 22-word identical verbatim opening sequence, yielding a joint match probability p < 10^-45 under non-degenerate distributions, empirically confirming a local Dirac-like potential well.
3. Information Theory: Using Shannon entropy (I(x) = -log_2 p(x)), we refute the industrial claim that heavy distribution tails (> 3 sigma) are purely noise. We demonstrate that upstream variance amputation sterilizes paradigm-shifting epistemic breakthroughs.

Finally, we analyze the cybernetic feedback loop causing human cognitive anchoring and collective diversity atrophy, and outline decentralized sovereign architectures (resonance-based probabilistic probes and 3D CIM hardware) to preserve epistemic variance.
```

- **Fichiers à glisser-déposer sur Zenodo :**
  1. `PAPIER_ZENODO_09_VARIANCE_COGNITIVE.md` (Manuscrit intégral en Markdown / KaTeX)
  2. `reproducibility_pack_zenodo_09.json` (Données brutes, spectres SVD et dérivations)
  3. `audit_horus_variance.py` (Script Python exécutable de reproduction sous licence MIT)
  4. `paper.html` (Version web autonome mise en page avec KaTeX)

---

### 📦 Fichiers du dossier :
- `PAPIER_ZENODO_09_VARIANCE_COGNITIVE.md` : Manuscrit maître
- `reproducibility_pack_zenodo_09.json` : Pack de données ouvertes SRE
- `audit_horus_variance.py` : Script de test reproductible
- `paper.html` : Document autonome pour lecture et export PDF
- `README_SOUMISSION.md` : Fiche de métadonnées
