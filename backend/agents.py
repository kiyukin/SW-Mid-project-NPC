from __future__ import annotations

import json
from typing import Dict, Any, Tuple, List
import logging

from .models import (
    InputPayload,
    PlayerAnalysis,
    WorldAnalysis,
    NPCIntent,
    NPCResponse,
    Quest,
)
from .prompts import (
    PLAYER_ANALYZER_PROMPT,
    WORLD_CONTEXT_PROMPT,
    INTENT_PLANNER_PROMPT,
    DIALOGUE_ACTION_PROMPT,
    CONSISTENCY_CRITIC_PROMPT,
)

# Logger for structured outputs
logger = logging.getLogger("npc_backend")

# DeepAgents availability check
try:
    from deepagents_cli.llm import chat_completion  # type: ignore
    DEEPAGENTS_AVAILABLE = True
except Exception:  # pragma: no cover
    chat_completion = None  # type: ignore
    DEEPAGENTS_AVAILABLE = False
    print("[NPC Backend] DeepAgents not found; heuristic fallback mode ACTIVE.")


def run_with_deepagents(prompt: str, user_content: str) -> str:
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]
    # model and provider are read from DeepAgents config/environment
    result = chat_completion(messages=messages, model=None)  # type: ignore
    return result.get("content", "{}")


def run_with_heuristic(prompt: str, user_content: str) -> str:
    return heuristic_response(prompt, user_content)


