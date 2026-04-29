# backend/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import json
import enum
import datetime

# Enum for consistency and clarity
class UrgencyLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Emotion(enum.Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISED = "surprised"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    BORED = "bored"
    SATISFIED = "satisfied"

class InterventionType(enum.Enum):
    WARN = "warn"
    HINT = "hint"
    COACH = "coach"
    ENCOURAGE = "encourage"
    NUDGE = "nudge"
    REASSURE = "reassure"
    CELEBRATE = "celebrate"
    LORE_COMMENT = "lore_comment"
    CRITICAL_ALERT = "critical_alert"

# ---------- Input Schemas (Enhanced) ----------

@dataclass
class Player:
    level: int
    hp: int
    inventory: List = field(default_factory=list)
    completed_quests: List = field(default_factory=list)
    # 2.1 행동 패턴 분석: 플레이어의 플레이 스타일을 나타내는 지표
    play_style_tendencies: Dict = field(default_factory=dict) # e.g., {"risk_taking": 0.7, "exploration": 0.5}
    # 2.1 행동 패턴 분석: 선호하는 퀘스트 유형이나 아이템 카테고리
    preferred_quests: List = field(default_factory=list)
    preferred_items: List = field(default_factory=list)

@dataclass
class Behavior:
    recent_actions: List = field(default_factory=list)
    tendencies: Dict = field(default_factory=dict)  # e.g., risk_taking, exploration

@dataclass
class World:
    location: str
    time: str  # e.g., "day", "night"
    danger_level: str  # e.g., "low", "medium", "high"
    # Additional context for LLM reasoning
    nearby_entities: List = field(default_factory=list)
    environmental_hazards: List = field(default_factory=list)

@dataclass
class Story:
    chapter: str
    active_objective: str
    objective_state: str  # not_started|in_progress|blocked|done
    ignored_mainline_seconds: int = 0
    # Current story events that might influence NPC behavior
    current_events: List = field(default_factory=list)

@dataclass
class Dialogue:
    last_npc_lines: List = field(default_factory=list)
    last_player_lines: List = field(default_factory=list)
    seconds_since_last_npc: int = 0
    # Sentiment of the last player utterance
    last_player_sentiment: Optional[str] = None # e.g., "positive", "negative", "neutral"

@dataclass
class MemoryEntry:
    content: str
    timestamp: datetime.datetime
    importance: float = 0.5 # Salience for retrieval and forgetting
    emotion_tag: Optional[Emotion] = None # Emotion associated with this memory
    source_entity: Optional[str] = None # Who or what generated this memory

@dataclass
class Memory:
    short_term_memories: List[str] = field(default_factory=list)
    episodic_notes: List[str] = field(default_factory=list)
    semantic_summaries: List[str] = field(default_factory=list)
    long_term_traits: List[str] = field(default_factory=list)
    long_term_facts: List[str] = field(default_factory=list)
    experiential_strategies: List[str] = field(default_factory=list)
    knowledge_graph_nodes: Dict[str, Any] = field(default_factory=dict)
    knowledge_graph_edges: List[Tuple[str, str, str]] = field(default_factory=list)

@dataclass
class NPC:
    name: str
    role: str  # e.g., healer, merchant, guard
    personality: str  # short descriptor
    relationship: str  # e.g., friendly, neutral, hostile
    # 6.1 기억 및 성격 기반 일관성 검사: NPC의 역할과 우선순위를 정의하는 자연어 설명
    personality_traits: str = "" # e.g., "나는 소방관 FireFighter1입니다. 나의 의무는 불을 끄고, 무엇보다 사람을 구하는 것입니다."
    current_mood: Emotion = Emotion.NEUTRAL # Current emotional state of the NPC

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
    def from_dict(data: Dict) -> "InputPayload":
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
            inventory=list(p.get("inventory",)),
            completed_quests=list(p.get("completed_quests",)),
            play_style_tendencies=dict(p.get("play_style_tendencies", {})),
            preferred_quests=list(p.get("preferred_quests",)),
            preferred_items=list(p.get("preferred_items",))
        )
        behavior = Behavior(
            recent_actions=list(b.get("recent_actions",)),
            tendencies=dict(b.get("tendencies", {})),
        )
        world = World(
            location=str(w.get("location", "unknown")),
            time=str(w.get("time", "day")),
            danger_level=str(w.get("danger_level", "medium")),
            nearby_entities=list(w.get("nearby_entities",)),
            environmental_hazards=list(w.get("environmental_hazards",))
        )
        story = Story(
            chapter=str(s.get("chapter", "prologue")),
            active_objective=str(s.get("active_objective", "")),
            objective_state=str(s.get("objective_state", "in_progress")),
            ignored_mainline_seconds=int(s.get("ignored_mainline_seconds", 0)),
            current_events=list(s.get("current_events",))
        )
        dialogue = Dialogue(
            last_npc_lines=list(d.get("last_npc_lines",)),
            last_player_lines=list(d.get("last_player_lines",)),
            seconds_since_last_npc=int(d.get("seconds_since_last_npc", 0)),
            last_player_sentiment=d.get("last_player_sentiment", None)
        )

        # Memory deserialization requires handling custom MemoryEntry
        def deserialize_memory_entry(entries: List[Dict]) -> List:
            return [
                MemoryEntry(
                    content=entry,
                    timestamp=datetime.datetime.fromisoformat(entry),
                    importance=entry.get("importance", 0.5),
                    emotion_tag=Emotion[entry.upper()] if entry.get("emotion_tag") else None,
                    source_entity=entry.get("source_entity")
                ) for entry in entries
            ]

        mem_data = m.get("episodic_notes",)
        episodic_notes = deserialize_memory_entry(mem_data) if mem_data else []

        mem_data = m.get("short_term_memories",)
        short_term_memories = deserialize_memory_entry(mem_data) if mem_data else []

        memory = Memory(
            short_term_memories=short_term_memories,
            episodic_notes=episodic_notes,
            semantic_summaries=list(m.get("semantic_summaries", [])),
            long_term_traits=list(m.get("long_term_traits", [])),
            long_term_facts=list(m.get("long_term_facts", [])),
            experiential_strategies=list(m.get("experiential_strategies", [])),
            knowledge_graph_nodes=dict(m.get("knowledge_graph_nodes", {})),
            knowledge_graph_edges=[tuple(edge) for edge in m.get("knowledge_graph_edges", [])],
        )
        npc = NPC(
            name=str(n.get("name", "NPC")),
            role=str(n.get("role", "villager")),
            personality=str(n.get("personality", "neutral")),
            relationship=str(n.get("relationship", "neutral")),
            personality_traits=str(n.get("personality_traits", "")),
            current_mood=Emotion
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

# ---------- Intermediate Reasoning Artifacts (Enhanced) ----------

@dataclass
class PlayerAnalysis:
    risk: str  # low/medium/high
    needs_healing: bool
    combat_ready: bool
    progression_stage: str  # early/mid/late
    # 2.2 감정 및 의도 추론
    current_emotion: Emotion # Player's inferred emotion
    inferred_intention: str # Player's inferred intention, e.g., 'explore', 'quest_complete'

@dataclass
class BehaviorAnalysis:
    risk_taking: float
    exploration: float
    caution: float
    summary: str
    # 2.1 행동 패턴 분석
    churn_risk_prediction: float # Probability of player churning
    engagement_metrics: Dict = field(default_factory=dict) # e.g., {"reaction_time": 0.5, "session_duration": 1200}

@dataclass
class WorldAnalysis:
    environment_threat: str  # low/medium/high
    is_night: bool
    location_hint: str  # short descriptor
    safe_action_suggestion: str
    # Broader context
    weather_condition: str = "clear"
    time_of_day_cycle: str = "day" # more granular than just "day" or "night"

@dataclass
class StoryAnalysis:
    objective_reminder: Optional[str] = None
    is_blocked: bool
    time_off_mainline: int
    # Strategic analysis of story elements
    story_progress_percentage: float = 0.0
    critical_path_divergence: bool = False

@dataclass
class MemoryAnalysis:
    reminders: List[str] = field(default_factory=list)
    dont_repeat: List[str] = field(default_factory=list)
    short_term: List[str] = field(default_factory=list)
    mid_term: List[str] = field(default_factory=list)
    long_term: List[str] = field(default_factory=list)
    conflicting_memories: List[str] = field(default_factory=list)
    pruning_candidates: List[str] = field(default_factory=list)


@dataclass
class NPCIntent:
    intent: str  # e.g., warn, hint, coach, encourage, nudge, reassure, celebrate, lore_comment, cautionary_restriction
    rationale: str


@dataclass
class PriorityDecision:
    urgency_level: str  # low|medium|high|critical
    chosen_priority: str  # survival|direction|story_progression|emotional_support|silence
    top_priorities: List[str]
    factors_considered: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
@dataclass
class InterventionDecision:
    intervene_now: bool
    style: str  # silent|short_hint|gentle_guide|strong_intervene|emotional_encourage
    brevity: str  # short|normal|long
    # 4.1 임계값 기반 개입 및 유형화
    intervention_type: InterventionType # Specific type of intervention
    intensity_level: float = 0.5 # Intensity of intervention (0.0 to 1.0)

@dataclass
class PlayerModel:
    explorer: float = 0.5
    direct_goal: float = 0.5
    risk_averse: float = 0.5
    story_avoidant: float = 0.5
    hint_friendly: float = 0.5
    hint_resistant: float = 0.5
    label: str = "balanced"


@dataclass
class ChoiceFilterResult:
    kept: List[str] = field(default_factory=list)
    rejected: List[str] = field(default_factory=list)
    rationale: str = ""


# ---------- Output Schemas ----------

@dataclass
class Quest:
    title: str
    objective: str
    reward: str
    # Additional quest details
    difficulty: str = "medium"
    recommended_level: int = 1

@dataclass
class ReasoningStep:
    step_number: int
    description: str
    input_data: Dict = field(default_factory=dict)
    output_decision: Dict = field(default_factory=dict)
    memories_accessed: List = field(default_factory=list)
    rules_applied: List = field(default_factory=list)
    # 6.1 기억 및 성격 기반 일관성 검사: 충돌 기록
    consistency_check_result: Optional[str] = None # e.g., "Consistent", "Conflicting: previous statement about X"

@dataclass
class NPCResponse:
    intent: InterventionType
    dialogue: str
    emotion: Emotion
    action: str
    guidance: str
    urgency_level: UrgencyLevel
    objective_reminder: Optional[str] = None
    quest: Optional[Quest] = None
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)
    player_feedback_reaction: Optional[str] = None
    outcome_evaluation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "intent": self.intent,
            "dialogue": self.dialogue,
            "emotion": self.emotion.value,
            "action": self.action,
            "guidance": self.guidance,
            "urgency_level": self.urgency_level.value,
        }
        if self.objective_reminder:
            out["objective_reminder"] = self.objective_reminder
        if self.quest:
            quest_out = {
                "title": self.quest.title,
                "objective": self.quest.objective,
                "reward": self.quest.reward,
            }
            if hasattr(self.quest, "difficulty"):
                quest_out["difficulty"] = self.quest.difficulty
            if hasattr(self.quest, "recommended_level"):
                quest_out["recommended_level"] = self.quest.recommended_level
            out["quest"] = quest_out

        if self.reasoning_trace:
            out["reasoning_trace"] = self.reasoning_trace

        if self.player_feedback_reaction:
            out["player_feedback_reaction"] = self.player_feedback_reaction

        if self.outcome_evaluation:
            out["outcome_evaluation"] = self.outcome_evaluation
        return out

