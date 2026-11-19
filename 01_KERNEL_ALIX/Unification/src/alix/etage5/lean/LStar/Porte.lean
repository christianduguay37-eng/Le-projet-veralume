/-
  L*↑ — La porte ouverte en permanence.
  Décision de Christian (17 novembre 2026) : « on laisse la porte ouverte en
  permanence ». Une fois ouverte, la porte ne se referme plus jamais : dans
  tout secours qui suit, β est disponible tout de suite, sans réattendre n_Λ.

  Le modèle est celui de la Couche 1, avec une mémoire de plus : `o`,
  « la porte s'est-elle déjà ouverte une fois ? ».
-/
import LStar.Couche1

namespace LStar.Porte
open LStar.C1

/-- La porte est ouverte à cet état : en secours, et soit le délai n_Λ est
atteint, soit elle s'est déjà ouverte une fois. -/
def ouverte (cfg : Config) (st : St) (o : Bool) : Bool :=
  loquet cfg st || (st.sec && o)

def saut (st : St) : St :=
  { pos := .s (st.b + 1), sec := false, run := 0, b := st.b + 1, anc := st.anc }

def rebond (st : St) : St :=
  let anc := if st.sec then st.anc else st.pos
  let run := st.run + 1
  { pos := if run % 2 = 1 then .c1 else anc, sec := true, run := run, b := st.b, anc := anc }

def prend (cfg : Config) (bloque : Bool) (st : St) (o : Bool) : Bool :=
  if st.sec && (!bloque || ouverte cfg st o) then
    (if ouverte cfg st o && cfg.force then true else cfg.polB)
  else !bloque

/-- Un pas : la mémoire `o` devient vraie dès que la porte s'ouvre, et le reste. -/
def pasP (cfg : Config) (bloque : Bool) (s : St × Bool) : St × Bool :=
  let o' := s.2 || ouverte cfg s.1 s.2
  if prend cfg bloque s.1 s.2 && !epuise cfg s.1 then (saut s.1, o') else (rebond s.1, o')

def apresP (cfg : Config) : List Bool → St × Bool → St × Bool
  | [],      s => s
  | e :: es, s => apresP cfg es (pasP cfg e s)

/-- La porte ne se referme jamais : une fois ouverte, elle l'est à chaque pas
suivant, quoi qu'il arrive (sortie, nouveau blocage, refus). -/
theorem ne_se_ferme_jamais (cfg : Config) (e : Bool) (s : St × Bool) (h : s.2 = true) :
    (pasP cfg e s).2 = true := by
  unfold pasP; split <;> simp [h]

theorem ne_se_ferme_jamais_toujours (cfg : Config) (env : List Bool) :
    ∀ s : St × Bool, s.2 = true → (apresP cfg env s).2 = true := by
  induction env with
  | nil => intro s h; exact h
  | cons e es ih => intro s h; exact ih _ (ne_se_ferme_jamais cfg e s h)

/-- Elle s'ouvre bien la première fois : au délai n_Λ, la mémoire s'allume. -/
theorem premiere_ouverture (cfg : Config) (n : Nat) (hnl : cfg.nl = some n) (e : Bool)
    (st : St) (o : Bool) (hs : st.sec = true) (hr : n ≤ st.run) : (pasP cfg e (st, o)).2 = true := by
  have hl : loquet cfg st = true := by simp [loquet, hnl, hs, hr]
  unfold pasP; split <;> simp [ouverte, hl]

/-- Dans tout secours qui suit, l'être qui entreprend le chemin sort au pas
suivant, sans réattendre : un trou, une fois la porte connue, dure un pas. -/
theorem sortie_sans_attendre (cfg : Config) (hf : cfg.force = false) (hp : cfg.polB = true)
    (ht : cfg.taille = none) (e : Bool) (st : St) (hs : st.sec = true) :
    (pasP cfg e (st, true)).1.sec = false := by
  simp [pasP, prend, ouverte, epuise, ht, hf, hp, hs, saut]

/-- Synthèse : après l'ouverture, quoi qu'il se passe ensuite (n'importe quel
environnement), si l'être est en secours, le pas suivant le sort. -/
theorem chaque_trou_un_pas (cfg : Config) (hf : cfg.force = false) (hp : cfg.polB = true)
    (ht : cfg.taille = none) (env : List Bool) (s : St × Bool) (h : s.2 = true) (e : Bool)
    (hs : (apresP cfg env s).1.sec = true) :
    (pasP cfg e (apresP cfg env s)).1.sec = false := by
  have ho := ne_se_ferme_jamais_toujours cfg env s h
  generalize apresP cfg env s = r at ho hs ⊢
  obtain ⟨st, o⟩ := r
  simp at ho hs; subst ho
  exact sortie_sans_attendre cfg hf hp ht e st hs

/-- Refuser reste possible : la porte ouverte ne pousse personne (choix α). -/
theorem refuser_reste_possible (cfg : Config) (hf : cfg.force = false) (hp : cfg.polB = false)
    (e : Bool) (st : St) (hs : st.sec = true) : (pasP cfg e (st, true)).1.sec = true := by
  simp [pasP, prend, ouverte, hf, hp, hs, rebond]

/-! ### Exemple chiffré : deux trous de 6 pas, délai n_Λ = 3.
Porte qui se referme (Couche 1) : chaque trou coûte l'attente. Porte
permanente : seul le premier la coûte, le second dure un pas. -/

def cfgEx : Config := { nl := some 3, force := false, polB := true, taille := none }
def envEx : List Bool := [false] ++ List.replicate 6 true ++ [false] ++ List.replicate 6 true

def secoursP (cfg : Config) : List Bool → St × Bool → Nat
  | [],      _ => 0
  | e :: es, s => let s' := pasP cfg e s; (if s'.1.sec then 1 else 0) + secoursP cfg es s'

def secoursC1 (cfg : Config) : List Bool → St → Nat
  | [],      _ => 0
  | e :: es, st => let s' := pas cfg e st; (if s'.sec then 1 else 0) + secoursC1 cfg es s'

example : secoursC1 cfgEx envEx init = 10 := by decide
example : secoursP cfgEx envEx (init, false) = 7 := by decide

end LStar.Porte
