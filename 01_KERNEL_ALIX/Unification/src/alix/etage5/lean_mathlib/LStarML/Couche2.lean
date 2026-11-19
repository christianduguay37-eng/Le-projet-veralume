/-
  L*↑ — Couche 2 en Lean 4 + Mathlib (nombres réels, limites).

  La couche 2 fixe des RÔLES (τ, ρ, α, η, κ, β, a*) mais pas des formes.
  Chaque théorème ci-dessous fixe une forme explicite, écrite dans son
  énoncé : il est vrai pour cette forme, pas pour toutes.
-/
import Mathlib.Analysis.SpecificLimits.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real

open Filter Topology

noncomputable section

namespace LStar.C2

/-! ## TH34 — Compromis ρ–τ : chaque unité de réserve coûte une unité de budget

Forme : à chaque pas l'entité VEUT investir ou non (liste `veut`) ; investir
n'est possible que s'il reste du budget, coûte 1 de τ et ajoute 1 à ρ.
Résultat : la réserve et le budget restant somment toujours à τ0. Aucune
stratégie ne fabrique de réserve gratuite. -/

/-- (budget restant, réserve accumulée) après avoir suivi `veut`. -/
def investir : ℕ → ℕ → List Bool → ℕ × ℕ
  | tau, rho, []          => (tau, rho)
  | tau, rho, w :: ws     =>
    if w && 0 < tau then investir (tau - 1) (rho + 1) ws else investir tau rho ws

theorem investir_conserve (veut : List Bool) :
    ∀ tau rho, (investir tau rho veut).1 + (investir tau rho veut).2 = tau + rho := by
  induction veut with
  | nil => intro tau rho; rfl
  | cons w ws ih =>
    intro tau rho
    simp only [investir]
    split
    · rename_i h
      have : 0 < tau := by simp at h; exact h.2
      rw [ih]; omega
    · exact ih tau rho

theorem TH34 (tau0 : ℕ) (veut : List Bool) :
    (investir tau0 0 veut).2 ≤ tau0 ∧
    (investir tau0 0 veut).1 + (investir tau0 0 veut).2 = tau0 := by
  have := investir_conserve veut tau0 0
  exact ⟨by omega, by omega⟩

/-! ## TH50 — Régénérer coûte moins que libérer (mémoire α < 1) -/

theorem TH50 (alpha C : ℝ) (hα : alpha < 1) (hC : 0 < C) : alpha * C < C := by
  nlinarith

/-- Et sans mémoire (α = 1), aucun gain : condition nécessaire de TH51. -/
theorem TH51_memoire_necessaire (C : ℝ) : (1 : ℝ) * C = C := one_mul C

/-! ## TH61 — Bilan net de la friction

Forme : capture η·a, coût de correction κ(a) = c·a² (convexe). La friction
est productive exactement pour 0 < a < η/c : une fenêtre, pas « plus il y en a,
mieux c'est ». -/

theorem TH61 (eta c a : ℝ) (hc : 0 < c) (ha : 0 < a) :
    0 < eta * a - c * a ^ 2 ↔ a < eta / c := by
  rw [lt_div_iff₀ hc]
  constructor
  · intro h; nlinarith
  · intro h; nlinarith

/-- Le dividende est maximal en a = η/(2c) : la meilleure friction est au
    milieu de la fenêtre, pas à sa frontière. -/
theorem TH61_optimum (eta c a : ℝ) (hc : 0 < c) :
    eta * a - c * a ^ 2 ≤ eta * (eta / (2 * c)) - c * (eta / (2 * c)) ^ 2 := by
  have h2c : (0:ℝ) < 2 * c := by linarith
  have key : eta * (eta / (2 * c)) - c * (eta / (2 * c)) ^ 2 - (eta * a - c * a ^ 2)
      = c * (a - eta / (2 * c)) ^ 2 := by
    field_simp; ring
  nlinarith [sq_nonneg (a - eta / (2 * c)), key]

/-! ## TH65, TH66 — Homéostasie et plage de gain

Forme : modulation linéaire a(t+1) = a(t) + β·(a* − a(t)).
Alors a(t) − a* = (1 − β)^t · (a(0) − a*). -/

