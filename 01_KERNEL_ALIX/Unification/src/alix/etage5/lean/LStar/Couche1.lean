/-
  L*↑ — Couche 1 complète (TH1 à TH31), Lean 4 core, sans Mathlib.

  Modèle généralisé : toutes les interprétations que la spécification laisse
  ouvertes sont des paramètres (`Config`) :
    - loquet R-Λ (n_Λ ou aucun), qui force β ou seulement le rend disponible ;
    - politique au point de choix (β ou α) ;
    - univers fini (au plus N sauts β) ou non borné ;
  et le vide ∅ est un objet du langage, pour que TH1 dise quelque chose.
-/

namespace LStar.C1

inductive Obj where
  | vide : Obj
  | x0   : Obj
  | c1   : Obj
  | s    : Nat → Obj
  deriving DecidableEq, Repr

structure St where
  pos : Obj
  sec : Bool
  run : Nat
  b   : Nat
  anc : Obj
  deriving DecidableEq, Repr

structure Config where
  nl     : Option Nat   -- n_Λ ; none = pas de loquet
  force  : Bool         -- le loquet force-t-il β ?
  polB   : Bool         -- au point de choix : true = β, false = α
  taille : Option Nat   -- univers fini : au plus N sauts β ; none = non borné

def loquet (cfg : Config) (st : St) : Bool :=
  match cfg.nl with
  | none   => false
  | some n => st.sec && decide (n ≤ st.run)

def epuise (cfg : Config) (st : St) : Bool :=
  match cfg.taille with
  | none   => false
  | some N => decide (N ≤ st.b)

/-- Point de choix (régime mixte) : en secours, β disponible, loquet non forçant. -/
def choix (cfg : Config) (bloque : Bool) (st : St) : Bool :=
  st.sec && (!bloque || loquet cfg st) && !(loquet cfg st && cfg.force)

def prendBeta (cfg : Config) (bloque : Bool) (st : St) : Bool :=
  if st.sec && (!bloque || loquet cfg st) then
    (if loquet cfg st && cfg.force then true else cfg.polB)
  else !bloque

def pas (cfg : Config) (bloque : Bool) (st : St) : St :=
  if prendBeta cfg bloque st && !epuise cfg st then
    { pos := .s (st.b + 1), sec := false, run := 0, b := st.b + 1, anc := st.anc }
  else
    let anc := if st.sec then st.anc else st.pos
    let run := st.run + 1
    { pos := if run % 2 = 1 then .c1 else anc, sec := true, run := run, b := st.b, anc := anc }

def init : St := { pos := .x0, sec := false, run := 0, b := 0, anc := .x0 }

def apres (cfg : Config) : List Bool → St → St
  | [],      st => st
  | e :: es, st => apres cfg es (pas cfg e st)

def etats (cfg : Config) : List Bool → St → List St
  | [],      st => [st]
  | e :: es, st => st :: etats cfg es (pas cfg e st)

theorem apres_snoc (cfg : Config) (l : List Bool) (e : Bool) (st : St) :
    apres cfg (l ++ [e]) st = pas cfg e (apres cfg l st) := by
  induction l generalizing st with
  | nil => rfl
  | cons x xs ih => simp [apres, ih]

theorem etats_snoc (cfg : Config) (l : List Bool) (e : Bool) (st : St) :
    etats cfg (l ++ [e]) st = etats cfg l st ++ [pas cfg e (apres cfg l st)] := by
  induction l generalizing st with
  | nil => simp [etats, apres]
  | cons x xs ih => simp [etats, apres, ih]

theorem etats_length (cfg : Config) (l : List Bool) (st : St) :
    (etats cfg l st).length = l.length + 1 := by
  induction l generalizing st with
  | nil => rfl
  | cons x xs ih => simp [etats, ih]

/-- Le dernier état de `etats` est `apres`. -/
theorem mem_etats_apres (cfg : Config) (l : List Bool) (st : St) :
    apres cfg l st ∈ etats cfg l st := by
  induction l generalizing st with
  | nil => simp [etats, apres]
  | cons x xs ih => simp [etats, apres]; exact Or.inr (ih _)

theorem rep_snoc (x : Bool) (k : Nat) :
    List.replicate (k + 1) x = List.replicate k x ++ [x] := by
  induction k with
  | zero => rfl
  | succ k ih => simp [List.replicate_succ] at *; exact ih

