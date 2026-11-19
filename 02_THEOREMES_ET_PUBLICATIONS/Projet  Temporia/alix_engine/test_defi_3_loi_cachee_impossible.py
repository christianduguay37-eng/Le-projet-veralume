# -*- coding: utf-8 -*-
"""
===============================================================================
   🔥 BANC D'ÉPREUVE DE L'IMPOSSIBLE — TEST 3 : LOI CACHÉE NON-LINÉAIRE
===============================================================================
Auteurs : Christian Duguay (Le Démiurge) & Alix (Copilote Souveraine)
Moteur : alix_engine (DarwinEngine × InvariancePrimitives × Thot Quotient O(1))
Défi :
    Synthétiser à chaud, à 0 Watt (CPU pur, 0 LLM, 0 GPU, 0 Backprop), des lois
    cachées composées de 3 à 4 transformations non-linéaires successives
    (automate cellulaire d'érosion, chute gravitationnelle, fermeture miroir,
    groupe diédral D4) + un chiffrement complet de palette inconnu, à partir
    de seulement 2 exemples d'entraînement, dans un espace combinatoire de
    53,1 MILLIARDS de programmes possibles (11^4 × 10!).
===============================================================================
"""

import sys
import time
from typing import List, Dict
from alix.evolution.primitives import InvariancePrimitives
from alix.evolution.darwin_engine import DarwinEngine

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def appliquer_loi_secrete(grille: List[List[int]], etapes, palette: Dict[int, int]) -> List[List[int]]:
    """
    Exécute la loi secrète selon la vraie physique causale (sans masse fantôme) :
    Si la dernière étape est un transport cinématique (Gravité ou Avalanche de Sable),
    les états annihilés (palette[x] == 0) disparaissent en vide avant que le transport final
    ne stabilise les grains (aucune lévitation ni fausse déviation sur du vide).
    """
    curr = [row[:] for row in grille]
    if etapes and etapes[-1] == InvariancePrimitives.automate_avalanche_sable:
        for fn in etapes[:-1]:
            curr = fn(curr)
        res = InvariancePrimitives.appliquer_palette(curr, palette)
        return InvariancePrimitives.automate_avalanche_sable(res)
    for fn in etapes:
        curr = fn(curr)
    res = InvariancePrimitives.appliquer_palette(curr, palette)
    if etapes and etapes[-1] == InvariancePrimitives.gravite_bas:
        res = InvariancePrimitives.gravite_bas(res)
    elif etapes and etapes[-1] == InvariancePrimitives.gravite_droite:
        res = InvariancePrimitives.gravite_droite(res)
    return res