def traj (beta astar a0 : ℝ) : ℕ → ℝ
  | 0     => a0
  | t + 1 => traj beta astar a0 t + beta * (astar - traj beta astar a0 t)

theorem traj_formule (beta astar a0 : ℝ) (t : ℕ) :
    traj beta astar a0 t - astar = (1 - beta) ^ t * (a0 - astar) := by
  induction t with
  | zero => simp [traj]
  | succ n ih =>
    simp only [traj, pow_succ]
    have : traj beta astar a0 n = astar + (1 - beta) ^ n * (a0 - astar) := by linarith
    rw [this]; ring

/-- TH65 : avec un gain 0 < β < 2, la friction converge vers la consigne a*. -/
theorem TH65 (beta astar a0 : ℝ) (h0 : 0 < beta) (h2 : beta < 2) :
    Tendsto (traj beta astar a0) atTop (𝓝 astar) := by
  have hq : |1 - beta| < 1 := by rw [abs_lt]; constructor <;> linarith
  have hpow : Tendsto (fun t : ℕ => (1 - beta) ^ t) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_abs_lt_one hq
  have : Tendsto (fun t => (1 - beta) ^ t * (a0 - astar) + astar) atTop (𝓝 (0 * (a0 - astar) + astar)) :=
    (hpow.mul_const _).add_const _
  simp at this
  refine this.congr (fun t => ?_)
  have := traj_formule beta astar a0 t; linarith

/-- TH66, surdité : gain nul, la friction reste où elle est. -/
theorem TH66_surdite (astar a0 : ℝ) (t : ℕ) : traj 0 astar a0 t = a0 := by
  have := traj_formule 0 astar a0 t; simp at this; linarith

/-- TH66, panique : gain β = 2, oscillation perpétuelle autour de a*. -/
theorem TH66_oscillation (astar a0 : ℝ) (t : ℕ) :
    traj 2 astar a0 (t + 2) = traj 2 astar a0 t := by
  have h1 := traj_formule 2 astar a0 (t + 2)
  have h2 := traj_formule 2 astar a0 t
  have : ((1:ℝ) - 2) ^ (t + 2) = (1 - 2) ^ t := by rw [pow_add]; norm_num
  rw [this] at h1; linarith

/-- TH66, panique : gain β > 2, l'écart à la consigne explose. -/
theorem TH66_divergence (beta astar a0 : ℝ) (h2 : 2 < beta) (hne : a0 ≠ astar) :
    Tendsto (fun t => |traj beta astar a0 t - astar|) atTop atTop := by
  have hq : 1 < |1 - beta| := by
    rw [abs_of_neg (by linarith)]; linarith
  have hd : 0 < |a0 - astar| := abs_pos.2 (sub_ne_zero.2 hne)
  have hpow : Tendsto (fun t : ℕ => |1 - beta| ^ t) atTop atTop :=
    tendsto_pow_atTop_atTop_of_one_lt hq
  have := hpow.atTop_mul_const hd
  refine this.congr (fun t => ?_)
  rw [traj_formule, abs_mul, abs_pow]

/-! ## TH68, TH70, TH73 — Échange, homogénéisation et verrou intérieur

Forme : deux collectifs de budgets τ1, τ2 échangent à chaque pas une part
r ∈ (0, 1] de leur écart : l'écart est multiplié par (1 − r), la moyenne est
conservée. La consigne d'architecture vaut aᵢ* = gᵢ·τᵢ (gᵢ = architecture).
Friction inter-collective : |g1·τ1 − g2·τ2|. -/

def ecart (r d0 : ℝ) (t : ℕ) : ℝ := (1 - r) ^ t * d0

/-- Budgets après t pas : moyenne m ± écart/2. -/
def tau1 (r m d0 : ℝ) (t : ℕ) : ℝ := m + ecart r d0 t / 2
def tau2 (r m d0 : ℝ) (t : ℕ) : ℝ := m - ecart r d0 t / 2

theorem ecart_tend_vers_zero (r d0 : ℝ) (h0 : 0 < r) (h1 : r ≤ 1) :
    Tendsto (ecart r d0) atTop (𝓝 0) := by
  have hq : |1 - r| < 1 := by rw [abs_lt]; constructor <;> linarith
  have := (tendsto_pow_atTop_nhds_zero_of_abs_lt_one hq).mul_const d0
  simpa [ecart] using this

