# GitHub Copilot Code Review Instructions

This document defines custom review focus areas for GitHub Copilot when reviewing pull requests in the Conversational Flight Search project.

## Review Focus Areas

### Agent Patterns

**Requirements:**
- All agent tools MUST return typed Pydantic models (not plain dicts)
- Tool invocations MUST be logged with structured metadata including:
  - `tool_name`: Name of the tool being invoked
  - `session_id`: Active session identifier
  - `input_params`: Tool input parameters
  - `execution_time_ms`: Tool execution duration
- Tool errors MUST be caught and converted to user-friendly messages (no stack traces exposed to users)
- Agent orchestrator MUST validate tool outputs against expected schemas

**Examples:**
```python
# ✅ GOOD: Typed tool with logging
async def search_flights(params: FlightSearchParams) -> List[FlightOption]:
    logger.info("tool_invoked", extra={
        "tool_name": "search_flights",
        "session_id": params.session_id,
        "input_params": params.model_dump()
    })
    try:
        results = await amadeus_client.search(params)
        return [FlightOption(**r) for r in results]
    except Exception as e:
        logger.error("tool_failed", extra={"error": str(e)})
        raise ToolExecutionError("Unable to search flights. Please try again.")

# ❌ BAD: Untyped, no logging, raw exception
def search_flights(params):
    results = amadeus_client.search(params)
    return results  # Raw dict, no validation
```

### LLM Integration

**Requirements:**
- All prompts MUST be versioned with semantic versioning (e.g., `system_agent_v1.0.0.txt`)
- Prompt files MUST be loaded via centralized registry (not hardcoded strings)
- LLM responses MUST be validated against Pydantic schemas before use
- Malformed LLM outputs MUST trigger retry logic (max 2 attempts)
- All LLM calls MUST include timeout configuration (default: 30s)
- Token usage MUST be logged for cost tracking

**Examples:**
```python
# ✅ GOOD: Versioned prompt, validated output, retry logic
from app.prompts.registry import get_prompt

async def extract_intent(message: str) -> TravelIntent:
    prompt = get_prompt("intent_extraction", version="1.0.0")
    
    for attempt in range(2):
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": prompt}, 
                          {"role": "user", "content": message}],
                timeout=30.0
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            intent = TravelIntent(**intent_data)  # Pydantic validation
            
            logger.info("intent_extracted", extra={
                "confidence": intent.confidence_score,
                "tokens_used": response.usage.total_tokens
            })
            return intent
            
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == 1:
                raise IntentExtractionError("Failed to extract valid intent")
            logger.warning(f"Malformed LLM output, retry {attempt + 1}")

# ❌ BAD: Hardcoded prompt, no validation, no retry
async def extract_intent(message: str):
    response = await openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Extract travel intent..."}]
    )
    return json.loads(response.choices[0].message.content)  # No validation
```

### API Clients (External Services)

**Requirements:**
- All external API calls MUST have timeout configuration (default: 10s)
- Transient failures MUST trigger retry with exponential backoff (3 total attempts, base delay 1s)
- API clients MUST implement graceful degradation/mock fallback when service unavailable
- OAuth tokens MUST be cached and refreshed before expiry
- Rate limit errors MUST be logged with `rate_limit_exceeded` event

**Examples:**
```python
# ✅ GOOD: Timeout, retry, fallback
from app.utils.retry import retry_with_backoff
from app.services.mock_data import get_mock_flights

class AmadeusClient:
    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    async def search_flights(self, params: FlightSearchParams) -> List[FlightOption]:
        try:
            response = await self.http_client.get(
                "/v2/shopping/flight-offers",
                params=params.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return [FlightOption(**item) for item in response.json()["data"]]
            
        except httpx.TimeoutException:
            logger.warning("amadeus_timeout", extra={"params": params.model_dump()})
            # Fallback to mock data with disclaimer
            return get_mock_flights(params, disclaimer=True)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("rate_limit_exceeded", extra={"service": "amadeus"})
            raise

# ❌ BAD: No timeout, no retry, no fallback
async def search_flights(params):
    response = await http_client.get("/v2/shopping/flight-offers", params=params)
    return response.json()["data"]
```

### Redis/Session Management

