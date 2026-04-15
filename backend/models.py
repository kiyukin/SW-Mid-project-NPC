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
class World:
    location: str
    time: str  # e.g., "day", "night"
    danger_level: str  # e.g., "low", "medium", "high"


@dataclass
class NPC:
    name: str
    role: str  # e.g., healer, merchant, guard
    personality: str  # short descriptor
    relationship: str  # e.g., friendly, neutral, hostile


@dataclass
class InputPayload:
    player: Player
    world: World
    npc: NPC

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "InputPayload":
        p = data.get("player", {})
        w = data.get("world", {})
        n = data.get("npc", {})
        player = Player(
            level=int(p.get("level", 1)),
            hp=int(p.get("hp", 1)),
            inventory=list(p.get("inventory", [])),
            completed_quests=list(p.get("completed_quests", [])),
        )
        world = World(
            location=str(w.get("location", "unknown")),
            time=str(w.get("time", "day")),
            danger_level=str(w.get("danger_level", "medium")),
        )
        npc = NPC(
            name=str(n.get("name", "NPC")),
            role=str(n.get("role", "villager")),
            personality=str(n.get("personality", "neutral")),
            relationship=str(n.get("relationship", "neutral")),
        )
        return InputPayload(player=player, world=world, npc=npc)


# ---------- Intermediate Reasoning Artifacts ----------

@dataclass
class PlayerAnalysis:
    risk: str  # low/medium/high
    needs_healing: bool
    combat_ready: bool
    progression_stage: str  # early/mid/late


@dataclass
class WorldAnalysis:
    environment_threat: str  # low/medium/high
    is_night: bool
    location_hint: str  # short descriptor
    safe_action_suggestion: str


@dataclass
class NPCIntent:
    intent: str  # e.g., warn, offer_quest, hint, trade, casual, warn_and_offer_quest
    rationale: str


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
    quest: Optional[Quest] = None
    reasoning_trace: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "intent": self.intent,
            "dialogue": self.dialogue,
            "emotion": self.emotion,
            "action": self.action,
        }
        if self.quest:
            out["quest"] = {
                "title": self.quest.title,
                "objective": self.quest.objective,
                "reward": self.quest.reward,
            }
        if self.reasoning_trace is not None:
            out["reasoning_trace"] = self.reasoning_trace
        return out
