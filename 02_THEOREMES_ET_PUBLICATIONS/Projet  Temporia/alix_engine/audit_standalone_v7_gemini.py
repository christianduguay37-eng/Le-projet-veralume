#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET TEMPORIA / ALIX ENGINE — SYNTHÈSE DE LOIS CACHÉES NON-LINÉAIRES (0 WATT)
MODULE AUTONOME V8.0 (CORRECTIFS DES FAILLES P & Q DE L'AUDIT RED-TEAM V7.0)
================================================================================
Correctifs V8.0 intégrés suite à l'audit Red-Team de la V7.0 :
1. Correction Faille P (Unification Tensorielle du Faisceau Global de Fibres) :
   Au lieu d'exiger qu'un exemple d'entraînement A soit intégralement résolu en
   silo avant de transmettre ses règles à l'exemple B (ce qui créait un
   Cross-Resolution Deadlock si A bloquait sur une règle de B et B bloquait sur
   une règle de A), `inferer_bijection_faisceau_global` réunit TOUTES les fibres
   (colonnes/lignes) de tous les exemples d'entraînement dans un unique Faisceau
   Global F_global résolu par un point-fixe synchrone en O(K*H*W).
2. Correction Faille Q (Physique Émergente N-Corps & Hypergraphe Stratifié) :
   - Sur toute fibre sans surplus de masse fantôme (`len(p_s) == len(p_t)`),
     l'extraction directe a priorité absolue sur le graphe binaire de Condorcet,
     permettant d'apprendre des lois d'émergence à 3 corps (ex: {1,2,4}=392 -> 9
     Or) même lorsque les paires 2 à 2 s'annihilent ({1,4}=120 -> 0) !
   - Lors du test OOD à 4 corps (ex: {1,2,3,4}=4472), `resoudre_projection_ood`
     interroge les hyper-arêtes N-corps de `bijection` avant les paires binaires,
     réduisant 4472 -> 392 -> 9 (Or) tout en traversant le vide gravitationnel
     créé par l'annihilation binaire 120 -> 0.
