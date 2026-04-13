"""
OMNI AGENT — Mémoire Trajectoire v0.2

Ajouts:
- Recherche par contenu texte
- Compaction des vieux fichiers
- Meilleure injection de contexte pour STRIC
- Séparation learnings / interactions / traces
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    timestamp: float
    entry_type: str          # "interaction", "stric_trace", "learning", "system"
    content: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "type": self.entry_type,
            "content": self.content,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "MemoryEntry":
        return cls(
            timestamp=d["timestamp"],
            entry_type=d["type"],
            content=d["content"],
            tags=d.get("tags", []),
        )
    
    def text_content(self) -> str:
        """Extraire le texte cherchable de l'entrée."""
        parts = []
        for key in ("content", "objective", "insight", "summary", "understanding"):
            val = self.content.get(key)
            if isinstance(val, str):
                parts.append(val)
        # Tags aussi
        parts.extend(self.tags)
        return " ".join(parts).lower()


class TrajectoryMemory:
    """
    Mémoire trajectoire persistante v0.2
    
    Améliorations:
    - search(): recherche plein texte dans le cache
    - get_learnings(): récupérer uniquement les apprentissages
    - Contexte STRIC enrichi: sépare interactions, learnings, et résumé trajectoire
    """
    
    def __init__(self, base_dir: Path, max_context: int = 50):
        self.base_dir = base_dir
        self.max_context = max_context
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: list[MemoryEntry] = []
        self._load_recent()
    
    def _today_file(self) -> Path:
        return self.base_dir / f"{time.strftime('%Y-%m-%d')}.jsonl"
    
    def _load_recent(self):
        self._cache = []
        files = sorted(self.base_dir.glob("*.jsonl"), reverse=True)
        
        for f in files[:14]:  # 2 semaines max
            try:
                lines = f.read_text(encoding="utf-8").strip().split("\n")
                for line in lines:
                    if line.strip():
                        try:
                            entry = MemoryEntry.from_dict(json.loads(line))
                            self._cache.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
            except Exception:
                continue
            
            if len(self._cache) >= self.max_context * 3:
                break
        
        self._cache.sort(key=lambda e: e.timestamp, reverse=True)
    
    def append(self, entry_type: str, content: dict, tags: list[str] | None = None):
        entry = MemoryEntry(
            timestamp=time.time(),
            entry_type=entry_type,
            content=content,
            tags=tags or [],
        )
        
        with open(self._today_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        
        self._cache.insert(0, entry)
        if len(self._cache) > self.max_context * 4:
            self._cache = self._cache[:self.max_context * 3]
    
    def get_recent(self, n: int | None = None, entry_type: str | None = None) -> list[MemoryEntry]:
        n = n or self.max_context
        entries = self._cache
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        return entries[:n]
    
    def get_learnings(self, n: int = 20) -> list[str]:
        """Récupérer les insights extraites des traces."""
        entries = self.get_recent(n, "learning")
        return [e.content.get("insight", "") for e in entries if e.content.get("insight")]
    
    def search(self, query: str, limit: int = 20) -> list[MemoryEntry]:
        """Recherche plein texte dans le cache."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored = []
        for entry in self._cache:
            text = entry.text_content()
            if not text:
                continue
            # Score = nombre de mots-clés trouvés
            score = sum(1 for w in query_words if w in text)
            if score > 0:
                scored.append((score, entry))
        
        scored.sort(key=lambda x: (-x[0], -x[1].timestamp))
        return [e for _, e in scored[:limit]]
    
    def search_by_tags(self, tags: list[str], limit: int = 20) -> list[MemoryEntry]:
        tag_set = set(t.lower() for t in tags)
        results = [e for e in self._cache if tag_set & set(t.lower() for t in e.tags)]
        return results[:limit]
    
    def get_context_for_stric(self) -> list[dict]:
        """
        Contexte enrichi pour STRIC_i:
        - Dernières interactions (conversation)
        - Apprentissages récents (pattern matching)
        - Résumé trajectoire
        """
        context = []
        
        # Dernières interactions (conversation courante)
        interactions = self.get_recent(15, "interaction")
        for entry in reversed(interactions):
            context.append({
                "role": entry.content.get("role", "?"),
                "content": str(entry.content.get("content", ""))[:300],
            })
        
        # Apprentissages récents — injectés comme "mémoire de travail"
        learnings = self.get_learnings(5)
        if learnings:
            context.append({
                "role": "memory",
                "content": "Apprentissages récents: " + " | ".join(learnings),
            })
        
        return context
    
    def get_trajectory_summary(self) -> dict:
        total = len(self._cache)
        by_type: dict[str, int] = {}
        for e in self._cache:
            by_type[e.entry_type] = by_type.get(e.entry_type, 0) + 1
        
        span_hours = 0.0
        if total > 1:
            span_hours = (self._cache[0].timestamp - self._cache[-1].timestamp) / 3600
        
        n_learnings = by_type.get("learning", 0)
        n_files = len(list(self.base_dir.glob("*.jsonl")))
        
        return {
            "total_entries": total,
            "by_type": by_type,
            "span_hours": span_hours,
            "files": n_files,
            "learnings": n_learnings,
        }
    
    def compact_old(self, days_to_keep: int = 7):
        """
        Compacter les fichiers plus vieux que N jours.
        Garde seulement les learnings et les résumés de traces.
        """
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        
        for f in self.base_dir.glob("*.jsonl"):
            if f.stem < cutoff_str:
                compacted = []
                try:
                    for line in f.read_text(encoding="utf-8").strip().split("\n"):
                        if not line.strip():
                            continue
                        entry = json.loads(line)
                        # Garder learnings et traces (sans le détail)
                        if entry["type"] == "learning":
                            compacted.append(line)
                        elif entry["type"] == "stric_trace":
                            # Garder seulement objective + decision + duration
                            mini = {
                                "timestamp": entry["timestamp"],
                                "type": "stric_trace_summary",
                                "content": {
                                    "objective": entry["content"].get("objective", "")[:200],
                                    "final_decision": entry["content"].get("final_decision"),
                                    "duration_ms": entry["content"].get("duration_ms"),
                                    "learning": entry["content"].get("learning"),
                                },
                                "tags": entry.get("tags", []),
                            }
                            compacted.append(json.dumps(mini, ensure_ascii=False))
                except Exception:
                    continue
                
                if compacted:
                    f.write_text("\n".join(compacted) + "\n", encoding="utf-8")
                else:
                    f.unlink()
        
        # Recharger le cache
        self._load_recent()
