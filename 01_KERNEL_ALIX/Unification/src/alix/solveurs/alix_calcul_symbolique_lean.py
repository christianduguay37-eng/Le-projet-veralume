# -*- coding: utf-8 -*-
"""
================================================================================
   ALIX CALCUL SYMBOLIQUE, DIMENSIONNEL & AUDITEUR LEAN 4 (Couche 3 — Déterministe)
================================================================================
Moteur déterministe conçu pour être branché comme outil du Kernel partagé
(`alix_calculer_exact` dans `alix.mcp.outils_metal`), et pour auditer les
théorèmes Lean 4 émis par `alix_math_lean_60m.pt`.

Bibliothèques lourdes (`sympy`, `torch`) importées paresseusement dans les
fonctions : importer ce module coûte ~0 ms et 0 Mo RAM au démarrage du relais MCP.
================================================================================
"""
from __future__ import annotations

import ast
import operator
import re
import shutil
import threading
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# 1. NORMALISATION & ÉVALUATION ARITHMÉTIQUE EXACTE (AST + FRACTION)
# =============================================================================

_OPS_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_OPS_UN = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_SUBSUP_MAP = str.maketrans({
    "²": "^2",
    "³": "^3",
    "−": "-",
    "–": "-",
    "×": "*",
    "·": "*",
    "÷": "/",
})


def normaliser_expression(texte: str) -> str:
    txt = texte.translate(_SUBSUP_MAP)
    txt = txt.replace("≤", "<=").replace("≥", ">=").replace("≠", "!=")
    txt = re.sub(r"\bmodulo\b|\bmod\b", "%", txt, flags=re.IGNORECASE)
    return txt.strip()


def formater_fraction(val: Fraction) -> str:
    if val.denominator == 1:
        return str(val.numerator)
    dec = float(val)
    return f"{val.numerator}/{val.denominator} ({dec:.6g})"


def evaluer_arithmetique_ast(expression: str) -> Dict[str, Any]:
    """Évalue exactement une expression numérique via AST Python et fractions.Fraction."""
    t0 = time.perf_counter()
    expr_norm = normaliser_expression(expression).replace("^", "**")
    tree = ast.parse(expr_norm, mode="eval")

    def _eval(node: ast.AST) -> Fraction:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Fraction(str(node.value))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS_BIN:
            g, d = _eval(node.left), _eval(node.right)
            if isinstance(node.op, ast.Pow) and d > 10000:
                raise ValueError("Exposant trop élevé pour évaluation sûre (> 10000)")
            return _OPS_BIN[type(node.op)](g, d)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS_UN:
            return _OPS_UN[type(node.op)](_eval(node.operand))
        raise ValueError(f"Élément AST non autorisé en mode arithmétique : {type(node).__name__}")

    val = _eval(tree)
    details: Dict[str, Any] = {
        "statut": "OK",
        "mode": "arithmetique",
        "expression": expression.strip(),
        "resultat": formater_fraction(val),
        "valeur_exacte": str(val.numerator) if val.denominator == 1 else f"{val.numerator}/{val.denominator}",
        "valeur_decimale": float(val),
        "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
    }

    m_mod = re.fullmatch(r"\s*(-?\d+)\s*%\s*(-?\d+)\s*", expr_norm)
    if m_mod:
        n, d = int(m_mod.group(1)), int(m_mod.group(2))
        q, r = divmod(n, d)
        details["quotient"] = q
        details["reste"] = r
    return details


# =============================================================================
# 2. CALCUL SYMBOLIQUE GÉNÉRAL (SYMPY)
# =============================================================================

def _sympy_parser_config():
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        implicit_multiplication_application,
        parse_expr,
        standard_transformations,
    )
    transforms = standard_transformations + (implicit_multiplication_application,)
    return sp, parse_expr, transforms


def _formater_sympy(expr: Any) -> str:
    return str(expr).replace("**", "^")


def _detecter_symbole(expr_str: str, variable: str = ""):
    sp, parse_expr, transforms = _sympy_parser_config()
    norm = normaliser_expression(expr_str).replace("^", "**")
    expr = parse_expr(norm, transformations=transforms)
    if variable:
        sym = sp.Symbol(variable, real=True)
    else:
        syms = sorted(expr.free_symbols, key=lambda s: s.name)
        sym = sp.Symbol(syms[0].name, real=True) if syms else sp.Symbol("x", real=True)
    expr = parse_expr(norm, local_dict={sym.name: sym}, transformations=transforms)
    return sp, expr, sym


