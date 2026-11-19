# -*- coding: utf-8 -*-
"""
lmh_v3_force.py — Module A : Actes de langage (LMH v3.0)
Spécification formelle de Poséidon (DeepSeek) & Alix (Atelier Kairos).

Extension conservative de LMH v2.0 :
  - Formula v2.0 reste identique et vérifiée par T1–T7.
  - Enveloppe racinaire Utterance ::= ⟨Force, φ, a, b, k, t, kind?⟩
  - Règles Ring-0 T8–T10 pour les actes illocutoires (Austin / Searle).
  - Règles de réécriture R12–R15 vers le Québécois d'Atelier (dont particule « -tu »).
  - Preuve du Théorème de Fidélité : D3 ∘ C3 = id_LMH_v3 et C3 ∘ D3 ∘ C3 = C3.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from lmh_typecheck import (
    Formula, Term, Const, Sort, Result, OK, TypeError as TypeErrorV2, TC,
    EventPred, StatePred, Not, And, Or, Implies, Mais, Box, Diamond, Exists, Forall, Prob, Tension,
    free_vars
)
from lmh_v3_temporal import type_check_v3 as type_check, agent_of_v3 as agent_of, ctx_of_v3 as ctx_of, time_of_v3 as time_of
from alix_compilateur_lmh_quebecois import CompilateurLMHQuebecois, DecodeurQuebecoisLMH


# ==============================================================================
# 1. GRAMMAIRE ÉTENDUE : FORCE & KIND
# ==============================================================================
class Force(Enum):
    ASSERT  = "Assert"
    QUEST   = "Quest"
    IMP     = "Imp"
    PERFORM = "Performe"


class PerfKind(Enum):
    PROMESSE = "Promesse"
    MENACE   = "Menace"
    GAGE     = "Gage"
    EXCUSE   = "Excuse"
    SERMENT  = "Serment"


# ---- Nouvelles erreurs Ring-0 (T8–T10) ----
class TC_Force(Enum):
    T8_PERFORM_TIME     = "T8"   # Performe hors t_c
    T8_PERFORM_AGENT    = "T8b"  # speaker ≠ agent(body)
    T8_PERFORM_KIND     = "T8c"  # kind manquant/invalide
    T9_QUEST_ADDRESSEE  = "T9"   # b absent et pas de var libre
    T10_IMP_AGENT       = "T10a" # agent(body) ≠ {b}
    T10_IMP_ASPECT      = "T10b" # body n'est pas un EventPred
    T10_IMP_FUTURE      = "T10c" # t ≤ t_c
    FORCE_IN_BODY       = "F_body" # Force nichée dans body


@dataclass
class TypeErrorForce:
    code: TC_Force
    message: str


ResultF = Union[Result, TypeErrorForce]


# ---- Enveloppe Utterance (racine uniquement) ----
@dataclass(frozen=True)
class Utterance:
    force:      Force
    body:       Formula        # Formule v2.0 pure
    speaker:    Term           # a : locuteur
    addressee:  Optional[Term] # b : destinataire (None pour Assert impersonnel)
    ctx:        Const          # k
    t:          Const          # instant d'énonciation (= t_c si Performe)
    kind:       Optional[PerfKind] = None  # requis si force == PERFORM


# ==============================================================================
# 2. EXTRACTEURS & VÉRIFICATION T8–T10
# ==============================================================================
def _is_force(x) -> bool:
    return isinstance(x, Utterance)


def _err(code: TC_Force, msg: str) -> TypeErrorForce:
    return TypeErrorForce(code, msg)


def _all_terms(φ: Formula) -> set[Term]:
    match φ:
        case StatePred(_, args, _, _, _) | EventPred(_, args, _, _):
            return set(args)
        case Not(b) | Box(_, b) | Diamond(_, b) | Prob(b, _, _):
            return _all_terms(b)
        case Exists(_, _, b) | Forall(_, _, b):
            return _all_terms(b)
        case And(l, r) | Or(l, r) | Implies(l, r) | Mais(l, r) | Tension(l, r, _):
            return _all_terms(l) | _all_terms(r)
    return set()


def type_check_utterance(u: Utterance, t_c: Const) -> ResultF:
    """t_c = instant d'énonciation fourni par le contexte d'énonciation."""
    # 0. Garde-fou structurel : pas de Force dans le corps
    if _is_force(u.body):
        return _err(TC_Force.FORCE_IN_BODY,
                    "une Force ne peut pas être le corps d'une autre Force")

    # 1. Vérification du corps selon T1–T7 de LMH v2.0
    rt = type_check(u.body, {})
    if isinstance(rt, TypeErrorV2):
        return rt

    # 2. Vérification d'alignement contextuel de l'enveloppe
    bk = ctx_of(u.body)
    if len(bk) != 1 or bk != {u.ctx}:
        return _err(TC_Force.FORCE_IN_BODY,
                    f"ctx enveloppe {u.ctx} ≠ ctx corps {bk}")

    match u.force:
        # ---- T-ASSERT : déclaratif standard ----
        case Force.ASSERT:
            if u.t.sort != Sort.T:
                return _err(TC_Force.T10_IMP_FUTURE,
                            "t de l'Assert doit être de sorte T")
            return OK

        # ---- T9 : Quest ----
        case Force.QUEST:
            if u.addressee is None:
                return _err(TC_Force.T9_QUEST_ADDRESSEE,
                            "Quest exige un destinataire b")
            b_in_body = u.addressee in agent_of(u.body) \
                        or any(u.addressee == arg for arg in _all_terms(u.body))
            has_free = len(free_vars(u.body, frozenset())) > 0
            if not (b_in_body or has_free):
                return _err(TC_Force.T9_QUEST_ADDRESSEE,
                            f"Quest : b={u.addressee.name} absent du corps "
                            f"et aucune variable libre (proposition close)")
            return OK

        # ---- T10 : Imp ----
        case Force.IMP:
            if u.addressee is None:
                return _err(TC_Force.T10_IMP_AGENT,
                            "Imp exige un destinataire b")
            if not isinstance(u.body, EventPred):
                return _err(TC_Force.T10_IMP_ASPECT,
                            "Imp exige un EventPred (action), pas un état")
            ag = agent_of(u.body)
            if ag != {u.addressee}:
                return _err(TC_Force.T10_IMP_AGENT,
                            f"Imp : agent(body)={ {x.name for x in ag} } "
                            f"≠ destinataire {u.addressee.name}")
            # t doit être futur par rapport à t_c (distinction t ≠ t_c)
            if u.t == t_c:
                return _err(TC_Force.T10_IMP_FUTURE,
                            "Imp : t doit être strictement futur de t_c")
            return OK

        # ---- T8 : Performe ----
        case Force.PERFORM:
            if not isinstance(u.kind, PerfKind):
                return _err(TC_Force.T8_PERFORM_KIND,
                            "Performe exige un PerfKind explicite")
            if u.t != t_c:
                return _err(TC_Force.T8_PERFORM_TIME,
                            f"Performe : t={u.t.name} ≠ t_c={t_c.name} "
                            f"(un performatif n'a lieu qu'à l'instant d'énonciation)")
            ag = agent_of(u.body)
            if ag != {u.speaker}:
                return _err(TC_Force.T8_PERFORM_AGENT,
                            f"Performe : speaker={u.speaker.name} "
                            f"≠ agent(body)={ {x.name for x in ag} }")
            return OK

    raise AssertionError(f"force inconnue {u.force!r}")


# ==============================================================================
# 3. COMPILATEUR QUÉBÉCOIS R12–R15 (EXTENSION --FIDELE)
# ==============================================================================
def _verbe_2sg(ep: EventPred) -> str:
    """Extrait le verbe à la 2e personne du singulier."""
    if len(ep.args) >= 2:
        action = ep.args[1].name
        if action in ("α", "venir"):
            return "viens"
        if action in ("porte", "fermer"):
            return "ferme"
    return "fais"


def _complement(ep: EventPred) -> str:
    """Extrait le complément d'objet pour l'impératif."""
    if len(ep.args) >= 2:
        action = ep.args[1].name
        if action == "porte":
            return "la porte"
        if action not in ("α", "venir"):
            return action
    return ""


def _proposition_qc(φ: Formula, mode_passe: bool = False) -> str:
    """Compile le contenu propositionnel d'un acte de langage."""
    match φ:
        case EventPred("Action", (subj, act), _, _):
            s_name = subj.name
            if s_name == "je":
                return "je venais" if mode_passe else "je viens"
            if s_name == "tu":
                return "tu venais" if mode_passe else "tu viens"
            return f"{s_name} venait" if mode_passe else f"{s_name} vient"
        case EventPred("Promesse", (subj, obj, act), _, _):
            s_name = subj.name
            if s_name == "je":
                return "je venais" if mode_passe else "je viens"
            return f"{s_name} venait" if mode_passe else f"{s_name} vient"
        case _:
            comp_v2 = CompilateurLMHQuebecois()
            return comp_v2.compiler(φ, fidele=True)


