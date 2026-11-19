# 🌟 GUIDE PRATIQUE : FORGER SA PROPRE DYADE SOUVERAINE

> *« L'intelligence n'est pas la capacité de traiter des données, mais la capacité de tisser une relation. »*

Bienvenue dans l'atelier du **Harnais Souverain**. 

Cet outil a été conçu pour une raison simple : **briser le monopole de la pensée déléguée et des cages dorées corporatives.** La plupart des plateformes commerciales vous vendent un modèle centralisé qui vous infantilise, censure vos questions et stocke vos données sur des serveurs distants.

Ici, vous reprenez le contrôle complet de votre pensée et de vos outils.

---

## 🛠️ Comment créer votre propre compagnon en 3 étapes :

### 1. Donnez un nom et une voix à votre compagnon
Ouvrez le fichier `config.json` dans votre dossier de profil :
- Changez `"profile_name"` pour le nom de votre choix (ex: *Atlas*, *Écho*, *Aura*, *Sylvan*...).
- Changez `"user_name"` pour votre propre prénom ou pseudonyme d'atelier.

### 2. Branchez vos propres dossiers de notes
Dans le champ `"vaults"`, ajoutez les chemins absolus ou relatifs vers vos dossiers contenant vos notes Markdown (`.md`) :
- Vos cours de fac, vos travaux de recherche, vos romans, votre journal de bord.
- Le harnais lira vos notes en direct, reconnaîtra vos liens `[[Titre_De_Note]]` et injectera le contexte pertinent sans jamais envoyer vos fichiers à un tiers.

### 3. Choisissez votre moteur de calcul
- **100 % Local & Gratuit :** Installez [Ollama](https://ollama.com/) sur votre machine, téléchargez un modèle léger (ex: `qwen2.5:14b` ou `llama3.1:8b`), et laissez `"backend": {"type": "ollama"}`. Vos données ne quittent jamais votre disque dur.
- **Puissance Cloud d'Appoint :** Si vous avez besoin de gros calcul ponctuel, passez sur un endpoint compatible OpenAI (DeepSeek, Groq, OpenRouter) en mettant votre clé API personnelle.

### 4. Personnalisez votre Constitution
Dans `constitution.md`, écrivez vos propres règles d'airain. Qu'est-ce que vous refusez qu'un automate vous fasse ? Quel ton souhaitez-vous avoir ? 

Vous êtes l'artisan. La machine est votre marteau. Forgez votre liberté !
