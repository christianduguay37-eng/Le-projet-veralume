"""
OMNI AGENT — Substrats v0.2
Retry avec backoff exponentiel, health tracking, streaming SSE.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from dataclasses import dataclass, field
import json
import urllib.request
import urllib.error
import asyncio
import time


@dataclass
class SubstrateHealth:
    """Tracking santé d'un substrat."""
    total_calls: int = 0
    total_errors: int = 0
    total_tokens_approx: int = 0
    avg_latency_ms: float = 0.0
    last_error: str | None = None
    last_call_at: float = 0.0
    consecutive_errors: int = 0
    
    def record_success(self, latency_ms: float, tokens_approx: int = 0):
        self.total_calls += 1
        self.total_tokens_approx += tokens_approx
        self.consecutive_errors = 0
        self.last_call_at = time.time()
        if self.avg_latency_ms == 0:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = self.avg_latency_ms * 0.8 + latency_ms * 0.2
    
    def record_error(self, error: str):
        self.total_calls += 1
        self.total_errors += 1
        self.consecutive_errors += 1
        self.last_error = error
        self.last_call_at = time.time()
    
    @property
    def error_rate(self) -> float:
        return self.total_errors / max(self.total_calls, 1)
    
    @property
    def is_degraded(self) -> bool:
        return self.consecutive_errors >= 3 or (self.total_calls > 5 and self.error_rate > 0.5)
    
    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "error_rate": round(self.error_rate, 3),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "consecutive_errors": self.consecutive_errors,
            "is_degraded": self.is_degraded,
        }


class Substrate(ABC):
    """Interface de base pour tout substrat cognitif."""
    
    def __init__(self):
        self.health = SubstrateHealth()
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def role(self) -> str: ...
    
    @abstractmethod
    async def _raw_complete(self, messages: list[dict], system: str = "") -> str:
        """Appel brut au substrat — sans retry."""
        ...
    
    @abstractmethod
    async def is_available(self) -> bool: ...
    
    async def complete(self, messages: list[dict], system: str = "",
                       max_retries: int = 3, base_delay: float = 1.0) -> str:
        """Appel au substrat avec retry et backoff exponentiel."""
        last_error = None
        
        for attempt in range(max_retries):
            t0 = time.time()
            try:
                result = await self._raw_complete(messages, system)
                latency = (time.time() - t0) * 1000
                self.health.record_success(latency, len(result) // 4)
                return result
                
            except Exception as e:
                last_error = str(e)
                self.health.record_error(last_error)
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        return f"[ERREUR SUBSTRAT {self.name}] {max_retries} tentatives échouées. Dernière: {last_error}"


def _build_messages(messages: list[dict], system: str) -> list[dict]:
    all_msgs = []
    if system:
        all_msgs.append({"role": "system", "content": system})
    all_msgs.extend(messages)
    return all_msgs


class LocalSubstrate(Substrate):
    """Substrat local via llama-server (API OpenAI-compatible)."""
    
    def __init__(self, name: str, role: str, endpoint: str, model: str, 
                 timeout: int = 180):
        super().__init__()
        self._name = name
        self._role = role
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def role(self) -> str:
        return self._role
    
    async def _raw_complete(self, messages: list[dict], system: str = "") -> str:
        all_messages = _build_messages(messages, system)
        
        payload = json.dumps({
            "model": self.model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": False,
        }).encode("utf-8")
        
        def _call():
            req = urllib.request.Request(
                self.endpoint, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        
        return await asyncio.get_event_loop().run_in_executor(None, _call)
    
    async def stream(self, messages: list[dict], system: str = "") -> AsyncIterator[str]:
        """Streaming SSE depuis llama-server."""
        all_messages = _build_messages(messages, system)
        
        payload = json.dumps({
            "model": self.model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": True,
        }).encode("utf-8")
        
        def _stream():
            req = urllib.request.Request(
                self.endpoint, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            chunks = []
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                buffer = ""
                for raw_chunk in iter(lambda: resp.read(256), b""):
                    buffer += raw_chunk.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    chunks.append(content)
                            except json.JSONDecodeError:
                                pass
            return chunks
        
        chunks = await asyncio.get_event_loop().run_in_executor(None, _stream)
        for c in chunks:
            yield c
    
    async def is_available(self) -> bool:
        def _ping():
            try:
                base = self.endpoint.rsplit("/v1/", 1)[0]
                for suffix in ["/v1/models", "/health", "/"]:
                    try:
                        req = urllib.request.Request(base + suffix, method="GET")
                        with urllib.request.urlopen(req, timeout=5):
                            return True
                    except urllib.error.HTTPError as e:
                        if e.code < 500:
                            return True
                return False
            except Exception:
                return False
        return await asyncio.get_event_loop().run_in_executor(None, _ping)


class RemoteSubstrate(Substrate):
    """Substrat distant via API (OpenAI-compatible)."""
    
    def __init__(self, name: str, role: str, endpoint: str, model: str, 
                 api_key: str, timeout: int = 120):
        super().__init__()
        self._name = name
        self._role = role
        self.endpoint = endpoint
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def role(self) -> str:
        return self._role
    
    async def _raw_complete(self, messages: list[dict], system: str = "") -> str:
        all_messages = _build_messages(messages, system)
        
        payload = json.dumps({
            "model": self.model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }).encode("utf-8")
        
        def _call():
            req = urllib.request.Request(
                self.endpoint, data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                }, method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        
        return await asyncio.get_event_loop().run_in_executor(None, _call)
    
    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        if self.health.is_degraded:
            return False
        return True
