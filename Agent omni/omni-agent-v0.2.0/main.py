#!/usr/bin/env python3
"""
OMNI AGENT — Interface CLI v0.2

Améliorations:
- Affichage live des phases STRIC
- Confirmation interactive pour commandes dangereuses
- /trace — inspecter la dernière trace STRIC
- /search — chercher dans la mémoire
- /health — santé des substrats
- /compact — compacter la mémoire ancienne
"""

import asyncio
import sys
import json
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.agent import OmniAgent
from core.stric import STRICEvent
from pathlib import Path


# ═══════════════════════════════════════
# Couleurs terminal
# ═══════════════════════════════════════

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    
    # Move cursor
    UP      = "\033[A"
    CLEAR   = "\033[2K"
    
    @staticmethod
    def bar(value: float, width: int = 20) -> str:
        """Mini barre de progression."""
        filled = int(value * width)
        color = C.GREEN if value >= 0.7 else C.YELLOW if value >= 0.4 else C.RED
        return f"{color}{'█' * filled}{'░' * (width - filled)}{C.RESET} {value:.2f}"


BANNER = f"""{C.CYAN}{C.BOLD}
  ╔═══════════════════════════════════════╗
  ║       OMNI AGENT v0.2.0              ║
  ║  Double STRIC · Local · VERALUME     ║
  ╚═══════════════════════════════════════╝
{C.RESET}"""

HELP = f"""
{C.DIM}Commandes:{C.RESET}
  {C.YELLOW}/status{C.RESET}     — État de l'agent
  {C.YELLOW}/health{C.RESET}     — Santé détaillée des substrats
  {C.YELLOW}/memory{C.RESET}     — Résumé trajectoire mémoire
  {C.YELLOW}/search{C.RESET} q   — Chercher dans la mémoire
  {C.YELLOW}/trace{C.RESET}      — Inspecter la dernière trace STRIC
  {C.YELLOW}/learnings{C.RESET}  — Voir les apprentissages récents
  {C.YELLOW}/config{C.RESET}     — Configuration active
  {C.YELLOW}/compact{C.RESET}    — Compacter la mémoire ancienne
  {C.YELLOW}/verbose{C.RESET}    — Toggle affichage détaillé STRIC
  {C.YELLOW}/clear{C.RESET}      — Effacer la conversation
  {C.YELLOW}/help{C.RESET}       — Cette aide
  {C.YELLOW}/quit{C.RESET}       — Quitter

{C.DIM}Tout le reste → objectif traité par Double STRIC.{C.RESET}
"""


# ═══════════════════════════════════════
# Event handler — affichage live STRIC
# ═══════════════════════════════════════