/-! ## Compteurs de la signature Σ (D11–D13) -/

def T_R (cfg : Config) (env : List Bool) : Nat :=
  ((etats cfg env init).filter (fun st => st.sec)).length

def positions (cfg : Config) (env : List Bool) : List Obj :=
  (etats cfg env init).map St.pos

/-- D12 : nombre de pas qui répètent un objet déjà visité. -/
def rc : List Obj → List Obj → Nat
  | _,    []      => 0
  | vus,  x :: xs => (if x ∈ vus then 1 else 0) + rc (x :: vus) xs

def R (cfg : Config) (env : List Bool) : Nat := rc [] (positions cfg env)

def Dbeta (cfg : Config) (env : List Bool) : Nat := (apres cfg env init).b

/-! ## TH1, TH6 — Non-écrasement : aucune trajectoire n'atteint ∅ -/

def sain (st : St) : Prop := st.pos ≠ .vide ∧ st.anc ≠ .vide

theorem pas_sain (cfg : Config) (e : Bool) (st : St) (h : sain st) : sain (pas cfg e st) := by
  obtain ⟨hp, ha⟩ := h
  unfold pas sain
  split
  · simp [ha]
  · cases hs : st.sec <;> simp [hs, hp, ha] <;> split <;> simp_all

theorem apres_sain (cfg : Config) (env : List Bool) :
    ∀ st, sain st → sain (apres cfg env st) := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st h; exact ih _ (pas_sain cfg e st h)

theorem etats_sains (cfg : Config) (env : List Bool) :
    ∀ st, sain st → ∀ s ∈ etats cfg env st, sain s := by
  induction env with
  | nil => intro st h s hs; simp [etats] at hs; rw [hs]; exact h
  | cons e es ih =>
    intro st h s hs
    simp [etats] at hs
    rcases hs with hs | hs
    · rw [hs]; exact h
    · exact ih _ (pas_sain cfg e st h) s hs

/-- TH1 (et TH6 : même sous secours) : pour toute interprétation et tout
    environnement, aucun état visité n'est ∅. -/
theorem TH1 (cfg : Config) (env : List Bool) : Obj.vide ∉ positions cfg env := by
  intro h
  simp [positions, List.mem_map] at h
  obtain ⟨st, hst, hp⟩ := h
  exact (etats_sains cfg env init ⟨by simp [init], by simp [init]⟩ st hst).1 hp

/-! ## TH2, TH3, TH4, TH5 — Le régime saturé pur (univers non borné) -/

theorem sature_etat (cfg : Config) (h : cfg.taille = none) (t : Nat) :
    apres cfg (List.replicate (t + 1) false) init
      = { pos := .s (t + 1), sec := false, run := 0, b := t + 1, anc := .x0 } := by
  induction t with
  | zero => simp [apres, pas, prendBeta, epuise, h, init]
  | succ k ih =>
    rw [rep_snoc, apres_snoc, ih]
    simp [pas, prendBeta, epuise, h]

/-- I(x) : compteur d'issues ; pour s_n, n issues ouvertes. -/
def I : Obj → Nat
  | .s n => n
  | _    => 0

/-- TH2 : en régime saturé pur, I croît strictement (de 1 à chaque pas). -/
theorem TH2 (cfg : Config) (h : cfg.taille = none) (t : Nat) :
    I (apres cfg (List.replicate (t + 2) false) init).pos
      = I (apres cfg (List.replicate (t + 1) false) init).pos + 1 := by
  rw [sature_etat cfg h, sature_etat cfg h]; simp [I]

/-- TH3 : jamais deux fois le même objet. -/
theorem TH3 (cfg : Config) (h : cfg.taille = none) (t u : Nat) (htu : t ≠ u) :
    (apres cfg (List.replicate (t + 1) false) init).pos
      ≠ (apres cfg (List.replicate (u + 1) false) init).pos := by
  rw [sature_etat cfg h, sature_etat cfg h]; simp; omega

/-- TH4 : jamais l'attracteur. -/
theorem TH4 (cfg : Config) (h : cfg.taille = none) (t : Nat) :
    (apres cfg (List.replicate (t + 1) false) init).pos ≠ .c1 := by
  rw [sature_etat cfg h]; simp

/-- TH5 (Libération structurelle, Conjecture C) : non écrasée, sans retour,
    hors de tout puits. -/
