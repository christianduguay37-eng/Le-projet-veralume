/-
  L*↑ — Noyau formel (couche 1), Lean 4 core, sans Mathlib.

  Même sémantique que `alix/etage5/noyau.py` (cas : un attracteur c1,
  politique « toujours β », loquet R-Λ qui force β, univers non borné).
  Les preuves ici sont GÉNÉRALES : pour tout horizon, toute histoire,
  tout n_Λ concerné — pas seulement dans une borne.
-/

namespace LStar

/-- Objets formels : état initial, attracteur, objets de strate s_n (β). -/
inductive Obj where
  | x0 : Obj
  | c1 : Obj
  | s  : Nat → Obj
  deriving DecidableEq, Repr

/-- État d'une dérivation. `sec` = régime de secours ; `run` = pas consécutifs
    en secours ; `b` = nombre de sauts β ; `anc` = ancre de l'excursion. -/
structure St where
  pos : Obj
  sec : Bool
  run : Nat
  b   : Nat
  anc : Obj
  deriving DecidableEq, Repr

/-- Le loquet R-Λ se déclenche-t-il ? `none` = pas de loquet (R-Λ′). -/
def loquet : Option Nat → St → Bool
  | none,   _  => false
  | some n, st => st.sec && decide (n ≤ st.run)

/-- Un pas. `bloque = true` : l'environnement bloque β. -/
def pas (nl : Option Nat) (bloque : Bool) (st : St) : St :=
  if !bloque || loquet nl st then
    -- branche β : saut hors-stratique vers un objet frais (R-G β, R-A)
    { pos := .s (st.b + 1), sec := false, run := 0, b := st.b + 1, anc := st.anc }
  else
    -- secours : branche α, oscillation ancre / attracteur (R-G α)
    let anc := if st.sec then st.anc else st.pos
    let run := st.run + 1
    { pos := if run % 2 = 1 then .c1 else anc, sec := true, run := run, b := st.b, anc := anc }

def init : St := { pos := .x0, sec := false, run := 0, b := 0, anc := .x0 }

/-- État après avoir suivi l'environnement `env` (liste de blocages). -/
def apres (nl : Option Nat) : List Bool → St → St
  | [],      st => st
  | e :: es, st => apres nl es (pas nl e st)

/-- Liste des états visités (état initial compris). -/
def etats (nl : Option Nat) : List Bool → St → List St
  | [],      st => [st]
  | e :: es, st => st :: etats nl es (pas nl e st)

def positions (nl : Option Nat) (env : List Bool) : List Obj :=
  (etats nl env init).map St.pos

/-- T_R : nombre d'états en secours. -/
def T_R (nl : Option Nat) (env : List Bool) : Nat :=
  ((etats nl env init).filter (fun st => st.sec)).length