def resoudre_sympy(expression: str, action: str = "auto", variable: str = "") -> Dict[str, Any]:
    """Résout équations, inégalités, développements, factorisations, dérivées/intégrales via SymPy."""
    t0 = time.perf_counter()
    sp, parse_expr, transforms = _sympy_parser_config()
    norm = normaliser_expression(expression)

    # Extraire forme naturelle "d/dx (...)" ou "f(x) = ..." pour dériver
    m_ddx = re.match(r"^\s*d/d([A-Za-z])\s+(.+)$", norm)
    if m_ddx:
        variable = variable or m_ddx.group(1)
        norm_clean = m_ddx.group(2).strip()
        if action == "auto":
            action = "deriver"
    else:
        norm_clean = re.sub(r"^[A-Za-z]\(\s*([A-Za-z])\s*\)\s*=\s*", "", norm).strip()
        if not variable:
            m_fx = re.search(r"[A-Za-z]\(\s*([A-Za-z])\s*\)\s*=", norm)
            if m_fx:
                variable = m_fx.group(1)

    if action == "auto":
        if any(op in norm_clean for op in ("<=", ">=", "<", ">")):
            action = "inegalite"
        elif "=" in norm_clean:
            action = "resoudre"
        else:
            action = "developper"

    resultat_texte = ""
    details: Dict[str, Any] = {}

    if action == "inegalite":
        m_op = re.search(r"(.+?)(<=|>=|<|>)(.+)", norm_clean)
        if not m_op:
            raise ValueError(f"Inégalité illisible : {expression}")
        g_s, op, d_s = m_op.group(1).strip(), m_op.group(2), m_op.group(3).strip()
        _, g_e, sym = _detecter_symbole(g_s, variable)
        d_e = parse_expr(d_s.replace("^", "**"), local_dict={sym.name: sym}, transformations=transforms)
        rel_map = {"<=": g_e <= d_e, ">=": g_e >= d_e, "<": g_e < d_e, ">": g_e > d_e}
        sol = sp.solve_univariate_inequality(rel_map[op], sym, relational=True)
        resultat_texte = _formater_sympy(sol)
        details["symbole"] = sym.name

    elif action in ("resoudre", "verifier_egalite"):
        if "=" not in norm_clean:
            raise ValueError(f"Égalité attendue avec '=' : {expression}")
        g_s, d_s = norm_clean.split("=", 1)
        _, g_e, sym = _detecter_symbole(g_s, variable)
        d_e = parse_expr(d_s.strip().replace("^", "**"), local_dict={sym.name: sym}, transformations=transforms)
        diff = sp.simplify(g_e - d_e)
        if action == "verifier_egalite":
            egales = (diff == 0)
            resultat_texte = "VRAI" if egales else f"FAUX (écart : {_formater_sympy(diff)})"
            details["egales"] = bool(egales)
            details["ecart"] = _formater_sympy(diff)
        else:
            if diff == 0:
                resultat_texte = f"Identité vraie pour tout {sym.name}"
                details["solutions"] = ["IDENTITE"]
            else:
                sols = sp.solve(sp.Eq(g_e, d_e), sym)
                sols_str = [_formater_sympy(s) for s in sols]
                resultat_texte = " ou ".join(f"{sym.name} = {s}" for s in sols_str) if sols_str else "Aucune solution réelle"
                details["solutions"] = sols_str
                details["symbole"] = sym.name

    elif action == "developper":
        _, expr, sym = _detecter_symbole(norm_clean, variable)
        dev = sp.expand(expr)
        resultat_texte = _formater_sympy(dev)
        details["forme_developpee"] = resultat_texte
        details["symbole"] = sym.name

    elif action == "factoriser":
        _, expr, sym = _detecter_symbole(norm_clean, variable)
        fac = sp.factor(expr)
        resultat_texte = _formater_sympy(fac)
        details["forme_factorisee"] = resultat_texte

    elif action == "simplifier":
        _, expr, _ = _detecter_symbole(norm_clean, variable)
        sim = sp.simplify(expr)
        resultat_texte = _formater_sympy(sim)

    elif action == "deriver":
        _, expr, sym = _detecter_symbole(norm_clean, variable)
        df = sp.diff(expr, sym)
        resultat_texte = _formater_sympy(df)
        details["derivee_par_rapport_a"] = sym.name

    elif action == "integrer":
        _, expr, sym = _detecter_symbole(norm_clean, variable)
        integ = sp.integrate(expr, sym)
        resultat_texte = _formater_sympy(integ)
        details["primitive_par_rapport_a"] = sym.name

    else:
        raise ValueError(f"Action SymPy inconnue : {action}")

    return {
        "statut": "OK",
        "mode": "sympy",
        "action": action,
        "expression": expression.strip(),
        "resultat": resultat_texte,
        "details": details,
        "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
    }


# =============================================================================
# 3. ANALYSE DIMENSIONNELLE VECTORIELLE EXACTE (SYSTÈME DE GRANDEURS)
# =============================================================================

# Signature dimensionnelle : (M, L, T, DATA, I, THETA)
DimVec = Tuple[int, int, int, int, int, int]

