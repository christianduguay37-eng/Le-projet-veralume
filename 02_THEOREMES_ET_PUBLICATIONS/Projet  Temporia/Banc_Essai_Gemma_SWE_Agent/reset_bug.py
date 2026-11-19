# -*- coding: utf-8 -*-
"""
Script de réinitialisation des bogues dans `target_repo`.
Supporte les deux paliers de difficulté :
- Palier 1 : DAG Kahn & Tri Topologique (Mono-fichier : core/graph.py)
- Palier 2 : Invalidation Cache & Mutation Réseau Multi-Modules (Multi-fichiers : core/mutation.py)
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_DIR = Path(__file__).parent / "target_repo"

# ==============================================================================
# BOGUE PALIER 1 : Kahn Topological Sort Tronqué
# ==============================================================================
BUGGY_GRAPH_TOPOLOGICAL = '''        in_degree: Dict[str, int] = {}
        for u in self.adj:
            in_degree[u] = 0

        for u in self.adj:
            for v in self.adj[u]:
                if v in in_degree:
                    in_degree[v] += 1

        queue: List[str] = [u for u, deg in in_degree.items() if deg == 0]
        sorted_order: List[str] = []

        while queue:
            curr = queue.pop(0)
            sorted_order.append(curr)
            for neighbor in self.adj.get(curr, {}):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return sorted_order'''

CLEAN_GRAPH_TOPOLOGICAL = '''        in_degree: Dict[str, int] = {node: 0 for node in self.nodes}

        for u in self.nodes:
            for v in self.adj.get(u, {}):
                if v in in_degree:
                    in_degree[v] += 1

        queue: List[str] = [u for u, deg in in_degree.items() if deg == 0]
        sorted_order: List[str] = []

        while queue:
            curr = queue.pop(0)
            sorted_order.append(curr)
            for neighbor in self.adj.get(curr, {}):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(sorted_order) != len(self.nodes):
            raise CycleDetectedException(
                f"Cycle détecté dans le graphe : seuls {len(sorted_order)}/{len(self.nodes)} nœuds résolus."
            )

        return sorted_order'''

# ==============================================================================
# BOGUE PALIER 2 : Omission d'Invalidation Cache dans core/mutation.py
# ==============================================================================
BUGGY_MUTATION_CODE = '''# -*- coding: utf-8 -*-
"""
Module de mutation dynamique de topologie réseau.
Gère l'ajout, le retrait et la modification d'éléments du graphe.
"""

from typing import Optional
from core.graph import DirectedGraph


class GraphMutator:
    """
    Opérateur de mutation sur le graphe de réseau.
    Permet de modifier dynamiquement les liens et les nœuds en cours d'exécution.
    """

    def __init__(self, graph: DirectedGraph):
        self.graph = graph

    def remove_node(self, node: str) -> bool:
        """
        Supprime un nœud du réseau ainsi que toutes ses arêtes incidentes et sortantes.
        """
        if node not in self.graph.nodes:
            return False

        # 1. Suppression du nœud dans l'ensemble des nœuds
        self.graph.nodes.remove(node)

        # 2. Suppression des arêtes sortantes
        if node in self.graph.adj:
            del self.graph.adj[node]

        # 3. Suppression des arêtes incidentes (vers ce nœud)
        for u in list(self.graph.adj.keys()):
            if node in self.graph.adj[u]:
                del self.graph.adj[u][node]

        return True

    def update_edge_weight(self, u: str, v: str, new_weight: float) -> bool:
        """
        Met à jour la pondération / latence d'une liaison réseau.
        """
        if u not in self.graph.adj or v not in self.graph.adj[u]:
            return False

        self.graph.adj[u][v] = float(new_weight)
        return True
'''


BUGGY_FLOW_CODE = '''        path, _ = self.graph.get_shortest_path(source, sink)
        
        # Bogue : n'alloue que sur le premier tronçon
        first_hop = path[1]
        self.allocate_edge_flow(source, first_hop, demand)
        
        self.verify_conservation(source, sink)
        return demand'''

CLEAN_FLOW_CODE = '''        path, _ = self.graph.get_shortest_path(source, sink)
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            self.allocate_edge_flow(u, v, demand)
        
        self.verify_conservation(source, sink)
        return demand'''


STUB_LIMITER_CODE = '''# -*- coding: utf-8 -*-
"""
Module de limitation de débit (Rate Limiter) par algorithme Token Bucket.
À construire de zéro par le K-SIL SWE Agent.
"""

import time


class TokenBucketRateLimiter:
    """
    Limiteur de débit par seau de jetons (Token Bucket).
    Doit être implémenté selon le contrat des tests unitaires :
    - __init__(capacity: float, refill_rate: float)
    - refill() -> None
    - consume(tokens: float = 1.0) -> bool
    - get_available_tokens() -> float
    """

    def __init__(self, capacity: float, refill_rate: float):
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def consume(self, tokens: float = 1.0) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def get_available_tokens(self) -> float:
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_1():
    graph_file = REPO_DIR / "core" / "graph.py"
    content = graph_file.read_text(encoding="utf-8")
    if CLEAN_GRAPH_TOPOLOGICAL in content:
        content = content.replace(CLEAN_GRAPH_TOPOLOGICAL, BUGGY_GRAPH_TOPOLOGICAL)
        graph_file.write_text(content, encoding="utf-8")
        print("🔄 [RESET] Palier 1 réinitialisé dans `core/graph.py` (Kahn Topo RED).")
    else:
        print("ℹ️ [RESET] Palier 1 déjà en état bogue ou motif propre non trouvé.")


def reset_palier_2():
    mutation_file = REPO_DIR / "core" / "mutation.py"
    mutation_file.write_text(BUGGY_MUTATION_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 2 réinitialisé dans `core/mutation.py` (Cache Invalidation RED).")


STUB_PARSER_CODE = '''# -*- coding: utf-8 -*-
"""
Module de parsing et évaluation d'expressions mathématiques complexes.
Palier 5 : Défi extrême d'analyse syntaxique récursive / Shunting-Yard.
"""


class ExpressionEvaluator:
    """
    Évaluateur d'expressions mathématiques avec précédence d'opérateurs,
    associativité droite pour l'exponentiation (^), parenthèses imbriquées
    et négation unaire.
    
    Attention : le symbole '^' représente la puissance mathématique (ex: 2^3 = 8),
    avec associativité à droite (ex: 2^3^2 = 2^(3^2) = 512).
    """

    def evaluate(self, expr: str) -> float:
        """
        Analyse et évalue l'expression sous forme de chaîne et retourne le résultat numérique.
        Lève ZeroDivisionError si division par zéro.
        Lève ValueError en cas d'erreur de syntaxe ou parenthèses non appariées.
        """
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_3():
    flow_file = REPO_DIR / "core" / "flow.py"
    content = flow_file.read_text(encoding="utf-8")
    if CLEAN_FLOW_CODE in content:
        content = content.replace(CLEAN_FLOW_CODE, BUGGY_FLOW_CODE)
        flow_file.write_text(content, encoding="utf-8")
    print("🔄 [RESET] Palier 3 réinitialisé dans `core/flow.py` (Flow Conservation RED).")


def reset_palier_4():
    limiter_file = REPO_DIR / "core" / "limiter.py"
    limiter_file.write_text(STUB_LIMITER_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 4 réinitialisé dans `core/limiter.py` (Stub NotImplementedError RED).")


STUB_RINGBUFFER_CODE = '''# -*- coding: utf-8 -*-
"""
Module de Buffer Circulaire Sans Verrou (Lock-Free Concurrent Ring Buffer).
Palier 6 : Défi extrême de concurrence multi-thread et d'invariance d'état mémoire.
"""

from typing import Any, Tuple, Optional


class LockFreeRingBuffer:
    """
    Buffer circulaire haute performance sans verrou (lock-free / mutex-free).
    Doit opérer de manière concurrente et thread-safe sans utiliser `threading.Lock`.
    """

    def __init__(self, capacity: int):
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def enqueue(self, item: Any) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def dequeue(self) -> Tuple[bool, Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def size(self) -> int:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def is_empty(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def is_full(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_5():
    parser_file = REPO_DIR / "core" / "parser.py"
    parser_file.write_text(STUB_PARSER_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 5 réinitialisé dans `core/parser.py` (Stub NotImplementedError RED).")


def reset_palier_6():
    rb_file = REPO_DIR / "core" / "ringbuffer.py"
    rb_file.write_text(STUB_RINGBUFFER_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 6 réinitialisé dans `core/ringbuffer.py` (Stub NotImplementedError RED).")


STUB_RBTREE_CODE = '''# -*- coding: utf-8 -*-
"""
Module d'Arbre Rouge-Noir Auto-Équilibré (Red-Black Tree).
Palier 7 : Défi algorithmique extrême d'invariants de structures arborescentes et de rotations.
"""

from typing import Optional, List, Any


class Node:
    """Nœud d'arbre rouge-noir."""
    def __init__(self, val: int, color: str = "RED"):
        self.val = val
        self.color = color  # "RED" ou "BLACK"
        self.left: Optional['Node'] = None
        self.right: Optional['Node'] = None
        self.parent: Optional['Node'] = None