**Requirements:**
- All session operations MUST handle connection failures gracefully
- TTL MUST be set on all session keys (default: 3600s per constitution)
- Session data MUST be serialized via Pydantic `.model_dump_json()` and deserialized with validation
- Redis connection pool MUST be configured with max connections limit
- Expired sessions MUST return clear user message (not internal error)

**Examples:**
```python
# ✅ GOOD: TTL, error handling, Pydantic serialization
async def save_session(session: Session) -> None:
    try:
        serialized = session.model_dump_json()
        await redis_client.setex(
            f"session:{session.session_id}",
            3600,  # TTL from constitution
            serialized
        )
    except redis.ConnectionError:
        logger.error("redis_connection_failed", extra={"session_id": session.session_id})
        raise SessionStorageError("Unable to save session. Please try again.")

async def get_session(session_id: str) -> Optional[Session]:
    try:
        data = await redis_client.get(f"session:{session_id}")
        if data is None:
            return None
        return Session.model_validate_json(data)
    except redis.ConnectionError:
        logger.error("redis_connection_failed")
        return None  # Graceful degradation

# ❌ BAD: No TTL, no error handling, plain dict
async def save_session(session):
    await redis_client.set(f"session:{session['id']}", json.dumps(session))
```

### Security

**Requirements:**
- API keys MUST be loaded from environment variables (never hardcoded)
- Input validation MUST enforce max message length (2000 chars per constitution)
- Rate limiting MUST be enforced per session/IP (10 sessions per IP per hour)
- User inputs MUST be sanitized before logging (PII redaction)
- Prompt injection attempts MUST be detected and rejected

**Examples:**
```python
# ✅ GOOD: Env vars, input validation, rate limiting
from app.config.settings import Settings

settings = Settings()  # Loads from .env

class ChatAPI:
    @app.post("/api/v1/chat/message")
    @rate_limit(max_sessions_per_ip=10, window_seconds=3600)
    async def send_message(
        self,
        request: ChatRequest,
        session_id: Optional[str] = None
    ) -> ChatResponse:
        # Input validation
        if len(request.message) > 2000:
            raise ValidationError("Message exceeds 2000 character limit")
        
        # Prompt injection detection
        if contains_prompt_injection(request.message):
            logger.warning("prompt_injection_detected", extra={
                "message_preview": request.message[:50]  # Redacted
            })
            raise SecurityError("Invalid input detected")
        
        # Use env-based API key
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        ...

# ❌ BAD: Hardcoded key, no validation
@app.post("/api/v1/chat/message")
async def send_message(message: str):
    openai_client = OpenAI(api_key="sk-hardcoded-key-bad")  # NEVER DO THIS
    # No length check, no injection detection
```

### Performance

**Requirements:**
- No blocking I/O in async functions (use `await` for I/O operations)
- Database queries MUST use indexed fields
- Cost per LLM call MUST be documented in code comments or logged
- N+1 query patterns MUST be avoided (use batch operations)
- Conversation history MUST be pruned at 40+ messages to prevent context overflow

**Examples:**
```python
# ✅ GOOD: Async I/O, cost tracking, pruning
async def process_message(session_id: str, message: str) -> str:
    # Cost: ~$0.02 per call (GPT-4 Turbo, ~4K tokens)
    session = await get_session(session_id)  # Async Redis call
    
    # Prune conversation history if exceeds limit
    if len(session.conversation_history) > 40:
        session.conversation_history = [
            session.conversation_history[0],  # System message
            *session.conversation_history[-3:]  # Last 3 exchanges
        ]
    
    response = await openai_client.chat.completions.create(...)
    
    logger.info("llm_call_cost", extra={
        "tokens": response.usage.total_tokens,
        "estimated_cost_usd": response.usage.total_tokens * 0.00001
    })
    
    return response.choices[0].message.content

# ❌ BAD: Blocking I/O, no cost tracking, no pruning
def process_message(session_id: str, message: str) -> str:
    session = redis_client.get(f"session:{session_id}")  # Blocking!
    response = openai_client.chat.completions.create(...)  # Blocks event loop
    return response.choices[0].message.content
```

### Testing & Observability

**Requirements:**
- All agent tools MUST have unit tests with mocked external dependencies
- Golden datasets MUST be updated when prompt versions change
- Integration tests MUST verify end-to-end user story flows
- All errors MUST be logged with structured context (not just exception messages)
- Metrics MUST be exposed for: latency, token usage, tool invocation counts, error rates