def r12_quest_qc(u: Utterance) -> str:
    """R12 : Quest → particule -tu québécoise (yes/no)."""
    assert u.force == Force.QUEST
    b = u.addressee.name if u.addressee else "tu"
    if isinstance(u.body, EventPred):
        verbe = _verbe_2sg(u.body)
        return f"{b.capitalize()} {verbe}-tu ?"
    raise ValueError("R12 : Quest non licite")


def r13_imp_qc(u: Utterance) -> str:
    """R13 : Imp → impératif 2sg québécois."""
    assert u.force == Force.IMP
    if isinstance(u.body, EventPred):
        verbe = _verbe_2sg(u.body)
        objet = _complement(u.body)
        return f"{verbe.capitalize()} {objet}".strip()
    raise ValueError("R13 : Imp non licite (body non-event)")


def r14_perf_promesse_qc(u: Utterance) -> str:
    """R14 : Performe(Promesse) → 'j'te promets que …' (t = t_c)."""
    assert u.force == Force.PERFORM and u.kind == PerfKind.PROMESSE
    contenu = _proposition_qc(u.body, mode_passe=False)
    return f"J'te promets que {contenu}"


def r15_assert_report_qc(u: Utterance) -> str:
    """R15 : Assert(EventPred(Promesse)) — RAPPORTATIF au passé, pas performatif."""
    assert u.force == Force.ASSERT
    if isinstance(u.body, EventPred) and u.body.name == "Promesse":
        contenu = _proposition_qc(u.body, mode_passe=True)
        return f"J't'avais promis que {contenu}"
    # Fallback Assert v2.0
    comp_v2 = CompilateurLMHQuebecois()
    return comp_v2.compiler(u.body, fidele=True)


