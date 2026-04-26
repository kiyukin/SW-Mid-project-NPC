# Unity-Integrated DeepAgents NPC Reasoning Demo

A minimal multi-agent NPC reasoning backend (Python) with a Unity client example.

Goal: Given a JSON input from Unity containing player, behavior, world, story, dialogue, memory, and NPC data, the Python backend returns structured JSON with dialogue, emotion, action, guidance, urgency_level, optional objective_reminder, and a reasoning_trace.

Folder structure:
- backend/
  - main.py               # Minimal HTTP server exposing POST /npc; structured logging
  - agents.py             # Explicit multi-agent pipeline (LLM vs heuristic modes); logs each sub-agent
  - models.py             # Data models and schema (includes reasoning_trace in output)
  - prompts.py            # Agent system prompts
  - sample_input.json     # Example payload for local testing (danger-at-night scenario)
- unity/
  - NPCClient.cs          # Unity MonoBehaviour example sending/receiving JSON (updated schema)

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
- For scenario 2, modify the payload in NPCClient.cs Start() or call SendNPCRequest with the JSON shown below.

Design notes (Step 2 MVP):
- Sub-agents implemented now:
  1) PlayerBehaviorAnalyzer
  2) PlayerStateAnalyzer
  3) WorldContextReasoner
  4) StoryGoalTracker
  5) MemoryAgent
  6) PriorityManager
  7) InterventionController
  8) GuideIntentPlanner
  9) DialogueEmotionActionGenerator
  10) SelfCriticConsistencyAgent
  11) ReasoningTraceBuilder (inline via pipeline logs)
- Intent style: guide companion (warn, hint, coach, encourage, nudge, reassure, celebrate, lore_comment)
- Placeholders prepared (stubs to be added in Step 3): PlayerModelEstimator, ChoiceFilterAgent, OutcomeFeedbackLearner
- Reasoning flow (explicit, logged):
  1) PlayerStateAnalyzer => PlayerAnalysis
  2) PlayerBehaviorAnalyzer => BehaviorAnalysis
  3) WorldContextReasoner => WorldAnalysis
  4) StoryGoalTracker => StoryAnalysis
  5) MemoryAgent => MemoryAnalysis
  6) PriorityManager => PriorityDecision (urgency_level)
  7) InterventionController => InterventionDecision (intervene, brevity)
  8) GuideIntentPlanner => NPCIntent
  9) DialogueEmotionActionGenerator => Draft content (dialogue, emotion, action, guidance, quest?)
  10) SelfCriticConsistencyAgent => Final content
  - Each step logs a structured JSON record and is appended to reasoning_trace returned to Unity.
- Output schema fields now include: dialogue, emotion, action, guidance, urgency_level, optional objective_reminder, reasoning_trace.

Configuration:
- By default, the backend tries to import DeepAgents (deepagents_cli.llm.chat_completion). If unavailable, it uses a deterministic heuristic so you have a working demo without API keys.
- To enable a real LLM via deepagents-cli, install/configure DeepAgents and set your model/provider env per its docs.

Second sample scenario (story stagnation):
Use this JSON to nudge player back to main objective:
{
  "player": {"level": 6, "hp": 65, "inventory": ["bow"], "completed_quests": ["side_1"]},
  "behavior": {"recent_actions": ["fish_lake", "explore_cave"], "tendencies": {"risk_taking": 0.4, "exploration": 0.8, "caution": 0.6}},
  "world": {"location": "meadows", "time": "day", "danger_level": "low"},
  "story": {"chapter": "chapter_2", "active_objective": "Meet the Warden", "objective_state": "in_progress", "ignored_mainline_seconds": 1200},
  "dialogue": {"last_npc_lines": ["The Warden awaits."], "last_player_lines": ["Maybe later."], "seconds_since_last_npc": 120},
  "memory": {"episodic_notes": ["Player skipped Warden twice"], "semantic_summaries": ["Likes side quests"]},
  "npc": {"name": "Companion", "role": "guide", "personality": "supportive", "relationship": "friendly"}
}

Notes:
- Keep the project minimal. No DB, auth, dashboards, voice, or images.
- Unity is the client; Python handles reasoning only.

1. 프로젝트 개요

본 프로젝트는 Unity와 연동 가능한 게임 NPC 응답 생성 시스템을 구현한 것이다.
플레이어 상태와 게임 세계의 맥락을 입력으로 받아, 여러 서브에이전트가 단계적으로 추론하여 NPC의 대사(dialogue), 감정(emotion), 행동(action), 퀘스트(quest)를 생성한다.

본 시스템은 단순한 챗봇형 NPC가 아니라, 역할이 분리된 여러 에이전트가 협업하여 결과를 만드는 특수목적 멀티에이전트 시스템이다.

2. 에이전트 목표

이 에이전트 팀의 목표는 다음과 같다.

플레이어의 현재 상태를 분석한다.
게임 세계의 위험도와 맥락을 해석한다.
NPC가 어떤 의도로 반응해야 하는지 결정한다.
의도에 맞는 대사, 감정, 행동, 퀘스트를 생성한다.
최종 결과가 일관적인지 검증한다.

즉, 상황에 따라 자연스럽고 설명 가능한 NPC 반응을 생성하는 것이 본 프로젝트의 핵심 목표이다.

3. 시스템 구조

본 시스템은 1개의 오케스트레이터와 5개의 서브에이전트로 구성된다.

전체 구조
Unity / 외부 클라이언트
JSON 입력 전송
Python Backend (/npc)
멀티에이전트 추론 수행
최종 JSON 응답 반환
서브에이전트 구성
PlayerStateAnalyzer
WorldContextReasoner
NPCIntentPlanner
DialogueActionGenerator
ConsistencyCritic
4. 각 에이전트의 역할
1) PlayerStateAnalyzer

