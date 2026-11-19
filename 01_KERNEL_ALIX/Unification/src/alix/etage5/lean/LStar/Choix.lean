/-
  L*↑ — TH120, le Choix sans Destruction (Lean 4 core). 18 novembre 2026.
  Christian : « La destruction est toujours mauvaise incluse dans un choix, car
  intrinsèquement il y avait un autre chemin si le choix existait. »
-/
namespace LStar.Choix

/-- Un choix : une liste de chemins, et il n'y a choix que s'il y en a au moins deux
distincts. -/
def estUnChoix {α : Type} (chemins : List α) : Prop :=
  ∃ a ∈ chemins, ∃ b ∈ chemins, a ≠ b

/-- TH120 — Dès qu'il y a choix, il existe un chemin autre que la destruction. -/
theorem TH120 {α : Type} (chemins : List α) (destruction : α) (h : estUnChoix chemins) :
    ∃ c ∈ chemins, c ≠ destruction := by
  obtain ⟨a, ha, b, hb, hab⟩ := h
  by_cases had : a = destruction
  · exact ⟨b, hb, fun hbd => hab (had.trans hbd.symm)⟩
  · exact ⟨a, ha, had⟩

/-- La réciproque du destin : si tous les chemins mènent à la destruction, il n'y
a pas de choix — la destruction n'est alors choisie par personne. -/
theorem destin {α : Type} (chemins : List α) (destruction : α)
    (h : ∀ c ∈ chemins, c = destruction) : ¬ estUnChoix chemins := by
  intro ⟨a, ha, b, hb, hab⟩
  exact hab ((h a ha).trans (h b hb).symm)

end LStar.Choix