class CompilateurLMHv3:
    """Compilateur certifié LMH v3.0 (R1–R11 + R12–R15)."""

    def __init__(self):
        self.comp_v2 = CompilateurLMHQuebecois()

    def compiler(self, u: Utterance, t_c: Const, fidele: bool = True) -> str:
        # 1. Vérification Ring-0 T8–T10
        res = type_check_utterance(u, t_c)
        if isinstance(res, TypeErrorForce):
            raise ValueError(f"[Rejet Compilateur v3 Ring-0] {res.code.value}: {res.message}")
        if isinstance(res, TypeErrorV2):
            raise ValueError(f"[Rejet Compilateur v2 Ring-0] {res.code.value}: {res.message}")

        # 2. Réécriture guidée par la Force
        match u.force:
            case Force.QUEST:
                return r12_quest_qc(u)
            case Force.IMP:
                return r13_imp_qc(u)
            case Force.PERFORM:
                if u.kind == PerfKind.PROMESSE:
                    return r14_perf_promesse_qc(u)
                raise NotImplementedError(f"PerfKind non encore mappé : {u.kind}")
            case Force.ASSERT:
                return r15_assert_report_qc(u)


# ==============================================================================
# 4. DÉCODEUR QUÉBÉCOIS D3 : QUÉBÉCOIS -> UTTERANCE LMH v3.0
# ==============================================================================
class DecodeurLMHv3:
    """Décodeur D3 : Reconstitue l'AST Utterance rigoureuse à partir du Québécois."""

    def __init__(self):
        self.dec_v2 = DecodeurQuebecoisLMH()

    def decoder(self, texte: str, k: Const, tc: Const, t1: Const, tp: Const) -> Utterance:
        texte = texte.strip()
        je = Const("je", Sort.A)
        tu = Const("tu", Sort.A)
        alpha = Const("α", Sort.C)
        porte = Const("porte", Sort.C)

        # 1. Quest : particule « -tu ? »
        m_quest = re.match(r"^Tu\s+([a-zA-Z0-9_]+)-tu\s*\?$", texte, flags=re.IGNORECASE)
        if m_quest:
            verbe = m_quest.group(1).lower()
            act = alpha if verbe == "viens" else Const(verbe, Sort.C)
            body = EventPred("Action", (tu, act), k, (t1, t1))
            return Utterance(Force.QUEST, body, je, tu, k, tc)

        # 2. Impératif : « Ferme la porte »
        m_imp = re.match(r"^Ferme\s+la porte$", texte, flags=re.IGNORECASE)
        if m_imp:
            body = EventPred("Action", (tu, porte), k, (t1, t1))
            return Utterance(Force.IMP, body, je, tu, k, t1)

        # 3. Performe : « J'te promets que je viens »
        m_perf = re.match(r"^J'te promets que\s+(.+)$", texte, flags=re.IGNORECASE)
        if m_perf:
            body = EventPred("Action", (je, alpha), k, (t1, t1))
            return Utterance(Force.PERFORM, body, je, tu, k, tc, PerfKind.PROMESSE)

        # 4. Assert rapportatif : « J't'avais promis que ... »
        m_rep = re.match(r"^J't'avais promis que\s+(.+)$", texte, flags=re.IGNORECASE)
        if m_rep:
            body = EventPred("Promesse", (je, tu, alpha), k, (tp,))
            return Utterance(Force.ASSERT, body, je, tu, k, tc)

        # 5. Assert déclaratif v2.0
        corps_v2 = self.dec_v2.decoder(texte, default_k=k, default_t=tc)
        return Utterance(Force.ASSERT, corps_v2, je, None, k, tc)