theorem TH5 (cfg : Config) (h : cfg.taille = none) :
    Obj.vide ∉ positions cfg (List.replicate 1 false)
    ∧ (∀ t u, t ≠ u → (apres cfg (List.replicate (t + 1) false) init).pos
                    ≠ (apres cfg (List.replicate (u + 1) false) init).pos)
    ∧ (∀ t, (apres cfg (List.replicate (t + 1) false) init).pos ≠ .c1) :=
  ⟨TH1 cfg _, TH3 cfg h, TH4 cfg h⟩

/-! ## TH7, TH13 — α neutre, β croissant -/

theorem TH7 (cfg : Config) (e : Bool) (st : St) (h : (pas cfg e st).sec = true) :
    (pas cfg e st).b = st.b := by
  unfold pas at *; split at h <;> simp_all
  split <;> simp_all

theorem TH13 (cfg : Config) (e : Bool) (st : St) (h : (pas cfg e st).sec = false) :
    (pas cfg e st).b = st.b + 1 ∧ I (pas cfg e st).pos = st.b + 1 := by
  unfold pas at *; split at h <;> simp_all [I]

/-! ## TH8 — Secours pur sans loquet : période 2 (pour toute politique) -/

theorem secours_pur_etat (cfg : Config) (hnl : cfg.nl = none) (k : Nat) :
    apres cfg (List.replicate (k + 1) true) init
      = { pos := if (k + 1) % 2 = 1 then .c1 else .x0, sec := true,
          run := k + 1, b := 0, anc := .x0 } := by
  induction k with
  | zero => simp [apres, pas, prendBeta, loquet, hnl, init, epuise]
  | succ k ih =>
    rw [rep_snoc, apres_snoc, ih]
    simp [pas, prendBeta, loquet, hnl, epuise]

theorem TH8 (cfg : Config) (hnl : cfg.nl = none) (k : Nat) :
    (apres cfg (List.replicate (k + 3) true) init).pos
      = (apres cfg (List.replicate (k + 1) true) init).pos := by
  rw [secours_pur_etat cfg hnl (k + 2), secours_pur_etat cfg hnl k]
  have : (k + 2 + 1) % 2 = (k + 1) % 2 := by omega
  simp only [this]

/-! ## TH9 — Retour dès le 2e pas de secours (n_Λ ≥ 2 ou pas de loquet) -/

def bienForme (st : St) : Prop := st.sec = false → st.run = 0

theorem pas_bienForme (cfg : Config) (e : Bool) (st : St) : bienForme (pas cfg e st) := by
  unfold bienForme pas; split <;> simp

theorem apres_bienForme (cfg : Config) (env : List Bool) :
    ∀ st, bienForme st → bienForme (apres cfg env st) := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st _; exact ih _ (pas_bienForme cfg e st)

theorem TH9 (cfg : Config) (h : ∀ n, cfg.nl = some n → 2 ≤ n)
    (st : St) (hsat : st.sec = false) (hrun : st.run = 0) :
    (pas cfg true (pas cfg true st)).pos = st.pos := by
  cases hnl : cfg.nl with
  | none => simp [pas, prendBeta, loquet, hnl, hsat, hrun]
  | some n =>
    have hn := h n hnl
    have h1 : ¬ n ≤ 1 := by omega
    simp [pas, prendBeta, loquet, hnl, hsat, hrun, h1]

theorem TH9_trajectoire (cfg : Config) (h : ∀ n, cfg.nl = some n → 2 ≤ n)
    (prefixe : List Bool) (hsat : (apres cfg prefixe init).sec = false) :
    (apres cfg (prefixe ++ [true, true]) init).pos = (apres cfg prefixe init).pos := by
  have hb := apres_bienForme cfg prefixe init (fun _ => rfl) hsat
  have : prefixe ++ [true, true] = (prefixe ++ [true]) ++ [true] := by simp
  rw [this, apres_snoc, apres_snoc]
  exact TH9 cfg h _ hsat hb

/-! ## TH10, TH11, TH12 — Le loquet -/

/-- TH10 : loquet forçant, univers non épuisé : β est pris. -/
theorem TH10 (cfg : Config) (n : Nat) (hnl : cfg.nl = some n) (hf : cfg.force = true)
    (e : Bool) (st : St) (hs : st.sec = true) (hr : n ≤ st.run) (he : epuise cfg st = false) :
    (pas cfg e st).sec = false := by
  simp [pas, prendBeta, loquet, hnl, hf, hs, hr, he]