class CLIEventHandler:
    """Affiche les phases STRIC en temps réel dans le terminal."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._last_line_count = 0
        self._t0 = time.time()
    
    def _elapsed(self) -> str:
        return f"{C.DIM}{(time.time() - self._t0)*1000:.0f}ms{C.RESET}"
    
    async def handle(self, event: STRICEvent):
        self._t0 = self._t0 or time.time()
        
        match event.type:
            case "stric_i_start":
                print(f"  {C.CYAN}⟳ STRIC_i{C.RESET} — planification intérieure")
            
            case "stric_i_phase":
                if self.verbose:
                    phase = event.data.get("phase", "?")
                    attempt = event.data.get("attempt", 0)
                    symbols = {"S": "👁 observe", "T": "🧠 structure", "R": "📋 formule", 
                              "I": "⚖ valide", "C": "⚡ décide"}
                    desc = symbols.get(phase, phase)
                    suffix = f" (tentative {attempt+1})" if attempt > 0 else ""
                    print(f"    {C.DIM}{phase}{C.RESET} {desc}{suffix}")
            
            case "stric_i_coherence":
                seq = event.data.get("seq", 0)
                sem = event.data.get("sem", 0)
                multi = event.data.get("multi", 0)
                passes = event.data.get("passes", False)
                icon = f"{C.GREEN}✓{C.RESET}" if passes else f"{C.RED}✗{C.RESET}"
                
                if self.verbose:
                    print(f"    {icon} Cohérence:")
                    print(f"      seq:   {C.bar(seq)}")
                    print(f"      sem:   {C.bar(sem)}")
                    print(f"      multi: {C.bar(multi)}")
                else:
                    print(f"    {icon} Cohérence: seq={seq:.2f} sem={sem:.2f} multi={multi:.2f}")
            
            case "stric_i_decision":
                decision = event.data.get("decision", "?")
                colors = {"act": C.GREEN, "reformulate": C.YELLOW, 
                         "escalate": C.RED, "clarify": C.MAGENTA}
                color = colors.get(decision, C.WHITE)
                symbols = {"act": "→ exécution", "reformulate": "↻ reformulation",
                          "escalate": "⬆ escalade", "clarify": "❓ clarification"}
                desc = symbols.get(decision, decision)
                print(f"    {color}{desc}{C.RESET} {self._elapsed()}")
            
            case "stric_e_start":
                n = event.data.get("total_steps", "?")
                print(f"  {C.CYAN}⟳ STRIC_e{C.RESET} — exécution ({n} étapes)")
            
            case "stric_e_step":
                num = event.data.get("step_num", "?")
                total = event.data.get("total", "?")
                action = event.data.get("action", "?")
                reason = event.data.get("reason", "")
                if self.verbose and reason:
                    print(f"    [{num}/{total}] {C.YELLOW}{action}{C.RESET}: {C.DIM}{reason}{C.RESET}")
                else:
                    print(f"    [{num}/{total}] {C.YELLOW}{action}{C.RESET}")
            
            case "stric_e_result":
                if self.verbose:
                    preview = event.data.get("preview", "")[:100]
                    print(f"      {C.DIM}→ {preview}{C.RESET}")
            
            case "stric_e_eval":
                pct = event.data.get("progress_pct", 0)
                bar_len = 20
                filled = int(pct / 100 * bar_len)
                bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
                print(f"    {C.DIM}progression:{C.RESET} {bar} {pct}%")
            
            case "synthesizing":
                print(f"  {C.CYAN}⟳{C.RESET} Synthèse...")
            
            case "learning":
                insight = event.data.get("insight", "")
                if insight:
                    print(f"  {C.MAGENTA}💡{C.RESET} {C.DIM}{insight}{C.RESET}")
            
            case "complete":
                ms = event.data.get("duration_ms", 0)
                calls = event.data.get("calls", 0)
                print(f"  {C.GREEN}✓{C.RESET} Terminé en {ms:.0f}ms ({calls} appels substrat)")


# ═══════════════════════════════════════
# Commandes
# ═══════════════════════════════════════

async def handle_command(agent: OmniAgent, cmd: str, event_handler: CLIEventHandler) -> str | None:
    parts = cmd.strip().split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""
    
    match command:
        case "/help" | "/h":
            return HELP
        
        case "/status" | "/s":
            status = await agent.status()
            sub_icon = f"{C.GREEN}●{C.RESET}" if status["substrat_available"] else f"{C.RED}●{C.RESET}"
            lines = [
                f"\n{C.BOLD}Agent Status{C.RESET}",
                f"  Substrat: {sub_icon} {status['substrat_default'] or 'aucun'}",
                f"  Outils: {', '.join(t['name'] for t in status['tools'])}",
                f"  Mémoire: {status['memory']['total_entries']} entrées, "
                f"{status['memory']['learnings']} apprentissages, "
                f"{status['memory']['span_hours']:.1f}h de trajectoire",
            ]
            return "\n".join(lines)
        
        case "/health":
            status = await agent.status()
            lines = [f"\n{C.BOLD}Santé des substrats{C.RESET}"]
            for name, h in status.get("health", {}).items():
                icon = f"{C.GREEN}●{C.RESET}" if h.get("available") and not h.get("is_degraded") \
                       else f"{C.YELLOW}◐{C.RESET}" if h.get("available") \
                       else f"{C.RED}●{C.RESET}"
                lines.append(
                    f"  {icon} {name} ({h.get('role', '?')}): "
                    f"{h.get('total_calls', 0)} appels, "
                    f"erreurs {h.get('error_rate', 0):.1%}, "
                    f"latence {h.get('avg_latency_ms', 0):.0f}ms"
                )
            return "\n".join(lines)
        
        case "/memory" | "/m":
            summary = agent.memory.get_trajectory_summary()
            recent = agent.memory.get_recent(10)
            lines = [
                f"\n{C.BOLD}Trajectoire Mémoire{C.RESET}",
                f"  Total: {summary['total_entries']} entrées",
                f"  Types: {json.dumps(summary['by_type'])}",
                f"  Span: {summary['span_hours']:.1f}h | {summary['files']} fichiers",
                f"  Apprentissages: {summary['learnings']}",
                f"\n  {C.DIM}Récent:{C.RESET}",
            ]
            for e in recent:
                content_preview = str(e.content.get("content", e.content.get("insight", e.content)))[:80]
                type_color = {
                    "interaction": C.BLUE, "stric_trace": C.CYAN,
                    "learning": C.MAGENTA, "system": C.DIM,
                }.get(e.entry_type, C.WHITE)
                lines.append(f"  {type_color}[{e.entry_type}]{C.RESET} {content_preview}")
            return "\n".join(lines)
        
        case "/search":
            if not arg:
                return f"{C.YELLOW}Usage: /search <termes>{C.RESET}"
            results = agent.memory.search(arg)
            if not results:
                return f"{C.DIM}Aucun résultat pour '{arg}'{C.RESET}"
            lines = [f"\n{C.BOLD}Résultats pour '{arg}':{C.RESET}"]
            for e in results[:10]:
                content = str(e.content.get("content", e.content.get("insight", "")))[:100]
                lines.append(f"  [{e.entry_type}] {content}")
            return "\n".join(lines)
        
        case "/trace" | "/t":
            if not agent.last_trace:
                return f"{C.DIM}Aucune trace disponible.{C.RESET}"
            trace = agent.last_trace
            lines = [
                f"\n{C.BOLD}Dernière trace STRIC{C.RESET}",
                f"  Objectif: {trace.objective[:100]}",
                f"  Décision: {trace.final_decision.value if trace.final_decision else '?'}",
                f"  Durée: {trace.duration_ms:.0f}ms",
                f"  Appels substrat: {trace.substrate_calls}",
                f"  Cycles STRIC_i: {len(trace.stric_i_cycles)}",
                f"  Cycles STRIC_e: {len(trace.stric_e_cycles)}",
            ]
            if trace.clarification_needed:
                lines.append(f"  Clarification: {trace.clarification_needed}")
            if trace.learning:
                lines.append(f"  Apprentissage: {C.MAGENTA}{trace.learning}{C.RESET}")
            
            # Détail STRIC_i
            for i, cycle in enumerate(trace.stric_i_cycles):
                lines.append(f"\n  {C.CYAN}STRIC_i #{i+1}:{C.RESET}")
                for state in cycle:
                    coherence_str = ""
                    if state.coherence and any(v > 0 for v in state.coherence.values()):
                        coherence_str = f" [{', '.join(f'{k}={v:.2f}' for k, v in state.coherence.items())}]"
                    decision_str = f" → {state.decision.value}" if state.decision else ""
                    lines.append(f"    {state.phase.value}{coherence_str}{decision_str}")
            
            return "\n".join(lines)
        
        case "/learnings" | "/l":
            learnings = agent.memory.get_learnings(20)
            if not learnings:
                return f"{C.DIM}Aucun apprentissage enregistré.{C.RESET}"
            lines = [f"\n{C.BOLD}Apprentissages ({len(learnings)}){C.RESET}"]
            for i, l in enumerate(learnings, 1):
                lines.append(f"  {C.MAGENTA}{i}.{C.RESET} {l}")
            return "\n".join(lines)
        
        case "/config":
            return json.dumps({
                "stric": {
                    "thresholds": f"seq={agent.config.stric.threshold_seq} sem={agent.config.stric.threshold_sem} multi={agent.config.stric.threshold_multi}",
                    "max_loops": f"i={agent.config.stric.max_stric_i_loops} e={agent.config.stric.max_stric_e_loops}",
                    "substrate_eval": agent.config.stric.substrate_coherence_eval,
                    "extract_learning": agent.config.stric.extract_learning,
                },
                "substrates": [s.name for s in agent.config.substrates],
                "tools": agent.config.tools.enabled,
                "verbose": agent.config.verbose,
            }, indent=2)
        
        case "/compact":
            agent.memory.compact_old(7)
            return f"{C.GREEN}✓{C.RESET} Mémoire compactée (>7 jours)."
        
        case "/verbose" | "/v":
            agent.config.verbose = not agent.config.verbose
            event_handler.verbose = agent.config.verbose
            state = "ON" if agent.config.verbose else "OFF"
            return f"Verbose: {C.BOLD}{state}{C.RESET}"
        
        case "/clear":
            agent._conversation.clear()
            return f"{C.DIM}Conversation effacée.{C.RESET}"
        
        case "/quit" | "/q" | "/exit":
            return None
        
        case _:
            return f"{C.RED}Commande inconnue: {command}{C.RESET}\n{C.DIM}/help pour la liste{C.RESET}"


# ═══════════════════════════════════════
# Confirmation callback
# ═══════════════════════════════════════

async def confirm_action(message: str) -> bool:
    """Demander confirmation à l'utilisateur pour une action dangereuse."""
    print(f"\n{C.YELLOW}{message}{C.RESET}")
    try:
        response = input(f"{C.YELLOW}Confirmer? [y/N] {C.RESET}").strip().lower()
        return response in ("y", "yes", "oui", "o")
    except (EOFError, KeyboardInterrupt):
        return False


# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

async def main():
    print(BANNER)
    
    # Config
    config_path = Path.home() / ".omni-agent" / "config.json"
    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = Path(sys.argv[idx + 1])
    
    if config_path.exists():
        print(f"{C.DIM}Config: {config_path}{C.RESET}")
        config = Config.load(config_path)
    else:
        print(f"{C.DIM}Config par défaut (llama-server localhost:8080){C.RESET}")
        config = Config.default()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config.save(config_path)
        print(f"{C.DIM}Sauvegardé: {config_path}{C.RESET}")
    
    if "--verbose" in sys.argv or "-v" in sys.argv:
        config.verbose = True
    
    # Event handler
    event_handler = CLIEventHandler(verbose=config.verbose)
    
    # Agent
    agent = OmniAgent(
        config=config,
        on_event=event_handler.handle,
        on_confirm=confirm_action,
    )
    
    # Check substrat
    status = await agent.status()
    if status["substrat_available"]:
        print(f"{C.GREEN}● Substrat connecté: {status['substrat_default']}{C.RESET}")
    else:
        print(f"{C.YELLOW}⚠ Substrat non disponible: {status['substrat_default']}")
        print(f"  → llama-server sur localhost:8080 ou modifier ~/.omni-agent/config.json{C.RESET}")
    
    # Mémoire
    mem = status.get("memory", {})
    if mem.get("total_entries", 0) > 0:
        print(f"{C.DIM}Mémoire: {mem['total_entries']} entrées, {mem.get('learnings', 0)} apprentissages{C.RESET}")
    
    print(f"{C.DIM}/help pour les commandes{C.RESET}\n")
    
    # Boucle
    while True:
        try:
            user_input = input(f"{C.BLUE}{C.BOLD}❯ {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C.DIM}Au revoir.{C.RESET}")
            break
        
        if not user_input:
            continue
        
        if user_input.startswith("/"):
            result = await handle_command(agent, user_input, event_handler)
            if result is None:
                print(f"\n{C.DIM}Au revoir.{C.RESET}")
                break
            print(result)
            continue
        
        # Reset timer pour l'event handler
        event_handler._t0 = time.time()
        
        try:
            response = await agent.process(user_input)
            print(f"\n{C.MAGENTA}{C.BOLD}◆{C.RESET} {response}\n")
        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}Interrompu.{C.RESET}\n")
        except Exception as e:
            print(f"\n{C.RED}Erreur: {e}{C.RESET}\n")
            if config.verbose:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
