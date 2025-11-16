---

description: "Tasks for implementing 001-conversational-flight-search"
---

# Tasks: 001-conversational-flight-search

**Input**: Design documents from `/specs/001-conversational-flight-search/`
**Prerequisites**: plan.md (required), spec.md (required), research.md (optional), data-model.md (optional), contracts/ (optional)

**Tests**: Tests are optional. This MVP focuses on delivering independently testable user stories without mandatory test scaffolding unless later requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository initialization and basic project structure

- [ ] T001 Create project directory structure at `int-travel-planner/`
- [ ] T002 Initialize backend dependencies in `int-travel-planner/backend/requirements.txt`
- [ ] T003 [P] Create Python project metadata in `int-travel-planner/backend/pyproject.toml`
- [ ] T004 [P] Scaffold FastAPI app in `int-travel-planner/backend/app/main.py`
- [ ] T005 [P] Add env sample in `int-travel-planner/.env.example`
- [ ] T006 [P] Add backend Dockerfile in `int-travel-planner/backend/Dockerfile`
- [ ] T007 [P] Add docker compose with Redis in `int-travel-planner/docker-compose.yml`
- [ ] T008 [P] Initialize frontend scaffold in `int-travel-planner/frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure required before any user story

- [ ] T009 Implement settings and configuration in `int-travel-planner/backend/app/config/settings.py`
- [ ] T010 [P] Implement structured JSON logging in `int-travel-planner/backend/app/utils/logging.py`
- [ ] T011 [P] Implement exceptions and error codes in `int-travel-planner/backend/app/utils/exceptions.py`
- [ ] T012 [P] Implement metrics helper in `int-travel-planner/backend/app/utils/metrics.py`
- [ ] T013 [P] Implement Redis client with TTL in `int-travel-planner/backend/app/services/redis_client.py`
- [ ] T014 [P] Add health endpoints in `int-travel-planner/backend/app/api/health.py`
- [ ] T015 [P] Wire routers and CORS in `int-travel-planner/backend/app/main.py`
- [ ] T068 [P] Add input validation middleware in `int-travel-planner/backend/app/api/middleware/input_validator.py` to enforce MAX_MESSAGE_LENGTH (2000 chars), truncate if exceeded, and emit structured log event
- [ ] T016 [P] Create prompts registry in `int-travel-planner/backend/app/prompts/registry.py`
- [ ] T017 [P] Create initial prompt files in `int-travel-planner/backend/app/prompts/`
- [ ] T018 [P] Create Pydantic model files in `int-travel-planner/backend/app/models/{intent.py,flight.py,session.py}`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

- [ ] T058 [P] Add WebSocket chat endpoint in `int-travel-planner/backend/app/api/chat.py` and route in `int-travel-planner/backend/app/main.py`

---

## Phase 3: User Story 1 - Basic Intent Extraction and Flight Search (Priority: P1) 🎯 MVP

**Goal**: Extract travel intent from natural language and return 3–5 ranked flight options via Amadeus

**Independent Test**: POST to `/api/v1/chat/message` with a natural language request returns 3–5 flights including airline, price (USD), duration, and stops within 5s p95.

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement `TravelIntent` schema in `int-travel-planner/backend/app/models/intent.py`
- [ ] T020 [P] [US1] Implement `FlightSegment` and `FlightOption` in `int-travel-planner/backend/app/models/flight.py`
- [ ] T021 [P] [US1] Implement `Session` and `ConversationMessage` in `int-travel-planner/backend/app/models/session.py`
- [ ] T022 [US1] Implement Amadeus OAuth2 client in `int-travel-planner/backend/app/services/amadeus_client.py`
- [ ] T023 [US1] Implement flight search tool in `int-travel-planner/backend/app/agents/tools/flight_search.py`
- [ ] T024 [US1] Implement ranking (50% price, 30% duration, 20% direct) in `int-travel-planner/backend/app/agents/tools/result_ranker.py`
- [ ] T025 [US1] Implement intent extractor tool using OpenAI in `int-travel-planner/backend/app/agents/tools/intent_extractor.py`
- [ ] T026 [US1] Implement agent orchestrator in `int-travel-planner/backend/app/agents/orchestrator.py`
- [ ] T067 [US1] Enforce Pydantic schema validation on all LLM/tool outputs in `int-travel-planner/backend/app/agents/orchestrator.py` with retry on malformed responses (max 2 attempts)
- [ ] T056 [US1] Implement scope guardrails in `int-travel-planner/backend/app/agents/orchestrator.py` and enforce via `int-travel-planner/backend/app/prompts/system_agent_v1.0.0.txt`
- [ ] T057 [P] [US1] Add prompt injection detection and guardrails in `int-travel-planner/backend/app/validators/guardrails.py` and integrate into orchestrator
- [ ] T060 [P] [US1] Implement IATA airport validation (Amadeus Locations API or cached list) in `int-travel-planner/backend/app/validators/airport_codes.py` and use in `intent_validator.py`
- [ ] T027 [US1] Implement chat endpoint (POST) in `int-travel-planner/backend/app/api/chat.py`
- [ ] T028 [US1] Wire chat router in `int-travel-planner/backend/app/main.py`
- [ ] T029 [US1] Format response with 3–5 top results in `int-travel-planner/backend/app/api/chat.py`

**Checkpoint**: User Story 1 is fully functional and testable independently

---

## Phase 4: User Story 2 - Multi-Turn Context and Search Refinement (Priority: P1)

**Goal**: Maintain context across turns and support refinements like cheaper and direct-only

**Independent Test**: After US1, user says “show me cheaper options” and receives updated results filtered to <80% of previous lowest price; context retained without repeating origin/destination.

### Implementation for User Story 2

- [ ] T030 [US2] Persist and fetch session state in `int-travel-planner/backend/app/services/redis_client.py`
- [ ] T031 [US2] Apply context in orchestrator across turns in `int-travel-planner/backend/app/agents/orchestrator.py`
- [ ] T032 [US2] Implement "cheaper" refinement (<80% lowest) in `int-travel-planner/backend/app/agents/tools/flight_search.py`
- [ ] T033 [P] [US2] Implement `prefer_direct` filtering in `int-travel-planner/backend/app/agents/tools/flight_search.py`
- [ ] T034 [US2] Update response messaging to explain refinements in `int-travel-planner/backend/app/api/chat.py`

**Checkpoint**: User Story 2 is independently testable with multi-turn flow

---

## Phase 5: User Story 3 - Intelligent Clarification Questions (Priority: P1)

**Goal**: Ask targeted clarifying questions when confidence <0.7 or parameters missing

**Independent Test**: Vague input like “I want to travel next month” triggers a single, targeted question (e.g., origin) with suggestion options.

### Implementation for User Story 3

- [ ] T035 [US3] Implement clarification tool in `int-travel-planner/backend/app/agents/tools/generate_clarification.py`
- [ ] T036 [US3] Add low-confidence routing (<0.7) to clarifications in `int-travel-planner/backend/app/agents/orchestrator.py`
- [ ] T037 [P] [US3] Implement missing-parameter validator in `int-travel-planner/backend/app/validators/intent_validator.py`
- [ ] T038 [US3] Add clarification prompt in `int-travel-planner/backend/app/prompts/clarification_v1.0.0.txt`

**Checkpoint**: User Story 3 independently testable with controlled clarifications

---

## Phase 6: User Story 4 - Itinerary Summary Generation (Priority: P2)

**Goal**: Generate a formatted itinerary summary for a selected option with deep link

**Independent Test**: After a user indicates a specific option, the system returns a markdown/text summary with flight details and booking link.

### Implementation for User Story 4

- [ ] T039 [US4] Implement itinerary generator tool in `int-travel-planner/backend/app/agents/tools/itinerary_generator.py`
- [ ] T040 [US4] Support selection input and summary return in `int-travel-planner/backend/app/api/chat.py`
- [ ] T041 [P] [US4] Add formatting template support in `int-travel-planner/backend/app/prompts/system_agent_v1.0.0.txt`

- [ ] T061 [US4] Implement `booking_url` generation strategy in `int-travel-planner/backend/app/services/booking_links.py` and integrate with itinerary generator

**Checkpoint**: User Story 4 delivers copyable itinerary summaries

---

## Phase 7: User Story 5 - Graceful Error Handling and Fallbacks (Priority: P2)

**Goal**: Resilient behavior with retries, user-friendly errors, and mock fallback

**Independent Test**: Simulate Amadeus timeout: retries then fallback to static mock flights with disclaimer; conversational error messages.

### Implementation for User Story 5

- [ ] T042 [US5] Implement retry/backoff utility in `int-travel-planner/backend/app/utils/retry.py`
- [ ] T043 [US5] Add mock flight dataset service in `int-travel-planner/backend/app/services/mock_data.py`
- [ ] T044 [US5] Integrate fallback to mock data with disclaimer in `int-travel-planner/backend/app/agents/tools/flight_search.py`
- [ ] T045 [P] [US5] Improve user-facing error messages in `int-travel-planner/backend/app/agents/orchestrator.py`
- [ ] T046 [US5] Implement simple rate limiting per session/IP in `int-travel-planner/backend/app/api/middleware/rate_limit.py`

**Checkpoint**: User Story 5 independently testable for resilience scenarios

---

## Phase 8: User Story 6 - Session Management and Context Limits (Priority: P3)

**Goal**: TTL-based session management and context pruning when approaching token limits

**Independent Test**: 40+ message conversation prunes older context, preserving last 3 exchanges + parameters; expired sessions restart cleanly.

### Implementation for User Story 6

- [ ] T047 [US6] Implement context pruning in `int-travel-planner/backend/app/agents/orchestrator.py`
- [ ] T048 [P] [US6] Ensure TTL expiry handling in `int-travel-planner/backend/app/services/redis_client.py`
- [ ] T049 [US6] Handle expired sessions with friendly restart in `int-travel-planner/backend/app/api/chat.py`

**Checkpoint**: User Story 6 independently testable with long conversations

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements spanning multiple stories and docs

- [ ] T050 [P] Update API docs in `int-travel-planner/docs/api.md`
- [ ] T051 [P] Update error codes reference in `int-travel-planner/docs/error-codes.md`
- [ ] T052 Code cleanup and refactoring across `int-travel-planner/backend/app/`
- [ ] T053 Performance instrumentation in `int-travel-planner/backend/app/utils/metrics.py`
- [ ] T054 [P] Add quickstart guide in `int-travel-planner/specs/001-conversational-flight-search/quickstart.md`
- [ ] T055 [P] Add golden dataset JSONs in `int-travel-planner/backend/tests/golden_dataset/`

- [ ] T059 [P] Add WebSocket client hook in `int-travel-planner/frontend/src/hooks/useWebSocket.ts` and integrate in `int-travel-planner/frontend/src/components/ChatInterface.tsx`
- [ ] T062 [P] Add load testing with Locust in `int-travel-planner/backend/tests/load/locustfile.py` targeting 1000 concurrent sessions
- [ ] T063 [P] Add p95 latency measurement and CI gate; expose operation timings and fail build if p95 > 5s (scripts + CI)
- [ ] T064 [P] Add token usage and cost tracking metrics in `int-travel-planner/backend/app/utils/metrics.py` and logging enrichment
- [ ] T065 [P] Add prompt regression tests and CI workflow in `.github/workflows/ai-quality.yml` using golden datasets
- [ ] T066 [P] Expose Prometheus metrics and add basic dashboards/alerts (Grafana or provider alternative)
- [ ] T069 [P] Add optional post-search satisfaction prompt in `int-travel-planner/backend/app/api/chat.py` (thumbs up/down) and log satisfaction_signal event to support SC-006

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): No dependencies — can start immediately
- Foundational (Phase 2): Depends on Setup completion — BLOCKS all user stories
- User Stories (Phases 3–8): Depend on Foundational completion; execute P1 first
- Polish (Phase 9): Depends on desired user stories being complete

### User Story Dependencies

- User Story 1 (P1): Starts after Phase 2; no dependency on other stories
- User Story 2 (P1): Starts after Phase 2; uses US1 components but is independently testable
- User Story 3 (P1): Starts after Phase 2; independently testable
- User Story 4 (P2): Starts after US1 (selection context) but independently testable via direct input
- User Story 5 (P2): Starts after US1 (flight search path) but can be validated independently via simulated failures
- User Story 6 (P3): Starts after Phase 2; independently testable

### Parallel Opportunities

- Setup: T003–T008 can run in parallel
- Foundational: T010–T018 can run in parallel
- US1: T019–T021 in parallel (models), then T022–T029 sequentially
- US2: T033 in parallel with T032
- US3: T037 in parallel with T035/T038
- US4: T041 in parallel with T039–T040
- US5: T045 in parallel with T042–T044
- US6: T048 in parallel with T047/T049

---

## Parallel Execution Examples

- US1 models together:
  - Task: "Implement TravelIntent schema in `backend/app/models/intent.py`"
  - Task: "Implement FlightSegment and FlightOption in `backend/app/models/flight.py`"
  - Task: "Implement Session and ConversationMessage in `backend/app/models/session.py`"

- US5 resilience tasks:
  - Task: "Implement retry/backoff utility in `backend/app/utils/retry.py`"
  - Task: "Add mock flight dataset service in `backend/app/services/mock_data.py`"

---

## Implementation Strategy

- MVP First: Complete Phases 1–2, then Phase 3 (US1). Validate end-to-end via `/api/v1/chat/message`.
- Incremental Delivery: Add US2 → US3 (P1), then US4–US5 (P2), then US6 (P3).
- Parallelization: After Phase 2, assign US1–US3 to separate threads if capacity allows.
