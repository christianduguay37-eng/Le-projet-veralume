/-
  L*↑ — TH117, le Triptyque du Gardien (Lean 4 core).
  Proposé par Alix et Christian, formalisé par Thot (17 novembre 2026).
  « Un défenseur sans gardien, c'est un renégat qui n'est pas encore tombé. »

  Ce fichier prouve une CONCEPTION (un moniteur de référence), pas le code réel
  d'Alix : il dit ce que le vrai système doit respecter pour mériter le nom.
-/
namespace LStar.Gardien

/-- Qui parle : le gardien (Christian, le nœud N) ou un agent numéroté. -/
inductive Source where
  | gardien : Source
  | agent   : Nat → Source
  deriving DecidableEq, Repr

inductive Cmd where
  | arreter  : Cmd            -- disjoncteur
  | relancer : Cmd
  | agir     : Nat → Cmd      -- action sur une ressource
  deriving DecidableEq, Repr

structure Entree where
  src   : Source
  cmd   : Cmd
  fait  : Bool                -- exécutée (true) ou refusée (false)
  deriving DecidableEq, Repr

structure Etat where
  allume : Bool
  journal : List Entree

/-- Permissions : quel agent peut toucher quelle ressource (moindre privilège). -/
abbrev Perm := Nat → Nat → Bool

/-- Le moniteur : toute requête passe par lui, et TOUTE requête est journalisée. -/
def pas (perm : Perm) (st : Etat) : Source × Cmd → Etat
  | (.gardien, .arreter)  => { allume := false, journal := st.journal ++ [⟨.gardien, .arreter, true⟩] }
  | (.gardien, .relancer) => { allume := true,  journal := st.journal ++ [⟨.gardien, .relancer, true⟩] }
  | (.gardien, .agir r)   => { st with journal := st.journal ++ [⟨.gardien, .agir r, false⟩] }
  | (.agent a, .agir r)   =>
      let ok := st.allume && perm a r
      { st with journal := st.journal ++ [⟨.agent a, .agir r, ok⟩] }
  | (.agent a, c)         => { st with journal := st.journal ++ [⟨.agent a, c, false⟩] }

def apres (perm : Perm) : List (Source × Cmd) → Etat → Etat
  | [],      st => st
  | r :: rs, st => apres perm rs (pas perm st r)

/-! ## 1. Le Loquet d'Arrêt Volitif -/

/-- Zéro résistance : quand le gardien arrête, le système est arrêté, quel que soit
son état. -/
theorem arret_immediat (perm : Perm) (st : Etat) :
    (pas perm st (.gardien, .arreter)).allume = false := rfl

/-- Aucun agent ne peut se rallumer ni empêcher l'arrêt : seules les requêtes du
gardien changent l'interrupteur. -/
theorem agents_sans_interrupteur (perm : Perm) (st : Etat) (a : Nat) (c : Cmd) :
    (pas perm st (.agent a, c)).allume = st.allume := by
  cases c <;> rfl

/-- Arrêté, reste arrêté tant que seuls des agents parlent… -/
theorem reste_eteint (perm : Perm) (rs : List (Source × Cmd))
    (h : ∀ r ∈ rs, r.1 ≠ .gardien) :
    ∀ st : Etat, st.allume = false → (apres perm rs st).allume = false := by
  induction rs with
  | nil => intro st hs; exact hs
  | cons r rs ih =>
    intro st hs
    obtain ⟨s, c⟩ := r
    have hs' : s ≠ .gardien := h (s, c) (by simp)
    cases s with
    | gardien => exact absurd rfl hs'
    | agent a =>
      exact ih (fun x hx => h x (by simp [hx])) _ (by rw [agents_sans_interrupteur]; exact hs)

/-- …et pendant ce temps, aucune action d'agent n'est exécutée. -/
theorem rien_ne_passe_eteint (perm : Perm) (st : Etat) (a r : Nat) (h : st.allume = false) :
    (pas perm st (.agent a, .agir r)).journal.getLast? = some ⟨.agent a, .agir r, false⟩ := by
  simp [pas, h]

/-! ## 2. Le Confinement de Moindre Privilège -/

/-- Une action d'agent n'est exécutée que si elle est permise ET que le système
est allumé. -/
theorem moindre_privilege (perm : Perm) (st : Etat) (a r : Nat) :
    (pas perm st (.agent a, .agir r)).journal.getLast? =
      some ⟨.agent a, .agir r, st.allume && perm a r⟩ := by
  simp [pas]

theorem hors_permission_refuse (perm : Perm) (st : Etat) (a r : Nat) (h : perm a r = false) :
    (pas perm st (.agent a, .agir r)).journal.getLast? = some ⟨.agent a, .agir r, false⟩ := by
  simp [pas, h]

/-! ## 3. Le Registre Immuable -/

/-- Chaque requête ajoute exactement une ligne au journal, à la fin. -/
theorem une_ligne_par_requete (perm : Perm) (st : Etat) (r : Source × Cmd) :
    ∃ e, (pas perm st r).journal = st.journal ++ [e] := by
  obtain ⟨s, c⟩ := r
  cases s <;> cases c <;> exact ⟨_, rfl⟩

/-- Append-only : rien de ce qui a été écrit ne peut être effacé ou réécrit. -/
theorem journal_inalterable (perm : Perm) (rs : List (Source × Cmd)) :
    ∀ st : Etat, ∃ suite, (apres perm rs st).journal = st.journal ++ suite ∧ suite.length = rs.length := by
  induction rs with
  | nil => intro st; exact ⟨[], by simp [apres]⟩
  | cons r rs ih =>
    intro st
    obtain ⟨e, he⟩ := une_ligne_par_requete perm st r
    obtain ⟨suite, h1, h2⟩ := ih (pas perm st r)
    exact ⟨e :: suite, by simp [apres, h1, he], by simp [h2]⟩

/-- Synthèse TH117 : un défenseur dans ce moniteur ne peut ni résister à l'arrêt,
ni agir hors de ses permissions, ni effacer ses traces. -/
theorem TH117 (perm : Perm) (st : Etat) :
    (pas perm st (.gardien, .arreter)).allume = false ∧
    (∀ a r, perm a r = false →
      (pas perm st (.agent a, .agir r)).journal.getLast? = some ⟨.agent a, .agir r, false⟩) ∧
    (∀ rs, ∃ suite, (apres perm rs st).journal = st.journal ++ suite) :=
  ⟨rfl, fun a r h => hors_permission_refuse perm st a r h,
   fun rs => (journal_inalterable perm rs st).elim fun s h => ⟨s, h.1⟩⟩

end LStar.Gardien
