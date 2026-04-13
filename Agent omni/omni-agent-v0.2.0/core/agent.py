"""
OMNI AGENT — Agent Principal v0.2

Ajouts:
- Système d'événements pour feedback live à la CLI
- Flow de clarification: si STRIC_i demande des précisions, retour à l'utilisateur
- Stockage des apprentissages en mémoire
- Meilleur routage conversation → les réponses directes injectent l'historique
- Confirmation callback pour outils dangereux
"""

from typing import Callable, Awaitable, Any
from config import Config, SubstrateConfig
from core.stric import DoubleSTRIC, STRICDecision, STRICEvent, STRICTrace
from core.memory import TrajectoryMemory
from core.router import SubstrateRouter
from substrates.base import LocalSubstrate, RemoteSubstrate
from tools.base import ToolRegistry
from tools.terminal import TerminalTool
from tools.filesystem import FilesystemTool
from tools.web import WebFetchTool


EventCallback = Callable[[STRICEvent], Awaitable[None]] | Callable[[STRICEvent], None]
ConfirmCallback = Callable[[str], Awaitable[bool]]


class OmniAgent:
    """
    Agent Omni local v0.2 — STRIC natif dans l'os.
    
    Nouvelles capacités:
    - on_event: callback pour chaque phase STRIC (feedback CLI live)
    - on_confirm: callback pour confirmer les actions dangereuses
    - Clarification flow: retourne la question au lieu de forcer un plan
    - Apprentissage automatique stocké en mémoire
    """
    
    def __init__(self, config: Config | None = None,
                 on_event: EventCallback | None = None,
                 on_confirm: ConfirmCallback | None = None):
        self.config = config or Config.default()
        self._on_event = on_event
        self._on_confirm = on_confirm
        
        # Mémoire
        self.memory = TrajectoryMemory(
            base_dir=self.config.memory.trajectory_dir,
            max_context=self.config.memory.max_context_entries
        )
        
        # Outils
        self.tools = self._create_tools()
        
        # Routeur & substrats
        self.router = SubstrateRouter()
        self._init_substrates()
        
        # Boucle STRIC
        self.stric = DoubleSTRIC(
            config=self.config.stric,
            substrate_fn=self._substrate_call,
            tool_registry=self.tools,
            event_callback=on_event,
        )
        
        # Conversation courante
        self._conversation: list[dict] = []
        
        # Dernier trace pour inspection
        self.last_trace: STRICTrace | None = None
    
    def _create_tools(self) -> ToolRegistry:
        registry = ToolRegistry()
        
        # Terminal avec confirmation
        registry.register(TerminalTool(
            confirm_patterns=self.config.tools.confirm_patterns,
            blocked_patterns=self.config.tools.blocked_patterns,
            confirm_fn=self._on_confirm,
        ))
        registry.register(FilesystemTool())
        registry.register(WebFetchTool())
        
        return registry
    
    def _init_substrates(self):
        for sc in self.config.substrates:
            if sc.is_local:
                substrate = LocalSubstrate(
                    sc.name, sc.role, sc.endpoint, sc.model, sc.timeout_s
                )
            else:
                substrate = RemoteSubstrate(
                    sc.name, sc.role, sc.endpoint, sc.model, sc.api_key, sc.timeout_s
                )
            self.router.register(substrate, is_default=(sc.priority == 0))
    
    async def _substrate_call(self, messages: list[dict], system: str = "") -> str:
        substrate = self.router.get_default()
        if substrate is None:
            return "[ERREUR] Aucun substrat disponible"
        return await substrate.complete(messages, system)
    
    async def process(self, user_input: str) -> str:
        """Point d'entrée principal. Input → Double STRIC → Réponse."""
        
        # Enregistrer
        self.memory.append("interaction", {"role": "user", "content": user_input})
        self._conversation.append({"role": "user", "content": user_input})
        
        # Router: simple ou complexe
        if self._is_simple_query(user_input):
            response = await self._direct_response(user_input)
        else:
            context = self.memory.get_context_for_stric()
            trace = await self.stric.execute(user_input, context)
            self.last_trace = trace
            
            # Enregistrer la trace (version compacte)
            trace_data = {
                "objective": trace.objective,
                "final_decision": trace.final_decision.value if trace.final_decision else None,
                "duration_ms": trace.duration_ms,
                "substrate_calls": trace.substrate_calls,
                "learning": trace.learning,
                "i_cycles": len(trace.stric_i_cycles),
                "e_cycles": len(trace.stric_e_cycles),
            }
            self.memory.append("stric_trace", trace_data,
                             tags=["objective", trace.final_decision.value if trace.final_decision else "unknown"])
            
            # Stocker l'apprentissage séparément
            if trace.learning:
                self.memory.append("learning", {
                    "insight": trace.learning,
                    "from_objective": trace.objective[:200],
                })
            
            # Extraire la réponse
            response = self._extract_response(trace)
        
        # Enregistrer la réponse
        self.memory.append("interaction", {
            "role": "agent",
            "content": response[:2000],
        })
        self._conversation.append({"role": "assistant", "content": response})
        
        return response
    
    def _extract_response(self, trace: STRICTrace) -> str:
        """Extraire la réponse appropriée selon la décision finale."""
        match trace.final_decision:
            case STRICDecision.CLARIFY:
                return f"[❓] {trace.clarification_needed}"
            
            case STRICDecision.ESCALATE:
                return self._handle_escalation(trace)
            
            case STRICDecision.ABORT:
                return "[Agent] Exécution interrompue — dérive détectée par rapport à l'objectif initial."
            
            case STRICDecision.COMPLETE:
                if trace.result:
                    return str(trace.result)
                return "[Agent] Objectif traité mais aucun résultat concret produit."
            
            case _:
                return "[Agent] État inattendu."
    
    def _is_simple_query(self, text: str) -> bool:
        """
        Heuristique améliorée: simple vs complexe.
        """
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Commandes explicites vers l'agent
        if text_lower.startswith(("fais", "crée", "créer", "build", "construis",
                                   "cherche", "search", "find", "trouve",
                                   "analyse", "analyze", "compare",
                                   "installe", "install", "configure",
                                   "modifie", "edit", "change", "update",
                                   "exécute", "run", "lance", "execute",
                                   "écris", "write", "deploy", "supprime",
                                   "télécharge", "download", "upload")):
            return False
        
        # Signaux de complexité dans le corps
        complex_signals = [
            "et ensuite", "puis", "after that", "then",
            "dans le fichier", "in the file", "dans le dossier",
            "sur le serveur", "via api", "http://", "https://",
        ]
        if any(s in text_lower for s in complex_signals):
            return False
        
        # Court et interrogatif = simple
        if len(words) < 20 and ("?" in text or 
            any(text_lower.startswith(q) for q in 
                ("c'est", "what", "how", "comment", "pourquoi", "why", 
                 "qui", "who", "quand", "when", "où", "where",
                 "est-ce", "is ", "are ", "do ", "does ", "can ",
                 "combien", "how much", "how many", "quel", "quelle"))):
            return True
        
        # Court et conversationnel
        if len(words) < 8:
            return True
        
        # Par défaut: pas simple (mieux vaut planifier que rater)
        return False
    
    async def _direct_response(self, query: str) -> str:
        """Réponse directe avec conversation complète."""
        # Construire les messages avec historique
        messages = []
        for msg in self._conversation[-10:]:  # 10 derniers messages
            messages.append(msg)
        
        if not messages or messages[-1].get("content") != query:
            messages.append({"role": "user", "content": query})
        
        # Injecter les learnings pertinents
        learnings = self.memory.get_learnings(5)
        memory_note = ""
        if learnings:
            memory_note = "\nApprentissages récents: " + " | ".join(learnings[:3])
        
        return await self._substrate_call(
            messages=messages,
            system=f"Tu es Omni, un agent local intelligent. Réponds directement et utilement. Sois concis.{memory_note}"
        )
    
    def _handle_escalation(self, trace: STRICTrace) -> str:
        last_cycle = trace.stric_i_cycles[-1] if trace.stric_i_cycles else []
        coherence = {"seq": 0, "sem": 0, "multi": 0}
        for state in last_cycle:
            if state.coherence and any(v > 0 for v in state.coherence.values()):
                coherence = state.coherence
        
        weak = [k for k, v in coherence.items() if v < 0.7]
        weak_desc = {
            "seq": "enchaînement logique des étapes",
            "sem": "compréhension de l'objectif",
            "multi": "adéquation des outils/approche",
        }
        
        details = ", ".join(weak_desc.get(w, w) for w in weak)
        
        return (
            f"[Agent] Plan insuffisamment cohérent après {len(trace.stric_i_cycles)} tentatives.\n"
            f"Problème: {details}\n"
            f"Scores: seq={coherence.get('seq', 0):.2f} sem={coherence.get('sem', 0):.2f} "
            f"multi={coherence.get('multi', 0):.2f}\n"
            f"Peux-tu reformuler ou préciser?"
        )
    
    async def status(self) -> dict:
        default_sub = self.router.get_default()
        available = await default_sub.is_available() if default_sub else False
        health = await self.router.health_report()
        
        return {
            "substrat_default": default_sub.name if default_sub else None,
            "substrat_available": available,
            "substrates": self.router.list_substrates(),
            "health": health,
            "tools": self.tools.list_tools(),
            "memory": self.memory.get_trajectory_summary(),
        }
