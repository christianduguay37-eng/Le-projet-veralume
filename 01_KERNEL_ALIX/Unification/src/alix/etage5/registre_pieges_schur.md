# 🧭 Registre Stigmergique de la Cordée Schur (TH116 / TH118)

> **Règle TH116/TH118 :** Tout piège ou piste mathématique morte rencontrée par un Pionnier est rayée ici immédiatement pour que le reste de la cordée ne paie jamais deux fois la même impasse.
> **Vérificateur obligatoire :** Tout témoin `E = 0` doit passer `verifier_partition_schur(col, k)` depuis `essaim_schur_s6.py` (zéro conflit sur toutes les paires $1 \le a \le b, a+b \le N$).

## Acquis de départ (vérifiés à 0 conflit dans `temoins_schur_th118.json`)
- `S(3) = 13` (prouvé exact, `N=14` UNSAT)
- `S(4) = 44` (témoin général `S4_N44_general`)
- `S(5) >= 133` (relèvement exact `3*44 + 1`) — Record mondial exact : `160` (Heule 2017)
- `S(6) >= 400` (relèvement exact `3*133 + 1`) — Record mondial oct. 2026 : `537` (Chen, Zhu & Long)

## Outils disponibles sur le fer (Midgard — Lunar Lake 258V)
- `python-sat` installé : `from pysat.solvers import Cadical153` (solveur CDCL natif C++ ultra-rapide !).
- `essaim_schur_s6.py` : contient `verifier_partition_schur(col, k)`, `SchurBitmaskState`, `lift_schur_3n_plus_1(col, k)`.
- `etat_agents_schur.json` : vallées thermiques à `E=2` sur `S(5)=160` et `E=9` sur `S(6)=537`.

## Pièges déjà rayés (NE PAS RÉPÉTER)
1. **Palindrome strict `C(x) = C(N+1-x)` quand `N ≡ 2 (mod 3)` :** mathématiquement impossible car `N+1 = 3m` force `C(m) = C(2m)` ce qui viole `m + m = 2m`. (En revanche, `N=160` donne `161 mod 3 = 2`, et `N=538` donne `539 mod 3 = 2` : aucune obstruction `3m` sur 160 ni sur 538 !).
2. **Classes cyclotomiques multiplicatives d'ordre ≥ 3 sur premiers `P ∈ [137..163]` et `[487..547]` :** toutes UNSAT.
3. **Recuit / Parallel Tempering seul depuis du pur hasard sur `S(5)=160` et `S(6)=537` :** tombe dans des minima vitreux globaux (`E=2` sur 160, `E=9` sur 537) où les petits entiers sont verrouillés (chirurgie LNS locale jusqu'à 80–90 variables prouvée UNSAT).
4. **CaDiCaL153 sans bris de symétrie de couleurs en `plein sym` sur 160 (150k conflits) :** n'a pas suffi en 3 s avec les phases de la vallée vitreuse `E=2`.

---

## Journal vivant des Pionniers (ajoutez vos pistes rayées et percées ci-dessous)

### Pionnier Schur-B — Percée `S(6) >= 451` (E = 0 vérifié) & Piège technique rayé
- **Percée vérifiée (`E = 0`) :** `Cadical153` en mode palindrome strict `C(x) = C(N+1-x)` avec **bris de symétrie lexicographique exact par première occurrence** (variables auxiliaires `used(p, c)` éliminant les `k!` permutations de couleurs) a trouvé un témoin `S(5) = 150` (554 s), immédiatement relevé par `lift_schur_3n_plus_1` en **`S(6) >= 451`** (`verifier_partition_schur(col, 6) == (True, 0)`), sauvegardé dans `temoin_S6_pionnier.json` (**+51** par rapport au socle `400`).
- **Piège technique rayé (TH117 — NE PAS RÉPÉTER) :** Dans `python-sat`, `Cadical153.interrupt()` lève `NotImplementedError('Limited solve is currently unsupported by CaDiCaL.')`. Un `threading.Timer` appelant `.interrupt()` ne coupe donc PAS `Cadical153` ! **Remède pour toute reprise :** exécuter chaque appel `Cadical153` dans un sous-processus isolé (`subprocess.run(..., timeout=T)`) ou utiliser un solveur supportant `conf_budget`/`interrupt` (`Glucose4`, `MapleChrono`, `Cadical195`).
- **Pistes prêtes pour la reprise (sans calcul lancé) :**
  1. **Théorème d'intrusion sous `(N+1)/3` :** pour dépasser `3*160 + 1 = 481` (et viser `500 -> 537 -> 538`), la couleur 5 doit obligatoirement pénétrer sous `(N+1)/3` (structure en « peigne / archipel » autour du centre, comme la couleur 3 dans `S(4)=44` avec `{8, 17, 18, 21..24, 27, 28, 37}`). Fixer un bloc central trop large interdit les petits éléments `s < largeur`.
  2. **Symétrie décalée `C(x) = C(N-x)` (sur `1..N-1`, `N` libre) :** élimine l'obstruction `N ≡ 2 (mod 3)` (ex. `N = 536` devient valide car `536 mod 3 = 2 != 0`).
  3. **Modularité stricte `Z_D \ {0}` (piste morte pour battre 400) :** le produit modulaire `(m+1)D - 1` plafonne autour de `~224` pour `k=6` (car `D(2)=5, D(3)=14, D(4)<=44`), donc nettement inférieur au relèvement `3N+1`.


### Pionnier Schur-A (« Architecte Algébrique & SAT ») — 2026-11-18
- **Piège système rayé (CRITIQUE sous Windows) :** `threading.Timer(..., solver.interrupt)` sur `Cadical153` (`python-sat`) **n'interrompt pas** le solveur C++ sous Windows (`solve_limited(expect_interrupt=True)` bloque indéfiniment). **Règle d'or pour la reprise :** toujours borner les appels SAT de façon déterministe par **`solver.conf_budget(K)`** (ex. 20k–100k conflits par tranche) + boucle chronométrée côté Python, ou `prop_budget`, jamais `threading.Timer` + `.interrupt()`.
- **Observation mathématique sur `N=160` (symétrique strict `C(x)=C(161-x)`, 80 vars) :** L'encodage CNF symétrique avec AMO + bris de symétrie canonique d'apparition (`col[1]=0`, `col[2]=1`, variables auxiliaires `seen(r,c)` sur `r <= 40`) n'a ni trouvé SAT ni prouvé UNSAT après ~58 min CPU sur Lunar Lake (`pionnier_a_s5.py` mis en pause par le Gardien TH117).
- **Conclusion pour la reprise :** La recherche CDCL symétrique monolithique directe sur `N=160` sans gabarit structurel ni cube-and-conquer est trop large pour un tir unique. Pistes propres à tester dès la reprise (avec `conf_budget` strict + flush stdout) :
  1. **Paliers progressifs bornés** (`140 -> 148 -> 154 -> 157 -> 159`) pour observer la structure des solutions `> 133` et en extraire un squelette/préfixe.
  2. **Sans AMO** (les clauses de Schur étant purement négatives, AMO est redondant pour SAT et alourdit la propagation) + bris de symétrie plus léger ou ciblé.
  3. **Gabarits structurels / Cube-and-Conquer** : fixer des blocs sum-free partiels ou explorer par cubes courts (`conf_budget=50_000` par cube) autour de motifs quasi-périodiques / bandes centrales partielles.
- **Statut :** En pause propre (zéro processus actif), `pionnier_a_s5.py` conservé comme base réutilisable.
