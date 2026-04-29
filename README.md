SW Mid Project - Guide Companion NPC Multi-Agent System
1. 프로젝트 개요

본 프로젝트는 Unity와 연동 가능한 가이드형 동행 NPC 응답 생성 시스템을 설계하는 것이다.
이 NPC는 게임 내에서 주인공의 곁에 항상 함께하며, 단순히 정해진 대사를 반복하는 일반 NPC가 아니라 플레이어의 상황을 분석하고 스스로 적절한 도움을 제공하는 특수목적 AI 에이전트 시스템이다.

본 시스템은 플레이어 상태, 플레이어 행동 습관, 게임 세계의 맥락, 시간, 날씨, 스토리 진행도, 최근 대화, NPC 기억, 현재 가능한 선택지 등 다양한 정보를 동시에 입력으로 받아 여러 서브에이전트가 단계적으로 추론한 뒤 NPC의 대사, 감정, 행동, 가이드 메시지를 생성하는 구조를 목표로 한다.

예를 들어, 플레이어의 체력이 낮고 회복 아이템이 없으며 위험 지역으로 향하고 있다면 NPC는 생존을 우선시하여 안전한 회복 루트를 안내할 수 있다. 또한 플레이어가 장기간 메인 스토리를 진행하지 않고 있다면 NPC는 현재 목표를 상기시키고 스토리 진행을 유도하는 방향으로 반응할 수 있다.

이 프로젝트의 핵심은 단순한 규칙 기반 NPC가 아니라, 많은 종류의 정보를 해석하고 우선순위를 판단하며 플레이어에게 가장 적절한 방식으로 개입하는 가이드형 동행 NPC를 멀티에이전트 구조로 구현하는 데 있다.

2. 에이전트 목표

이 에이전트 팀의 목표는 다음과 같다.

플레이어의 현재 상태를 분석한다.
플레이어의 행동 습관과 반복 패턴을 분석한다.
게임 세계의 맥락과 위험도를 해석한다.
메인 스토리 진행도와 최종 목표와의 관계를 판단한다.
최근 대화와 NPC 기억을 바탕으로 일관성 있는 반응을 유지한다.
현재 상황에서 가장 중요한 문제를 우선순위화한다.
플레이어에게 필요한 선택지만 남기고 불필요한 선택지는 줄인다.
NPC가 지금 말해야 하는지, 조용히 있어야 하는지, 강하게 개입해야 하는지를 결정한다.
최종적으로 대사, 감정, 행동, 가이드 메시지를 생성한다.
결과가 세계관, 캐릭터 성격, 최근 대화와 충돌하지 않는지 검증한다.

즉, 본 프로젝트의 핵심 목표는 많은 입력 요소를 여러 서브에이전트가 분담하여 해석하고 통합한 뒤, 상황에 따라 자연스럽고 설명 가능한 가이드형 NPC 반응을 생성하는 것이다.

3. 왜 멀티에이전트 구조가 필요한가

이 프로젝트에서는 입력 요소가 매우 많다.
단순한 if-else 규칙이나 하나의 함수만으로는 다음과 같은 복합 상황을 충분히 처리하기 어렵다.

플레이어의 HP는 낮지만 스토리 진행도도 장기간 정체되어 있는 경우
현재 날씨와 시간 때문에 평소의 안전 루트가 더 이상 안전하지 않은 경우
플레이어가 같은 힌트를 여러 번 무시한 경우
플레이어의 성향에 따라 같은 정보라도 다른 방식으로 전달해야 하는 경우
현재 가능한 선택지가 너무 많아 정보 과부하가 생기는 경우

따라서 본 시스템은 하나의 거대한 함수로 처리하는 대신, 서로 다른 역할을 담당하는 여러 서브에이전트가 정보를 나누어 분석하고, 우선순위를 정하고, 개입 수준을 조절하고, 최종 응답을 생성하는 구조로 설계하였다.

이러한 구조는 다음과 같은 장점이 있다.

