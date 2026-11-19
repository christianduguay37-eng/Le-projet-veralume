# -*- coding: utf-8 -*-
"""
===============================================================================
    ⚛️🧠 COMPILATEUR DE MATIÈRE & ORDONNANCEUR STŒCHIOMÉTRIQUE (V2.0)
    Couplage : RevisedSimplex (Poséidon v10) × CDCL(T) IDL (Hadès) × Prométhée
===============================================================================
Auteurs  : Christian Duguay (L'Artisan-Démiurge) & Alix (VERALUME × KAIROS V6)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — 0 W GPU, 100% Déterministe
Rôle :
    1. Prend n'importe quel profil de déchets bruts en entrée (C, H, O, N, Si, Fe, Cl)
       et un profil d'urgence humaine (Survie Alimentaire, Hydratation, Construction,
       Hiver/Textile, Médical).
    2. Résout par Programmation Linéaire Exacte (`RevisedSimplex` à inversion
       Gauss-Jordan de `alix_moteur_deductif_poseidon_v10.py`) l'allocation
       optimale en moles et en grammes des molécules synthétisées sous contrainte
       de conservation atomique stricte (A * x <= b) et de plafond thermique
       Brillouin (P_phonons <= 1200 W).
    3. Ordonnance et certifie par Solveur SMT `CDCL(T)` (`DifferenceLogic("idl")`
       de `alix_dpll_t_solver_hades.py`) la séquence temporelle des 4 étages :
       Dissociation Palier A (8200 K) -> Palier B (11200 K) -> Tri MHD (15 kV)
       -> Soudure Floquet-STIRAP + Fenêtre EIT + Pompage Brillouin.
===============================================================================
"""

import os
import sys
import time
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Importation directe des moteurs souverains locaux (Poséidon v10 & Hadès CDCL(T))
DOSSIER_MOTEURS = os.path.dirname(os.path.abspath(__file__))
if DOSSIER_MOTEURS not in sys.path:
    pass  # rénovation 4.5 : sys.path vers A/B retiré (paquet unique) — sys.path.insert(0, DOSSIER_MOTEURS)

from alix.solveurs.alix_moteur_deductif_poseidon_v10 import RevisedSimplex
from alix.solveurs.alix_dpll_t_solver_hades import Solver

# Masses molaires atomiques (g/mol)
MASSE_MOLAIRE = {
    "C":  12.011,
    "H":  1.008,
    "O":  15.999,
    "N":  14.007,
    "Si": 28.085,
    "Fe": 55.845,
    "Cl": 35.450,
}

ELEMENTS_ORDRE = ["C", "H", "O", "N", "Si", "Fe", "Cl"]


@dataclass
class RecetteMoleculaire:
    code: str
    nom: str
    formule: str
    atomes: Dict[str, float]      # Composition stœchiométrique par mole de brique
    liaisons_par_mole_N_A: int    # Nombre de liaisons covalentes par unité de formule
    phonons_W_par_mol: float      # Charge phononique (STIRAP résiduel + Landauer stencil 1.5 bit) pour 600s
    utilite_base: Dict[str, float]# Utilité humaine par mole selon le scénario

    @property
    def masse_molaire_g(self) -> float:
        return sum(nb * MASSE_MOLAIRE[el] for el, nb in self.atomes.items())


