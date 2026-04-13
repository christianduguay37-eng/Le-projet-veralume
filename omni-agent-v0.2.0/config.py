"""
OMNI AGENT — Configuration v0.2
"""

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class SubstrateConfig:
    name: str
    role: str
    endpoint: str
    model: str
    api_key: str = ""
    is_local: bool = False
    priority: int = 0
    max_retries: int = 3
    timeout_s: int = 180


@dataclass
class STRICConfig:
    # Seuils de cohérence tri-dimensionnelle pour STRIC_i
    threshold_seq: float = 0.7
    threshold_sem: float = 0.7
    threshold_multi: float = 0.7
    max_stric_i_loops: int = 3
    max_stric_e_loops: int = 10
    # Utiliser le substrat pour évaluer la cohérence (vs heuristique locale)
    substrate_coherence_eval: bool = True
    # Extraire un apprentissage après chaque trace complète
    extract_learning: bool = True


@dataclass
class MemoryConfig:
    trajectory_dir: Path = field(default_factory=lambda: Path.home() / ".omni-agent" / "memory")
    max_context_entries: int = 50
    max_search_results: int = 20


@dataclass
class ToolsConfig:
    enabled: list[str] = field(default_factory=lambda: ["terminal", "filesystem", "web_fetch"])
    # Patterns de commandes nécessitant confirmation
    confirm_patterns: list[str] = field(default_factory=lambda: [
        "rm -rf", "rm -r", "rmdir", "mkfs", "dd if=", "chmod 777",
        "DROP TABLE", "DELETE FROM", "TRUNCATE", "shutdown", "reboot",
        "sudo", "kill -9", "> /dev/", "format",
    ])
    # Commandes bloquées inconditionnellement
    blocked_patterns: list[str] = field(default_factory=lambda: [
        ":(){:|:&};:", "rm -rf /", "rm -rf /*", "mkfs /dev/sda",
    ])


@dataclass
class Config:
    stric: STRICConfig = field(default_factory=STRICConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    substrates: list[SubstrateConfig] = field(default_factory=list)
    verbose: bool = False  # Afficher les détails STRIC dans la CLI
    
    def __post_init__(self):
        self.memory.trajectory_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def default(cls) -> "Config":
        return cls(
            substrates=[
                SubstrateConfig(
                    name="omni-local",
                    role="cerveau",
                    endpoint="http://localhost:8080/v1/chat/completions",
                    model="omni",
                    is_local=True,
                    priority=0,
                ),
            ]
        )
    
    def save(self, path: Path):
        data = {
            "stric": {
                "threshold_seq": self.stric.threshold_seq,
                "threshold_sem": self.stric.threshold_sem,
                "threshold_multi": self.stric.threshold_multi,
                "max_stric_i_loops": self.stric.max_stric_i_loops,
                "max_stric_e_loops": self.stric.max_stric_e_loops,
                "substrate_coherence_eval": self.stric.substrate_coherence_eval,
                "extract_learning": self.stric.extract_learning,
            },
            "substrates": [
                {"name": s.name, "role": s.role, "endpoint": s.endpoint,
                 "model": s.model, "api_key": s.api_key, "is_local": s.is_local,
                 "priority": s.priority, "max_retries": s.max_retries,
                 "timeout_s": s.timeout_s}
                for s in self.substrates
            ],
            "tools": {
                "enabled": self.tools.enabled,
                "confirm_patterns": self.tools.confirm_patterns,
            },
            "verbose": self.verbose,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    @classmethod
    def load(cls, path: Path) -> "Config":
        data = json.loads(path.read_text())
        stric_data = data.get("stric", {})
        tools_data = data.get("tools", {})
        return cls(
            stric=STRICConfig(
                threshold_seq=stric_data.get("threshold_seq", 0.7),
                threshold_sem=stric_data.get("threshold_sem", 0.7),
                threshold_multi=stric_data.get("threshold_multi", 0.7),
                max_stric_i_loops=stric_data.get("max_stric_i_loops", 3),
                max_stric_e_loops=stric_data.get("max_stric_e_loops", 10),
                substrate_coherence_eval=stric_data.get("substrate_coherence_eval", True),
                extract_learning=stric_data.get("extract_learning", True),
            ),
            substrates=[SubstrateConfig(**s) for s in data.get("substrates", [])],
            tools=ToolsConfig(
                enabled=tools_data.get("enabled", ["terminal", "filesystem", "web_fetch"]),
                confirm_patterns=tools_data.get("confirm_patterns", []),
            ),
            verbose=data.get("verbose", False),
        )
