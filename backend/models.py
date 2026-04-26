from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# ---------- Input Schemas ----------

@dataclass
class Player:
    level: int
    hp: int
    inventory: List[str] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)


@dataclass
class Behavior:
    recent_actions: List[str] = field(default_factory=list)
    tendencies: Dict[str, float] = field(default_factory=dict)  # e.g., risk_taking, exploration


@dataclass
class World:
    location: str
    time: str  # e.g., "day", "night"
    danger_level: str  # e.g., "low", "medium", "high"


@dataclass
class Story:
    chapter: str
    active_objective: str
    objective_state: str  # not_started|in_progress|blocked|done
    ignored_mainline_seconds: int = 0


@dataclass
class Dialogue:
    last_npc_lines: List[str] = field(default_factory=list)
    last_player_lines: List[str] = field(default_factory=list)
    seconds_since_last_npc: int = 0


@dataclass
class Memory:
    episodic_notes: List[str] = field(default_factory=list)
    semantic_summaries: List[str] = field(default_factory=list)


@dataclass
class NPC:
    name: str
    role: str  # e.g., healer, merchant, guard
    personality: str  # short descriptor
    relationship: str  # e.g., friendly, neutral, hostile


@dataclass
class InputPayload:
    player: Player
    behavior: Behavior
    world: World
    story: Story
    dialogue: Dialogue
    memory: Memory
    npc: NPC

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "InputPayload":
        p = data.get("player", {})
        b = data.get("behavior", {})
        w = data.get("world", {})
        s = data.get("story", {})
        d = data.get("dialogue", {})
        m = data.get("memory", {})
        n = data.get("npc", {})
        player = Player(
            level=int(p.get("level", 1)),
            hp=int(p.get("hp", 1)),
            inventory=list(p.get("inventory", [])),
            completed_quests=list(p.get("completed_quests", [])),
        )
        behavior = Behavior(
            recent_actions=list(b.get("recent_actions", [])),
            tendencies=dict(b.get("tendencies", {})),
        )
        world = World(
            location=str(w.get("location", "unknown")),
            time=str(w.get("time", "day")),
            danger_level=str(w.get("danger_level", "medium")),
        )
        story = Story(
            chapter=str(s.get("chapter", "prologue")),
            active_objective=str(s.get("active_objective", "")),
            objective_state=str(s.get("objective_state", "in_progress")),
            ignored_mainline_seconds=int(s.get("ignored_mainline_seconds", 0)),
        )
        dialogue = Dialogue(
            last_npc_lines=list(d.get("last_npc_lines", [])),
            last_player_lines=list(d.get("last_player_lines", [])),
            seconds_since_last_npc=int(d.get("seconds_since_last_npc", 0)),
        )
        memory = Memory(
            episodic_notes=list(m.get("episodic_notes", [])),
            semantic_summaries=list(m.get("semantic_summaries", [])),
        )
        npc = NPC(
            name=str(n.get("name", "NPC")),
            role=str(n.get("role", "villager")),
            personality=str(n.get("personality", "neutral")),
            relationship=str(n.get("relationship", "neutral")),
        )
        return InputPayload(
            player=player,
            behavior=behavior,
            world=world,
            story=story,
            dialogue=dialogue,
            memory=memory,
            npc=npc,
        )


# ---------- Intermediate Reasoning Artifacts ----------

@dataclass
class PlayerAnalysis:
    risk: str  # low/medium/high
    needs_healing: bool
    combat_ready: bool
    progression_stage: str  # early/mid/late


@dataclass
class BehaviorAnalysis:
    risk_taking: float
    exploration: float
    caution: float
    summary: str


@dataclass
class WorldAnalysis:
    environment_threat: str  # low/medium/high
    is_night: bool
    location_hint: str  # short descriptor
    safe_action_suggestion: str


@dataclass
class StoryAnalysis:
    objective_reminder: Optional[str]
    is_blocked: bool
    time_off_mainline: int


@dataclass
class MemoryAnalysis:
    reminders: List[str] = field(default_factory=list)
    dont_repeat: List[str] = field(default_factory=list)


@dataclass
class NPCIntent:
    intent: str  # e.g., warn, hint, coach, encourage, nudge, reassure, celebrate, lore_comment
    rationale: str


@dataclass
class PriorityDecision:
    urgency_level: str  # low|medium|high|critical
    top_priorities: List[str]


@dataclass
class InterventionDecision:
    intervene_now: bool
    brevity: str  # short|normal|long


# ---------- Output Schemas ----------

@dataclass
class Quest:
    title: str
    objective: str
    reward: str


@dataclass
class NPCResponse:
    intent: str
    dialogue: str
    emotion: str
    action: str
    guidance: str
    urgency_level: str
    objective_reminder: Optional[str] = None
    quest: Optional[Quest] = None
    reasoning_trace: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "intent": self.intent,
            "dialogue": self.dialogue,
            "emotion": self.emotion,
            "action": self.action,
            "guidance": self.guidance,
            "urgency_level": self.urgency_level,
        }
        if self.objective_reminder:
            out["objective_reminder"] = self.objective_reminder
        if self.quest:
            out["quest"] = {
                "title": self.quest.title,
                "objective": self.quest.objective,
                "reward": self.quest.reward,
            }
        if self.reasoning_trace is not None:
            out["reasoning_trace"] = self.reasoning_trace
        return out