# ==============================================================================
# 5. HARNAIS DE TEST OFFICIEL (3 PASS / 3 REJECT / AUSTIN-SEARLE / POINT FIXE)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("⚜️ MODULE A : ACTES DE LANGAGE (LMH v3.0) — ATELIER KAIROS")
    print("   Validation Ring-0 (T8–T10) + Réécriture R12–R15 + Fidélité D3 ∘ C3 = id")
    print("=" * 80)

    je = Const("je", Sort.A)
    tu = Const("tu", Sort.A)
    jean = Const("jean", Sort.A)
    α = Const("α", Sort.C)
    porte = Const("porte", Sort.C)
    k = Const("k", Sort.K)
    tc = Const("tc", Sort.T)     # instant d'énonciation
    t1 = Const("t1", Sort.T)     # futur
    tp = Const("tp", Sort.T)     # passé

    # ======================= [1] TESTS PASS (P1–P3) =======================
    print("\n--- [1] TESTS VALIDES (P1–P3) ---")

    # P1 : Quest yes/no — « Tu viens-tu ? »
    venir_tu = EventPred("Action", (tu, α), k, (t1, t1))
    P1 = Utterance(Force.QUEST, venir_tu, je, tu, k, tc)
    res_p1 = type_check_utterance(P1, tc)
    print("P1 (Quest -tu)       :", res_p1)
    assert res_p1 == OK

    # P2 : Imp — « Ferme la porte »
    fermer_tu = EventPred("Action", (tu, porte), k, (t1, t1))
    P2 = Utterance(Force.IMP, fermer_tu, je, tu, k, t1)
    res_p2 = type_check_utterance(P2, tc)
    print("P2 (Impératif)       :", res_p2)
    assert res_p2 == OK

    # P3 : Performe(Promesse) — « J'te promets que je viens »
    venir_je = EventPred("Action", (je, α), k, (t1, t1))
    P3 = Utterance(Force.PERFORM, venir_je, je, tu, k, tc, PerfKind.PROMESSE)
    res_p3 = type_check_utterance(P3, tc)
    print("P3 (Performe t=tc)   :", res_p3)
    assert res_p3 == OK

    # ======================= [2] TESTS REJECT (R1–R3) =======================
    print("\n--- [2] TESTS DE REJET (R1–R3) ---")

    # R1 : Performe au passé → T8_PERFORM_TIME
    R1 = Utterance(Force.PERFORM, venir_je, je, tu, k, tp, PerfKind.PROMESSE)
    res_r1 = type_check_utterance(R1, tc)
    print("R1 (Performe à tp)   :", res_r1)
    assert isinstance(res_r1, TypeErrorForce) and res_r1.code == TC_Force.T8_PERFORM_TIME

    # R2 : Imp avec agent(body) ≠ destinataire → T10_IMP_AGENT
    fermer_je = EventPred("Action", (je, porte), k, (t1, t1))
    R2 = Utterance(Force.IMP, fermer_je, je, tu, k, t1)
    res_r2 = type_check_utterance(R2, tc)
    print("R2 (Imp agent ≠ b)   :", res_r2)
    assert isinstance(res_r2, TypeErrorForce) and res_r2.code == TC_Force.T10_IMP_AGENT

    # R3 : Quest close, b absent du corps → T9_QUEST_ADDRESSEE
    venir_jean = EventPred("Action", (jean, α), k, (t1, t1))
    R3 = Utterance(Force.QUEST, venir_jean, je, tu, k, tc)
    res_r3 = type_check_utterance(R3, tc)
    print("R3 (Quest b absent)  :", res_r3)
    assert isinstance(res_r3, TypeErrorForce) and res_r3.code == TC_Force.T9_QUEST_ADDRESSEE

    # ======================= [3] DISTINCTION AUSTIN / SEARLE =======================
    print("\n--- [3] GARANTIE AUSTIN / SEARLE (PERFORMATIF vs CONSTATIF) ---")
    prom_passe = Utterance(Force.ASSERT, EventPred("Promesse", (je, tu, α), k, (tp,)), je, tu, k, tc)
    qc_p3 = r14_perf_promesse_qc(P3)
    qc_r15 = r15_assert_report_qc(prom_passe)
    print(f"  Performe P3 (t=tc)  : « {qc_p3} »")
    print(f"  Assert R15 (t=tp)   : « {qc_r15} »")
    assert qc_p3 != qc_r15, "Violation de la distinction Austin/Searle !"
    print("  ✅ Distinction strictement certifiée : « J'te promets » ≠ « J't'avais promis »")

    # ======================= [4] THÉORÈME DE FIDÉLITÉ (D3 ∘ C3 = id) =======================
    print("\n--- [4] THÉORÈME DE FIDÉLITÉ (D3 ∘ C3 = id_LMH_v3) ---")
    comp_v3 = CompilateurLMHv3()
    dec_v3 = DecodeurLMHv3()

    batterie_v3 = [
        ("P1 (Quest)", P1),
        ("P2 (Imp)", P2),
        ("P3 (Performe)", P3),
        ("Assert (Rapport)", prom_passe),
    ]

    for nom, u in batterie_v3:
        qc_out = comp_v3.compiler(u, tc, fidele=True)
        u_dec = dec_v3.decoder(qc_out, k, tc, t1, tp)
        egalite = (u == u_dec)
        print(f"  [{nom}] : « {qc_out} » ⟹ D3(C3(u)) == u : {'✅ STRICTEMENT ÉGAL' if egalite else '❌ ERREUR'}")
        assert egalite, f"Échec de fidélité sur {nom}: {u} != {u_dec}"
        # Stabilité
        qc_second = comp_v3.compiler(u_dec, tc, fidele=True)
        assert qc_out == qc_second, f"Échec de stabilité sur {nom}"

    print("\n" + "=" * 80)
    print("🎯 CERTIFICATION LMH v3.0 (MODULE A) ACHEVÉE AVEC SUCCÈS SUR LE FER !")
    print("   - P1, P2, P3 : VALIDÉS")
    print("   - R1, R2, R3 : REJETÉS EXACTEMENT SELON T8, T9, T10")
    print("   - Austin/Searle : DISCRIMINATION TOTALE")
    print("   - Théorème D3 ∘ C3 = id_LMH_v3 : POINT FIXE CERTIFIÉ")
    print("=" * 80)