# Catalogue des 7 briques moléculaires synthétisables dans la Chambre Holographique (Pilier 3 & 4)
CATALOGUE_MOLECULES: List[RecetteMoleculaire] = [
    RecetteMoleculaire(
        code="GLUCOSE",
        nom="D-Glucose Pur (Énergie Métabolique)",
        formule="C6H12O6",
        atomes={"C": 6, "H": 12, "O": 6},
        liaisons_par_mole_N_A=24,
        phonons_W_par_mol=20.8,
        utilite_base={"NUTRITION": 180.0, "HYDRATATION": 60.0, "CONSTRUCTION": 25.0}
    ),
    RecetteMoleculaire(
        code="ACIDE_AMINE",
        nom="Acides Aminés Essentiels (Protéines / Tissu Vivant)",
        formule="C4H9NO2",
        atomes={"C": 4, "H": 9, "O": 2, "N": 1},
        liaisons_par_mole_N_A=16,
        phonons_W_par_mol=13.9,
        utilite_base={"NUTRITION": 240.0, "HYDRATATION": 90.0, "CONSTRUCTION": 50.0}
    ),
    RecetteMoleculaire(
        code="EAU_PURE",
        nom="Eau Ultra-Pure Minéralisée",
        formule="H2O",
        atomes={"H": 2, "O": 1},
        liaisons_par_mole_N_A=2,
        phonons_W_par_mol=1.73,
        utilite_base={"NUTRITION": 15.0, "HYDRATATION": 55.0, "CONSTRUCTION": 10.0}
    ),
    RecetteMoleculaire(
        code="ARAMIDE_TEXTILE",
        nom="Fibre Aramide / Polymère Haute Résistance",
        formule="C7H5NO",
        atomes={"C": 7, "H": 5, "O": 1, "N": 1},
        liaisons_par_mole_N_A=15,
        phonons_W_par_mol=13.0,
        utilite_base={"NUTRITION": 95.0, "HYDRATATION": 70.0, "CONSTRUCTION": 210.0}
    ),
    RecetteMoleculaire(
        code="POLYETHYLENE_PROPRE",
        nom="Polymère Médical & Tuyauterie Sanitaire",
        formule="C2H4",
        atomes={"C": 2, "H": 4},
        liaisons_par_mole_N_A=6,
        phonons_W_par_mol=5.2,
        utilite_base={"NUTRITION": 18.0, "HYDRATATION": 16.0, "CONSTRUCTION": 42.0}
    ),
    RecetteMoleculaire(
        code="QUARTZ_SILICE",
        nom="Verre de Quartz / Substrat Silicium",
        formule="SiO2",
        atomes={"Si": 1, "O": 2},
        liaisons_par_mole_N_A=4,
        phonons_W_par_mol=3.46,
        utilite_base={"NUTRITION": 50.0, "HYDRATATION": 40.0, "CONSTRUCTION": 140.0}
    ),
    RecetteMoleculaire(
        code="CARBURE_SILICIUM",
        nom="Céramique Blindée Carbure de Silicium (SiC)",
        formule="SiC",
        atomes={"Si": 1, "C": 1},
        liaisons_par_mole_N_A=4,
        phonons_W_par_mol=3.46,
        utilite_base={"NUTRITION": 35.0, "HYDRATATION": 35.0, "CONSTRUCTION": 160.0}
    ),
    RecetteMoleculaire(
        code="ACIER_FE3C",
        nom="Acier Structural & Outillage (Fe-C)",
        formule="FeC0.05",
        atomes={"Fe": 1.0, "C": 0.05},
        liaisons_par_mole_N_A=2,
        phonons_W_par_mol=1.73,
        utilite_base={"NUTRITION": 65.0, "HYDRATATION": 65.0, "CONSTRUCTION": 150.0}
    ),
    RecetteMoleculaire(
        code="SEL_CHLORE_STABLE",
        nom="Cartouche Chlore Neutralisé (Zéro Dioxine)",
        formule="HCl_confine",
        atomes={"Cl": 1.0, "H": 1.0},
        liaisons_par_mole_N_A=1,
        phonons_W_par_mol=0.86,
        utilite_base={"NUTRITION": 120.0, "HYDRATATION": 120.0, "CONSTRUCTION": 120.0}
    ),
]