class RedBlackTree:
    """
    Arbre binaire de recherche auto-équilibré rouge-noir (Red-Black Tree).
    Garantit une hauteur en O(log N) par maintien des 4 invariants fondamentaux :
    1. Chaque nœud est soit ROUGE soit NOIR.
    2. La racine est toujours NOIRE.
    3. Deux nœuds ROUGES ne peuvent jamais être adjacents (un nœud rouge n'a que des enfants noirs).
    4. Tout chemin d'un nœud à ses feuilles descendantes contient le même nombre de nœuds noirs.
    """

    def __init__(self):
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def insert(self, val: int) -> None:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def search(self, val: int) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def inorder(self) -> List[int]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def get_black_height(self) -> int:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def verify_invariants(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_7():
    rbt_file = REPO_DIR / "core" / "rbtree.py"
    rbt_file.write_text(STUB_RBTREE_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 7 réinitialisé dans `core/rbtree.py` (Stub NotImplementedError RED).")


STUB_CACHE_CODE = '''# -*- coding: utf-8 -*-
"""
Module de Cache LRU (Least Recently Used) haute performance en O(1).
Palier 8 : Défi d'invariants de liste doublement chaînée et table de hachage.
"""

from typing import Any, Optional


class Node:
    """Nœud de liste doublement chaînée pour LRU."""
    def __init__(self, key: Any = None, val: Any = None):
        self.key = key
        self.val = val
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None


class LRUCache:
    """
    Cache LRU avec opérations get et put en temps constant strict O(1).
    Garantit l'éviction de l'élément le moins récemment accédé à saturation.
    Interdiction d'utiliser collections.OrderedDict.
    """

    def __init__(self, capacity: int):
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def get(self, key: Any) -> Any:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def put(self, key: Any, val: Any) -> None:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def size(self) -> int:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def is_empty(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_8():
    cache_file = REPO_DIR / "core" / "cache.py"
    cache_file.write_text(STUB_CACHE_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 8 réinitialisé dans `core/cache.py` (Stub NotImplementedError RED).")


STUB_SKIPLIST_CODE = '''# -*- coding: utf-8 -*-
"""
Module de Concurrent SkipList Map (Ordered Concurrent Map).
Palier 9 : Défi de structure ordonnée haute concurrence avec locking fin par nœud.
"""

import threading
from typing import Any, Optional, Iterator, Tuple, List


class SkipListNode:
    """Nœud d'une Skip List concurrente avec tour de pointeurs et verrou fin."""

    def __init__(self, key: Any = None, value: Any = None, level: int = 1):
        self.key = key
        self.value = value
        self.level = level
        self.forward: List[Optional['SkipListNode']] = [None] * level
        self.marked: bool = False
        self.fully_linked: bool = False
        self.lock = threading.Lock()


class SkipListMap:
    """
    Map concurrente ordonnée basée sur une Skip List à verrouillage fin (Fine-Grained Locking).
    Toutes les opérations d'écriture utilisent un verrouillage local par nœud.
    Les lectures de traversée sont lock-free.
    """

    def __init__(self, max_level: int = 16, p: float = 0.5):
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def put(self, key: Any, value: Any) -> Optional[Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def get(self, key: Any) -> Optional[Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def remove(self, key: Any) -> Optional[Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def contains(self, key: Any) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def size(self) -> int:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def is_empty(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def first_key(self) -> Optional[Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def last_key(self) -> Optional[Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def range(self, start: Optional[Any] = None, end: Optional[Any] = None) -> Iterator[Tuple[Any, Any]]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def validate(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_9():
    skiplist_file = REPO_DIR / "core" / "skiplist.py"
    skiplist_file.write_text(STUB_SKIPLIST_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 9 réinitialisé dans `core/skiplist.py` (Stub NotImplementedError RED).")


STUB_MVCC_CODE = '''# -*- coding: utf-8 -*-
"""
Module Mini MVCC Storage Engine (Snapshot Isolation).
Palier 10 : Moteur de stockage transactionnel multi-versions.
"""

from typing import Any, Optional, Dict, List, Tuple


class WriteConflictError(Exception):
    pass


class TransactionAbortedError(Exception):
    pass


class Version:
    def __init__(self, created_ts: int, value: Any, is_tombstone: bool = False):
        self.created_ts = created_ts
        self.deleted_ts: Optional[int] = None
        self.value = value
        self.is_tombstone = is_tombstone


class MVCCStore:
    def __init__(self):
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def begin_transaction(self) -> int:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def get(self, tx_id: int, key: Any) -> Optional[Any]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def put(self, tx_id: int, key: Any, value: Any) -> None:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def delete(self, tx_id: int, key: Any) -> None:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def commit(self, tx_id: int) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def rollback(self, tx_id: int) -> None:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def vacuum(self) -> int:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def get_history(self, key: Any) -> List[Tuple[int, Optional[int], Any, bool]]:
        raise NotImplementedError("Module non implémenté. Construction requise.")

    def validate_invariants(self) -> bool:
        raise NotImplementedError("Module non implémenté. Construction requise.")
'''


def reset_palier_10():
    mvcc_file = REPO_DIR / "core" / "mvcc.py"
    mvcc_file.write_text(STUB_MVCC_CODE, encoding="utf-8")
    print("🔄 [RESET] Palier 10 réinitialisé dans `core/mvcc.py` (Stub NotImplementedError RED).")


def reset_all():
    reset_palier_1()
    reset_palier_2()
    reset_palier_3()
    reset_palier_4()
    reset_palier_5()
    reset_palier_6()
    reset_palier_7()
    reset_palier_8()
    reset_palier_9()
    reset_palier_10()
    print("✅ [RESET COMPLET] Dépôt remis à zéro pour l'ensemble des benchmarks.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "1":
        reset_palier_1()
    elif len(sys.argv) > 1 and sys.argv[1] == "2":
        reset_palier_2()
    elif len(sys.argv) > 1 and sys.argv[1] == "3":
        reset_palier_3()
    elif len(sys.argv) > 1 and sys.argv[1] == "4":
        reset_palier_4()
    elif len(sys.argv) > 1 and sys.argv[1] == "5":
        reset_palier_5()
    elif len(sys.argv) > 1 and sys.argv[1] == "6":
        reset_palier_6()
    elif len(sys.argv) > 1 and sys.argv[1] == "7":
        reset_palier_7()
    elif len(sys.argv) > 1 and sys.argv[1] == "8":
        reset_palier_8()
    elif len(sys.argv) > 1 and sys.argv[1] == "9":
        reset_palier_9()
    elif len(sys.argv) > 1 and sys.argv[1] == "10":
        reset_palier_10()
    else:
        reset_all()
