"""
OMNI AGENT — Outil Terminal v0.2
Exécution shell avec confirmation pour commandes dangereuses.
"""

import asyncio
from typing import Any, Callable, Awaitable
from tools.base import Tool


class TerminalTool(Tool):
    
    def __init__(self, confirm_patterns: list[str] | None = None,
                 blocked_patterns: list[str] | None = None,
                 confirm_fn: Callable[[str], Awaitable[bool]] | None = None):
        """
        confirm_patterns: commandes nécessitant confirmation
        blocked_patterns: commandes bloquées inconditionnellement
        confirm_fn: async function qui demande confirmation à l'utilisateur
        """
        self._confirm_patterns = confirm_patterns or []
        self._blocked_patterns = blocked_patterns or [
            ":(){:|:&};:", "rm -rf /", "rm -rf /*", "mkfs /dev/sda"
        ]
        self._confirm_fn = confirm_fn
    
    @property
    def name(self) -> str:
        return "terminal"
    
    @property
    def description(self) -> str:
        return "Exécute une commande shell et retourne stdout/stderr. Timeout 30s par défaut."
    
    @property
    def parameters(self) -> dict:
        return {
            "command": {"type": "string", "description": "Commande shell à exécuter"},
            "timeout": {"type": "integer", "description": "Timeout en secondes", "default": 30},
            "cwd": {"type": "string", "description": "Répertoire de travail", "default": None},
        }
    
    def _check_safety(self, command: str) -> tuple[str, str | None]:
        """
        Retourne (status, message).
        status: "ok" | "confirm" | "blocked"
        """
        cmd_lower = command.lower().strip()
        
        # Bloqué inconditionnellement
        for pattern in self._blocked_patterns:
            if pattern.lower() in cmd_lower:
                return "blocked", f"Commande bloquée — pattern interdit: {pattern}"
        
        # Nécessite confirmation
        for pattern in self._confirm_patterns:
            if pattern.lower() in cmd_lower:
                return "confirm", f"⚠ Commande potentiellement dangereuse ({pattern}): {command}"
        
        return "ok", None
    
    async def execute(self, command: str = "", timeout: int = 30, 
                      cwd: str | None = None, **kwargs) -> Any:
        if not command:
            return {"error": "Commande vide"}
        
        # Vérification de sécurité
        status, message = self._check_safety(command)
        
        if status == "blocked":
            return {"error": message, "blocked": True}
        
        if status == "confirm":
            if self._confirm_fn:
                confirmed = await self._confirm_fn(message)
                if not confirmed:
                    return {"error": "Commande annulée par l'utilisateur", "cancelled": True}
            else:
                # Pas de callback de confirmation → bloquer par précaution
                return {"error": f"Confirmation requise mais pas de callback: {message}", "needs_confirm": True}
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            return {
                "returncode": proc.returncode,
                "stdout": stdout_str[:10000],
                "stderr": stderr_str[:5000],
                "truncated": len(stdout_str) > 10000 or len(stderr_str) > 5000,
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return {"error": f"Timeout après {timeout}s", "returncode": -1}
        except Exception as e:
            return {"error": str(e), "returncode": -1}