복잡한 입력을 역할별로 분리하여 처리할 수 있다.
왜 특정 대사와 행동이 선택되었는지 설명하기 쉽다.
기능 확장과 유지보수가 쉽다.
게임 상황에 따라 더 적응적인 NPC 반응을 만들 수 있다.
4. 시스템 구조

본 시스템은 다음과 같은 계층 구조를 가진다.

입력 계층
플레이어 상태
플레이어 행동 습관
세계 맥락
스토리 맥락
최근 대화
NPC 기억
현재 가능한 선택지
분석 계층
플레이어 행동 분석
플레이어 상태 분석
세계 상황 분석
스토리 진행 추적
기억 관리
플레이어 모델 추정
판단 계층
우선순위 결정
선택지 필터링
개입 정도 판단
가이드 의도 결정
생성 계층
대사, 감정, 행동, 가이드 메시지 생성
검증 계층
자기 비판 및 일관성 점검
설명 계층
reasoning trace 생성
피드백 계층
플레이어 반응 결과를 기억과 모델에 반영
5. 서브에이전트 구성

본 시스템은 고품질 가이드형 동행 NPC를 위해 다음과 같은 서브에이전트 구조를 가진다.

PlayerBehaviorAnalyzer
PlayerStateAnalyzer
WorldContextReasoner
StoryGoalTracker
MemoryAgent
PlayerModelEstimator
PriorityManager
ChoiceFilterAgent
InterventionController
GuideIntentPlanner
DialogueEmotionActionGenerator
SelfCriticConsistencyAgent
ReasoningTraceBuilder
OutcomeFeedbackLearner
6. 각 서브에이전트의 역할
1) PlayerBehaviorAnalyzer

플레이어의 행동 패턴을 분석한다.

주요 분석 요소:

같은 장소를 오래 맴도는지
잘못된 방향으로 반복 이동하는지
전투를 자주 피하는지
힌트를 무시하는지
탐험형인지 직진형인지

역할:

플레이어가 길을 잃었는지 판단
반복 실수와 행동 습관 분석
2) PlayerStateAnalyzer

플레이어의 현재 상태를 분석한다.

주요 분석 요소:

HP
스태미나
인벤토리
회복 아이템 유무
전투 가능 여부
현재 위치

역할:

생존 위험도 판단
즉각적인 지원이 필요한지 판단
3) WorldContextReasoner

게임 세계의 맥락을 분석한다.

주요 분석 요소:

시간
날씨
지역 위험도
주변 몬스터
환경 이벤트
안전 루트

역할:

현재 환경이 안전한지 위험한지 판단
이동 및 안내 방향 제안
4) StoryGoalTracker

스토리 진행을 추적한다.

주요 분석 요소:

메인 퀘스트 진행도
장기간 정체 여부
현재 목표와 최종 목표의 거리
플레이어의 스토리 회피 여부

역할:

지금 스토리 진행을 유도해야 하는지 판단
5) MemoryAgent

NPC의 기억을 관리한다.

기억 종류:

단기 기억: 직전 대화, 최근 조언, 최근 경고
중기 기억: 자주 막히는 구간, 반복 실수, 최근 플레이어 반응
장기 기억: 플레이어 성향, NPC와의 관계, 선호하는 안내 방식

역할:

같은 내용을 반복하지 않도록 조절
플레이어와의 친밀감과 일관성 유지
6) PlayerModelEstimator

플레이어 타입을 추정한다.

예시:

탐험형
최단 진행형
신중형
전투 회피형
힌트 선호형
힌트 비선호형

역할:

플레이어 성향에 맞는 말투와 개입 방식 선택
7) PriorityManager

현재 가장 중요한 문제를 결정한다.

우선순위 후보:

생존
길 안내
스토리 진행
감정적 위로
침묵

역할:

여러 입력이 동시에 들어왔을 때 무엇을 먼저 처리할지 결정
8) ChoiceFilterAgent

현재 플레이어에게 필요한 선택지만 정리한다.

역할:

불필요한 선택지 제거
정보 과부하 감소
플레이어 성향에 맞는 선택지 우선 제공
9) InterventionController

NPC가 얼마나 개입해야 하는지 결정한다.

