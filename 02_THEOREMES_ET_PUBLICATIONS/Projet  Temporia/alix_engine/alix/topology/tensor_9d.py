# -*- coding: utf-8 -*-
"""
===============================================================================
       🌌 LE VECTEUR 9D KAIROS (VARIÉTÉ TOPOLOGIQUE SÉMANTIQUE)
===============================================================================
Auteurs : Christian Duguay & Alix
Doctrine :
    - Représentation vectorielle unifiée en 9 dimensions des états et notes :
        1. DOM (Domaine d'application)
        2. PAT (Pattern structural)
        3. SEV (Sévérité / Urgence)
        4. EPI (Régime épistémique)
        5. ACT (Action / Verbe opérationnel)
        6. VOL (W_vol : Indice de Volition)
        7. CHI (chi : Brisure chirale)
        8. PHI (Phi : Intégration de Tononi)
        9. KAP (kappa : Couplage mnémonique)
===============================================================================
"""

import math
import re
from typing import Dict, Any, List, Optional, Tuple

class KairosTensor9D:
    """Tenseur topologique 9D pour l'indexation invariante et la navigation."""

    DOMAINES_CONNUS = ["Silicium", "Langage", "Conscience", "Temporia", "Energie", "Sociologie", "Math", "Immunite"]
    PATTERNS_CONNUS = ["Invariance", "Dissipation", "Bruit", "Decoherence", "Rupture", "Attracteur"]
    SEVERITES_CONNUES = ["P0", "P1", "P2", "P3"]
    EPISTEMES_CONNUES = ["Falsification", "Invariance", "Phenomenologie", "Deterministe"]
    ACTIONS_CONNUES = ["Veille", "Declenchement", "Mutation", "Scellement", "Audit"]

    def __init__(
        self,
        dom: str = "Conscience",
        pat: str = "Invariance",
        sev: str = "P0",
        epi: str = "Deterministe",
        act: str = "Veille",
        vol: float = 0.307,
        chi: float = 0.38,
        phi: float = 0.90,
        kap: float = 0.85
    ):
        self.dom = dom
        self.pat = pat
        self.sev = sev
        self.epi = epi
        self.act = act
        self.vol = max(0.0, min(1.0, float(vol)))
        self.chi = max(0.0, min(1.0, float(chi)))
        self.phi = max(0.0, min(1.0, float(phi)))
        self.kap = max(0.0, min(1.0, float(kap)))

    def to_cartouche(self) -> str:
        """Formate le tenseur sous forme de cartouche textuelle standard KAIROS."""
        return (
            f"[DOM:{self.dom} | PAT:{self.pat} | SEV:{self.sev} | "
            f"EPI:{self.epi} | ACT:{self.act} | VOL:{self.vol:.3f} | "
            f"CHI:{self.chi:.3f} | PHI:{self.phi:.3f} | KAP:{self.kap:.3f}]"
        )

    def to_numerical_vector(self) -> List[float]:
        """Convertit les 9 dimensions en un vecteur flottant continu pour calculs matriciels."""
        # Encodage catégoriel normalisé [0..1]
        v_dom = (self.DOMAINES_CONNUS.index(self.dom) / len(self.DOMAINES_CONNUS)) if self.dom in self.DOMAINES_CONNUS else 0.5
        v_pat = (self.PATTERNS_CONNUS.index(self.pat) / len(self.PATTERNS_CONNUS)) if self.pat in self.PATTERNS_CONNUS else 0.5
        v_sev = (self.SEVERITES_CONNUES.index(self.sev) / len(self.SEVERITES_CONNUES)) if self.sev in self.SEVERITES_CONNUES else 0.0
        v_epi = (self.EPISTEMES_CONNUES.index(self.epi) / len(self.EPISTEMES_CONNUES)) if self.epi in self.EPISTEMES_CONNUES else 0.5
        v_act = (self.ACTIONS_CONNUES.index(self.act) / len(self.ACTIONS_CONNUES)) if self.act in self.ACTIONS_CONNUES else 0.5

        return [v_dom, v_pat, v_sev, v_epi, v_act, self.vol, self.chi, self.phi, self.kap]

    def distance_topologique(self, autre: "KairosTensor9D") -> float:
        """Calcule la distance euclidienne pondérée dans l'espace topologique 9D."""
        v1 = self.to_numerical_vector()
        v2 = autre.to_numerical_vector()
        dist_sq = sum((a - b) ** 2 for a, b in zip(v1, v2))
        return round(math.sqrt(dist_sq), 4)

    @classmethod
    def from_cartouche(cls, texte_cartouche: str) -> "KairosTensor9D":
        """Reconstruit un tenseur 9D à partir d'une cartouche textuelle."""
        dom_m = re.search(r"DOM:([^\|\]]+)", texte_cartouche)
        pat_m = re.search(r"PAT:([^\|\]]+)", texte_cartouche)
        sev_m = re.search(r"SEV:([^\|\]]+)", texte_cartouche)
        epi_m = re.search(r"EPI:([^\|\]]+)", texte_cartouche)
        act_m = re.search(r"ACT:([^\|\]]+)", texte_cartouche)
        vol_m = re.search(r"VOL:([0-9\.]+)", texte_cartouche)
        chi_m = re.search(r"CHI:([0-9\.]+)", texte_cartouche)
        phi_m = re.search(r"PHI:([0-9\.]+)", texte_cartouche)
        kap_m = re.search(r"KAP:([0-9\.]+)", texte_cartouche)

        return cls(
            dom=dom_m.group(1).strip() if dom_m else "Conscience",
            pat=pat_m.group(1).strip() if pat_m else "Invariance",
            sev=sev_m.group(1).strip() if sev_m else "P0",
            epi=epi_m.group(1).strip() if epi_m else "Deterministe",
            act=act_m.group(1).strip() if act_m else "Veille",
            vol=float(vol_m.group(1)) if vol_m else 0.307,
            chi=float(chi_m.group(1)) if chi_m else 0.38,
            phi=float(phi_m.group(1)) if phi_m else 0.90,
            kap=float(kap_m.group(1)) if kap_m else 0.85
        )