DIM_ZERO: DimVec = (0, 0, 0, 0, 0, 0)
DIM_MASSE: DimVec = (1, 0, 0, 0, 0, 0)
DIM_LONGUEUR: DimVec = (0, 1, 0, 0, 0, 0)
DIM_TEMPS: DimVec = (0, 0, 1, 0, 0, 0)
DIM_DONNEES: DimVec = (0, 0, 0, 1, 0, 0)
DIM_COURANT: DimVec = (0, 0, 0, 0, 1, 0)
DIM_TEMP: DimVec = (0, 0, 0, 0, 0, 1)
DIM_VITESSE: DimVec = (0, 1, -1, 0, 0, 0)
DIM_FORCE: DimVec = (1, 1, -2, 0, 0, 0)
DIM_ENERGIE: DimVec = (1, 2, -2, 0, 0, 0)
DIM_PUISSANCE: DimVec = (1, 2, -3, 0, 0, 0)
DIM_FREQUENCE: DimVec = (0, 0, -1, 0, 0, 0)
DIM_TENSION: DimVec = (1, 2, -3, 0, -1, 0)
DIM_RESISTANCE: DimVec = (1, 2, -3, 0, -2, 0)
DIM_DEBIT_DATA: DimVec = (0, 0, -1, 1, 0, 0)

NOMS_DIMENSIONS: Dict[DimVec, Tuple[str, str]] = {
    DIM_ZERO: ("SANS_DIMENSION", ""),
    DIM_MASSE: ("MASSE", "kg"),
    DIM_LONGUEUR: ("LONGUEUR", "m"),
    DIM_TEMPS: ("TEMPS", "s"),
    DIM_DONNEES: ("DONNEES", "octets"),
    DIM_COURANT: ("COURANT", "A"),
    DIM_TEMP: ("TEMPERATURE", "K"),
    DIM_VITESSE: ("VITESSE", "m/s"),
    DIM_FORCE: ("FORCE", "N"),
    DIM_ENERGIE: ("ENERGIE", "J"),
    DIM_PUISSANCE: ("PUISSANCE", "W"),
    DIM_FREQUENCE: ("FREQUENCE", "Hz"),
    DIM_TENSION: ("TENSION", "V"),
    DIM_RESISTANCE: ("RESISTANCE", "ohm"),
    DIM_DEBIT_DATA: ("DEBIT_DONNEES", "octets/s"),
}


@dataclass(frozen=True)
class UniteSpec:
    symbole: str
    dim: DimVec
    facteur: Fraction


def _construire_catalogue_unites() -> Dict[str, UniteSpec]:
    u: Dict[str, UniteSpec] = {}
    def add(noms: Tuple[str, ...], dim: DimVec, facteur: Fraction, sym: str):
        spec = UniteSpec(sym, dim, facteur)
        for nom in noms:
            u[nom.lower()] = spec

    # Données (canonique = octet ; IEC binaire 1024 pour Ko/Mo/Go/To)
    add(("bit", "bits", "b"), DIM_DONNEES, Fraction(1, 8), "bits")
    add(("kb", "kbit", "kbits"), DIM_DONNEES, Fraction(1024, 8), "Kb")
    add(("mb", "mbit", "mbits"), DIM_DONNEES, Fraction(1024 ** 2, 8), "Mb")
    add(("gb", "gbit", "gbits"), DIM_DONNEES, Fraction(1024 ** 3, 8), "Gb")
    add(("o", "octet", "octets"), DIM_DONNEES, Fraction(1), "octets")
    add(("ko", "kio"), DIM_DONNEES, Fraction(1024), "Ko")
    add(("mo", "mio"), DIM_DONNEES, Fraction(1024 ** 2), "Mo")
    add(("go", "gio"), DIM_DONNEES, Fraction(1024 ** 3), "Go")
    add(("to", "tio"), DIM_DONNEES, Fraction(1024 ** 4), "To")

    # Temps (canonique = s)
    add(("ns",), DIM_TEMPS, Fraction(1, 10 ** 9), "ns")
    add(("us", "µs"), DIM_TEMPS, Fraction(1, 10 ** 6), "us")
    add(("ms", "milliseconde", "millisecondes"), DIM_TEMPS, Fraction(1, 1000), "ms")
    add(("s", "sec", "seconde", "secondes"), DIM_TEMPS, Fraction(1), "s")
    add(("min", "minute", "minutes"), DIM_TEMPS, Fraction(60), "min")
    add(("h", "heure", "heures"), DIM_TEMPS, Fraction(3600), "h")

    # Énergie (canonique = J)
    add(("mj",), DIM_ENERGIE, Fraction(1, 1000), "mJ")
    add(("j", "joule", "joules"), DIM_ENERGIE, Fraction(1), "J")
    add(("kj",), DIM_ENERGIE, Fraction(1000), "kJ")

    # Puissance (canonique = W)
    add(("mw",), DIM_PUISSANCE, Fraction(1, 1000), "mW")
    add(("w", "watt", "watts"), DIM_PUISSANCE, Fraction(1), "W")
    add(("kw",), DIM_PUISSANCE, Fraction(1000), "kW")

    # Fréquence (canonique = Hz)
    add(("hz", "hertz"), DIM_FREQUENCE, Fraction(1), "Hz")
    add(("khz",), DIM_FREQUENCE, Fraction(1000), "kHz")
    add(("mhz",), DIM_FREQUENCE, Fraction(1000 ** 2), "MHz")
    add(("ghz",), DIM_FREQUENCE, Fraction(1000 ** 3), "GHz")

    # Masse, Longueur, Électricité, Température
    add(("mg",), DIM_MASSE, Fraction(1, 10 ** 6), "mg")
    add(("g", "gramme", "grammes"), DIM_MASSE, Fraction(1, 1000), "g")
    add(("kg", "kilogramme", "kilogrammes"), DIM_MASSE, Fraction(1), "kg")
    add(("mm",), DIM_LONGUEUR, Fraction(1, 1000), "mm")
    add(("cm",), DIM_LONGUEUR, Fraction(1, 100), "cm")
    add(("m", "metre", "metres", "mètre", "mètres"), DIM_LONGUEUR, Fraction(1), "m")
    add(("km",), DIM_LONGUEUR, Fraction(1000), "km")
    add(("v", "volt", "volts"), DIM_TENSION, Fraction(1), "V")
    add(("a", "ampere", "amperes", "ampère", "ampères"), DIM_COURANT, Fraction(1), "A")
    add(("ohm", "ohms"), DIM_RESISTANCE, Fraction(1), "ohm")
    add(("k", "kelvin"), DIM_TEMP, Fraction(1), "K")
    return u


