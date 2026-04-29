from __future__ import annotations

import json
from typing import Any
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os

from .agents import run_pipeline, DEEPAGENTS_AVAILABLE

HOST = os.environ.get("NPC_HOST", "127.0.0.1")
PORT = int(os.environ.get("NPC_PORT", "8089"))

# Basic structured logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')


class Handler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):  # noqa: N802
        if self.path != "/npc":
            self.send_response(404)
            self._set_cors()
            self.end_headers()
            self.wfile.write(b"Not Found")
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
        except Exception:
            self.send_response(400)
            self._set_cors()
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return
        try:
            result = run_pipeline(data)
            out = json.dumps(result).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors()
            self.end_headers()
            self.wfile.write(out)
        except Exception as e:  # pragma: no cover
            self.send_response(500)
            self._set_cors()
            self.end_headers()
            msg = {"error": str(e)}
            self.wfile.write(json.dumps(msg).encode('utf-8'))


def run_server():
    mode = "DEEP AGENTS" if DEEPAGENTS_AVAILABLE else "FALLBACK"
    print(f"NPC backend listening on http://{HOST}:{PORT}/npc | Mode: {mode}")
    with HTTPServer((HOST, PORT), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()

# # main.py
# import json
# import enum
# import datetime
# import sys
# import os
# import logging
# from http.server import BaseHTTPRequestHandler, HTTPServer
# from models import (
#     UrgencyLevel, Emotion, InterventionType,
#     Player, Behavior, World, Story, Dialogue, Memory, NPC, InputPayload,
#     PlayerAnalysis, BehaviorAnalysis, WorldAnalysis, StoryAnalysis, MemoryAnalysis,
#     NPCIntent, PriorityDecision, InterventionDecision, Quest, ReasoningStep, NPCResponse
# )

# # Basic structured logging to stdout
# logging.basicConfig(level=logging.INFO, format='%(message)s')

# # ---------- LLM Client (Mock-up) ----------
# class LLMClient:
#     """
#     대규모 언어 모델(LLM)과의 상호작용을 시뮬레이션하는 목업 클라이언트입니다.
#     실제 LLM API 호출은 이 클래스에서 이루어집니다.
#     """
#     def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
#         # 실제 LLM API 호출 로직은 여기에 구현됩니다. (예: OpenAI, Claude, Gemini 등)
#         # 현재는 단순한 목업 응답을 반환합니다.
#         logging.info(f"--- LLM Prompt --- \n{prompt}\n--- End Prompt ---")
#         if "player_analysis" in prompt.lower() and "risk" in prompt.lower():
#             return json.dumps({"risk": "medium", "needs_healing": False, "combat_ready": True, "progression_stage": "mid", "current_emotion": Emotion.NEUTRAL.value, "inferred_intention": "explore"})
#         elif "npc_intent" in prompt.lower():
#             return json.dumps({"intent": InterventionType.HINT.value, "rationale": "Player is exploring off the main path, a gentle hint about the objective might be useful."})
#         elif "priority_decision" in prompt.lower():
#             return json.dumps({"urgency_level": UrgencyLevel.MEDIUM.value, "top_priorities": [], "factors_considered": {"story_progression": 0.6}, "rationale": "Player has been ignoring the main quest for some time."})
#         elif "dialogue_generation" in prompt.lower():
#             return json.dumps({"dialogue": "음... 요즘 이곳을 탐험하는 사람이 거의 없었는데. 혹시 메인 퀘스트에 어려움이 있나?", "emotion": Emotion.CURIOUS.value, "action": "look_around", "guidance": "메인 퀘스트 진행을 위해 마을 지도 참고", "objective_reminder": "잃어버린 유물 찾기"})
#         elif "memory_analysis" in prompt.lower():
#             return json.dumps({"reminders": [], "dont_repeat": [], "conflicting_memories": [], "pruning_candidates": []})
#         elif "consistency_check" in prompt.lower():
#              return json.dumps({"consistency_check_result": "Consistent"})
#         return "LLM mock response based on prompt."

# # ---------- Core Reasoning Engine ----------

# class NPCAgent:
#     def __init__(self, llm_client: LLMClient):
#         self.llm_client = llm_client
#         self.reasoning_steps: List[ReasoningStep] = []
#         self.step_counter = 0

#     def _add_reasoning_step(self, description: str, input_data: Dict, output_decision: Dict,
#                              memories_accessed: Optional[List[str]] = None, rules_applied: Optional[List[str]] = None,
#                              consistency_check_result: Optional[str] = None):
#         self.step_counter += 1
#         self.reasoning_steps.append(
#             ReasoningStep(
#                 step_number=self.step_counter,
#                 description=description,
#                 input_data=input_data,
#                 output_decision=output_decision,
#                 memories_accessed=memories_accessed if memories_accessed is not None else [],
#                 rules_applied=rules_applied if rules_applied is not None else [],
#                 consistency_check_result=consistency_check_result
#             )
#         )

#     def analyze_player(self, player: Player, behavior: Behavior, dialogue: Dialogue) -> PlayerAnalysis:
#         prompt = f"""
#         Given the player's current state, recent behavior, and last dialogue, analyze their situation.
#         Player Level: {player.level}, HP: {player.hp}
#         Inventory: {player.inventory}
#         Completed Quests: {player.completed_quests}
#         Play Style Tendencies: {player.play_style_tendencies}
#         Recent Actions: {behavior.recent_actions}
#         Last Player Lines: {dialogue.last_player_lines}
#         Last Player Sentiment: {dialogue.last_player_sentiment}

#         Based on this, provide a PlayerAnalysis:
#         - risk (low/medium/high)
#         - needs_healing (bool)
#         - combat_ready (bool)
#         - progression_stage (early/mid/late)
#         - current_emotion (e.g., {', '.join([e.value for e in Emotion])})
#         - inferred_intention (e.g., 'explore', 'quest_complete', 'interact_npc')

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         analysis_data = json.loads(response_json)
#         analysis = PlayerAnalysis(
#             risk=analysis_data.get("risk", "medium"),
#             needs_healing=analysis_data.get("needs_healing", False),
#             combat_ready=analysis_data.get("combat_ready", True),
#             progression_stage=analysis_data.get("progression_stage", "mid"),
#             current_emotion=Emotion[analysis_data.get("current_emotion", Emotion.NEUTRAL.value).upper()],
#             inferred_intention=analysis_data.get("inferred_intention", "unknown")
#         )
#         self._add_reasoning_step("Player Analysis", {"player": player.__dict__, "behavior": behavior.__dict__, "dialogue": dialogue.__dict__}, analysis.__dict__)
#         return analysis

#     def analyze_world(self, world: World) -> WorldAnalysis:
#         prompt = f"""
#         Analyze the current world state.
#         Location: {world.location}, Time: {world.time}, Danger Level: {world.danger_level}
#         Nearby Entities: {world.nearby_entities}
#         Environmental Hazards: {world.environmental_hazards}

#         Provide a WorldAnalysis:
#         - environment_threat (low/medium/high)
#         - is_night (bool)
#         - location_hint (short descriptor)
#         - safe_action_suggestion (e.g., 'stay_put', 'return_to_town', 'explore_cautiously')
#         - weather_condition (e.g., 'clear', 'rainy', 'stormy')
#         - time_of_day_cycle (e.g., 'dawn', 'morning', 'afternoon', 'dusk', 'night')

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         analysis_data = json.loads(response_json)
#         analysis = WorldAnalysis(
#             environment_threat=analysis_data.get("environment_threat", "medium"),
#             is_night=analysis_data.get("is_night", False),
#             location_hint=analysis_data.get("location_hint", "a quiet place"),
#             safe_action_suggestion=analysis_data.get("safe_action_suggestion", "explore_cautiously"),
#             weather_condition=analysis_data.get("weather_condition", "clear"),
#             time_of_day_cycle=analysis_data.get("time_of_day_cycle", "day")
#         )
#         self._add_reasoning_step("World Analysis", {"world": world.__dict__}, analysis.__dict__)
#         return analysis

#     def analyze_story(self, story: Story) -> StoryAnalysis:
#         prompt = f"""
#         Analyze the current story progression.
#         Chapter: {story.chapter}, Active Objective: {story.active_objective}, Objective State: {story.objective_state}
#         Ignored Mainline Seconds: {story.ignored_mainline_seconds}
#         Current Events: {story.current_events}

#         Provide a StoryAnalysis:
#         - objective_reminder (Optional)
#         - is_blocked (bool)
#         - time_off_mainline (int)
#         - story_progress_percentage (float)
#         - critical_path_divergence (bool)

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         analysis_data = json.loads(response_json)
#         analysis = StoryAnalysis(
#             objective_reminder=analysis_data.get("objective_reminder"),
#             is_blocked=analysis_data.get("is_blocked", False),
#             time_off_mainline=analysis_data.get("time_off_mainline", 0),
#             story_progress_percentage=analysis_data.get("story_progress_percentage", 0.0),
#             critical_path_divergence=analysis_data.get("critical_path_divergence", False)
#         )
#         self._add_reasoning_step("Story Analysis", {"story": story.__dict__}, analysis.__dict__)
#         return analysis

#     def analyze_memory(self, memory: Memory, player_analysis: PlayerAnalysis, world_analysis: WorldAnalysis) -> MemoryAnalysis:
#         short_term_contents = [entry.content for entry in memory.short_term_memories]
#         episodic_contents = [entry.content for entry in memory.episodic_notes]

#         prompt = f"""
#         Given the NPC's memory and current context, perform a memory analysis.
#         Short-term memories: {short_term_contents}
#         Episodic notes: {episodic_contents}
#         Semantic summaries: {memory.semantic_summaries}
#         Long-term facts: {memory.long_term_facts}
#         Experiential strategies: {memory.experiential_strategies}
#         Knowledge Graph Nodes (simplified): {memory.knowledge_graph_nodes}
#         Knowledge Graph Edges (simplified): {memory.knowledge_graph_edges}
#         Player's inferred emotion: {player_analysis.current_emotion.value}
#         Current environment threat: {world_analysis.environment_threat}

#         Identify:
#         - reminders: What key memories should the NPC consider right now?
#         - dont_repeat: What should the NPC avoid saying/doing based on past interactions?
#         - conflicting_memories: Are there any memories that contradict each other or current reality?
#         - pruning_candidates: Which memories are old or low importance and could be pruned or summarized?

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         analysis_data = json.loads(response_json)
#         analysis = MemoryAnalysis(
#             reminders=analysis_data.get("reminders", []),
#             dont_repeat=analysis_data.get("dont_repeat", []),
#             conflicting_memories=analysis_data.get("conflicting_memories", []),
#             pruning_candidates=analysis_data.get("pruning_candidates", [])
#         )
#         all_memories_accessed = short_term_contents + episodic_contents + memory.semantic_summaries + memory.long_term_facts
#         self._add_reasoning_step("Memory Analysis", {"memory": memory.__dict__, "player_analysis": player_analysis.__dict__, "world_analysis": world_analysis.__dict__}, analysis.__dict__,
#                                  memories_accessed=all_memories_accessed)
#         return analysis

#     def determine_npc_intent(self, npc: NPC, player_analysis: PlayerAnalysis, world_analysis: WorldAnalysis,
#                               story_analysis: StoryAnalysis, memory_analysis: MemoryAnalysis) -> NPCIntent:
#         prompt = f"""
#         Based on the current situation and NPC's personality, what should {npc.name}'s primary intent be?
#         NPC: {npc.name}, Role: {npc.role}, Personality: {npc.personality}, Relationship: {npc.relationship}
#         NPC Personality Traits: {npc.personality_traits}
#         NPC Current Mood: {npc.current_mood.value}

#         Player Analysis: {player_analysis.__dict__}
#         World Analysis: {world_analysis.__dict__}
#         Story Analysis: {story_analysis.__dict__}
#         Memory Reminders: {memory_analysis.reminders}
#         Memory Don't Repeat: {memory_analysis.dont_repeat}

#         Consider NPC's core duties and personality traits.
#         Possible intents: {', '.join([e.value for e in InterventionType])}

#         Provide an NPCIntent:
#         - intent (one of the possible intents)
#         - rationale (justification for the intent)

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         intent_data = json.loads(response_json)
#         try:
#             resolved_intent_type = InterventionType[intent_data.get("intent", InterventionType.LORE_COMMENT.value).upper()]
#         except KeyError:
#             logging.warning(f"Invalid intent type: {intent_data.get('intent')}. Defaulting to LORE_COMMENT.")
#             resolved_intent_type = InterventionType.LORE_COMMENT
#         intent = NPCIntent(
#             intent=resolved_intent_type,
#             rationale=intent_data.get("rationale", "No clear rationale.")
#         )
#         self._add_reasoning_step("NPC Intent Determination",
#                                  {"npc": npc.__dict__, "player_analysis": player_analysis.__dict__, "world_analysis": world_analysis.__dict__, "story_analysis": story_analysis.__dict__, "memory_analysis": memory_analysis.__dict__},
#                                  intent.__dict__)
#         return intent

#     def make_priority_decision(self, npc_intent: NPCIntent, player_analysis: PlayerAnalysis,
#                                world_analysis: WorldAnalysis, story_analysis: StoryAnalysis) -> PriorityDecision:
#         prompt = f"""
#         Given the determined NPC intent and overall context, prioritize the NPC's actions.
#         NPC Intent: {npc_intent.__dict__}
#         Player Analysis: {player_analysis.__dict__}
#         World Analysis: {world_analysis.__dict__}
#         Story Analysis: {story_analysis.__dict__}

#         Determine the PriorityDecision:
#         - urgency_level (low/medium/high/critical)
#         - top_priorities (List)
#         - factors_considered (Dict) - Key factors and their relative weights
#         - rationale (natural language explanation)

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         priority_data = json.loads(response_json)
#         priority = PriorityDecision(
#             urgency_level=UrgencyLevel[priority_data.get("urgency_level", UrgencyLevel.LOW.value).upper()],
#             top_priorities=priority_data.get("top_priorities", []),
#             factors_considered=priority_data.get("factors_considered", {}),
#             rationale=priority_data.get("rationale", "")
#         )
#         self._add_reasoning_step("Priority Decision",
#                                  {"npc_intent": npc_intent.__dict__, "player_analysis": player_analysis.__dict__, "world_analysis": world_analysis.__dict__, "story_analysis": story_analysis.__dict__},
#                                  priority.__dict__)
#         return priority

#     def decide_intervention(self, npc_intent: NPCIntent, priority_decision: PriorityDecision,
#                             dialogue: Dialogue, player_analysis: PlayerAnalysis) -> InterventionDecision:
#         intervene = False
#         brevity = "normal"
#         intensity = 0.5

#         if priority_decision.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
#             intervene = True
#             brevity = "long" if priority_decision.urgency_level == UrgencyLevel.CRITICAL else "normal"
#             intensity = 0.8 if priority_decision.urgency_level == UrgencyLevel.CRITICAL else 0.6
#         elif npc_intent.intent == InterventionType.HINT and player_analysis.inferred_intention == "explore":
#             if dialogue.seconds_since_last_npc > 60:
#                 intervene = True
#                 brevity = "short"
#                 intensity = 0.4

#         prompt = f"""
#         Given the NPC's intent ({npc_intent.intent.value}) and priority ({priority_decision.urgency_level.value}), decide if and how to intervene.
#         Last NPC lines: {dialogue.last_npc_lines}
#         Seconds since last NPC speech: {dialogue.seconds_since_last_npc}
#         Player's current emotion: {player_analysis.current_emotion.value}
#         Player's inferred intention: {player_analysis.inferred_intention}

#         Current intervention decision: intervene={intervene}, brevity={brevity}, intensity={intensity}

#         Finalize the InterventionDecision:
#         - intervene_now (bool)
#         - brevity (short|normal|long)
#         - intervention_type ({', '.join([e.value for e in InterventionType])})
#         - intensity_level (float 0.0-1.0)

#         Return a JSON object.
#         """
#         response_json = self.llm_client.generate_response(prompt)
#         intervention_data = json.loads(response_json)
#         intervention_type_value = intervention_data.get("intervention_type", InterventionType.HINT.value)
#         try:
#             resolved_intervention_type = InterventionType[intervention_type_value.upper()]
#         except ValueError:
#             resolved_intervention_type = InterventionType.HINT
#         decision = InterventionDecision(
#             intervene_now=intervention_data.get("intervene_now", intervene),
#             brevity=intervention_data.get("brevity", brevity),
#             intervention_type=resolved_intervention_type,
#             intensity_level=intervention_data.get("intensity_level", intensity)
#         )
#         self._add_reasoning_step("Intervention Decision",
#                                  {"npc_intent": npc_intent.__dict__, "priority_decision": priority_decision.__dict__, "dialogue": dialogue.__dict__},
#                                  decision.__dict__)
#         return decision

#     def _perform_consistency_check(self, npc: NPC, proposed_dialogue: str, memory: Memory) -> str:
#         # Extract content from MemoryEntry objects for prompt
#         episodic_contents = [entry.content for entry in memory.episodic_notes]

#         prompt = f"""
#         Evaluate if the following dialogue is consistent with NPC's personality and long-term memory.
#         NPC Name: {npc.name}
#         NPC Personality Traits: {npc.personality_traits}
#         NPC Current Mood: {npc.current_mood.value}
#         Proposed Dialogue: "{proposed_dialogue}"
#         Relevant long-term facts: {memory.long_term_facts[:5]} # Only top 5 for brevity
#         Relevant episodic notes: {episodic_contents[:3]} # Only top 3 for brevity

#         Is this dialogue consistent with the NPC's established traits and memories?
#         If not, state why. Return "Consistent" or "Conflicting:".
#         """
#         response = self.llm_client.generate_response(prompt, temperature=0.2)
#         return json.loads(response).get("consistency_check_result", "Unknown")

#     def generate_npc_response(self, input_payload: InputPayload, player_analysis: PlayerAnalysis,
#                               world_analysis: WorldAnalysis, story_analysis: StoryAnalysis,
#                               memory_analysis: MemoryAnalysis, npc_intent: NPCIntent,
#                               priority_decision: PriorityDecision, intervention_decision: InterventionDecision) -> NPCResponse:

#         potential_guidance: List[str] = []
#         if player_analysis.needs_healing:
#             potential_guidance.append("가까운 치료사 방문")
#         if story_analysis.objective_reminder:
#             potential_guidance.append(story_analysis.objective_reminder)
#         if world_analysis.environment_threat == "high":
#             potential_guidance.append(world_analysis.safe_action_suggestion)
#         if player_analysis.inferred_intention == "explore" and story_analysis.critical_path_divergence:
#             potential_guidance.append("메인 퀘스트 지역 탐색")

#         dialogue_prompt = f"""
#         You are {input_payload.npc.name}, a {input_payload.npc.role} with a {input_payload.npc.personality} personality.
#         Your current mood is {input_payload.npc.current_mood.value}.
#         Your core traits: {input_payload.npc.personality_traits}
#         Your current intent is to {npc_intent.intent.value} because {npc_intent.rationale}.
#         Your top priorities are: {priority_decision.top_priorities}.
#         You have decided to intervene: {intervention_decision.intervene_now}, with brevity: {intervention_decision.brevity}, and intensity: {intervention_decision.intensity_level}.

#         Player's current state: {player_analysis.__dict__}
#         World state: {world_analysis.__dict__}
#         Story state: {story_analysis.__dict__}
#         Memory reminders for NPC: {memory_analysis.reminders}
#         Things to avoid saying: {memory_analysis.dont_repeat}
#         Last player dialogue: {input_payload.dialogue.last_player_lines if input_payload.dialogue.last_player_lines else 'None'}
#         Player's inferred emotion: {player_analysis.current_emotion.value}
#         Player's inferred intention: {player_analysis.inferred_intention}

#         Generate a dialogue, emotion, action, and guidance for the NPC.
#         If appropriate, suggest a new quest based on player_analysis.preferred_quests.
#         Ensure the dialogue is consistent with your personality traits and memory.

#         Return a JSON object with:
#         - dialogue (str)
#         - emotion ({', '.join([e.value for e in Emotion])})
#         - action (str, e.g., 'idle', 'approach_player', 'point_direction')
#         - guidance (str, e.g., '가까운 치료사 방문', '메인 퀘스트 진행')
#         - quest (Optional with title, objective, reward, difficulty, recommended_level)
#         - objective_reminder (Optional)
#         """
#         raw_response = self.llm_client.generate_response(dialogue_prompt, temperature=0.8)
#         response_data = json.loads(raw_response)

#         consistency_check_result = self._perform_consistency_check(
#             input_payload.npc, response_data.get("dialogue", ""), input_payload.memory
#         )
#         all_accessed_memories_for_check = [m.content for m in input_payload.memory.episodic_notes] + input_payload.memory.long_term_facts
#         self._add_reasoning_step("Consistency Check for Dialogue", {"proposed_dialogue": response_data.get("dialogue", "")}, {"result": consistency_check_result},
#                                  memories_accessed=all_accessed_memories_for_check,
#                                  consistency_check_result=consistency_check_result)

#         if "Conflicting" in consistency_check_result:
#             logging.warning(f"Consistency check failed: {consistency_check_result}. Attempting to adjust dialogue...")
#             response_data["dialogue"] += " (하지만 나는 내 본연의 모습에 충실해야 해.)" # Accessing as dict

#         quest_data = response_data.get("quest")
#         quest = Quest(**quest_data) if quest_data else None

#         final_response = NPCResponse(
#             intent=npc_intent.intent,
#             dialogue=response_data.get("dialogue", "무슨 말을 해야 할지 모르겠군."),
#             emotion=Emotion[response_data.get("emotion", Emotion.NEUTRAL.value).upper()],
#             action=response_data.get("action", "idle"),
#             guidance=response_data.get("guidance", "계속 진행"),
#             urgency_level=priority_decision.urgency_level,
#             objective_reminder=response_data.get("objective_reminder"),
#             quest=quest,
#             reasoning_trace=self.reasoning_steps
#         )
#         self._add_reasoning_step("Final NPC Response Generation", response_data, final_response.to_dict())
#         return final_response

#     def process_turn(self, payload: InputPayload) -> NPCResponse:
#         self.reasoning_steps = []
#         self.step_counter = 0

#         player_analysis = self.analyze_player(payload.player, payload.behavior, payload.dialogue)
#         world_analysis = self.analyze_world(payload.world)
#         story_analysis = self.analyze_story(payload.story)
#         memory_analysis = self.analyze_memory(payload.memory, player_analysis, world_analysis)

#         npc_intent = self.determine_npc_intent(payload.npc, player_analysis, world_analysis, story_analysis, memory_analysis)
#         priority_decision = self.make_priority_decision(npc_intent, player_analysis, world_analysis, story_analysis)

#         intervention_decision = self.decide_intervention(npc_intent, priority_decision, payload.dialogue, player_analysis)

#         if not intervention_decision.intervene_now:
#             self._add_reasoning_step("No Intervention", {"intervention_decision": intervention_decision.__dict__}, {"response": "Passive/No response"})
#             return NPCResponse(
#                 intent=InterventionType.LORE_COMMENT,
#                 dialogue="",
#                 emotion=payload.npc.current_mood,
#                 action="idle",
#                 guidance="",
#                 urgency_level=UrgencyLevel.LOW,
#                 reasoning_trace=self.reasoning_steps
#             )

#         final_response = self.generate_npc_response(
#             payload, player_analysis, world_analysis, story_analysis,
#             memory_analysis, npc_intent, priority_decision, intervention_decision
#         )

#         self._update_learning_data(payload, final_response)

#         return final_response

#     def _update_learning_data(self, payload: InputPayload, response: NPCResponse):
#         logging.info(f"--- Learning Data Update (Conceptual) ---")
#         logging.info(f"NPC Response: {response.dialogue}")
#         simulated_feedback = "positive" if "도움" in response.dialogue else "neutral"
#         response.player_feedback_reaction = simulated_feedback
#         response.outcome_evaluation = "Goal aligned" if response.objective_reminder else "Generic interaction"
#         logging.info(f"Simulated Player Feedback: {simulated_feedback}, Outcome: {response.outcome_evaluation}")
#         logging.info(f"--- End Learning Data Update ---")

# # ---------- Example Usage and Server Setup (for main.py) ----------
# HOST = os.environ.get("NPC_HOST", "127.0.0.1")
# PORT = int(os.environ.get("NPC_PORT", "8089"))

# # This is a placeholder for DEEPAGENTS_AVAILABLE. In a real setup, this would be determined by actual agent availability.
# DEEPAGENTS_AVAILABLE = False # Set to True if you have DeepAgents integrated.

# class Handler(BaseHTTPRequestHandler):
#     def _set_cors(self):
#         self.send_header("Access-Control-Allow-Origin", "*")
#         self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
#         self.send_header("Access-Control-Allow-Headers", "Content-Type")

#     def do_OPTIONS(self):
#         self.send_response(200)
#         self._set_cors()
#         self.end_headers()

#     def do_POST(self):
#         if self.path != "/npc":
#             self.send_response(404)
#             self._set_cors()
#             self.end_headers()
#             self.wfile.write(b"Not Found")
#             return
#         try:
#             length = int(self.headers.get('Content-Length', '0'))
#             body = self.rfile.read(length).decode('utf-8')
#             data = json.loads(body)
#         except Exception as e:
#             logging.error(f"Invalid JSON payload received: {e}")
#             self.send_response(400)
#             self._set_cors()
#             self.end_headers()
#             self.wfile.write(b"Invalid JSON")
#             return
#         try:
#             llm_client_instance = LLMClient()
#             npc_agent_instance = NPCAgent(llm_client_instance)
#             input_payload = InputPayload.from_dict(data)
#             result_response = npc_agent_instance.process_turn(input_payload)
#             out = json.dumps(result_response.to_dict(), indent=2, ensure_ascii=False).encode('utf-8')
#             self.send_response(200)
#             self.send_header("Content-Type", "application/json")
#             self._set_cors()
#             self.end_headers()
#             self.wfile.write(out)
#         except Exception as e:
#             logging.exception("Error processing pipeline request:")
#             self.send_response(500)
#             self._set_cors()
#             self.end_headers()
#             msg = {"error": str(e), "message": "An internal server error occurred."}
#             self.wfile.write(json.dumps(msg, indent=2, ensure_ascii=False).encode('utf-8'))

# def run_server():
#     mode = "DEEP AGENTS" if DEEPAGENTS_AVAILABLE else "FALLBACK"
#     logging.info(f"NPC backend listening on http://{HOST}:{PORT}/npc | Mode: {mode}")
#     try:
#         with HTTPServer((HOST, PORT), Handler) as httpd:
#             httpd.serve_forever()
#     except KeyboardInterrupt:
#         logging.info("Server is shutting down.")
#         httpd.shutdown()
#     except Exception as e:
#         logging.critical(f"Failed to start server: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     # Example usage for direct testing (not via HTTP server)
#     llm_client = LLMClient()
#     npc_agent = NPCAgent(llm_client)

#     example_payload_dict = {
#         "player": {
#             "level": 5,
#             "hp": 80,
#             "inventory": [],
#             "completed_quests": [],
#             "play_style_tendencies": {"risk_taking": 0.6, "exploration": 0.8},
#             "preferred_quests": [],
#             "preferred_items": []
#         },
#         "behavior": {
#             "recent_actions": [],
#             "tendencies": {"risk_taking": 0.6, "exploration": 0.8}
#         },
#         "world": {
#             "location": "dark_forest_edge",
#             "time": "day",
#             "danger_level": "medium",
#             "nearby_entities": [],
#             "environmental_hazards": []
#         },
#         "story": {
#             "chapter": "chapter_2",
#             "active_objective": "잃어버린 유물 찾기",
#             "objective_state": "in_progress",
#             "ignored_mainline_seconds": 3600,
#             "current_events": []
#         },
#         "dialogue": {
#             "last_npc_lines": [],
#             "last_player_lines": ["어디로 가야 할지 모르겠군."],
#             "seconds_since_last_npc": 120,
#             "last_player_sentiment": "curious"
#         },
#         "memory": {
#             "short_term_memories": [],
#             "episodic_notes": [],
#             "semantic_summaries": ["마을 경비병 존은 플레이어가 퀘스트를 진행하지 않고 숲을 헤매는 것을 걱정한다."],
#             "long_term_facts": ["고대 유물은 위험한 숲 깊숙한 곳에 있다.", "존은 마을의 안전을 최우선으로 생각한다."],
#             "experiential_strategies": [],
#             "knowledge_graph_nodes": {"ancient_ruins": {"type": "location", "status": "undiscovered"}},
#             "knowledge_graph_edges": []
#         },
#         "npc": {
#             "name": "마을 경비병 존",
#             "role": "guard",
#             "personality": "신중하고 책임감 강함",
#             "relationship": "neutral",
#             "personality_traits": "나는 마을의 안전을 최우선으로 하는 경비병이다. 모험가는 환영하지만, 무모한 행동은 막아야 한다.",
#             "current_mood": "NEUTRAL"
#         }
#     }

#     input_payload = InputPayload.from_dict(example_payload_dict)

#     logging.info("\n--- Processing NPC Turn ---")
#     npc_response = npc_agent.process_turn(input_payload)

#     logging.info("\n--- Final NPC Response ---")
#     logging.info(json.dumps(npc_response.to_dict(), indent=2, ensure_ascii=False))

#     logging.info("\n--- Reasoning Trace ---")
#     for step in npc_response.reasoning_trace:
#         logging.info(f"Step {step.step_number}: {step.description}")
#         logging.info(f"  Input: {json.dumps(step.input_data, ensure_ascii=False)}")
#         logging.info(f"  Output: {json.dumps(step.output_decision, ensure_ascii=False)}")
#         if step.memories_accessed:
#             logging.info(f"  Memories Accessed: {step.memories_accessed}")
#         if step.consistency_check_result:
#             logging.info(f"  Consistency Check: {step.consistency_check_result}")

#     # Uncomment this to run the HTTP server
#     # run_server()