/-- R = 0 : aucun retour identique (positions deux à deux distinctes ; par R-B
    l'empreinte d'un objet est l'objet lui-même). -/
def sansRetour (l : List Obj) : Prop := l.Nodup

theorem rep_snoc (x : Bool) (k : Nat) :
    List.replicate (k + 1) x = List.replicate k x ++ [x] := by
  induction k with
  | zero => rfl
  | succ k ih => simp [List.replicate_succ] at *; exact ih

/-- Invariant des états atteignables : en régime saturé, le compteur de
    secours est à zéro (R-Λ et β le remettent à 0). -/
def bienForme (st : St) : Prop := st.sec = false → st.run = 0

/-- Suivre `l ++ [e]`, c'est suivre `l` puis faire un pas. -/
theorem apres_snoc (nl : Option Nat) (l : List Bool) (e : Bool) (st : St) :
    apres nl (l ++ [e]) st = pas nl e (apres nl l st) := by
  induction l generalizing st with
  | nil => rfl
  | cons x xs ih => simp [apres, ih]

/-! ## TH3 — Régime saturé pur : la trajectoire ne revisite jamais un état -/

theorem sature_etat (nl : Option Nat) (t : Nat) :
    apres nl (List.replicate (t + 1) false) init
      = { pos := .s (t + 1), sec := false, run := 0, b := t + 1, anc := .x0 } := by
  induction t with
  | zero => simp [apres, pas, init]
  | succ k ih =>
    rw [rep_snoc, apres_snoc, ih]
    simp [pas]

/-- TH3 : deux instants distincts du régime saturé pur ont des objets distincts. -/
theorem TH3 (nl : Option Nat) (t u : Nat) (h : t ≠ u) :
    (apres nl (List.replicate (t + 1) false) init).pos
      ≠ (apres nl (List.replicate (u + 1) false) init).pos := by
  rw [sature_etat, sature_etat]
  simp
  omega

/-! ## TH9 — Point de non-retour précoce (général)

Depuis n'importe quel état saturé, avec n'importe quelle histoire, si β est
bloqué deux pas de suite et que le loquet ne peut pas se déclencher avant le
2e pas (pas de loquet, ou n_Λ ≥ 2), l'objet du 2e pas est l'objet de départ :
un retour identique, R ≥ 1. -/
theorem TH9 (nl : Option Nat) (h : ∀ n, nl = some n → 2 ≤ n)
    (st : St) (hsat : st.sec = false) (hrun : st.run = 0) :
    (pas nl true (pas nl true st)).pos = st.pos := by
  cases nl with
  | none => simp [pas, loquet, hsat, hrun]
  | some n =>
    have hn := h n rfl
    have h1 : ¬ n ≤ 1 := by omega
    simp [pas, loquet, hsat, hrun, h1]

/-- Et le premier pas de l'excursion est bien un pas de secours vers c1. -/
theorem TH9_premier_pas (nl : Option Nat) (st : St) (hsat : st.sec = false)
    (hrun : st.run = 0) :
    (pas nl true st).pos = .c1 ∧ (pas nl true st).sec = true := by
  cases nl <;> simp [pas, loquet, hsat, hrun]

/-! ## TH8 — Secours pur sans loquet : période 2 -/

theorem TH8_etat (k : Nat) :
    apres none (List.replicate (k + 1) true) init
      = { pos := if (k + 1) % 2 = 1 then .c1 else .x0, sec := true,
          run := k + 1, b := 0, anc := .x0 } := by
  induction k with
  | zero => simp [apres, pas, loquet, init]
  | succ k ih =>
    rw [rep_snoc, apres_snoc, ih]
    simp [pas, loquet]

theorem TH8 (k : Nat) :
    (apres none (List.replicate (k + 3) true) init).pos
      = (apres none (List.replicate (k + 1) true) init).pos := by
  rw [TH8_etat (k + 2), TH8_etat k]
  have : (k + 2 + 1) % 2 = (k + 1) % 2 := by omega
  simp only [this]

/-! ## TH11 — Le loquet qui force β borne toute excursion par max(n_Λ, 1)

(Le « max » est un résultat : avec n_Λ = 0, une excursion dure quand même un pas.) -/

def borne (n : Nat) (st : St) : Prop :=
  bienForme st ∧ (st.sec = true → 1 ≤ st.run ∧ st.run ≤ max n 1)

theorem TH11_pas (n : Nat) (e : Bool) (st : St) (h : borne n st) :
    borne n (pas (some n) e st) := by
  obtain ⟨hb, hr⟩ := h
  unfold borne bienForme at *
  cases hs : st.sec
  · have h0 := hb hs
    cases e <;> simp [pas, loquet, hs, h0] <;> omega
  · have ⟨h1, h2⟩ := hr hs
    cases e
    · simp [pas, loquet, hs]
    · by_cases hn : n ≤ st.run
      · simp [pas, loquet, hs, hn]
      · simp [pas, loquet, hs, hn]
        omega

theorem TH11 (n : Nat) (env : List Bool) :
    ∀ st, borne n st → borne n (apres (some n) env st) := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st h; exact ih _ (TH11_pas n e st h)

theorem TH11_depuis_init (n : Nat) (env : List Bool) :
    (apres (some n) env init).sec = true → (apres (some n) env init).run ≤ max n 1 := by
  have h := TH11 n env init ⟨fun _ => rfl, fun h => by simp [init] at h⟩
  exact fun hs => (h.2 hs).2

/-! ## TH21 (réfutation) — B0 existe, pour TOUT n_Λ

Une excursion d'un seul pas : β bloqué une fois, puis libre. T_R = 1, aucun
retour, sortie du secours. La classe B0, retirée en v1.6, est habitée. -/

theorem B0_existe (nl : Option Nat) :
    positions nl [true, false] = [.x0, .c1, .s 1]
    ∧ T_R nl [true, false] = 1
    ∧ sansRetour (positions nl [true, false])
    ∧ (apres nl [true, false] init).sec = false := by
  cases nl with
  | none => refine ⟨?_, ?_, ?_, ?_⟩ <;> simp [positions, T_R, etats, apres, pas, loquet, init, sansRetour] <;> decide
  | some n =>
    refine ⟨?_, ?_, ?_, ?_⟩ <;>
      (cases n with
       | zero => simp [positions, T_R, etats, apres, pas, loquet, init, sansRetour] <;> decide
       | succ m => simp [positions, T_R, etats, apres, pas, loquet, init, sansRetour] <;> decide)

/-! ## Invariant : tout état atteignable est bien formé -/

theorem pas_bienForme (nl : Option Nat) (e : Bool) (st : St) :
    bienForme (pas nl e st) := by
  unfold bienForme pas
  split <;> simp

theorem apres_bienForme (nl : Option Nat) (env : List Bool) :
    ∀ st, bienForme st → bienForme (apres nl env st) := by
  induction env with
  | nil => intro st h; exact h
  | cons e es ih => intro st _; exact ih _ (pas_bienForme nl e st)

theorem atteignable_bienForme (nl : Option Nat) (env : List Bool) :
    bienForme (apres nl env init) :=
  apres_bienForme nl env init (fun _ => rfl)

/-- TH9 sur toute trajectoire réelle : après n'importe quel préfixe qui laisse
    l'entité en régime saturé, deux blocages consécutifs (n_Λ ≥ 2 ou pas de
    loquet) ramènent exactement à l'objet de départ. -/
