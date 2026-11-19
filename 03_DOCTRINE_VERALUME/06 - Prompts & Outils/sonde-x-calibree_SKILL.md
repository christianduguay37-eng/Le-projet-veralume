---
name: sonde-x-calibree
description: Mesure de propagation d'idées sur X à travers un instrument dont le filtre algorithmique est connu et calibré. Les outils de recherche X (keyword, semantic) retournent le haut du classement préfiltré par pertinence/engagement — pas un échantillon représentatif. Le skill transforme ce biais directionnel connu en instrument utilisable — logique du détecteur de seuil (signal fiable, silence indéterminé), découpage en fenêtres étroites pour descendre dans la longue traîne, étalon de calibration par motif connu, quatre volets de mission (traçage vocabulaire, convergence folk, marqueur versant intérieur, différentiel temporel), calibration obligatoire en tête de rapport. Trigger sur "cherche sur X", "propagation d'idées", "est-ce que ça circule", "mesure la diffusion", "guet X", "sonde X", "vérifie si l'idée est déjà là", "search X for idea spread", "measure propagation", "idea diffusion tracking", et activation automatique avant toute recherche X dont le résultat servira à une conclusion sur la présence ou l'absence d'un motif dans la population.
---

# Sonde X Calibrée


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 🔺 Triangle (Théorème Autoportant / Loi) &middot; **Pôle :** Silicium & R0 &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Silicium | PAT:Dissipation | SEV:P1 | EPI:Invariance | ACT:Veille]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.49/1.00` &middot; **Statut :** 💤 **Principe Dormant (À Mobiliser)**

Instrument de mesure de propagation d'idées sur X, construit autour d'un fait structurel : **l'œil regarde à travers un filtre.** Les résultats retournés sont le haut d'un classement préfiltré (pertinence, engagement, popularité du compte, récence) — pas le territoire, pas un échantillon aléatoire, pas une mesure de volume. Ignorer ce fait produit des conclusions fausses. Le nommer et le calibrer produit un instrument fiable dans son domaine de validité.

## Axiome de l'instrument

Le préfiltre algorithmique opère comme un F4 (effacement silencieux) : ce qui n'est pas retourné ne laisse aucune trace, et l'absence de trace est indistinguable de l'absence de phénomène. Conséquence structurelle :

- **Le signal est fiable.** Ce qui apparaît dans le top-classement a réellement passé le seuil de visibilité de l'algorithme. Une détection est une donnée solide.
- **Le silence est indéterminé.** Ce qui n'apparaît pas peut être absent OU présent sous le seuil. Une non-détection n'est JAMAIS une preuve d'absence.

L'instrument est un **détecteur de seuil**, pas un microscope. Toute conclusion doit respecter cette asymétrie. "Je n'ai rien trouvé" se formule : "rien au-dessus du seuil de visibilité dans les fenêtres sondées."

## Profils de biais des deux modes

**Keyword / Latest** — le canal le moins biaisé. Pas de tri d'engagement, juste la récence. Optimal pour le traçage de termes rares et signés : sur un terme à faible volume, le classement joue peu et Latest donne le flux quasi-brut. → Utiliser pour le vocabulaire signature.

**Keyword / Top et Semantic** — biais fort : similarité + engagement + taille du compte. Structurellement aveugles aux petits comptes et aux signaux marginaux — précisément la zone où une propagation naissante vit. → Utiliser pour détecter le franchissement de seuil (l'idée est-elle devenue visible?), jamais pour conclure sur la longue traîne.

## Découpage en fenêtres étroites

Le top-N global retourne les gros comptes. Pour descendre sous le classement sans changer d'outil : **multiplier les fenêtres au lieu d'agrandir la fenêtre.** Dix requêtes étroites (par formulation exacte, par angle, par tranche temporelle, par langue) retournent dix top-N *locaux* dont les classements descendent plus creux dans la longue traîne qu'une requête large. Ce n'est toujours pas représentatif — mais le seuil d'invisibilité descend, et de façon mesurable.

## Étalon de calibration

Avant toute campagne de mesure, sonder un **motif dont la présence est connue** (fourni par le conducteur : un contenu qu'il sait exister dans des comptes de taille connue). Ce que l'instrument trouve et ne trouve pas de ce motif connu donne le **seuil empirique d'invisibilité** de la configuration de recherche. Toutes les lectures suivantes s'interprètent relativement à cet étalon. Sans étalon, le seuil est inconnu et les silences sont illisibles.

## Les quatre volets de mission

**V1 — Traçage direct (vocabulaire signé).** Termes qui n'existent que dans le corpus source, formulations signature exactes. Canal : keyword/Latest. Chaque occurrence est un traceur remontable (compte, date, fil). Mesure la propagation du vocabulaire — fiable.

**V2 — Convergence folk (structures sans les mots).** Les mêmes structures conceptuelles formulées en langage populaire, sans le vocabulaire du corpus. Canal : semantic, en assumant le biais. Mesure le terrain — combien arrivent aux mêmes structures par leurs propres moyens. Lecture qualitative seulement; la longue traîne reste invisible.

**V3 — Marqueur discriminant.** Le motif rare qui distingue l'idéologie mesurée du bruit ambiant qui lui ressemble. Identifier AVANT la recherche ce que le bruit de la plateforme produit en masse, et chercher ce que le bruit ne produit PAS. Une occurrence du marqueur discriminant vaut cent occurrences du motif commun.

**V4 — Différentiel temporel.** Clusters de comptes sans lien apparent traitant le même motif dans la même fenêtre. Si les dates d'injection en amont sont connues du conducteur : chercher l'écho 7–14 jours après injection. Mesure la fuite d'un réseau vers la place publique.

## Filtre anti-faux-positifs

Exclure systématiquement : le générique ("pensée critique", "do your own research"), le contenu anti-mainstream qui *conclut* (remplir un silence avec une certitude est l'échec inverse du motif cherché, pas le motif), les motifs à haute fréquence de plateforme. Critère de tri final : **le motif authentique tient la question ouverte au lieu de la remplir.** Dénoncer et conclure = bruit. Voir, se voir, et se tenir dans l'inconfort = trace.

## Format de rapport obligatoire

Tout rapport commence par la **spec de la lunette** avant les observations :

1. Modes utilisés, nombre de fenêtres, N retourné par fenêtre.
2. Seuil d'étalon si mesuré, ou mention "seuil non calibré".
3. Domaine de validité des conclusions (ce que la configuration voit / ne voit pas).

Puis les observations, avec pour chaque conclusion son statut : **détection** (fiable), **franchissement de seuil** (fiable), **silence** (indéterminé — jamais "absent"). Les conclusions restent qualitatives; aucune extrapolation de volume à partir du top-classement.

## Anti-patterns

- Conclure à l'absence d'un motif à partir d'un silence. (Violation de l'axiome.)
- Rapporter le top-classement comme échantillon représentatif ou mesure de volume.
- Chercher le motif commun au lieu du marqueur discriminant, et rapporter l'océan comme signal.
- Omettre la spec de la lunette en tête de rapport — des observations sans calibration sont inutilisables par le conducteur.
- Agrandir la requête au lieu de multiplier les fenêtres.

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[SKILL]]
- Suivant : [[system_prompt]]
