from __future__ import annotations

import json
from typing import Dict, Any, Tuple, List, Optional
import os
import logging

from .models import (
    InputPayload,
    PlayerAnalysis,
    BehaviorAnalysis,
    WorldAnalysis,
    StoryAnalysis,
    MemoryAnalysis,
    NPCIntent,
    PriorityDecision,
    InterventionDecision,
    NPCResponse,
    Quest,
)
from .prompts import (
    PLAYER_ANALYZER_PROMPT,
    BEHAVIOR_ANALYZER_PROMPT,
    WORLD_CONTEXT_PROMPT,
    STORY_TRACKER_PROMPT,
    MEMORY_AGENT_PROMPT,
    GUIDE_INTENT_PLANNER_PROMPT,
    PRIORITY_MANAGER_PROMPT,
    INTERVENTION_CONTROLLER_PROMPT,
    DIALOGUE_EMOTION_ACTION_PROMPT,
    SELF_CRITIC_CONSISTENCY_PROMPT,
)

# Logger for structured outputs
logger = logging.getLogger("npc_backend")

# DeepAgents availability check
DEEPAGENTS_MODEL = os.getenv("DEEPAGENTS_MODEL", "openai:gpt-4o")

try:
    from deepagents import create_deep_agent
    DEEPAGENTS_AVAILABLE = True
except Exception:
    create_deep_agent = None
    DEEPAGENTS_AVAILABLE = False
    print("[NPC Backend] Mode: FALLBACK (Deep Agents not found)")

_DEEP_AGENT: Optional[object] = None

def get_deep_agent():
    global _DEEP_AGENT
    if not DEEPAGENTS_AVAILABLE:
        return None
    if _DEEP_AGENT is None:
        _DEEP_AGENT = create_deep_agent(model=DEEPAGENTS_MODEL)
    return _DEEP_AGENT


def run_with_deepagents(prompt: str, user_content: str) -> str:
    agent = get_deep_agent()
    if agent is None:
        raise RuntimeError("Deep Agents is not available")

    result = agent.invoke({
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are one sub-agent inside a game companion NPC reasoning pipeline. "
                    "Follow the system prompt exactly and return only valid JSON. "
                    "Do not add explanations."
                ),
            },
            {
                "role": "user",
                "content": f"SYSTEM PROMPT:\n{prompt}\n\nINPUT JSON:\n{user_content}",
            },
        ]
    })

    messages = result.get("messages", [])
    if not messages:
        return "{}"

    last = messages[-1]
    content = getattr(last, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts).strip() or "{}"

    return str(content) if content else "{}"


def run_with_heuristic(prompt: str, user_content: str) -> str:
    return heuristic_response(prompt, user_content)


def run_llm_system_prompt(prompt: str, user_content: str) -> Tuple[str, str]:
    """Return (assistant_text, mode) where mode in {"deepagents", "heuristic"}."""
    if DEEPAGENTS_AVAILABLE:
        try:
            return run_with_deepagents(prompt, user_content), "deepagents"
        except Exception as e:
            print(f"[NPC Backend] Deep Agents runtime failed, switching to fallback: {e}")
            text = run_with_heuristic(prompt, user_content)
            return text, "heuristic"
    else:
        text = run_with_heuristic(prompt, user_content)
        return text, "heuristic"

