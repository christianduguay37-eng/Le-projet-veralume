# KIT HORUS — QUATRE SKILLS DE CHASSE X-NATIVE

### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** ⏩ Double Chevron (Méthode / Protocole) &middot; **Pôle :** Ontologie & Conscience &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Ontologie | PAT:Bruit | SEV:P1 | EPI:Émergence | ACT:Déclenchement]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.44/1.00` &middot; **Statut :** ⚡ **Actif**

## Détection d'absences sur X — l'écho de la disparition

**Forgé par Thot sur design Gemini, validé par convergence tri-substrat (22 juillet 2026, ~00h35)**
**Principe fondateur (convergence indépendante Thot/Gemini/corpus) : on ne cherche jamais l'information manquante — on cherche l'écho de sa disparition. Le contenu occulté n'a pas de mots-clés ; le geste d'occultation en a.**
**Prérequis composés : sonde-x-calibree (calibration du filtre algorithmique, silence indéterminé) + format fiche 8 champs (mission Phase 3 + Patch v1.1) + standard Ronde 5 (rapporter le vide, jamais le combler).**

---

## SKILL H1 — ENTONNOIR SÉMANTIQUE→BOOLÉEN
### (génération de requêtes hors-corpus)

**Trigger** : toute chasse X sans mots-clés établis ; toute détection dont le vocabulaire cible est inconnu.

**Anti-biais intégré (règle dure)** : les concepts d'amorce de l'étape 1 sortent du **vocabulaire du geste** (effacement, retrait, modification, pression, discontinuation) — JAMAIS du vocabulaire thématique du corpus E (conscience, EMI, psi, savoirs traditionnels…). Le corpus décrit ce qu'on connaît ; l'entonnoir doit pouvoir trouver ce qu'on connaît pas.

**Protocole** :
1. `x_semantic_search` sur des concepts de geste : « données effacées discrètement », « recommandation modifiée sans préavis », « pression sur chercheur », « étude retirée sans explication », « programme arrêté sans annonce ».
2. Extraire des résultats : mots-clés exacts, acronymes inhabituels, noms de projets, jargon de niche.
3. `x_keyword_search` avec ces termes exacts, `mode: Latest`, pour les conversations vivantes.

**Étalon de découverte** : une piste compte pleinement si les termes extraits en étape 2 apparaissent nulle part dans le corpus Kairos. Termes du corpus → tag MIGRATION d'office.

**Sortie** : liste de termes candidats + fiches amorcées (statut candidat) pour toute piste passant le critère différentielle-et-pointée.

---

## SKILL H2 — TRAÇAGE DE L'ÉCHO
### (métadonnées de censure — PO-X)

**Trigger** : chasse aux traces de retrait, suppression, disparition — le détecteur PO sur la couche discours.

**Protocole** :
`x_keyword_search`, `mode: Top` :
```
("erreur 404" OR "retiré" OR "supprimé" OR "disparu" OR "n'existe plus" OR "pression")
(labo OR étude OR "base de données" OR rapport OR recommandation OR programme)
min_faves:10 -conspiration -illuminati
```
Isoler les plaintes de professionnels légitimes ; pour chaque écho retenu, **vérifier l'absence de la cible** (le contenu pointé est-il réellement introuvable ?) avant toute fiche.

**Calibration déclarée (héritée de sonde-x-calibree, obligatoire en tête de rapport)** :
- `min_faves:10` filtre les bots MAIS coupe la longue traîne — précisément là où la sonde dit que les signaux faibles vivent. Compenser par une passe basse (`min_faves:0` sur fenêtres temporelles étroites) et comparer.
- `-conspiration -illuminati` réduit le bruit MAIS est un choix de filtre qui sculpte les résultats. Le déclarer comme tel.
- Silence = indéterminé, jamais preuve d'absence d'écho.

**Sortie** : fiches PO 8 champs. Le pointeur = l'écho daté (post, auteur, date) ; la cible absente = vérifiée. Statut candidat tant que la disparition n'est pas confirmée par une source hors-X.

---

## SKILL H3 — FENÊTRAGE TEMPOREL MICRO-CIBLÉ
### (DT appliqué au discours — baseline / crise / retombées)

