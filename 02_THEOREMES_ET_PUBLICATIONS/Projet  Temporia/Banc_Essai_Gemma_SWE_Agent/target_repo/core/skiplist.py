# -*- coding: utf-8 -*-
"""
================================================================================
       🏛️ K-SIL SOUVERAIN : CONCURRENT SKIPLIST MAP (PALIER 9)
       Structure de Données Ordonnée Haute Concurrence (Locking Fin)
       Christian Duguay & Alix · Atelier Démiurgique KAIROS
================================================================================
Forme Normale en 4 Pôles :
• PÔLE 1 : ÉTAT, TOUR DE POINTEURS & SENTINELLE
    - SkipListNode[K, V] : key, value, forward[], marked, fully_linked, lock par nœud.
    - SkipListMap[K, V] : sentinelle head (-inf), max_level=16, p=0.5, size atomique.
• PÔLE 2 : MICRO-MUTATIONS ATOMIQUES & VERROUILLAGE FIN
    - _random_level() : distribution géométrique stricte p=0.5 bornée à max_level.
    - _find_preds_succs() : traversée descendante lock-free O(log n).
    - Verrouillage fin des prédécesseurs sans interblocage (ordre strict des clés).
    - Suppression en deux temps : marquage logique atomique + déconnexion physique.
• PÔLE 3 : PRÉDICATS D'INVARIANCE & VALIDATE()
    - validate() : vérification formelle de la stricte monotonie, cohérence multi-niveaux.
    - contains(), is_empty(), size().
• PÔLE 4 : TRANSITIONS THREAD-SAFE & NAVIGATION ORDONNÉE
    - get(), put(), remove(), first_key(), last_key(), range(start, end).
================================================================================
"""

import random
import threading
from typing import Optional, Iterator, Tuple, List, Any


class SkipListNode:
    """Nœud d'une Skip List concurrente avec tour de pointeurs et verrou fin."""

    def __init__(self, key: Any = None, value: Any = None, level: int = 1):
        self.key = key
        self.value = value
        self.level = level
        self.forward: List[Optional['SkipListNode']] = [None] * level
        self.marked: bool = False          # Marquage logique pour suppression concurrente
        self.fully_linked: bool = False    # Vrai quand le nœud est raccordé à tous ses niveaux
        self.lock = threading.Lock()       # Verrouillage fin strict par nœud (zéro verrou global)

    def __repr__(self) -> str:
        return f"SkipListNode(key={self.key}, val={self.value}, lvl={self.level}, marked={self.marked})"