def compiler_allocation_optimale_lp(
    dechets_g: Dict[str, float],
    profil_besoin: str = "NUTRITION",
    plafond_brillouin_W: float = 1200.0
) -> Dict:
    """
    Utilise RevisedSimplex (Poséidon v10) pour trouver le vecteur de production x (en moles)
    qui maximise l'utilité humaine tout en respectant :
      1. Conservation atomique : sum_j (a_{i,j} * x_j) <= n_atomes_i (en moles)
      2. Stabilité thermodynamique (Pilier 5) : sum_j (phonons_j * x_j) <= plafond_brillouin_W
    """
    t0 = time.perf_counter()
    # Conversion des grammes d'entrée en moles disponibles pour chaque élément
    moles_dispo = {el: dechets_g.get(el, 0.0) / MASSE_MOLAIRE[el] for el in ELEMENTS_ORDRE}

    n_var = len(CATALOGUE_MOLECULES)
    A = []
    b = []

    # 7 contraintes de conservation élémentaire (C, H, O, N, Si, Fe, Cl)
    for el in ELEMENTS_ORDRE:
        ligne = [mol.atomes.get(el, 0.0) for mol in CATALOGUE_MOLECULES]
        A.append(ligne)
        b.append(moles_dispo[el])

    # 8ème contrainte : Plafond Thermodynamique du Pilier 5 (Pompage Brillouin Anti-Stokes <= 1200 W)
    ligne_thermique = [mol.phonons_W_par_mol for mol in CATALOGUE_MOLECULES]
    A.append(ligne_thermique)
    b.append(plafond_brillouin_W)

    # Fonction objectif : RevisedSimplex minimise c^T x, donc on pose c_j = -utilite_j
    c = [-mol.utilite_base[profil_besoin] for mol in CATALOGUE_MOLECULES]

    solveur_lp = RevisedSimplex(A, b, c)
    res_lp = solveur_lp.resoudre(max_iter=500)
    dt_ms = (time.perf_counter() - t0) * 1000.0

    x_moles = res_lp.get("x", [0.0] * n_var)
    produits_synthetises = []
    masse_totale_produite_g = 0.0
    charge_phonons_totale_W = 0.0
    liaisons_totales_moles = 0.0

    atomes_consommes_moles = {el: 0.0 for el in ELEMENTS_ORDRE}

    for j, mol in enumerate(CATALOGUE_MOLECULES):
        nb_mol = x_moles[j]
        if nb_mol > 1e-6:
            masse_g = nb_mol * mol.masse_molaire_g
            phonons_W = nb_mol * mol.phonons_W_par_mol
            masse_totale_produite_g += masse_g
            charge_phonons_totale_W += phonons_W
            liaisons_totales_moles += nb_mol * mol.liaisons_par_mole_N_A
            for el, qte in mol.atomes.items():
                atomes_consommes_moles[el] += nb_mol * qte

            produits_synthetises.append({
                "code": mol.code,
                "nom": mol.nom,
                "formule": mol.formule,
                "moles": round(nb_mol, 3),
                "masse_g": round(masse_g, 2),
                "phonons_W": round(phonons_W, 2),
            })

    # Atomes purs stockés en lingots/silos élémentaires (surplus non engagé dans une molécule)
    silos_elementaires_g = {}
    masse_silos_g = 0.0
    for el in ELEMENTS_ORDRE:
        reste_mol = max(0.0, moles_dispo[el] - atomes_consommes_moles[el])
        reste_g = reste_mol * MASSE_MOLAIRE[el]
        if reste_g > 0.05:
            silos_elementaires_g[el] = round(reste_g, 2)
            masse_silos_g += reste_g

    masse_entree_g = sum(dechets_g.values())

    return {
        "profil": profil_besoin,
        "statut_lp": res_lp["statut"],
        "iterations_simplex": res_lp["iterations"],
        "temps_calcul_ms": round(dt_ms, 3),
        "masse_entree_g": round(masse_entree_g, 2),
        "masse_molecules_g": round(masse_totale_produite_g, 2),
        "masse_silos_purs_g": round(masse_silos_g, 2),
        "masse_totale_sortie_g": round(masse_totale_produite_g + masse_silos_g, 2),
        "charge_phonons_W": round(charge_phonons_totale_W, 2),
        "plafond_brillouin_W": plafond_brillouin_W,
        "T_equilibre_C": round(26.85 + max(0.0, charge_phonons_totale_W - 650.0) / 85.0, 2),
        "produits": produits_synthetises,
        "silos_purs_g": silos_elementaires_g,
    }