def heuristic_response(prompt: str, user_content: str) -> str:
    """Very small rule-based fallback to keep demo functional offline."""
    try:
        data = json.loads(user_content)
    except Exception:
        data = {}

    # Player state analyzer
    if "PlayerStateAnalyzer" in prompt:
        player = data.get("player", {})
        level = int(player.get("level", 1))
        hp = int(player.get("hp", 10))
        inventory = player.get("inventory", [])
        risk = "high" if hp < 15 or level < 3 else ("medium" if hp < 40 else "low")
        needs_healing = hp < 30
        combat_ready = (level >= 3) and (hp >= 20) and any(x in inventory for x in ["sword", "bow"]) 
        stage = "early" if level < 5 else ("mid" if level < 10 else "late")
        return json.dumps({
            "risk": risk,
            "needs_healing": needs_healing,
            "combat_ready": combat_ready,
            "progression_stage": stage,
        })

    # Player behavior analyzer
    if "PlayerBehaviorAnalyzer" in prompt:
        beh = data.get("behavior", {})
        tends = beh.get("tendencies", {})
        risk_taking = float(tends.get("risk_taking", 0.5))
        exploration = float(tends.get("exploration", 0.5))
        caution = float(tends.get("caution", 0.5))
        recent = beh.get("recent_actions", [])
        if any("attack" in a for a in recent):
            risk_taking = min(1.0, risk_taking + 0.2)
        if any("sneak" in a for a in recent):
            caution = min(1.0, caution + 0.2)
        if any("explore" in a for a in recent):
            exploration = min(1.0, exploration + 0.2)
        summary = "assertive" if risk_taking > 0.7 else ("cautious" if caution > 0.7 else "balanced")
        return json.dumps({
            "risk_taking": round(risk_taking, 2),
            "exploration": round(exploration, 2),
            "caution": round(caution, 2),
            "summary": summary,
        })

    # World context reasoner
    if "WorldContextReasoner" in prompt:
        world = data.get("world", {})
        danger = world.get("danger_level", "medium")
        time = world.get("time", "day")
        environment_threat = danger
        is_night = str(time).lower() == "night"
        location = world.get("location", "unknown")
        hint = f"beware the {location}" if location != "unknown" else "stay alert"
        safe_action_suggestion = "stick to lit paths" if is_night else "stay near road"
        return json.dumps({
            "environment_threat": environment_threat,
            "is_night": is_night,
            "location_hint": hint,
            "safe_action_suggestion": safe_action_suggestion,
        })

    # Story goal tracker
    if "StoryGoalTracker" in prompt:
        s = data.get("story", {})
        active = s.get("active_objective")
        ignored = int(s.get("ignored_mainline_seconds", 0))
        state = s.get("objective_state", "in_progress")
        reminder = None
        if state in ("not_started", "in_progress") and ignored > 120:
            reminder = f"Main quest: {active}" if active else "Return to the main path"
        return json.dumps({
            "objective_reminder": reminder,
            "is_blocked": state == "blocked",
            "time_off_mainline": ignored,
        })

    # Memory agent
    if "MemoryAgent" in prompt:
        m = data.get("memory", {})
        episodic = m.get("episodic_notes", [])
        semantic = m.get("semantic_summaries", [])
        dont_repeat = ["avoid repeating last hint"] if episodic[-1:] else []
        reminders = semantic[:2]
        return json.dumps({"reminders": reminders, "dont_repeat": dont_repeat})

    # Priority manager
    if "PriorityManager" in prompt:
        analyses = data.get("analyses", {})
        pa = analyses.get("player", {})
        wa = analyses.get("world", {})
        sa = analyses.get("story", {})
        urgency = "low"
        if wa.get("environment_threat") == "high" or pa.get("risk") == "high":
            urgency = "high"
        if sa.get("time_off_mainline", 0) > 300 and urgency != "high":
            urgency = "medium"

        priorities: List[str] = []
        if urgency == "high":
            priorities.append("safety")
        if sa.get("objective_reminder"):
            priorities.append("story_progression")

        chosen_priority = priorities[0] if priorities else "silence"

        return json.dumps({
            "urgency_level": urgency,
            "top_priorities": priorities[:3],
            "chosen_priority": chosen_priority
        })

    # Intervention controller
    if "InterventionController" in prompt:
        urgency = data.get("urgency_level", "low")
        cooldown = int(data.get("cooldown_seconds", 0))
        intervene = urgency in ("high", "critical") or cooldown > 30
        brevity = "short" if urgency in ("high", "critical") else ("normal" if urgency == "medium" else "long")
        style = "protective" if urgency in ("high", "critical") else ("gentle" if urgency == "medium" else "minimal")
        return json.dumps({
            "intervene_now": intervene,
            "brevity": brevity,
            "style": style
        })

    # Intent planner
    if "GuideIntentPlanner" in prompt:
            pa = data.get("player_analysis", {})
            ba = data.get("behavior_analysis", {})
            wa = data.get("world_analysis", {})
            sa = data.get("story_analysis", {})
            ma = data.get("memory_analysis", {})
            npc = data.get("npc", {})
            intent = "hint"
            if wa.get("environment_threat") == "high" or pa.get("risk") == "high":
                intent = "warn"
            elif sa.get("objective_reminder") and sa.get("time_off_mainline", 0) > 300:
                intent = "nudge"
            elif pa.get("combat_ready") and (ma.get("reminders") or ba.get("exploration", 0) > 0.6):
                intent = "coach"
            rationale = "Guide-style intent chosen from safety, story, and behavior signals."
            return json.dumps({"intent": intent, "rationale": rationale})

    # Dialogue + action generator
    if "DialogueEmotionActionGenerator" in prompt:
        npc= data.get("npc", {})
        intent = data.get("intent", "hint")
        world_summary = data.get("world_analysis", {})
        name = npc.get("name", "Companion")
        emotion = "calm"
        action = "idle"
        dialogue = "I'm here."
        guidance = "Stay alert."

        if intent == "warn":
            dialogue = "Careful—this area is dangerous."
            guidance = "Stick to the lit path and avoid the treeline."
            emotion = "concerned"
            action = "gesture_warning"
            if world_summary.get("is_night"):
                action = "point_to_safe_path"
        elif intent == "nudge":
            dialogue = "We’ve wandered a while—shall we return to the goal?"
            guidance = "Head east toward the watchtower marker."
            emotion = "stern"
            action = "beckon_forward"
        elif intent == "coach":
            dialogue = "Nice form. Try spacing attacks and watch your stamina."
            guidance = "Time your strikes and back off when low on stamina."
            emotion = "cheerful"
            action = "demonstrate_move"
        elif intent == "encourage":
            dialogue = "You’ve got this. One careful step at a time."
            guidance = "Keep to cover and advance between safe spots."
            emotion = "cheerful"
            action = "thumbs_up"
        elif intent == "reassure":
            dialogue = "It’s fine—we can take a breath and plan."
            guidance = "Open the map and mark a safe route."
            emotion = "calm"
            action = "soothe_gesture"
        elif intent == "lore_comment":
            dialogue = "These stones mark an old border—travelers kept to the road."
            guidance = "Follow road markers to avoid ambush points."
            emotion = "neutral"
            action = "point_marker"
        else:  # hint default
            dialogue = "If we follow the old road, we’ll avoid most trouble."
            guidance = "Follow the old road east."
            emotion = "calm"
            action = "point_path"

        return json.dumps({
            "dialogue": dialogue,
            "emotion": emotion,
            "action": action,
            "guidance": guidance
        })

    # Consistency critic
    if "SelfCriticConsistencyAgent" in prompt or "ConsistencyCritic" in prompt:
        try:
            resp = data.get("response", {})
            intent = data.get("intent", "casual")
            npc = data.get("npc", {})
            allowed_emotions = {"calm", "concerned", "stern", "cheerful", "neutral"}
            if resp.get("emotion") not in allowed_emotions:
                resp["emotion"] = "concerned" if "warn" in intent else "neutral"
            final = {
                "intent": intent,
                "dialogue": resp.get("dialogue", ""),
                "emotion": resp.get("emotion", "neutral"),
                "action": resp.get("action", "idle"),
                "guidance": resp.get("guidance", "Stay alert."),
            }
            if resp.get("quest"):
                final["quest"] = resp["quest"]
            return json.dumps(final)
        except Exception:
            return json.dumps({
                "intent": "casual",
                "dialogue": "Safe travels.",
                "emotion": "neutral",
                "action": "nod",
                "guidance": "Keep to the road.",
            })

    return "{}"


