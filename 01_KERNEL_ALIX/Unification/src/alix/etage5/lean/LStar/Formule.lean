/-
  La formule d'origine L*(x) = G ⊕ H ⊕ T ⊕ D ⊕ B (15 novembre 2026),
  réponse aux 4 limites du trou noir posées par Cristo.

  Une formule faite de lois (des implications) ne se « prouve » pas comme un
  théorème : on peut vérifier qu'elle est cohérente, que chaque clause compte,
  et ce qu'elle entraîne. C'est ce que fait ce fichier, en Lean 4 pur.
-/

namespace LStar.Formule

/-- Un univers : des objets et les primitives de la Partie I. Le symbole ∼ de
    la clause G n'est défini nulle part dans la spécification : il est laissé
    libre ici (`sim`), comme paramètre. -/
structure Univers where
  E      : Type
  vide   : E                    -- ∅
  pente  : E → E → Prop         -- x → y
  sim    : E → E → Prop         -- x ∼ c (non défini dans le texte)
  saut   : E → E → Prop         -- passage x ⊲ y vers la strate supérieure
  front  : E → E → Prop         -- x | y
  reson  : E → E → Prop         -- x ≍ y
  subi   : E → E → Prop         -- x ⇝ y
  navig  : E → E → Prop         -- x ↭ y
  grain  : E → Prop             -- □ ⊆ x
  Emp    : Type
  emp    : E → Emp

variable (U : Univers)

/-- G : la gravité déjouée (fontaine blanche ou échappée dimensionnelle). -/
def G : Prop := ∀ x c, U.pente x c → U.sim x c → U.pente c x ∨ ∃ y, U.saut x y
/-- H : l'horizon rendu transparent. -/
def H : Prop := ∀ x y, U.front x y → U.reson x y
/-- T : le temps affranchi. -/
def T : Prop := ∀ x y, U.subi x y → U.navig x y
/-- D : le volume irréductible. -/
def D : Prop := ∀ x, x ≠ U.vide → U.grain x
/-- B : la loi d'unicité. -/
def B : Prop := ∀ x y, x ≠ y → U.emp x ≠ U.emp y

/-- L*(x) : les cinq clauses ensemble. -/
def Lstar : Prop := G U ∧ H U ∧ T U ∧ D U ∧ B U

/-- Une dérivation : une suite d'objets, chaque pas suivant une pente. -/
def Derivation (x : Nat → U.E) : Prop := ∀ k, U.pente (x k) (x (k + 1))

/-! ## 1. Cohérence — et même quand toutes les hypothèses se déclenchent

Un univers vide de relations satisfait trivialement des implications ; ce
modèle-ci est plus exigeant : TOUTES les pentes, frontières et flèches subies
existent, et L*(x) tient quand même. La formule n'est pas contradictoire. -/

/-- Univers sur les entiers (0 joue ∅), relations au choix. -/
abbrev surNat (pente sim saut front reson subi navig : Nat → Nat → Prop)
    (grain : Nat → Prop) (emp : Nat → Nat) : Univers :=
  { E := Nat, vide := 0, pente := pente, sim := sim, saut := saut, front := front,
    reson := reson, subi := subi, navig := navig, grain := grain, Emp := Nat, emp := emp }

abbrev tout : Nat → Nat → Prop := fun _ _ => True
abbrev rien : Nat → Nat → Prop := fun _ _ => False

abbrev plein : Univers :=
  surNat tout tout (fun x y => y = x + 1) tout tout tout tout (fun x => x ≠ 0) id

theorem coherente : Lstar plein := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · intro x c _ _; exact Or.inl trivial
  · intro _ _ _; trivial
  · intro _ _ _; trivial
  · intro x h; exact h
  · intro x y h; exact h

/-! ## 2. Chaque clause compte : aucune ne découle des quatre autres

Pour chaque clause, un univers où les quatre autres tiennent et elle échoue. -/

abbrev sansG : Univers :=
  surNat (fun x c => x = 1 ∧ c = 2) tout rien tout tout tout tout (fun x => x ≠ 0) id
theorem G_independante : ¬ G sansG ∧ H sansG ∧ T sansG ∧ D sansG ∧ B sansG := by
  refine ⟨?_, fun _ _ _ => trivial, fun _ _ _ => trivial, fun x h => h, fun x y h => h⟩
  intro hG
  rcases hG (1 : Nat) (2 : Nat) ⟨rfl, rfl⟩ trivial with h | ⟨y, hy⟩
  · exact absurd h.1 (by decide)
  · exact hy

abbrev sansH : Univers := surNat tout tout (fun x y => y = x + 1) tout rien tout tout (fun x => x ≠ 0) id
theorem H_independante : G sansH ∧ ¬ H sansH ∧ T sansH ∧ D sansH ∧ B sansH :=
  ⟨fun _ _ _ _ => Or.inl trivial, fun h => h (0 : Nat) (0 : Nat) trivial, fun _ _ _ => trivial,
   fun x h => h, fun x y h => h⟩

abbrev sansT : Univers := surNat tout tout (fun x y => y = x + 1) tout tout tout rien (fun x => x ≠ 0) id
theorem T_independante : G sansT ∧ H sansT ∧ ¬ T sansT ∧ D sansT ∧ B sansT :=
  ⟨fun _ _ _ _ => Or.inl trivial, fun _ _ _ => trivial, fun h => h (0 : Nat) (0 : Nat) trivial,
   fun x h => h, fun x y h => h⟩

