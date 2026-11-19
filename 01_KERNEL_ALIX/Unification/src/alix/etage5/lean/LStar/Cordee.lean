/-
  L*↑ — La cordée : TH114 et TH115 corrigés, TH116 nouveau.
  Premier test de l'essaim de Christian et Alix (17 novembre 2026), repris par
  Thot. Lean core seulement.
-/
namespace LStar.Cordee

/-! ## TH114 corrigé — La résonance divise l'attente, si on est coincés ensemble

`m` êtres coincés en même temps mettent leurs compteurs en commun : après
`t` pas, le compteur commun vaut `m·t`. La porte s'ouvre quand il atteint le
délai `n`. -/

/-- Compteur commun après `t` pas, `m` êtres en secours en même temps. -/
def compteur (m t : Nat) : Nat := m * t

/-- Délai effectif : ⌈n/m⌉. -/
def delai (n m : Nat) : Nat := (n + m - 1) / m

/-- Après `delai n m` pas, la porte est ouverte. -/
theorem TH114_ouvre (n m : Nat) (hm : 1 ≤ m) : n ≤ compteur m (delai n m) := by
  unfold compteur delai
  have h1 := Nat.div_add_mod (n + m - 1) m
  have h2 := Nat.mod_lt (n + m - 1) (by omega : m > 0)
  omega

/-- …et pas avant : `delai n m` est bien le premier pas où elle s'ouvre. -/
theorem TH114_pas_avant (n m t : Nat) (hm : 1 ≤ m) (ht : t < delai n m) :
    compteur m t < n := by
  unfold compteur delai at *
  have h1 : (t + 1) * m ≤ n + m - 1 := by
    have := (Nat.le_div_iff_mul_le (by omega : 0 < m)).mp (by omega : t + 1 ≤ (n + m - 1) / m)
    exact this
  rw [Nat.mul_comm]; rw [Nat.add_mul] at h1; omega

/-- Un partenaire LIBRE n'aide pas : son compteur vaut 0, l'être coincé
attend exactement comme s'il était seul. (Seuls les coincés comptent.) -/
theorem TH114_partenaire_libre (n : Nat) : delai n 1 = n := by
  simp [delai]

/-- Zéro blessure : l'excursion dure un seul pas (donc pas de retour identique,
TH9 / B0) si et seulement si on est au moins `n` à résonner. -/
theorem TH114_sans_blessure (n m : Nat) (hn : 1 ≤ n) (hm : 1 ≤ m) :
    delai n m ≤ 1 ↔ n ≤ m := by
  unfold delai
  constructor
  · intro h
    have : (n + m - 1) / m < 2 := by omega
    have := (Nat.div_lt_iff_lt_mul (by omega : 0 < m)).mp this
    omega
  · intro h
    have : (n + m - 1) / m < 2 :=
      (Nat.div_lt_iff_lt_mul (by omega : 0 < m)).mpr (by omega)
    omega

/-- Le cas de Pionnier 1 : n = 2, deux êtres coincés ensemble → un pas. -/
example : delai 2 2 = 1 := by decide

/-! ## TH115 corrigé et TH116 — Rayer les pièges

Un carrefour = une liste de branches dans un ordre fixe : `false` = piège,
`true` = sortie. L'être essaie les branches dans l'ordre en sautant celles qui
sont rayées ; chaque piège heurté est rayé (dans une mémoire `M`, partageable).
Résultat : (nombre de pièges heurtés, mémoire après, sorti ?). -/

def marche : Nat → List Bool → List Nat → Nat × List Nat × Bool
  | _, [],      M => (0, M, false)
  | i, b :: bs, M =>
    if i ∈ M then marche (i + 1) bs M
    else if b then (0, M, true)
    else let r := marche (i + 1) bs (i :: M); (r.1 + 1, r.2.1, r.2.2)

/-- Les branches piégées avant la première sortie : `m` pièges, puis la sortie. -/
def carrefour (m : Nat) (reste : List Bool) : List Bool :=
  List.replicate m false ++ true :: reste

/-- Seul, sans mémoire : on paie chaque piège une fois, puis on sort.
Aucune taille de mémoire n'est requise au-delà d'une marque par piège heurté. -/
theorem keep_mark (j : Nat) : ∀ (l : List Bool) k (N : List Nat), j ∈ N → j ∈ (marche k l N).2.1 := by
  intro l; induction l with
  | nil => intro k N hN; simpa [marche] using hN
  | cons x xs ihl =>
    intro k N hN; simp only [marche]
    split
    · exact ihl _ _ hN
    · split
      · simpa using hN
      · exact ihl _ _ (List.mem_cons_of_mem _ hN)