**Examples:**
```python
# ✅ GOOD: Structured logging, metrics
async def search_flights_tool(params: FlightSearchParams) -> List[FlightOption]:
    start_time = time.time()
    
    try:
        results = await amadeus_client.search(params)
        
        # Metrics
        metrics.increment("tool.invocations", tags={"tool": "search_flights"})
        metrics.histogram("tool.latency_ms", 
                         (time.time() - start_time) * 1000,
                         tags={"tool": "search_flights"})
        
        # Structured logging
        logger.info("flight_search_completed", extra={
            "session_id": params.session_id,
            "origin": params.origin,
            "destination": params.destination,
            "results_count": len(results),
            "latency_ms": (time.time() - start_time) * 1000
        })
        
        return results
        
    except Exception as e:
        metrics.increment("tool.errors", tags={"tool": "search_flights"})
        logger.error("flight_search_failed", extra={
            "error_type": type(e).__name__,
            "error_message": str(e),
            "session_id": params.session_id
        })
        raise

# ❌ BAD: Plain print, no metrics
async def search_flights_tool(params):
    try:
        results = await amadeus_client.search(params)
        print(f"Found {len(results)} flights")  # No structured logging
        return results
    except Exception as e:
        print(f"Error: {e}")  # No context, no metrics
        raise
```

## Review Checklist

When reviewing code, Copilot should verify:

### Code Quality
- [ ] All functions have type hints
- [ ] Error handling follows conversational error pattern (user-friendly messages)
- [ ] External API calls include timeout configuration
- [ ] Async functions properly await I/O operations
- [ ] Structured logging includes relevant context

### AI Quality
- [ ] Prompts loaded from versioned files (not hardcoded)
- [ ] LLM responses validated against Pydantic schemas
- [ ] Retry logic implemented for malformed outputs
- [ ] Token usage tracked and logged
- [ ] Guardrails implemented for out-of-scope requests

### Security
- [ ] No API keys or secrets in code
- [ ] Input validation enforced (length, format, injection detection)
- [ ] Rate limiting applied where appropriate
- [ ] PII redacted in logs
- [ ] User inputs sanitized

### Performance
- [ ] No blocking I/O in async context
- [ ] Cost implications documented for LLM calls
- [ ] Conversation history pruned to prevent overflow
- [ ] Database queries use indexed fields
- [ ] No N+1 query patterns

### Testing
- [ ] Unit tests provided for new functions
- [ ] Mocks used for external dependencies
- [ ] Integration tests cover user story acceptance criteria
- [ ] Golden datasets updated if prompts changed

## Severity Levels

When flagging issues, use these severity levels:

- **CRITICAL**: Security vulnerability, hardcoded secrets, data loss risk
- **HIGH**: Missing error handling, unvalidated LLM outputs, blocking I/O in async
- **MEDIUM**: Missing logging, no cost tracking, unversioned prompts
- **LOW**: Missing type hints, suboptimal patterns, documentation gaps

## Examples of Common Issues

### Issue: Hardcoded Prompt (HIGH)
```python
# ❌ Found in PR
response = await openai.chat.completions.create(
    messages=[{"role": "system", "content": "You are a travel agent..."}]
)

# ✅ Suggested fix
from app.prompts.registry import get_prompt
prompt = get_prompt("system_agent", version="1.0.0")
response = await openai.chat.completions.create(
    messages=[{"role": "system", "content": prompt}]
)
```

### Issue: Unvalidated LLM Output (CRITICAL)
```python
# ❌ Found in PR
intent = json.loads(llm_response.content)  # No validation
await search_flights(intent["origin"], intent["destination"])

# ✅ Suggested fix
try:
    intent_data = json.loads(llm_response.content)
    intent = TravelIntent(**intent_data)  # Pydantic validation
    await search_flights(intent.origin, intent.destination)
except (json.JSONDecodeError, ValidationError) as e:
    logger.error("Invalid LLM output", extra={"error": str(e)})
    return "I'm having trouble understanding. Could you rephrase?"
```

### Issue: Missing Timeout (HIGH)
```python
# ❌ Found in PR
response = await http_client.get(external_api_url)

# ✅ Suggested fix
response = await http_client.get(external_api_url, timeout=10.0)
```

---

**Last Updated**: 2025-11-16  
**Constitution Version**: v2.0.0  
**Applies to**: Feature 001-conversational-flight-search