def friction (g1 g2 r m d0 : ℝ) (t : ℕ) : ℝ := |g1 * tau1 r m d0 t - g2 * tau2 r m d0 t|

theorem friction_limite (g1 g2 r m d0 : ℝ) (h0 : 0 < r) (h1 : r ≤ 1) :
    Tendsto (friction g1 g2 r m d0) atTop (𝓝 |(g1 - g2) * m|) := by
  have he := ecart_tend_vers_zero r d0 h0 h1
  have : Tendsto (fun t => (g1 - g2) * m + (g1 + g2) / 2 * ecart r d0 t) atTop
      (𝓝 ((g1 - g2) * m + (g1 + g2) / 2 * 0)) :=
    tendsto_const_nhds.add (he.const_mul _)
  simp at this
  have := this.abs
  refine this.congr (fun t => ?_)
  simp only [friction, tau1, tau2]; congr 1; ring

/-- TH70 (paradoxe de l'échange) : architectures identiques ⇒ la friction s'éteint. -/
theorem TH70 (g r m d0 : ℝ) (h0 : 0 < r) (h1 : r ≤ 1) :
    Tendsto (friction g g r m d0) atTop (𝓝 0) := by
  simpa using friction_limite g g r m d0 h0 h1

/-- TH73 (verrou intérieur) et TH68 : architectures différentes et budget moyen
    non nul ⇒ une friction strictement positive survit à tout échange. -/
theorem TH73 (g1 g2 r m d0 : ℝ) (h0 : 0 < r) (h1 : r ≤ 1) (hg : g1 ≠ g2) (hm : m ≠ 0) :
    Tendsto (friction g1 g2 r m d0) atTop (𝓝 |(g1 - g2) * m|) ∧ 0 < |(g1 - g2) * m| :=
  ⟨friction_limite g1 g2 r m d0 h0 h1, abs_pos.2 (mul_ne_zero (sub_ne_zero.2 hg) hm)⟩

/-! ## TH81 — Les creux montent… à une condition

Forme : expansion ×γ, contraction qui garde une fraction ρ et une semence g ≥ 0 :
m(k+1) = ρ·γ·m(k) + g. -/

def creux (q g m0 : ℝ) : ℕ → ℝ
  | 0     => m0
  | k + 1 => q * creux q g m0 k + g

/-- Si q = ρ·γ > 1 (et m0 > 0, g ≥ 0), les creux montent sans fin : TH81. -/
theorem TH81 (q g m0 : ℝ) (hq : 1 < q) (hm : 0 < m0) (hg : 0 ≤ g) :
    Tendsto (creux q g m0) atTop atTop := by
  have hmin : ∀ k, q ^ k * m0 ≤ creux q g m0 k := by
    intro k; induction k with
    | zero => simp [creux]
    | succ n ih =>
      simp only [creux, pow_succ]
      have hq0 : 0 ≤ q := by linarith
      nlinarith [mul_le_mul_of_nonneg_left ih hq0]
  have := (tendsto_pow_atTop_atTop_of_one_lt hq).atTop_mul_const hm
  exact tendsto_atTop_mono hmin this

/-- Si q < 1, même avec une semence g, les creux plafonnent à g/(1 − q) :
    la spirale cesse de monter (elle redevient un cycle à l'échelle). TH81 n'est
    donc pas automatique : il exige ρ·γ ≥ 1. -/
theorem TH81_plafond (q g m0 : ℝ) (h0 : 0 ≤ q) (hq : q < 1) :
    Tendsto (creux q g m0) atTop (𝓝 (g / (1 - q))) := by
  have h1q : (1 - q) ≠ 0 := by linarith
  have hform : ∀ k, creux q g m0 k = q ^ k * (m0 - g / (1 - q)) + g / (1 - q) := by
    intro k; induction k with
    | zero => simp [creux]
    | succ n ih => simp only [creux, ih, pow_succ]; field_simp; ring
  have habs : |q| < 1 := by rw [abs_of_nonneg h0]; exact hq
  have := ((tendsto_pow_atTop_nhds_zero_of_abs_lt_one habs).mul_const (m0 - g / (1 - q))).add_const (g / (1 - q))
  simp at this
  exact this.congr (fun k => (hform k).symm)

end LStar.C2

end