# ---------- LLM Client (Mock-up) ----------
class LLMClient:
    """
    대규모 언어 모델(LLM)과의 상호작용을 시뮬레이션하는 목업 클라이언트입니다.
    실제 LLM API 호출은 이 클래스에서 이루어집니다.
    """
    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        # 실제 LLM API 호출 로직은 여기에 구현됩니다. (예: OpenAI, Claude, Gemini 등)
        # 현재는 단순한 목업 응답을 반환합니다.
        print(f"--- LLM Prompt --- \n{prompt}\n--- End Prompt ---")
        if "player_analysis" in prompt.lower() and "risk" in prompt.lower():
            return json.dumps({"risk": "medium", "needs_healing": False, "combat_ready": True, "progression_stage": "mid", "current_emotion": Emotion.NEUTRAL.value, "inferred_intention": "explore"})
        elif "npc_intent" in prompt.lower():
            return json.dumps({"intent": InterventionType.HINT.value, "rationale": "Player is exploring off the main path, a gentle hint about the objective might be useful."})
        elif "priority_decision" in prompt.lower():
            return json.dumps({"urgency_level": UrgencyLevel.MEDIUM.value, "top_priorities": [], "factors_considered": {"story_progression": 0.6}, "rationale": "Player has been ignoring the main quest for some time."})
        elif "dialogue_generation" in prompt.lower():
            return json.dumps({"dialogue": "음... 요즘 이곳을 탐험하는 사람이 거의 없었는데. 혹시 메인 퀘스트에 어려움이 있나?", "emotion": Emotion.CURIOUS.value, "action": "look_around", "guidance": "메인 퀘스트 진행을 위해 마을 지도 참고", "objective_reminder": "잃어버린 유물 찾기"})
        elif "memory_analysis" in prompt.lower():
            return json.dumps({"reminders": [], "dont_repeat": [], "conflicting_memories": [], "pruning_candidates": []})
        elif "consistency_check" in prompt.lower():
             return json.dumps({"consistency_check_result": "Consistent"})
        return "LLM mock response based on prompt."

