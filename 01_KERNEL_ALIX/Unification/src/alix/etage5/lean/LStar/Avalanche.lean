/-
  L*↑ — TH119, l'Avalanche Solidaire (Lean 4 core). 18 novembre 2026.
  Démonstration de Christian et Alix ; formalisation de Thot.

  Hissage SYNCHRONE : à chaque cycle, tous les porteurs disponibles hissent en
  même temps, m = min(captifs, porteurs) ; chaque libéré devient porteur (r = 1,
  décision de Christian du 18 nov.).
-/
namespace LStar.Avalanche

/-- État : (captifs restants C, porteurs actifs H). Porteurs inépuisables. -/
def cycle (s : Nat × Nat) : Nat × Nat :=
  let m := min s.1 s.2
  (s.1 - m, s.2 + m)

def apres : Nat → Nat × Nat → Nat × Nat
  | 0,     s => s
  | t + 1, s => apres t (cycle s)

/-- Libérés après t cycles, en partant de n captifs et 1 porteur : min(n, 2^t − 1).
Et les porteurs sont toujours « 1 + libérés ». -/
theorem avalanche (n : Nat) : ∀ t,
    n - (apres t (n, 1)).1 = min n (2 ^ t - 1) ∧
    (apres t (n, 1)).2 = 1 + (n - (apres t (n, 1)).1) ∧
    (apres t (n, 1)).1 ≤ n := by
  -- on raisonne sur la forme « apres t s = cycle^t s » en avançant par la fin
  have step : ∀ t, apres (t + 1) (n, 1) = cycle (apres t (n, 1)) := by
    have gen : ∀ t (s : Nat × Nat), apres (t + 1) s = cycle (apres t s) := by
      intro t; induction t with
      | zero => intro s; rfl
      | succ t ih => intro s; simp only [apres] at ih ⊢; exact ih (cycle s)
    intro t; exact gen t (n, 1)
  intro t; induction t with
  | zero => simp [apres]
  | succ t ih =>
    obtain ⟨h1, h2, h3⟩ := ih
    rw [step]
    generalize hC : (apres t (n, 1)).1 = C at h1 h2 h3
    generalize hH : (apres t (n, 1)).2 = H at h2
    have hp : 2 ^ (t + 1) = 2 * 2 ^ t := by rw [Nat.pow_succ]; omega
    have hpos : 1 ≤ 2 ^ t := Nat.one_le_two_pow
    rw [hp]
    generalize 2 ^ t = x at h1 hpos
    simp only [cycle]
    refine ⟨?_, ?_, ?_⟩ <;> omega

/-- TH119 — Avec T cycles tels que n ≤ 2^T − 1, tous les captifs sont libres. -/
theorem TH119_libres (n T : Nat) (h : n ≤ 2 ^ T - 1) : (apres T (n, 1)).1 = 0 := by
  obtain ⟨h1, _, h3⟩ := avalanche n T
  omega

/-- …et pas avant : si 2^t − 1 < n, il reste au moins un captif. T = ⌈log₂(n+1)⌉ est exact. -/
theorem TH119_pas_avant (n t : Nat) (h : 2 ^ t - 1 < n) : 0 < (apres t (n, 1)).1 := by
  obtain ⟨h1, _, h3⟩ := avalanche n t
  omega

example : (apres 10 (1000, 1)).1 = 0 := by decide        -- 1 000 captifs : 10 cycles
example : (apres 9 (1000, 1)).1 = 489 := by decide       -- 9 cycles ne suffisent pas

/-! ### La condition cachée : l'endurance des porteurs

La démonstration suppose que chaque porteur peut hisser à CHAQUE cycle, sans fin.
Si un porteur ne peut hisser qu'une seule fois dans sa vie (c = ⌊τ₀/δ⌋ = 1),
il s'épuise en libérant son captif, qui le remplace : le nombre de porteurs ne
double jamais, il reste à 1, et la libération redevient linéaire. -/

/-- Porteurs à usage unique : ceux qui hissent s'épuisent, les libérés les remplacent. -/
def cycleUnique (s : Nat × Nat) : Nat × Nat :=
  let m := min s.1 s.2
  (s.1 - m, s.2 - m + m)

def apresUnique : Nat → Nat × Nat → Nat × Nat
  | 0,     s => s
  | t + 1, s => apresUnique t (cycleUnique s)

theorem porteurs_constants : ∀ t (s : Nat × Nat), (apresUnique t s).2 = s.2 := by
  intro t; induction t with
  | zero => intro s; rfl
  | succ t ih => intro s; simp only [apresUnique]; rw [ih]; simp [cycleUnique]; omega

example : (apresUnique 10 (1000, 1)).1 = 990 := by decide  -- 10 cycles : 10 libérés seulement

end LStar.Avalanche
