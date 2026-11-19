# -*- coding: utf-8 -*-
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
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: Any) -> Any:
        if key in self.cache:
            node = self.cache[key]
            self._remove_node(node)
            self._add_to_head(node)
            return node.val
        return None

    def put(self, key: Any, val: Any) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.val = val
            self._remove_node(node)
            self._add_to_head(node)
        else:
            if len(self.cache) >= self.capacity:
                lru = self.tail.prev
                self._remove_node(lru)
                del self.cache[lru.key]
            new_node = Node(key, val)
            self.cache[key] = new_node
            self._add_to_head(new_node)

    def size(self) -> int:
        return len(self.cache)

    def is_empty(self) -> bool:
        return len(self.cache) == 0

    def _remove_node(self, node: Node):
        p = node.prev
        n = node.next
        p.next = n
        n.prev = p

    def _add_to_head(self, node: Node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
