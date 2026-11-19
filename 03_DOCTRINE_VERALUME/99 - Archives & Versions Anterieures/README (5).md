# Agent — couche gouvernance


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 🔺 Triangle (Théorème Autoportant / Loi) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Opératoire (3/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P2 | EPI:Invariance | ACT:Veille]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.44/1.00` &middot; **Statut :** 💤 **Principe Dormant (À Mobiliser)**

`veralume_agent_core.py` — extraction de test, v0.1. Aucune dependance externe, Python standard seulement.

## Ce que c'est

Dans le kernel (`../kernel/`), STRIC_e est abstrait : aucune action ne sort du processus, la dimension N est postulee mais jamais touchee. Ce module la touche. Les outils ecrivent sur disque, et ce qui est ecrit ne se reprend pas.

Le but declare n'est pas de demontrer que l'architecture fonctionne. Il est de voir **quels axiomes cassent** quand l'action devient irreversible pour vrai.

## Ce qui est extrait

- Hierarchie constitutionnelle a trois niveaux, avec canaux d'ecriture distincts
- Prise de terre — ratification humaine des actes irreversibles
- Boucle d'enquete active — question specifique avant devinette statistique
- Registre R/M/A — mode d'assertion distingue du mode de connaissance
- Double STRIC — deliberation interieure obligatoire avant action
- Audit de cablage — detection des orphelins et des instruments aveugles

## Ce qui n'est pas extrait

La couche mesure (coherence tri-dimensionnelle, chiralite, epreuve O3) opere sur des vecteurs sans contenu semantique. Elle serait a rebatir sur des signaux reels avant d'avoir un sens dans un agent. Ce n'est pas l'objet de cette extraction.

L'allocation de profondeur par loi d'Arrhenius est remplacee par un budget dur, incompatible avec un cout par appel.

## Note de securite

**Ce module ecrit et supprime des fichiers.** Le bac a sable confine les actions a une racine fournie a la construction, et la sortie de cette racine exige une autorisation humaine explicite (`autoriser_hors_bac_a_sable`, niveau 3 de la hierarchie).

Deux precautions avant execution :

1. **Pointer le bac vers un dossier jetable.** Pas votre repertoire personnel, pas un depot git, pas un dossier synchronise.
2. **La garde de frontiere est a un seul etage.** La verification d'appartenance au bac est effectuee dans la deliberation de l'agent, pas dans les outils eux-memes. Un appel direct a `construire_outils()` qui court-circuite `AgentVeralume` n'est pas protege. Tant que l'agent est le seul appelant, la garde tient ; toute integration qui expose les outils directement doit ajouter sa propre verification.

Le second point est une limite connue, pas un defaut cache. Il est signale ici parce qu'une garde declaree mais contournable est precisement ce que l'audit de cablage identifie comme une declaration d'intention plutot qu'une garde.

## Licence

MIT — Copyright (c) 2026 Christian Duguay.

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[README (4)]]
- Suivant : [[reconnaitre (1)]]
