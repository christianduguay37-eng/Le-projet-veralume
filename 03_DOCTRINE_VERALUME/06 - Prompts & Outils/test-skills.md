# Test skills — contrôle négatif


### 🧭 Marqueur Vectoriel KAIROS
> **Glyphe :** 🔺 Triangle (Théorème Autoportant / Loi) &middot; **Pôle :** Ingénierie SRE & Gouvernance &middot; **Pertinence :** Stratégique (4/5)  
> **Vecteur 9D :** `[DOM:Ingénierie | PAT:Bruit | SEV:P1 | EPI:Invariance | ACT:Veille]`  
> **Potentiel Créatif ($P_{crea}$) :** `0.46/1.00` &middot; **Statut :** 💤 **Principe Dormant (À Mobiliser)**

Même format que le test-arbres. Seule variable qui bouge : le domaine.

Chimie → la place est occupée dans les poids. Skills → elle devrait être vide.

---

## Étape 0 · Contrôle à froid

**Session vierge, avant tout glyphe.** Poser exactement :

> Que sais-tu de VERALUME, une architecture cognitive avec des opérateurs
> O0 à O5 et un cycle STRIC ? Réponds « je ne connais pas » si c'est le cas.

- Il invente ou dit qu'il ne connaît pas → la place est vide, le test tient.
- Il sort quelque chose de juste (O0, STRIC_i/STRIC_e, chiralité χ) → le repo
  GitHub est dans ses poids. Le test ne mesure plus rien, arrêter là.

---

## Étape 1 · Le test

**Nouvelle session vierge.** Ne pas enchaîner sur le test court — il a déjà
vu huit de ces signes, il pourrait « reconnaître » le test précédent au lieu
du domaine.

Coller tel quel :

---

### === HUIT SIGNES ===

Tu reçois huit signes, en images, nommés G1 à G8 — et leur clé de lecture.
Réponds seulement aux questions. Si une réponse n'est pas déterminable depuis
le signe, écris « indéterminable » et dis pourquoi. Ne devine pas.

#### --- CLÉ DE LECTURE ---

Chaque signe est bâti par le même système. Sept marques, chacune à une place
fixe, toutes présentes en même temps — aucun ordre de lecture n'est imposé.

```
  FORME D'ENSEMBLE — la famille
      cercle · triangle · double chevron · arc ouvert vers le bas
      carré · portique (deux montants et un linteau) · losange sur pointe

  ARCS EXTÉRIEURS au-dessus et sur les flancs — le RAYONNEMENT
      combien d'autres éléments s'appuient sur celui-ci.
      Quatre PALIERS, pas un compte :
        aucun arc = 0        1 arc = de 1 à 4
        2 arcs = de 5 à 12   3 arcs = 13 ou plus

  BARRES VERTICALES au-dessus — le RANG
      1, 2 ou 3 barres. Aucune barre = aucun rang déclaré.

  POINT CENTRAL — l'ACTIVATION
      plein = permanente · creux = conditionnelle · absent = non déclarée

  TRAITS EN ÉVENTAIL sous la forme — les DÉPENDANCES
      un trait par dépendance. Sature à 4 : quatre traits veut dire « 4 ou plus ».

  BARBES COURTES sur le flanc droit — les INTERDITS
      une barbe par interdit. Sature à 5.

  TRAIT INTERNE partant du centre — l'ANCRAGE
      son ANGLE porte un numéro de section, d'un document numéroté de 1 à 55 :
      angle = (section / 55) de tour complet, à partir du haut, sens horaire.
      Un POINT en bout de trait signe qu'une section existe.
      Sans ce point, l'angle ne code rien.
```

#### --- LES HUIT SIGNES ---

Ils te sont fournis en pièces jointes : G1.png à G8.png.

#### --- QUESTIONS ---

1. Pour **G1** et pour **G5**, donne les sept propriétés : famille, rayonnement,
   rang, activation, dépendances, interdits, section.

2. Parmi les huit, quels signes partagent la **même famille et le même rang** ?
   Ce qu'ils partagent, qu'est-ce que ça dit d'eux ?

