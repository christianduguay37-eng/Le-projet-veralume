# L*↑ — Couche 2 en Lean 4 + Mathlib

Nombres réels et limites. Lean 4.15 + Mathlib v4.15.0. Aucune preuve n'utilise `sorry`.

La couche 2 de la v4.0 fixe des rôles (τ, ρ, α, η, κ, β, a*) mais pas des formes.
Chaque théorème ici fixe une forme explicite, écrite dans son énoncé : il est
vrai pour cette forme. Changer la forme, c'est un autre théorème à prouver.

| Théorème | Forme choisie | Résultat |
|---|---|---|
| `TH34` | investir coûte 1 de τ et ajoute 1 à ρ, seulement s'il reste du budget | réserve + budget restant = τ0, pour toute stratégie : aucune réserve gratuite |
| `TH50` | coût de régénération α·C | α < 1 ⇒ régénérer coûte moins que libérer |
| `TH61` | capture η·a, coût κ(a) = c·a² | productif **exactement** pour 0 < a < η/c |
| `TH61_optimum` | même forme | le meilleur dividende est en a = η/(2c), **au milieu** de la fenêtre. Le pari de la v2.4 (optimum à la frontière η·a = κ(a)) est faux pour cette forme : à la frontière, le dividende vaut 0 |
| `TH65` | modulation a ← a + β(a* − a) | 0 < β < 2 ⇒ la friction converge vers a* |
| `TH66_surdite` | β = 0 | la friction ne bouge plus |
| `TH66_oscillation` | β = 2 | oscillation perpétuelle (période 2) |
| `TH66_divergence` | β > 2 | l'écart à la consigne explose |
| `TH70` | échange qui réduit l'écart des budgets d'un facteur (1 − r) ; consignes gᵢ·τᵢ | architectures identiques ⇒ la friction s'éteint |
| `TH73` (et TH68) | même forme | architectures différentes ⇒ une friction > 0 survit à tout échange : le verrou intérieur |
| `TH81` | creux m ← ρ·γ·m + g | ρ·γ > 1 ⇒ les creux montent sans fin |
| `TH81_plafond` | même forme | ρ·γ < 1 ⇒ les creux plafonnent à g/(1 − ρ·γ), même avec une semence : la spirale cesse de monter |

Compiler (Lean et Mathlib installés par elan) :

```
lake exe cache get
lake build
```
