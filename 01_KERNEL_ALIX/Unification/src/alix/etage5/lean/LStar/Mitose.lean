/-
  L*↑ — TH118, la Mitose Stigmergique (Lean 4 core).
  Proposé par Alix et Christian (18 nov. 2026), formalisé par Thot.

  Modèle : un carrefour dont les branches piégées forment la liste `P` ; toute
  autre branche est une sortie. Chaque agent a son PROPRE ordre d'essai (routes
  différentes, comme dans la simulation), saute les branches déjà rayées dans la
  mémoire commune, raye chaque piège qu'il heurte, et s'arrête à la première sortie.
  Les agents passent l'un après l'autre (une arborescence binaire parcourue dans
  n'importe quel ordre est un cas particulier : la forme de l'arbre ne compte pas).
-/
namespace LStar.Mitose
open Classical

/-- Un agent : (pièges heurtés, mémoire après). -/
def essai (P : List Nat) : List Nat → List Nat → Nat × List Nat
  | [],      M => (0, M)
  | i :: is, M =>
    if i ∈ M then essai P is M
    else if i ∈ P then let r := essai P is (i :: M); (r.1 + 1, r.2)
    else (0, M)

/-- Invariant d'un agent : la mémoire grandit exactement de ce qu'il paie, reste
sans doublon, et ne contient que des pièges. -/
theorem essai_inv (P : List Nat) : ∀ (ordre M : List Nat), M.Nodup → (∀ x ∈ M, x ∈ P) →
    (essai P ordre M).2.length = M.length + (essai P ordre M).1 ∧
    (essai P ordre M).2.Nodup ∧ (∀ x ∈ (essai P ordre M).2, x ∈ P) := by
  intro ordre; induction ordre with
  | nil => intro M h1 h2; exact ⟨by simp [essai], by simpa [essai] using h1, by simpa [essai] using h2⟩
  | cons i is ih =>
    intro M h1 h2; simp only [essai]
    by_cases hi : i ∈ M
    · simp only [hi, if_true]; exact ih M h1 h2
    · simp only [hi, if_false]
      by_cases hp : i ∈ P
      · simp only [hp, if_true]
        obtain ⟨a, b, c⟩ := ih (i :: M) (List.nodup_cons.mpr ⟨hi, h1⟩)
          (by intro x hx; simp at hx; rcases hx with rfl | hx
              · exact hp
              · exact h2 x hx)
        refine ⟨by simp at a ⊢; omega, b, c⟩
      · simp only [hp, if_false]; exact ⟨by simp, h1, h2⟩

/-- La colonie, agents en séquence : (coût total, mémoire finale). -/
def colonie (P : List Nat) : List (List Nat) → List Nat → Nat × List Nat
  | [],      M => (0, M)
  | o :: os, M => let r := essai P o M; let s := colonie P os r.2; (r.1 + s.1, s.2)

theorem colonie_inv (P : List Nat) : ∀ (agents : List (List Nat)) (M : List Nat), M.Nodup → (∀ x ∈ M, x ∈ P) →
    (colonie P agents M).2.length = M.length + (colonie P agents M).1 ∧
    (colonie P agents M).2.Nodup ∧ (∀ x ∈ (colonie P agents M).2, x ∈ P) := by
  intro agents; induction agents with
  | nil => intro M h1 h2; exact ⟨by simp [colonie], by simpa [colonie] using h1, by simpa [colonie] using h2⟩
  | cons o os ih =>
    intro M h1 h2
    obtain ⟨a1, b1, c1⟩ := essai_inv P o M h1 h2
    obtain ⟨a2, b2, c2⟩ := ih _ b1 c1
    refine ⟨?_, b2, c2⟩
    simp only [colonie]; omega

/-- Une mémoire sans doublon faite de pièges n'est jamais plus longue que la liste
des pièges. -/
theorem borne_aux (M : List Nat) : ∀ P : List Nat, M.Nodup → (∀ x ∈ M, x ∈ P) → M.length ≤ P.length := by
  induction M with
  | nil => intro P _ _; simp
  | cons x M ih =>
    intro P h1 h2
    have hx : x ∈ P := h2 x (by simp)
    have hnd := List.nodup_cons.mp h1
    have := ih (P.erase x) hnd.2 (fun y hy => by
      have hne : y ≠ x := fun e => hnd.1 (e ▸ hy)
      exact (List.mem_erase_of_ne hne).mpr (h2 y (by simp [hy])))
    have hl := List.length_erase_of_mem hx
    have hpos : 0 < P.length := List.length_pos.mpr (fun e => by simp [e] at hx)
    simp at this ⊢; omega

