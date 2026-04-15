# Unity-Integrated DeepAgents NPC Reasoning Demo

A minimal multi-agent NPC reasoning backend (Python) with a Unity client example.

Goal: Given a JSON input from Unity containing player, world, and NPC data, the Python backend (DeepAgents-powered) returns structured JSON with intent, dialogue, quest, emotion, and action.

Folder structure:
- backend/
  - main.py               # Minimal HTTP server exposing POST /npc; structured logging
  - agents.py             # Explicit 5-step multi-agent pipeline (LLM vs heuristic modes)
  - models.py             # Data models and schema (includes reasoning_trace in output)
  - prompts.py            # Agent system prompts
  - sample_input.json     # Example payload for local testing
- unity/
  - NPCClient.cs          # Unity MonoBehaviour example sending/receiving JSON

Requirements/Assumptions:
- Python 3.10+
- Optional: deepagents-cli installed and configured. If not available, the backend falls back to a small rule-based heuristic so it still runs locally.
- Unity 2020+ (for the example script), using UnityWebRequest.

Run backend locally:
1) python3 -m backend.main
   - Starts HTTP server at http://127.0.0.1:8089/npc
2) Test with curl:
   curl -s -X POST http://127.0.0.1:8089/npc -H "Content-Type: application/json" -d @backend/sample_input.json | jq .

Unity usage:
- Add unity/NPCClient.cs to a GameObject in your scene.
- Ensure the backend is running locally (URL set in script: http://127.0.0.1:8089/npc).
- Press Play; the Start() example sends a request and logs the parsed response.

Design notes:
- Sub-agents (logical roles):
  1) PlayerStateAnalyzer
  2) WorldContextReasoner
  3) NPCIntentPlanner
  4) DialogueActionGenerator
  5) ConsistencyCritic
- Reasoning flow (explicit, logged):
  1) PlayerStateAnalyzer => PlayerAnalysis
  2) WorldContextReasoner => WorldAnalysis
  3) NPCIntentPlanner => NPCIntent
  4) DialogueActionGenerator => Draft NPC content
  5) ConsistencyCritic => Final NPCResponse
  - Each step logs a structured JSON record and is appended to reasoning_trace returned to Unity.
- Output schema (example):
  {
    "intent": "warn_and_offer_quest",
    "dialogue": "This forest is dangerous at night...",
    "quest": {"title":"Herbs for Survival","objective":"Collect 3 herbs near the village","reward":"healing_potion"},
    "emotion": "concerned",
    "action": "point_to_safe_path"
  }

Configuration:
- By default, the backend tries to import DeepAgents (deepagents_cli.llm.chat_completion). If unavailable, it uses a deterministic heuristic so you have a working demo without API keys.
- To enable a real LLM via deepagents-cli, install/configure DeepAgents and set your model/provider env per its docs.

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

6. 입력 / 출력 형식
입력 예시

player:

level: 3
hp: 20
inventory: sword, herb
completed_quests: empty list

world:

location: forest
time: night
danger_level: high

npc:

name: Elder Rowan
role: healer
personality: kind but cautious
relationship: neutral
출력 예시
intent: warn_and_offer_quest
dialogue: Night brings danger. Bring me three fresh herbs and I shall brew medicine for you.
emotion: concerned
action: point_to_safe_path
quest:
title: Herbs for Survival
objective: Collect 3 herbs near the village
reward: healing_potion

또한 reasoning_trace를 통해 각 서브에이전트의 출력 결과를 확인할 수 있다.

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

현재 환경에서는 DeepAgents가 설치 또는 연결되지 않아 시스템은 heuristic fallback mode로 실행된다.

즉, 현재는 다음 상태이다.

멀티에이전트 구조: 구현 완료
단계별 추론 로그: 구현 완료
Unity 연동 가능 구조: 구현 완료
DeepAgents 본 실행 모드: 미적용
fallback heuristic 모드: 적용 완료

이로 인해 시스템 구조와 동작 원리는 충분히 확인할 수 있지만, 향후에는 DeepAgents 본 모드로 전환하여 실제 LLM 기반 멀티에이전트 실행까지 확장할 수 있다.

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
