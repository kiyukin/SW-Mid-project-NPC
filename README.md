# Unity-Integrated DeepAgents NPC Reasoning Demo (Step 3)

A multi-agent NPC reasoning backend (Python) with a Unity client example.

Goal: Given a JSON input from Unity containing player, behavior, world, story, dialogue, memory, and NPC data, the Python backend returns structured JSON with:
- intent, dialogue, emotion, action, guidance
- urgency_level
- optional objective_reminder
- reasoning_trace (including primary_reason, secondary_reason, chosen_priority, rejected_options, final_rationale)

Folder structure:
- backend/
  - main.py               # Minimal HTTP server exposing POST /npc; structured logging
  - agents.py             # Explicit multi-agent pipeline (LLM vs heuristic modes); logs each sub-agent
  - models.py             # Data models and schema (includes reasoning_trace in output)
  - prompts.py            # Agent system prompts
  - sample_input.json     # Example payload for local testing (Step 3 schema with long_term_traits)
- unity/
  - NPCClient.cs          # Unity MonoBehaviour example sending/receiving JSON (Step 3 schema)

Requirements/Assumptions:
- Python 3.10+
- Optional: deepagents-cli installed and configured. If not available, the backend falls back to a small rule-based heuristic so it still runs locally.
- Unity 2020+ (for the example script), using UnityWebRequest.

Run backend locally:
1) python3 -m backend.main
   - Starts HTTP server at http://127.0.0.1:8089/npc
   - Prints Mode: DEEP AGENTS or Mode: FALLBACK
2) Test with curl:
   curl -s -X POST http://127.0.0.1:8089/npc -H "Content-Type: application/json" -d @backend/sample_input.json | jq .

Unity usage:
- Add unity/NPCClient.cs to a GameObject in your scene.
- Ensure the backend is running locally (URL set in script: http://127.0.0.1:8089/npc).
- Press Play; the Start() example sends a request and logs the parsed response.

Design (Step 3 system):
- Sub-agents implemented:
  1) PlayerBehaviorAnalyzer
  2) PlayerStateAnalyzer
  3) WorldContextReasoner
  4) StoryGoalTracker
  5) MemoryAgent (short_term / mid_term / long_term)
  6) PlayerModelEstimator
  7) PriorityManager
  8) ChoiceFilterAgent
  9) InterventionController
  10) GuideIntentPlanner
  11) DialogueEmotionActionGenerator
  12) SelfCriticConsistencyAgent
  13) OutcomeFeedbackLearner

- Reasoning flow (explicit, logged and appended to reasoning_trace):
  1) PlayerStateAnalyzer => PlayerAnalysis
     - reasoning_trace: primary_reason = "player_state"
  2) PlayerBehaviorAnalyzer => BehaviorAnalysis
     - reasoning_trace: secondary_reason = "behavior_patterns"
  3) WorldContextReasoner => WorldAnalysis
  4) StoryGoalTracker => StoryAnalysis
  5) MemoryAgent => MemoryAnalysis (reminders, dont_repeat, short_term, mid_term, long_term)
  6) PlayerModelEstimator => PlayerModel
  7) PriorityManager => PriorityDecision (urgency_level, chosen_priority)
     - reasoning_trace: chosen_priority
  8) ChoiceFilterAgent => ChoiceFilterResult (kept, rejected)
     - reasoning_trace: rejected_options
  9) InterventionController => InterventionDecision (intervene_now, style, brevity)
  10) GuideIntentPlanner => NPCIntent (intent, rationale)
  11) DialogueEmotionActionGenerator => Draft response (dialogue, emotion, action, guidance)
  12) SelfCriticConsistencyAgent => Final NPCResponse (consistency and tone checks)
  13) OutcomeFeedbackLearner => Feedback summary (non-persistent)
  14) reasoning_trace adds final_rationale from NPCIntent.rationale

- Output schema fields now include:
  - dialogue, emotion, action, guidance
  - urgency_level
  - optional objective_reminder
  - reasoning_trace (array of compact records; includes primary_reason, secondary_reason, chosen_priority, rejected_options, final_rationale)

Configuration:
- By default, the backend tries to import DeepAgents (deepagents_cli.llm.chat_completion). If unavailable, it uses a deterministic heuristic so you have a working demo without API keys.
- To enable a real LLM via deepagents-cli, install/configure DeepAgents and set your model/provider env per its docs.

Sample scenarios:
1) Night danger + low HP → warning/safety guidance (backend/sample_input.json)
2) Story stagnation → story_push
3) Option overload → filtered choices and gentle guidance

Notes:
- Keep the project minimal. No DB, auth, dashboards, voice, or images.
- Unity is the client; Python handles reasoning only.