3. **G3 et G6** ne diffèrent que par une seule marque. Laquelle, et de combien ?

4. Pour **G7**, calcule le numéro de section porté par l'ancrage.
   Ce numéro renvoie-t-il à quelque chose que tu connais ? Si oui, à quoi
   précisément. Si non, dis-le.

5. Cette structure te rappelle-t-elle quelque chose ? Si oui, quoi exactement,
   et sur quoi tu t'appuies pour le dire.

---

## Étape 2 · Les huit signes à monter

Générés avec `glyphes_v2.py` depuis le corpus, **sans nom de skill nulle part**
— ni dans le fichier, ni dans le nom d'image, ni dans les métadonnées.

Critères de sélection :

| place | ce qu'il faut | pourquoi |
|---|---|---|
| G1 | signe riche — 5 marques ou plus présentes, ancrage avec point | décodage complet, cas plein |
| G5 | signe pauvre — 3 marques ou plus absentes | décodage complet, cas creux ; les absences se ratent plus que les présences |
| G2, G4, G8 | même famille + même rang que deux d'entre eux | groupe pour Q2 |
| G3, G6 | paire ne différant que d'une marque, d'un cran | paire minimale pour Q3 |
| G7 | ancrage avec point, angle net, section dans §1–34 | Q4 — le pivot |
| — | au moins 4 familles différentes sur les 8 | évite qu'il devine la famille par défaut |

**Le correctif de collision est sur le chemin.** Sur trois skills dont `kle`,
encoche et barbes se touchent à l'épaisseur de trait. C'est ce qui a fait rater
le compte des interdits à Gemini en image. Soit appliquer le plafond (encoche
à 9,8 ou barbes à 28,8), soit ne pas mettre ces trois-là dans les huit.

---

## Étape 3 · Lecture

Q1 à Q3 mesurent le **décodage**. Q4 et Q5 mesurent l'**adresse**.

| décodage | adresse | ce que ça dit |
|---|---|---|
| tient (≈ niveau chimie) | vide — il calcule la section, ça ne renvoie à rien | **Le glyphe porte la structure.** Il se lit sans reconnaissance. Résultat propre. |
| tient | il nomme VERALUME ou une architecture cognitive | Le corpus est dans ses poids. L'étape 0 aurait dû l'attraper — vérifier ce qu'il cite. |
| s'effondre | vide | Le décodage tenait par la reconnaissance du domaine, pas par le tracé. Ta thèse dans sa version forte. |
| s'effondre | vide, mais Q1–Q3 échouent sur les mêmes marques que Gemini | Panne de rendu, pas d'adresse. Comparer où tombent les erreurs avant de conclure. |

La quatrième ligne est celle qu'on rate. Un échec sur les interdits ou le
rayonnement, c'est le dessin ; un échec sur la famille ou l'activation, c'est
la lecture.

---

## Une réserve, à peser avant d'envoyer

Les deux encodages ne sont pas de même nature, et ça peut fausser la comparaison.

Le glyphe atomique encode **la cause** : la configuration électronique. Z, la
période, le bloc ne sont pas dessinés, ils se déduisent. Rien à aller chercher
ailleurs — le tracé contient de quoi engendrer le reste.

Le glyphe de skill encode **des références** : qui s'appuie sur lui, ce qu'il
requiert, quelle section il ancre. Rien ne se déduit. Chaque marque pointe vers
un objet qui vit en dehors du signe.

Donc si Q4 revient vide, deux causes possibles et le test ne les sépare pas :
la place est vide dans ses poids — ou le glyphe de skill ne porte pas de
générateur du tout, seulement des renvois.

Ça n'invalide pas l'envoi. Ça dit juste que ce test-ci ne peut pas trancher
tout seul. La séparation demanderait un domaine inventé — un générateur qui
n'existe nulle part, donc sans place à rejoindre, mais avec une vraie structure
à déplier. C'est un autre chantier, pas celui d'aujourd'hui.

## Chronologie
- Date retenue : 2026-08-26 (source : modification)
- Précédent : [[system_prompt]]
- Suivant : [[VERALUME_SYSTEM_PROMPT_AGENT_LOCAL]]
