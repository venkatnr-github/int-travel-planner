# Implementation Plan: Conversational Flight Search

**Feature**: 001-conversational-flight-search  
**Branch**: `001-conversational-flight-search`  
**Created**: 2025-11-15  
**Status**: Planning

---

## Executive Summary

**Objective**: Build MVP conversational flight search agent that extracts user intent from natural language, searches via Amadeus API, and provides intelligent recommendations through multi-turn dialogue.

**Core Hypothesis**: Users prefer conversational interfaces over traditional form-based flight search.

**Success Metrics**:
- <60 seconds from intent to results
- <6 conversational turns average
- 80%+ intent extraction accuracy
- <$0.05 per conversation cost

**Timeline Estimate**: 4-5 weeks (includes CI/CD setup + P1 features for MVP validation)

**Risk Level**: MEDIUM
- High: OpenAI Agents SDK adoption (newer technology, less community resources)
- Medium: Amadeus API free tier limits (2K calls/month)
- Low: Redis session management (well-established pattern)

**Critical Path**: CI/CD infrastructure must be established BEFORE any feature implementation begins to ensure quality gates and automated testing from day one.

---

## Technical Context

### Architecture Overview

```
┌─────────────┐         WebSocket/HTTP        ┌──────────────┐
│   React     │────────────────────────────────│   FastAPI    │
│  Frontend   │                                │   Backend    │
└─────────────┘                                └──────┬───────┘
                                                      │
                                         ┌────────────┼────────────┐
                                         │            │            │
                                    ┌────▼───┐  ┌────▼────┐  ┌───▼────┐
                                    │ OpenAI │  │ Amadeus │  │ Redis  │
                                    │  GPT-4 │  │   API   │  │Session │
                                    └────────┘  └─────────┘  └────────┘
```

**Agent Orchestration Flow**:
```
User Message → FastAPI Endpoint → Agent Orchestrator
                                        ↓
                                   Intent Extractor (LLM Tool)
                                        ↓
                                   Validate Parameters
                                        ↓
                              ┌─────────┴──────────┐
                              ↓                    ↓
                         Search Flights       Ask Clarification
                         (Amadeus Tool)       (LLM Response)
                              ↓                    │
                         Rank Results              │
                              ↓                    │
                         Format Response           │
                              ↓                    │
                         Update Session ←──────────┘
                              ↓
                         Return to User
```

### Technology Stack (Constitution-Locked)

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Backend** | Python | 3.11+ | Rich AI/ML ecosystem, native OpenAI SDK |
| **Framework** | FastAPI | 0.104+ | Async, WebSocket, OpenAPI docs |
| **Agent SDK** | OpenAI Agents SDK | Latest | Native integration, simpler than LangChain |
| **LLM** | OpenAI GPT-4 | gpt-4-turbo | Function calling, conversational quality |
| **Session Store** | Redis | 7.0+ | Low latency, TTL support |
| **Flight API** | Amadeus Self-Service | v1 | Free tier 2K calls/month |
| **Frontend** | React | 18+ | shadcn/ui components |
| **Validation** | Pydantic | 2.0+ | Schema validation, type safety |

### Dependency Matrix

| Dependency | Purpose | Fallback Strategy |
|------------|---------|-------------------|
| OpenAI GPT-4 | Intent extraction, conversation | CRITICAL - No fallback, fail gracefully |
| Amadeus API | Flight data | Fallback to static mock data with disclaimer |
| Redis | Session storage | In-memory fallback (single instance only) |
| Frontend | User interface | Can test with Postman/curl initially |

### Data Models (Pydantic Schemas)

```python
# Core Entities from spec.md

class TravelIntent(BaseModel):
    """Extracted structured data from user input"""
    origin: Optional[str] = Field(None, min_length=3, max_length=3)  # IATA code
    destination: Optional[str] = Field(None, min_length=3, max_length=3)
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    passengers: Optional[int] = Field(None, ge=1, le=9)
    max_price: Optional[int] = None
    prefer_direct: bool = False
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class FlightSegment(BaseModel):
    """One leg of a flight"""
    departure_airport: str  # IATA code
    departure_time: datetime
    arrival_airport: str
    arrival_time: datetime
    flight_number: str
    aircraft_type: Optional[str] = None

class FlightOption(BaseModel):
    """Single flight search result"""
    flight_id: str
    airline: str
    price_usd: float
    currency: str = "USD"
    duration_minutes: int
    stops: int
    outbound_segment: FlightSegment
    return_segment: FlightSegment
    booking_url: str
    relevance_score: float  # For ranking algorithm

class Session(BaseModel):
    """Active conversation session"""
    session_id: str
    conversation_history: List[ConversationMessage]
    extracted_parameters: Optional[TravelIntent] = None
    last_search_results: List[FlightOption] = []
    last_search_lowest_price: Optional[float] = None  # For refinement
    created_at: datetime
    last_activity: datetime
    message_count: int = 0

class ConversationMessage(BaseModel):
    """Single turn in conversation"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
```

### Configuration Management