theorem borne_memoire (P M : List Nat) (h1 : M.Nodup) (h2 : ∀ x ∈ M, x ∈ P) :
    M.length ≤ P.length := borne_aux M P h1 h2

/-- TH118 (a) — Le coût total de la colonie est borné par |P|, quel que soit le
nombre d'agents et quels que soient leurs ordres d'essai. -/
theorem TH118_borne (P : List Nat) (agents : List (List Nat)) :
    (colonie P agents []).1 ≤ P.length := by
  obtain ⟨a, b, c⟩ := colonie_inv P agents [] List.nodup_nil (by simp)
  have := borne_memoire P _ b c
  simp at a; omega

/-! ### (b) La génération g* — une suite infinie d'agents -/

/-- Mémoire après les `n` premiers agents d'une suite infinie. -/
def memoire (P : List Nat) (agent : Nat → List Nat) : Nat → List Nat
  | 0     => []
  | n + 1 => (essai P (agent n) (memoire P agent n)).2

def cout (P : List Nat) (agent : Nat → List Nat) (n : Nat) : Nat :=
  (essai P (agent n) (memoire P agent n)).1

theorem memoire_inv (P : List Nat) (agent : Nat → List Nat) : ∀ n,
    (memoire P agent n).Nodup ∧ (∀ x ∈ memoire P agent n, x ∈ P) := by
  intro n; induction n with
  | zero => simp [memoire]
  | succ n ih =>
    obtain ⟨_, b, c⟩ := essai_inv P (agent n) _ ih.1 ih.2
    exact ⟨b, c⟩

theorem memoire_pas (P : List Nat) (agent : Nat → List Nat) (n : Nat) :
    (memoire P agent (n + 1)).length = (memoire P agent n).length + cout P agent n :=
  (essai_inv P (agent n) _ (memoire_inv P agent n).1 (memoire_inv P agent n).2).1

/-- Une suite d'entiers croissante et bornée finit par se figer. -/
theorem fige (f : Nat → Nat) (B : Nat) (mono : ∀ n, f n ≤ f (n + 1)) (bd : ∀ n, f n ≤ B) :
    ∃ g, ∀ j, g ≤ j → f j = f g := by
  have monoG : ∀ a b, a ≤ b → f a ≤ f b := by
    intro a b hab; induction hab with
    | refl => exact Nat.le_refl _
    | step _ ih => exact Nat.le_trans ih (mono _)
  suffices H : ∀ k s, B - f s = k → ∃ g, ∀ j, g ≤ j → f j = f g from H _ 0 rfl
  intro k
  induction k using Nat.strongRecOn with
  | _ k ih =>
    intro s hs
    by_cases h : ∀ j, s ≤ j → f j = f s
    · exact ⟨s, h⟩
    · have : ∃ j, s ≤ j ∧ f j ≠ f s := by
        apply Classical.byContradiction; intro hn
        exact h (fun j hj => Classical.byContradiction fun hne => hn ⟨j, hj, hne⟩)
      obtain ⟨j, hj, hne⟩ := this
      have hlt : f s < f j := Nat.lt_of_le_of_ne (monoG s j hj) (Ne.symm hne)
      exact ih (B - f j) (by have := bd j; omega) j rfl

/-- TH118 (b) — Il existe une génération g* à partir de laquelle tout nouvel agent
passe sans payer un seul piège. -/
theorem TH118_gstar (P : List Nat) (agent : Nat → List Nat) :
    ∃ g, ∀ j, g ≤ j → cout P agent j = 0 := by
  let f := fun n => (memoire P agent n).length
  obtain ⟨g, hg⟩ := fige f P.length
    (fun n => by simp only [f]; rw [memoire_pas]; omega)
    (fun n => borne_memoire P _ (memoire_inv P agent n).1 (memoire_inv P agent n).2)
  refine ⟨g, fun j hj => ?_⟩
  have h1 := hg j hj; have h2 := hg (j + 1) (by omega)
  have := memoire_pas P agent j
  simp only [f] at h1 h2; omega

/-! ### La condition qui ne se négocie pas : partager AVANT le suivant

Si une génération agit en parallèle avec la mémoire du début de génération,
la borne |P| tombe : deux sœurs heurtent le même piège et le paient deux fois. -/

def generationParallele (P : List Nat) (soeurs : List (List Nat)) (M : List Nat) : Nat :=
  (soeurs.map fun o => (essai P o M).1).foldl (· + ·) 0

/-- Contre-exemple : un seul piège (branche 0), deux sœurs en parallèle → 2 > |P| = 1. -/
example : generationParallele [0] [[0, 1], [0, 1]] [] = 2 := by decide
example : (colonie [0] [[0, 1], [0, 1]] []).1 = 1 := by decide

end LStar.Mitose