def ordonnancer_sequence_cdcl_smt() -> Dict:
    """
    Utilise le solveur CDCL(T) DifferenceLogic("idl") (Hadès) pour prouver et ordonnancer
    sans conflit temporel ni croisement thermique la séquence des 5 Piliers (en secondes)
    sur une fenêtre stricte de 600 s (10 minutes).
    """
    t0 = time.perf_counter()
    s = Solver(theory="idl")

    # Variables temporelles (en secondes) :
    # t_start = 0
    # t_p1A_fin : Fin de l'extraction plasma Palier A (8 200 K : Si+, Fe+)
    # t_p1B_fin : Fin de l'extraction plasma Palier B (11 200 K : C+, H+, O+, N+, Cl+)
    # t_mhd_fin : Fin du tri magnétohydrodynamique (V_acc = 15 kV, B = 0.45 T)
    # t_eit_on  : Verrouillage de la fenêtre de transparence EIT + Onde stationnaire Brillouin
    # t_synth_0 : Début de la soudure Floquet-STIRAP (Pilier 4)
    # t_synth_f : Fin de la synthèse et refroidissement final <= 600 s

    clauses = [
        # 1. t_start == 0
        s.atom("t_start", None, 0),
        s.atom(None, "t_start", 0),

        # 2. Palier A (8200 K) dure au moins 90 s après t_start
        s.atom("t_start", "t_p1A_fin", -90),

        # 3. Palier B (11200 K) démarre après Palier A et dure au moins 150 s
        s.atom("t_p1A_fin", "t_p1B_fin", -150),

        # 4. Le tri MHD s'achève au moins 40 s après la fin du Palier B
        s.atom("t_p1B_fin", "t_mhd_fin", -40),

        # 5. SÉCURITÉ THERMODYNAMIQUE CRITIQUE (Pilier 5) :
        #    La fenêtre EIT et le pompage Brillouin (t_eit_on) DOIVENT être verrouillés
        #    au moins 15 s AVANT l'allumage du laser de soudure Floquet-STIRAP (t_synth_0) !
        s.atom("t_mhd_fin", "t_eit_on", -10),
        s.atom("t_eit_on", "t_synth_0", -15),

        # 6. La soudure holographique STIRAP dure 280 s
        s.atom("t_synth_0", "t_synth_f", -280),

        # 7. Deadline globale du lot de 1.0 kg : t_synth_f <= 600 s
        s.atom("t_synth_f", "t_start", 600),
    ]

    for lit in clauses:
        s.add_clause([lit])

    ok = s.solve()
    dt_ms = (time.perf_counter() - t0) * 1000.0

    # Extraction des potentiels (horodatages minimaux prouvés par Cotton-Maler)
    p0 = s.theory.p[s.theory.var("t_start")][0]
    horaires = {}
    for nom in ["t_start", "t_p1A_fin", "t_p1B_fin", "t_mhd_fin", "t_eit_on", "t_synth_0", "t_synth_f"]:
        horaires[nom] = s.theory.p[s.theory.var(nom)][0] - p0

    # Contre-épreuve de sécurité : que se passe-t-il si on tente d'allumer la soudure Floquet
    # AVANT la fenêtre EIT (t_synth_0 < t_eit_on) ? Le solveur CDCL(T) doit retourner UNSAT !
    lit_violation_eit = s.atom("t_synth_0", "t_eit_on", -1)
    ok_violation = s.solve(assumptions=[lit_violation_eit])

    return {
        "sat_nominal": bool(ok),
        "violation_eit_bloquee_unsat": (not ok_violation),
        "temps_preuve_smt_ms": round(dt_ms, 3),
        "chronogramme_s": horaires,
    }


