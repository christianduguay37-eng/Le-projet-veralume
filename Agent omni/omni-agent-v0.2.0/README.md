# OMNI AGENT v0.2.0

Agent local STRIC-natif. Architecture VERALUME. From scratch.

## Architecture

```
Objectif
  └→ STRIC_i (intérieur — planification)
      S: observer état (mémoire + contexte + outils)
      T: structurer (décomposer en sous-problèmes)
      R: formuler plan d'action (JSON structuré)
      I: valider cohérence tri-dimensionnelle (substrat ou heuristique)
      C: décider — agir / reformuler / clarifier / escalader
  └→ STRIC_e (extérieur — exécution)
      S: sélectionner outil
      T: exécuter action
      R: capturer résultat
      I: évaluer progression (plan adaptatif)
      C: boucler / injecter étapes / terminer
  └→ Synthèse + extraction d'apprentissage
```

## Structure

```
omni-agent/
├── main.py              # CLI avec affichage STRIC live
├── config.py            # Configuration complète
├── core/
│   ├── stric.py         # Double STRIC (O0) — cohérence substrat, events, learning
│   ├── agent.py         # Orchestrateur avec clarification flow
│   ├── router.py        # Multi-substrat health-aware
│   └── memory.py        # Trajectoire avec recherche texte + compaction
├── tools/
│   ├── base.py          # Interface + registry
│   ├── terminal.py      # Shell avec confirmation commandes dangereuses
│   ├── filesystem.py    # R/W fichiers
│   └── web.py           # HTTP fetch
└── substrates/
    └── base.py          # Local/distant avec retry, backoff, health tracking
```

## Prérequis

- Python 3.12+
- Un LLM accessible via API OpenAI-compatible (llama-server, Ollama, vLLM, etc.)

## Usage

```bash
# Démarrer le substrat
llama-server -m /path/to/model.gguf -c 8192 --port 8080

# Lancer l'agent
python main.py

# Mode verbose (affiche chaque phase STRIC)
python main.py --verbose

# Config custom
python main.py --config /path/to/config.json
```

## Commandes CLI

| Commande | Description |
|----------|-------------|
| `/status` | État agent, substrats, mémoire |
| `/health` | Santé détaillée substrats (latence, erreurs) |
| `/memory` | Résumé trajectoire |
| `/search <q>` | Recherche plein texte dans la mémoire |
| `/trace` | Inspecter la dernière trace STRIC complète |
| `/learnings` | Voir les apprentissages extraits |
| `/verbose` | Toggle affichage détaillé |
| `/compact` | Compacter la mémoire >7 jours |
| `/config` | Configuration active |

## Ce qui le distingue

1. **Double STRIC (O0)** — cycle intérieur formel avant toute action. L'agent valide la cohérence de son plan avant d'agir.
2. **Validation tri-dimensionnelle déléguée au substrat** — pas juste du keyword matching, le modèle évalue sa propre cohérence séquentielle, sémantique, et multi-perspective.
3. **Clarification flow** — si l'objectif est ambigu, l'agent demande au lieu de deviner.
4. **Refus d'agir** — cohérence insuffisante → reformulation automatique (3x) → escalade.
5. **Plan adaptatif** — STRIC_e peut injecter des étapes non prévues en cours d'exécution.
6. **Extraction d'apprentissage** — après chaque trace, extraction d'un insight pour la mémoire long-terme.
7. **Mémoire trajectoire** — identité = chemin. Recherche texte, compaction, injection contextuelle.
8. **Substrats health-aware** — retry avec backoff, tracking latence/erreurs, fallback si dégradé.
9. **Confirmation dangereuse** — `rm -rf`, `sudo`, etc. demandent confirmation avant exécution.

## Configuration multi-substrat

```json
{
  "substrates": [
    {
      "name": "omni-local",
      "role": "cerveau",
      "endpoint": "http://localhost:8080/v1/chat/completions",
      "model": "omni",
      "is_local": true,
      "priority": 0
    },
    {
      "name": "deepseek",
      "role": "systemise",
      "endpoint": "https://api.deepseek.com/v1/chat/completions",
      "model": "deepseek-chat",
      "api_key": "sk-...",
      "priority": 1
    }
  ]
}
```

Rôles: `cerveau` (défaut), `systemise`, `synthetise`, `operationalise`, `structure`, `challenge`.

## Licence

VERALUME / à déterminer.