def run_llm_system_prompt(prompt: str, user_content: str) -> Tuple[str, str]:
    """Return (assistant_text, mode) where mode in {"deepagents", "heuristic"}."""
    if DEEPAGENTS_AVAILABLE:
        try:
            return run_with_deepagents(prompt, user_content), "deepagents"
        except Exception:
            # Safety net: fall back if runtime call fails
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

    if "WorldContextReasoner" in prompt:
        world = data.get("world", {})
        danger = world.get("danger_level", "medium")
        time = world.get("time", "day")
        environment_threat = danger
        is_night = time.lower() == "night"
        location = world.get("location", "unknown")
        hint = f"beware the {location}" if location != "unknown" else "stay alert"
        safe_action_suggestion = "stick to lit paths" if is_night else "stay near road"
        return json.dumps({
            "environment_threat": environment_threat,
            "is_night": is_night,
            "location_hint": hint,
            "safe_action_suggestion": safe_action_suggestion,
        })

    if "NPCIntentPlanner" in prompt:
        pa = data.get("player_analysis", {})
        wa = data.get("world_analysis", {})
        npc = data.get("npc", {})
        intent = "casual"
        if wa.get("environment_threat") == "high" or pa.get("risk") == "high":
            intent = "warn"
            if pa.get("needs_healing") and npc.get("role") == "healer":
                intent = "warn_and_offer_quest"
        elif not pa.get("combat_ready", False):
            intent = "hint"
        elif npc.get("role") == "merchant":
            intent = "trade"
        rationale = "Chosen based on risk, NPC role, and readiness."
        return json.dumps({"intent": intent, "rationale": rationale})

    if "DialogueActionGenerator" in prompt:
        npc = data.get("npc", {})
        intent = data.get("intent", "casual")
        world_summary = data.get("world_analysis", {})
        pa = data.get("player_analysis", {})
        name = npc.get("name", "NPC")
        role = npc.get("role", "villager")
        emotion = "calm"
        action = "idle"
        dialogue = f"Greetings."
        quest = None
        if intent in ("warn", "warn_and_hint", "warn_and_offer_quest"):
            dialogue = "These parts are perilous. Tread carefully."
            emotion = "concerned"
            action = "gesture_warning"
            if world_summary.get("is_night"):
                action = "point_to_safe_path"
        if intent in ("hint", "warn_and_hint"):
            dialogue = dialogue + " Follow the old road; it is safer." if dialogue else "Follow the old road; it is safer."
        if intent in ("offer_quest", "warn_and_offer_quest") and role == "healer":
            dialogue = "Night brings danger. Bring me three fresh herbs and I shall brew medicine for you."
            quest = {
                "title": "Herbs for Survival",
                "objective": "Collect 3 herbs near the village",
                "reward": "healing_potion",
            }
        if intent == "trade" and role == "merchant":
            dialogue = "Looking for supplies? I have what you need for the road."
            emotion = "neutral"
            action = "open_trade_menu"
        if intent == "casual":
            dialogue = f"Good day. I am {name}. The weather holds, for now."
            emotion = "cheerful"
            action = "nod"
        return json.dumps({
            "dialogue": dialogue,
            "emotion": emotion,
            "action": action,
            "quest": quest,
        })

    if "ConsistencyCritic" in prompt:
        try:
            resp = data.get("response", {})
            intent = data.get("intent", "casual")
            npc = data.get("npc", {})
            # Minimal adjustments: ensure quest only when provided
            if intent == "warn_and_offer_quest" and not resp.get("quest") and npc.get("role") == "healer":
                resp["quest"] = {
                    "title": "Herbs for Survival",
                    "objective": "Collect 3 herbs near the village",
                    "reward": "healing_potion",
                }
            # Clamp emotion set
            allowed_emotions = {"calm", "concerned", "stern", "cheerful", "neutral"}
            if resp.get("emotion") not in allowed_emotions:
                resp["emotion"] = "concerned" if "warn" in intent else "neutral"
            # Ensure keys exist
            final = {
                "intent": intent,
                "dialogue": resp.get("dialogue", ""),
                "emotion": resp.get("emotion", "neutral"),
                "action": resp.get("action", "idle"),
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


def plan_intent(payload: InputPayload, pa: PlayerAnalysis, wa: WorldAnalysis) -> Tuple[NPCIntent, Dict[str, Any]]:
    data, mode = _run_subagent(
        "NPCIntentPlanner",
        INTENT_PLANNER_PROMPT,
        {"player_analysis": pa.__dict__, "world_analysis": wa.__dict__, "npc": payload.npc.__dict__},
    )
    intent = NPCIntent(
        intent=data.get("intent", "casual"),
        rationale=data.get("rationale", ""),
    )
    trace = {"agent": "NPCIntentPlanner", "mode": mode, "output": data}
    return intent, trace


def generate_dialogue_action(payload: InputPayload, pa: PlayerAnalysis, wa: WorldAnalysis, intent: NPCIntent) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    data, mode = _run_subagent(
        "DialogueActionGenerator",
        DIALOGUE_ACTION_PROMPT,
        {
            "npc": payload.npc.__dict__,
            "player_analysis": pa.__dict__,
            "world_analysis": wa.__dict__,
            "intent": intent.intent,
        },
    )
    trace = {"agent": "DialogueActionGenerator", "mode": mode, "output": data}
    return data, trace


def critique_and_finalize(payload: InputPayload, intent: NPCIntent, response: Dict[str, Any]) -> Tuple[NPCResponse, Dict[str, Any]]:
    data, mode = _run_subagent(
        "ConsistencyCritic",
        CONSISTENCY_CRITIC_PROMPT,
        {
            "npc": payload.npc.__dict__,
            "intent": intent.intent,
            "response": response,
            "player": payload.player.__dict__,
            "world": payload.world.__dict__,
        },
    )
    quest = None
    if "quest" in data and data["quest"]:
        q = data["quest"]
        quest = Quest(title=q.get("title", ""), objective=q.get("objective", ""), reward=q.get("reward", ""))
    final = NPCResponse(
        intent=data.get("intent", "casual"),
        dialogue=data.get("dialogue", ""),
        emotion=data.get("emotion", "neutral"),
        action=data.get("action", "idle"),
        quest=quest,
    )
    trace = {"agent": "ConsistencyCritic", "mode": mode, "output": data}
    return final, trace


def run_pipeline(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Explicit 5-step multi-agent pipeline producing a structured NPC response."""
    payload = InputPayload.from_dict(input_dict)

    reasoning_trace: List[Dict[str, Any]] = []

    # 1) Analyze player state
    pa, t1 = analyze_player(payload)
    reasoning_trace.append(t1)

    # 2) Analyze world/NPC context
    wa, t2 = analyze_world(payload)
    reasoning_trace.append(t2)

    # 3) Decide NPC intent
    intent, t3 = plan_intent(payload, pa, wa)
    reasoning_trace.append(t3)

    # 4) Generate dialogue/action/quest
    draft, t4 = generate_dialogue_action(payload, pa, wa, intent)
    reasoning_trace.append(t4)

    # 5) Critique and refine final result
    final, t5 = critique_and_finalize(payload, intent, draft)
    reasoning_trace.append(t5)

    # 6) Return final JSON with reasoning trace
    final.reasoning_trace = reasoning_trace
    return final.to_dict()