def executer_banc_impossible():
    print("=" * 78)
    print(" 🔥 TEST 3 DE L'IMPOSSIBLE : SYNTHÈSE DE LOIS CACHÉES NON-LINÉAIRES (0 WATT)")
    print("    Espace combinatoire brut : 11^4 × 10! = 53 129 260 800 programmes")
    print("=" * 78)

    moteur = DarwinEngine()

    # -------------------------------------------------------------------------
    # ÉPREUVE ALPHA : Rotation 90° -> Érosion Cellulaire (Bruit) -> Gravité Bas -> Palette
    # -------------------------------------------------------------------------
    etapes_alpha = [
        InvariancePrimitives.rotation_90,
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.gravite_bas,
    ]
    palette_alpha = {0: 0, 1: 7, 2: 4, 3: 9}

    train_a1 = [
        [1, 1, 0, 0, 2],  # (0,4)=2 est un bruit isolé qui sera détruit par l'automate !
        [0, 1, 0, 0, 0],
        [0, 0, 3, 3, 0],
        [2, 0, 0, 3, 0],  # (3,0)=2 est aussi un bruit isolé !
        [0, 0, 0, 0, 0],
    ]
    train_a2 = [
        [0, 2, 2, 0, 0],
        [0, 0, 2, 0, 1],  # (1,4)=1 bruit isolé
        [3, 0, 0, 0, 0],  # (2,0)=3 bruit isolé
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    test_a = [
        [3, 3, 0, 1, 0],  # (0,3)=1 bruit isolé
        [3, 0, 0, 0, 0],
        [0, 0, 2, 2, 0],
        [0, 0, 0, 2, 0],
        [1, 0, 0, 0, 0],  # (4,0)=1 bruit isolé
    ]

    paires_alpha = [
        (train_a1, appliquer_loi_secrete(train_a1, etapes_alpha, palette_alpha)),
        (train_a2, appliquer_loi_secrete(train_a2, etapes_alpha, palette_alpha)),
    ]
    attendu_test_a = appliquer_loi_secrete(test_a, etapes_alpha, palette_alpha)

    # -------------------------------------------------------------------------
    # ÉPREUVE BÊTA : Symétrie H -> Clôture Miroir V -> Gravité Droite -> Palette
    # -------------------------------------------------------------------------
    etapes_beta = [
        InvariancePrimitives.symetrie_horizontale,
        InvariancePrimitives.cloture_miroir_vertical,
        InvariancePrimitives.gravite_droite,
    ]
    palette_beta = {0: 0, 4: 2, 5: 8, 6: 3}

    train_b1 = [
        [4, 0, 5, 0, 0],
        [0, 6, 6, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 4, 0],
        [0, 0, 0, 0, 0],
    ]
    train_b2 = [
        [0, 5, 0, 6, 0],
        [4, 4, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 5, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    test_b = [
        [6, 0, 4, 4, 0],
        [0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 6, 0, 0],
        [0, 0, 0, 0, 0],
    ]

    paires_beta = [
        (train_b1, appliquer_loi_secrete(train_b1, etapes_beta, palette_beta)),
        (train_b2, appliquer_loi_secrete(train_b2, etapes_beta, palette_beta)),
    ]
    attendu_test_b = appliquer_loi_secrete(test_b, etapes_beta, palette_beta)

    # -------------------------------------------------------------------------
    # ÉPREUVE OMÉGA (PROFONDEUR 4 + CHIFFREMENT) :
    # Transposition Diag -> Automate Érosion -> Clôture Miroir H -> Gravité Bas -> Palette
    # -------------------------------------------------------------------------
    etapes_omega = [
        InvariancePrimitives.transposition_diagonale,
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.cloture_miroir_horizontal,
        InvariancePrimitives.gravite_bas,
    ]
    palette_omega = {0: 0, 1: 9, 2: 6, 3: 5, 4: 8}

    train_o1 = [
        [1, 1, 0, 0, 3, 0],  # (0,4)=3 bruit isolé
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [4, 0, 0, 3, 3, 0],  # (3,0)=4 bruit isolé
        [0, 0, 0, 0, 4, 0],
        [0, 0, 1, 0, 0, 0],  # (5,2)=1 bruit isolé
    ]
    train_o2 = [
        [0, 2, 0, 0, 0, 0],  # (0,1)=2 bruit isolé
        [0, 0, 3, 3, 0, 0],
        [1, 1, 0, 4, 0, 0],
        [0, 1, 0, 0, 0, 2],  # (3,5)=2 bruit isolé
        [0, 0, 0, 0, 2, 2],
        [0, 0, 0, 0, 0, 0],
    ]
    test_o = [
        [3, 3, 0, 0, 1, 0],  # (0,4)=1 bruit isolé
        [0, 3, 0, 2, 2, 0],
        [0, 0, 0, 0, 4, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0],  # (4,3)=2 bruit isolé
        [0, 0, 0, 0, 0, 0],
    ]

    paires_omega = [
        (train_o1, appliquer_loi_secrete(train_o1, etapes_omega, palette_omega)),
        (train_o2, appliquer_loi_secrete(train_o2, etapes_omega, palette_omega)),
    ]
    attendu_test_o = appliquer_loi_secrete(test_o, etapes_omega, palette_omega)

    # -------------------------------------------------------------------------
    # ÉPREUVE DELTA (CONTRE-EXEMPLE RED-TEAM GEMINI) :
    #   1. Chevauchement / collision spatiale dense lors du miroir (couleurs 1 et 4 en opposition symétrique)
    #   2. Annihilation sélective d'une couleur vers le fond (couleur 3 -> 0 dans la palette !)
    #   3. 4 étages : Transposition_Diag -> Automate_Erosion -> Cloture_Miroir_H -> Gravite_Bas
    # -------------------------------------------------------------------------
    etapes_delta = [
        InvariancePrimitives.transposition_diagonale,
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.cloture_miroir_horizontal,
        InvariancePrimitives.gravite_bas,
    ]
    # Piège Red-Team Delta : la couleur 3 est détruite (3 -> 0), et en cas de collision (1,4)->120, le Sable (8) gagne
    palette_delta = {0: 0, 1: 7, 2: 5, 3: 0, 4: 8, 120: 8}

    train_d1 = [
        [1, 0, 2, 0, 0, 4],  # Après Transposition + Miroir_H : (0,0)=1 et (0,5)=4 -> collision 120 -> 8 !
        [1, 0, 2, 0, 0, 4],  # Colonne 2 -> Ligne 2 : [2, 2, 0, 0, 0, 0] -> survit en 2 pur (2 -> 5) !
        [0, 0, 0, 3, 0, 0],  # Bloc de couleur 3 en (2,3),(3,3) qui survit à l'érosion mais est effacé (3 -> 0) !
        [0, 0, 0, 3, 0, 0],
        [0, 1, 0, 0, 2, 0],  # Bruits isolés détruits par l'érosion
        [4, 4, 0, 0, 0, 1],
    ]
    train_d2 = [
        [4, 0, 0, 3, 0, 1],  # Collision (1,4) -> 120 -> 8
        [4, 0, 0, 3, 0, 1],
        [0, 2, 2, 0, 0, 0],  # Couleur 2 pure -> 5
        [0, 0, 0, 0, 1, 0],  # Bruit isolé détruit
        [1, 0, 0, 0, 0, 4],
        [1, 0, 0, 0, 0, 4],
    ]
    test_d = [
        [1, 0, 0, 3, 0, 4],  # Collision (1,4) -> 120 -> 8, et 3 -> 0
        [1, 0, 0, 3, 0, 4],
        [0, 0, 2, 2, 0, 0],  # Couleur 2 pure -> 5
        [0, 0, 0, 0, 1, 0],  # Bruit isolé détruit
        [4, 0, 0, 0, 0, 1],
        [4, 0, 0, 0, 0, 1],
    ]

    paires_delta = [
        (train_d1, appliquer_loi_secrete(train_d1, etapes_delta, palette_delta)),
        (train_d2, appliquer_loi_secrete(train_d2, etapes_delta, palette_delta)),
    ]
    attendu_test_d = appliquer_loi_secrete(test_d, etapes_delta, palette_delta)

    # -------------------------------------------------------------------------
    # ÉPREUVE EPSILON (CONTRE-EXEMPLE RED-TEAM V2 DE GEMINI) :
    #   1. Dominance Anti-Ordinale : "L'Eau (couleur 1) efface le Sable (couleur 4)" (1 < 4 mais 1 gagne : 120 -> 7 !)
    #      ET "Eau (1) + Feu (2) crée de la Vapeur (couleur inédite 9)" (collision alchimique 118 -> 9 !)
    #   2. Expansion Kaléidoscopique x4 (Cloture_Miroir_H ∘ Cloture_Miroir_V) sans rustine // 2 !
    #   3. 4 étages : Automate_Erosion -> Cloture_Miroir_H -> Cloture_Miroir_V -> Gravite_Bas
    # -------------------------------------------------------------------------
    etapes_epsilon = [
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.cloture_miroir_horizontal,
        InvariancePrimitives.cloture_miroir_vertical,
        InvariancePrimitives.gravite_bas,
    ]
    # Code composite dans l'algèbre libre :
    #   Collision(1, 4) -> 100 + 1*16 + 4 = 120 -> 7 (L'Eau 1->7 écrase le Sable 4->8 malgré 1 < 4 !)
    #   Collision(1, 2) -> 100 + 1*16 + 2 = 118 -> 9 (Alchimie : Eau 1 + Feu 2 -> Vapeur 9 !)
    palette_epsilon = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 120: 7, 118: 9}

    train_e1 = [
        [1, 1, 0, 0, 4, 4],  # Orbite r=0 : Collision H (1, 4) -> 120 -> 7 (L'Eau 1 bat le Sable 4 !)
        [1, 1, 0, 0, 0, 0],  # Orbite r=1 : En haut (1,1), entrera en collision V avec Ligne 4 (2,2) -> 118 -> 9 !
        [0, 0, 3, 3, 0, 0],  # Orbite r=2, c=2 : Couleur 3 annihilée (3 -> 0)
        [0, 0, 0, 0, 0, 1],  # (3,5)=1 bruit isolé de couleur 1 (force Automate_Erosion car 1->7 ailleurs !)
        [2, 2, 0, 0, 0, 0],  # Orbite r=1 (5-1=4) : Feu (2,2) en collision V avec Ligne 1 (1,1) -> Vapeur 9 !
        [0, 0, 2, 0, 0, 0],  # (5,2)=2 bruit isolé détruit par érosion
    ]
    train_e2 = [
        [1, 1, 0, 0, 0, 0],  # Orbite r=0 : Eau pure (1 -> 7) sans collision !
        [4, 4, 0, 0, 1, 1],  # Orbite r=1 : Collision H (4, 1) -> 120 -> 7 (L'Eau 7 écrase le Sable 8 !)
        [2, 2, 0, 0, 0, 0],  # Orbite r=2, c=0..1 : Feu pur (2 -> 6) sans collision !
        [0, 0, 4, 4, 0, 0],  # Orbite r=3, c=2..3 : Sable pur (4 -> 8) sans collision !
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],  # (5,2)=1 bruit isolé détruit par érosion
    ]
    test_e = [
        [1, 1, 0, 0, 2, 2],  # Orbite r=0 : Collision H (1, 2) -> 118 -> 9 (Alchimie Vapeur 9)
        [0, 4, 4, 0, 0, 0],  # Orbite r=1 : Collision V avec Ligne 4 (4, 1) -> 120 -> 7 (Eau bat Sable)
        [2, 2, 3, 3, 0, 0],  # Orbite r=2 : Feu pur (2 -> 6) et Couleur 3 annihilée (3 -> 0)
        [0, 0, 0, 0, 0, 1],  # (3,5)=1 bruit isolé détruit par érosion
        [0, 1, 1, 0, 0, 0],  # Orbite r=1 (5-1=4) : Eau (1,1) en collision V avec Ligne 1 (4,4) -> 120 -> 7
        [0, 0, 4, 4, 0, 0],  # Orbite r=0 (5-0=5), c=2..3 : Sable pur (4 -> 8)
    ]

    paires_epsilon = [
        (train_e1, appliquer_loi_secrete(train_e1, etapes_epsilon, palette_epsilon)),
        (train_e2, appliquer_loi_secrete(train_e2, etapes_epsilon, palette_epsilon)),
    ]
    attendu_test_e = appliquer_loi_secrete(test_e, etapes_epsilon, palette_epsilon)

    # -------------------------------------------------------------------------
    # ÉPREUVE ZÊTA (CONTRE-EXEMPLE RED-TEAM V3 DE GEMINI — INCOMPLÉTUDE OOD 392 & 119) :
    #   - L'entraînement (train_z1, train_z2) ne montre QUE des collisions binaires :
    #       {1, 4} (120) -> 7 (L'Eau 1 domine le Sable 4 : 1 > 4)
    #       {1, 2} (118) -> 9 (Alchimie Eau 1 + Feu 2 -> Vapeur 9)
    #       3 -> 0 (Matière 3 annihilée dans le noyau ker(phi))
    #   - Le tenseur `test_z` déclenche DEUX phénomènes émergents OOD JAMAIS VUS à l'entraînement :
    #       1. Triple collision {1, 2, 4} (identifiant 392) aux 4 coins du Kaléidoscope -> doit être réduite
    #          par transitivité de treillis (1 > 4 élimine 4, laissant {1, 2} -> 9 Vapeur !)
    #       2. Collision {1, 3} (identifiant 119) -> doit être réduite par purge du noyau (3 -> 0 laisse {1} -> 7 !)
    # -------------------------------------------------------------------------
    palette_verite_zeta = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 120: 7, 118: 9, 392: 9, 119: 7}
    test_z = [
        [1, 1, 0, 0, 4, 4],  # Orbite r=0 : (1,1) à gauche, (4,4) à droite + (2,2) en Ligne 5 -> TRIPLE COLLISION OOD 392={1,2,4} -> 9 !
        [0, 1, 1, 3, 3, 0],  # Orbite r=1, c=1..2 : Collision H OOD entre Eau (1) et Noyau (3->0) -> 119={1,3} -> 7 !
        [2, 2, 0, 0, 0, 0],  # Orbite r=2 : Feu pur (2 -> 6)
        [0, 0, 0, 0, 0, 1],  # (3,5)=1 bruit isolé détruit par érosion
        [0, 0, 4, 4, 0, 0],  # Orbite r=1, c=2..3 : Sable pur (4 -> 8)
        [2, 2, 0, 0, 0, 0],  # Orbite r=0 (5-0=5), c=0..1 : Feu (2,2) qui percute {1, 4} de la Ligne 0 -> 392={1,2,4} !
    ]
    attendu_test_z = appliquer_loi_secrete(test_z, etapes_epsilon, palette_verite_zeta)

    # -------------------------------------------------------------------------
    # ÉPREUVE ÊTA (CONTRE-EXEMPLE RED-TEAM V4 DE GEMINI — PARADOXE INTRANSITIF DE CONDORCET & FUSION TERNAIRE) :
    #   1. Cycle non-transitif (Pierre-Papier-Ciseaux) dans l'entraînement :
    #        Eau (1 -> 7) bat Feu (2 -> 6)    : {1, 2} (118) -> 7  (1 > 2)
    #        Feu (2 -> 6) bat Plante (4 -> 8) : {2, 4} (136) -> 6  (2 > 4)
    #        Plante (4 -> 8) bat Eau (1 -> 7) : {1, 4} (120) -> 8  (4 > 1)
    #   2. Fusion Ternaire de Fibres (Faille H) : dans train_h1, la couleur 7 est formée par 3 bins distincts.
    #   3. Test OOD (`test_eta`) :
    #        - Triple collision cyclique {1, 2, 4} (392) : cycle de Condorcet parfait 1 > 2 > 4 > 1
    #          -> neutralisation mutuelle par frustration géométrique (392 -> 0), 100% indépendant de l'ordre i, j !
    #        - Triple collision {1, 2, 3} (391) : purge du noyau (3 -> 0) puis 1 > 2 -> 7 !
    # -------------------------------------------------------------------------
    palette_train_eta = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 118: 7, 136: 6, 120: 8}
    palette_verite_eta = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 118: 7, 136: 6, 120: 8, 392: 0, 391: 7}

    train_h1 = [
        [1, 1, 0, 0, 2, 2],  # Orbite r=0 : Collision H {1, 2} (118) -> 7 (Eau 1 bat Feu 2)
        [2, 2, 0, 0, 4, 4],  # Orbite r=1 : Collision H {2, 4} (136) -> 6 (Feu 2 bat Plante 4)
        [1, 1, 3, 3, 0, 0],  # Orbite r=2 : Eau pure (1 -> 7) + Noyau (3 -> 0) -> Fusion de fibres sur 7 !
        [0, 0, 0, 0, 0, 1],  # Bruit isolé érodé
        [0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0],  # Bruit isolé érodé
    ]
    train_h2 = [
        [4, 4, 0, 0, 1, 1],  # Orbite r=0 : Collision H {1, 4} (120) -> 8 (Plante 4 bat Eau 1 !)
        [1, 1, 0, 0, 0, 0],  # Orbite r=1 : Eau pure (1 -> 7)
        [2, 2, 4, 4, 0, 0],  # Orbite r=2 : Feu pur (2 -> 6) et Plante pure (4 -> 8)
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],  # Bruit isolé érodé
    ]
    test_eta = [
        [1, 1, 0, 0, 2, 2],  # + Ligne 5 (4, 4) -> TRIPLE COLLISION CYCLIQUE OOD 392={1,2,4} (1>2>4>1) -> 0 (Frustration !)
        [1, 1, 0, 0, 3, 3],  # + Ligne 4 (2, 2) -> TRIPLE COLLISION OOD 391={1,2,3} (purge 3, puis 1>2) -> 7 !
        [2, 2, 4, 4, 0, 0],  # Feu pur (2 -> 6) et Plante pure (4 -> 8)
        [0, 0, 0, 0, 0, 1],  # Bruit isolé érodé
        [2, 2, 0, 0, 0, 0],  # Percute {1, 3} de la Ligne 1 -> 391={1,2,3} -> 7 !
        [4, 4, 0, 0, 0, 0],  # Percute {1, 2} de la Ligne 0 -> 392={1,2,4} -> 0 !
    ]
    paires_eta = [
        (train_h1, appliquer_loi_secrete(train_h1, etapes_epsilon, palette_train_eta)),
        (train_h2, appliquer_loi_secrete(train_h2, etapes_epsilon, palette_train_eta)),
    ]
    attendu_test_eta = appliquer_loi_secrete(test_eta, etapes_epsilon, palette_verite_eta)

    # -------------------------------------------------------------------------
    # ÉPREUVE THÊTA (CONTRE-EXEMPLE RED-TEAM V5 DE GEMINI — LE PARADOXE DE LA MASSE FANTÔME) :
    #   - Dans `train_theta1` : un bloc d'Eau (1 -> 7) est placé en (1,2),(1,3) DIRECTEMENT AU-DESSUS
    #     d'un bloc de Masse Fantôme (3 -> 0) en (2,2),(2,3) sur les mêmes colonnes 2 et 3 !
    #     Dans la vérité physique, 3 se désintègre en vide (0) et l'Eau (7) tombe jusqu'au fond (lignes 4-5)
    #     sans rester en lévitation aux lignes 2-3 !
    #   - Dans `test_theta` : un bloc de Plante (4 -> 8) est empilé sur les colonnes 0 et 1 AU-DESSUS
    #     du cycle de Condorcet 392={1,2,4} -> 0, ET de l'Eau (1 -> 7) est empilée AU-DESSUS du noyau 3 -> 0 !
    #     Les deux piles traversent les masses fantômes désintégrées et chutent jusqu'au sol !
    # -------------------------------------------------------------------------
    train_theta1 = [
        [1, 1, 0, 0, 2, 2],  # Col 0-1 : Collision H {1, 2} (118) -> 7
        [2, 2, 1, 1, 4, 4],  # Col 2-3 : Eau (1 -> 7) placée AU-DESSUS de la Masse Fantôme (3 -> 0) !
        [0, 0, 3, 3, 0, 0],  # Col 2-3 : Masse Fantôme (3 -> 0) SOUS l'Eau (1 -> 7) !
        [0, 0, 0, 0, 0, 1],  # Bruit isolé érodé
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    train_theta2 = [
        [4, 4, 0, 0, 1, 1],  # Col 0-1 : Collision H {1, 4} (120) -> 8 (4 > 1)
        [4, 4, 2, 2, 0, 0],  # Col 0-1 : Plante pure (4 -> 8) ; Col 2-3 : Feu (2 -> 6) AU-DESSUS de 3 -> 0 !
        [1, 1, 3, 3, 0, 0],  # Col 0-1 : Eau pure (1 -> 7) ; Col 2-3 : Masse Fantôme (3 -> 0) SOUS le Feu (2 -> 6) !
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],  # Bruit isolé érodé
    ]
    test_theta = [
        [1, 1, 0, 0, 2, 2],  # + Ligne 5 (4, 4) -> Cycle Condorcet 392={1,2,4} -> 0 SOUS la colonne 0-1 !
        [0, 0, 1, 1, 0, 0],  # Col 2-3 : Eau (1 -> 7) placée AU-DESSUS de la Masse Fantôme (3 -> 0) !
        [4, 4, 3, 3, 0, 0],  # Col 0-1 : Plante (4 -> 8) AU-DESSUS de 392->0 ; Col 2-3 : Masse Fantôme 3->0 !
        [0, 0, 0, 0, 0, 1],  # Bruit isolé érodé
        [0, 0, 0, 0, 0, 0],
        [4, 4, 0, 0, 0, 0],  # Percute {1, 2} de Ligne 0 -> 392={1,2,4} -> 0 (se désintègre sous Plante 4->8 !)
    ]
    paires_theta = [
        (train_theta1, appliquer_loi_secrete(train_theta1, etapes_epsilon, palette_train_eta)),
        (train_theta2, appliquer_loi_secrete(train_theta2, etapes_epsilon, palette_train_eta)),
    ]
    attendu_test_theta = appliquer_loi_secrete(test_theta, etapes_epsilon, palette_verite_eta)

    # -------------------------------------------------------------------------
    # ÉPREUVE IOTA (CONTRE-EXEMPLE RED-TEAM V6 DE GEMINI — SANDWICH FANTÔME & PROPAGATION INTER-EXEMPLES) :
    #   - Faille N (Sandwich entre deux blocs de la MÊME couleur) :
    #     Dans `train_iota1`, les colonnes 2 et 3 contiennent un SANDWICH [1, 3, 1] :
    #     de l'Eau (1 -> 7) en ligne 0, une Masse Fantôme (3 -> 0) au milieu en ligne 1,
    #     et de l'Eau (1 -> 7) en bas en ligne 2 ! Après désintégration du cœur 3 -> 0,
    #     les deux tranches d'Eau (7 et 7) fusionnent au fond de la colonne !
    #   - Faille M (Propagation Inter-Exemples & Sandwich de Condorcet) :
    #     Dans `test_iota`, le cycle de Condorcet 392={1,2,4} -> 0 est lui-même pris en
    #     SANDWICH entre deux blocs actifs sur les colonnes 0 et 1, tandis que le sandwich
    #     [2, 3, 2] -> [6, 6] s'affaisse sur les colonnes 2 et 3 !
    # -------------------------------------------------------------------------
    train_iota1 = [
        [1, 1, 1, 1, 2, 2],  # Col 0-1 : {1, 2}=118->7 ; Col 2-3 (Haut du Sandwich) : Eau (1 -> 7) !
        [2, 2, 3, 3, 4, 4],  # Col 0-1 : {2, 4}=136->6 ; Col 2-3 (Cœur du Sandwich) : Masse Fantôme (3 -> 0) !
        [0, 0, 1, 1, 0, 0],  # Col 2-3 (Bas du Sandwich) : Eau (1 -> 7) SOUS la Masse Fantôme 3 -> 0 !
        [0, 0, 0, 0, 0, 1],  # Bruit isolé érodé
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    train_iota2 = [
        [4, 4, 0, 0, 1, 1],  # Col 0-1 : {1, 4}=120->8 (Plante 4 bat Eau 1)
        [4, 4, 2, 2, 0, 0],  # Col 0-1 : Plante (4 -> 8) ; Col 2-3 (Haut du Sandwich) : Feu (2 -> 6) !
        [0, 0, 3, 3, 0, 0],  # Col 2-3 (Cœur du Sandwich) : Masse Fantôme (3 -> 0) !
        [0, 0, 2, 2, 0, 0],  # Col 2-3 (Bas du Sandwich) : Feu (2 -> 6) SOUS la Masse Fantôme 3 -> 0 !
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],  # Bruit isolé érodé
    ]
    test_iota = [
        [4, 4, 2, 2, 0, 0],  # Col 0-1 (Haut du Sandwich) : Plante (4 -> 8) ; Col 2-3 (Haut) : Feu (2 -> 6)
        [1, 1, 3, 3, 2, 2],  # Col 0-1 + Ligne 4 (4,4) -> Cœur du Sandwich Condorcet 392={1,2,4}->0 ! Col 2-3 : 3->0 !
        [1, 1, 2, 2, 0, 0],  # Col 0-1 (Bas du Sandwich) : Eau (1 -> 7) ; Col 2-3 (Bas) : Feu (2 -> 6) !
        [0, 0, 0, 0, 0, 1],  # Bruit isolé érodé
        [4, 4, 0, 0, 0, 0],  # Miroir V de Ligne 1 -> crée le cycle de Condorcet 392->0 au milieu du sandwich !
        [0, 0, 0, 0, 0, 0],
    ]
    paires_iota = [
        (train_iota1, appliquer_loi_secrete(train_iota1, etapes_epsilon, palette_train_eta)),
        (train_iota2, appliquer_loi_secrete(train_iota2, etapes_epsilon, palette_train_eta)),
    ]
    attendu_test_iota = appliquer_loi_secrete(test_iota, etapes_epsilon, palette_verite_eta)

    # -------------------------------------------------------------------------
    # ÉPREUVE KAPPA (CONTRE-EXEMPLE RED-TEAM V7 DE GEMINI — DEADLOCK CROISÉ & ÉMERGENCE N-CORPS) :
    #   1. Faille P (Cross-Resolution Deadlock) :
    #      - `train_kappa1` révèle `118 -> 7` et l'émergence à 3 corps `392 -> 9` en col 0-1, mais sa
    #        col 2-3 (`[136, 120, 1, 1, 120, 136] -> [6, 7, 7, 6]`) bloque sur deux inconnues (`136` et `120`).
    #      - `train_kappa2` révèle `136 -> 6` en col 0-1, mais sa col 2-3 (`[118, 120, 120, 118] -> [7, 7]`)
    #        bloque sur deux inconnues (`118` et `120`).
    #      En silo individuel, `inferer_bijection_palette_o1(train_kappa1)` == None ET
    #      `inferer_bijection_palette_o1(train_kappa2)` == None ! Seul le Faisceau Global de Fibres V8.0
    #      brise le deadlock et découvre simultanément l'annihilation binaire `120 -> 0`.
    #   2. Faille Q (Physique Émergente N-Corps vs Annihilation Binaire) :
    #      - À 2 corps, `{1, 4} = 120 -> 0` s'annihile (Matière + Antimatière -> Vide).
    #      - Mais à 3 corps, `{1, 2, 4} = 392 -> 9` fusionne en Or (`9`) !
    #      - Et en test OOD (`test_kappa`), une collision inédite à 4 CORPS `{1, 2, 3, 4} = 4472`
    #        est réduite vers l'hyper-arête à 3 corps `392 -> 9` (Or) tout en traversant le vide créé
    #        par l'annihilation binaire `120 -> 0` située juste en dessous !
    # -------------------------------------------------------------------------
    palette_train_kappa = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 118: 7, 136: 6, 120: 0, 392: 9}
    palette_verite_kappa = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 118: 7, 136: 6, 120: 0, 392: 9, 4472: 9}

    train_kappa1 = [
        [1, 1, 2, 2, 2, 2],
        [1, 1, 1, 1, 4, 4],
        [1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [2, 2, 4, 4, 0, 0],
        [0, 0, 4, 4, 0, 0],
    ]
    train_kappa2 = [
        [2, 2, 1, 1, 4, 4],
        [2, 2, 1, 1, 0, 0],
        [4, 4, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, 0, 4, 4, 0, 0],
        [0, 0, 2, 2, 0, 0],
    ]
    test_kappa = [
        [1, 1, 2, 2, 2, 2],
        [1, 1, 3, 3, 4, 4],
        [2, 2, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0],
        [3, 3, 0, 0, 4, 4],
    ]
    paires_kappa = [
        (train_kappa1, appliquer_loi_secrete(train_kappa1, etapes_epsilon, palette_train_kappa)),
        (train_kappa2, appliquer_loi_secrete(train_kappa2, etapes_epsilon, palette_train_kappa)),
    ]
    attendu_test_kappa = appliquer_loi_secrete(test_kappa, etapes_epsilon, palette_verite_kappa)

    # -------------------------------------------------------------------------
    # ÉPREUVE LAMBDA (V9.0 - Faille R « La Limite de Gödel » : Automate de Sable Asynchrone & Transport Inter-Fibres) :
    #   Remplace Gravite_Bas par Automate_Avalanche (dynamique granulaire non-linéaire et non-commutative
    #   où les grains dévient en diagonale c+1 / c-1 lorsqu'ils percutent un obstacle).
    #   - Sans purge pré-transport du noyau ker(phi) = {3, 120}, les grains rebondissent sur les masses
    #     fantômes (3->0 et 120->0) et changent de colonne (brisure d'invariance par fibre).
    #   - Grâce au Solveur Lagrangien Diophantien V9.0, le moteur identifie ker(phi) en O(1) par perte
    #     de masse exacte, purge l'état pré-transport et résout le deadlock croisé + l'émergence 4-corps OOD !
    # -------------------------------------------------------------------------
    etapes_lambda = [
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.cloture_miroir_vertical,
        InvariancePrimitives.cloture_miroir_horizontal,
        InvariancePrimitives.automate_avalanche_sable,
    ]
    cible_l1 = appliquer_loi_secrete(train_kappa1, etapes_lambda, palette_train_kappa)
    cible_l2 = appliquer_loi_secrete(train_kappa2, etapes_lambda, palette_train_kappa)
    paires_lambda = [
        (train_kappa1, cible_l1),
        (train_kappa2, cible_l2),
    ]
    attendu_test_lambda = appliquer_loi_secrete(test_kappa, etapes_lambda, palette_verite_kappa)

    # -------------------------------------------------------------------------
    # ÉPREUVE MU (V10.0 - Faille S : Sabotage Adversarial Byzantin de l'Équation Diophantienne & d'Avalanche) :
    #   Un adversaire actif corrompt délibérément 4 pixels dans les cibles d'entraînement de l'Avalanche :
    #   - Grille 1 : injecte un faux grain dans le vide (0, 2) : 0 -> 8 (sabote Delta_M_1 de -1 !)
    #                et falsifie un grain d'Or 3-corps en (5, 2) : 9 -> 6 !
    #   - Grille 2 : efface un grain solide au fond en (5, 0) : 6 -> 0 (sabote Delta_M_2 de +1 !)
    #                et falsifie un grain en (5, 1) : 7 -> 8 !
    #   Le moteur V10.0 absorbe le sabotage via la Fenêtre Diophantienne de Hamming, vote par consensus
    #   Byzantin, localise les 4 pixels menteurs par leur Syndrome L0 et réussit le test OOD à 100 % !
    # -------------------------------------------------------------------------
    cible_mu1 = [row[:] for row in cible_l1]
    cible_mu1[0][2] = 8  # Sabotage 1 : fausse matière dans le vide (casse Delta_M_1 de -1)
    cible_mu1[4][0] = 6  # Sabotage 2 : corruption d'un grain d'Or 3-corps 9 -> 6
    cible_mu2 = [row[:] for row in cible_l2]
    cible_mu2[5][0] = 0  # Sabotage 3 : trou impossible au fond de l'avalanche (casse Delta_M_2 de +1)
    cible_mu2[5][1] = 8  # Sabotage 4 : falsification chromatique 6 -> 8
    paires_mu = [
        (train_kappa1, cible_mu1),
        (train_kappa2, cible_mu2),
    ]

    epreuves = [
        ("ÉPREUVE ALPHA   (3 étages non-linéaires + Palette)", paires_alpha, test_a, attendu_test_a),
        ("ÉPREUVE BÊTA    (3 étages symétrie/gravité + Palette)", paires_beta, test_b, attendu_test_b),
        ("ÉPREUVE OMÉGA   (4 étages profonds + Automate + Palette)", paires_omega, test_o, attendu_test_o),
        ("ÉPREUVE DELTA   (Collision Miroir + Destruction 3->0)", paires_delta, test_d, attendu_test_d),
        ("ÉPREUVE EPSILON (Eau 1 bat Sable 4 + Alchimie 1+2->9 + Kaléidoscope x4)", paires_epsilon, test_e, attendu_test_e),
        ("ÉPREUVE ZÊTA    (Triple Collision OOD 392={1,2,4}->9 + Noyau OOD 119={1,3}->7)", paires_epsilon, test_z, attendu_test_z),
        ("ÉPREUVE ÊTA     (Condorcet Pierre-Papier-Ciseaux 392->0 & 391->7 + BnB Exact)", paires_eta, test_eta, attendu_test_eta),
        ("ÉPREUVE THÊTA   (Paradoxe Masse Fantôme : Chute à travers 3->0 et 392->0)", paires_theta, test_theta, attendu_test_theta),
        ("ÉPREUVE IOTA    (Sandwich Fantôme [1,3,1]->[7,7] & Sandwich Condorcet 392->0)", paires_iota, test_iota, attendu_test_iota),
        ("ÉPREUVE KAPPA   (Deadlock Croisé P + Émergence 3-Corps 392->9 & 4-Corps 4472->9)", paires_kappa, test_kappa, attendu_test_kappa),
        ("ÉPREUVE LAMBDA  (Limite de Gödel R : Avalanche de Sable Asynchrone Inter-Colonnes)", paires_lambda, test_kappa, attendu_test_lambda),
        ("ÉPREUVE MU      (Sabotage Adversarial Byzantin S : 4 Pixels Menteurs & Syndrome L0)", paires_mu, test_kappa, attendu_test_lambda),
    ]

    t_global = time.perf_counter()
    reussites = 0

    for nom, paires, t_in, t_attendu in epreuves:
        print(f"\n🚀 Lancement : {nom}")
        res = moteur.resoudre_loi_cachee_multi_exemples(paires, test_input=t_in, max_profondeur=4, beam_width=128)
        exact = (res.get("prediction_test") == t_attendu)
        if res.get("succes") and exact:
            reussites += 1
            print(f"   ✅ STATUT            : LOI CACHÉE DÉCOUVERTE & TEST 100.00% PIXEL-PERFECT")
            print(f"   🧬 Formule Synthétisée: {res['formule_mathematique']}")
            if any(res.get("syndrome_adversarial", [])):
                print(f"   🛡️ Syndrome Byzantin  : Pixels menteurs démasqués (r, c, faux, vrai) = {res['syndrome_adversarial']}")
            print(f"   ⚡ Temps d'exécution : {res['temps_ms']} ms (0 Watt GPU / CPU pur)")
            print(f"   🔍 États évalués     : {res['evaluations_reelles']} sur {res['espace_combinatoire_brut']:,} possibles")
            print(f"   📐 Compression Thot  : {res['facteur_compression_thot']:,.0f}x d'élagage déterministe")
        else:
            print(f"   ❌ ÉCHEC : {res}")

    dt_tot = round((time.perf_counter() - t_global) * 1000, 2)
    print("\n" + "=" * 78)
    print(f" 🏆 BILAN FINAL : {reussites}/{len(epreuves)} LOIS IMPOSSIBLES DÉCOUVERTES EN {dt_tot} ms !")
    print("=" * 78)
    return reussites == len(epreuves)


if __name__ == "__main__":
    ok = executer_banc_impossible()
    raise SystemExit(0 if ok else 1)
