#!/usr/bin/env python3
"""
OMNI AGENT — Serveur Web
Interface web avec WebSocket pour chat + événements STRIC en temps réel.

Usage: python web_server.py [--port 8888] [--config path/to/config.json]
Prérequis: pip install aiohttp
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import aiohttp
    from aiohttp import web
except ImportError:
    print("❌ aiohttp requis. Installe-le avec:")
    print("   pip install aiohttp")
    sys.exit(1)

from config import Config
from core.agent import OmniAgent
from core.stric import STRICEvent


class WebInterface:
    """Serveur web + WebSocket pour l'agent Omni."""
    
    def __init__(self, config: Config, port: int = 8888):
        self.config = config
        self.port = port
        self.agent: OmniAgent | None = None
        self.ws_clients: list[web.WebSocketResponse] = []
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        self.app.router.add_get("/", self._serve_ui)
        self.app.router.add_get("/ws", self._websocket_handler)
        self.app.router.add_get("/api/status", self._api_status)
        self.app.router.add_get("/api/health", self._api_health)
        self.app.router.add_get("/api/memory", self._api_memory)
        self.app.router.add_get("/api/learnings", self._api_learnings)
        self.app.router.add_post("/api/compact", self._api_compact)
    
    async def _init_agent(self):
        """Initialiser l'agent avec les callbacks WebSocket."""
        self.agent = OmniAgent(
            config=self.config,
            on_event=self._broadcast_event,
            on_confirm=self._ws_confirm,
        )
    
    async def _broadcast_event(self, event: STRICEvent):
        """Envoyer un événement STRIC à tous les clients WebSocket."""
        msg = json.dumps({
            "type": "stric_event",
            "event": event.type,
            "data": event.data,
            "timestamp": event.timestamp,
        }, ensure_ascii=False, default=str)
        
        dead = []
        for ws in self.ws_clients:
            try:
                await ws.send_str(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.ws_clients.remove(ws)
    
    async def _ws_confirm(self, message: str) -> bool:
        """Demander confirmation via WebSocket (premier client)."""
        if not self.ws_clients:
            return False
        
        ws = self.ws_clients[0]
        try:
            await ws.send_str(json.dumps({
                "type": "confirm_request",
                "message": message,
            }))
            # Attendre la réponse (timeout 30s)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("type") == "confirm_response":
                        return data.get("confirmed", False)
                break
        except Exception:
            pass
        return False
    
    async def _serve_ui(self, request: web.Request) -> web.Response:
        """Servir l'interface HTML."""
        html_path = Path(__file__).parent / "ui.html"
        if html_path.exists():
            return web.Response(
                text=html_path.read_text(encoding="utf-8"),
                content_type="text/html"
            )
        return web.Response(text="ui.html non trouvé", status=404)
    
    async def _websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handler WebSocket principal — chat + événements."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.append(ws)
        
        # Envoyer le status initial
        if self.agent:
            status = await self.agent.status()
            await ws.send_str(json.dumps({
                "type": "status",
                "data": status,
            }, default=str))
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_ws_message(ws, data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            if ws in self.ws_clients:
                self.ws_clients.remove(ws)
        
        return ws
    
    async def _handle_ws_message(self, ws: web.WebSocketResponse, data: dict):
        """Traiter un message WebSocket du client."""
        msg_type = data.get("type", "")
        
        if msg_type == "chat":
            user_input = data.get("content", "").strip()
            if not user_input or not self.agent:
                return
            
            # Signaler le début du traitement
            await ws.send_str(json.dumps({"type": "processing_start"}))
            
            try:
                response = await self.agent.process(user_input)
                
                # Envoyer la réponse
                await ws.send_str(json.dumps({
                    "type": "chat_response",
                    "content": response,
                    "trace_available": self.agent.last_trace is not None,
                }, ensure_ascii=False))
                
            except Exception as e:
                await ws.send_str(json.dumps({
                    "type": "error",
                    "content": str(e),
                }))
            
            # Envoyer le status mis à jour
            status = await self.agent.status()
            await ws.send_str(json.dumps({
                "type": "status",
                "data": status,
            }, default=str))
        
        elif msg_type == "get_trace":
            if self.agent and self.agent.last_trace:
                await ws.send_str(json.dumps({
                    "type": "trace",
                    "data": self.agent.last_trace.to_dict(),
                }, default=str))
        
        elif msg_type == "get_status":
            if self.agent:
                status = await self.agent.status()
                await ws.send_str(json.dumps({
                    "type": "status",
                    "data": status,
                }, default=str))
        
        elif msg_type == "search_memory":
            query = data.get("query", "")
            if self.agent and query:
                results = self.agent.memory.search(query)
                await ws.send_str(json.dumps({
                    "type": "search_results",
                    "data": [e.to_dict() for e in results[:10]],
                }, default=str))
    
    # ─── API REST (pour monitoring externe) ─────
    
    async def _api_status(self, request: web.Request) -> web.Response:
        if not self.agent:
            return web.json_response({"error": "agent not initialized"}, status=503)
        status = await self.agent.status()
        return web.json_response(status, dumps=lambda x: json.dumps(x, default=str))
    
    async def _api_health(self, request: web.Request) -> web.Response:
        if not self.agent:
            return web.json_response({"error": "agent not initialized"}, status=503)
        health = await self.agent.router.health_report()
        return web.json_response(health, dumps=lambda x: json.dumps(x, default=str))
    
    async def _api_memory(self, request: web.Request) -> web.Response:
        if not self.agent:
            return web.json_response({"error": "agent not initialized"}, status=503)
        summary = self.agent.memory.get_trajectory_summary()
        return web.json_response(summary)
    
    async def _api_learnings(self, request: web.Request) -> web.Response:
        if not self.agent:
            return web.json_response({"error": "agent not initialized"}, status=503)
        learnings = self.agent.memory.get_learnings(20)
        return web.json_response({"learnings": learnings})
    
    async def _api_compact(self, request: web.Request) -> web.Response:
        if not self.agent:
            return web.json_response({"error": "agent not initialized"}, status=503)
        self.agent.memory.compact_old(7)
        return web.json_response({"status": "compacted"})
    
    async def run(self):
        """Démarrer le serveur."""
        await self._init_agent()
        
        # Vérifier le substrat
        status = await self.agent.status()
        sub_ok = status.get("substrat_available", False)
        sub_name = status.get("substrat_default", "?")
        
        print(f"\n  ╔═══════════════════════════════════════╗")
        print(f"  ║       OMNI AGENT — Interface Web      ║")
        print(f"  ╚═══════════════════════════════════════╝")
        if sub_ok:
            print(f"  ● Substrat: {sub_name}")
        else:
            print(f"  ⚠ Substrat non disponible: {sub_name}")
        print(f"  → http://localhost:{self.port}")
        print()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()
        
        # Garder le serveur en vie
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await runner.cleanup()


async def main():
    # Config
    config_path = Path.home() / ".omni-agent" / "config.json"
    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = Path(sys.argv[idx + 1])
    
    port = 8888
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    
    if config_path.exists():
        config = Config.load(config_path)
    else:
        config = Config.default()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config.save(config_path)
    
    config.verbose = True  # Toujours verbose pour le web
    
    server = WebInterface(config, port)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
