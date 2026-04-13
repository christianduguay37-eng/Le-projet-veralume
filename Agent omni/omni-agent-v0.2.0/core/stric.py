"""
OMNI AGENT — Double STRIC (O0) v0.2

Améliorations:
- Validation tri-dimensionnelle déléguée au substrat (plus seulement heuristique)
- Parsing JSON robuste (gère ```json blocks, JSON imbriqué)
- Gestion needs_clarification → retour à l'utilisateur
- Extraction d'apprentissage post-trace
- Plan adaptatif: STRIC_e peut injecter des étapes supplémentaires
- Système d'événements pour feedback live à la CLI
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable
import time
import json
import re


# ═══════════════════════════════════════
# Types et structures
# ═══════════════════════════════════════

class STRICPhase(Enum):
    SUBSTRAT = "S"
    TRAITEMENT = "T"
    RESULTAT = "R"
    INTERPRETATION = "I"
    CREATION = "C"


class STRICDecision(Enum):
    ACT = "act"
    REFORMULATE = "reformulate"
    ESCALATE = "escalate"
    CLARIFY = "clarify"        # Nouveau: besoin de clarification utilisateur
    CONTINUE = "continue"
    COMPLETE = "complete"
    ABORT = "abort"


@dataclass
class STRICState:
    phase: STRICPhase
    content: dict[str, Any] = field(default_factory=dict)
    coherence: dict[str, float] = field(default_factory=lambda: {
        "seq": 0.0, "sem": 0.0, "multi": 0.0
    })
    decision: STRICDecision | None = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "content": self.content,
            "coherence": self.coherence,
            "decision": self.decision.value if self.decision else None,
            "timestamp": self.timestamp,
        }


@dataclass 
class STRICTrace:
    objective: str
    stric_i_cycles: list[list[STRICState]] = field(default_factory=list)
    stric_e_cycles: list[list[STRICState]] = field(default_factory=list)
    final_decision: STRICDecision | None = None
    result: Any = None
    clarification_needed: str | None = None
    learning: str | None = None
    duration_ms: float = 0.0
    substrate_calls: int = 0
    
    def to_dict(self) -> dict:
        return {
            "objective": self.objective,
            "stric_i": [[s.to_dict() for s in cycle] for cycle in self.stric_i_cycles],
            "stric_e": [[s.to_dict() for s in cycle] for cycle in self.stric_e_cycles],
            "final_decision": self.final_decision.value if self.final_decision else None,
            "clarification_needed": self.clarification_needed,
            "learning": self.learning,
            "duration_ms": self.duration_ms,
            "substrate_calls": self.substrate_calls,
        }


# ═══════════════════════════════════════
# Event system
# ═══════════════════════════════════════

class STRICEvent:
    """Événement émis pendant l'exécution pour feedback live."""
    def __init__(self, event_type: str, data: dict | None = None):
        self.type = event_type
        self.data = data or {}
        self.timestamp = time.time()


# Event types:
# "stric_i_start"      — début cycle intérieur
# "stric_i_phase"      — phase STRIC_i en cours {phase, attempt}
# "stric_i_coherence"  — résultat cohérence {seq, sem, multi, passes}
# "stric_i_decision"   — décision STRIC_i {decision}
# "stric_e_start"      — début cycle extérieur
# "stric_e_step"       — étape en cours {step_num, total, action}
# "stric_e_result"     — résultat d'étape {step_num, preview}
# "stric_e_eval"       — évaluation progression {progress_pct}
# "synthesizing"       — synthèse en cours
# "learning"           — apprentissage extrait {insight}
# "complete"           — terminé {duration_ms}

EventCallback = Callable[[STRICEvent], Awaitable[None]] | Callable[[STRICEvent], None]


# ═══════════════════════════════════════
# JSON parsing robuste
# ═══════════════════════════════════════

def extract_json(text: str) -> dict | None:
    """
    Extraire du JSON depuis une réponse LLM.
    Gère: ```json blocks, JSON nu, texte avant/après.
    """
    # 1. Essayer ```json ... ```
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # 2. Chercher le JSON le plus complet (gestion accolades imbriquées)
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    start = -1
                    continue
    
    # 3. Dernier recours: trouver le plus gros bloc { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}") + 1
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end])
        except json.JSONDecodeError:
            pass
    
    return None