플레이어의 상태를 분석한다.

레벨
HP
인벤토리
진행 단계
회복 필요 여부
전투 준비 여부

출력 예:

risk
needs_healing
combat_ready
progression_stage
2) WorldContextReasoner

게임 세계의 상황을 분석한다.

위치
시간대
위험도
환경 위협 수준
안전 행동 제안

출력 예:

environment_threat
is_night
location_hint
safe_action_suggestion
3) NPCIntentPlanner

플레이어 분석 결과와 세계 분석 결과를 바탕으로 NPC가 어떤 의도로 반응해야 하는지 결정한다.

예:

casual
warn
hint
trade
warn_and_offer_quest

출력 예:

intent
rationale
4) DialogueActionGenerator

의도에 맞는 실제 NPC 응답을 생성한다.

출력 예:

dialogue
emotion
action
quest
5) ConsistencyCritic

최종 결과가 게임 맥락과 맞는지 검증하고 보정한다.

검사 예:

퀘스트 누락 여부
감정 값 범위
응답 형식 일관성
NPC 역할과 결과의 적절성
5. 동작 원리

본 시스템은 다음과 같은 다단계 추론 과정으로 동작한다.

플레이어 상태 분석
세계 맥락 분석
NPC 의도 결정
대사, 행동, 퀘스트 생성
결과 검증 및 보정
최종 JSON 반환

즉, 하나의 LLM이 한 번에 답을 만드는 방식이 아니라, 각 단계가 분리된 멀티에이전트 파이프라인으로 설계되었다.

6. 입력 / 출력 형식 (MVP)
입력 JSON 주요 항목
- player, behavior, world, story, dialogue, memory, npc

출력 JSON 주요 항목
- dialogue, emotion, action, guidance, urgency_level, objective_reminder?, reasoning_trace, quest?

샘플 시나리오 1 (위험 상황: 밤의 숲, 안전 유도)
- backend/sample_input.json 그대로 사용

샘플 시나리오 2 (메인 스토리 장기 미진행: 푸시 유도)
- 예시 요청 바디:
{
  "player": {"level": 6, "hp": 65, "inventory": ["bow"], "completed_quests": ["side_1"]},
  "behavior": {"recent_actions": ["fish_lake", "explore_cave"], "tendencies": {"risk_taking": 0.4, "exploration": 0.8, "caution": 0.6}},
  "world": {"location": "meadows", "time": "day", "danger_level": "low"},
  "story": {"chapter": "chapter_2", "active_objective": "Meet the Warden", "objective_state": "in_progress", "ignored_mainline_seconds": 1200},
  "dialogue": {"last_npc_lines": ["The Warden awaits."], "last_player_lines": ["Maybe later."], "seconds_since_last_npc": 120},
  "memory": {"episodic_notes": ["Player skipped Warden twice"], "semantic_summaries": ["Likes side quests"]},
  "npc": {"name": "Elder Rowan", "role": "healer", "personality": "kind but cautious", "relationship": "friendly"}
}

7. 실행 결과

본 프로젝트는 로컬 환경에서 정상적으로 실행되었으며, POST /npc 요청을 받아 NPC 응답을 JSON 형태로 반환하는 것을 확인하였다.

실제 실행 결과 요약

입력 조건:

플레이어 레벨 3
HP 20
밤의 숲
위험도 high
NPC 역할: healer

최종 결과:

intent: warn_and_offer_quest
dialogue: 위험 경고 + 약초 수집 퀘스트 제안
emotion: concerned
action: point_to_safe_path
quest: Herbs for Survival

또한 최종 응답에 reasoning_trace가 포함되어, 각 서브에이전트의 판단 결과를 확인할 수 있었다.

8. 현재 실행 모드

서버 시작 시 콘솔에 "Mode: DEEP AGENTS" 또는 "Mode: FALLBACK"가 출력된다.
- FALLBACK: 본 저장소만으로 로컬에서 즉시 실행 가능 (룰 기반/휴리스틱)
- DEEP AGENTS: deepagents-cli 설정 후 실제 LLM 호출 경로 사용

양 모드 모두 서브에이전트 단계별 로그를 남기며, reasoning_trace에 포함된다.

9. 기술 스택
Python
HTTPServer
JSON
Unity C# Client
DeepAgents-compatible structure
heuristic fallback pipeline
10. 폴더 구조
backend
main.py
agents.py
models.py
prompts.py
sample_input.json
init.py
unity
NPCClient.cs
README.md
11. 실행 방법
서버 실행

python3 -m backend.main

테스트 요청

curl -s -X POST http://127.0.0.1:8089/npc
 -H "Content-Type: application/json" -d @backend/sample_input.json | python3 -m json.tool

12. 기대 효과

본 프로젝트를 통해 다음과 같은 효과를 기대할 수 있다.

게임 NPC 반응의 자연스러움 향상
NPC 응답 생성 과정을 설명 가능한 형태로 구조화
Unity와 AI 백엔드의 연동 구조 학습
멀티에이전트 기반 게임 AI 설계 경험 축적
13. 한계점

현재 시스템의 한계는 다음과 같다.

DeepAgents 본 실행이 아닌 heuristic mode 기반 테스트
입력 변화에 따른 다양한 사례 실험 부족
Unity UI 상의 시각적 결과 통합은 미완성
현재 NPC 유형이 제한적임
14. 향후 개선 방향
DeepAgents 실제 실행 환경 구축
다양한 NPC 역할 추가
장기 기억(memory) 시스템 추가
퀘스트 분기 확장
Unity 내 UI와 애니메이션에 직접 연결