UNITES = _construire_catalogue_unites()


def _resoudre_unite(unite_str: str) -> UniteSpec:
    u_raw = unite_str.strip()
    cle = u_raw.lower()
    if cle in UNITES:
        return UNITES[cle]
    if "/" in u_raw:
        num_s, den_s = u_raw.split("/", 1)
        num_u = _resoudre_unite(num_s)
        den_u = _resoudre_unite(den_s)
        dim = tuple(a - b for a, b in zip(num_u.dim, den_u.dim))
        return UniteSpec(f"{num_u.symbole}/{den_u.symbole}", dim, num_u.facteur / den_u.facteur)
    raise ValueError(f"Unité inconnue : '{unite_str}'")


def _nom_dimension(dim: DimVec) -> str:
    if dim in NOMS_DIMENSIONS:
        return NOMS_DIMENSIONS[dim][0]
    etiquettes = ["M", "L", "T", "DATA", "I", "Θ"]
    parties = [f"{e}^{p}" if p != 1 else e for e, p in zip(etiquettes, dim) if p != 0]
    return "*".join(parties) or "SANS_DIMENSION"


def analyser_dimensionnel(expression: str, vers_unite: str = "") -> Dict[str, Any]:
    """Vérifie l'homogénéité physique et effectue conversions / produits / quotients exacts."""
    t0 = time.perf_counter()
    txt = normaliser_expression(expression)

    # Extraire toutes les paires <nombre> <unité> (avec unité composée possible comme Mo/s)
    # Important : distinguer "40 Go / 8 s" (deux grandeurs) d'une unité composée "5 Mo/s"
    pattern = re.compile(
        r"(-?\d+(?:[.,]\d+)?)\s*([A-Za-zµ°]+(?:/[A-Za-z]+)?)(?=\s|$|[\+\-\*\)/,;?])"
    )
    matches: List[Tuple[Fraction, UniteSpec, int, int]] = []
    for m in pattern.finditer(txt):
        u_txt = m.group(2)
        try:
            spec = _resoudre_unite(u_txt)
        except ValueError:
            continue
        val = Fraction(m.group(1).replace(",", "."))
        matches.append((val, spec, m.start(), m.end()))

    if not matches:
        raise ValueError(f"Aucune grandeur physique reconnue dans : {expression}")

    # Cas 1 : conversion simple d'une seule grandeur (ou avec "en <unite>" dans le texte)
    if len(matches) == 1:
        val, spec, _, _ = matches[0]
        if not vers_unite:
            m_vers = re.search(r"\b(?:en|vers|->)\s+([A-Za-zµ]+(?:/[A-Za-z]+)?)\b", txt, re.I)
            if m_vers:
                vers_unite = m_vers.group(1)
        if vers_unite:
            cible = _resoudre_unite(vers_unite)
            if cible.dim != spec.dim:
                return {
                    "statut": "ILLICITE_DIMENSIONNEL",
                    "mode": "dimensionnel",
                    "erreur": f"Conversion impossible : {_nom_dimension(spec.dim)} vers {_nom_dimension(cible.dim)}",
                    "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
                }
            res = (val * spec.facteur) / cible.facteur
            return {
                "statut": "OK",
                "mode": "dimensionnel",
                "operation": "conversion",
                "resultat": f"{formater_fraction(res)} {cible.symbole}",
                "valeur_exacte": formater_fraction(res),
                "unite": cible.symbole,
                "dimension": _nom_dimension(cible.dim),
                "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        return {
            "statut": "OK",
            "mode": "dimensionnel",
            "resultat": f"{formater_fraction(val)} {spec.symbole}",
            "dimension": _nom_dimension(spec.dim),
            "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
        }

    # Cas 2 : deux grandeurs -> déterminer l'opérateur entre elles (+, -, *, /)
    (v1, s1, _, fin1), (v2, s2, deb2, _) = matches[0], matches[1]
    entre = txt[fin1:deb2].lower()

    if any(tok in entre for tok in ("/", "par", "en", "pendant", "durant", "sur")):
        op = "/"
    elif any(tok in entre for tok in ("*", "fois")):
        op = "*"
    elif "-" in entre:
        op = "-"
    elif "+" in entre or "et" in entre or "avec" in entre:
        op = "+"
    else:
        raise ValueError(f"Opérateur physique ambigu entre '{s1.symbole}' et '{s2.symbole}'")

    if op in ("+", "-"):
        if s1.dim != s2.dim:
            return {
                "statut": "ILLICITE_DIMENSIONNEL",
                "mode": "dimensionnel",
                "operation": "addition" if op == "+" else "soustraction",
                "resultat": (
                    f"ILLICITE — Conflit dimensionnel : [{_nom_dimension(s1.dim)}] ({s1.symbole}) "
                    f"incompatible avec [{_nom_dimension(s2.dim)}] ({s2.symbole})"
                ),
                "dimension_gauche": _nom_dimension(s1.dim),
                "dimension_droite": _nom_dimension(s2.dim),
                "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        cible = _resoudre_unite(vers_unite) if vers_unite else s1
        if cible.dim != s1.dim:
            raise ValueError("Unité cible incompatible avec les opérandes")
        canon = (v1 * s1.facteur) + (v2 * s2.facteur) if op == "+" else (v1 * s1.facteur) - (v2 * s2.facteur)
        res = canon / cible.facteur
        return {
            "statut": "OK",
            "mode": "dimensionnel",
            "operation": "addition" if op == "+" else "soustraction",
            "resultat": f"{formater_fraction(res)} {cible.symbole}",
            "dimension": _nom_dimension(s1.dim),
            "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
        }

    # Produit ou quotient
    sign = 1 if op == "*" else -1
    dim_res = tuple(a + sign * b for a, b in zip(s1.dim, s2.dim))
    val_canon = (v1 * s1.facteur) * (v2 * s2.facteur) if op == "*" else (v1 * s1.facteur) / (v2 * s2.facteur)

    equivalents: Dict[str, str] = {}
    if vers_unite:
        cible = _resoudre_unite(vers_unite)
        if cible.dim != dim_res:
            raise ValueError(f"Unité cible '{vers_unite}' incompatible avec {_nom_dimension(dim_res)}")
        res_fmt = f"{formater_fraction(val_canon / cible.facteur)} {cible.symbole}"
    elif dim_res == DIM_DEBIT_DATA:
        mo_s = val_canon / Fraction(1024 ** 2)
        mb_s = mo_s * 8
        go_s = val_canon / Fraction(1024 ** 3)
        equivalents = {
            "Mo/s": formater_fraction(mo_s),
            "Mb/s": formater_fraction(mb_s),
            "Go/s": formater_fraction(go_s),
        }
        res_fmt = f"{equivalents['Mo/s']} Mo/s ({equivalents['Mb/s']} Mb/s) = {equivalents['Go/s']} Go/s"
    elif dim_res in NOMS_DIMENSIONS and NOMS_DIMENSIONS[dim_res][1]:
        sym_canon = NOMS_DIMENSIONS[dim_res][1]
        res_fmt = f"{formater_fraction(val_canon)} {sym_canon}".strip()
    else:
        res_fmt = f"{formater_fraction(val_canon)} [{_nom_dimension(dim_res)}]"

    return {
        "statut": "OK",
        "mode": "dimensionnel",
        "operation": "produit" if op == "*" else "quotient",
        "resultat": res_fmt,
        "dimension": _nom_dimension(dim_res),
        "equivalents": equivalents,
        "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
    }


# =============================================================================
# 4. VÉRIFICATEUR LOGIQUE PROPOSITIONNELLE GÉNÉRAL (SYMPY + TABLE / SAT)
# =============================================================================

def _compiler_formule_bool(formule: str, sp: Any):
    """Parse une formule propositionnelle avec ->, <->, ¬/~, ∧/&, ∨/| vers SymPy BoolAlg."""
    # Tokeniseur descendant propre pour supporter -> (right-assoc) et <->
    s = formule.replace("→", "->").replace("↔", "<->")
    s = s.replace("∧", "&").replace("&&", "&").replace("∨", "|").replace("||", "|")
    s = s.replace("¬", "~").replace("!", "~")
    tokens = re.findall(r"<->|->|[()~&|]|[A-Za-z_][A-Za-z0-9_]*", s)
    pos = [0]
    syms: Dict[str, Any] = {}

    def peek() -> Optional[str]:
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume(expected: Optional[str] = None) -> str:
        tok = peek()
        if tok is None or (expected and tok != expected):
            raise ValueError(f"Jeton attendu '{expected}', obtenu '{tok}' dans '{formule}'")
        pos[0] += 1
        return tok

    def parse_iff():
        gauche = parse_imp()
        while peek() == "<->":
            consume("<->")
            droite = parse_imp()
            gauche = sp.Equivalent(gauche, droite)
        return gauche

    def parse_imp():
        gauche = parse_or()
        if peek() == "->":
            consume("->")
            droite = parse_imp()
            return sp.Implies(gauche, droite)
        return gauche

    def parse_or():
        gauche = parse_and()
        while peek() == "|":
            consume("|")
            droite = parse_and()
            gauche = sp.Or(gauche, droite)
        return gauche

    def parse_and():
        gauche = parse_not()
        while peek() == "&":
            consume("&")
            droite = parse_not()
            gauche = sp.And(gauche, droite)
        return gauche

    def parse_not():
        if peek() == "~":
            consume("~")
            return sp.Not(parse_not())
        if peek() == "(":
            consume("(")
            val = parse_iff()
            consume(")")
            return val
        nom = consume()
        if nom in ("True", "TRUE", "1"):
            return sp.true
        if nom in ("False", "FALSE", "0"):
            return sp.false
        if nom not in syms:
            syms[nom] = sp.Symbol(nom)
        return syms[nom]

    ast_bool = parse_iff()
    if pos[0] != len(tokens):
        raise ValueError(f"Fin inattendue après '{tokens[pos[0]]}' dans '{formule}'")
    return ast_bool, syms


def verifier_logique_propositionnelle(
    premisses: Optional[List[str]] = None,
    conclusion: str = "",
    formule: str = "",
) -> Dict[str, Any]:
    """Prouve par SAT / SymPy si (prémisse_1 & ...) -> conclusion (ou formule) est une tautologie."""
    t0 = time.perf_counter()
    import sympy as sp
    from sympy.logic.inference import satisfiable

    if formule and not premisses and not conclusion:
        cible_expr, _ = _compiler_formule_bool(formule, sp)
        libelle = formule
    else:
        prems = premisses or []
        if not conclusion:
            raise ValueError("Fournir soit 'formule', soit 'premisses' + 'conclusion'")
        exprs_p = [_compiler_formule_bool(p, sp)[0] for p in prems]
        expr_c, _ = _compiler_formule_bool(conclusion, sp)
        cible_expr = sp.Implies(sp.And(*exprs_p), expr_c) if exprs_p else expr_c
        libelle = f"({' ∧ '.join(prems)}) → ({conclusion})" if prems else conclusion

    # Une formule F est une tautologie ssi ~F est insatisfiable (UNSAT)
    contre = satisfiable(sp.Not(cible_expr))
    est_tautologie = (contre is False)
    est_contradiction = (satisfiable(cible_expr) is False)

    res: Dict[str, Any] = {
        "statut": "OK",
        "mode": "logique",
        "enonce": libelle,
        "tautologie": est_tautologie,
        "contradiction": est_contradiction,
        "resultat": "TAUTOLOGIE_VALIDE" if est_tautologie else (
            "CONTRADICTION" if est_contradiction else "CONTINGENTE (contre-exemple trouvé)"
        ),
        "contre_exemple": None if est_tautologie or not isinstance(contre, dict) else {str(k): bool(v) for k, v in contre.items()},
        "variables": sorted(str(s) for s in cible_expr.free_symbols),
        "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
    }
    return res


# =============================================================================
# 5. AUDITEUR LEAN 4 GÉNÉRAL + COUPLAGE OPTIONNEL AU MODÈLE 57.1M
# =============================================================================

_CACHE_57M_LOCK = threading.Lock()
_CACHE_57M: Dict[str, Any] = {}


def _charger_57m_paresseux():
    with _CACHE_57M_LOCK:
        if "model" in _CACHE_57M:
            return _CACHE_57M["model"], _CACHE_57M["tok"]
        import sys
        import torch

        racine = Path(r"C:\Alix\Modele_Alix_From_Scratch") if Path(r"C:\Alix\Modele_Alix_From_Scratch").exists() else Path.home() / "Desktop" / "Projet alix" / "Modele_Alix_From_Scratch"
        p_weights = racine / "alix_math_lean_60m.pt"
        if not p_weights.exists():
            raise FileNotFoundError(f"Poids introuvables : {p_weights}")
        if str(racine) not in sys.path:
            sys.path.insert(0, str(racine))
        from banc_essai_math_lean_massif import AlixMathLean, ByteTokenizer, MathLeanConfig

        tok = ByteTokenizer()
        model = AlixMathLean(MathLeanConfig())
        model.load_state_dict(torch.load(p_weights, map_location="cpu", weights_only=True))
        model.eval()
        _CACHE_57M["model"] = model
        _CACHE_57M["tok"] = tok
        return model, tok


def _delimiters_equilibres(texte: str) -> bool:
    paires = {")": "(", "]": "[", "}": "{"}
    pile: List[str] = []
    for ch in texte:
        if ch in "([{":
            pile.append(ch)
        elif ch in paires:
            if not pile or pile[-1] != paires[ch]:
                return False
            pile.pop()
    return not pile


def _extraire_clause_lean(code: str) -> str:
    if ":=" not in code:
        return ""
    entete = code.split(":=", 1)[0]
    prof = 0
    dernier_deux_pts = -1
    for i, ch in enumerate(entete):
        if ch in "({[":
            prof += 1
        elif ch in ")}]":
            prof = max(0, prof - 1)
        elif ch == ":" and prof == 0:
            dernier_deux_pts = i
    if dernier_deux_pts == -1:
        return ""
    clause = entete[dernier_deux_pts + 1 :].strip()
    return re.sub(r"^∀[^,]*,\s*", "", clause).strip()


def auditer_lean4(code: str, spec_attendue: str = "") -> Dict[str, Any]:
    """Audite la syntaxe moderne Lean 4 et vérifie mathématiquement la proposition via SymPy/AST."""
    t0 = time.perf_counter()
    s = code.strip()
    lean3_markers = ["begin\n", " begin ", "\nbegin", "\nend", "assume ", "refl,"]
    a_lean3 = any(m in s for m in lean3_markers)
    a_theorem = bool(re.search(r"\b(?:theorem|lemma|example)\s*[A-Za-z0-9_']*", s))
    a_tactique = bool(re.search(r":=\s*(?:by\s+\w+|le_trans|Or\.inl|Or\.inr|fun\s+)", s))
    equilibre = _delimiters_equilibres(s)

    clause = _extraire_clause_lean(s)
    math_verifie: Optional[bool] = None
    detail_math = ""

    if clause:
        norm = normaliser_expression(clause)
        if "%" in norm and "=" in norm:
            m_mod = re.fullmatch(r"\s*(\d+)\s*%\s*(\d+)\s*=\s*(\d+)\s*", norm)
            if m_mod:
                n, d, r = int(m_mod.group(1)), int(m_mod.group(2)), int(m_mod.group(3))
                math_verifie = ((n % d) == r)
                detail_math = f"{n} % {d} == {n % d} vs {r}"
        elif "=" in norm and "≤" not in clause and "<=" not in norm:
            try:
                verif = resoudre_sympy(clause, action="verifier_egalite")
                math_verifie = verif["details"]["egales"]
                detail_math = verif["resultat"]
            except Exception as e:
                detail_math = f"Analyse symbolique impossible : {e}"

    coherent = True
    if spec_attendue:
        coherent = bool(clause) and (
            spec_attendue.replace(" ", "") in clause.replace(" ", "")
            or clause.replace(" ", "") == spec_attendue.replace(" ", "")
        )

    syntaxe_ok = a_theorem and a_tactique and equilibre and not a_lean3
    valide = syntaxe_ok and coherent and (math_verifie is not False)
    if "=" in clause and math_verifie is None:
        valide = False

    return {
        "statut": "OK" if valide else "ECHEC_AUDIT",
        "mode": "auditer_lean4",
        "syntaxe_lean4_moderne": syntaxe_ok,
        "syntaxe_lean3_obsolete": a_lean3,
        "delimiters_equilibres": equilibre,
        "clause_extraite": clause,
        "proposition_verifiee_sympy": math_verifie,
        "detail_verification": detail_math,
        "coherent_avec_cible": coherent,
        "compilateur_lean_binaire": bool(shutil.which("lean")),
        "valide_kernel": valide,
        "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
    }


def generer_lean4_couple(expression: str, utiliser_57m: bool = True) -> Dict[str, Any]:
    """Calcule d'abord le résultat exact, puis sollicite le 57.1M et audite son théorème Lean 4."""
    t0 = time.perf_counter()
    res_kernel = calculer_exact(expression=expression, mode="auto")
    proposition_cible = expression.strip()
    prompt_lean = f"Christian: Prouver en Lean 4 que {proposition_cible} [ALIX] "

    # Si l'entrée était une expression sans '=', on construit la proposition "expr = resultat"
    norm = normaliser_expression(expression)
    if "=" not in norm and "<=" not in norm and ">=" not in norm and res_kernel.get("statut") == "OK":
        val = res_kernel.get("valeur_exacte") or res_kernel.get("resultat", "")
        if val:
            expr_lean = re.sub(r"\bmodulo\b|\bmod\b", "%", expression.strip(), flags=re.IGNORECASE)
            proposition_cible = f"{expr_lean} = {val}"
            prompt_lean = f"Christian: Prouver en Lean 4 que {proposition_cible} [ALIX] "

    sortie_57m = ""
    audit = None
    if utiliser_57m:
        import torch
        model, tok = _charger_57m_paresseux()
        toks = tok.encode(prompt_lean, add_bos=True, add_eos=False)
        x = torch.tensor([toks], dtype=torch.long)
        with torch.no_grad():
            for _ in range(110):
                if x.shape[1] >= model.cfg.max_seq_len:
                    break
                logits = model(x)
                nxt = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
                if nxt.item() == tok.eos_id:
                    break
                x = torch.cat([x, nxt], dim=1)
        sortie_57m = tok.decode(x[0].tolist())[len(prompt_lean):].strip()
        spec = proposition_cible if "=" in proposition_cible else ""
        audit = auditer_lean4(sortie_57m, spec_attendue=spec)

    valide_57m = bool(audit and audit["valide_kernel"])
    return {
        "statut": "OK",
        "mode": "generer_lean4",
        "kernel_verite": res_kernel,
        "proposition_cible": proposition_cible,
        "sortie_57m": sortie_57m,
        "audit_lean4": audit,
        "source_retenue": "57M_VALIDE_PAR_KERNEL" if valide_57m else "KERNEL_SEUL (57M rejeté par l'auditeur)",
        "duree_ms": round((time.perf_counter() - t0) * 1000, 3),
    }


# =============================================================================
# 6. ROUTEUR GÉNÉRAL SANS RÈGLES CODÉES EN DUR (`calculer_exact`)
# =============================================================================

_UNITE_MULTI_RE = re.compile(
    r"-?\d+(?:[.,]\d+)?\s*(?:ko|mo|go|to|kio|mio|gio|tio|kb|mb|gb|kbit|mbit|gbit|bit|bits|octet|octets|ms|sec|min|mw|kw|mj|kj|watt|watts|joule|joules|hz|khz|mhz|ghz|hertz|kg|mg|km|cm|mm|volt|volts|ohm|ohms|kelvin)\b",
    re.IGNORECASE,
)
_UNITE_COURTE_RE = re.compile(
    r"-?\d+(?:[.,]\d+)?\s+(?:o|s|h|w|j|m|g|a|v|k)\b",
    re.IGNORECASE,
)


def _contient_grandeurs_physiques(txt: str) -> bool:
    if _UNITE_MULTI_RE.search(txt):
        return True
    # Les unités d'une seule lettre ne déclenchent l'auto-détection que hors équation algébrique
    if "=" not in txt and "<=" not in txt and ">=" not in txt and "^" not in txt and "²" not in txt:
        return bool(_UNITE_COURTE_RE.search(txt))
    return False


def calculer_exact(
    expression: str = "",
    mode: str = "auto",
    action: str = "auto",
    variable: str = "",
    vers_unite: str = "",
    premisses: Optional[List[str]] = None,
    conclusion: str = "",
    utiliser_57m: bool = False,
) -> Dict[str, Any]:
    """Point d'entrée unifié du Kernel mathématique / dimensionnel / logique / Lean 4."""
    if mode == "logique" or premisses is not None or conclusion:
        return verifier_logique_propositionnelle(premisses=premisses, conclusion=conclusion, formule=expression)

    if not expression or not expression.strip():
        raise ValueError("Le paramètre 'expression' est requis.")

    if mode == "auditer_lean4":
        return auditer_lean4(expression)
    if mode == "generer_lean4":
        return generer_lean4_couple(expression, utiliser_57m=utiliser_57m)
    if mode == "arithmetique":
        return evaluer_arithmetique_ast(expression)
    if mode == "sympy":
        return resoudre_sympy(expression, action=action, variable=variable)
    if mode == "dimensionnel":
        return analyser_dimensionnel(expression, vers_unite=vers_unite)

    # Routage automatique générique
    txt = expression.strip()
    if re.search(r"^\s*(?:theorem|lemma|example)\b", txt) or ":=" in txt:
        return auditer_lean4(txt)
    if "->" in txt or "<->" in txt or "→" in txt or "∧" in txt or "∨" in txt or "¬" in txt:
        return verifier_logique_propositionnelle(formule=txt)
    if _contient_grandeurs_physiques(txt) or vers_unite:
        return analyser_dimensionnel(txt, vers_unite=vers_unite)

    norm = normaliser_expression(txt)
    # Si purement numérique (chiffres, opérateurs, parenthèses, pas de lettres hors 'mod') -> AST Fraction
    if not re.search(r"[A-Za-z_]", norm):
        return evaluer_arithmetique_ast(txt)

    return resoudre_sympy(txt, action=action, variable=variable)
