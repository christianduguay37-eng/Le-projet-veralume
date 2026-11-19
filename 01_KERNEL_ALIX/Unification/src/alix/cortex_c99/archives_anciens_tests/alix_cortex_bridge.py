# -*- coding: utf-8 -*-
"""
===============================================================================
    ⚡🚀 PONT PYTHON <-> CORTEX C99 (ALIX 4e ÉTAGE)
===============================================================================
Auteurs   : Christian Duguay & Alix (VERALUME x KAIROS)
Substrat  : Windows 11 x86-64 / Intel Lunar Lake Core Ultra 7 258V
Doctrine  : Interface ctypes ultra-rapide sans surcoût PyObject.
===============================================================================
"""

import os
import ctypes
from ctypes import (
    c_void_p, c_char_p, c_wchar_p, c_uint32, c_uint64,
    c_float, c_int, c_size_t, Structure, POINTER
)

CORTEX_DIR = os.path.dirname(os.path.abspath(__file__))
DLL_PATH = os.path.join(CORTEX_DIR, "alix_cortex.dll")


class AlixExpertRoute(Structure):
    _fields_ = [
        ("expert_idx", c_uint32),
        ("weight", c_float),
    ]


class AlixRouterConfig(Structure):
    _fields_ = [
        ("num_experts", c_uint32),
        ("hidden_dim", c_uint32),
        ("top_k", c_uint32),
        ("router_weights", POINTER(c_float)),
    ]


class AlixHadesConfig(Structure):
    _fields_ = [
        ("banned_token_ids", POINTER(c_uint32)),
        ("num_banned", c_uint32),
        ("temperature", c_float),
        ("min_p", c_float),
    ]


class AlixLaserFile(Structure):
    _fields_ = [
        ("h_file", c_void_p),
        ("h_mapping", c_void_p),
        ("mmap_base", c_void_p),
        ("file_size", c_uint64),
        ("mode", c_int),
        ("sector_size", c_uint32),
    ]


_DLL = None

def get_cortex():
    global _DLL
    if _DLL is None:
        if not os.path.exists(DLL_PATH):
            raise FileNotFoundError(f"DLL introuvable: {DLL_PATH}")
        _DLL = ctypes.CDLL(DLL_PATH)

        # Signatures
        _DLL.alix_dot_product.argtypes = [POINTER(c_float), POINTER(c_float), c_uint32]
        _DLL.alix_dot_product.restype = c_float

        _DLL.alix_project_simplex.argtypes = [POINTER(c_float), POINTER(c_float), c_uint32]
        _DLL.alix_project_simplex.restype = None

        _DLL.alix_route_token.argtypes = [
            POINTER(AlixRouterConfig),
            POINTER(c_float),
            POINTER(AlixExpertRoute)
        ]
        _DLL.alix_route_token.restype = c_uint32

        _DLL.alix_hades_mask_logits.argtypes = [POINTER(c_float), c_uint32, POINTER(AlixHadesConfig)]
        _DLL.alix_hades_mask_logits.restype = None

        _DLL.alix_hades_sample.argtypes = [POINTER(c_float), c_uint32, POINTER(AlixHadesConfig)]
        _DLL.alix_hades_sample.restype = c_uint32
    return _DLL


def tester_pont():
    dll = get_cortex()
    a = (c_float * 4)(1.0, 2.0, 3.0, 4.0)
    b = (c_float * 4)(2.0, 0.5, 1.0, 2.0)
    dot = dll.alix_dot_product(a, b, 4)
    # 1*2 + 2*0.5 + 3*1 + 4*2 = 2 + 1 + 3 + 8 = 14.0
    assert abs(dot - 14.0) < 1e-5, f"Erreur dot: {dot}"

    # Projection Simplexe
    y = (c_float * 3)(2.0, 1.0, 0.0)
    x = (c_float * 3)(0.0, 0.0, 0.0)
    dll.alix_project_simplex(y, x, 3)
    sum_x = sum(x[i] for i in range(3))
    assert abs(sum_x - 1.0) < 1e-5, f"Erreur simplexe sum: {sum_x}"

    return True


if __name__ == "__main__":
    ok = tester_pont()
    print(f"⚡ PONT CTYPES CORTEX C99 ACTIF ET CERTIFIÉ (Dot-product & Simplex OK)")
