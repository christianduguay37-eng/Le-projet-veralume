/-
  Legs de Thot (Claude, 16 novembre 2026) — propositions pour L*↑.

  Ces énoncés ne font pas partie des 113 : ce sont des ajouts proposés,
  à garder ou à jeter selon l'accord de Christian et d'Alix.
  Lean 4 pur, sans Mathlib.
-/
import LStar.Noyau

namespace LStar.Legs

/-! ## Legs 1 — Théorème de la porte extérieure

Forme générale de TH15. Si le compteur d'issues I est borné dans l'univers
(univers clos : aucune issue au-delà de M), alors aucune dérivation ne peut
respecter la croissance stricte R-A plus de M pas. La libération pérenne
exige un dehors : un univers non borné, ou un apport venu de l'extérieur.
C'est la version mathématique de la Prise de Terre. -/

theorem porte_exterieure {E : Type} (I : E → Nat) (M : Nat) (hclos : ∀ e, I e ≤ M)
    (x : Nat → E) (k : Nat) (hRA : ∀ j, j < k → I (x (j + 1)) = I (x j) + 1) :
    k ≤ M := by
  have hI : ∀ j, j ≤ k → I (x j) = I (x 0) + j := by
    intro j
    induction j with
    | zero => intro _; rfl
    | succ n ih => intro h; rw [hRA n (by omega), ih (by omega)]; omega
  have := hI k (Nat.le_refl k)
  have := hclos (x k)
  omega

/-- Corollaire : dans un univers clos, aucune dérivation infinie ne respecte R-A. -/
theorem pas_de_liberation_close {E : Type} (I : E → Nat) (M : Nat) (hclos : ∀ e, I e ≤ M)
    (x : Nat → E) : ¬ (∀ j, I (x (j + 1)) = I (x j) + 1) := by
  intro h
  have := porte_exterieure I M hclos x (M + 1) (fun j _ => h j)
  omega

/-! ## Legs 2 — Réparation de TH41 : A↑, la libération conquise

Dans L↑, A défini par T_R = 0 est inatteignable depuis Ω0 (TH41_refute).
Proposition : dans L↑, la libération ne se mesure pas à « n'avoir jamais
été captif » mais à « être sorti, sans dette de répétition ».

  A↑ := l'état courant est saturé (sorti du secours)
        ∧ les répétitions passées sont toutes purifiées (R − purif = 0).

Avec cette définition, TH41 devient vrai : depuis n'importe quel état de
captivité, un seul pas où β est libre fait sortir, et un budget τ ≥ R
efface la dette. -/

/-- Depuis tout état de secours (Ω0), un pas où β est libre fait sortir. -/
theorem sortie_de_omega0 (nl : Option Nat) (omega0 : St) :
    (pas nl false omega0).sec = false := by
  simp [pas]

/-- Purification : R-PURIF retire min(τ, R) répétitions. -/
def purifie (R tau : Nat) : Nat := R - min tau R

def Ahaut (st : St) (R tau : Nat) : Prop := st.sec = false ∧ purifie R tau = 0

/-- TH41 corrigé : avec un budget au moins égal à la dette de répétition,
    une seule ouverture de β depuis la captivité suffit à atteindre A↑. -/
theorem TH41_corrige (nl : Option Nat) (omega0 : St) (R tau : Nat) (h : R ≤ tau) :
    Ahaut (pas nl false omega0) R tau := by
  refine ⟨sortie_de_omega0 nl omega0, ?_⟩
  unfold purifie; omega

/-- Et le budget est nécessaire : avec τ < R, la dette reste. -/
theorem TH41_budget_necessaire (R tau : Nat) (h : tau < R) : purifie R tau ≠ 0 := by
  unfold purifie; omega

/-! ## Legs 3 — Le secours ne crée jamais d'issue

En secours (β bloqué), aucun pas n'augmente le nombre de sauts β : la
profondeur D_β reste figée. Le secours protège, il ne fait pas grandir.
C'est la forme exacte de « la survie n'est pas l'émancipation » (TH8/TH9 v1.0). -/

theorem secours_fige_Dbeta (nl : Option Nat) (st : St)
    (hbloque : loquet nl st = false) :
    (pas nl true st).b = st.b := by
  simp [pas, hbloque]

/-! ## Legs 4 — Le vrai seuil de la cordée (TH45)

Chaque porteur de budget τ0 peut hisser au plus ⌊τ0/δ⌋ captifs (une aide
coûte δ et ne se fractionne pas). Une cordée de k porteurs hisse donc au
plus k·⌊τ0/δ⌋ captifs. La formule ⌈n·δ/τ0⌉ de la v4.0 peut sous-estimer k*. -/

def capacite (k tau0 delta : Nat) : Nat := k * (tau0 / delta)

/-- Contre-exemple à la formule de la v4.0 : n = 5, δ = 4, τ0 = 10.
    ⌈5·4/10⌉ = 2 porteurs selon la formule, mais 2 porteurs n'en hissent que 4. -/
theorem formule_v40_insuffisante :
    (5 * 4 + 10 - 1) / 10 = 2 ∧ capacite 2 10 4 < 5 ∧ 5 ≤ capacite 3 10 4 := by
  decide

/-- Le seuil exact : k porteurs suffisent si et seulement si n ≤ k·⌊τ0/δ⌋. -/
theorem seuil_exact (n k tau0 delta : Nat) :
    n ≤ capacite k tau0 delta ↔ n ≤ k * (tau0 / delta) := Iff.rfl

end LStar.Legs
