# -*- coding: utf-8 -*-
"""
===============================================================================
       🧬 LES PRIMITIVES GÉOMÉTRIQUES & D'INVARIANCE DÉTERMINISTE (K-SIL)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Primitives d'invariance géométrique en O(1) sur grilles discrètes (ARC-AGI).
    - Opérations diédrales D4, projections, bijections de palettes, symétries.
    - Zéro calcul matriciel lourd, exécution en microsecondes.
===============================================================================
"""

from typing import List, Dict, Any, Optional, Tuple

class InvariancePrimitives:
    """Banque de primitives géométriques d'invariance discrète."""

    @staticmethod
    def symetrie_horizontale(grille: List[List[int]]) -> List[List[int]]:
        """Miroir horizontal (axe vertical central)."""
        return [row[::-1] for row in grille]

    @staticmethod
    def symetrie_verticale(grille: List[List[int]]) -> List[List[int]]:
        """Miroir vertical (axe horizontal central)."""
        return grille[::-1]

    @staticmethod
    def rotation_90(grille: List[List[int]]) -> List[List[int]]:
        """Rotation quart de tour 90° sens horaire."""
        if not grille or not grille[0]:
            return []
        h = len(grille)
        w = len(grille[0])
        return [[grille[h - 1 - r][c] for r in range(h)] for c in range(w)]

    @staticmethod
    def rotation_180(grille: List[List[int]]) -> List[List[int]]:
        """Rotation demi-tour 180°."""
        return [row[::-1] for row in grille[::-1]]

    @staticmethod
    def decomposer_etat_algebrique(val: int) -> List[int]:
        """Décompose un état (atomique < 100 ou composite >= 100) en liste triée de couleurs atomiques."""
        if val <= 0:
            return []
        if val < 100:
            return [val]
        s = set()
        rem = val - 100
        while rem > 0:
            s.add(rem % 16)
            rem //= 16
        return sorted(s)

    @staticmethod
    def encoder_etat_algebrique(couleurs: List[int]) -> int:
        """Encode un ensemble de couleurs atomiques en son identifiant canonique dans l'algèbre libre."""
        uniques = sorted(set(c for c in couleurs if c > 0))
        if not uniques:
            return 0
        if len(uniques) == 1:
            return uniques[0]
        code = 0
        for c in uniques:
            code = code * 16 + c
        return 100 + code

    @staticmethod
    def resoudre_projection_ood(val: int, bijection: Dict[int, int]) -> int:
        """
        CLÔTURE DE TREILLIS & NOYAU DE CONDORCET OOD V5 (Correction Failles F & G) :
        1. Purge du Noyau ker(phi) : toute composante c telle que phi(c) == 0 est neutre et éliminée.
        2. Réduction Synchrone de Schwartz / Condorcet (Invariant d'Ordre — Correction Faille G) :
           Au lieu d'éliminer séquentiellement selon l'ordre des entiers i < j, construit le graphe
           orienté complet des dominances (a -> b ssi phi({a,b}) == phi(a) != phi(b)) et élimine
           SIMULTANÉMENT tous les éléments dominés qui n'ont pas de chemin de revanche vers leur vainqueur.
        3. Frustration Cyclique (Paradoxe Pierre-Papier-Ciseaux : 1 > 2 > 4 > 1) :
           Si le sous-ensemble irréductible forme un cycle intransitif symétrique (chaque élément est
           battu par un autre élément du cycle), il y a neutralisation mutuelle par frustration -> 0.
        """
        if val in bijection:
            return bijection[val]
        if val < 100:
            return bijection.get(val, val)

        # 1. Décomposition atomique & purge des couleurs annihilées (ker(phi))
        composantes = [
            c for c in InvariancePrimitives.decomposer_etat_algebrique(val)
            if bijection.get(c, c) != 0
        ]
        if not composantes:
            return 0
        if len(composantes) == 1:
            c0 = composantes[0]
            return bijection.get(c0, c0)

        # 2. Réduction synchrone invariante par permutation des identifiants (Ensemble de Schwartz)
        while len(composantes) > 1:
            code_actuel = InvariancePrimitives.encoder_etat_algebrique(composantes)
            if code_actuel in bijection:
                return bijection[code_actuel]

            # Construction du graphe orienté de dominance : dom[a] = {b | a bat b}
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

            # Fermeture transitive des chemins de dominance (accessibilité dans le graphe)
            atteignables: Dict[int, set] = {c: set(dom[c]) for c in composantes}
            for k in composantes:
                for i_c in composantes:
                    if k in atteignables[i_c]:
                        atteignables[i_c] |= atteignables[k]

            # Un élément x est strictement dominé (hors de l'ensemble de Schwartz) s'il existe y
            # tel que y atteint x mais x n'atteint pas y
            survivants = [
                x for x in composantes
                if not any((x in atteignables[y]) and (y not in atteignables[x]) for y in composantes if y != x)
            ]

            if len(survivants) < len(composantes):
                composantes = survivants
                continue

            # Aucun élément n'est asymétriquement dominé :
            # Soit il y a un cycle intransitif de Condorcet (ex: 1 > 2 > 4 > 1 où chacun est battu),
            # soit des réactions alchimiques non-dominantes.
            tous_battus_dans_cycle = all(
                any(x in dom[y] for y in composantes if y != x)
                for x in composantes
            )
            if tous_battus_dans_cycle:
                # Paradoxe de Condorcet symétrique (Pierre-Papier-Ciseaux) : annihilation mutuelle -> 0
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

        # 3. Réaction alchimique binaire unique parmi les survivants non-dominés
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
    def appliquer_palette(grille: List[List[int]], bijection: Dict[int, int]) -> List[List[int]]:
        """Applique l'épimorphisme de palette avec résolution analytique OOD des collisions."""
        resoudre = InvariancePrimitives.resoudre_projection_ood
        return [[resoudre(val, bijection) for val in row] for row in grille]

    @staticmethod
    def superposition_booleenne(grille_a: List[List[int]], grille_b: List[List[int]]) -> List[List[int]]:
        """Superpose B sur A en écrasant uniquement les pixels non nuls de B."""
        if not grille_a or not grille_b:
            return grille_a or grille_b
        h = min(len(grille_a), len(grille_b))
        w = min(len(grille_a[0]), len(grille_b[0]))
        res = []
        for r in range(h):
            row = []
            for c in range(w):
                v_b = grille_b[r][c]
                row.append(v_b if v_b != 0 else grille_a[r][c])
            res.append(row)
        return res

    @staticmethod
    def rotation_270(grille: List[List[int]]) -> List[List[int]]:
        """Rotation 270° sens horaire (90° anti-horaire)."""
        if not grille or not grille[0]:
            return []
        h = len(grille)
        w = len(grille[0])
        return [[grille[r][w - 1 - c] for r in range(h)] for c in range(w)]

    @staticmethod
    def transposition_diagonale(grille: List[List[int]]) -> List[List[int]]:
        """Symétrie selon la diagonale principale (M^T)."""
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        return [[grille[r][c] for r in range(h)] for c in range(w)]

    @staticmethod
    def gravite_bas(grille: List[List[int]]) -> List[List[int]]:
        """Opérateur physique non-linéaire : chute gravitationnelle des cellules non-nulles vers le bas."""
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
        """Opérateur physique non-linéaire : glissement gravitationnel vers la droite."""
        if not grille or not grille[0]:
            return []
        h, w = len(grille), len(grille[0])
        res = []
        for r in range(h):
            vals = [v for v in grille[r] if v != 0]
            res.append([0] * (w - len(vals)) + vals)
        return res

    @staticmethod
    def _fusionner_cellules_algebrique(a: int, b: int) -> int:
        """
        ALGÈBRE LIBRE DE COLLISION (Zéro Biais Ordinal) :
        Émet un état composite commutatif canonique dans l'algèbre des parties.
        """
        if a == 0:
            return b
        if b == 0:
            return a
        if a == b:
            return a
        union_couleurs = sorted(
            set(InvariancePrimitives.decomposer_etat_algebrique(a))
            | set(InvariancePrimitives.decomposer_etat_algebrique(b))
        )
        return InvariancePrimitives.encoder_etat_algebrique(union_couleurs)

    @staticmethod
    def superposition_commutative(grille_a: List[List[int]], grille_b: List[List[int]]) -> List[List[int]]:
        """
        Superposition commutative dans l'algèbre libre des couleurs :
        Préserve l'isomorphisme D4 strict ET élimine l'artefact ordinal de max(A, B).
        """
        if not grille_a or not grille_b:
            return grille_a or grille_b
        h = min(len(grille_a), len(grille_b))
        w = min(len(grille_a[0]), len(grille_b[0]))
        fusion = InvariancePrimitives._fusionner_cellules_algebrique
        return [
            [fusion(grille_a[r][c], grille_b[r][c]) for c in range(w)]
            for r in range(h)
        ]

    @staticmethod
    def cloture_miroir_horizontal(grille: List[List[int]]) -> List[List[int]]:
        """Miroir gauche-droite (axe vertical) avec algèbre libre de collision."""
        miroir = InvariancePrimitives.symetrie_horizontale(grille)
        return InvariancePrimitives.superposition_commutative(grille, miroir)

    @staticmethod
    def cloture_miroir_vertical(grille: List[List[int]]) -> List[List[int]]:
        """Miroir haut-bas (axe horizontal) avec algèbre libre de collision."""
        miroir = InvariancePrimitives.symetrie_verticale(grille)
        return InvariancePrimitives.superposition_commutative(grille, miroir)

    @staticmethod
    def automate_frontiere_interne(grille: List[List[int]]) -> List[List[int]]:
        """
        Opérateur topologique non-linéaire : érosion cellulaire (ne conserve un pixel
        que s'il possède au moins un voisin orthogonal non-nul, éliminant les poussières isolées).
        """
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
    def appliquer_palette_causale(
        grille: List[List[int]],
        bijection: Dict[int, int],
        derniere_primitive: Optional[str] = None,
        grille_pre_transport: Optional[List[List[int]]] = None
    ) -> List[List[int]]:
        """
        PROJECTION CAUSALE AVEC ÉQUIVARIANCE CINÉMATIQUE LAGRANGIENNE (V9.0 — Corrections Failles J & R) :
        - Pour Gravite_Bas / Gravite_Droite (1D ordonné) : G(phi(G(X))) == G(phi(X)).
        - Pour Automate_Avalanche (2D asynchrone non-commutatif, Faille R) :
          En vertu du Théorème d'Équivariance Cinématique G_Av(phi(X)) == phi(G_Av(Purge_ker(X))),
          la projection est appliquée sur l'état pré-transport X avant la relaxation d'avalanche,
          afin qu'aucun grain ne dévie sur une masse fantôme vouée au vide.
        """
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
        """
        BOUCLIER AXIOMATIQUE V9.0 (Anti-Blackhole, Anti-Pot-de-Peinture & Émergence N-Corps) :
        1. Axiome du Vide : mapping[0] == 0.
        2. Borne de Noyau Atomique (Faille E) : dim(ker_atomes(phi)) <= 1 sur les atomes purs (0 < k < 100).
        3. Injectivité Atomique Stricte (Faille I) : deux atomes survivants distincts (0 < k1 != k2 < 100)
           ne peuvent JAMAIS mapper vers la même couleur active.
        4. Physique des Collisions N-Corps (Correction Faille Q) :
           - Une collision k >= 100 (binaire Matière-Antimatière ou ternaire de Condorcet) peut s'annihiler (v == 0).
           - Si v > 0, la couleur produite est soit héritée d'un atome parent de la collision (dominance),
             soit une couleur émergente d'alchimie N-corps (n'usurpant aucun atome étranger hors collision).
        """
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
        """
        DÉTECTEUR DE SYNDROME DE HAMMING (HORUS BYZANTIN V10.0 — Correction Faille S) :
        Localise chirurgicalement chaque pixel menteur injecté par un adversaire dans les cibles d'entraînement.
        Retourne pour chaque grille la liste des quadruplets (r, c, valeur_sabotee, vraie_valeur_causale).
        """
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
        """
        UNIFICATION TENSORIELLE, ÉQUIVARIANCE LAGRANGIENNE & CONSENSUS BYZANTIN (V10.0 — Failles P, Q, R, S) :
        1. Passe 1 : Alignement spatial direct global.
        2. Passe 2 : Faisceau Global de Fibres sous Gravité 1D (Failles J, M, N, O, P, Q).
        3. Passe 3 (Correction Faille R) : Solveur Lagrangien Diophantien exact pour Automate_Avalanche.
        4. Passe 3B (Correction Faille S — Tolérance Byzantine & Décodage de Syndrome L0) :
           Lorsque `tolerance_adversariale > 0` (pixels menteurs sabotant l'équation diophantienne et les cibles),
           ouvre une Fenêtre Diophantienne de Hamming |m_ker - Delta_M_i| <= tau, exécute un Vote Majoritaire
           de Reed-Solomon sur le faisceau global et valide la loi si le syndrome d_H(Y_pur, Y_adv) <= tau.
        """
        if not grilles_sources or not grilles_cibles or len(grilles_sources) != len(grilles_cibles):
            return None

        # Vérification des dimensions et Loi de Conservation d'Énergie par grille (Faille L + marge Byzantine tau)
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

            # 3A. Mode Diophantien Exact (0 erreur, ultra-rapide)
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
                        # Fenêtre Diophantienne de Hamming O(1) : |m_ker - Delta_M_i| <= tau
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
                        grilles_simulees: List[List[List[int]]] = []

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
                            grilles_simulees.append(g_sim)

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

                        # Vote Majoritaire Byzantin par classe chromatique
                        vote_valide = True
                        for sv, urne in votes.items():
                            tv_maj, nb_voix = max(urne.items(), key=lambda kv: kv[1])
                            if nb_voix < 2:
                                vote_valide = False
                                break
                            map_byz[sv] = tv_maj

                        if not vote_valide or not InvariancePrimitives.valider_coherence_algebrique_palette(map_byz):
                            continue

                        # Mesure exacte du Syndrome de Hamming d_H(Y_pur, Y_adv) <= tau par grille
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

            # Correction Faille O : Pré-Filtre Géométrique O(K*W) sur tout le faisceau
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
                # Point-Fixe Synchrone sur le Faisceau Global de Fibres (Corrections P & Q)
                for iter_pf in range(6):
                    progres = False
                    for fs, ft in zip(fibres_s, fibres_t):
                        # 1. Purge primaire : uniquement l'atome nul et les états déjà prouvés == 0 dans map_test
                        p_s = [v for v in fs if v != atome_nul and map_test.get(v, -1) != 0]
                        p_t = list(ft)

                        # Correction Faille Q (Priorité à l'Émergence N-Corps) :
                        # On n'invoque la réduction OOD vers 0 QUE si la fibre présente un surplus
                        # physique strict de masse fantôme (len(p_s) > len(p_t)) et qu'on a déjà
                        # extrait les règles directes des fibres sans surplus (iter_pf >= 1).
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

                        # 2. Fibre sans surplus : extraction directe (y compris lois N-Corps 392 -> 9 !)
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

                        # 3. Épluchage Bilatéral de Sandwich sur fibre avec surplus (len(p_s) > len(p_t))
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
        palette_initiale: Optional[Dict[int, int]] = None
    ) -> Optional[Dict[int, int]]:
        """Wrapper unitaire O(1) déléguant au solveur de Faisceau Global de Fibres V8.0."""
        return InvariancePrimitives.inferer_bijection_faisceau_global(
            [grille_source],
            [grille_cible],
            autoriser_projection_zero=autoriser_projection_zero,
            derniere_primitive=derniere_primitive,
            noyau_attendu=noyau_attendu,
            palette_initiale=palette_initiale,
        )

    @staticmethod
    def masque_binaire_structurel(grille: List[List[int]]) -> List[List[int]]:
        """Projette la grille sur son invariant topologique pur {0, 1} indépendant de la palette."""
        return [[1 if v != 0 else 0 for v in row] for row in grille]

    @staticmethod
    def extraire_bbox_non_nulle(grille: List[List[int]]) -> Tuple[int, int, int, int]:
        """Retourne (r_min, r_max, c_min, c_max) du contenu non-nul."""
        h = len(grille)
        w = len(grille[0]) if h > 0 else 0
        r_min, r_max, c_min, c_max = h, -1, w, -1
        for r in range(h):
            for c in range(w):
                if grille[r][c] != 0:
                    if r < r_min: r_min = r
                    if r > r_max: r_max = r
                    if c < c_min: c_min = c
                    if c > c_max: c_max = c
        if r_max == -1:
            return (0, 0, 0, 0)
        return (r_min, r_max, c_min, c_max)
