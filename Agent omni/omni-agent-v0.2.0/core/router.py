"""
OMNI AGENT — Routeur Multi-Substrat v0.2
Health-aware routing avec fallback chain.
"""

from substrates.base import Substrate


ROLE_KEYWORDS = {
    "cerveau":       ["default", "general", "plan", "analyse", "résume"],
    "systemise":     ["architecture", "système", "structure", "formalise", "taxonomie", "ontologie"],
    "synthetise":    ["synthèse", "combine", "résume", "vue d'ensemble", "merge", "compare"],
    "operationalise":["implémente", "code", "exécute", "opérationnel", "build", "deploy"],
    "structure":     ["organise", "format", "template", "schéma", "clean", "restructure"],
    "challenge":     ["critique", "teste", "adversarial", "devil's advocate", "red team", "vérifie"],
}


class SubstrateRouter:
    """
    Routeur v0.2: health-aware avec fallback.
    
    Si le substrat optimal est dégradé, tombe sur le suivant.
    Le cerveau local reste toujours le dernier fallback.
    """
    
    def __init__(self):
        self._substrates: dict[str, Substrate] = {}
        self._default: Substrate | None = None
    
    def register(self, substrate: Substrate, is_default: bool = False):
        self._substrates[substrate.name] = substrate
        if is_default:
            self._default = substrate
    
    def get_default(self) -> Substrate | None:
        return self._default
    
    async def route(self, task_description: str, preferred_role: str | None = None) -> Substrate:
        # Rôle explicite
        if preferred_role:
            for s in self._substrates.values():
                if s.role == preferred_role and await s.is_available() and not s.health.is_degraded:
                    return s
        
        # Scoring par mots-clés + santé
        task_lower = task_description.lower()
        candidates = []
        
        for substrate in self._substrates.values():
            if substrate == self._default:
                continue
            if not await substrate.is_available():
                continue
            if substrate.health.is_degraded:
                continue
            
            keywords = ROLE_KEYWORDS.get(substrate.role, [])
            score = sum(1 for kw in keywords if kw in task_lower)
            
            # Bonus pour faible latence, pénalité pour erreurs
            if score > 0:
                health_bonus = -substrate.health.error_rate * 0.5
                candidates.append((score + health_bonus, substrate))
        
        if candidates:
            candidates.sort(key=lambda x: -x[0])
            if candidates[0][0] > 0:
                return candidates[0][1]
        
        # Fallback: cerveau local
        return self._default
    
    def list_substrates(self) -> list[dict]:
        return [
            {
                "name": s.name, 
                "role": s.role,
                "health": s.health.to_dict(),
            }
            for s in self._substrates.values()
        ]
    
    async def health_report(self) -> dict:
        """Rapport de santé de tous les substrats."""
        report = {}
        for name, s in self._substrates.items():
            available = await s.is_available()
            report[name] = {
                "role": s.role,
                "available": available,
                **s.health.to_dict(),
            }
        return report
