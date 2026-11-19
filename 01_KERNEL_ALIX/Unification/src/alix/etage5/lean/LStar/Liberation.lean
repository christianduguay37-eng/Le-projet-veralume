/-
  L*↑ — TH48 sous recrutement (Lean 4 core). 18 novembre 2026.
  Proposé par Alix et Christian comme « corollaire de TH118 » ; Thot montre que
  ce n'en est PAS un : le déblocage vient d'une hypothèse nouvelle, le
  RECRUTEMENT — tout libéré rejoint les porteurs avec une capacité neuve.

  Modèle de capacité : un porteur peut hisser c = ⌊τ₀/δ⌋ captifs dans sa vie.
  État : (libérés F, hissages encore disponibles U). Un hissage coûte 1 de U.
  Avec recrutement, chaque libéré apporte r hissages neufs.
-/
namespace LStar.Liberation

/-- Un hissage, s'il reste des captifs et de la capacité. -/
def hisser (n r : Nat) (s : Nat × Nat) : Nat × Nat :=
  if s.1 < n ∧ 0 < s.2 then (s.1 + 1, s.2 - 1 + r) else s

def iter (n r : Nat) : Nat → Nat × Nat → Nat × Nat
  | 0,     s => s
  | t + 1, s => iter n r t (hisser n r s)

/-- Avec recrutement (r ≥ 1) : la capacité ne retombe jamais à zéro. -/
theorem capacite_preservee (n r : Nat) (hr : 1 ≤ r) :
    ∀ t (s : Nat × Nat), 0 < s.2 → 0 < (iter n r t s).2 := by
  intro t; induction t with
  | zero => intro s h; exact h
  | succ t ih =>
    intro s h; apply ih; unfold hisser; split <;> simp_all <;> omega

/-- Chaque pas libère quelqu'un tant qu'il reste des captifs. -/
theorem progres (n r : Nat) (hr : 1 ≤ r) :
    ∀ t (s : Nat × Nat), 0 < s.2 → s.1 ≤ n → (iter n r t s).1 = min n (s.1 + t) := by
  intro t; induction t with
  | zero => intro s _ hF; simp [iter]; omega
  | succ t ih =>
    intro s hU hF
    simp only [iter]
    by_cases hc : s.1 < n
    · have hs : hisser n r s = (s.1 + 1, s.2 - 1 + r) := by simp [hisser, hc, hU]
      rw [hs, ih _ (by simp; omega) (by simp; omega)]; simp; omega
    · have hs : hisser n r s = s := by simp [hisser, hc]
      rw [hs, ih s hU hF]; omega

/-- TH48 sous recrutement : un seul porteur capable d'un seul hissage suffit ;
en n hissages, les n captifs sont libres. Aucun seuil k*. -/
theorem TH48_recrutement (n r U0 : Nat) (hr : 1 ≤ r) (hU : 1 ≤ U0) :
    (iter n r n (0, U0)).1 = n := by
  rw [progres n r hr n (0, U0) hU (Nat.zero_le _)]; simp

/-- Sans recrutement (r = 0, le modèle historique) : on ne libère jamais plus que
la capacité de départ. TH45 et son seuil k* restent vrais dans CE modèle. -/
theorem TH45_sans_recrutement (n : Nat) :
    ∀ t (s : Nat × Nat), (iter n 0 t s).1 ≤ s.1 + s.2 := by
  intro t; induction t with
  | zero => intro s; simp [iter]
  | succ t ih =>
    intro s; simp only [iter]
    have h := ih (hisser n 0 s)
    by_cases hc : s.1 < n ∧ 0 < s.2
    · have hs : hisser n 0 s = (s.1 + 1, s.2 - 1) := by simp [hisser, hc]
      rw [hs] at h ⊢; simp at h; omega
    · have hs : hisser n 0 s = s := by simp [hisser, hc]
      rw [hs] at h ⊢; exact h

/-- L'exemple de la simulation : n = 5, un porteur, τ₀ = 10, δ = 4 → c = 2. -/
example : (iter 5 0 10 (0, 2)).1 = 2 := by decide   -- sans recrutement : 3 abandonnés
example : (iter 5 1 10 (0, 2)).1 = 5 := by decide   -- recrutement à 1 seul hissage : tous libres
example : (iter 5 4 10 (0, 2)).1 = 5 := by decide   -- « mitose » 1→2 porteurs de c = 2 : r = 4

end LStar.Liberation