theorem TH9_trajectoire (nl : Option Nat) (h : ∀ n, nl = some n → 2 ≤ n)
    (prefixe : List Bool) (hsat : (apres nl prefixe init).sec = false) :
    (apres nl (prefixe ++ [true, true]) init).pos = (apres nl prefixe init).pos := by
  have hb := atteignable_bienForme nl prefixe hsat
  have : prefixe ++ [true, true] = (prefixe ++ [true]) ++ [true] := by simp
  rw [this, apres_snoc, apres_snoc]
  exact TH9 nl h _ hsat hb

/-! ## TH21 (réfutation, forme générale)

Pour tout n_Λ et tout t : t+1 pas saturés, UN pas bloqué, puis β libre :
l'entité ressort du secours en un seul pas, vers un objet frais s(t+2).
(L'absence de tout retour est prouvée sur le cas t = 0 par `B0_existe` ;
la forme générale de la non-répétition reste à écrire.) -/

theorem B0_general_etat (nl : Option Nat) (t : Nat) :
    apres nl (List.replicate (t + 1) false ++ [true, false]) init
      = { pos := .s (t + 2), sec := false, run := 0, b := t + 2, anc := .s (t + 1) } := by
  have : List.replicate (t + 1) false ++ [true, false]
      = (List.replicate (t + 1) false ++ [true]) ++ [false] := by simp
  rw [this, apres_snoc, apres_snoc, sature_etat]
  cases nl <;> simp [pas, loquet]

/-! ## TH23 / TH41 — T_R ne décroît jamais ; en L↑, A est hors d'atteinte

`A` exige T_R = 0. Si la dérivation commence en secours (Ω0 : captivité),
T_R ≥ 1 dès le départ et ne décroît jamais ; R-PURIF n'agit que sur R.
Donc aucune dérivation partie de Ω0 n'est jamais dans A. TH41, tel qu'écrit
dans la v4.0, est faux : il faut redéfinir A dans L↑. -/

def T_R_depuis (nl : Option Nat) (env : List Bool) (st : St) : Nat :=
  ((etats nl env st).filter (fun s => s.sec)).length

theorem T_R_depuis_secours (nl : Option Nat) (env : List Bool) (st : St)
    (h : st.sec = true) : 1 ≤ T_R_depuis nl env st := by
  cases env <;> simp [T_R_depuis, etats, h]

/-- Classe A au sens de D11–D14 : T_R = 0 et aucun retour. -/
def classeA (nl : Option Nat) (env : List Bool) (st : St) : Prop :=
  T_R_depuis nl env st = 0 ∧ ((etats nl env st).map St.pos).Nodup

/-- Ω0 : n'importe quel état de départ en secours. Avec ou sans purification
    de R, la condition T_R = 0 de A ne peut pas être satisfaite. -/
theorem TH41_refute (nl : Option Nat) (env : List Bool) (omega0 : St)
    (h : omega0.sec = true) : ¬ classeA nl env omega0 := by
  intro ⟨h0, _⟩
  have := T_R_depuis_secours nl env omega0 h
  omega

end LStar