def borne (n : Nat) (st : St) : Prop :=
  bienForme st ∧ (st.sec = true → 1 ≤ st.run ∧ st.run ≤ n)

/-- TH11 : loquet forçant (n_Λ ≥ 1) et univers non borné : toute excursion dure
    au plus n_Λ pas. (Avec n_Λ = 0, une excursion dure quand même un pas.) -/
theorem TH11_pas (cfg : Config) (n : Nat) (hn : 1 ≤ n) (hnl : cfg.nl = some n)
    (hf : cfg.force = true) (ht : cfg.taille = none) (e : Bool) (st : St) (h : borne n st) :
    borne n (pas cfg e st) := by
  obtain ⟨hb, hr⟩ := h
  refine ⟨pas_bienForme cfg e st, ?_⟩
  intro hsec
  by_cases hc : (prendBeta cfg e st && !epuise cfg st) = true
  · simp [pas, hc] at hsec
  · simp only [pas, if_neg hc] at hsec ⊢
    cases hs : st.sec
    · have h0 := hb hs; simp [h0]; omega
    · have ⟨h1, h2⟩ := hr hs
      by_cases hn' : n ≤ st.run
      · exfalso; apply hc
        simp [prendBeta, epuise, loquet, hnl, hf, hs, hn', ht]
      · simp; omega

theorem TH11 (cfg : Config) (n : Nat) (hn : 1 ≤ n) (hnl : cfg.nl = some n)
    (hf : cfg.force = true) (ht : cfg.taille = none) (env : List Bool) :
    ∀ st, borne n st → borne n (apres cfg env st) := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st h; exact ih _ (TH11_pas cfg n hn hnl hf ht e st h)

theorem TH11_depuis_init (cfg : Config) (n : Nat) (hn : 1 ≤ n) (hnl : cfg.nl = some n)
    (hf : cfg.force = true) (ht : cfg.taille = none) (env : List Bool)
    (hs : (apres cfg env init).sec = true) : (apres cfg env init).run ≤ n :=
  ((TH11 cfg n hn hnl hf ht env init ⟨fun _ => rfl, fun h => by simp [init] at h⟩).2 hs).2

/-- TH12 : pendant une excursion bornée par max(n_Λ,1), l'oscillation a
    période 2 ; la boucle transitoire tient en au plus 2·max(n_Λ,1) objets
    distincts visités… en fait en 2 : l'ancre et c1. -/
theorem TH12 (cfg : Config) (e : Bool) (st : St) (hs : st.sec = true)
    (h : (pas cfg e st).sec = true) :
    (pas cfg e st).pos = .c1 ∨ (pas cfg e st).pos = st.anc := by
  by_cases hc : (prendBeta cfg e st && !epuise cfg st) = true
  · simp [pas, hc] at h
  · simp only [pas, if_neg hc, hs, if_true]
    by_cases hp : (st.run + 1) % 2 = 1
    · simp [hp]
    · simp [hp]

/-- Nouveau : dans un univers FINI épuisé, le loquet ne sauve plus rien.
    TH11 exige un univers non borné. -/
theorem TH11_exige_univers_ouvert :
    let cfg : Config := { nl := some 1, force := true, polB := true, taille := some 0 }
    (apres cfg (List.replicate 6 false) init).sec = true := by
  decide

/-! ## TH15, TH16 — Univers fini : le principe des tiroirs -/

theorem tiroirs {α : Type} [DecidableEq α] :
    ∀ (l L : List α), l.Nodup → (∀ x ∈ l, x ∈ L) → l.length ≤ L.length := by
  intro l
  induction l with
  | nil => intro L _ _; simp
  | cons a l ih =>
    intro L hnd hsub
    rw [List.nodup_cons] at hnd
    have haL : a ∈ L := hsub a (by simp)
    have hsub' : ∀ x ∈ l, x ∈ L.erase a := by
      intro x hx
      have hxa : x ≠ a := fun h => hnd.1 (h ▸ hx)
      exact (List.mem_erase_of_ne hxa).2 (hsub x (by simp [hx]))
    have := ih (L.erase a) hnd.2 hsub'
    rw [List.length_erase_of_mem haL] at this
    have : 0 < L.length := List.length_pos_of_mem haL
    simp; omega

/-- Les objets d'un univers de taille N. -/
def objets (N : Nat) : List Obj := .x0 :: .c1 :: (List.range N).map (fun i => .s (i + 1))

theorem mem_objets_s (N k : Nat) : Obj.s k ∈ objets N ↔ 1 ≤ k ∧ k ≤ N := by
  simp [objets, List.mem_map]
  constructor
  · rintro ⟨i, hi, rfl⟩; omega
  · intro ⟨h1, h2⟩; exact ⟨k - 1, by omega, by omega⟩

def dansU (N : Nat) (st : St) : Prop := st.b ≤ N ∧ st.pos ∈ objets N ∧ st.anc ∈ objets N

theorem pas_dansU (cfg : Config) (N : Nat) (ht : cfg.taille = some N) (e : Bool) (st : St)
    (h : dansU N st) : dansU N (pas cfg e st) := by
  obtain ⟨hb, hp, ha⟩ := h
  by_cases hc : (prendBeta cfg e st && !epuise cfg st) = true
  · simp only [pas, hc, if_true]
    have hlt : st.b < N := by
      simp [epuise, ht] at hc; omega
    refine ⟨by simp; omega, ?_, ha⟩
    simp only; rw [mem_objets_s]; omega
  · simp only [pas, if_neg hc]
    refine ⟨hb, ?_, ?_⟩
    · by_cases hpar : (st.run + 1) % 2 = 1
      · simp [hpar, objets]
      · simp only [hpar, if_false]
        cases hs : st.sec <;> simp [hp, ha]
    · cases hs : st.sec <;> simp [hp, ha]

theorem etats_dansU (cfg : Config) (N : Nat) (ht : cfg.taille = some N) (env : List Bool) :
    ∀ st, dansU N st → ∀ s ∈ etats cfg env st, dansU N s := by
  induction env with
  | nil => intro st h s hs; simp [etats] at hs; rw [hs]; exact h
  | cons e es ih =>
    intro st h s hs
    simp [etats] at hs
    rcases hs with hs | hs
    · rw [hs]; exact h
    · exact ih _ (pas_dansU cfg N ht e st h) s hs

/-- TH16 : dans un univers de taille N, toute trajectoire de plus de N + 2
    états répète un objet — quelle que soit l'interprétation et l'environnement. -/
theorem TH16 (cfg : Config) (N : Nat) (ht : cfg.taille = some N) (env : List Bool)
    (hlong : N + 2 < env.length + 1) : ¬ (positions cfg env).Nodup := by
  intro hnd
  have hsub : ∀ x ∈ positions cfg env, x ∈ objets N := by
    intro x hx
    simp [positions, List.mem_map] at hx
    obtain ⟨st, hst, rfl⟩ := hx
    exact (etats_dansU cfg N ht env init ⟨by simp [init], by simp [init, objets], by simp [init, objets]⟩ st hst).2.1
  have := tiroirs _ _ hnd hsub
  simp [positions, etats_length, objets] at this
  omega

/-- TH15 : contraposée — une évasion sans retour aussi longue qu'on veut
    exige un univers non borné. -/
theorem TH15 (cfg : Config) (N : Nat) (ht : cfg.taille = some N) :
    ¬ ∀ k, ∃ env : List Bool, env.length = k ∧ (positions cfg env).Nodup := by
  intro h
  obtain ⟨env, hl, hnd⟩ := h (N + 2)
  exact TH16 cfg N ht env (by omega) hnd

/-! ## TH17, TH20, TH22 — Le mécanisme M revisite le passé

Tout mécanisme qui, en secours, ne se déplace que sur la β-chaîne déjà
parcourue (ou sur n'importe quel objet déjà visité) produit un retour :
« sans boucle » au sens non périodique, jamais « sans retour » au sens D12. -/

theorem TH17_revisite {α : Type} (passe : List α) (x : α) (h : x ∈ passe) :
    ¬ (passe ++ [x]).Nodup := by
  intro hnd
  exact (List.pairwise_append.1 hnd).2.2 x h x (by simp) rfl

/-! ## TH18 — Ordre par la β-chaîne : chaque saut β porte un indice neuf -/

theorem TH18 (cfg : Config) (e : Bool) (st : St) (h : (pas cfg e st).sec = false) :
    ∃ k, (pas cfg e st).pos = .s k ∧ k = st.b + 1 := by
  have := TH13 cfg e st h
  unfold pas at *; split at h <;> simp_all

/-! ## TH23 — Monotonie des composantes de Σ -/

theorem TH23_T_R (cfg : Config) (l : List Bool) (e : Bool) :
    T_R cfg l ≤ T_R cfg (l ++ [e]) := by
  simp [T_R, etats_snoc, List.filter_append]

theorem TH23_Dbeta (cfg : Config) (l : List Bool) (e : Bool) :
    Dbeta cfg l ≤ Dbeta cfg (l ++ [e]) := by
  simp only [Dbeta, apres_snoc]
  unfold pas; split <;> simp

theorem rc_append (vus l m : List Obj) : rc vus l ≤ rc vus (l ++ m) := by
  induction l generalizing vus with
  | nil => simp [rc]
  | cons x xs ih =>
    rw [List.cons_append]
    show (if x ∈ vus then 1 else 0) + rc (x :: vus) xs ≤ (if x ∈ vus then 1 else 0) + rc (x :: vus) (xs ++ m)
    have := ih (x :: vus); omega

theorem TH23_R (cfg : Config) (l : List Bool) (e : Bool) :
    R cfg l ≤ R cfg (l ++ [e]) := by
  simp only [R, positions, etats_snoc, List.map_append]
  exact rc_append _ _ _

/-! ## TH25, TH26 — A est une source ; le point de non-retour est fermé -/

theorem T_R_mono (cfg : Config) (m : List Bool) :
    ∀ l, T_R cfg l ≤ T_R cfg (l ++ m) := by
  induction m with
  | nil => intro l; simp
  | cons e m ih =>
    intro l
    have h1 := TH23_T_R cfg l e
    have h2 := ih (l ++ [e])
    have : l ++ [e] ++ m = l ++ e :: m := by simp
    rw [this] at h2; omega

theorem R_mono (cfg : Config) (m : List Bool) :
    ∀ l, R cfg l ≤ R cfg (l ++ m) := by
  induction m with
  | nil => intro l; simp
  | cons e m ih =>
    intro l
    have h1 := TH23_R cfg l e
    have h2 := ih (l ++ [e])
    have : l ++ [e] ++ m = l ++ e :: m := by simp
    rw [this] at h2; omega

/-- TH25 : une fois T_R > 0, il le reste pour toute suite (quitter A est irréversible). -/
theorem TH25 (cfg : Config) (l m : List Bool) (h : 0 < T_R cfg l) : 0 < T_R cfg (l ++ m) := by
  have := T_R_mono cfg m l; omega

/-- TH26 : une fois R > 0 (point de non-retour), il le reste. -/
theorem TH26 (cfg : Config) (l m : List Bool) (h : 0 < R cfg l) : 0 < R cfg (l ++ m) := by
  have := R_mono cfg m l; omega

/-! ## TH28, TH29 — Points de choix -/

/-- TH28 : un point de choix n'arrive qu'en secours, β disponible (régime mixte). -/
theorem TH28 (cfg : Config) (e : Bool) (st : St) (h : choix cfg e st = true) :
    st.sec = true ∧ (e = false ∨ loquet cfg st = true) := by
  unfold choix at h; cases e <;> simp_all

/-- TH29 : avec la politique β, un point de choix termine l'excursion :
    au plus un point de choix par excursion. -/
theorem TH29 (cfg : Config) (hp : cfg.polB = true) (ht : cfg.taille = none)
    (e : Bool) (st : St) (h : choix cfg e st = true) : (pas cfg e st).sec = false := by
  unfold choix at h
  simp [pas, prendBeta, epuise, ht, hp] at *
  cases e <;> simp_all

/-- … et avec la politique α, une même excursion en rencontre plusieurs. -/
theorem TH29_politique_alpha :
    let cfg : Config := { nl := none, force := false, polB := false, taille := none }
    let s1 := pas cfg true init
    let s2 := pas cfg false s1
    choix cfg false s1 = true ∧ s2.sec = true ∧ choix cfg false s2 = true := by
  decide

/-! ## TH30 — Dominance de « toujours β » (loquet non forçant)

Avec la politique α et un loquet qui ne force pas, le secours est absorbant :
une fois entrée, la trajectoire n'en sort plus. Donc à chaque instant où la
trajectoire « toujours β » est en secours, la trajectoire α l'est aussi :
T_R(β) ≤ T_R(α), pour tout environnement. -/

def cfgA (nl : Option Nat) (t : Option Nat) : Config := { nl := nl, force := false, polB := false, taille := t }
def cfgB (nl : Option Nat) (t : Option Nat) : Config := { nl := nl, force := false, polB := true, taille := t }

theorem alpha_absorbant (nl t : Option Nat) (e : Bool) (st : St) (h : st.sec = true) :
    (pas (cfgA nl t) e st).sec = true := by
  simp [pas, prendBeta, cfgA, h]
  cases e <;> simp

theorem apres_alpha_absorbant (nl t : Option Nat) (env : List Bool) :
    ∀ st, st.sec = true → (apres (cfgA nl t) env st).sec = true := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st h; exact ih _ (alpha_absorbant nl t e st h)

def Tfrom (cfg : Config) (env : List Bool) (st : St) : Nat :=
  ((etats cfg env st).filter (fun s => s.sec)).length

theorem filter_len_cons (st : St) (l : List St) :
    ((st :: l).filter (fun s => s.sec)).length
      = (if st.sec then 1 else 0) + (l.filter (fun s => s.sec)).length := by
  cases h : st.sec <;> simp [List.filter_cons, h] <;> omega

theorem Tfrom_cons (cfg : Config) (e : Bool) (es : List Bool) (st : St) :
    Tfrom cfg (e :: es) st = (if st.sec then 1 else 0) + Tfrom cfg es (pas cfg e st) := by
  simp only [Tfrom, etats]; exact filter_len_cons _ _

/-- Invariant : soit les deux trajectoires coïncident, soit α est en secours. -/
theorem TH30_general (nl t : Option Nat) (env : List Bool) :
    ∀ sA sB : St, (sA = sB ∨ sA.sec = true) →
      Tfrom (cfgB nl t) env sB ≤ Tfrom (cfgA nl t) env sA := by
  induction env with
  | nil =>
    intro sA sB h
    rcases h with rfl | h
    · simp [Tfrom, etats]
    · simp only [Tfrom, etats]; rw [filter_len_cons, filter_len_cons]; simp [h]
      cases sB.sec <;> simp
  | cons e es ih =>
    intro sA sB h
    have hnext : pas (cfgA nl t) e sA = pas (cfgB nl t) e sB ∨ (pas (cfgA nl t) e sA).sec = true := by
      rcases h with rfl | h
      · cases hs : sA.sec
        · left; simp [pas, prendBeta, epuise, cfgA, cfgB, hs]
        · right; exact alpha_absorbant nl t e sA hs
      · right; exact alpha_absorbant nl t e sA h
    have := ih _ _ hnext
    have hhead : (if sB.sec then 1 else 0) ≤ (if sA.sec then 1 else 0) := by
      rcases h with rfl | h
      · exact Nat.le_refl _
      · simp [h]; cases sB.sec <;> simp
    rw [Tfrom_cons, Tfrom_cons]; omega

/-- TH30 : pour tout environnement, « toujours β » passe au plus autant de
    pas en secours que la politique α. -/
theorem TH30 (nl t : Option Nat) (env : List Bool) :
    T_R (cfgB nl t) env ≤ T_R (cfgA nl t) env :=
  TH30_general nl t env init init (Or.inl rfl)

/-! ## TH31 — Un seul blocage suffit à perdre A

La v4.0 dit « un blocage de ≥ 2 pas ». C'est plus fort que ça : UN pas
bloqué fait toujours entrer en secours, donc T_R > 0, donc A est perdu. -/

theorem bloquer_entre_en_secours (cfg : Config) (st : St) (hs : st.sec = false) :
    (pas cfg true st).sec = true := by
  simp [pas, prendBeta, hs]

theorem TH31 (cfg : Config) (l m : List Bool) (hs : (apres cfg l init).sec = false) :
    0 < T_R cfg (l ++ [true] ++ m) := by
  apply TH25
  simp only [T_R, etats_snoc, List.filter_append, List.length_append]
  have := bloquer_entre_en_secours cfg _ hs
  simp [this]

/-! ## Décision de Christian (17 nov. 2026) : « la porte ne fait rien, elle s'ouvre »

Le loquet ne force pas : il rend le chemin vers le haut disponible. Tous les
chemins existent déjà ; l'entité les entreprend ou non.

- Si elle entreprend le chemin dès que la porte s'ouvre (politique β),
  l'excursion dure au plus n_Λ pas : `TH11_porte_ouverte`.
- Si elle ne l'entreprend jamais (politique α), elle reste en secours pour
  toujours (`apres_alpha_absorbant`), et le secours tourne en rond (TH8, TH9) :
  refuser la porte, c'est le piège, pas l'errance. -/

theorem TH11_porte_ouverte_pas (cfg : Config) (n : Nat) (hn : 1 ≤ n) (hnl : cfg.nl = some n)
    (hf : cfg.force = false) (hp : cfg.polB = true) (ht : cfg.taille = none)
    (e : Bool) (st : St) (h : borne n st) : borne n (pas cfg e st) := by
  obtain ⟨hb, hr⟩ := h
  refine ⟨pas_bienForme cfg e st, ?_⟩
  intro hsec
  by_cases hc : (prendBeta cfg e st && !epuise cfg st) = true
  · simp [pas, hc] at hsec
  · simp only [pas, if_neg hc] at hsec ⊢
    cases hs : st.sec
    · have h0 := hb hs; simp [h0]; omega
    · have ⟨h1, h2⟩ := hr hs
      by_cases hn' : n ≤ st.run
      · exfalso; apply hc
        simp [prendBeta, epuise, loquet, hnl, hf, hp, hs, hn', ht]
      · simp; omega

theorem TH11_porte_ouverte (cfg : Config) (n : Nat) (hn : 1 ≤ n) (hnl : cfg.nl = some n)
    (hf : cfg.force = false) (hp : cfg.polB = true) (ht : cfg.taille = none) (env : List Bool) :
    ∀ st, borne n st → borne n (apres cfg env st) := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st h; exact ih _ (TH11_porte_ouverte_pas cfg n hn hnl hf hp ht e st h)

/-- Refuser la porte : une fois en secours, on n'en sort plus, quel que soit
    l'environnement — et on tourne entre l'ancre et l'attracteur. -/
theorem refuser_la_porte (nl t : Option Nat) (env : List Bool) (st : St) (h : st.sec = true) :
    (apres (cfgA nl t) env st).sec = true :=
  apres_alpha_absorbant nl t env st h

/-! ## La porte reste ouverte (décision de Christian, 17 nov. 2026, précisée)
« La porte doit rester ouverte. » Une fois ouverte, elle ne se referme pas tant
que l'être est en secours : il peut la passer au pas suivant, ou dans mille pas.
Refuser maintenant n'est pas refuser pour toujours. -/

/-- Une fois ouverte, la porte reste ouverte au pas suivant, quel que soit
l'environnement, tant que l'être ne l'a pas passée. -/
theorem porte_reste_ouverte (nl t : Option Nat) (e : Bool) (st : St)
    (h : loquet (cfgA nl t) st = true) : loquet (cfgA nl t) (pas (cfgA nl t) e st) = true := by
  cases hnl : nl with
  | none => simp [loquet, cfgA, hnl] at h
  | some n =>
    have h' : st.sec = true ∧ n ≤ st.run := by simpa [loquet, cfgA, hnl] using h
    simp [pas, prendBeta, epuise, loquet, cfgA, hnl, h'.1, h'.2]
    cases t <;> cases e <;> (try simp) <;> omega

/-- …et après n'importe quel nombre de refus. -/
theorem porte_reste_ouverte_toujours (nl t : Option Nat) (env : List Bool) :
    ∀ st, loquet (cfgA nl t) st = true → loquet (cfgA nl t) (apres (cfgA nl t) env st) = true := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st h; exact ih _ (porte_reste_ouverte nl t e st h)

/-- Le jour où l'être décide d'entreprendre le chemin, la porte ouverte le laisse
passer, en un seul pas, quel que soit l'environnement. -/
theorem passer_quand_on_veut (n : Nat) (e : Bool) (st : St)
    (h : loquet (cfgA (some n) none) st = true) : (pas (cfgB (some n) none) e st).sec = false := by
  have h' : st.sec = true ∧ n ≤ st.run := by simpa [loquet, cfgA] using h
  simp [pas, prendBeta, epuise, loquet, cfgB, h'.1, h'.2]

/-- Synthèse : refuser k fois, puis entreprendre → sortie. Aucun délai ne ferme la porte. -/
theorem jamais_trop_tard (n : Nat) (refus : List Bool) (e : Bool) (st : St)
    (h : loquet (cfgA (some n) none) st = true) :
    (pas (cfgB (some n) none) e (apres (cfgA (some n) none) refus st)).sec = false :=
  passer_quand_on_veut n e _ (porte_reste_ouverte_toujours (some n) none refus st h)

end LStar.C1