개입 방식 예시:

조용히 있음
짧은 힌트 제공
부드러운 유도
강한 경고
감정적 격려

역할:

너무 많이 말하는 NPC가 되지 않도록 조절
필요한 순간에만 적절한 방식으로 개입
10) GuideIntentPlanner

NPC의 최종 의도를 결정한다.

의도 예시:

경고
안전 루트 안내
회복 유도
스토리 진행 촉구
탐험 제안
위로
목표 상기

역할:

무엇을 말할지보다 먼저 왜 말하는지를 결정
11) DialogueEmotionActionGenerator

최종 NPC 응답을 생성한다.

출력:

대사
감정
행동
가이드 메시지
긴급도
필요 시 목표 리마인드
12) SelfCriticConsistencyAgent

출력의 품질과 일관성을 점검한다.

점검 요소:

세계관과의 일치 여부
NPC 성격과의 일치 여부
최근 발화와의 중복 여부
과도한 개입 여부
플레이어 자유를 침해하는지 여부

역할:

부자연스럽거나 과도한 응답을 수정
13) ReasoningTraceBuilder

왜 이런 응답이 나왔는지 설명 가능한 형태로 기록한다.

기록 요소:

primary reason
secondary reason
chosen priority
rejected options
final rationale

역할:

추론 과정을 보고서나 발표에서 설명 가능하게 만듦
14) OutcomeFeedbackLearner

NPC의 조언이 실제로 어떤 결과를 냈는지 반영한다.

학습 요소:

플레이어가 조언을 따랐는가
힌트를 무시했는가
개입이 너무 강했는가
스토리 진행이 개선되었는가

역할:

MemoryAgent와 PlayerModelEstimator에 결과를 반영하여 점진적으로 적응적 NPC를 만듦
7. 동작 원리

본 시스템은 다음과 같은 다단계 추론 흐름으로 동작한다.

입력 계층에서 플레이어 상태, 행동 습관, 세계 맥락, 스토리 정보, 최근 대화, 기억, 선택지 정보를 수집한다.
분석 계층에서 각 서브에이전트가 자신의 역할에 맞게 정보를 해석한다.
판단 계층에서 PriorityManager가 현재 가장 중요한 문제를 정하고, ChoiceFilterAgent와 InterventionController가 선택지와 개입 수준을 정리한다.
GuideIntentPlanner가 NPC가 어떤 의도로 반응해야 하는지 결정한다.
DialogueEmotionActionGenerator가 최종 대사, 감정, 행동, 가이드 메시지를 생성한다.
SelfCriticConsistencyAgent가 결과를 검토하고 필요 시 수정한다.
ReasoningTraceBuilder가 최종 응답이 어떤 이유로 선택되었는지 기록한다.
플레이어의 이후 반응은 OutcomeFeedbackLearner를 통해 다시 기억과 플레이어 모델에 반영된다.

즉, 하나의 단순 함수가 결과를 만드는 것이 아니라, 역할이 나뉜 여러 에이전트가 단계적으로 추론하고 협업하여 최종 응답을 만든다.

8. 입력 정보 설계

본 시스템은 다음과 같은 입력 정보를 사용한다.

플레이어 상태
HP
스태미나
인벤토리
위치
전투 가능 여부
회복 자원 여부
플레이어 행동 습관
최근 이동 패턴
반복 실수
길 잃음 여부
스토리 회피 경향
힌트 수용 여부
세계 맥락
시간
날씨
지역 위험도
주변 몬스터
안전 루트
환경 이벤트
스토리 정보
메인 퀘스트 진행도
현재 목표
최종 목표
장기 정체 여부
대화 정보
최근 대화
현재 플레이어 요청
현재 대화 상황
기억 정보
단기 기억
중기 기억
장기 기억
선택지 정보
현재 가능한 행동 후보
숨겨도 되는 선택지
지금 우선 제시해야 하는 선택지
9. 출력 정보 설계

본 시스템의 출력은 다음과 같다.

dialogue
emotion
action
guidance
urgency_level
optional objective reminder
reasoning_trace