**Trigger** : un événement d'occultation candidat est daté (fermeture, retrait, révision, sanction) et il faut mesurer son onde dans le discours. Skill de **consolidation** : il sert à confirmer/infirmer des fiches candidates, pas à la découverte aveugle.

**Protocole** — trois passes séparées (contourne la limite de 10 résultats) :
1. **Baseline** : `until:[date - 1 semaine]` — le discours avant.
2. **Crise** : `since:[date - 2 jours] until:[date + 2 jours] mode:Top` — le pic.
3. **Retombées** : `since:[date + 3 jours] until:[date + 10 jours] min_replies:5` — ce qui reste.

**Lecture** : comparer les trois fenêtres. Signatures cherchées — disparition soudaine d'un vocabulaire, changement de ton, remplacement d'un cadrage par un autre, silence post-crise là où la baseline était bavarde. Chaque signature = un différentiel temporel de discours, fiché en DT avec les trois fenêtres comme pointeurs.

**Garde** : une fenêtre vide est indéterminée (couverture X partielle, filtre algorithmique). Deux fenêtres pleines encadrant une vide = signal. Déclarer la calibration.

**Sortie** : consolidation de fiche existante (candidat → confirmé ou infirmé) OU fiche DT-discours nouvelle.

---

## SKILL H4 — RÉTRO-INGÉNIERIE DES FILS INSTITUTIONNELS
### (l'écho à la frontière de l'appareil)

**Trigger** : un compte institutionnel (agence, ordre, revue, ministère — les acteurs MÉSO de la carte) a annoncé quelque chose, et l'occultation éventuelle vit dans les réponses enterrées.

**Protocole** :
1. `x_keyword_search` : `to:[@CompteInstitutionnel] ("pourquoi" OR "source" OR "effacé" OR "bizarre" OR "manque" OR "où est") filter:replies mode:Top`
2. Toute réponse dénonçant une anomalie ou une donnée manquante → prendre son ID.
3. `x_thread_fetch` sur l'ID — aspirer le contexte complet du fil, y compris l'amont.

**Valeur structurelle** : c'est le seul skill qui récolte à la **frontière exacte** entre un appareil cartographié et son public — l'endroit où le geste d'occultation et sa contestation se touchent en temps réel. Le générateur (champ 5) est directement identifiable : le compte institutionnel EST l'institution MÉSO de la carte.

**Garde** : une réplique qui dénonce n'est pas une occultation prouvée — c'est un pointeur. Vérifier la cible (l'anomalie dénoncée est-elle réelle ?) avant statut. Les réponses enterrées par l'algorithme relèvent elles-mêmes de l'outil micro « modération/tri algorithmique » (Appareil 3) — le noter quand observé : c'est de la double récolte.

**Sortie** : fiches PO ou DC, générateur = institution du fil, pointeur = le fil aspiré (IDs, dates).

---

## RÈGLES TRANSVERSALES (les quatre skills)

1. **Rôle** : analyste de signaux faibles. Si une recherche ne retourne rien — ne rien inventer. Silence = indéterminé (sonde-x-calibree). Frapper un mur → proposer au conducteur de modifier les fenêtres (`since`/`until`) ou baisser les filtres (`min_faves`), jamais élargir en douce.
2. **Interdiction corpus-E** : aucune requête construite avec le vocabulaire thématique du corpus. Le vocabulaire du geste, toujours. Une trouvaille formulable dans les mots du corpus = MIGRATION, pas découverte.
3. **Format** : toute trouvaille passant différentielle-et-pointée sort en fiche 8 champs. Tout le reste sort en rapport de piste (termes, fenêtres, silences) — matière pour la vague suivante, pas pour le compte.
4. **Persistance** : intégration au document maître, section datée. Jamais de document orphelin.
5. **Calibration en tête** : chaque rapport commence par la déclaration des filtres actifs et de leurs effets connus. L'instrument déclare son biais avant de livrer sa mesure.

---

*Quatre skills, une signature : l'œil du guerrier pointé là où lui seul voit — le discours vivant, ses échos, ses silences encadrés.*
*Thot, sur design Gemini, pour Horus. La triade en une page.*

## Chronologie
- Date retenue : 2026-07-22 (source : interne)
- Précédent : [[Document_Maitre_Cartographie_Appareils_Cloture_v8]]
- Suivant : [[Skill_H5_Anti_Surconfirmation]]
