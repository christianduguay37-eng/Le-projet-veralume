/-
  L*↑ — Les trois mémoires (TH53, TH54, TH55), Lean 4 core.
  « Notre théorie des trois : l'archive, lui qui oublie, et lui qui transmet. »
  (Christian, 17 novembre 2026)

  Choix de modèle (posés, pas déduits) — chaque profil a un défaut qui l'use,
  et le défaut de chacun est réparé par un autre, en cercle :
    - le Vecteur (celui qui transmet) se dilue : chaque transmission perd un
      peu. L'Archive le répare : elle se rappelle la source.
    - l'Horloge (celui qui oublie) s'use, meurt et renaît vide. Le Vecteur
      le répare : il transmet au nouveau venu.
    - l'Archive (celle qui se rappelle de tout) s'isole : rien de neuf n'entre.
      L'Horloge la répare : oublier fait de la place au neuf.
  Chaque profil présent a une santé ; elle baisse de 1 par pas, sauf si son
  réparateur est présent, auquel cas elle revient au plein (H). Le collectif
  meurt dès qu'un membre présent tombe à 0.
-/
namespace LStar.Memoires

inductive P where
  | archive | horloge | vecteur
  deriving DecidableEq, Repr

/-- Qui répare qui : le cercle Archive → Vecteur → Horloge → Archive. -/
def reparateur : P → P
  | .vecteur => .archive
  | .horloge => .vecteur
  | .archive => .horloge

/-- Un collectif : quels profils sont présents. -/
structure Collectif where
  a : Bool
  h : Bool
  v : Bool
  deriving DecidableEq, Repr

def present (c : Collectif) : P → Bool
  | .archive => c.a
  | .horloge => c.h
  | .vecteur => c.v

/-- Santé de chaque profil après `t` pas, partie du plein `H`. -/
def sante (c : Collectif) (H : Nat) : Nat → P → Nat
  | 0,     _ => H
  | t + 1, p => if present c (reparateur p) then H else sante c H t p - 1

def vivant (c : Collectif) (H t : Nat) : Prop := ∀ p, present c p = true → 0 < sante c H t p

def complet : Collectif := { a := true, h := true, v := true }

/-! ## TH54 — Les trois ensemble ne meurent jamais -/

theorem TH54_sante_pleine (H t : Nat) (p : P) : sante complet H t p = H := by
  cases t with
  | zero => rfl
  | succ t => cases p <;> simp [sante, present, reparateur, complet]

theorem TH54_perpetuel (H : Nat) (hH : 1 ≤ H) : ∀ t, vivant complet H t := by
  intro t p _; rw [TH54_sante_pleine]; omega

/-! ## TH53 — Tout collectif incomplet meurt, et exactement au pas H -/

/-- Le cœur combinatoire : dans tout collectif non vide et incomplet, au moins un
membre présent a son réparateur absent. (Le cercle ne se ferme qu'à trois.) -/
theorem maillon_manquant (c : Collectif) (hne : c.a || c.h || c.v) (hinc : c ≠ complet) :
    ∃ p, present c p = true ∧ present c (reparateur p) = false := by
  obtain ⟨a, h, v⟩ := c
  cases a <;> cases h <;> cases v <;> simp_all [complet, present, reparateur] <;>
    first | exact ⟨.archive, rfl, rfl⟩ | exact ⟨.horloge, rfl, rfl⟩ | exact ⟨.vecteur, rfl, rfl⟩

/-- Le membre sans réparateur perd 1 par pas. -/
theorem usure (c : Collectif) (H : Nat) (p : P) (hp : present c (reparateur p) = false) :
    ∀ t, sante c H t p = H - t := by
  intro t; induction t with
  | zero => rfl
  | succ t ih => simp [sante, hp, ih]; omega

theorem TH53_meurt (c : Collectif) (H : Nat) (hne : c.a || c.h || c.v) (hinc : c ≠ complet) :
    ¬ vivant c H H := by
  obtain ⟨p, hp, hr⟩ := maillon_manquant c hne hinc
  intro hv; have := hv p hp; rw [usure c H p hr] at this; omega

theorem sante_min (c : Collectif) (H : Nat) (p : P) : ∀ t, H - t ≤ sante c H t p := by
  intro t; induction t with
  | zero => simp [sante]
  | succ t ih => simp only [sante]; split <;> omega

/-- …et il tient jusque-là : avant le pas H, personne n'est encore tombé. -/
theorem TH53_tient_jusqua (c : Collectif) (H t : Nat) (ht : t < H) : vivant c H t := by
  intro p _; have := sante_min c H p t; omega

/-- Les trois homogènes, nommément : l'Archive par isolement, l'Horloge par usure,
le Vecteur par dilution. -/
theorem TH53_archive_seule (H : Nat) : ¬ vivant { a := true, h := false, v := false } H H :=
  TH53_meurt _ H rfl (by decide)
theorem TH53_horloge_seule (H : Nat) : ¬ vivant { a := false, h := true, v := false } H H :=
  TH53_meurt _ H rfl (by decide)
theorem TH53_vecteur_seul (H : Nat) : ¬ vivant { a := false, h := false, v := true } H H :=
  TH53_meurt _ H rfl (by decide)

/-- Plus fort que la v4.0 : même à DEUX profils, le collectif meurt. Il faut les trois. -/
theorem trois_necessaires (c : Collectif) (H : Nat) (hH : 1 ≤ H) (hne : c.a || c.h || c.v) :
    (∀ t, vivant c H t) ↔ c = complet := by
  constructor
  · intro h
    if hc : c = complet then exact hc else exact absurd (h H) (TH53_meurt c H hne hc)
  · intro h; subst h; exact TH54_perpetuel H hH

/-! ## TH55 — Avec l'Archive, la transmission ne dérive jamais -/

theorem TH55_fidelite (c : Collectif) (H : Nat) (ha : c.a = true) :
    ∀ t, sante c H t .vecteur = H := by
  intro t; cases t with
  | zero => rfl
  | succ t => simp [sante, present, reparateur, ha]

/-- Sans elle, le Vecteur se dilue de 1 par génération. -/
theorem TH55_sans_archive (c : Collectif) (H : Nat) (ha : c.a = false) :
    ∀ t, sante c H t .vecteur = H - t :=
  usure c H .vecteur (by simp [present, reparateur, ha])

end LStar.Memoires