3. Bonus V8.0 (Signature d'État Taguée par Régime Gravitationnel) :
   Sur une grille saturée de masses fantômes où `gravite_bas(g) == g` avant
   projection, taguer `etats_visites` par `mode_grav` garantit que la relaxation
   causale post-annihilation n'est jamais élidée prématurément.
================================================================================
"""

import sys
import time
from typing import List, Tuple, Dict, Callable, Optional, Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class InvariancePrimitives:
    """Catalogue des opérateurs d'invariance géométrique, topologique et causale (V8.0)."""

    @staticmethod
    def identite(grille: List[List[int]]) -> List[List[int]]:
        return [row[:] for row in grille]

    @staticmethod
    def rotation_90(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        return [[grille[h - 1 - r][c] for r in range(h)] for c in range(w)]

    @staticmethod
    def rotation_180(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        return [row[::-1] for row in grille[::-1]]

    @staticmethod
    def rotation_270(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        return [[grille[r][w - 1 - c] for r in range(h)] for c in range(w)]

    @staticmethod
    def symetrie_horizontale(grille: List[List[int]]) -> List[List[int]]:
        if not grille:
            return []
        return [row[::-1] for row in grille]

    @staticmethod
    def symetrie_verticale(grille: List[List[int]]) -> List[List[int]]:
        if not grille:
            return []
        return [row[:] for row in grille[::-1]]

    @staticmethod
    def transposition_diagonale(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        return [[grille[r][c] for r in range(h)] for c in range(w)]

    @staticmethod
    def gravite_bas(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        res = [[0] * w for _ in range(h)]
        for c in range(w):
            col_vals = [grille[r][c] for r in range(h) if grille[r][c] != 0]
            start_r = h - len(col_vals)
            for idx, val in enumerate(col_vals):
                res[start_r + idx][c] = val
        return res

    @staticmethod
    def gravite_droite(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        res = []
        for r in range(h):
            vals = [v for v in grille[r] if v != 0]
            res.append([0] * (w - len(vals)) + vals)
        return res

    @staticmethod
    def encoder_etat_algebrique(couleurs: List[int]) -> int:
        uniques = sorted(set(c for c in couleurs if c > 0))
        if not uniques:
            return 0
        if len(uniques) == 1:
            return uniques[0]
        code = 0
        for c in uniques:
            code = (code << 4) | (c & 0xF)
        return 100 + code

    @staticmethod
    def decomposer_etat_algebrique(val: int) -> List[int]:
        if val <= 0:
            return []
        if val < 100:
            return [val]
        code = val - 100
        atomes = []
        while code > 0:
            atomes.append(code & 0xF)
            code >>= 4
        return sorted(set(atomes))

    @staticmethod
    def _fusionner_cellules_algebrique(a: int, b: int) -> int:
        if a == 0:
            return b
        if b == 0 or a == b:
            return a
        union_couleurs = sorted(
            set(InvariancePrimitives.decomposer_etat_algebrique(a))
            | set(InvariancePrimitives.decomposer_etat_algebrique(b))
        )
        return InvariancePrimitives.encoder_etat_algebrique(union_couleurs)

    @staticmethod
    def superposition_commutative(grille_a: List[List[int]], grille_b: List[List[int]]) -> List[List[int]]:
        if not grille_a or not grille_b:
            return grille_a or grille_b
        h = min(len(grille_a), len(grille_b))
        w = min(len(grille_a[0]), len(grille_b[0]))
        fusion = InvariancePrimitives._fusionner_cellules_algebrique
        return [[fusion(grille_a[r][c], grille_b[r][c]) for c in range(w)] for r in range(h)]

    @staticmethod
    def cloture_miroir_horizontal(grille: List[List[int]]) -> List[List[int]]:
        return InvariancePrimitives.superposition_commutative(
            grille, InvariancePrimitives.symetrie_horizontale(grille)
        )

    @staticmethod
    def cloture_miroir_vertical(grille: List[List[int]]) -> List[List[int]]:
        return InvariancePrimitives.superposition_commutative(
            grille, InvariancePrimitives.symetrie_verticale(grille)
        )

    @staticmethod
    def automate_frontiere_interne(grille: List[List[int]]) -> List[List[int]]:
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        res = [[0] * w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                val = grille[r][c]
                if val == 0:
                    continue
                voisins = 0
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grille[nr][nc] != 0:
                        voisins += 1
                if voisins >= 1:
                    res[r][c] = val
        return res

    @staticmethod
    def resoudre_projection_ood(val: int, bijection: Dict[int, int]) -> int:
        if val in bijection:
            return bijection[val]
        if val < 100:
            return bijection.get(val, val)

        composantes = [
            c for c in InvariancePrimitives.decomposer_etat_algebrique(val)
            if bijection.get(c, c) != 0
        ]
        if not composantes:
            return 0
        if len(composantes) == 1:
            c0 = composantes[0]
            return bijection.get(c0, c0)

        while len(composantes) > 1:
            # Priorité N-Corps (Faille Q) : si l'hyper-arête d'ordre k >= 2 (ex: 392={1,2,4}->9)
            # est dans bijection, elle l'emporte immédiatement sur les paires binaires !
            code_actuel = InvariancePrimitives.encoder_etat_algebrique(composantes)
            if code_actuel in bijection:
                return bijection[code_actuel]

            dom: Dict[int, set] = {c: set() for c in composantes}
            n = len(composantes)
            for i in range(n):
                for j in range(i + 1, n):
                    ca, cb = composantes[i], composantes[j]
                    code_paire = InvariancePrimitives.encoder_etat_algebrique([ca, cb])
                    if code_paire in bijection:
                        res_paire = bijection[code_paire]
                        proj_a = bijection.get(ca, ca)
                        proj_b = bijection.get(cb, cb)
                        if res_paire == proj_a and proj_a != proj_b:
                            dom[ca].add(cb)
                        elif res_paire == proj_b and proj_a != proj_b:
                            dom[cb].add(ca)

            atteignables: Dict[int, set] = {c: set(dom[c]) for c in composantes}
            for k in composantes:
                for i_c in composantes:
                    if k in atteignables[i_c]:
                        atteignables[i_c] |= atteignables[k]

            survivants = [
                x for x in composantes
                if not any((x in atteignables[y]) and (y not in atteignables[x]) for y in composantes if y != x)
            ]

            if len(survivants) < len(composantes):
                composantes = survivants
                continue

            tous_battus_dans_cycle = all(
                any(x in dom[y] for y in composantes if y != x)
                for x in composantes
            )
            if tous_battus_dans_cycle:
                return 0
            break

        if not composantes:
            return 0
        if len(composantes) == 1:
            c0 = composantes[0]
            return bijection.get(c0, c0)

        code_reduit = InvariancePrimitives.encoder_etat_algebrique(composantes)
        if code_reduit in bijection:
            return bijection[code_reduit]

        produits_alchimiques = set()
        for i in range(len(composantes)):
            for j in range(i + 1, len(composantes)):
                code_paire = InvariancePrimitives.encoder_etat_algebrique([composantes[i], composantes[j]])
                if code_paire in bijection:
                    produits_alchimiques.add(bijection[code_paire])
        if len(produits_alchimiques) == 1:
            return next(iter(produits_alchimiques))

        return 0

    @staticmethod
    def automate_avalanche_sable(grille: List[List[int]]) -> List[List[int]]:
        """
        AUTOMATE CELLULAIRE ASYNCHRONE D'AVALANCHE DE SABLE (Correction Faille R — Non-Commutativité Spatiale) :
        Dynamique granulaire séquentielle (Bak-Tang-Wiesenfeld / Sandpile) où l'ordre de chute des grains
        modifie la topologie inter-colonnes :
        - Chaque grain tombe verticalement tant que (r+1, c) est vide.
        - S'il percute un obstacle sous lui ((r+1, c) != 0) mais qu'un flanc diagonal est libre
          ((r, c+1) == 0 et (r+1, c+1) == 0, ou à gauche c-1), il dévie et roule sur la colonne adjacente !
        """
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        res = [row[:] for row in grille]
        while True:
            mouvement = False
            for r in range(h - 2, -1, -1):
                for c in range(w):
                    val = res[r][c]
                    if val == 0:
                        continue
                    if res[r + 1][c] == 0:
                        res[r + 1][c] = val
                        res[r][c] = 0
                        mouvement = True
                    elif c + 1 < w and res[r][c + 1] == 0 and res[r + 1][c + 1] == 0:
                        res[r + 1][c + 1] = val
                        res[r][c] = 0
                        mouvement = True
                    elif c - 1 >= 0 and res[r][c - 1] == 0 and res[r + 1][c - 1] == 0:
                        res[r + 1][c - 1] = val
                        res[r][c] = 0
                        mouvement = True
            if not mouvement:
                break
        return res

    @staticmethod
    def appliquer_palette(grille: List[List[int]], bijection: Dict[int, int]) -> List[List[int]]:
        resoudre = InvariancePrimitives.resoudre_projection_ood
        return [[resoudre(val, bijection) for val in row] for row in grille]

    @staticmethod
    def appliquer_palette_causale(
        grille: List[List[int]],
        bijection: Dict[int, int],
        derniere_primitive: Optional[str] = None,
        grille_pre_transport: Optional[List[List[int]]] = None
    ) -> List[List[int]]:
        if derniere_primitive == "Automate_Avalanche":
            base = grille_pre_transport if grille_pre_transport is not None else grille
            projetee = InvariancePrimitives.appliquer_palette(base, bijection)
            return InvariancePrimitives.automate_avalanche_sable(projetee)

        projetee = InvariancePrimitives.appliquer_palette(grille, bijection)
        if derniere_primitive == "Gravite_Bas":
            return InvariancePrimitives.gravite_bas(projetee)
        if derniere_primitive == "Gravite_Droite":
            return InvariancePrimitives.gravite_droite(projetee)
        return projetee

    @staticmethod
    def valider_coherence_algebrique_palette(mapping: Dict[int, int]) -> bool:
        if mapping.get(0, 0) != 0:
            return False

        atomiques_nuls = set()
        images_atomiques_actives: Dict[int, int] = {}

        for k, v in mapping.items():
            if 0 < k < 100:
                if v == 0:
                    atomiques_nuls.add(k)
                    if len(atomiques_nuls) > 1:
                        return False
                else:
                    if v in images_atomiques_actives and images_atomiques_actives[v] != k:
                        return False
                    images_atomiques_actives[v] = k

        for k, v in mapping.items():
            if k >= 100 and v > 0:
                comp = InvariancePrimitives.decomposer_etat_algebrique(k)
                atome_proprietaire = images_atomiques_actives.get(v)
                if atome_proprietaire is not None and atome_proprietaire not in comp:
                    return False

        return True

    @staticmethod
    def extraire_syndrome_adversarial(
        grilles_sources: List[List[List[int]]],
        grilles_cibles_corrompues: List[List[List[int]]],
        bijection: Dict[int, int],
        derniere_primitive: Optional[str] = None,
        grilles_pre_transport: Optional[List[List[List[int]]]] = None
    ) -> List[List[Tuple[int, int, int, int]]]:
        syndromes: List[List[Tuple[int, int, int, int]]] = []
        for idx, (g_s, g_cib) in enumerate(zip(grilles_sources, grilles_cibles_corrompues)):
            g_pre = grilles_pre_transport[idx] if grilles_pre_transport else None
            g_pure = InvariancePrimitives.appliquer_palette_causale(g_s, bijection, derniere_primitive, g_pre)
            h, w = len(g_cib), len(g_cib[0])
            anomalies = []
            for r in range(h):
                for c in range(w):
                    if g_cib[r][c] != g_pure[r][c]:
                        anomalies.append((r, c, g_cib[r][c], g_pure[r][c]))
            syndromes.append(anomalies)
        return syndromes

    @staticmethod
    def inferer_bijection_faisceau_global(
        grilles_sources: List[List[List[int]]],
        grilles_cibles: List[List[List[int]]],
        autoriser_projection_zero: bool = True,
        derniere_primitive: Optional[str] = None,
        noyau_attendu: Optional[int] = None,
        palette_initiale: Optional[Dict[int, int]] = None,
        grilles_pre_transport: Optional[List[List[List[int]]]] = None,
        tolerance_adversariale: int = 0
    ) -> Optional[Dict[int, int]]:
        if not grilles_sources or not grilles_cibles or len(grilles_sources) != len(grilles_cibles):
            return None

        for g_src, g_cib in zip(grilles_sources, grilles_cibles):
            if not g_src or not g_cib:
                return None
            if len(g_src) != len(g_cib) or len(g_src[0]) != len(g_cib[0]):
                return None
            h, w = len(g_src), len(g_src[0])
            m_s = sum(1 for r in range(h) for c in range(w) if g_src[r][c] != 0)
            m_t = sum(1 for r in range(h) for c in range(w) if g_cib[r][c] != 0)
            if m_s + tolerance_adversariale < m_t:
                return None

        # --- PASSE 1 : Alignement spatial direct global ---
        mapping: Dict[int, int] = dict(palette_initiale) if palette_initiale else {0: 0}
        mapping[0] = 0
        direct_ok = True
        for g_src, g_cib in zip(grilles_sources, grilles_cibles):
            h, w = len(g_src), len(g_src[0])
            for r in range(h):
                for c in range(w):
                    s_val = g_src[r][c]
                    t_val = g_cib[r][c]
                    if not autoriser_projection_zero and ((s_val == 0) != (t_val == 0)):
                        direct_ok = False
                        break
                    if s_val in mapping:
                        if mapping[s_val] != t_val:
                            direct_ok = False
                            break
                    else:
                        mapping[s_val] = t_val
                if not direct_ok:
                    break
            if not direct_ok:
                break

        if direct_ok and InvariancePrimitives.valider_coherence_algebrique_palette(mapping):
            if derniere_primitive in ("Gravite_Bas", "Gravite_Droite", "Automate_Avalanche"):
                if all(
                    InvariancePrimitives.appliquer_palette_causale(
                        g_s, mapping, derniere_primitive,
                        grilles_pre_transport[idx] if grilles_pre_transport else None
                    ) == g_c
                    for idx, (g_s, g_c) in enumerate(zip(grilles_sources, grilles_cibles))
                ):
                    return mapping
            else:
                return mapping

        # --- PASSE 3 & 3B : Solveur Lagrangien Diophantien & Décodage Byzantin L0 (Failles R & S) ---
        if autoriser_projection_zero and (
            derniere_primitive == "Automate_Avalanche"
            or (tolerance_adversariale > 0 and derniere_primitive in ("Gravite_Bas", "Gravite_Droite"))
        ):
            sources_pre = grilles_pre_transport if grilles_pre_transport is not None else grilles_sources
            freqs_par_grille: List[Dict[int, int]] = []
            deficits_masse: List[int] = []
            toutes_couleurs: set = set()

            for g_pre, g_cib in zip(sources_pre, grilles_cibles):
                h, w = len(g_pre), len(g_pre[0])
                fq: Dict[int, int] = {}
                m_pre = 0
                for r in range(h):
                    for c in range(w):
                        v = g_pre[r][c]
                        if v != 0:
                            fq[v] = fq.get(v, 0) + 1
                            m_pre += 1
                            toutes_couleurs.add(v)
                m_cib = sum(1 for r in range(h) for c in range(w) if g_cib[r][c] != 0)
                if m_pre + tolerance_adversariale < m_cib:
                    return None
                freqs_par_grille.append(fq)
                deficits_masse.append(m_pre - m_cib)

            atomes_cand: List[Optional[int]] = [None] + sorted(k for k in toutes_couleurs if 0 < k < 100)
            comps_cand: List[Optional[int]] = [None] + sorted(k for k in toutes_couleurs if k >= 100)

            # 3A. Mode Diophantien Exact (0 erreur)
            if derniere_primitive == "Automate_Avalanche":
                for k_at in atomes_cand:
                    if noyau_attendu is not None and k_at is not None and k_at != noyau_attendu:
                        continue
                    for k_comp in comps_cand:
                        masse_exacte = True
                        for fq, dm in zip(freqs_par_grille, deficits_masse):
                            m_ker = (fq.get(k_at, 0) if k_at is not None else 0) + (
                                fq.get(k_comp, 0) if k_comp is not None else 0
                            )
                            if m_ker != dm:
                                masse_exacte = False
                                break
                        if not masse_exacte:
                            continue

                        map_av: Dict[int, int] = dict(palette_initiale) if palette_initiale else {0: 0}
                        map_av[0] = 0
                        if k_at is not None:
                            map_av[k_at] = 0
                        if k_comp is not None:
                            map_av[k_comp] = 0

                        aligne_ok = True
                        for g_pre, g_cib in zip(sources_pre, grilles_cibles):
                            h, w = len(g_pre), len(g_pre[0])
                            g_purgee = [
                                [0 if (v == k_at or v == k_comp or map_av.get(v, -1) == 0) else v for v in row]
                                for row in g_pre
                            ]
                            g_sim = InvariancePrimitives.automate_avalanche_sable(g_purgee)
                            for r in range(h):
                                for c in range(w):
                                    sv = g_sim[r][c]
                                    tv = g_cib[r][c]
                                    if (sv == 0) != (tv == 0):
                                        aligne_ok = False
                                        break
                                    if sv != 0:
                                        if sv in map_av:
                                            if map_av[sv] != tv:
                                                aligne_ok = False
                                                break
                                        else:
                                            map_av[sv] = tv
                                if not aligne_ok:
                                    break
                            if not aligne_ok:
                                break

                        if aligne_ok and InvariancePrimitives.valider_coherence_algebrique_palette(map_av):
                            if all(
                                InvariancePrimitives.appliquer_palette_causale(
                                    g_s, map_av, "Automate_Avalanche", g_pre
                                ) == g_c
                                for g_s, g_pre, g_c in zip(grilles_sources, sources_pre, grilles_cibles)
                            ):
                                return map_av

            # 3B. Mode Décodage Byzantin par Syndrome de Hamming L0 (Correction Faille S : Sabotage Adversarial)
            if tolerance_adversariale > 0:
                meilleure_map_byz: Optional[Dict[int, int]] = None
                meilleur_syndrome_total = (tolerance_adversariale * len(grilles_cibles)) + 1

                for k_at in atomes_cand:
                    if noyau_attendu is not None and k_at is not None and k_at != noyau_attendu:
                        continue
                    for k_comp in comps_cand:
                        fenetre_ok = True
                        for fq, dm in zip(freqs_par_grille, deficits_masse):
                            m_ker = (fq.get(k_at, 0) if k_at is not None else 0) + (
                                fq.get(k_comp, 0) if k_comp is not None else 0
                            )
                            if abs(m_ker - dm) > tolerance_adversariale:
                                fenetre_ok = False
                                break
                        if not fenetre_ok:
                            continue

                        map_byz: Dict[int, int] = dict(palette_initiale) if palette_initiale else {0: 0}
                        map_byz[0] = 0
                        if k_at is not None:
                            map_byz[k_at] = 0
                        if k_comp is not None:
                            map_byz[k_comp] = 0

                        votes: Dict[int, Dict[int, int]] = {}
                        support_ok = True

                        for g_pre, g_cib in zip(sources_pre, grilles_cibles):
                            h, w = len(g_pre), len(g_pre[0])
                            g_purgee = [
                                [0 if (v == k_at or v == k_comp or map_byz.get(v, -1) == 0) else v for v in row]
                                for row in g_pre
                            ]
                            if derniere_primitive == "Automate_Avalanche":
                                g_sim = InvariancePrimitives.automate_avalanche_sable(g_purgee)
                            elif derniere_primitive == "Gravite_Bas":
                                g_sim = InvariancePrimitives.gravite_bas(g_purgee)
                            else:
                                g_sim = InvariancePrimitives.gravite_droite(g_purgee)

                            err_support = 0
                            for r in range(h):
                                for c in range(w):
                                    sv = g_sim[r][c]
                                    tv = g_cib[r][c]
                                    if (sv == 0) != (tv == 0):
                                        err_support += 1
                                        if err_support > tolerance_adversariale:
                                            support_ok = False
                                            break
                                    elif sv != 0 and tv != 0:
                                        if sv not in votes:
                                            votes[sv] = {}
                                        votes[sv][tv] = votes[sv].get(tv, 0) + 1
                                if not support_ok:
                                    break
                            if not support_ok:
                                break

                        if not support_ok:
                            continue

                        vote_valide = True
                        for sv, urne in votes.items():
                            tv_maj, nb_voix = max(urne.items(), key=lambda kv: kv[1])
                            if nb_voix < 2:
                                vote_valide = False
                                break
                            map_byz[sv] = tv_maj

                        if not vote_valide or not InvariancePrimitives.valider_coherence_algebrique_palette(map_byz):
                            continue

                        syndrome_total = 0
                        syndrome_ok = True
                        for g_s, g_pre, g_cib in zip(grilles_sources, sources_pre, grilles_cibles):
                            g_pred = InvariancePrimitives.appliquer_palette_causale(
                                g_s, map_byz, derniere_primitive, g_pre
                            )
                            h, w = len(g_cib), len(g_cib[0])
                            d_hamming = sum(
                                1 for r in range(h) for c in range(w) if g_pred[r][c] != g_cib[r][c]
                            )
                            if d_hamming > tolerance_adversariale:
                                syndrome_ok = False
                                break
                            syndrome_total += d_hamming

                        if syndrome_ok and syndrome_total < meilleur_syndrome_total:
                            meilleur_syndrome_total = syndrome_total
                            meilleure_map_byz = map_byz
                            if syndrome_total == 0:
                                return meilleure_map_byz

                if meilleure_map_byz is not None:
                    return meilleure_map_byz

            if derniere_primitive == "Automate_Avalanche":
                return None

        # --- PASSE 2 : Faisceau Global de Fibres sous Gravité (Failles J, M, N, O, P, Q) ---
        if autoriser_projection_zero and derniere_primitive in ("Gravite_Bas", "Gravite_Droite"):
            fibres_s: List[List[int]] = []
            fibres_t: List[List[int]] = []

            for g_src, g_cib in zip(grilles_sources, grilles_cibles):
                h, w = len(g_src), len(g_src[0])
                if derniere_primitive == "Gravite_Bas":
                    for c in range(w):
                        fibres_s.append([g_src[r][c] for r in range(h) if g_src[r][c] != 0])
                        fibres_t.append([g_cib[r][c] for r in range(h) if g_cib[r][c] != 0])
                else:
                    for r in range(h):
                        fibres_s.append([v for v in g_src[r] if v != 0])
                        fibres_t.append([v for v in g_cib[r] if v != 0])

            for fs, ft in zip(fibres_s, fibres_t):
                if len(fs) < len(ft):
                    return None

            toutes_couleurs_src = sorted({v for fs in fibres_s for v in fs})
            atomes_src = [k for k in toutes_couleurs_src if 0 < k < 100]
            if noyau_attendu is not None:
                candidats_noyau: List[Optional[int]] = [noyau_attendu]
            else:
                candidats_noyau = [None] + atomes_src

            for atome_nul in candidats_noyau:
                if atome_nul is not None:
                    if any(sum(1 for v in fs if v != atome_nul) < len(ft) for fs, ft in zip(fibres_s, fibres_t)):
                        continue

                map_test: Dict[int, int] = dict(palette_initiale) if palette_initiale else {0: 0}
                map_test[0] = 0
                if atome_nul is not None:
                    if atome_nul in map_test and map_test[atome_nul] != 0:
                        continue
                    map_test[atome_nul] = 0

                incoherant = False
                for iter_pf in range(6):
                    progres = False
                    for fs, ft in zip(fibres_s, fibres_t):
                        p_s = [v for v in fs if v != atome_nul and map_test.get(v, -1) != 0]
                        p_t = list(ft)

                        if iter_pf >= 1 and len(p_s) > len(p_t):
                            p_s_reduit = []
                            for v in p_s:
                                if v >= 100 and v not in map_test:
                                    comp_v = InvariancePrimitives.decomposer_etat_algebrique(v)
                                    if all(c in map_test for c in comp_v):
                                        if InvariancePrimitives.resoudre_projection_ood(v, map_test) == 0:
                                            map_test[v] = 0
                                            progres = True
                                            continue
                                p_s_reduit.append(v)
                            p_s = p_s_reduit

                        if len(p_s) < len(p_t):
                            incoherant = True
                            break

                        if len(p_s) == len(p_t):
                            for sv, tv in zip(p_s, p_t):
                                if sv in map_test:
                                    if map_test[sv] != tv:
                                        incoherant = True
                                        break
                                else:
                                    map_test[sv] = tv
                                    progres = True
                            if incoherant:
                                break
                            continue

                        idx_haut_s, idx_bas_s = 0, len(p_s) - 1
                        idx_haut_t, idx_bas_t = 0, len(p_t) - 1

                        while idx_haut_s <= idx_bas_s and idx_haut_t <= idx_bas_t:
                            sv = p_s[idx_haut_s]
                            est_solide = (0 < sv < 100) or (map_test.get(sv, 0) > 0)
                            if not est_solide and iter_pf >= 2 and sv >= 100 and sv not in map_test:
                                proj_ood = InvariancePrimitives.resoudre_projection_ood(sv, map_test)
                                if proj_ood > 0 and proj_ood != sv:
                                    est_solide = True
                            if est_solide:
                                tv = p_t[idx_haut_t]
                                if sv in map_test:
                                    if map_test[sv] != tv:
                                        incoherant = True
                                        break
                                else:
                                    map_test[sv] = tv
                                    progres = True
                                idx_haut_s += 1
                                idx_haut_t += 1
                            else:
                                break

                        if incoherant:
                            break

                        while idx_bas_s >= idx_haut_s and idx_bas_t >= idx_haut_t:
                            sv = p_s[idx_bas_s]
                            est_solide = (0 < sv < 100) or (map_test.get(sv, 0) > 0)
                            if not est_solide and iter_pf >= 2 and sv >= 100 and sv not in map_test:
                                proj_ood = InvariancePrimitives.resoudre_projection_ood(sv, map_test)
                                if proj_ood > 0 and proj_ood != sv:
                                    est_solide = True
                            if est_solide:
                                tv = p_t[idx_bas_t]
                                if sv in map_test:
                                    if map_test[sv] != tv:
                                        incoherant = True
                                        break
                                else:
                                    map_test[sv] = tv
                                    progres = True
                                idx_bas_s -= 1
                                idx_bas_t -= 1
                            else:
                                break

                        if incoherant:
                            break

                        if idx_haut_t > idx_bas_t and idx_haut_s <= idx_bas_s:
                            for idx_m in range(idx_haut_s, idx_bas_s + 1):
                                sv_m = p_s[idx_m]
                                if (0 < sv_m < 100) or (sv_m in map_test and map_test[sv_m] != 0):
                                    incoherant = True
                                    break
                                if sv_m not in map_test:
                                    map_test[sv_m] = 0
                                    progres = True

                        if incoherant:
                            break

                    if incoherant or not progres:
                        break

                if not incoherant and InvariancePrimitives.valider_coherence_algebrique_palette(map_test):
                    if all(
                        InvariancePrimitives.appliquer_palette_causale(g_s, map_test, derniere_primitive) == g_c
                        for g_s, g_c in zip(grilles_sources, grilles_cibles)
                    ):
                        return map_test

        return None

    @staticmethod
    def inferer_bijection_palette_o1(
        grille_source: List[List[int]],
        grille_cible: List[List[int]],
        autoriser_projection_zero: bool = True,
        derniere_primitive: Optional[str] = None,
        noyau_attendu: Optional[int] = None,
        palette_initiale: Optional[Dict[int, int]] = None,
        grille_pre_transport: Optional[List[List[int]]] = None
    ) -> Optional[Dict[int, int]]:
        return InvariancePrimitives.inferer_bijection_faisceau_global(
            [grille_source],
            [grille_cible],
            autoriser_projection_zero=autoriser_projection_zero,
            derniere_primitive=derniere_primitive,
            noyau_attendu=noyau_attendu,
            palette_initiale=palette_initiale,
            grilles_pre_transport=[grille_pre_transport] if grille_pre_transport is not None else None,
        )


class DarwinGenome:
    def __init__(self, nom: str, fonction: Callable[[List[List[int]]], List[List[int]]], profondeur: int = 1):
        self.nom = nom
        self.fonction = fonction
        self.profondeur = profondeur


class DarwinEngine:
    """Moteur Darwinien de synthèse de lois cachées non-linéaires à 0 Watt (V9.0)."""

    def __init__(self):
        self.primitives: List[DarwinGenome] = [
            DarwinGenome("Identite", InvariancePrimitives.identite, 1),
            DarwinGenome("Rotation_90", InvariancePrimitives.rotation_90, 1),
            DarwinGenome("Rotation_180", InvariancePrimitives.rotation_180, 1),
            DarwinGenome("Rotation_270", InvariancePrimitives.rotation_270, 1),
            DarwinGenome("Symetrie_H", InvariancePrimitives.symetrie_horizontale, 1),
            DarwinGenome("Symetrie_V", InvariancePrimitives.symetrie_verticale, 1),
            DarwinGenome("Transposition_Diag", InvariancePrimitives.transposition_diagonale, 1),
            DarwinGenome("Gravite_Bas", InvariancePrimitives.gravite_bas, 1),
            DarwinGenome("Gravite_Droite", InvariancePrimitives.gravite_droite, 1),
            DarwinGenome("Cloture_Miroir_H", InvariancePrimitives.cloture_miroir_horizontal, 1),
            DarwinGenome("Cloture_Miroir_V", InvariancePrimitives.cloture_miroir_vertical, 1),
            DarwinGenome("Automate_Erosion", InvariancePrimitives.automate_frontiere_interne, 1),
            DarwinGenome("Automate_Avalanche", InvariancePrimitives.automate_avalanche_sable, 1),
        ]

    @staticmethod
    def extraire_signature_spectrale(grille: List[List[int]]) -> Tuple[int, ...]:
        counts: Dict[int, int] = {}
        for row in grille:
            for val in row:
                if val != 0:
                    counts[val] = counts.get(val, 0) + 1
        return tuple(sorted(counts.values(), reverse=True))

    @staticmethod
    def _partition_exacte_branch_and_bound(
        masses_src: List[int],
        masses_cib: Tuple[int, ...],
        max_noeuds: int = 64
    ) -> float:
        tot_s = sum(masses_src)
        tot_t = sum(masses_cib)
        if tot_s == 0 and tot_t == 0:
            return 0.0
        if tot_s == 0 or tot_t == 0:
            return 1.0

        p_src = sorted((m / tot_s for m in masses_src), reverse=True)
        p_cib = [m / tot_t for m in masses_cib]
        q = len(p_cib)
        p = len(p_src)

        bins = [0.0] * q
        meilleur_surplus = [1.0]
        noeuds_explores = [0]

        def dfs(idx: int, surplus_courant: float) -> None:
            if surplus_courant >= meilleur_surplus[0] - 1e-9:
                return
            if noeuds_explores[0] >= max_noeuds:
                return
            noeuds_explores[0] += 1
            if idx == p:
                meilleur_surplus[0] = surplus_courant
                return

            masse = p_src[idx]
            deficits = sorted(range(q), key=lambda j: p_cib[j] - bins[j], reverse=True)
            etats_vus = set()

            for j in deficits:
                cle_symetrie = (round(bins[j], 9), round(p_cib[j], 9))
                if cle_symetrie in etats_vus:
                    continue
                etats_vus.add(cle_symetrie)

                avant = max(0.0, bins[j] - p_cib[j])
                bins[j] += masse
                apres = max(0.0, bins[j] - p_cib[j])
                dfs(idx + 1, surplus_courant + (apres - avant))
                bins[j] -= masse

                if meilleur_surplus[0] <= 1e-9 or noeuds_explores[0] >= max_noeuds:
                    return

        dfs(0, 0.0)
        return min(1.0, meilleur_surplus[0])

    @staticmethod
    def calculer_fitness_topologique(pred: List[List[int]], cible: List[List[int]]) -> float:
        if not pred or not cible:
            return 0.0
        if len(pred) != len(cible) or len(pred[0]) != len(cible[0]):
            return 0.0

        h, w = len(pred), len(pred[0])
        total = h * w
        if total == 0:
            return 1.0

        match_support = 0
        counts_pred: Dict[int, int] = {}
        for r in range(h):
            for c in range(w):
                vp = pred[r][c]
                vc = cible[r][c]
                if (vp == 0) == (vc == 0):
                    match_support += 1
                if vp != 0:
                    counts_pred[vp] = counts_pred.get(vp, 0) + 1

        score_spatial = match_support / total
        spec_cib = DarwinEngine.extraire_signature_spectrale(cible)
        masse_cib = sum(spec_cib)

        if not counts_pred and not spec_cib:
            return 0.65 + 0.35 * score_spatial
        if not counts_pred or not spec_cib:
            return 0.35 * score_spatial

        meilleur_score_spectral = 0.0
        candidats_atomes: List[Optional[int]] = [None] + [k for k in counts_pred if 0 < k < 100]
        candidats_collisions: List[Optional[int]] = [None] + [k for k in counts_pred if k >= 100]

        for k_nul in candidats_atomes:
            for k_comp_nul in candidats_collisions:
                masses = [m for k, m in counts_pred.items() if k != k_nul and k != k_comp_nul]
                masse_surv = sum(masses)
                if masse_surv == 0:
                    continue

                if masse_cib > 0 and masse_surv * 4 < masse_cib:
                    ratio_energie = (masse_surv * 4) / masse_cib
                    eta_energie = ratio_energie * ratio_energie
                else:
                    eta_energie = 1.0

                tv = DarwinEngine._partition_exacte_branch_and_bound(masses, spec_cib, max_noeuds=64)
                score_courant = eta_energie * (1.0 - tv)
                if score_courant > meilleur_score_spectral:
                    meilleur_score_spectral = score_courant
                    if meilleur_score_spectral >= 1.0 - 1e-6:
                        break
            if meilleur_score_spectral >= 1.0 - 1e-6:
                break

        return 0.65 * meilleur_score_spectral + 0.35 * score_spatial

    def resoudre_loi_cachee_multi_exemples(
        self,
        paires_train: List[Tuple[List[List[int]], List[List[int]]]],
        test_input: Optional[List[List[int]]] = None,
        max_profondeur: int = 4,
        beam_width: int = 128,
        max_par_orbite_spectrale: int = 8,
        tolerance_adversariale_max: int = 3
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        nb_ops = len(self.primitives) - 1
        espace_combinatoire_brut = (nb_ops ** max_profondeur) * 3628800

        etats_visites = set()
        evaluations_reelles = 0

        def signature_etat(grilles: List[List[List[int]]]) -> Tuple:
            return tuple(tuple(tuple(row) for row in g) for g in grilles)

        def signature_orbite_spectrale(grilles: List[List[List[int]]]) -> Tuple:
            return tuple(self.extraire_signature_spectrale(g) for g in grilles)

        grilles_cibles_train = [cible for _, cible in paires_train]

        def verifier_et_extraire_palette_globale(
            grilles_courantes: List[List[List[int]]],
            derniere_prim: Optional[str],
            grilles_pre: Optional[List[List[List[int]]]] = None,
            tau: int = 0
        ) -> Optional[Dict[int, int]]:
            return InvariancePrimitives.inferer_bijection_faisceau_global(
                grilles_courantes,
                grilles_cibles_train,
                autoriser_projection_zero=True,
                derniere_primitive=derniere_prim,
                grilles_pre_transport=grilles_pre,
                tolerance_adversariale=tau,
            )

        grilles_init = [entree for entree, _ in paires_train]
        etats_visites.add((signature_etat(grilles_init), None))
        faisceau = [(0.0, 0, [], [], grilles_init)]
        candidats_byzantins = []

        for prof in range(1, max_profondeur + 1):
            candidats_niveau = []
            for _, _, noms_chaine, fns_chaine, grilles_etat in faisceau:
                for prim in self.primitives:
                    if prim.nom == "Identite":
                        continue
                    if prim.nom == "Automate_Erosion" and "Automate_Erosion" in noms_chaine:
                        continue

                    evaluations_reelles += 1
                    nouvelles_grilles = [prim.fonction(g) for g in grilles_etat]
                    mode_grav = prim.nom if prim.nom in ("Gravite_Bas", "Gravite_Droite", "Automate_Avalanche") else None
                    sig = (signature_etat(nouvelles_grilles), mode_grav)
                    if sig in etats_visites:
                        continue
                    etats_visites.add(sig)

                    nouv_noms = noms_chaine + [prim.nom]
                    nouv_fns = fns_chaine + [prim.fonction]
                    derniere_prim = prim.nom

                    bijection_exacte = verifier_et_extraire_palette_globale(
                        nouvelles_grilles, derniere_prim, grilles_etat, 0
                    )
                    if bijection_exacte is not None:
                        dt_ms = round((time.perf_counter() - t0) * 1000, 3)
                        pred_test = None
                        if test_input is not None:
                            curr_t = [row[:] for row in test_input]
                            pre_t = None
                            for idx_fn, fn_step in enumerate(nouv_fns):
                                if idx_fn == len(nouv_fns) - 1:
                                    pre_t = curr_t
                                curr_t = fn_step(curr_t)
                            pred_test = InvariancePrimitives.appliquer_palette_causale(
                                curr_t, bijection_exacte, derniere_prim, pre_t
                            )

                        chaine_formule = " ∘ ".join(reversed(nouv_noms))
                        return {
                            "succes": True,
                            "profondeur": prof,
                            "chaine_operateurs": nouv_noms,
                            "formule_mathematique": f"Palette({bijection_exacte}) ∘ {chaine_formule}",
                            "bijection_palette": bijection_exacte,
                            "syndrome_adversarial": [],
                            "evaluations_reelles": evaluations_reelles,
                            "espace_combinatoire_brut": espace_combinatoire_brut,
                            "facteur_compression_thot": round(espace_combinatoire_brut / max(1, evaluations_reelles), 1),
                            "temps_ms": dt_ms,
                            "prediction_test": pred_test,
                        }

                    fit_moyen = sum(
                        self.calculer_fitness_topologique(g_p, g_c)
                        for g_p, (_, g_c) in zip(nouvelles_grilles, paires_train)
                    ) / len(paires_train)

                    candidats_niveau.append(
                        (fit_moyen, -evaluations_reelles, nouv_noms, nouv_fns, nouvelles_grilles)
                    )
                    if prof == max_profondeur and derniere_prim in ("Automate_Avalanche", "Gravite_Bas", "Gravite_Droite"):
                        candidats_byzantins.append(
                            (fit_moyen, prof, nouv_noms, nouv_fns, nouvelles_grilles, grilles_etat)
                        )

            candidats_niveau.sort(key=lambda x: (x[0], x[1]), reverse=True)
            faisceau_diversifie = []
            compteur_orbites: Dict[Tuple, int] = {}
            for cand in candidats_niveau:
                sig_orbite = signature_orbite_spectrale(cand[4])
                c_orb = compteur_orbites.get(sig_orbite, 0)
                if c_orb < max_par_orbite_spectrale:
                    faisceau_diversifie.append(cand)
                    compteur_orbites[sig_orbite] = c_orb + 1
                    if len(faisceau_diversifie) >= beam_width:
                        break
            faisceau = faisceau_diversifie
            if not faisceau:
                break

        # Repli Byzantin Automatique (Correction Faille S : Décodage par Syndrome L0 face aux pixels menteurs)
        if tolerance_adversariale_max > 0 and candidats_byzantins:
            candidats_byzantins.sort(key=lambda x: x[0], reverse=True)
            meilleur_res_byz = None
            meilleur_poids_syndrome = (tolerance_adversariale_max * len(paires_train)) + 1

            for fit_m, prof, nouv_noms, nouv_fns, nouvelles_grilles, grilles_pre in candidats_byzantins:
                derniere_prim = nouv_noms[-1]
                palette_byz = verifier_et_extraire_palette_globale(
                    nouvelles_grilles, derniere_prim, grilles_pre, tolerance_adversariale_max
                )
                if palette_byz is not None:
                    syndromes = InvariancePrimitives.extraire_syndrome_adversarial(
                        nouvelles_grilles, grilles_cibles_train, palette_byz, derniere_prim, grilles_pre
                    )
                    poids_syndrome = sum(len(s) for s in syndromes)
                    if poids_syndrome < meilleur_poids_syndrome:
                        meilleur_poids_syndrome = poids_syndrome
                        meilleur_res_byz = (prof, nouv_noms, nouv_fns, palette_byz, syndromes)
                        if poids_syndrome <= 2:
                            break

            if meilleur_res_byz is not None:
                prof, nouv_noms, nouv_fns, bijection_exacte, syndromes = meilleur_res_byz
                derniere_prim = nouv_noms[-1]
                dt_ms = round((time.perf_counter() - t0) * 1000, 3)
                pred_test = None
                if test_input is not None:
                    curr_t = [row[:] for row in test_input]
                    pre_t = None
                    for idx_fn, fn_step in enumerate(nouv_fns):
                        if idx_fn == len(nouv_fns) - 1:
                            pre_t = curr_t
                        curr_t = fn_step(curr_t)
                    pred_test = InvariancePrimitives.appliquer_palette_causale(
                        curr_t, bijection_exacte, derniere_prim, pre_t
                    )

                chaine_formule = " ∘ ".join(reversed(nouv_noms))
                return {
                    "succes": True,
                    "profondeur": prof,
                    "chaine_operateurs": nouv_noms,
                    "formule_mathematique": f"Palette({bijection_exacte}) ∘ {chaine_formule}",
                    "bijection_palette": bijection_exacte,
                    "syndrome_adversarial": syndromes,
                    "evaluations_reelles": evaluations_reelles,
                    "espace_combinatoire_brut": espace_combinatoire_brut,
                    "facteur_compression_thot": round(espace_combinatoire_brut / max(1, evaluations_reelles), 1),
                    "temps_ms": dt_ms,
                    "prediction_test": pred_test,
                }

        dt_ms = round((time.perf_counter() - t0) * 1000, 3)
        return {
            "succes": False,
            "evaluations_reelles": evaluations_reelles,
            "espace_combinatoire_brut": espace_combinatoire_brut,
            "temps_ms": dt_ms,
        }


# ==============================================================================
# BANC DE TORTURE SRE V10.0 : ÉPREUVES IOTA, KAPPA, LAMBDA (R) & MU (BYZANTIN S)
# ==============================================================================
if __name__ == "__main__":
    moteur = DarwinEngine()
    etapes_loi = [
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.cloture_miroir_horizontal,
        InvariancePrimitives.cloture_miroir_vertical,
        InvariancePrimitives.gravite_bas,
    ]
    etapes_lambda = [
        InvariancePrimitives.automate_frontiere_interne,
        InvariancePrimitives.cloture_miroir_vertical,
        InvariancePrimitives.cloture_miroir_horizontal,
        InvariancePrimitives.automate_avalanche_sable,
    ]

    def appliquer_loi_secrete(grille: List[List[int]], pal: Dict[int, int], etapes=None) -> List[List[int]]:
        ops = etapes if etapes is not None else etapes_loi
        curr = [row[:] for row in grille]
        if ops and ops[-1] == InvariancePrimitives.automate_avalanche_sable:
            for fn in ops[:-1]:
                curr = fn(curr)
            return InvariancePrimitives.appliquer_palette_causale(curr, pal, "Automate_Avalanche", curr)
        for fn in ops:
            curr = fn(curr)
        return InvariancePrimitives.appliquer_palette_causale(curr, pal, "Gravite_Bas")

    # 1. ÉPREUVE IOTA (Sandwich Fantôme [1,3,1]->[7,7] & Sandwich Condorcet 392->0)
    palette_train_iota = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 118: 7, 136: 6, 120: 8}
    palette_verite_iota = {0: 0, 1: 7, 2: 6, 3: 0, 4: 8, 118: 7, 136: 6, 120: 8, 392: 0, 391: 7}
    train_iota1 = [
        [1, 1, 1, 1, 2, 2],
        [2, 2, 3, 3, 4, 4],
        [0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    train_iota2 = [
        [4, 4, 0, 0, 1, 1],
        [4, 4, 2, 2, 0, 0],
        [0, 0, 3, 3, 0, 0],
        [0, 0, 2, 2, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
    ]
    test_iota = [
        [4, 4, 2, 2, 0, 0],
        [1, 1, 3, 3, 2, 2],
        [1, 1, 2, 2, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [4, 4, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    res_iota = moteur.resoudre_loi_cachee_multi_exemples(
        [(train_iota1, appliquer_loi_secrete(train_iota1, palette_train_iota)),
         (train_iota2, appliquer_loi_secrete(train_iota2, palette_train_iota))],
        test_input=test_iota, max_profondeur=4, beam_width=128
    )
    exact_iota = (res_iota.get("prediction_test") == appliquer_loi_secrete(test_iota, palette_verite_iota))
    print(f"ÉPREUVE IOTA (SANDWICH FANTÔME) SUCCÈS: {res_iota['succes']} | EXACT TEST OOD: {exact_iota} | ÉTATS: {res_iota['evaluations_reelles']} | TEMPS: {res_iota['temps_ms']} ms")

    # 2. ÉPREUVE KAPPA (Failles P & Q : Cross-Resolution Deadlock + Émergence 3-Corps Or 392->9 & OOD 4-Corps 4472->9)
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

    res_kappa = moteur.resoudre_loi_cachee_multi_exemples(
        [(train_kappa1, appliquer_loi_secrete(train_kappa1, palette_train_kappa)),
         (train_kappa2, appliquer_loi_secrete(train_kappa2, palette_train_kappa))],
        test_input=test_kappa, max_profondeur=4, beam_width=128
    )
    exact_kappa = (res_kappa.get("prediction_test") == appliquer_loi_secrete(test_kappa, palette_verite_kappa))
    print(f"ÉPREUVE KAPPA (DEADLOCK P + N-CORPS Q) SUCCÈS: {res_kappa['succes']} | EXACT TEST OOD 4-CORPS (4472->9): {exact_kappa} | ÉTATS: {res_kappa['evaluations_reelles']} | TEMPS: {res_kappa['temps_ms']} ms")

    # 3. ÉPREUVE LAMBDA (Faille R « La Limite de Gödel » : Automate de Sable Asynchrone & Transport Inter-Colonnes)
    cible_l1 = appliquer_loi_secrete(train_kappa1, palette_train_kappa, etapes_lambda)
    cible_l2 = appliquer_loi_secrete(train_kappa2, palette_train_kappa, etapes_lambda)
    cible_test_l = appliquer_loi_secrete(test_kappa, palette_verite_kappa, etapes_lambda)

    pre_l1, pre_l2 = train_kappa1, train_kappa2
    for fn in etapes_lambda[:-1]:
        pre_l1 = fn(pre_l1)
        pre_l2 = fn(pre_l2)
    av_naif_l1 = InvariancePrimitives.automate_avalanche_sable(pre_l1)
    av_naif_l2 = InvariancePrimitives.automate_avalanche_sable(pre_l2)
    echec_fibre_1d = InvariancePrimitives.inferer_bijection_faisceau_global(
        [av_naif_l1, av_naif_l2], [cible_l1, cible_l2], True, "Gravite_Bas"
    )

    res_lambda = moteur.resoudre_loi_cachee_multi_exemples(
        [(train_kappa1, cible_l1), (train_kappa2, cible_l2)],
        test_input=test_kappa, max_profondeur=4, beam_width=128
    )
    exact_lambda = (res_lambda.get("prediction_test") == cible_test_l)
    print(f"PREUVE BRISURE DE FIBRE 1D (FAILLE R) : Solveur_1D_Fibre_Seul={echec_fibre_1d}")
    print(f"ÉPREUVE LAMBDA (LIMITE DE GÖDEL R — AVALANCHE ASYNCHRONE) SUCCÈS: {res_lambda['succes']} | EXACT TEST OOD: {exact_lambda} | ÉTATS: {res_lambda['evaluations_reelles']} | TEMPS: {res_lambda['temps_ms']} ms")

    # 4. ÉPREUVE MU (Faille S : Sabotage Adversarial Byzantin de l'Équation Diophantienne & Décodage de Syndrome L0)
    cible_mu1 = [row[:] for row in cible_l1]
    cible_mu1[0][2] = 8  # Sabotage 1 : fausse matière dans le vide (casse Delta_M_1 de -1 !)
    cible_mu1[4][0] = 6  # Sabotage 2 : corruption d'un grain d'Or 3-corps 9 -> 6 !
    cible_mu2 = [row[:] for row in cible_l2]
    cible_mu2[5][0] = 0  # Sabotage 3 : trou impossible au fond de l'avalanche (casse Delta_M_2 de +1 !)
    cible_mu2[5][1] = 8  # Sabotage 4 : falsification chromatique 6 -> 8 !

    # Preuve que le solveur diophantien exact (tau=0) est mis en échec par le sabotage :
    echec_diophantien_exact = InvariancePrimitives.inferer_bijection_faisceau_global(
        [av_naif_l1, av_naif_l2], [cible_mu1, cible_mu2], True, "Automate_Avalanche",
        grilles_pre_transport=[pre_l1, pre_l2], tolerance_adversariale=0
    )

    res_mu = moteur.resoudre_loi_cachee_multi_exemples(
        [(train_kappa1, cible_mu1), (train_kappa2, cible_mu2)],
        test_input=test_kappa, max_profondeur=4, beam_width=128
    )
    exact_mu = (res_mu.get("prediction_test") == cible_test_l)
    print(f"PREUVE SABOTAGE DIOPHANTIEN (FAILLE S) : Solveur_Exact_Tau0={echec_diophantien_exact}")
    print(f"ÉPREUVE MU (SABOTAGE BYZANTIN S — 4 PIXELS MENTEURS) SUCCÈS: {res_mu['succes']} | EXACT TEST OOD: {exact_mu} | ÉTATS: {res_mu['evaluations_reelles']} | TEMPS: {res_mu['temps_ms']} ms")
    print(f"SYNDROME HORUS (PIXELS MENTEURS DÉMASQUÉS [r, c, faux, vrai]) : {res_mu.get('syndrome_adversarial')}")
    print(f"FORMULE MU: {res_mu.get('formule_mathematique')}")