abbrev sansD : Univers := surNat tout tout (fun x y => y = x + 1) tout tout tout tout (fun _ => False) id
theorem D_independante : G sansD ∧ H sansD ∧ T sansD ∧ ¬ D sansD ∧ B sansD :=
  ⟨fun _ _ _ _ => Or.inl trivial, fun _ _ _ => trivial, fun _ _ _ => trivial,
   fun h => h (1 : Nat) (by decide), fun x y h => h⟩

abbrev sansB : Univers := surNat tout tout (fun x y => y = x + 1) tout tout tout tout (fun x => x ≠ 0) (fun _ => 0)
theorem B_independante : G sansB ∧ H sansB ∧ T sansB ∧ D sansB ∧ ¬ B sansB :=
  ⟨fun _ _ _ _ => Or.inl trivial, fun _ _ _ => trivial, fun _ _ _ => trivial,
   fun x h => h, fun h => h (0 : Nat) (1 : Nat) (by decide) rfl⟩

/-! ## 3. Ce que la formule seule NE prouve PAS

Le texte du 15 novembre annonce que D « bannit formellement la densité
infinie » et que B « interdit la dégénérescence en boucle fermée ». Telles
qu'écrites, les clauses ne l'entraînent pas : voici des dérivations, dans un
univers qui satisfait les cinq clauses, qui tombent dans ∅ ou tournent en rond. -/

/-- D dit : ce qui n'est pas vide a un grain. Il ne dit pas qu'on ne peut pas
    devenir vide. Une dérivation peut atteindre ∅. -/
theorem D_ne_bannit_pas_le_vide :
    Lstar plein ∧ ∃ x : Nat → plein.E, Derivation plein x ∧ x 1 = plein.vide :=
  ⟨coherente, fun k => if k = 0 then (1 : Nat) else 0, fun _ => trivial, rfl⟩

/-- B dit : deux objets distincts ont deux empreintes distinctes. Il n'interdit
    pas de revenir au MÊME objet. Une dérivation peut boucler x → y → x. -/
theorem B_n_interdit_pas_la_boucle :
    Lstar plein ∧ ∃ x : Nat → plein.E, Derivation plein x ∧ x 0 = x 2 ∧ x 0 ≠ x 1 :=
  ⟨coherente, fun k => if k % 2 = 0 then (1 : Nat) else 2, fun _ => trivial,
   by decide, by decide⟩

/-- Même la clause G, branche α (fontaine blanche), donne une boucle : seule la
    branche β (saut de strate) fait sortir. -/
theorem fontaine_blanche_boucle :
    ∃ x : Nat → plein.E, Derivation plein x ∧ (∀ k, x (k + 2) = x k) ∧ x 0 ≠ x 1 :=
  ⟨fun k => if k % 2 = 0 then (1 : Nat) else 2, fun _ => trivial,
   fun k => by simp [Nat.add_mod], by decide⟩

/-! ## 4. Ce qu'il faut AJOUTER pour que la libération soit un théorème

La Conjecture C (TH5) devient vraie si l'on ajoute deux lois que la v1.x a
introduites : la croissance stricte R-A (chaque pas ouvre une issue de plus,
I(x') = I(x) + 1) et l'interdiction explicite de produire ∅. -/

/-- Sous R-A, une dérivation ne revient jamais sur un état (non-périodique). -/
theorem RA_sans_retour (I : U.E → Nat) (x : Nat → U.E)
    (hRA : ∀ k, I (x (k + 1)) = I (x k) + 1) :
    ∀ j k, j < k → x j ≠ x k := by
  have hI : ∀ k, I (x k) = I (x 0) + k := by
    intro k; induction k with
    | zero => rfl
    | succ n ih => rw [hRA, ih]; omega
  intro j k hjk h
  have := congrArg I h
  rw [hI j, hI k] at this
  omega

/-- Et avec B, les empreintes ne se répètent pas non plus. -/
theorem RA_B_empreintes (I : U.E → Nat) (x : Nat → U.E)
    (hRA : ∀ k, I (x (k + 1)) = I (x k) + 1) (hB : B U) :
    ∀ j k, j < k → U.emp (x j) ≠ U.emp (x k) :=
  fun j k h => hB _ _ (RA_sans_retour U I x hRA j k h)

/-- Libération structurelle (TH5) : sous R-A, B, et l'axiome « aucun pas ne
    mène à ∅ », une dérivation n'est jamais écrasée, ne répète ni état ni
    empreinte, et ne reste piégée sur aucun centre (elle ne le revisite pas). -/
theorem liberation (I : U.E → Nat) (x : Nat → U.E)
    (hRA : ∀ k, I (x (k + 1)) = I (x k) + 1) (hB : B U)
    (hdepart : x 0 ≠ U.vide) (hAntiVide : ∀ k, x (k + 1) ≠ U.vide) :
    (∀ k, x k ≠ U.vide)
    ∧ (∀ j k, j < k → x j ≠ x k)
    ∧ (∀ j k, j < k → U.emp (x j) ≠ U.emp (x k))
    ∧ (∀ c, ∀ j k, j < k → x j = c → x k ≠ c) := by
  refine ⟨?_, RA_sans_retour U I x hRA, RA_B_empreintes U I x hRA hB, ?_⟩
  · intro k; cases k with
    | zero => exact hdepart
    | succ n => exact hAntiVide n
  · intro c j k hjk hj hk
    exact RA_sans_retour U I x hRA j k hjk (hj.trans hk.symm)

end LStar.Formule