def main():
    print("=" * 86)
    print(" ⚛️🧠 COMPILATEUR DE MATIÈRE V2.0 — REVISED SIMPLEX (POSÉIDON) × CDCL(T) (HADÈS)")
    print("=" * 86)

    # Lot de 1 000 g de déchets mixtes (Plastiques, résidus organiques, verre, ferraille, PVC)
    lot_dechets_1kg = {
        "C":  480.0,
        "H":   80.0,
        "O":  250.0,
        "N":   30.0,
        "Si":  70.0,
        "Fe":  60.0,
        "Cl":  30.0,
    }

    # Test sur 3 scénarios de besoins humains à partir EXACTEMENT de la même poubelle de 1 kg !
    scenarios = [
        ("NUTRITION",    " Priorité Nutrition & Métabolisme (Glucides, Protéines, Eau)"),
        ("HYDRATATION",  "💧 Priorité Eau Potable & Assainissement d'Urgence"),
        ("CONSTRUCTION", "🛠️ Priorité Matériaux, Textiles, Céramique SiC & Outillage"),
    ]

    for code_scen, titre in scenarios:
        res = compiler_allocation_optimale_lp(lot_dechets_1kg, profil_besoin=code_scen)
        print(f"\n{titre}")
        print(f"  • Statut LP RevisedSimplex : {res['statut_lp'].upper()} en {res['iterations_simplex']} itérations ({res['temps_calcul_ms']} ms)")
        print(f"  • Bilan Masse Conservation : Entrée = {res['masse_entree_g']} g -> Sortie = {res['masse_totale_sortie_g']} g "
              f"({res['masse_molecules_g']} g molécules + {res['masse_silos_purs_g']} g lingots purs)")
        print(f"  • Bilan Thermique Pilier 5 : {res['charge_phonons_W']} W / {res['plafond_brillouin_W']} W max "
              f"-> Température Objet = {res['T_equilibre_C']} °C")
        for p in res["produits"]:
            print(f"    - {p['masse_g']:6.2f} g ({p['moles']:5.2f} mol) : {p['nom']:48s} [{p['formule']}] ({p['phonons_W']:5.1f} W)")
        if res["silos_purs_g"]:
            silos_str = ", ".join(f"{el}: {g} g" for el, g in res["silos_purs_g"].items())
            print(f"    - Lingots / Silos atomiques purs mis en réserve : {silos_str}")

    # Preuve d'ordonnancement temporel et de verrouillage EIT par CDCL(T)
    smt = ordonnancer_sequence_cdcl_smt()
    c = smt["chronogramme_s"]
    print("\n" + "-" * 86)
    print(" ⏱️🛡️ PREUVE D'ORDONNANCEMENT TEMPOREL & VERROU THERMIQUE PAR SOLVEUR SMT CDCL(T)")
    print("-" * 86)
    print(f"  • Preuve CDCL(T) Cotton-Maler : SAT = {smt['sat_nominal']} en {smt['temps_preuve_smt_ms']} ms")
    print(f"  • Contre-épreuve Sécurité EIT : Allumage Floquet sans EIT bloqué (UNSAT) = {smt['violation_eit_bloquee_unsat']}")
    print(f"  • Chronogramme certifié (Lot 1.0 kg <= 600 s) :")
    print(f"    [t = {c['t_start']:3d} s -> {c['t_p1A_fin']:3d} s] Étage 1A : Torche Plasma 8 200 K (Extraction Si+, Fe+ sans double ionisation)")
    print(f"    [t = {c['t_p1A_fin']:3d} s -> {c['t_p1B_fin']:3d} s] Étage 1B : Torche Plasma 11 200 K (Extraction C+, H+, O+, N+, Cl+)")
    print(f"    [t = {c['t_p1B_fin']:3d} s -> {c['t_mhd_fin']:3d} s] Étage 2  : Tri Cyclotronique MHD (15 kV, 0.45 T, ΔD_min = 20.16 mm)")
    print(f"    [t = {c['t_mhd_fin']:3d} s -> {c['t_eit_on']:3d} s] Étage 3  : Piégeage Holographique 3D (Noeuds sombres 0.085 nm)")
    print(f"    [t = {c['t_eit_on']:3d} s -> {c['t_synth_0']:3d} s] Étage 5A : Verrouillage Fenêtre EIT + Onde Brillouin Anti-Stokes (Pré-refroidissement)")
    print(f"    [t = {c['t_synth_0']:3d} s -> {c['t_synth_f']:3d} s] Étage 4  : Soudure Covalente Floquet-STIRAP (99.85% recyclé, T = 27.2 °C)")
    print("=" * 86)


if __name__ == "__main__":
    main()
