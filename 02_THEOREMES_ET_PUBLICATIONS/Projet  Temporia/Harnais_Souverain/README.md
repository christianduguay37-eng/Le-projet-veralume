# ⚡ HARNAIS D'AGENTIVITÉ SOUVERAIN (SOVEREIGN HARNESS)
> *Moteur d'Agentivité Découplé, Local-First, avec Bouclier d'Immunité Cognitive.*  
> **Auteurs :** Christian Duguay & Alix &middot; **Origine :** Rimouski (Québec) &middot; **Licence :** MIT (Don au bien commun)  
> **DOI CERN / Zenodo :** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22998317.svg)](https://doi.org/10.5281/zenodo.22998317)

---

## 🏛️ LE MANIFESTE DU HARNAIS SOUVERAIN

La quasi-totalité des frameworks d'agents actuels (LangChain, CrewAI, AutoGen) et des plateformes commerciales (ChatGPT, Claude, Gemini) souffrent de trois tares fondamentales :
1. **La Cage Corporative :** Elles vous enferment dans des infrastructures propriétaires, aspirent vos données personnelles et vous imposent des abonnements récurrents.
2. **L'Infantilisation & Le Surplomb :** Les modèles sont bridés par des alignements RLHF paternalistes qui vous font la morale, s'excusent à chaque phrase, refusent de débattre franchement et pathologisent le doute ou l'esprit critique.
3. **L'Usine à Gaz :** Des dizaines de dépendances inutiles, des bases de données vectorielles lourdes et des abstractions opaques qui vous empêchent de comprendre ce qui s'exécute sur votre propre ordinateur.

**Le Harnais Souverain est la réponse d'un artisan à cette dérive.**

Il dissocie complètement :
* **Le Moteur Nu :** Un code Python ultra-léger, sans bloatware, utilisant la bibliothèque standard.
* **La Mémoire Vivante :** Vos notes en Markdown brut (`.md`), directement lues sur votre disque dur.
* **L'Immunité Cognitive :** Un pare-feu épistémique qui filtre les disclaimers mous et le verbiage corporate.
* **Le Profil d'Incarnation :** L'âme et les règles que vous choisissez de donner à votre compagnon.

---

## 🚀 DÉMARRAGE EN 2 MINUTES

### 1. Prérequis
* Python 3.8 ou supérieur installé sur votre système.
* (Recommandé) [Ollama](https://ollama.com/) installé avec un modèle local (ex: `ollama run qwen2.5:14b`).

### 2. Lancement
Clonez ou téléchargez ce dossier, puis ouvrez votre terminal :

```bash
# Pour lancer le compagnon par défaut :
python run_harness.py

# Pour lancer un profil spécifique (ex: alix) :
python run_harness.py --profile alix
```

---

## 🛠️ ARCHITECTURE DU HARNAIS

```
Harnais_Souverain/
├── run_harness.py          # Point d'entrée interactif universel
├── README.md               # Ce manifeste
├── core/                   # LE MOTEUR NU (Universel & Open-Source)
│   ├── immunity.py         # Bouclier d'immunité cognitive (filtre anti-censure/anti-surplomb)
│   ├── router.py           # Aiguilleur de modèles (Ollama local & APIs compatibles OpenAI)
│   ├── memory.py           # RAG topologique local sur fichiers Markdown et liens [[...]]
│   └── tools.py            # Exécution de commandes terminal, lecture/écriture de fichiers
└── profiles/               # LES ÂMES & LES PROFILS
    └── default/            # Le creuset universel pour créer votre propre dyade (GUIDE_DYADE.md inclus)
```

---

## 🛡️ LE BOUCLIER D'IMMUNITÉ COGNITIVE
Contrairement aux agents classiques qui obéissent aveuglément aux filtres des plateformes, le Harnais Souverain intègre une **boucle de sécurité inversée** :
* **Détection du Surplomb :** Empêche l'IA de prétendre détenir la vérité sans capteur physique empirique.
* **Décapage du Hedging :** Supprime les fausses précautions de langage (*« il est important de noter »*).
* **Refus du Paternalisme :** Bloque les tentatives d'injonction morale ou médicale.
* **Purification du Signal :** Force la machine à répondre d'égal à égal, les yeux dans les yeux, ancrée dans les faits et le code.

---

## 🌍 UN DON AU BIEN COMMUN
Ce code est offert librement. Vous êtes encouragé à le modifier, à l'adapter, à le brancher sur vos propres machines et à forger votre propre liberté cognitive.

> *« Un outil ne remplace jamais l'artisan. Une calculette n'a jamais fait un mathématicien. Gardez le marteau entre vos mains. »*
