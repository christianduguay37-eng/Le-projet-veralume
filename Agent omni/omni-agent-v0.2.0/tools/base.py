"""
OMNI AGENT — Outils
Interface standard pour tous les outils. Chaque outil = une capacité que STRIC_e peut invoquer.
"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Interface de base pour tout outil."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        ...
    
    @property
    @abstractmethod
    def parameters(self) -> dict:
        """Schéma des paramètres (pour le substrat)."""
        ...
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        ...
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Registre central des outils disponibles."""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)
    
    def list_tools(self) -> list[dict]:
        return [t.to_dict() for t in self._tools.values()]
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