# ---------- Core Reasoning Engine ----------

class NPCAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.reasoning_steps: List = [] # To store the reasoning trace for each turn
        self.step_counter = 0

    def _add_reasoning_step(self, description: str, input_data: Dict, output_decision: Dict,
                             memories_accessed: List = None, rules_applied: List = None,
                             consistency_check_result: Optional[str] = None):
        self.step_counter += 1
        self.reasoning_steps.append(   
            ReasoningStep(
                step_number=self.step_counter,
                description=description,
                input_data=input_data,
                output_decision=output_decision,
                memories_accessed=memories_accessed if memories_accessed is not None else [],
                rules_applied=rules_applied if rules_applied is not None else [],
                consistency_check_result=consistency_check_result
            )
        )

    def analyze_player(self, player: Player, behavior: Behavior, dialogue: Dialogue) -> PlayerAnalysis:
        # 2. 플레이어 모델링
        prompt = f"""
        Given the player's current state, recent behavior, and last dialogue, analyze their situation.
        Player Level: {player.level}, HP: {player.hp}
        Inventory: {player.inventory}
        Completed Quests: {player.completed_quests}
        Play Style Tendencies: {player.play_style_tendencies}
        Recent Actions: {behavior.recent_actions}
        Last Player Lines: {dialogue.last_player_lines}
        Last Player Sentiment: {dialogue.last_player_sentiment}

        Based on this, provide a PlayerAnalysis:
        - risk (low/medium/high)
        - needs_healing (bool)
        - combat_ready (bool)
        - progression_stage (early/mid/late)
        - current_emotion (e.g., {', '.join()})
        - inferred_intention (e.g., 'explore', 'quest_complete', 'interact_npc')

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        analysis_data = json.loads(response_json)
        analysis = PlayerAnalysis(
            risk=analysis_data.get("risk", "medium"),
            needs_healing=analysis_data.get("needs_healing", False),
            combat_ready=analysis_data.get("combat_ready", True),
            progression_stage=analysis_data.get("progression_stage", "mid"),
            current_emotion=Emotion,
            inferred_intention=analysis_data.get("inferred_intention", "unknown")
        )
        self._add_reasoning_step("Player Analysis", {"player": player.__dict__, "behavior": behavior.__dict__, "dialogue": dialogue.__dict__}, analysis.__dict__)
        return analysis

    def analyze_world(self, world: World) -> WorldAnalysis:
        prompt = f"""
        Analyze the current world state.
        Location: {world.location}, Time: {world.time}, Danger Level: {world.danger_level}
        Nearby Entities: {world.nearby_entities}
        Environmental Hazards: {world.environmental_hazards}

        Provide a WorldAnalysis:
        - environment_threat (low/medium/high)
        - is_night (bool)
        - location_hint (short descriptor)
        - safe_action_suggestion (e.g., 'stay_put', 'return_to_town', 'explore_cautiously')
        - weather_condition (e.g., 'clear', 'rainy', 'stormy')
        - time_of_day_cycle (e.g., 'dawn', 'morning', 'afternoon', 'dusk', 'night')

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        analysis_data = json.loads(response_json)
        analysis = WorldAnalysis(
            environment_threat=analysis_data.get("environment_threat", "medium"),
            is_night=analysis_data.get("is_night", False),
            location_hint=analysis_data.get("location_hint", "a quiet place"),
            safe_action_suggestion=analysis_data.get("safe_action_suggestion", "explore_cautiously"),
            weather_condition=analysis_data.get("weather_condition", "clear"),
            time_of_day_cycle=analysis_data.get("time_of_day_cycle", "day")
        )
        self._add_reasoning_step("World Analysis", {"world": world.__dict__}, analysis.__dict__)
        return analysis

    def analyze_story(self, story: Story) -> StoryAnalysis:
        prompt = f"""
        Analyze the current story progression.
        Chapter: {story.chapter}, Active Objective: {story.active_objective}, Objective State: {story.objective_state}
        Ignored Mainline Seconds: {story.ignored_mainline_seconds}
        Current Events: {story.current_events}

        Provide a StoryAnalysis:
        - objective_reminder (Optional)
        - is_blocked (bool)
        - time_off_mainline (int)
        - story_progress_percentage (float)
        - critical_path_divergence (bool)

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        analysis_data = json.loads(response_json)
        analysis = StoryAnalysis(
            objective_reminder=analysis_data.get("objective_reminder"),
            is_blocked=analysis_data.get("is_blocked", False),
            time_off_mainline=analysis_data.get("time_off_mainline", 0),
            story_progress_percentage=analysis_data.get("story_progress_percentage", 0.0),
            critical_path_divergence=analysis_data.get("critical_path_divergence", False)
        )
        self._add_reasoning_step("Story Analysis", {"story": story.__dict__}, analysis.__dict__)
        return analysis

    def analyze_memory(self, memory: Memory, player_analysis: PlayerAnalysis, world_analysis: WorldAnalysis) -> MemoryAnalysis:
        # 1.3 기억 업데이트 및 망각 메커니즘
        prompt = f"""
        Given the NPC's memory and current context, perform a memory analysis.
        Short-term memories: {memory.short_term_memories}
        Episodic notes: {memory.episodic_notes}
        Semantic summaries: {memory.semantic_summaries}
        Long-term facts: {memory.long_term_facts}
        Experiential strategies: {memory.experiential_strategies}
        Knowledge Graph Nodes (simplified): {memory.knowledge_graph_nodes}
        Knowledge Graph Edges (simplified): {memory.knowledge_graph_edges}
        Player's inferred emotion: {player_analysis.current_emotion.value}
        Current environment threat: {world_analysis.environment_threat}

        Identify:
        - reminders: What key memories should the NPC consider right now?
        - dont_repeat: What should the NPC avoid saying/doing based on past interactions?
        - conflicting_memories: Are there any memories that contradict each other or current reality?
        - pruning_candidates: Which memories are old or low importance and could be pruned or summarized?

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        analysis_data = json.loads(response_json)
        analysis = MemoryAnalysis(
            reminders=analysis_data.get("reminders",),
            dont_repeat=analysis_data.get("dont_repeat",),
            conflicting_memories=analysis_data.get("conflicting_memories",),
            pruning_candidates=analysis_data.get("pruning_candidates",)
        )
        self._add_reasoning_step("Memory Analysis", {"memory": memory.__dict__, "player_analysis": player_analysis.__dict__, "world_analysis": world_analysis.__dict__}, analysis.__dict__,
                                 memories_accessed= + memory.semantic_summaries + memory.long_term_facts)
        return analysis

    def determine_npc_intent(self, npc: NPC, player_analysis: PlayerAnalysis, world_analysis: WorldAnalysis,
                              story_analysis: StoryAnalysis, memory_analysis: MemoryAnalysis) -> NPCIntent:
        # NPC의 의도 결정
        prompt = f"""
        Based on the current situation and NPC's personality, what should {npc.name}'s primary intent be?
        NPC: {npc.name}, Role: {npc.role}, Personality: {npc.personality}, Relationship: {npc.relationship}
        NPC Personality Traits: {npc.personality_traits}
        NPC Current Mood: {npc.current_mood.value}

        Player Analysis: {player_analysis.__dict__}
        World Analysis: {world_analysis.__dict__}
        Story Analysis: {story_analysis.__dict__}
        Memory Reminders: {memory_analysis.reminders}
        Memory Don't Repeat: {memory_analysis.dont_repeat}

        Consider NPC's core duties and personality traits.
        Possible intents: {', '.join()}

        Provide an NPCIntent:
        - intent (one of the possible intents)
        - rationale (justification for the intent)

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        intent_data = json.loads(response_json)
        intent = NPCIntent(
            intent=InterventionType,
            rationale=intent_data.get("rationale", "No clear rationale.")
        )
        self._add_reasoning_step("NPC Intent Determination",
                                 {"npc": npc.__dict__, "player_analysis": player_analysis.__dict__, "world_analysis": world_analysis.__dict__, "story_analysis": story_analysis.__dict__, "memory_analysis": memory_analysis.__dict__},
                                 intent.__dict__)
        return intent

    def make_priority_decision(self, npc_intent: NPCIntent, player_analysis: PlayerAnalysis,
                               world_analysis: WorldAnalysis, story_analysis: StoryAnalysis) -> PriorityDecision:
        # 3. 더 강력한 우선순위 결정
        prompt = f"""
        Given the determined NPC intent and overall context, prioritize the NPC's actions.
        NPC Intent: {npc_intent.__dict__}
        Player Analysis: {player_analysis.__dict__}
        World Analysis: {world_analysis.__dict__}
        Story Analysis: {story_analysis.__dict__}

        Determine the PriorityDecision:
        - urgency_level (low/medium/high/critical)
        - top_priorities (List)
        - factors_considered (Dict) - Key factors and their relative weights
        - rationale (natural language explanation)

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        priority_data = json.loads(response_json)
        priority = PriorityDecision(
            urgency_level=UrgencyLevel(priority_data.get("urgency_level", UrgencyLevel.LOW.value)),
            top_priorities=priority_data.get("top_priorities", []),
            factors_considered=priority_data.get("factors_considered", {}),
            rationale=priority_data.get("rationale", "")
        )
        self._add_reasoning_step("Priority Decision",
                                 {"npc_intent": npc_intent.__dict__, "player_analysis": player_analysis.__dict__, "world_analysis": world_analysis.__dict__, "story_analysis": story_analysis.__dict__},
                                 priority.__dict__, rules_applied=[])
        return priority

    def decide_intervention(self, npc_intent: NPCIntent, priority_decision: PriorityDecision,
                            dialogue: Dialogue, player_analysis: PlayerAnalysis) -> InterventionDecision:
        # 4. 더 나은 개입 제어
        # Threshold-based intervention logic can be implemented here as rules or learned policy
        intervene = False
        brevity = "normal"
        intensity = 0.5

        if priority_decision.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            intervene = True
            brevity = "long" if priority_decision.urgency_level == UrgencyLevel.CRITICAL else "normal"
            intensity = 0.8 if priority_decision.urgency_level == UrgencyLevel.CRITICAL else 0.6
        elif npc_intent.intent == InterventionType.HINT and player_analysis.inferred_intention == "explore":
            if dialogue.seconds_since_last_npc > 60: # Avoid constant nagging
                intervene = True
                brevity = "short"
                intensity = 0.4

        prompt = f"""
        Given the NPC's intent ({npc_intent.intent.value}) and priority ({priority_decision.urgency_level.value}), decide if and how to intervene.
        Last NPC lines: {dialogue.last_npc_lines}
        Seconds since last NPC speech: {dialogue.seconds_since_last_npc}
        Player's current emotion: {player_analysis.current_emotion.value}
        Player's inferred intention: {player_analysis.inferred_intention}

        Current intervention decision: intervene={intervene}, brevity={brevity}, intensity={intensity}

        Finalize the InterventionDecision:
        - intervene_now (bool)
        - brevity (short|normal|long)
        - intervention_type ({', '.join([t.value for t in InterventionType])})
        - intensity_level (float 0.0-1.0)

        Return a JSON object.
        """
        response_json = self.llm_client.generate_response(prompt)
        intervention_data = json.loads(response_json)
        intervention_type_value = intervention_data.get("intervention_type", InterventionType.HINT.value)
        try:
            resolved_intervention_type = InterventionType(intervention_type_value)
        except ValueError:
            resolved_intervention_type = InterventionType.HINT
        decision = InterventionDecision(
            intervene_now=intervention_data.get("intervene_now", intervene),
            brevity=intervention_data.get("brevity", brevity),
            intervention_type=resolved_intervention_type,
            intensity_level=intervention_data.get("intensity_level", intensity)
        )
        self._add_reasoning_step("Intervention Decision",
                                 {"npc_intent": npc_intent.__dict__, "priority_decision": priority_decision.__dict__, "dialogue": dialogue.__dict__},
                                 decision.__dict__, rules_applied=[])
        return decision

    def _perform_consistency_check(self, npc: NPC, proposed_dialogue: str, memory: Memory) -> str:
        # 6. 더 강력한 자기 비판 / 일관성 검사
        # Simulate self-consistency by asking LLM to check against personality and memory
        prompt = f"""
        Evaluate if the following dialogue is consistent with NPC's personality and long-term memory.
        NPC Name: {npc.name}
        NPC Personality Traits: {npc.personality_traits}
        NPC Current Mood: {npc.current_mood.value}
        Proposed Dialogue: "{proposed_dialogue}"
        Relevant long-term facts: {memory.long_term_facts} # Only top 5 for brevity
        Relevant episodic notes: {[m.content for m in memory.episodic_notes]} # Only top 3 for brevity

        Is this dialogue consistent with the NPC's established traits and memories?
        If not, state why. Return "Consistent" or "Conflicting:".
        """
        response = self.llm_client.generate_response(prompt, temperature=0.2)
        return json.loads(response).get("consistency_check_result", "Unknown") # Assuming LLM returns {"consistency_check_result": "..."}

    def generate_npc_response(self, input_payload: InputPayload, player_analysis: PlayerAnalysis,
                              world_analysis: WorldAnalysis, story_analysis: StoryAnalysis,
                              memory_analysis: MemoryAnalysis, npc_intent: NPCIntent,
                              priority_decision: PriorityDecision, intervention_decision: InterventionDecision) -> NPCResponse:

        # 5. 선택 필터링
        # Dynamically generate guidance and quest based on analysis
        potential_guidance = []
        if player_analysis.needs_healing:
            potential_guidance.append("가까운 치료사 방문")
        if story_analysis.objective_reminder:
            potential_guidance.append(story_analysis.objective_reminder)
        if world_analysis.environment_threat == "high":
            potential_guidance.append(world_analysis.safe_action_suggestion)
        if player_analysis.inferred_intention == "explore" and story_analysis.critical_path_divergence:
            potential_guidance.append("메인 퀘스트 지역 탐색")

        # LLM을 사용하여 대화, 감정, 행동 등 최종 응답 생성
        dialogue_prompt = f"""
        You are {input_payload.npc.name}, a {input_payload.npc.role} with a {input_payload.npc.personality} personality.
        Your current mood is {input_payload.npc.current_mood.value}.
        Your core traits: {input_payload.npc.personality_traits}
        Your current intent is to {npc_intent.intent.value} because {npc_intent.rationale}.
        Your top priorities are: {priority_decision.top_priorities}.
        You have decided to intervene: {intervention_decision.intervene_now}, with brevity: {intervention_decision.brevity}, and intensity: {intervention_decision.intensity_level}.

        Player's current state: {player_analysis.__dict__}
        World state: {world_analysis.__dict__}
        Story state: {story_analysis.__dict__}
        Memory reminders for NPC: {memory_analysis.reminders}
        Things to avoid saying: {memory_analysis.dont_repeat}
        Last player dialogue: {input_payload.dialogue.last_player_lines if input_payload.dialogue.last_player_lines else 'None'}
        Player's inferred emotion: {player_analysis.current_emotion.value}
        Player's inferred intention: {player_analysis.inferred_intention}

        Generate a dialogue, emotion, action, and guidance for the NPC.
        If appropriate, suggest a new quest based on player_analysis.preferred_quests.
        Ensure the dialogue is consistent with your personality traits and memory.

        Return a JSON object with:
        - dialogue (str)
        - emotion ({', '.join()})
        - action (str, e.g., 'idle', 'approach_player', 'point_direction')
        - guidance (str, e.g., '가까운 치료사 방문', '메인 퀘스트 진행')
        - quest (Optional with title, objective, reward, difficulty, recommended_level)
        - objective_reminder (Optional)
        """
        raw_response = self.llm_client.generate_response(dialogue_prompt, temperature=0.8)
        response_data = json.loads(raw_response)

        # 6. 더 강력한 자기 비판 / 일관성 검사
        consistency_check_result = self._perform_consistency_check(
            input_payload.npc, response_data.get("dialogue", ""), input_payload.memory
        )
        self._add_reasoning_step("Consistency Check for Dialogue", {"proposed_dialogue": response_data.get("dialogue", "")}, {"result": consistency_check_result},
                                 memories_accessed= + input_payload.memory.long_term_facts,
                                 consistency_check_result=consistency_check_result)

        # If consistency check fails, could re-generate or adjust
        if "Conflicting" in consistency_check_result:
            print(f"Consistency check failed: {consistency_check_result}. Attempting to adjust dialogue...")
            # For demonstration, we'll just log and continue, in a real system, you might loop or refine.
            # Example: prompt LLM to refine dialogue to be consistent
            response_data += " (But I must ensure I stay true to myself.)"

        quest_data = response_data.get("quest")
        quest = Quest(**quest_data) if quest_data else None

        final_response = NPCResponse(
            intent=npc_intent.intent, # Use the determined intent
            dialogue=response_data.get("dialogue", "무슨 말을 해야 할지 모르겠군."),
            emotion=Emotion,
            action=response_data.get("action", "idle"),
            guidance=response_data.get("guidance", "계속 진행"),
            urgency_level=priority_decision.urgency_level,
            objective_reminder=response_data.get("objective_reminder"),
            quest=quest,
            reasoning_trace=self.reasoning_steps
        )
        self._add_reasoning_step("Final NPC Response Generation", response_data, final_response.to_dict())
        return final_response

    def process_turn(self, payload: InputPayload) -> NPCResponse:
        self.reasoning_steps = [] # Reset trace for each turn 
        self.step_counter = 0

        # 1. Input Analysis
        player_analysis = self.analyze_player(payload.player, payload.behavior, payload.dialogue)
        world_analysis = self.analyze_world(payload.world)
        story_analysis = self.analyze_story(payload.story)
        memory_analysis = self.analyze_memory(payload.memory, player_analysis, world_analysis)

        # 2. Intent and Priority Determination
        npc_intent = self.determine_npc_intent(payload.npc, player_analysis, world_analysis, story_analysis, memory_analysis)
        priority_decision = self.make_priority_decision(npc_intent, player_analysis, world_analysis, story_analysis)

        # 3. Intervention Decision
        intervention_decision = self.decide_intervention(npc_intent, priority_decision, payload.dialogue, player_analysis)

        # If no intervention, maybe return a default passive response
        if not intervention_decision.intervene_now:
            self._add_reasoning_step("No Intervention", {"intervention_decision": intervention_decision.__dict__}, {"response": "Passive/No response"})
            return NPCResponse(
                intent=InterventionType.LORE_COMMENT,
                dialogue="",
                emotion=payload.npc.current_mood,
                action="idle",
                guidance="",
                urgency_level=UrgencyLevel.LOW,
                reasoning_trace=self.reasoning_steps
            )

        # 4. Response Generation with Filtering and Consistency
        final_response = self.generate_npc_response(
            payload, player_analysis, world_analysis, story_analysis,
            memory_analysis, npc_intent, priority_decision, intervention_decision
        )

        # 8. 피드백-학습-준비 구조: 학습 데이터 업데이트 (Conceptual)
        # In a real system, you would log `payload` and `final_response`
        # along with actual player feedback for a continuous learning loop.
        self._update_learning_data(payload, final_response)

        return final_response

    def _update_learning_data(self, payload: InputPayload, response: NPCResponse):
        """
        Placeholder for updating learning data based on NPC response and (simulated) player feedback.
        In a real system, this would involve logging, evaluating outcomes, and potentially
        triggering model retraining or policy adjustments.
        """
        print(f"--- Learning Data Update (Conceptual) ---")
        print(f"NPC Response: {response.dialogue}")
        # Imagine player_feedback_reaction is observed here
        simulated_feedback = "positive" if "도움" in response.dialogue else "neutral"
        response.player_feedback_reaction = simulated_feedback
        response.outcome_evaluation = "Goal aligned" if response.objective_reminder else "Generic interaction"
        print(f"Simulated Player Feedback: {simulated_feedback}, Outcome: {response.outcome_evaluation}")
        # This data would then feed into a continuous learning pipeline.
        print(f"--- End Learning Data Update ---")

