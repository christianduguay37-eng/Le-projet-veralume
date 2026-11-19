# -*- coding: utf-8 -*-
"""
================================================================================
  Étage 5 — Cycles Persistants des Mêmes Agents (TH114 + TH116/TH118 + TH117)
  sur les Frontières Humaines S(5) = 160 et S(6) = 537

  Auteurs : Christian Duguay & Alix (Binôme Souverain)
  Question testée :
    Que se passe-t-il si l'on NE repart PAS de zéro, mais que l'on fait
    enchaîner plusieurs cycles aux MÊMES 6 agents en conservant :
      1. Leurs états exacts d'un cycle à l'autre (aucune amnésie) ;
      2. La mémoire stigmergique partagée trap_pen[x][g] des pièges récurrents (TH116/TH118) ;
      3. La mitose inter-cycles autour de la meilleure vallée connue (TH118) ;
      4. La résonance thermique TH114 entre répliques adjacentes ;
      5. L'arrêt immédiat et vérification indépendante dès que E = 0 (TH117).
================================================================================
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from essaim_schur_s6 import SchurBitmaskState, SORTIE_TEMOINS, verifier_partition_schur

ETAT_PERSISTANT_PATH = CURRENT_DIR / "etat_agents_schur.json"


def _conflicted_positions(st: SchurBitmaskState, sym: bool) -> List[int]:
    """Retourne les positions (1..half si sym, sinon 1..N) impliquées dans un conflit."""
    n = st.N
    half = (n + 1) // 2 if sym else n
    out: List[int] = []
    for x in range(1, half + 1):
        if st.conflicts_for(x, st.col[x]) > 0:
            out.append(x)
        elif sym:
            y = n + 1 - x
            if y != x and st.conflicts_for(y, st.col[y]) > 0:
                out.append(x)
    return out


class ColoniePersistanteTH114:
    """
    Colonie persistante de 6 répliques (TH114 + TH116/TH118 + Mitose inter-cycles).
    """

    def __init__(
        self,
        n: int,
        k: int,
        sym: bool = False,
        seed: int = 42,
        init_col: Optional[List[int]] = None,
    ):
        self.N = n
        self.k = k
        self.sym = sym
        self.seed = seed
        self.rng = random.Random(seed)
        self.temps = [0.16, 0.25, 0.38, 0.56, 0.85, 1.30]
        self.half = (n + 1) // 2 if sym else n

        self.agents: List[SchurBitmaskState] = []
        for aid in range(len(self.temps)):
            if init_col is not None:
                col = list(init_col)
                if aid >= 2:
                    # Légère diversification autour de la graine initiale
                    for _ in range(min(8, max(2, aid * 2))):
                        px = self.rng.randint(1, self.half)
                        ng = self.rng.randrange(k)
                        col[px] = ng
                        if sym:
                            col[n + 1 - px] = ng
            else:
                col = [0] * (n + 1)
                for x in range(1, self.half + 1):
                    c = self.rng.randrange(k)
                    col[x] = c
                    if sym:
                        col[n + 1 - x] = c
            self.agents.append(SchurBitmaskState(n, k, col=col))

        self.trap_pen: List[List[float]] = [[0.0] * k for _ in range(self.half + 1)]
        self.cycle_num: int = 0
        self.best_E: int = 10**9
        self.best_col: List[int] = list(self.agents[0].col)
        for st in self.agents:
            if st.total_conflicts < self.best_E:
                self.best_E = st.total_conflicts
                self.best_col = list(st.col)

        self.historique: List[Dict[str, Any]] = []

    def _effective_energy(self, st: SchurBitmaskState) -> float:
        pen = 0.0
        col = st.col
        tpen = self.trap_pen
        for x in range(1, self.half + 1):
            pen += tpen[x][col[x]]
        return st.total_conflicts + pen

    def _reinforce_traps(self) -> int:
        """
        TH116/TH118 : inspecte les variables en conflit dans les 2 répliques froides
        et incrémente leur pénalité stigmergique partagée (+0.30, plafond 4.0).
        """
        updated = 0
        for st in self.agents[:2]:
            for x in _conflicted_positions(st, self.sym):
                g = st.col[x]
                old_v = self.trap_pen[x][g]
                new_v = min(4.0, old_v + 0.30)
                if new_v > old_v:
                    self.trap_pen[x][g] = new_v
                    updated += 1
        return updated

    def _mitose_inter_cycles(self) -> None:
        """
        TH118 (Mitose entre cycles) :
        - Répliques 0 et 1 conservées intactes.
        - Répliques 2 et 3 reçoivent la meilleure vallée connue best_col
          avec une perturbation ciblée de 4 à 8 variables (prioritairement en conflit).
        - Répliques 4 et 5 gardées chaudes pour explorer globalement.
        """
        st_best = SchurBitmaskState(self.N, self.k, col=self.best_col)
        confs = _conflicted_positions(st_best, self.sym)

        for aid in (2, 3):
            col = list(self.best_col)
            n_mut = self.rng.randint(4, 8)
            chosen: List[int] = []
            if confs:
                chosen.extend(self.rng.sample(confs, min(len(confs), max(2, n_mut // 2))))
            while len(chosen) < n_mut:
                rx = self.rng.randint(1, self.half)
                if rx not in chosen:
                    chosen.append(rx)
            for px in chosen:
                cur = col[px]
                ng = self.rng.randrange(self.k - 1)
                if ng >= cur:
                    ng += 1
                col[px] = ng
                if self.sym:
                    col[self.N + 1 - px] = ng
            self.agents[aid] = SchurBitmaskState(self.N, self.k, col=col)

    def run_cycle(self, secs: float) -> Dict[str, Any]:
        """Exécute un nouveau cycle persistant pour cette colonie."""
        self.cycle_num += 1
        t0 = time.perf_counter()

        if self.cycle_num >= 2 and self.best_E > 0:
            self._mitose_inter_cycles()

        e_debut = min(st.total_conflicts for st in self.agents)

        # Vérif initiale (au cas où)
        for st in self.agents:
            if st.total_conflicts == 0:
                ok, nc = verifier_partition_schur(st.col, self.k)
                assert ok, f"Échec vérif init cycle: {nc}"
                self.best_E = 0
                self.best_col = list(st.col)
                rec = {
                    "cycle": self.cycle_num,
                    "E_debut": e_debut,
                    "E_fin": 0,
                    "best_E_global": 0,
                    "steps": 0,
                    "swaps_TH114": 0,
                    "pieges_ponderes": 0,
                    "duree_s": 0.0,
                    "solved": True,
                }
                self.historique.append(rec)
                return rec

        steps = 0
        swaps = 0
        pieges_ponderes = 0
        next_trap_mark = 2500

        while (time.perf_counter() - t0) < secs and self.best_E > 0:
            for i, st in enumerate(self.agents):
                inv_t = 1.0 / self.temps[i]
                tpen = self.trap_pen
                for _ in range(200):
                    steps += 1
                    x = self.rng.randint(1, self.half)
                    cur = st.col[x]
                    g = self.rng.randrange(self.k - 1)
                    if g >= cur:
                        g += 1

                    d_pen = tpen[x][g] - tpen[x][cur]
                    if self.sym:
                        d_exact = st.move_symmetric(x, g)
                        d_eff = d_exact + d_pen
                        if d_eff > 0.0 and self.rng.random() >= math.exp(-d_eff * inv_t):
                            st.move_symmetric(x, cur)
                    else:
                        d_exact = st.delta_move(x, g)
                        d_eff = d_exact + d_pen
                        if d_eff <= 0.0 or self.rng.random() < math.exp(-d_eff * inv_t):
                            st.move(x, g)

                    if st.total_conflicts < self.best_E:
                        self.best_E = st.total_conflicts
                        self.best_col = list(st.col)
                        if self.best_E == 0:
                            ok, nc = verifier_partition_schur(self.best_col, self.k)
                            assert ok, f"Échec vérif E=0 au cycle {self.cycle_num}: {nc}"
                            break
                if self.best_E == 0:
                    break

            if self.best_E == 0:
                break

            if steps >= next_trap_mark:
                pieges_ponderes += self._reinforce_traps()
                next_trap_mark += 2500

            # Résonance TH114 entre répliques adjacentes sur l'énergie effective
            effs = [self._effective_energy(st) for st in self.agents]
            for i in range(len(self.temps) - 1):
                e1, e2 = effs[i], effs[i + 1]
                db = (1.0 / self.temps[i]) - (1.0 / self.temps[i + 1])
                if e2 <= e1 or self.rng.random() < math.exp((e1 - e2) * db):
                    self.agents[i], self.agents[i + 1] = self.agents[i + 1], self.agents[i]
                    effs[i], effs[i + 1] = effs[i + 1], effs[i]
                    swaps += 1

        # Fin de cycle : renforcement final des pièges + décroissance douce 0.88
        if self.best_E > 0:
            pieges_ponderes += self._reinforce_traps()
            for x in range(1, self.half + 1):
                for g in range(self.k):
                    self.trap_pen[x][g] *= 0.88

        # Vérifier l'invariant entre compteur incrémental et force brute exacte
        _, exact_best = verifier_partition_schur(self.best_col, self.k)
        assert exact_best == self.best_E, f"Dérive incrémentale détectée: best_E={self.best_E} vs exact={exact_best}"

        e_fin = min(st.total_conflicts for st in self.agents)
        total_triples = sum(max(0, self.N - 2 * a + 1) for a in range(1, self.N // 2 + 1))
        pct_ok = ((total_triples - self.best_E) / total_triples * 100.0) if total_triples > 0 else 100.0

        rec = {
            "cycle": self.cycle_num,
            "E_debut": e_debut,
            "E_fin": e_fin,
            "best_E_global": self.best_E,
            "total_triples": total_triples,
            "pct_contraintes_satisfaites": round(pct_ok, 4),
            "steps": steps,
            "swaps_TH114": swaps,
            "pieges_ponderes": pieges_ponderes,
            "nb_entrees_trap_actives": sum(1 for row in self.trap_pen[1:] for v in row if v > 0.05),
            "duree_s": round(time.perf_counter() - t0, 3),
            "solved": (self.best_E == 0),
        }
        self.historique.append(rec)
        return rec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "N": self.N,
            "k": self.k,
            "sym": self.sym,
            "seed": self.seed,
            "cycle_num": self.cycle_num,
            "best_E": self.best_E,
            "best_col": self.best_col[1:],
            "agents_cols": [st.col[1:] for st in self.agents],
            "trap_pen": [[round(v, 4) for v in row] for row in self.trap_pen],
            "historique": self.historique,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColoniePersistanteTH114":
        obj = cls(n=data["N"], k=data["k"], sym=data["sym"], seed=data["seed"])
        obj.cycle_num = data["cycle_num"]
        obj.best_E = data["best_E"]
        obj.best_col = [0] + list(data["best_col"])
        obj.agents = [SchurBitmaskState(data["N"], data["k"], col=[0] + list(c)) for c in data["agents_cols"]]
        obj.trap_pen = [list(row) for row in data["trap_pen"]]
        obj.historique = list(data["historique"])
        return obj


def _run_amnesic_reset_cycle(n: int, k: int, secs: float, sym: bool, seed: int) -> Tuple[int, int, float]:
    """Témoin amnésique pur : repart chaque fois de zéro sans mémoire ni mitose."""
    col_inst = ColoniePersistanteTH114(n=n, k=k, sym=sym, seed=seed)
    res = col_inst.run_cycle(secs=secs)
    return res["best_E_global"], res["steps"], res["duree_s"]


def main() -> None:
    t_global = time.perf_counter()
    print("=" * 84)
    print("🔄 TEST DES MÊMES AGENTS PERSISTANTS SUR PLUSIEURS CYCLES (TH114 + TH116/118)")
    print("   Aucune réinitialisation à zéro : les agents gardent acquis, vallées et pièges")
    print("=" * 84)

    # --------------------------------------------------------------------------
    # EXPÉRIENCE A : S(5) = 160 (RECORD MONDIAL EXACT HEULE 2017 — 6 400 TRIPLETS)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("🔥 EXPÉRIENCE A — S(5), N = 160 (6 400 triplets)")
    print("-" * 84)

    print("1) Témoin Amnésique (3 cycles indépendants repartant de zéro, sym=True, 2.0 s/cycle) :")
    amn_es = []
    for c_idx in range(1, 4):
        be, stp, dt = _run_amnesic_reset_cycle(160, 5, secs=2.0, sym=True, seed=700 + c_idx * 37)
        amn_es.append(be)
        print(f"   • Cycle amnésique {c_idx} : best_E = {be:2d} | {stp:,} pas | {dt:.2f} s")
    print(f"   📊 Bilan Amnésique S(5)=160 : meilleur E = {min(amn_es)} (moyenne = {sum(amn_es)/len(amn_es):.2f})")

    print("\n2) Mêmes 6 Agents Persistants (5 cycles consécutifs, sym=True, 3.0 s/cycle) :")
    col_s5 = ColoniePersistanteTH114(n=160, k=5, sym=True, seed=2026)
    for _ in range(5):
        r = col_s5.run_cycle(secs=3.0)
        print(
            f"   • Cycle {r['cycle']} : E_début={r['E_debut']:4d} -> E_fin={r['E_fin']:2d} | "
            f"best_E_global={r['best_E_global']:2d} ({r['pct_contraintes_satisfaites']:.2f}%) | "
            f"{r['steps']:,} pas | TH114={r['swaps_TH114']} | pièges_actifs={r['nb_entrees_trap_actives']} | {r['duree_s']:.2f} s"
        )
        if r["solved"]:
            print("   🏆 TÉMOIN EXACT S(5)=160 DÉCOUVERT ET VÉRIFIÉ (E = 0) !")
            break

    col_s5_libre: Optional[ColoniePersistanteTH114] = None
    if col_s5.best_E > 0:
        print(
            f"\n3) Déblocage de symétrie depuis la meilleure vallée (best_E={col_s5.best_E} -> sym=False, 160 variables, 2 × 2.5 s) :"
        )
        col_s5_libre = ColoniePersistanteTH114(
            n=160, k=5, sym=False, seed=3026, init_col=col_s5.best_col
        )
        for _ in range(2):
            r = col_s5_libre.run_cycle(secs=2.5)
            print(
                f"   • Cycle libre {r['cycle']} : E_début={r['E_debut']:2d} -> E_fin={r['E_fin']:2d} | "
                f"best_E_global={r['best_E_global']:2d} ({r['pct_contraintes_satisfaites']:.2f}%) | "
                f"{r['steps']:,} pas | TH114={r['swaps_TH114']} | pièges_actifs={r['nb_entrees_trap_actives']} | {r['duree_s']:.2f} s"
            )
            if r["solved"]:
                print("   🏆 TÉMOIN EXACT S(5)=160 DÉCOUVERT EN MODE LIBRE (E = 0) !")
                break

    # --------------------------------------------------------------------------
    # EXPÉRIENCE B : S(6) = 537 (FRONTIÈRE OUVERTE MONDIALE OCT. 2026 — 72 092 TRIPLETS)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 84)
    print("🌌 EXPÉRIENCE B — S(6), N = 537 (Frontière ouverte oct. 2026 — 72 092 triplets)")
    print("   Mêmes 6 Agents Persistants (5 cycles consécutifs, sym=False, 2.5 s/cycle) :")
    print("-" * 84)
    col_s6 = ColoniePersistanteTH114(n=537, k=6, sym=False, seed=4026)
    for _ in range(5):
        r = col_s6.run_cycle(secs=2.5)
        print(
            f"   • Cycle {r['cycle']} : E_début={r['E_debut']:5d} -> E_fin={r['E_fin']:2d} | "
            f"best_E_global={r['best_E_global']:2d} ({r['pct_contraintes_satisfaites']:.4f}%) | "
            f"{r['steps']:,} pas | TH114={r['swaps_TH114']} | pièges_actifs={r['nb_entrees_trap_actives']} | {r['duree_s']:.2f} s"
        )
        if r["solved"]:
            print("   🏆 TÉMOIN EXACT S(6)=537 DÉCOUVERT ET VÉRIFIÉ (E = 0) !")
            break

    # Vérification indépendante finale avant sauvegarde
    s5_final_col = col_s5_libre if (col_s5_libre is not None and col_s5_libre.best_E <= col_s5.best_E) else col_s5
    _, exact_s5 = verifier_partition_schur(s5_final_col.best_col, 5)
    assert exact_s5 == s5_final_col.best_E
    _, exact_s6 = verifier_partition_schur(col_s6.best_col, 6)
    assert exact_s6 == col_s6.best_E

    # Sauvegarde persistante des colonies sur disque
    etat_payload = {
        "meta": {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duree_totale_s": round(time.perf_counter() - t_global, 2),
        },
        "experience_A_amnesique_S5_160": {
            "energies_cycles": amn_es,
            "meilleur_E": min(amn_es),
        },
        "colonie_S5_160_sym": col_s5.to_dict(),
        "colonie_S5_160_libre": col_s5_libre.to_dict() if col_s5_libre is not None else None,
        "colonie_S6_537": col_s6.to_dict(),
    }
    ETAT_PERSISTANT_PATH.write_text(json.dumps(etat_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Test rapide de rechargement round-trip (preuve de continuité)
    reloaded = json.loads(ETAT_PERSISTANT_PATH.read_text(encoding="utf-8"))
    s5_reloaded = ColoniePersistanteTH114.from_dict(reloaded["colonie_S5_160_sym"])
    assert s5_reloaded.best_E == col_s5.best_E

    # Si un témoin E = 0 a été trouvé sur S(5)=160 ou S(6)=537, l'ajouter à temoins_schur_th118.json
    if SORTIE_TEMOINS.exists() and (s5_final_col.best_E == 0 or col_s6.best_E == 0):
        tem_data = json.loads(SORTIE_TEMOINS.read_text(encoding="utf-8"))
        if s5_final_col.best_E == 0:
            ok5, nc5 = verifier_partition_schur(s5_final_col.best_col, 5)
            assert ok5 and nc5 == 0
            tem_data["temoins_verifies"]["S5_N160_persistant"] = s5_final_col.best_col[1:]
        if col_s6.best_E == 0:
            ok6, nc6 = verifier_partition_schur(col_s6.best_col, 6)
            assert ok6 and nc6 == 0
            tem_data["temoins_verifies"]["S6_N537_persistant"] = col_s6.best_col[1:]
        SORTIE_TEMOINS.write_text(json.dumps(tem_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 84)
    print(f"💾 État complet des agents sauvegardé dans : {ETAT_PERSISTANT_PATH}")
    print(f"🔍 Vérification brute finale : S(5)=160 best_E={exact_s5} | S(6)=537 best_E={exact_s6}")
    print(f"⏱️  Durée totale : {etat_payload['meta']['duree_totale_s']} s")
    print("=" * 84)


if __name__ == "__main__":
    main()
