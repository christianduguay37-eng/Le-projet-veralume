"""
OMNI AGENT — Outil Web
Fetch HTTP basique pour récupérer du contenu web.
"""

import asyncio
import urllib.request
import urllib.error
from typing import Any
from tools.base import Tool


class WebFetchTool(Tool):
    
    @property
    def name(self) -> str:
        return "web_fetch"
    
    @property
    def description(self) -> str:
        return "Récupère le contenu d'une URL (texte/HTML). Pour lire des pages web ou APIs."
    
    @property
    def parameters(self) -> dict:
        return {
            "url": {"type": "string", "description": "URL à récupérer"},
            "timeout": {"type": "integer", "description": "Timeout en secondes", "default": 15},
        }
    
    async def execute(self, url: str = "", timeout: int = 15, **kwargs) -> Any:
        if not url:
            return {"error": "URL requise"}
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        def _fetch():
            req = urllib.request.Request(url, headers={
                "User-Agent": "OmniAgent/1.0"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                body = resp.read(500_000).decode("utf-8", errors="replace")
                return {
                    "status": resp.status,
                    "content_type": content_type,
                    "body": body[:50000],
                    "url": url,
                }
        
        try:
            return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "url": url}
        except urllib.error.URLError as e:
            return {"error": str(e.reason), "url": url}
        except asyncio.TimeoutError:
            return {"error": f"Timeout après {timeout}s", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}
