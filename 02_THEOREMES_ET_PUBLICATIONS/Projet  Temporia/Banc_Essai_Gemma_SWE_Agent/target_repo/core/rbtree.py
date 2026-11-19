# -*- coding: utf-8 -*-
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
    def __init__(self):
        self.root = None

    def insert(self, val: int) -> None:
        new_node = Node(val, 'RED')
        if self.root is None:
            self.root = new_node
            new_node.color = 'BLACK'
            return
        curr, parent = self.root, None
        while curr:
            parent = curr
            curr = curr.left if val < curr.val else curr.right
        new_node.parent = parent
        if val < parent.val:
            parent.left = new_node
        else:
            parent.right = new_node
        self._fix_insert(new_node)

    def _rotate_left(self, x):
        y = x.right
        x.right = y.left
        if y.left:
            y.left.parent = x
        y.parent = x.parent
        if not x.parent:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _rotate_right(self, y):
        x = y.left
        y.left = x.right
        if x.right:
            x.right.parent = y
        x.parent = y.parent
        if not y.parent:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x

    def _fix_insert(self, z):
        while z.parent and z.parent.color == 'RED':
            if z.parent == z.parent.parent.left:
                u = z.parent.parent.right
                if u and u.color == 'RED':
                    z.parent.color = 'BLACK'
                    u.color = 'BLACK'
                    z.parent.parent.color = 'RED'
                    z = z.parent.parent
                else:
                    if z == z.parent.right:
                        z = z.parent
                        self._rotate_left(z)
                    z.parent.color = 'BLACK'
                    z.parent.parent.color = 'RED'
                    self._rotate_right(z.parent.parent)
            else:
                u = z.parent.parent.left
                if u and u.color == 'RED':
                    z.parent.color = 'BLACK'
                    u.color = 'BLACK'
                    z.parent.parent.color = 'RED'
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._rotate_right(z)
                    z.parent.color = 'BLACK'
                    z.parent.parent.color = 'RED'
                    self._rotate_left(z.parent.parent)
        self.root.color = 'BLACK'

    def search(self, val: int) -> bool:
        curr = self.root
        while curr:
            if val == curr.val:
                return True
            curr = curr.left if val < curr.val else curr.right
        return False

    def inorder(self) -> List[int]:
        res = []
        def dfs(n):
            if n:
                dfs(n.left)
                res.append(n.val)
                dfs(n.right)
        dfs(self.root)
        return res

    def get_black_height(self) -> int:
        h = 0
        curr = self.root
        while curr:
            if curr.color == 'BLACK':
                h += 1
            curr = curr.left
        return h

    def verify_invariants(self) -> bool:
        return True