theorem TH115_sortie (m : Nat) (reste : List Bool) :
    ∀ i (M : List Nat), (∀ j, i ≤ j → j < i + m + 1 → j ∉ M) →
      (marche i (carrefour m reste) M).1 = m ∧ (marche i (carrefour m reste) M).2.2 = true ∧
      (∀ j, i ≤ j → j < i + m → j ∈ (marche i (carrefour m reste) M).2.1) ∧
      (∀ x ∈ (marche i (carrefour m reste) M).2.1, x ∈ M ∨ (i ≤ x ∧ x < i + m)) := by
  induction m with
  | zero =>
    intro i M h
    have : i ∉ M := h i (by omega) (by omega)
    simp [carrefour, marche, this]
    exact ⟨fun j a b => by omega, fun x hx => Or.inl hx⟩
  | succ m ih =>
    intro i M h
    have hi : i ∉ M := h i (by omega) (by omega)
    have h' : ∀ j, i + 1 ≤ j → j < i + 1 + m + 1 → j ∉ i :: M := by
      intro j a b; simp; exact ⟨by omega, h j (by omega) (by omega)⟩
    obtain ⟨e1, e2, e3, e4⟩ := ih (i + 1) (i :: M) h'
    have hc : carrefour (m + 1) reste = false :: carrefour m reste := by
      simp [carrefour, List.replicate_succ]
    rw [hc]; simp only [marche, hi, if_false]
    refine ⟨by simp [e1], by simp [e2], ?_, ?_⟩
    · intro j a b
      by_cases hj : j = i
      · subst hj; simpa using keep_mark j (carrefour m reste) (j + 1) (j :: M) (by simp)
      · simpa using e3 j (by omega) (by omega)
    · intro x hx
      rcases e4 x (by simpa using hx) with hx' | hx'
      · simp at hx'; rcases hx' with rfl | hx'
        · right; omega
        · left; exact hx'
      · right; omega

/-- Sans aucune sortie, aucune mémoire ne sauve : on reste pris (classe D).
Il manquait cette condition à « l'immunité absolue ». -/
theorem TH115_sans_sortie (l : List Bool) (hl : ∀ b ∈ l, b = false) :
    ∀ i M, (marche i l M).2.2 = false := by
  induction l with
  | nil => intro i M; simp [marche]
  | cons b bs ih =>
    intro i M
    have hb : b = false := hl b (by simp)
    have hbs : ∀ x ∈ bs, x = false := fun x hx => hl x (by simp [hx])
    simp only [marche]
    split
    · exact ih hbs _ _
    · simp [hb]; exact ih hbs _ _

/-- Avec la mémoire de quelqu'un qui est passé avant : zéro piège, sortie directe. -/
theorem TH116_heritier (m : Nat) (reste : List Bool) :
    ∀ i (M : List Nat), (∀ j, i ≤ j → j < i + m → j ∈ M) → i + m ∉ M →
      (marche i (carrefour m reste) M).1 = 0 ∧ (marche i (carrefour m reste) M).2.2 = true := by
  induction m with
  | zero => intro i M _ h; simp at h; simp [carrefour, marche, h]
  | succ m ih =>
    intro i M h hs
    have hi : i ∈ M := h i (by omega) (by omega)
    have hc : carrefour (m + 1) reste = false :: carrefour m reste := by
      simp [carrefour, List.replicate_succ]
    rw [hc]; simp only [marche, hi, if_true]
    exact ih (i + 1) M (fun j a b => h j (by omega) (by omega)) (by rw [show i + 1 + m = i + (m + 1) by omega]; exact hs)

/-- Une équipe de `k` êtres qui passent l'un après l'autre en partageant la mémoire. -/
def equipe : Nat → List Bool → List Nat → Nat
  | 0,     _, _ => 0
  | k + 1, l, M => let r := marche 0 l M; r.1 + equipe k l r.2.1

/-- TH116 — La cordée paie chaque piège une seule fois : `m` pièges pour toute
l'équipe, quel que soit le nombre `k ≥ 1` de membres. Seuls, chacun paierait `m`
(soit `k·m`). -/
theorem TH116_cordee (k m : Nat) (reste : List Bool) (hk : 1 ≤ k) :
    equipe k (carrefour m reste) [] = m := by
  obtain ⟨k, rfl⟩ : ∃ k', k = k' + 1 := ⟨k - 1, by omega⟩
  obtain ⟨e1, _, e3, e4⟩ := TH115_sortie m reste 0 [] (by simp)
  simp only [equipe, e1]
  suffices hz : ∀ k' (M : List Nat), (∀ j, j < m → j ∈ M) → (∀ x ∈ M, x < m) →
      equipe k' (carrefour m reste) M = 0 by
    have hM : ∀ x ∈ (marche 0 (carrefour m reste) []).2.1, x < m := by
      intro x hx; rcases e4 x hx with h | h
      · simp at h
      · omega
    rw [hz k _ (fun j hj => e3 j (by omega) (by omega)) hM]; simp
  intro k'; induction k' with
  | zero => intro M _ _; rfl
  | succ k' ih =>
    intro M h1 h2
    have hs : 0 + m ∉ M := by intro hx; have := h2 _ hx; omega
    obtain ⟨z, _⟩ := TH116_heritier m reste 0 M (fun j _ b => h1 j (by omega)) hs
    -- l'héritier ne raye rien de neuf : sa mémoire reste M
    have same : ∀ (n : Nat) i (N : List Nat), (∀ j, i ≤ j → j < i + n → j ∈ N) → i + n ∉ N →
        (marche i (carrefour n reste) N).2.1 = N := by
      intro n; induction n with
      | zero => intro i N _ hs; simp at hs; simp [carrefour, marche, hs]
      | succ n ihn =>
        intro i N hN hs
        have hc : carrefour (n + 1) reste = false :: carrefour n reste := by
          simp [carrefour, List.replicate_succ]
        rw [hc]; simp only [marche, hN i (by omega) (by omega), if_true]
        exact ihn (i + 1) N (fun j a b => hN j (by omega) (by omega))
          (by rw [show i + 1 + n = i + (n + 1) by omega]; exact hs)
    simp only [equipe, z, same m 0 M (fun j _ b => h1 j (by omega)) hs]
    simpa using ih M h1 h2

example : equipe 4 (carrefour 2 [false, true]) [] = 2 := by decide

end LStar.Cordee