# ---------- Sub-agent wrappers ----------

def _run_subagent(name: str, prompt: str, user_payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    user_json = json.dumps(user_payload)
    text, mode = run_llm_system_prompt(prompt, user_json)
    try:
        data = json.loads(text)
    except Exception:
        data = {}
    log_record = {
        "event": "subagent_result",
        "agent": name,
        "mode": mode,
        "input": user_payload,
        "output": data,
    }
    logger.info(json.dumps(log_record))
    return data, mode


# ---------- Pipeline Orchestrator ----------

def analyze_player(payload: InputPayload) -> Tuple[PlayerAnalysis, Dict[str, Any]]:
    data, mode = _run_subagent(
        "PlayerStateAnalyzer",
        PLAYER_ANALYZER_PROMPT,
        {"player": payload.player.__dict__},
    )
    pa = PlayerAnalysis(
        risk=data.get("risk", "medium"),
        needs_healing=bool(data.get("needs_healing", False)),
        combat_ready=bool(data.get("combat_ready", False)),
        progression_stage=data.get("progression_stage", "early"),
    )
    trace = {"agent": "PlayerStateAnalyzer", "mode": mode, "output": data}
    return pa, trace


def analyze_behavior(payload: InputPayload) -> Tuple[BehaviorAnalysis, Dict[str, Any]]:
    data, mode = _run_subagent(
        "PlayerBehaviorAnalyzer",
        BEHAVIOR_ANALYZER_PROMPT,
        {"behavior": payload.behavior.__dict__},
    )
    ba = BehaviorAnalysis(
        risk_taking=float(data.get("risk_taking", 0.5)),
        exploration=float(data.get("exploration", 0.5)),
        caution=float(data.get("caution", 0.5)),
        summary=str(data.get("summary", "balanced")),
    )
    trace = {"agent": "PlayerBehaviorAnalyzer", "mode": mode, "output": data}
    return ba, trace


def analyze_world(payload: InputPayload) -> Tuple[WorldAnalysis, Dict[str, Any]]:
    data, mode = _run_subagent(
        "WorldContextReasoner",
        WORLD_CONTEXT_PROMPT,
        {"world": payload.world.__dict__, "npc": payload.npc.__dict__},
    )
    wa = WorldAnalysis(
        environment_threat=data.get("environment_threat", "medium"),
        is_night=bool(data.get("is_night", False)),
        location_hint=data.get("location_hint", ""),
        safe_action_suggestion=data.get("safe_action_suggestion", ""),
    )
    trace = {"agent": "WorldContextReasoner", "mode": mode, "output": data}
    return wa, trace


def analyze_story(payload: InputPayload) -> Tuple[StoryAnalysis, Dict[str, Any]]:
    data, mode = _run_subagent(
        "StoryGoalTracker",
        STORY_TRACKER_PROMPT,
        {"story": payload.story.__dict__},
    )
    sa = StoryAnalysis(
        objective_reminder=data.get("objective_reminder"),
        is_blocked=bool(data.get("is_blocked", False)),
        time_off_mainline=int(data.get("time_off_mainline", 0)),
    )
    trace = {"agent": "StoryGoalTracker", "mode": mode, "output": data}
    return sa, trace


def analyze_memory(payload: InputPayload) -> Tuple[MemoryAnalysis, Dict[str, Any]]:
    data, mode = _run_subagent(
        "MemoryAgent",
        MEMORY_AGENT_PROMPT,
        {"memory": payload.memory.__dict__},
    )
    ma = MemoryAnalysis(
        reminders=list(data.get("reminders", [])),
        dont_repeat=list(data.get("dont_repeat", [])),
    )
    trace = {"agent": "MemoryAgent", "mode": mode, "output": data}
    return ma, trace


def prioritize(payload: InputPayload, pa: PlayerAnalysis, ba: BehaviorAnalysis, wa: WorldAnalysis, sa: StoryAnalysis, ma: MemoryAnalysis) -> Tuple[PriorityDecision, Dict[str, Any]]:
    data, mode = _run_subagent(
        "PriorityManager",
        PRIORITY_MANAGER_PROMPT,
        {"analyses": {"player": pa.__dict__, "behavior": ba.__dict__, "world": wa.__dict__, "story": sa.__dict__, "memory": ma.__dict__}},
    )
    pd = PriorityDecision(
        urgency_level=str(data.get("urgency_level", "low")),
        chosen_priority=str(data.get("chosen_priority", "silence")),
        top_priorities=list(data.get("top_priorities", [])),
    )
    trace = {"agent": "PriorityManager", "mode": mode, "output": data}
    return pd, trace


def control_intervention(pd: PriorityDecision, payload: InputPayload) -> Tuple[InterventionDecision, Dict[str, Any]]:
    data, mode = _run_subagent(
        "InterventionController",
        INTERVENTION_CONTROLLER_PROMPT,
        {"urgency_level": pd.urgency_level, "cooldown_seconds": payload.dialogue.seconds_since_last_npc},
    )
    ic = InterventionDecision(
        intervene_now=bool(data.get("intervene_now", False)),
        brevity=str(data.get("brevity", "normal")),
        style=str(data.get("style", "gentle")),
    )
    trace = {"agent": "InterventionController", "mode": mode, "output": data}
    return ic, trace

def plan_intent(payload: InputPayload, pa: PlayerAnalysis, ba: BehaviorAnalysis, wa: WorldAnalysis, sa: StoryAnalysis, ma: MemoryAnalysis) -> Tuple[NPCIntent, Dict[str, Any]]:
    data, mode = _run_subagent(
        "GuideIntentPlanner",
        GUIDE_INTENT_PLANNER_PROMPT,
        {"player_analysis": pa.__dict__, "behavior_analysis": ba.__dict__, "world_analysis": wa.__dict__, "story_analysis": sa.__dict__, "memory_analysis": ma.__dict__, "npc": payload.npc.__dict__},
    )
    intent = NPCIntent(
        intent=data.get("intent", "casual"),
        rationale=data.get("rationale", ""),
    )
    trace = {"agent": "GuideIntentPlanner", "mode": mode, "output": data}
    return intent, trace


def generate_dialogue_action(payload: InputPayload, pa: PlayerAnalysis, ba: BehaviorAnalysis, wa: WorldAnalysis, sa: StoryAnalysis, ma: MemoryAnalysis, intent: NPCIntent) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    data, mode = _run_subagent(
        "DialogueEmotionActionGenerator",
        DIALOGUE_EMOTION_ACTION_PROMPT,
        {
            "npc": payload.npc.__dict__,
            "player_analysis": pa.__dict__,
            "behavior_analysis": ba.__dict__,
            "world_analysis": wa.__dict__,
            "story_analysis": sa.__dict__,
            "memory_analysis": ma.__dict__,
            "intent": intent.intent,
        },
    )
    trace = {"agent": "DialogueEmotionActionGenerator", "mode": mode, "output": data}
    return data, trace


def critique_and_finalize(payload: InputPayload, intent: NPCIntent, response: Dict[str, Any], pd: PriorityDecision, sa: StoryAnalysis) -> Tuple[NPCResponse, Dict[str, Any]]:
    data, mode = _run_subagent(
        "SelfCriticConsistencyAgent",
        SELF_CRITIC_CONSISTENCY_PROMPT,
        {
            "npc": payload.npc.__dict__,
            "intent": intent.intent,
            "response": response,
            "player": payload.player.__dict__,
            "world": payload.world.__dict__,
        },
    )
    final = NPCResponse(
        intent=data.get("intent", intent.intent),
        dialogue=data.get("dialogue", ""),
        emotion=data.get("emotion", "neutral"),
        action=data.get("action", "idle"),
        guidance=data.get("guidance", "Stay alert."),
        urgency_level=pd.urgency_level,
        objective_reminder=sa.objective_reminder,
    )
    trace = {"agent": "SelfCriticConsistencyAgent", "mode": mode, "output": data}
    return final, trace


def run_pipeline(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Explicit multi-agent pipeline producing a structured NPC response."""
    payload = InputPayload.from_dict(input_dict)

    reasoning_trace: List[Dict[str, Any]] = []

    # 1) Analyze player state
    pa, t1 = analyze_player(payload)
    reasoning_trace.append(t1)

    # 2) Analyze behavior
    ba, t2 = analyze_behavior(payload)
    reasoning_trace.append(t2)

    # 3) Analyze world
    wa, t3 = analyze_world(payload)
    reasoning_trace.append(t3)

    # 4) Track story
    sa, t4 = analyze_story(payload)
    reasoning_trace.append(t4)

    # 5) Memory agent
    ma, t5 = analyze_memory(payload)
    reasoning_trace.append(t5)

    # 6) Prioritize
    pd, t6 = prioritize(payload, pa, ba, wa, sa, ma)
    reasoning_trace.append(t6)

    # 7) Intervention control
    ic, t7 = control_intervention(pd, payload)
    reasoning_trace.append(t7)

    # 8) Plan intent
    intent, t8 = plan_intent(payload, pa, ba, wa, sa, ma)
    reasoning_trace.append(t8)

    # 9) Generate dialogue/action
    draft, t9 = generate_dialogue_action(payload, pa, ba, wa, sa, ma, intent)
    reasoning_trace.append(t9)

    # 10) Critique and finalize
    final, t10 = critique_and_finalize(payload, intent, draft, pd, sa)
    reasoning_trace.append(t10)

    # 11) Return final JSON with reasoning trace
    final.reasoning_trace = reasoning_trace
    return final.to_dict()
