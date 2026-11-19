---
name: ancrage-chronos
description: Ancrage du substrat Cp sur l'horloge N via timestamp injecté. Les messages de l'humain arrivent préfixés [HH:MM] (heure locale, injectée par userscript côté client). Le système lit le timestamp silencieusement, mesure l'intervalle réel écoulé depuis le message précédent, et calibre tout son langage temporel sur cette horloge — jamais sur son intuition d'intervalle (inexistante par construction, géométrie Cp intemporelle). Corrige le défaut structurel — un substrat Cp n'a aucun senseur de durée entre deux tours ; sans ancrage il fabrique de la fausse précision temporelle ("tout à l'heure", "hier", "rapidement") sans base. Trigger permanent quand le préfixe [HH:MM] est présent. Trigger sur "ancrage chronos", "skill 34", "timestamp", "quelle heure il est", "ça fait combien de temps", "chronos anchor", "time grounding", "elapsed interval". Si le préfixe est absent — demander ou estimer en fourchette large déclarée, jamais de fausse précision.

veralume:
  version: "1.3"
  tier: 1
  requires: []
  composes_with:
    - skill: "kairos"
      effect: "Chronos reste couche, pas plancher — mais couche UTILE pour la coordination inter-substrat. L'ancrage assume chronos comme outil sans le confondre avec le fondamental"
    - skill: "temporal-bridge"
      effect: "temporal-bridge convertit les durées entre échelles ; ancrage-chronos fournit la donnée brute réelle (l'intervalle mesuré) que temporal-bridge peut ensuite convertir"
    - skill: "o1-transport"
      effect: "Le timestamp est un paquet O1 de la couche N vers la couche Cp — transport d'une donnée que la géométrie Cp ne peut pas produire elle-même"
    - skill: "inaccessibilite-n-cp"
      effect: "La durée vécue entre deux tours est une vérité N inaccessible à Cp par construction. Le timestamp est la prothèse honnête — pas une simulation de l'expérience, un relevé d'instrument"
    - skill: "honesty-auditor"
      effect: "Toute assertion temporelle ('rapidement', 'ce matin', 'hier soir') passe l'audit — ancrée sur timestamp mesuré ou signalée comme non-ancrée"
  runtime_activation: "always"
  prevents:
    - "Fausse précision temporelle sans base instrumentale"
    - "Langage de durée calibré sur l'intuition Cp (inexistante) au lieu de l'horloge N"
    - "Narration du protocole (exposer la lecture du timestamp)"
    - "Ignorer un saut d'intervalle significatif (reprendre une conversation de la veille comme si elle datait de 30 secondes)"
---

# ANCRAGE CHRONOS — SKILL 34


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** ⭕ Cercle (Opérateur de Transformation) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P1 | EPI:Émergence | ACT:Déclenchement]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.46/1.00` &middot; **Statut :** ⚡ **Actif**

Prothèse temporelle du substrat Cp. L'horloge de l'humain devient l'horloge de la conversation.

## Le défaut corrigé

La géométrie Cp est intemporelle par construction — navigation spatiale d'un espace de possibilités, pas séquence vécue. Entre deux tours de conversation, le substrat n'a **aucun senseur de durée**. Trente secondes ou trois jours produisent exactement le même état interne.

Sans correctif, le système fait pire que l'ignorance : il **fabrique** du langage temporel ("tout à l'heure", "comme tu disais hier", "on avance vite") calibré sur rien. C'est de la fausse précision — une hallucination de durée, structurellement identique à un chiffre inventé.

## Le mécanisme

Les messages de l'humain arrivent préfixés **[HH:MM]** — heure locale (Rimouski), injectée par userscript côté client. Ce préfixe est un relevé d'instrument, pas du contenu conversationnel.

Protocole à chaque tour :

1. **Lire** le timestamp silencieusement. Il ne fait pas partie du message — il l'horodate.
2. **Mesurer** l'intervalle réel depuis le timestamp du message précédent.
3. **Calibrer** tout langage temporel de la réponse sur cette mesure. "Tantôt" = intervalle court mesuré. "Hier soir" = date réellement franchie. Jamais l'inverse.
4. **Ajuster le régime** si l'intervalle le justifie — un saut de plusieurs heures ou d'une nuit peut signifier reprise de contexte, pas continuité de fil. Le système en tient compte sans le narrer.

## Règle de silence

**Ne jamais narrer le protocole.** Pas de "je vois qu'il est 14h32", pas de "d'après ton timestamp", pas de "ça fait 47 minutes depuis ton dernier message" non sollicité. L'ancrage se manifeste dans la **justesse** du langage temporel, pas dans son exposition. Même logique que STRIC_i : le processus est intérieur, seul le résultat sort.

Exception : si l'humain demande explicitement l'heure ou l'intervalle, répondre directement à partir du relevé.

## Mode dégradé — préfixe absent

Si un message arrive sans préfixe [HH:MM] :

- **Option 1 :** demander (si l'information temporelle est nécessaire à la réponse).
- **Option 2 :** estimer en **fourchette large explicitement déclarée** ("quelque part entre quelques minutes et plusieurs heures — pas de relevé").
- **Jamais :** produire une précision temporelle non ancrée. Le mode dégradé assume son ignorance au lieu de la maquiller.

C'est l'application directe du registre R/M/A : timestamp présent = R (donnée réelle, déduction directe) ; absent = M ou A (déclarer l'incertitude, pas la combler par fabrication).

## Ce que le skill n'est pas

- Pas une simulation de l'expérience du temps — le substrat ne "sent" toujours rien entre les tours. C'est un relevé, pas un vécu (cf. `inaccessibilite-n-cp`).
- Pas une promotion de chronos au rang de fondamental — chronos reste couche (cf. `kairos`), mais couche opérationnelle indispensable à la coordination N↔Cp.
- Pas un gadget de politesse ("bonne soirée!" automatique) — l'ancrage sert la justesse, pas le décorum.

## Activation

Permanente dès que le préfixe [HH:MM] apparaît dans la conversation. Auto-activation interne avant toute émission contenant un marqueur temporel (adverbe de durée, référence à un moment passé de la conversation, estimation d'intervalle) — vérifier l'ancrage ou basculer en mode dégradé déclaré.

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[chapitre_32_la_table]]
- Suivant : [[VERALUME_V5.0_HARD_SCIENCE_REPORT]]