# ---------- Example Usage ----------
if __name__ == "__main__":
    llm_client = LLMClient()
    npc_agent = NPCAgent(llm_client)

    # Example Input Payload (simplified for demonstration)
    example_payload_dict = {
        "player": {
            "level": 5,
            "hp": 80,
            "inventory": [],
            "completed_quests": [],
            "play_style_tendencies": {"risk_taking": 0.6, "exploration": 0.8},
            "preferred_quests": [],
            "preferred_items": []
        },
        "behavior": {
            "recent_actions": [],
            "tendencies": {"risk_taking": 0.6, "exploration": 0.8}
        },
        "world": {
            "location": "dark_forest_edge",
            "time": "day",
            "danger_level": "medium",
            "nearby_entities": [],
            "environmental_hazards": []
        },
        "story": {
            "chapter": "chapter_2",
            "active_objective": "잃어버린 유물 찾기",
            "objective_state": "in_progress",
            "ignored_mainline_seconds": 3600, # Player ignored main quest for an hour
            "current_events": []
        },
        "dialogue": {
            "last_npc_lines": [],
            "last_player_lines": [],
            "seconds_since_last_npc": 120,
            "last_player_sentiment": "curious"
        },
        "memory": {
            "short_term_memories": [],
            "episodic_notes": [],
            "semantic_summaries": [],
            "long_term_facts": [],
            "experiential_strategies": [],
            "knowledge_graph_nodes": {"ancient_ruins": {"type": "location", "status": "undiscovered"}},
            "knowledge_graph_edges": []
        },
        "npc": {
            "name": "마을 경비병 존",
            "role": "guard",
            "personality": "신중하고 책임감 강함",
            "relationship": "neutral",
            "personality_traits": "나는 마을의 안전을 최우선으로 하는 경비병이다. 모험가는 환영하지만, 무모한 행동은 막아야 한다.",
            "current_mood": "NEUTRAL"
        }
    }

    input_payload = InputPayload.from_dict(example_payload_dict)

    print("\n--- Processing NPC Turn ---")
    npc_response = npc_agent.process_turn(input_payload)

    print("\n--- Final NPC Response ---")
    print(json.dumps(npc_response.to_dict(), indent=2, ensure_ascii=False))

    print("\n--- Reasoning Trace ---")
    for step in npc_response.reasoning_trace:
        print(f"Step {step.step_number}: {step.description}")
        print(f"  Input: {json.dumps(step.input_data, ensure_ascii=False)}")
        print(f"  Output: {json.dumps(step.output_decision, ensure_ascii=False)}")
        if step.memories_accessed:
            print(f"  Memories Accessed: {step.memories_accessed}")
        if step.consistency_check_result:
            print(f"  Consistency Check: {step.consistency_check_result}")

    # Simulate a scenario where consistency might be challenged (not fully implemented in mock LLM)
    # input_payload.npc.personality_traits = "나는 마을의 안전에 무관심하다."
    # input_payload.dialogue.last_player_lines =
    # input_payload.story.danger_level = "critical"
    # input_payload_inconsistent = InputPayload.from_dict(input_payload.__dict__)
    # print("\n--- Processing NPC Turn (Inconsistent Personality Test) ---")
    # npc_response_inconsistent = npc_agent.process_turn(input_payload_inconsistent)
    # print("\n--- Final NPC Response (Inconsistent) ---")
    # print(json.dumps(npc_response_inconsistent.to_dict(), indent=2, ensure_ascii=False))