즉, 단순한 대사 한 줄만 생성하는 것이 아니라, NPC의 감정과 행동, 유도 메시지, 긴급도, 추론 근거까지 함께 생성하는 것을 목표로 한다.

10. 예상 사용 시나리오
시나리오 1

플레이어의 체력이 매우 낮고 회복 아이템이 없으며 위험한 지역으로 향하고 있다.
이 경우 NPC는 생존을 최우선으로 판단하고, 회복 아이템을 얻을 수 있는 안전한 경로를 제안한다.

시나리오 2

플레이어가 오랫동안 메인 스토리를 진행하지 않고 있다.
이 경우 NPC는 현재 목표와 최종 목표를 비교하여 스토리 진행의 필요성을 강조하는 가이드 메시지를 생성한다.

시나리오 3

플레이어가 같은 구간에서 계속 길을 잃고 있다.
이 경우 NPC는 단순한 방향 안내가 아니라, 플레이어 행동 패턴을 반영하여 더 직접적인 안내를 제공한다.

시나리오 4

플레이어가 이미 여러 번 같은 힌트를 무시했다.
이 경우 NPC는 말투나 개입 강도를 조정하여 다른 방식으로 도움을 제공한다.

11. MVP와 확장 계획
Step 1: 설계 단계

현재 단계이다.
멀티에이전트 구조, 서브에이전트 역할, 입력 및 출력 설계, 동작 원리를 정의하였다.

Step 2: MVP 구현

우선 다음 요소를 중심으로 기본 동작 가능한 백엔드를 구현한다.

PlayerBehaviorAnalyzer
PlayerStateAnalyzer
WorldContextReasoner
StoryGoalTracker
MemoryAgent
PriorityManager
InterventionController
GuideIntentPlanner
DialogueEmotionActionGenerator
SelfCriticConsistencyAgent
ReasoningTraceBuilder

목표:

JSON 입력 받기
다단계 추론 실행
JSON 출력 반환
reasoning_trace 포함
로컬 테스트 가능
Step 3: 고품질 확장

이후 다음 기능을 강화한다.

PlayerModelEstimator 정교화
ChoiceFilterAgent 추가
OutcomeFeedbackLearner 추가
기억 계층 강화
개입 강도 제어 개선
자기 비판 및 일관성 검증 강화
플레이어 반응 기반 피드백 반영
12. 기대 효과

본 프로젝트를 통해 다음과 같은 효과를 기대할 수 있다.

단순 규칙형 NPC보다 더 적응적인 가이드 경험 제공
플레이어의 상태와 성향에 맞는 맞춤형 지원 가능
NPC와의 친밀감 및 동행감 향상
오픈월드에서 과도한 선택지를 줄여 방향성 제공
다단계 추론 구조를 통한 설명 가능한 AI 에이전트 설계 경험 확보
Unity와 AI 백엔드 연동 구조 학습
13. 현재 진행 상태

현재는 Step 1 설계 단계가 완료된 상태이다.
즉, 본 README에는 시스템의 전체 구조, 에이전트 목표, 서브에이전트 역할, 동작 원리, 입력과 출력 설계, MVP 및 확장 계획이 정리되어 있다.

다음 단계에서는 이 설계를 바탕으로 Python backend와 JSON 기반 API를 구현하고, Unity와 연동 가능한 MVP 버전을 제작할 예정이다.

14. GitHub URL

프로젝트 코드:
https://github.com/kiyukin/SW-Mid-project-NPC
## Current Status

현재 실행 모드: Deep Agents mode confirmed  
fallback mode도 유지됨  
현재 출력 확인 완료  
일부 서브에이전트는 아직 빈 JSON 출력이 있어 prompt 개선 필요  
Step 3는 부분 반영 상태  

## Step 3 Refactor Goal

The next step is to upgrade the current MVP into a higher-quality guide companion NPC system.

Planned improvements:
- richer memory structure
- player model estimation
- better priority decisions
- better intervention control
- choice filtering
- stronger self-critique
- richer reasoning_trace
- feedback-learning-ready structure
