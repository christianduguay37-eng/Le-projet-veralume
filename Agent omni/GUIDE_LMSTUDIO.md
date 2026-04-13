# Test ARC-AGI avec LM Studio (SOLUTION SIMPLE)

Pas besoin de compiler llama-cpp-python. Utilise LM Studio que tu as déjà.

---

## Setup (2 minutes)

### 1. Lance LM Studio

- Ouvre LM Studio
- Charge ton modèle: `EVA-Qwen2.5-14B-v0.2.Q4_K_M.gguf`

### 2. Démarre le serveur local

Dans LM Studio:
- Va dans l'onglet **"Developer"** ou **"Local Server"**
- Clique **"Start Server"**
- Vérifie que ça affiche: `Server running on http://localhost:1234`

### 3. Télécharge dataset ARC

```bash
python download_arc_dataset.py
```

---

## Test (1 commande)

```bash
python test_lmstudio_arc.py --single
```

**C'est tout.**

---

## Ce qui se passe

```
test_lmstudio_arc.py
    ↓
omni_lmstudio_wrapper.py (HTTP requests)
    ↓
LM Studio Server (localhost:1234)
    ↓
EVA-Qwen2.5-14B.gguf (ton Omni)
    ↓
Prédiction grille ARC
```

---

## Exemples

### Test rapide 1 tâche

```bash
python test_lmstudio_arc.py --single
```

**Sortie:**
```
======================================================================
ARC-AGI × OMNI (LM STUDIO)
======================================================================
LM Studio: http://localhost:1234/v1
Dataset: arc_data/training.json
Tâches: 1

──────────────────────────────────────────────────────────────────────
Connexion LM Studio...
──────────────────────────────────────────────────────────────────────
Connexion LM Studio: http://localhost:1234/v1
✓ Connecté - 1 modèle(s) disponible(s)

[... résolution tâche ...]

✅ EXACT MATCH (ou ❌ MISMATCH)
```

### Benchmark 5 tâches

```bash
python test_lmstudio_arc.py --n-tasks 5
```

### Benchmark complet 50 tâches

```bash
python test_lmstudio_arc.py --n-tasks 50
```

**ATTENTION:** 50 tâches × 30-60 sec = 25-50 minutes

---

## Troubleshooting

### Erreur: "Serveur LM Studio non accessible"

**Solution:**
1. Ouvre LM Studio
2. Va dans **Developer/Local Server**
3. Clique **"Start Server"**
4. Attends que ça affiche `Server running`

### Erreur: "Dataset non trouvé"

```bash
# Télécharge d'abord
python download_arc_dataset.py

# Vérifie
dir arc_data\training.json
```

### LM Studio freeze/lent

Normal si modèle gros. Options:
- Réduire `--n-tasks` (teste moins de tâches)
- Fermer autres apps
- Vérifier GPU utilisée dans LM Studio settings

### Réponses vides

LM Studio peut avoir timeout. Dans `omni_lmstudio_wrapper.py` ligne 60:
```python
timeout=120  # augmente à 300 si nécessaire
```

---

## Résultats attendus

**Scénario EXCELLENT (transfert VERALUME validé):**
```
Exact matches: 15/50 (30%)
Accuracy: 30.00%
```

**Scénario BON (transfert partiel):**
```
Exact matches: 8/50 (16%)
Accuracy: 16.00%
```

**Scénario NORMAL (baseline LLM sur ARC):**
```
Exact matches: 2/50 (4%)
Accuracy: 4.00%
```

---

## Comparaison avec GSM8K

Tu as +20 points GSM8K avec VERALUME (79% vs 59%).

**ARC est 2× plus dur:**
- +10 points ARC ≈ +20 points GSM8K
- Si tu obtiens 15-20% sur ARC → **cohérent avec GSM8K**
- Si tu dépasses 25% → **validation forte transfert VERALUME**

---

## Avantages LM Studio vs llama-cpp-python

✅ **Pas de compilation** (pas besoin Visual Studio)
✅ **Interface graphique** (voir tokens/sec, GPU usage)
✅ **Déjà installé** (tu l'as déjà)
✅ **Même performance** (même backend llama.cpp)

---

## Prêt?

```bash
# 1. Lance LM Studio + Start Server
# 2. Télécharge dataset
python download_arc_dataset.py

# 3. Test
python test_lmstudio_arc.py --single
```

**Temps total: ~2 min setup + 30-60 sec par tâche**