class SkipListMap:
    """
    Map concurrente ordonnée basée sur une Skip List à verrouillage fin (Fine-Grained Locking).
    Toutes les opérations d'écriture utilisent un verrouillage local par nœud.
    Les lectures de traversée sont lock-free.
    """

    def __init__(self, max_level: int = 16, p: float = 0.5):
        self.max_level = max_level
        self.p = p
        # Sentinelle head (clé None représentant -l'infini, niveau maximal)
        self.head = SkipListNode(key=None, value=None, level=max_level)
        self.head.fully_linked = True
        self._size = 0
        self._size_lock = threading.Lock()

    # =========================================================================
    # PÔLE 1 & 2 : MICRO-MUTATIONS & GÉNÉRATION PROBABILISTE
    # =========================================================================

    def _random_level(self) -> int:
        """Génération probabiliste du niveau selon une loi géométrique bornée."""
        lvl = 1
        while random.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl

    def _find_preds_succs(self, key: Any) -> Tuple[List[SkipListNode], List[Optional[SkipListNode]]]:
        """
        Traversée descendante lock-free O(log n).
        Retourne la liste des prédécesseurs et successeurs pour chaque niveau.
        """
        preds = [self.head] * self.max_level
        succs: List[Optional[SkipListNode]] = [None] * self.max_level
        curr = self.head

        for lvl in range(self.max_level - 1, -1, -1):
            nxt = curr.forward[lvl]
            while nxt is not None and (nxt.key is not None and nxt.key < key):
                curr = nxt
                nxt = curr.forward[lvl]
            preds[lvl] = curr
            succs[lvl] = nxt

        return preds, succs

    def _lock_nodes(self, nodes: List[SkipListNode]):
        """Verrouille une liste de nœuds dans un ordre strict (clé ou id) pour éviter tout deadlock."""
        unique_nodes = sorted(list(set(nodes)), key=lambda n: (n.key is not None, n.key if n.key is not None else 0, id(n)))
        for n in unique_nodes:
            n.lock.acquire()
        return unique_nodes

    def _unlock_nodes(self, locked_nodes: List[SkipListNode]):
        """Déverrouille les nœuds préalablement acquis."""
        for n in locked_nodes:
            n.lock.release()

    # =========================================================================
    # PÔLE 3 : PRÉDICATS D'INVARIANCE & VALIDATE()
    # =========================================================================

    def size(self) -> int:
        """Retourne le nombre exact d'éléments dans la Skip List."""
        with self._size_lock:
            return self._size

    def is_empty(self) -> bool:
        """Prédicat d'état : vrai si la map est vide."""
        return self.size() == 0

    def contains(self, key: Any) -> bool:
        """Vérifie la présence d'une clé sans verrou global."""
        return self.get(key) is not None

    def validate(self) -> bool:
        """
        Vérifie formellement les invariants structurels de la Skip List :
        1. Monotonie strictement croissante des clés à tous les niveaux.
        2. Propriété de sous-ensemble : tout élément au niveau L est présent au niveau L-1.
        3. Intégrité des pointeurs de sentinelle et absence de cycles.
        """
        with self._size_lock:
            prev_level_keys = None

            for lvl in range(self.max_level - 1, -1, -1):
                curr = self.head.forward[lvl]
                current_level_keys = []
                last_key = None
                visited = set()

                while curr is not None:
                    if id(curr) in visited:
                        raise AssertionError(f"Cycle détecté au niveau {lvl} sur le nœud {curr.key}")
                    visited.add(id(curr))

                    if not curr.marked:
                        if last_key is not None and curr.key <= last_key:
                            raise AssertionError(
                                f"Rupture de tri au niveau {lvl} : {curr.key} <= {last_key}"
                            )
                        last_key = curr.key
                        current_level_keys.append(curr.key)

                    curr = curr.forward[lvl]

                if prev_level_keys is not None:
                    set_lower = set(current_level_keys)
                    for k in prev_level_keys:
                        if k not in set_lower:
                            raise AssertionError(
                                f"Invariant multi-niveaux rompu : clé {k} présente au niveau supérieur mais absente au niveau {lvl}"
                            )

                prev_level_keys = current_level_keys

            return True

    # =========================================================================
    # PÔLE 4 : TRANSITIONS THREAD-SAFE & NAVIGATION ORDONNÉE
    # =========================================================================

    def get(self, key: Any) -> Optional[Any]:
        """Lecture optimiste lock-free O(log n)."""
        curr = self.head
        for lvl in range(self.max_level - 1, -1, -1):
            nxt = curr.forward[lvl]
            while nxt is not None and (nxt.key is not None and nxt.key < key):
                curr = nxt
                nxt = curr.forward[lvl]

        cand = curr.forward[0]
        if cand is not None and cand.key == key and not cand.marked and cand.fully_linked:
            return cand.value
        return None

    def put(self, key: Any, value: Any) -> Optional[Any]:
        """
        Insertion concurrente thread-safe avec verrouillage fin.
        Retourne l'ancienne valeur si la clé existait déjà, sinon None.
        """
        top_level = self._random_level()

        while True:
            preds, succs = self._find_preds_succs(key)
            target = succs[0]

            # Cas 1 : La clé existe déjà au niveau 0
            if target is not None and target.key == key:
                target.lock.acquire()
                try:
                    if not target.marked:
                        old_val = target.value
                        target.value = value
                        return old_val
                finally:
                    target.lock.release()
                continue

            # Cas 2 : Nouvelle insertion avec raccordement des niveaux
            nodes_to_lock = preds[:top_level]
            locked = self._lock_nodes(nodes_to_lock)

            try:
                valid = True
                for lvl in range(top_level):
                    p_node = preds[lvl]
                    s_node = succs[lvl]
                    if p_node.marked or (s_node is not None and s_node.marked):
                        valid = False
                        break
                    if p_node.forward[lvl] != s_node:
                        valid = False
                        break

                if not valid:
                    continue

                new_node = SkipListNode(key=key, value=value, level=top_level)
                for lvl in range(top_level):
                    new_node.forward[lvl] = succs[lvl]
                    preds[lvl].forward[lvl] = new_node

                new_node.fully_linked = True
                with self._size_lock:
                    self._size += 1
                return None

            finally:
                self._unlock_nodes(locked)

    def remove(self, key: Any) -> Optional[Any]:
        """
        Suppression concurrente robuste en deux phases (Optimistic SkipList) :
        1. Phase logique : Détection et marquage atomique sous target.lock.
        2. Phase physique : Boucle de déconnexion physique avec verrouillage fin des prédécesseurs.
           Si la validation échoue (mutation concurrente d'un prédécesseur), on RETENTE jusqu'à
           déconnexion physique effective. Le compteur _size n'est décrémenté qu'une fois la déconnexion actée.
        """
        is_logically_marked = False
        top_level = 0
        target_node = None
        old_val = None

        while True:
            preds, succs = self._find_preds_succs(key)
            target = succs[0]

            if not is_logically_marked:
                # Étape 1 : Localisation et marquage logique
                if target is None or target.key != key:
                    return None

                target.lock.acquire()
                try:
                    if target.marked:
                        return None  # Déjà supprimé par un autre thread concurrent
                    target.marked = True
                    is_logically_marked = True
                    target_node = target
                    old_val = target.value
                    top_level = target.level
                finally:
                    target.lock.release()

            # Étape 2 : Déconnexion physique garantie
            # target_node est marqué. On doit impérativement délier physiquement
            # ses pointeurs à tous ses niveaux avant de quitter.
            nodes_to_lock = preds[:top_level]
            locked = self._lock_nodes(nodes_to_lock)
            try:
                valid = True
                for lvl in range(top_level):
                    p_node = preds[lvl]
                    if p_node.marked or p_node.forward[lvl] != target_node:
                        valid = False
                        break

                if valid:
                    # Déconnexion physique atomique réussie
                    for lvl in range(top_level):
                        preds[lvl].forward[lvl] = target_node.forward[lvl]
                    with self._size_lock:
                        self._size -= 1
                    return old_val

                # Si valid == False, un prédécesseur a muté entre-temps.
                # On boucle pour retrouver les nouveaux prédécesseurs et retenter le délien !
            finally:
                self._unlock_nodes(locked)

    def first_key(self) -> Optional[Any]:
        """Retourne la plus petite clé présente dans la map (O(1))."""
        curr = self.head.forward[0]
        while curr is not None:
            if not curr.marked and curr.fully_linked:
                return curr.key
            curr = curr.forward[0]
        return None

    def last_key(self) -> Optional[Any]:
        """
        Retourne la plus grande clé présente dans la map en O(log n).
        Descente optimisée depuis le niveau maximal sans balayage linéaire complet.
        """
        curr = self.head
        for lvl in range(self.max_level - 1, -1, -1):
            nxt = curr.forward[lvl]
            while nxt is not None:
                if nxt.marked or not nxt.fully_linked:
                    # Ne pas sauter par-dessus un nœud marqué ou non prêt : descendre de niveau
                    break
                curr = nxt
                nxt = curr.forward[lvl]

        # Au niveau 0, avancer au maximum sur les nœuds valides
        while curr.forward[0] is not None:
            nxt = curr.forward[0]
            if nxt.marked or not nxt.fully_linked:
                break
            curr = nxt

        if curr != self.head and not curr.marked and curr.fully_linked:
            return curr.key

        # Cas de bord rare (si suppression concurrente massive en fin de liste)
        cand = None
        n = self.head.forward[0]
        while n is not None:
            if not n.marked and n.fully_linked:
                cand = n.key
            n = n.forward[0]
        return cand

    def range(self, start: Optional[Any] = None, end: Optional[Any] = None) -> Iterator[Tuple[Any, Any]]:
        """
        Retourne un itérateur ordonné sur l'intervalle [start, end] inclus.
        """
        curr = self.head
        if start is not None:
            for lvl in range(self.max_level - 1, -1, -1):
                nxt = curr.forward[lvl]
                while nxt is not None and (nxt.key is not None and nxt.key < start):
                    curr = nxt
                    nxt = curr.forward[lvl]
            curr = curr.forward[0]
        else:
            curr = self.head.forward[0]

        while curr is not None:
            if end is not None and curr.key is not None and curr.key > end:
                break
            if not curr.marked and curr.fully_linked:
                yield (curr.key, curr.value)
            curr = curr.forward[0]