```python
# config/settings.py

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_MAX_TOKENS: int = 8000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Amadeus
    AMADEUS_API_KEY: str
    AMADEUS_API_SECRET: str
    AMADEUS_BASE_URL: str = "https://test.api.amadeus.com"
    AMADEUS_TIMEOUT_SECONDS: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_SESSION_TTL: int = 3600  # 60 minutes (locked per constitution)
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Application
    APP_ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    ENABLE_MOCK_DATA: bool = False  # For development/testing
    
    # Performance
    MAX_MESSAGES_PER_SESSION: int = 50
    MAX_MESSAGE_LENGTH: int = 2000
    CONTEXT_WINDOW_WARNING_THRESHOLD: int = 6400  # 80% of 8000
    
    # Rate Limiting
    RATE_LIMIT_SESSIONS_PER_IP_PER_HOUR: int = 10
    
    class Config:
        env_file = ".env"
```

### Project Structure

```
int-travel-planner/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py            # Configuration
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py        # Main agent logic
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── intent_extractor.py
│   │   │       ├── flight_search.py
│   │   │       ├── result_ranker.py
│   │   │       └── itinerary_generator.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── intent.py
│   │   │   └── flight.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── amadeus_client.py
│   │   │   ├── redis_client.py
│   │   │   └── mock_data.py
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── registry.py            # Prompt version management
│   │   │   ├── system_agent_v1.0.0.txt
│   │   │   ├── intent_extraction_v1.0.0.txt
│   │   │   └── clarification_v1.0.0.txt
│   │   ├── validators/
│   │   │   ├── __init__.py
│   │   │   └── intent_validator.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                # WebSocket/HTTP endpoints
│   │   │   └── health.py              # Health checks
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logging.py
│   │       ├── exceptions.py
│   │       └── metrics.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── golden_dataset/
│   │   │   ├── intent_extraction.json
│   │   │   ├── conversation_flows.json
│   │   │   └── edge_cases.json
│   │   └── conftest.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── FlightCard.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── .specify/
│   ├── memory/
│   │   └── constitution.md            # Product governance
│   ├── scripts/
│   └── templates/
├── specs/
│   └── 001-conversational-flight-search/
│       ├── spec.md                    # Feature specification
│       ├── plan.md                    # Implementation plan
│       └── tasks.md                   # Task breakdown (to be generated)
├── docs/
│   ├── error-codes.md
│   └── api.md
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Constitution Check

### Alignment with Core Principles

| Principle | Compliance | Evidence |
|-----------|------------|----------|
| **I. Conversational-First** | ✅ PASS | Natural language intent extraction (FR-001), no forms, clarification questions (FR-005) |
| **II. Agent-Orchestrated** | ✅ PASS | Tools designed for agent consumption (search_flights, intent_extractor), OpenAI Agents SDK |
| **III. MVP Scope Discipline** | ✅ PASS | Only flight search, no hotels/booking/accounts. P1-P3 priorities clearly separated |
| **IV. Session-Based Stateless** | ✅ PASS | Redis sessions with TTL (FR-008), no database, no user accounts |
| **V. Single Integration** | ✅ PASS | Amadeus only (FR-003), mock fallback (FR-017), no multi-provider |
| **VI. Observability** | ✅ PASS | Comprehensive logging (FR-015), all tool invocations tracked, structured JSON format |
| **VII. AI-First Engineering** | ✅ PASS | Pydantic validation (FR-012), prompt versioning, golden datasets (SC-003), confidence scoring (FR-016) |

### Technology Stack Compliance

| Required | Specified | Status |
|----------|-----------|--------|
| Python 3.11+ | ✅ | Backend language |
| FastAPI | ✅ | Web framework |
| OpenAI GPT-4 | ✅ | LLM provider |
| OpenAI Agents SDK | ✅ | Agent framework |
| Redis | ✅ | Session storage |
| Amadeus API | ✅ | Flight data source |
| React 18+ | ✅ | Frontend framework |

**No prohibited technologies detected**. No vector DB, no traditional DB, no alternative LLMs.

### Gate Evaluation

**PRE-IMPLEMENTATION GATES:**

✅ **Conversational-First Gate**: All user stories describe natural language interaction  
✅ **Agent-Orchestrated Gate**: Tools architecture specified, no direct UI-service coupling  
✅ **Scope Gate**: Feature strictly within MVP boundaries (flight search only)  
✅ **Technology Gate**: All technologies from approved stack  
✅ **Cost Gate**: Estimated $55-90/month within $100 budget  

**PROCEED TO CI/CD SETUP: No blocking gate failures**

---

## Phase 0: CI/CD Infrastructure (CRITICAL PREREQUISITE)

### Overview

**Objective**: Establish automated quality gates, testing pipelines, and deployment infrastructure BEFORE any feature code is written.

**Rationale**: 
- Prevents technical debt accumulation
- Ensures code quality from first commit
- Enables safe, frequent deployments
- Catches regressions early (cheaper to fix)
- Constitutional requirement (Principle VI: Observability)

**Timeline**: 3-5 days (must complete before Phase 1)

**Blocking Requirement**: NO feature implementation can proceed until CI/CD pipelines are operational and passing.

### CI/CD Infrastructure

#### Continuous Integration Requirements

**GitHub Actions Workflows** (all workflows in `.github/workflows/`):

##### 1. Code Quality Pipeline (`ci-quality.yml`)
- **Trigger**: Pull request, push to main/feature branches
- **Steps**:
  - Python linting (ruff, black, isort)
  - Type checking (mypy)
  - Security scanning (bandit)
  - Dependency audit (pip-audit)
  - Code coverage threshold (>80%)
- **Exit Criteria**: All checks pass; coverage threshold met

##### 2. AI Quality Pipeline (`ai-quality.yml`)
- **Trigger**: Pull request affecting prompts/, models/, or agents/
- **Steps**:
  - Prompt regression tests (golden datasets)
  - Intent extraction accuracy validation (>80%)
  - Schema validation tests
  - Guardrail effectiveness tests
  - LLM response format validation
- **Exit Criteria**: Accuracy >80%; no hallucinations detected

##### 3. Integration Tests Pipeline (`ci-integration.yml`)
- **Trigger**: Pull request to main
- **Steps**:
  - Spin up test containers (Redis, FastAPI)
  - Run integration tests (user story flows)
  - Mock external APIs (Amadeus, OpenAI)
  - Verify HTTP + WebSocket endpoints
  - Session management tests
- **Exit Criteria**: All user story tests pass

##### 4. Performance Gating Pipeline (`ci-performance.yml`)
- **Trigger**: Pull request to main
- **Steps**:
  - Run load tests (Locust, 100 concurrent sessions)
  - Measure p95 latency for flight searches
  - Validate <5s p95 requirement (SC-005)
  - Check memory usage under load
- **Exit Criteria**: p95 <5s; no memory leaks detected

##### 5. Security Pipeline (`ci-security.yml`)
- **Trigger**: Pull request, daily schedule
- **Steps**:
  - Dependency vulnerability scanning (Snyk/Dependabot)
  - Container image scanning (Trivy)
  - Secret detection (TruffleHog)
  - API rate limit tests
- **Exit Criteria**: No HIGH/CRITICAL vulnerabilities; secrets removed

#### Continuous Deployment Requirements

##### Deployment Environments

**1. Development Environment**
- **Trigger**: Push to feature branches
- **Platform**: Railway/Render preview deployments
- **Configuration**:
  - `ENABLE_MOCK_DATA=true` (bypass Amadeus API)
  - OpenAI API with low rate limits
  - Redis test instance
- **Purpose**: Developer testing, PR reviews

**2. Staging Environment**
- **Trigger**: Merge to main branch
- **Platform**: Railway/Render staging
- **Configuration**:
  - Real Amadeus test API
  - OpenAI production API keys
  - Redis production-like instance
  - Full observability stack
- **Purpose**: Pre-production validation, stakeholder demos

**3. Production Environment**
- **Trigger**: Manual approval after staging validation
- **Platform**: Railway/Render production
- **Configuration**:
  - Production API keys
  - Upstash Redis (paid tier if needed)
  - Full monitoring/alerting
  - Rate limiting enabled
- **Deployment Strategy**: Blue-green or rolling update
- **Rollback**: Automatic on health check failure

##### Deployment Pipeline (`cd-deploy.yml`)

**Staging Deployment Steps**:
1. Build Docker images (backend, frontend)
2. Push to container registry
3. Run smoke tests against staging
4. Deploy to staging environment
5. Run post-deployment health checks
6. Notify team (Slack)

**Production Deployment Steps**:
1. Require manual approval
2. Tag release (semantic versioning)
3. Build production images
4. Deploy with zero-downtime strategy
5. Run production smoke tests
6. Monitor error rates for 10 minutes
7. Auto-rollback if error rate >5%
8. Update release notes

#### Infrastructure as Code

**Configuration Files**:
- `.github/workflows/*.yml`: All CI/CD pipelines
- `docker-compose.yml`: Local development
- `docker-compose.test.yml`: CI test environment
- `Dockerfile`: Multi-stage builds (dev, prod)
- `.dockerignore`: Exclude unnecessary files
- `railway.toml` or `render.yaml`: Deployment config

**Environment Variables** (stored in GitHub Secrets):
```
# OpenAI
OPENAI_API_KEY
OPENAI_ORG_ID

# Amadeus
AMADEUS_API_KEY
AMADEUS_API_SECRET

# Redis
REDIS_URL
REDIS_PASSWORD

# Monitoring
SENTRY_DSN
PROMETHEUS_ENDPOINT

# Deployment
RAILWAY_TOKEN / RENDER_API_KEY
```

#### Automated Quality Gates

**Pre-Merge Requirements** (branch protection rules):
- ✅ All CI checks pass
- ✅ Code review approval (1+ reviewer)
- ✅ AI quality tests pass (if prompts changed)
- ✅ Performance tests pass (p95 <5s)
- ✅ No merge conflicts
- ✅ Branch up-to-date with main

**Post-Merge Monitoring** (10-minute window):
- ✅ Staging deployment successful
- ✅ Health checks pass
- ✅ Error rate <2%
- ✅ p95 latency <7s (staging allows higher)
- ⚠️ Auto-revert on failure

#### Observability Integration

**Metrics Collection**:
- Prometheus metrics endpoint (`/metrics`)
- Grafana dashboard auto-provisioning
- Alert manager configuration

**Log Aggregation**:
- Structured JSON logs to stdout
- Railway/Render native log collection
- Optional: Datadog/LogDNA integration

**Error Tracking**:
- Sentry integration for backend
- Source maps for frontend
- Release tagging for tracking

#### Testing Strategy

**Unit Tests** (fast, no external deps):
- Target: >80% coverage
- Run on every commit
- Mock external services

**Integration Tests** (with test containers):
- User story end-to-end flows
- Redis session persistence
- API contract validation
- Run on PR to main

**Load Tests** (performance validation):
- 100 concurrent sessions (CI)
- 1000 concurrent sessions (pre-production)
- Measure p95, p99 latency
- Memory leak detection

**AI Quality Tests** (prompt regression):
- 50-sample golden dataset
- Intent extraction accuracy
- Guardrail effectiveness
- Hallucination detection

#### Cost Optimization

**CI/CD Cost Targets**:
- GitHub Actions: Free tier (2000 min/month)
- Docker builds: Cache layers aggressively
- Test OpenAI calls: Use mock responses in CI
- Staging environment: Minimal resources

**Estimated Monthly CI/CD Costs**:
- GitHub Actions: $0 (within free tier)
- Railway/Render staging: $5-10
- Container registry: $0 (GitHub packages free)
- **Total**: <$15/month

### Phase 0 Deliverables

**Required Outputs** (must be complete before Phase 1):

1. ✅ All 5 CI workflows created and passing
2. ✅ Multi-stage Dockerfile with optimized builds
3. ✅ Docker-compose for local dev and CI tests
4. ✅ Deployment configuration for staging/production
5. ✅ Branch protection rules enforced
6. ✅ Sentry error tracking integrated
7. ✅ Smoke test suite operational
8. ✅ GitHub Secrets configured
9. ✅ CI/CD documentation complete
10. ✅ PR template with quality checklist

**Validation Criteria**:
- Push empty commit to feature branch → all CI checks pass
- Merge to main → staging deployment succeeds
- Smoke tests pass on staging
- Health endpoints return 200
- Logs visible in aggregation platform
- Metrics endpoint accessible

**Est. Time**: 24-32 hours (3-5 days)

---

## Phase 1: Outline & Research

### Research Questions

Based on Technical Context unknowns, these items require investigation before design:

#### R1: OpenAI Agents SDK Implementation Patterns

**Question**: How to structure agent orchestrator with OpenAI Agents SDK for tool calling and multi-turn conversation?

**Research Tasks**:
1. Review OpenAI Agents SDK documentation for function calling patterns
2. Identify best practices for tool registration and invocation
3. Determine session management strategy (thread IDs vs custom session handling)
4. Understand conversation history management and context window handling

**Deliverable**: `research.md` section on OpenAI Agents SDK architecture with code examples

**Est. Time**: 4 hours

#### R2: Amadeus API Flight Search Integration

**Question**: What are the exact request/response formats for Amadeus Flight Offers Search API? What error handling is required?

**Research Tasks**:
1. Review Amadeus Self-Service API documentation for flight search
2. Test API authentication flow (OAuth2 client credentials)
3. Map Amadeus response structure to FlightOption schema
4. Document rate limits, error codes, and timeout behaviors
5. Identify required vs optional parameters

**Deliverable**: `research.md` section on Amadeus integration with sample requests/responses

**Est. Time**: 3 hours

#### R3: Redis Session Management Best Practices

**Question**: How to efficiently serialize/deserialize Pydantic models in Redis with TTL and atomic updates?

**Research Tasks**:
1. Evaluate serialization approaches (JSON vs Pickle vs MessagePack)
2. Design session update strategy (full replace vs partial updates)
3. Determine Redis key naming convention
4. Plan for session cleanup and TTL enforcement

**Deliverable**: `research.md` section on Redis session architecture

**Est. Time**: 2 hours

#### R4: Flight Result Ranking Algorithm

**Question**: How to implement multi-factor weighted scoring (50% price, 30% duration, 20% direct flights)?

**Research Tasks**:
1. Design normalization strategy for price and duration (z-score vs min-max)
2. Calculate direct flight bonus application
3. Determine if sorting should be client-side or server-side
4. Consider edge cases (all same price, all same duration)

**Deliverable**: `research.md` section with ranking algorithm pseudocode and examples

**Est. Time**: 2 hours

#### R5: WebSocket vs HTTP Polling for Chat Interface

**Question**: Should we use WebSocket for real-time chat or HTTP long-polling?

**Research Tasks**:
1. Compare WebSocket vs HTTP for FastAPI chat interface
2. Evaluate connection overhead and latency implications
3. Consider mobile browser compatibility
4. Assess complexity vs benefit tradeoffs

**Deliverable**: `research.md` section with recommendation and rationale

**Est. Time**: 2 hours

#### R6: Prompt Engineering for Intent Extraction

**Question**: What prompt structure achieves >80% intent extraction accuracy?

**Research Tasks**:
1. Design system prompt for intent extraction with examples
2. Test prompt variations with sample inputs
3. Document few-shot examples to include
4. Determine JSON schema enforcement strategy

**Deliverable**: `research.md` section with initial prompts and test results

**Est. Time**: 4 hours

### Research Consolidation

**Total Research Time**: ~17 hours (2-3 days)

**Output**: `research.md` with:
- Decision: OpenAI Agents SDK thread-based session management
- Decision: Amadeus Flight Offers Search v2 endpoint
- Decision: Redis JSON serialization with Pydantic `.json()` method
- Decision: Server-side ranking with normalized scores
- Decision: WebSocket for real-time chat (better UX, manageable complexity)
- Decision: Few-shot prompts with structured JSON schema enforcement

**Risks Resolved**:
- ✅ OpenAI Agents SDK patterns validated
- ✅ Amadeus API integration approach confirmed
- ✅ Redis session design finalized

---

## Phase 1: Design & Contracts

### Prerequisites

✅ `research.md` complete with all decisions documented

### Deliverables

#### D1: Data Model Design (`data-model.md`)

**Entities** (from spec.md Key Entities):

```markdown
# Data Model: Conversational Flight Search

## Session Entity

**Purpose**: Maintain conversation state within 60-minute TTL

**Fields**:
- `session_id` (str, UUID): Unique session identifier
- `conversation_history` (List[ConversationMessage]): All messages in session
- `extracted_parameters` (TravelIntent | None): Cumulative extracted intent
- `last_search_results` (List[FlightOption]): Most recent search results
- `last_search_lowest_price` (float | None): For "cheaper" refinement calculation
- `created_at` (datetime): Session creation timestamp
- `last_activity` (datetime): Last message timestamp
- `message_count` (int): Total messages in session

**Storage**: Redis with 3600s TTL, JSON serialization

**Validation Rules**:
- `message_count` ≤ 50 (rate limit per session)
- `conversation_history` pruned at 40+ messages (keep last 3 + parameters)
- TTL refreshed on every message

## TravelIntent Entity

**Purpose**: Structured travel parameters extracted from conversation

**Fields**:
- `origin` (str | None): IATA airport code (3 chars)
- `destination` (str | None): IATA airport code (3 chars)
- `departure_date` (date | None): Future date only
- `return_date` (date | None): After departure_date
- `passengers` (int | None): 1-9 range
- `max_price` (int | None): USD amount
- `prefer_direct` (bool): Default false
- `confidence_score` (float): 0.0-1.0

**Validation Rules**:
- Dates must be future (> today)
- `return_date` > `departure_date`
- Airport codes validated against IATA list or Amadeus location API
- Confidence <0.7 triggers clarification

## FlightOption Entity

**Purpose**: Single flight search result with ranking

**Fields**:
- `flight_id` (str): Unique identifier from Amadeus
- `airline` (str): Carrier name
- `price_usd` (float): Total price
- `currency` (str): "USD"
- `duration_minutes` (int): Total travel time
- `stops` (int): 0 for direct
- `outbound_segment` (FlightSegment): Departure leg
- `return_segment` (FlightSegment): Return leg
- `booking_url` (str): Deep link to airline/booking site (see Booking URL Strategy below)
- `relevance_score` (float): Calculated ranking score

**Booking URL Generation Strategy**:

Supported airline deep links (MVP):
- **United Airlines**: `https://www.united.com/en/us/fsr/choose-flights?origin={origin}&destination={dest}&departure={dep_date}&return={ret_date}&passengers={pax}`
- **American Airlines**: `https://www.aa.com/booking/find-flights?origin={origin}&destination={dest}&departureDate={dep_date}&returnDate={ret_date}`

Fallback: Generic search URL with pre-filled origin/destination or airline homepage

Acceptance: Generate valid deep links for ≥2 major carriers; validate with real Amadeus flight results

**Ranking Algorithm** (from clarifications):
```
normalized_price_score = 1 - (price / max_price_in_results)
normalized_duration_score = 1 - (duration / max_duration_in_results)
direct_flight_bonus = 1.0 if stops == 0 else 0.0

relevance_score = (
    0.50 * normalized_price_score +
    0.30 * normalized_duration_score +
    0.20 * direct_flight_bonus
)
```

**State Transitions**:
- Created from Amadeus API response
- Ranked by relevance_score descending
- Top 3-5 returned to user
- Stored in session for refinement context

## FlightSegment Entity

**Purpose**: One leg of round-trip flight

**Fields**:
- `departure_airport` (str): IATA code
- `departure_time` (datetime): ISO 8601
- `arrival_airport` (str): IATA code
- `arrival_time` (datetime): ISO 8601
- `flight_number` (str): e.g., "UA123"
- `aircraft_type` (str | None): e.g., "Boeing 777"

## ConversationMessage Entity

**Purpose**: Single turn in dialogue

**Fields**:
- `role` (Literal["user", "assistant", "system"]): Speaker
- `content` (str): Message text
- `timestamp` (datetime): ISO 8601
- `metadata` (dict): Tool calls, extracted params, confidence scores

**Lifecycle**: Stored in session conversation_history, pruned after 40+ messages
```

**Est. Time**: 3 hours

#### D2: API Contracts (`contracts/`)

**Tool Contracts** (Agent-callable functions):

```yaml
# contracts/search_flights.yaml

name: search_flights
description: Search for round-trip flights matching user criteria. Returns 3-5 options sorted by relevance.
type: function

parameters:
  type: object
  required:
    - origin
    - destination
    - departure_date
    - return_date
  properties:
    origin:
      type: string
      description: "IATA airport code for departure (e.g., 'SFO')"
      pattern: "^[A-Z]{3}$"
    destination:
      type: string
      description: "IATA airport code for arrival (e.g., 'NRT')"
      pattern: "^[A-Z]{3}$"
    departure_date:
      type: string
      format: date
      description: "Departure date (ISO 8601: YYYY-MM-DD)"
    return_date:
      type: string
      format: date
      description: "Return date (ISO 8601: YYYY-MM-DD)"
    passengers:
      type: integer
      minimum: 1
      maximum: 9
      default: 1
      description: "Number of passengers"
    max_price:
      type: integer
      minimum: 0
      description: "Maximum price in USD (optional)"
    prefer_direct:
      type: boolean
      default: false
      description: "Prefer direct flights"

returns:
  type: array
  items:
    $ref: "#/components/schemas/FlightOption"
  minItems: 0
  maxItems: 5

errors:
  - API_001: Amadeus API timeout
  - API_002: Amadeus rate limit exceeded
  - API_003: Invalid airport code
  - VAL_001: Invalid date (past or malformed)
  - VAL_002: Return date before departure date
```

```yaml
# contracts/extract_intent.yaml

name: extract_intent
description: Extract structured travel parameters from user's natural language message.
type: function

parameters:
  type: object
  required:
    - user_message
    - conversation_history
  properties:
    user_message:
      type: string
      maxLength: 2000
      description: "Latest user message"
    conversation_history:
      type: array
      items:
        $ref: "#/components/schemas/ConversationMessage"
      maxItems: 5
      description: "Last 5 messages for context"

returns:
  $ref: "#/components/schemas/TravelIntent"

errors:
  - INTENT_001: Ambiguous intent (confidence <0.4)
  - INTENT_002: Extraction failed (LLM error)
  - LLM_001: OpenAI API timeout
  - LLM_003: Malformed JSON response
```

```yaml
# contracts/generate_clarification.yaml

name: generate_clarification
description: Generate targeted clarifying question when intent is ambiguous.
type: function

parameters:
  type: object
  required:
    - intent
    - missing_parameters
  properties:
    intent:
      $ref: "#/components/schemas/TravelIntent"
    missing_parameters:
      type: array
      items:
        type: string
        enum: [origin, destination, departure_date, return_date, passengers]

returns:
  type: object
  properties:
    question:
      type: string
      description: "User-facing clarification question"
    suggestions:
      type: array
      items:
        type: string
      description: "Optional example responses"

errors:
  - LLM_001: OpenAI API timeout
```

**HTTP/WebSocket Contracts**:

```yaml
# contracts/chat_endpoint.yaml

POST /api/v1/chat/message
description: Send message in existing session or create new session

request:
  content-type: application/json
  body:
    session_id:
      type: string
      description: "Session ID (omit for new session)"
    message:
      type: string
      maxLength: 2000
      required: true

response:
  200:
    session_id: string
    message: string  # Assistant response
    flights: FlightOption[] | null
    metadata:
      intent_confidence: float
      tool_calls: string[]
  400:
    error_code: string
    message: string
  429:
    error_code: "RATE_LIMIT"
    message: "Too many requests"
  503:
    error_code: "SERVICE_UNAVAILABLE"
    message: "External service unavailable"
```

```yaml
# contracts/chat_websocket.yaml

WebSocket /ws/chat
description: Real-time bidirectional chat communication

connection:
  query_params:
    session_id:
      type: string
      required: false
      description: "Resume existing session (omit for new)"

client_message:
  type: object
  properties:
    type:
      type: string
      enum: [message, ping]
    content:
      type: string
      maxLength: 2000
      description: "User message content"

server_message:
  type: object
  properties:
    type:
      type: string
      enum: [message, flights, error, session_init, pong]
    session_id: string
    content: string  # For type=message or type=error
    flights: FlightOption[]  # For type=flights
    metadata:
      intent_confidence: float
      tool_calls: string[]

errors:
  close_code: 1008  # Policy violation (rate limit, invalid message)
  close_code: 1011  # Server error
  close_code: 1001  # Going away (session expired)
```

**Est. Time**: 4 hours

#### D3: Quickstart Guide (`quickstart.md`)

```markdown
# Quickstart: Conversational Flight Search

## Prerequisites

- Python 3.11+
- Node.js 18+
- Redis 7.0+ (or Upstash account)
- OpenAI API key
- Amadeus Self-Service API credentials

## Backend Setup

1. Clone repository and navigate to backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=sk-...
   # AMADEUS_API_KEY=...
   # AMADEUS_API_SECRET=...
   # REDIS_URL=redis://localhost:6379
   ```

3. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

4. Run backend:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Test health endpoint:
   ```bash
   curl http://localhost:8000/health/ready
   ```

## Frontend Setup

1. Navigate to frontend:
   ```bash
   cd frontend
   npm install
   ```

2. Configure API endpoint:
   ```bash
   cp .env.example .env.local
   # Edit .env.local:
   # VITE_API_URL=http://localhost:8000
   ```

3. Start frontend:
   ```bash
   npm run dev
   ```

4. Open browser: http://localhost:5173

## Quick Test

Send a test message via curl:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to fly from SFO to Paris on December 1 for a week"}'
```

Expected response:
```json
{
  "session_id": "sess_abc123",
  "message": "I found 5 flight options for you from San Francisco to Paris...",
  "flights": [...],
  "metadata": {
    "intent_confidence": 0.95,
    "tool_calls": ["search_flights"]
  }
}
```

## Development Mode

Enable mock data for testing without Amadeus API calls:
```bash
# In .env:
ENABLE_MOCK_DATA=true
```

## Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## Next Steps

- Review `docs/api.md` for full API documentation
- Check `docs/error-codes.md` for error handling
- See `prompts/README.md` for prompt engineering guide
```

**Est. Time**: 2 hours

#### D4: Agent Context Update

Run the agent context update script to add this feature's technologies to the appropriate agent config:

```bash
cd /Users/venkatnr/Dev/genai/copilot-ai-projects/int-travel-planner
.specify/scripts/bash/update-agent-context.sh copilot
```

This will update `.copilot-context.md` with:
- OpenAI Agents SDK patterns
- Amadeus API integration details
- Redis session management approach
- FastAPI WebSocket implementation

**Est. Time**: Automated (< 1 minute)

### Re-evaluate Constitution Check Post-Design

**Technical Design Gates**:

✅ **Data Model Alignment**: All entities from spec.md represented in Pydantic schemas  
✅ **Tool Contract Clarity**: Clear single-purpose tools with typed parameters  
✅ **API Design**: RESTful + WebSocket, no form-based endpoints  
✅ **Error Handling**: Comprehensive error codes matching constitution framework  
✅ **Observability**: Metadata tracking designed into contracts  

**POST-DESIGN STATUS: APPROVED**

No constitutional violations introduced during design phase.

---

## Phase 2: Task Breakdown & Milestones

**Note**: Detailed task breakdown will be generated via `/speckit.tasks` command after this plan is approved.

### High-Level Milestones

#### Milestone 1: CI/CD Infrastructure (Week 1)

**Goal**: Automated pipelines operational before any feature code

**Prerequisites**: NONE - must complete first

**Key Tasks**:
- Create all 5 CI workflow files (quality, AI quality, integration, performance, security)
- Set up multi-stage Dockerfile and docker-compose configurations
- Configure deployment pipelines for staging/production
- Establish branch protection rules and quality gates
- Integrate Sentry error tracking
- Create smoke test suite
- Configure GitHub Secrets for all API keys
- Write CI/CD documentation and PR template

**Success Criteria**:
- All CI workflows pass on empty commit
- Staging deployment succeeds
- Health endpoints return 200
- Logs visible in aggregation platform
- Metrics endpoint accessible
- Branch protection rules enforced

**Estimated Effort**: 24-32 hours (3-5 days)

**BLOCKING**: No feature implementation can begin until this milestone is complete

#### Milestone 2: Foundation (Week 1-2)

**Goal**: Backend infrastructure operational with health checks

**Prerequisites**: Milestone 1 (CI/CD) must be complete

**Key Tasks**:
- Set up Python project with FastAPI + OpenAI Agents SDK
- Configure Redis session management
- Implement structured logging and error handling framework
- Create health check endpoints (liveness, readiness)
- Set up development environment with docker-compose

**Success Criteria**:
- Backend starts successfully
- Health checks return 200
- Redis connection verified
- Logs output structured JSON
- All CI checks pass

**Estimated Effort**: 16-20 hours

#### Milestone 3: Intent Extraction (Week 2)

**Goal**: Agent can extract travel intent from natural language with >80% accuracy

**Prerequisites**: Milestones 1 & 2 complete

**Key Tasks**:
- Implement OpenAI Agents SDK orchestrator
- Design and version intent extraction prompts
- Build Pydantic validation for TravelIntent
- Create golden dataset (50 test cases)
- Implement confidence scoring and clarification logic
- Test on golden dataset until >80% accuracy

**Success Criteria**:
- Intent extraction achieves >80% accuracy on golden dataset (SC-003)
- Clarification triggered for confidence <0.7 (FR-016)
- Prompts versioned in git (Principle VII)
- Unit tests pass

**Estimated Effort**: 24-28 hours

#### Milestone 4: Flight Search Tool (Week 2-3)

**Goal**: Search flights via Amadeus API with ranking and mock fallback

**Prerequisites**: Milestones 1 & 2 complete

**Key Tasks**:
- Implement Amadeus API client with OAuth2 authentication
- Build search_flights tool with Pydantic schemas
- Implement multi-factor ranking algorithm (50% price, 30% duration, 20% direct)
- Create static mock flight dataset for fallback
- Implement retry logic with exponential backoff (FR-013)
- Add comprehensive error handling with error codes

**Success Criteria**:
- Flight searches complete within 5 seconds p95 (FR-020, SC-005)
- Returns 3-5 ranked results (FR-004)
- Mock fallback works when Amadeus unavailable (FR-017)
- Error codes match constitution framework

**Estimated Effort**: 20-24 hours

#### Milestone 5: Conversational Refinement (Week 3)

**Goal**: Multi-turn context maintained, search refinement works

**Prerequisites**: Milestones 1 & 2 complete

**Key Tasks**:
- Implement session management in Redis with TTL
- Build context tracking across conversation turns
- Implement search refinement logic ("cheaper" = <80% of lowest price)
- Add context pruning for 40+ message conversations (FR-018)
- Test multi-turn conversation flows (3-5 turns)

**Success Criteria**:
- Context maintained across ≥5 turns (FR-002)
- "Cheaper" refinement filters to <80% lowest price (FR-007)
- Sessions stable for 60 minutes without data loss (SC-009)
- Conversation completes in <6 turns average (SC-002)

**Estimated Effort**: 16-20 hours

#### Milestone 6: Frontend Integration (Week 3-4)

**Goal**: React chat UI functional with WebSocket connection

**Prerequisites**: Milestones 1 & 2 complete

**Key Tasks**:
- Build React chat interface with shadcn/ui components
- Implement WebSocket connection to backend
- Create FlightCard component to display results
- Add message list with user/assistant roles
- Implement input validation and error display

**Success Criteria**:
- User can send messages and see responses in real-time
- Flight results displayed in cards
- Error messages shown user-friendly (no stack traces)
- UI responsive on desktop and mobile

**Estimated Effort**: 16-20 hours

#### Milestone 7: Testing & Validation (Week 4-5)

**Goal**: All P1 user stories validated, success criteria met

**Prerequisites**: Milestones 3-6 complete

**Key Tasks**:
- Run golden dataset regression tests
- Execute end-to-end conversation flows
- Load test with 1000 concurrent sessions (SC-004)
- Measure latency, accuracy, and cost metrics
- Test error scenarios (API failures, rate limits, edge cases)
- Fix bugs and tune prompts based on test results

**Success Criteria**:
- All P1 acceptance scenarios pass
- SC-001 through SC-015 measured and meet thresholds
- Cost per conversation <$0.05 (SC-012)
- No P1 blocking bugs
- All CI checks continue passing

**Estimated Effort**: 20-24 hours

### Total Effort Estimate

**CI/CD Infrastructure** (Phase 0 - MANDATORY): **24-32 hours** (3-5 days)

**P1 Features Only** (MVP Core): **112-136 hours** (3-4 weeks for 1 developer)

**Total MVP Delivery**: **136-168 hours** (4-5 weeks for 1 developer)

**P2 Features** (Production Readiness): +24-32 hours (error handling, itinerary generation)

**P3 Features** (Nice-to-Have): +16-20 hours (session context limits)

**Note**: CI/CD setup is NOT optional and must be completed before any feature development begins.

---

## Risk Mitigation

### High-Risk Items

**Risk 1: OpenAI Agents SDK Learning Curve**

- **Probability**: Medium
- **Impact**: Schedule delay (1-2 days)
- **Mitigation**: Allocate extra research time in Phase 0, prototype early, fallback to raw OpenAI API if SDK proves problematic
- **Trigger**: Cannot implement function calling in 8 hours

**Risk 2: Amadeus API Rate Limits**

- **Probability**: Medium (MVP testing phase)
- **Impact**: Cannot test fully, potential prod issues
- **Mitigation**: Implement mock data early, use sparingly during dev, consider paid tier if needed
- **Trigger**: Approaching 1800 calls/month

**Risk 3: Intent Extraction Accuracy Below 80%**

- **Probability**: Medium
- **Impact**: Fails SC-003, MVP hypothesis invalid
- **Mitigation**: Iterate on prompts, expand golden dataset, consider fine-tuning if time permits
- **Trigger**: Accuracy <75% after 3 prompt iterations

### Medium-Risk Items

**Risk 4: Cost Per Conversation Exceeds $0.05**

- **Probability**: Low
- **Impact**: Budget overrun
- **Mitigation**: Monitor token usage closely, optimize prompts for brevity, reduce conversation history context
- **Trigger**: Cost >$0.04/conversation in testing

**Risk 5: WebSocket Connection Stability**

- **Probability**: Low
- **Impact**: Poor UX, dropped connections
- **Mitigation**: Implement reconnection logic, fallback to HTTP polling if needed
- **Trigger**: >5% connection failures in testing

---

## Success Criteria Validation Plan

| Criterion | Measurement Method | Target | When |
|-----------|-------------------|--------|------|
| SC-001 | End-to-end timer | <60 sec | Milestone 6 |
| SC-002 | Conversation analytics | <6 turns avg | Milestone 6 |
| SC-003 | Golden dataset test | 80%+ accuracy | Milestone 2 |
| SC-004 | Load test (Locust) | 1000 concurrent | Milestone 6 |
| SC-005 | p95 latency metric | 90%+ <5 sec | Milestone 3 |
| SC-006 | User survey | 70%+ positive | Post-MVP |
| SC-007 | Out-of-scope detection test | 95%+ rejection | Milestone 2 |
| SC-008 | Hallucination validation | <5% invalid data | Milestone 2 |
| SC-009 | Redis monitoring | 99%+ stability | Milestone 4 |
| SC-010 | Retry test scenarios | 90%+ recovery | Milestone 3 |
| SC-011 | Abandonment tracking | <40% rate | Milestone 6 |
| SC-012 | Cost tracking dashboard | <$0.05/conv | Continuous |
| SC-013 | Uptime monitoring | 90%+ | 7-day MVP test |
| SC-014 | Clarification frequency | <30% conversations | Milestone 6 |
| SC-015 | Refinement success rate | 50%+ | Milestone 4 |

---

## Next Steps

1. **Review & Approve Plan**: Stakeholder sign-off on scope, timeline, architecture
2. **Execute Phase 0 (CI/CD)**: Set up all pipelines and quality gates (3-5 days) - **BLOCKING REQUIREMENT**
3. **Execute Phase 1 (Research)**: Complete research.md (2-3 days)
4. **Execute Phase 2 (Design)**: Complete design artifacts (1-2 days)
5. **Generate Tasks**: Run `/speckit.tasks` to create detailed task breakdown
6. **Begin Feature Implementation**: Start Milestone 2 (Foundation) only after CI/CD is operational

---

## Appendix

### Glossary

- **IATA Code**: 3-letter airport code (e.g., SFO, NRT, CDG)
- **Intent Extraction**: Converting natural language to structured TravelIntent
- **Tool**: Agent-callable function with typed parameters (e.g., search_flights)
- **Session**: Active conversation with 60-minute TTL stored in Redis
- **Golden Dataset**: Curated test cases for regression testing prompts
- **Confidence Score**: 0-1 float indicating LLM certainty in extraction

### References

- [OpenAI Agents SDK Documentation](https://platform.openai.com/docs/assistants/overview)
- [Amadeus Self-Service API](https://developers.amadeus.com/)
- [Constitution v2.0.0](.specify/memory/constitution.md)
- [Feature Specification](specs/001-conversational-flight-search/spec.md)

### Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-15 | 1.0.0 | Initial implementation plan created |