# ═══════════════════════════════════════
# Double STRIC
# ═══════════════════════════════════════

class DoubleSTRIC:
    """
    Opérateur O0 — Double STRIC v0.2
    
    Changements clés:
    - _evaluate_coherence délègue au substrat si configuré
    - needs_clarification interrompt le cycle et retourne à l'utilisateur
    - Extraction d'apprentissage après chaque trace
    - Événements émis à chaque phase pour feedback live
    - Plan adaptatif: possibilité d'ajouter des étapes en cours de route
    """
    
    def __init__(self, config, substrate_fn, tool_registry, 
                 event_callback: EventCallback | None = None):
        self.config = config
        self.substrate = substrate_fn
        self.tools = tool_registry
        self._on_event = event_callback
        self._call_count = 0
    
    async def _emit(self, event_type: str, data: dict | None = None):
        if self._on_event:
            event = STRICEvent(event_type, data)
            result = self._on_event(event)
            if hasattr(result, '__await__'):
                await result
    
    async def _call_substrate(self, messages: list[dict], system: str = "") -> str:
        """Wrapper pour compter les appels."""
        self._call_count += 1
        return await self.substrate(messages, system)
    
    async def execute(self, objective: str, context: list[dict]) -> STRICTrace:
        trace = STRICTrace(objective=objective)
        self._call_count = 0
        t0 = time.time()
        
        # ═══════════════════════════════════════
        # STRIC_i — Cycle intérieur
        # ═══════════════════════════════════════
        await self._emit("stric_i_start", {"objective": objective})
        
        stric_i_decision = STRICDecision.REFORMULATE
        plan = {}
        i_loop = 0
        prev_feedback = None
        
        while stric_i_decision == STRICDecision.REFORMULATE and i_loop < self.config.max_stric_i_loops:
            i_cycle = []
            
            # S — Observer
            await self._emit("stric_i_phase", {"phase": "S", "attempt": i_loop})
            s_state = STRICState(phase=STRICPhase.SUBSTRAT, content={
                "objective": objective,
                "tools_available": [t["name"] for t in self.tools.list_tools()],
                "context_size": len(context),
                "attempt": i_loop,
            })
            i_cycle.append(s_state)
            
            # T — Structurer
            await self._emit("stric_i_phase", {"phase": "T", "attempt": i_loop})
            plan_prompt = self._build_plan_prompt(objective, context, i_loop, prev_feedback)
            plan_response = await self._call_substrate(
                messages=[{"role": "user", "content": plan_prompt}],
                system=STRIC_I_SYSTEM_PROMPT
            )
            t_state = STRICState(phase=STRICPhase.TRAITEMENT, content={
                "raw_response_len": len(plan_response),
            })
            i_cycle.append(t_state)
            
            # R — Formuler plan
            await self._emit("stric_i_phase", {"phase": "R", "attempt": i_loop})
            plan = self._parse_plan(plan_response)
            r_state = STRICState(phase=STRICPhase.RESULTAT, content={
                "plan_steps": len(plan.get("steps", [])),
                "understanding": plan.get("understanding", "")[:200],
            })
            i_cycle.append(r_state)
            
            # Vérifier needs_clarification
            clarification = plan.get("needs_clarification")
            if clarification and isinstance(clarification, str) and clarification.lower() not in ("null", "none", ""):
                stric_i_decision = STRICDecision.CLARIFY
                trace.clarification_needed = clarification
                c_state = STRICState(phase=STRICPhase.CREATION, decision=stric_i_decision,
                                     content={"clarification": clarification})
                i_cycle.append(c_state)
                trace.stric_i_cycles.append(i_cycle)
                break
            
            # I — Valider cohérence
            await self._emit("stric_i_phase", {"phase": "I", "attempt": i_loop})
            if self.config.substrate_coherence_eval:
                coherence = await self._substrate_coherence_eval(plan, objective, context)
            else:
                coherence = self._heuristic_coherence_eval(plan, objective)
            
            passes = self._coherence_passes(coherence)
            await self._emit("stric_i_coherence", {**coherence, "passes": passes})
            
            i_state = STRICState(phase=STRICPhase.INTERPRETATION, coherence=coherence,
                                 content={"passes": passes})
            i_cycle.append(i_state)
            
            # C — Décider
            if passes:
                stric_i_decision = STRICDecision.ACT
            elif i_loop >= self.config.max_stric_i_loops - 1:
                stric_i_decision = STRICDecision.ESCALATE
            else:
                stric_i_decision = STRICDecision.REFORMULATE
                prev_feedback = coherence  # Passer le feedback de cohérence à la prochaine itération
            
            await self._emit("stric_i_decision", {"decision": stric_i_decision.value, "attempt": i_loop})
            
            c_state = STRICState(phase=STRICPhase.CREATION, 
                                content={"plan_steps": len(plan.get("steps", []))},
                                decision=stric_i_decision)
            i_cycle.append(c_state)
            trace.stric_i_cycles.append(i_cycle)
            i_loop += 1
        
        # Sortie sans STRIC_e
        if stric_i_decision in (STRICDecision.ESCALATE, STRICDecision.CLARIFY):
            trace.final_decision = stric_i_decision
            trace.duration_ms = (time.time() - t0) * 1000
            trace.substrate_calls = self._call_count
            return trace
        
        # ═══════════════════════════════════════
        # STRIC_e — Cycle extérieur
        # ═══════════════════════════════════════
        steps = plan.get("steps", [])
        total_steps = len(steps)
        accumulated_results = []
        e_loop = 0
        step_idx = 0
        
        await self._emit("stric_e_start", {"total_steps": total_steps})
        
        while step_idx < len(steps) and e_loop < self.config.max_stric_e_loops:
            step = steps[step_idx]
            e_cycle = []
            
            # S — Sélectionner
            await self._emit("stric_e_step", {
                "step_num": step_idx + 1, "total": len(steps),
                "action": step.get("action", "?"), "reason": step.get("reason", "")[:100],
            })
            s_state = STRICState(phase=STRICPhase.SUBSTRAT, content={
                "step": step, "step_num": step_idx + 1,
            })
            e_cycle.append(s_state)
            
            # T — Exécuter
            action_result = await self._execute_step(step, context, accumulated_results)
            t_state = STRICState(phase=STRICPhase.TRAITEMENT, content={
                "action": step.get("action", ""),
                "success": "error" not in str(action_result).lower()[:100],
            })
            e_cycle.append(t_state)
            
            # R — Capturer
            accumulated_results.append({"step": step, "result": action_result})
            result_preview = str(action_result)[:200]
            await self._emit("stric_e_result", {
                "step_num": step_idx + 1, "preview": result_preview,
            })
            r_state = STRICState(phase=STRICPhase.RESULTAT, content={
                "result_preview": result_preview,
            })
            e_cycle.append(r_state)
            
            # I — Évaluer (seulement toutes les N étapes ou à la dernière)
            should_eval = (step_idx == len(steps) - 1) or (e_loop % 3 == 2)
            
            if should_eval:
                eval_result = await self._evaluate_progress(
                    objective, steps, accumulated_results, context
                )
                await self._emit("stric_e_eval", {
                    "progress_pct": eval_result.get("progress_pct", 50),
                })
                i_state = STRICState(phase=STRICPhase.INTERPRETATION, content={
                    "evaluation": eval_result,
                })
                e_cycle.append(i_state)
                
                # C — Décider
                e_decision = self._decide_continuation(eval_result)
                
                # Plan adaptatif: le substrat peut suggérer de nouvelles étapes
                new_steps = eval_result.get("inject_steps", [])
                if new_steps and isinstance(new_steps, list):
                    steps.extend(new_steps)
                
            else:
                e_decision = STRICDecision.CONTINUE
            
            c_state = STRICState(phase=STRICPhase.CREATION, decision=e_decision)
            e_cycle.append(c_state)
            trace.stric_e_cycles.append(e_cycle)
            
            step_idx += 1
            e_loop += 1
            
            if e_decision in (STRICDecision.COMPLETE, STRICDecision.ABORT):
                break
        
        # Synthèse
        await self._emit("synthesizing")
        trace.result = await self._synthesize(objective, accumulated_results, context)
        trace.final_decision = STRICDecision.COMPLETE
        
        # Extraction d'apprentissage
        if self.config.extract_learning:
            trace.learning = await self._extract_learning(objective, accumulated_results, trace)
            if trace.learning:
                await self._emit("learning", {"insight": trace.learning[:200]})
        
        trace.duration_ms = (time.time() - t0) * 1000
        trace.substrate_calls = self._call_count
        await self._emit("complete", {"duration_ms": trace.duration_ms, "calls": self._call_count})
        
        return trace
    
    # ─── Plan building ───────────────────────
    
    def _build_plan_prompt(self, objective: str, context: list[dict], 
                           attempt: int, prev_feedback: dict | None) -> str:
        tools_desc = "\n".join(
            f"- {t['name']}: {t['description']}" 
            for t in self.tools.list_tools()
        )
        
        ctx_summary = ""
        if context:
            ctx_summary = "\n".join(
                f"[{c.get('role', c.get('t', '?'))}] {str(c.get('content', c.get('summary', '')))[:200]}" 
                for c in context[-10:]
            )
        
        feedback_note = ""
        if attempt > 0 and prev_feedback:
            weak_axes = [k for k, v in prev_feedback.items() if isinstance(v, (int, float)) and v < 0.7]
            feedback_note = (
                f"\n⚠ REFORMULATION #{attempt}. Le plan précédent manquait de cohérence."
                f"\nAxes faibles: {', '.join(weak_axes) if weak_axes else 'général'}."
                f"\nScores: seq={prev_feedback.get('seq', '?')}, sem={prev_feedback.get('sem', '?')}, multi={prev_feedback.get('multi', '?')}"
                f"\nCorrige spécifiquement les axes faibles."
            )
        
        return f"""OBJECTIF: {objective}
{feedback_note}

OUTILS DISPONIBLES:
{tools_desc}

CONTEXTE RÉCENT:
{ctx_summary if ctx_summary else "(aucun)"}

Analyse l'objectif et produis un plan d'action structuré.
Réponds UNIQUEMENT en JSON valide (pas de texte autour):
{{
  "understanding": "ta compréhension de l'objectif en une phrase",
  "decomposition": ["sous-problème 1", "sous-problème 2"],
  "steps": [
    {{"action": "tool_name", "params": {{}}, "reason": "pourquoi cette action"}}
  ],
  "risks": ["risque potentiel"],
  "needs_clarification": null
}}

Règles:
- "action" doit être un outil listé ci-dessus ou "respond" pour réponse directe
- "params" doit correspondre aux paramètres de l'outil
- Si l'objectif est trop ambigu, mets ta question dans "needs_clarification"
- Pas de texte en dehors du JSON"""
    
    def _parse_plan(self, response: str) -> dict:
        parsed = extract_json(response)
        if parsed and isinstance(parsed, dict):
            # Valider la structure minimale
            if "steps" not in parsed:
                parsed["steps"] = [{"action": "respond", "params": {"content": response}, "reason": "réponse directe"}]
            return parsed
        
        # Fallback
        return {
            "understanding": response[:200],
            "decomposition": [],
            "steps": [{"action": "respond", "params": {"content": response}, "reason": "parsing échoué, réponse directe"}],
            "risks": ["parsing JSON échoué"],
            "needs_clarification": None,
        }
    
    # ─── Coherence evaluation ───────────────────
    
    async def _substrate_coherence_eval(self, plan: dict, objective: str, context: list) -> dict[str, float]:
        """Déléguer l'évaluation tri-dimensionnelle au substrat."""
        plan_summary = json.dumps(plan, ensure_ascii=False)[:2000]
        
        eval_prompt = f"""Évalue la cohérence de ce plan d'action sur 3 axes (0.0 à 1.0):

OBJECTIF: {objective}

PLAN: {plan_summary}

Axes:
- seq (séquentielle): les étapes s'enchaînent logiquement? pas de dépendances manquantes?
- sem (sémantique): le plan répond réellement à l'objectif? compréhension correcte?
- multi (multi-perspective): les outils choisis sont appropriés? risques identifiés? rien d'oublié?

Réponds UNIQUEMENT en JSON: {{"seq": 0.0, "sem": 0.0, "multi": 0.0, "diagnostic": "..."}}"""
        
        response = await self._call_substrate(
            messages=[{"role": "user", "content": eval_prompt}],
            system="Tu es l'évaluateur de cohérence d'un agent autonome. Sois exigeant et honnête. JSON uniquement."
        )
        
        parsed = extract_json(response)
        if parsed:
            return {
                "seq": max(0.0, min(1.0, float(parsed.get("seq", 0.5)))),
                "sem": max(0.0, min(1.0, float(parsed.get("sem", 0.5)))),
                "multi": max(0.0, min(1.0, float(parsed.get("multi", 0.5)))),
            }
        
        # Fallback sur heuristique
        return self._heuristic_coherence_eval(plan, objective)
    
    def _heuristic_coherence_eval(self, plan: dict, objective: str) -> dict[str, float]:
        """Évaluation heuristique locale (fallback)."""
        scores = {"seq": 0.0, "sem": 0.0, "multi": 0.0}
        steps = plan.get("steps", [])
        understanding = plan.get("understanding", "")
        
        # C_seq
        if steps:
            valid = sum(1 for s in steps if s.get("action") and s.get("reason"))
            scores["seq"] = valid / len(steps)
        
        # C_sem
        if understanding:
            obj_words = set(w for w in objective.lower().split() if len(w) > 2)
            und_words = set(w for w in understanding.lower().split() if len(w) > 2)
            overlap = len(obj_words & und_words)
            scores["sem"] = min(1.0, overlap / max(len(obj_words), 1) * 2)
        
        # C_multi
        available = {t["name"] for t in self.tools.list_tools()} | {"respond"}
        if steps:
            known = sum(1 for s in steps if s.get("action") in available)
            scores["multi"] = known / len(steps)
        
        return scores
    
    def _coherence_passes(self, coherence: dict[str, float]) -> bool:
        return (
            coherence.get("seq", 0) >= self.config.threshold_seq
            and coherence.get("sem", 0) >= self.config.threshold_sem
            and coherence.get("multi", 0) >= self.config.threshold_multi
        )
    
    # ─── Execution ───────────────────────────
    
    async def _execute_step(self, step: dict, context: list, accumulated: list) -> Any:
        action = step.get("action", "respond")
        params = step.get("params", {})
        
        if action == "respond":
            # Génération enrichie: injecter le contexte accumulé
            resp_content = params.get("content", "")
            if accumulated:
                prev_results = "\n".join(
                    f"[{r['step'].get('action', '?')}] {str(r['result'])[:300]}"
                    for r in accumulated[-3:]
                )
                resp_content = f"Contexte des actions précédentes:\n{prev_results}\n\nQuestion/objectif: {resp_content}"
            
            return await self._call_substrate(
                messages=[{"role": "user", "content": resp_content}],
                system="Réponds directement et utilement. Synthétise les informations disponibles."
            )
        
        tool = self.tools.get(action)
        if tool is None:
            return {"error": f"Outil inconnu: {action}", "available": [t["name"] for t in self.tools.list_tools()]}
        
        try:
            return await tool.execute(**params)
        except TypeError as e:
            # Paramètres invalides
            return {"error": f"Paramètres invalides pour {action}: {e}", "expected": tool.parameters}
        except Exception as e:
            return {"error": f"Erreur {action}: {e}"}
    
    async def _evaluate_progress(self, objective: str, all_steps: list, 
                                  accumulated: list, context: list) -> dict:
        results_summary = "\n".join(
            f"Étape {i+1}/{len(all_steps)}: [{r['step'].get('action', '?')}] → {str(r['result'])[:200]}"
            for i, r in enumerate(accumulated)
        )
        remaining = len(all_steps) - len(accumulated)
        
        eval_prompt = f"""OBJECTIF: {objective}

RÉSULTATS ({len(accumulated)}/{len(all_steps)} étapes):
{results_summary}

ÉTAPES RESTANTES: {remaining}

Évalue et réponds en JSON:
{{
  "progress_pct": 0-100,
  "objective_reached": true/false,
  "drift_detected": true/false,
  "should_continue": true/false,
  "reasoning": "...",
  "inject_steps": []
}}

Si des étapes supplémentaires sont nécessaires (non prévues), ajoute-les dans "inject_steps" au même format que les étapes du plan.
Si l'objectif est atteint, mets objective_reached=true même si des étapes restent."""
        
        response = await self._call_substrate(
            messages=[{"role": "user", "content": eval_prompt}],
            system="Évaluateur d'agent. Sois factuel. JSON uniquement."
        )
        
        parsed = extract_json(response)
        if parsed:
            return parsed
        
        return {"progress_pct": 50, "objective_reached": False,
                "should_continue": True, "drift_detected": False}
    
    def _decide_continuation(self, eval_result: dict) -> STRICDecision:
        if eval_result.get("objective_reached"):
            return STRICDecision.COMPLETE
        if eval_result.get("drift_detected"):
            return STRICDecision.ABORT
        if eval_result.get("should_continue", True):
            return STRICDecision.CONTINUE
        return STRICDecision.COMPLETE
    
    # ─── Synthesis & Learning ───────────────────
    
    async def _synthesize(self, objective: str, accumulated: list, context: list) -> str:
        if not accumulated:
            return "[Agent] Aucune action exécutée."
        
        results_summary = "\n".join(
            f"[{r['step'].get('action', '?')}] {str(r['result'])[:500]}"
            for r in accumulated
        )
        
        return await self._call_substrate(
            messages=[{"role": "user", "content": f"""OBJECTIF: {objective}

RÉSULTATS DE TOUTES LES ACTIONS:
{results_summary}

Synthétise une réponse finale claire et utile. 
- Pas de méta-commentaire sur le processus
- Si une action a échoué, mentionne-le
- Va droit au but"""}],
            system="Synthétise les résultats en une réponse directe. Pas de filler."
        )
    
    async def _extract_learning(self, objective: str, accumulated: list, trace: STRICTrace) -> str | None:
        """Extraire un apprentissage de la trace pour la mémoire long-terme."""
        if not accumulated:
            return None
        
        errors = [r for r in accumulated if "error" in str(r.get("result", "")).lower()]
        reformulations = len(trace.stric_i_cycles) - 1
        
        learning_prompt = f"""Un agent vient de traiter cet objectif:
OBJECTIF: {objective}
ÉTAPES EXÉCUTÉES: {len(accumulated)}
ERREURS: {len(errors)}
REFORMULATIONS STRIC_i: {reformulations}
DURÉE: {trace.duration_ms:.0f}ms

Extrait UN apprentissage concis (1-2 phrases max) qui serait utile pour de futures tâches similaires.
Si rien d'utile → réponds exactement "null"."""
        
        response = await self._call_substrate(
            messages=[{"role": "user", "content": learning_prompt}],
            system="Extracteur d'apprentissage. Une insight concise ou null."
        )
        
        response = response.strip()
        if response.lower() in ("null", "none", "rien", ""):
            return None
        return response[:500]


# ─── System prompts ───────────────────────

STRIC_I_SYSTEM_PROMPT = """Tu es le module de planification d'un agent autonome.
Ton rôle: analyser un objectif et produire un plan d'action structuré.

Règles:
- Décompose l'objectif en sous-problèmes clairs
- Chaque étape doit référencer un outil disponible ou "respond" pour réponse directe
- Pour l'outil "terminal": params = {"command": "...", "timeout": 30}
- Pour l'outil "filesystem": params = {"operation": "read|write|list|exists|mkdir", "path": "...", "content": "..."}
- Pour l'outil "web_fetch": params = {"url": "..."}
- Si l'objectif est ambigu, utilise "needs_clarification" avec ta question
- Sois concis — pas de filler
- Réponds UNIQUEMENT en JSON valide, sans texte avant/après"""
