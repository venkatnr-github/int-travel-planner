# Feature Specification: Conversational Flight Search

**Feature Branch**: `001-conversational-flight-search`  
**Created**: 2025-11-15  
**Status**: Draft  
**Input**: User description: "Conversational flight search with AI agent that extracts user intent from natural language, searches flights via Amadeus API, and provides intelligent recommendations through multi-turn dialogue"

**Note**: "Intelligent recommendations" refers to the multi-factor ranking algorithm (FR-004: 50% price, 30% duration, 20% direct flight preference) and conversational refinement capabilities (FR-007), not personalization or ML-based prediction.

## Clarifications

### Session 2025-11-15

- Q: FR-004 states "display 3-5 flight options sorted by relevance (price and convenience balance)" but doesn't specify the exact ranking algorithm. → A: Multi-factor weighted scoring: price (50%), duration (30%), direct flights (20%)
- Q: FR-017 and User Story 5 mention "fallback to mock flight data" when Amadeus API is unavailable, but the behavior and data characteristics aren't specified. → A: Static dataset with 3-5 realistic flights for popular routes, clearly labeled as sample data
- Q: User Story 2 describes search refinement ("show me cheaper options"), but the spec doesn't clarify how "cheaper" is quantified when filtering. → A: Filter to flights priced <80% of the lowest price currently shown

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Intent Extraction and Flight Search (Priority: P1)

User describes their travel plans in natural language. The AI agent extracts structured parameters (origin, destination, dates, passengers) from the conversation, searches for flights using the Amadeus API, and presents 3-5 relevant flight options with prices, duration, and airline information.

**Why this priority**: This is the core MVP value proposition - proving that conversational AI can replace traditional flight search forms. Without this working, there is no product. This validates the fundamental hypothesis that users prefer natural language over form-filling.

**Independent Test**: Can be fully tested by having a user say "I want to fly from San Francisco to Tokyo in early December" and receiving valid flight options with prices. Delivers immediate value as a flight search tool without any other features.

**Acceptance Scenarios**:

1. **Given** a new conversation session, **When** user says "I want to fly from SFO to Paris next month for a week", **Then** agent extracts origin (SFO), destination (Paris), approximate dates (next month), duration (7 days), and displays 3-5 flight options with prices
2. **Given** user provides complete travel details, **When** agent searches flights via Amadeus API, **Then** results are displayed within 5 seconds with airline, price, duration, and number of stops
3. **Given** user uses colloquial language like "I need to go to London soon", **When** agent processes the message, **Then** it correctly identifies destination (London) and asks clarifying question about "soon" (specific dates)
4. **Given** agent displays flight results, **When** user views the options, **Then** each result includes: airline name, departure/arrival times, total duration, number of stops, total price in USD, and booking link

---

### User Story 2 - Multi-Turn Context and Search Refinement (Priority: P1)

After initial flight search, user refines their criteria through conversation (e.g., "show me cheaper options", "I prefer direct flights", "what about leaving a day earlier"). Agent maintains context from previous turns and adjusts search parameters accordingly without requiring user to repeat origin/destination.

**Why this priority**: This is critical for MVP because it demonstrates the conversational advantage over traditional search. Without context retention, the experience degrades to a chatbot-wrapped form. This is what makes the system "intelligent" and justifies the AI approach.

**Independent Test**: After completing User Story 1 search, user can say "show me cheaper flights" and receive updated results filtered by lower price, proving conversation context is maintained across at least 3 turns.

**Acceptance Scenarios**:

1. **Given** agent has displayed initial flight results, **When** user says "that's too expensive, show me cheaper options", **Then** agent searches again with max_price filter set to <80% of lowest price shown, maintaining origin, destination, and dates from context
2. **Given** user has been conversing for 3+ turns, **When** user provides refinement criteria like "I prefer direct flights", **Then** agent applies filter without asking user to repeat origin/destination
3. **Given** agent maintains session context, **When** user changes search parameters ("what about leaving on December 10 instead?"), **Then** system updates only the specified parameter and keeps others constant
4. **Given** user asks for refinement, **When** search completes, **Then** agent explains what changed ("Here are direct flights from SFO to Paris on Dec 1-8")

---

### User Story 3 - Intelligent Clarification Questions (Priority: P1)

When user input is ambiguous or missing critical parameters, agent asks targeted clarifying questions (maximum 1-2 per turn) with examples or suggestions to guide the user. Agent avoids interrogating the user with excessive questions.

**Why this priority**: Essential for MVP because real users rarely provide all details upfront. Without clarification logic, the system either fails silently or makes wrong assumptions, destroying trust. This proves the AI can handle ambiguity gracefully.

**Independent Test**: User provides vague input like "I want to travel next month" → agent identifies missing origin and asks "Where will you be flying from?" Delivers value by guiding users to successful searches even with incomplete information.

**Acceptance Scenarios**:

1. **Given** user says "I want to visit Tokyo soon", **When** agent analyzes input, **Then** it identifies missing origin and specific dates, asks "Where will you be flying from?" (not bombarding with multiple questions)
2. **Given** user provides ambiguous dates like "next month", **When** agent needs clarification, **Then** it offers specific options: "Do you mean early December (Dec 1-7) or later in the month?"
3. **Given** user input has low confidence score (<0.7), **When** agent processes it, **Then** it asks for confirmation: "Did you mean round-trip flights from San Francisco to Tokyo departing December 1?"
4. **Given** agent asks clarifying question, **When** user responds, **Then** agent incorporates answer into context and proceeds with search (max 2 clarification rounds before search)

---

### User Story 4 - Itinerary Summary Generation (Priority: P2)

After user selects or shows interest in specific flights, agent generates a formatted itinerary summary including flight details, dates, prices, and a deep link to the airline's booking page. User can copy/paste this summary for reference.

**Why this priority**: Important for UX completeness but not required for core validation. Users can still evaluate flights without a formatted summary. This adds polish and shows the end-to-end journey but doesn't change the fundamental hypothesis being tested.

**Independent Test**: After User Story 1-3 are complete and user says "book the second option", agent generates summary with all details and booking link. Demonstrates value-add of having AI synthesize information into actionable format.

**Acceptance Scenarios**:

1. **Given** user says "I like the second flight option", **When** agent processes selection, **Then** it generates formatted summary with: travel dates, outbound flight details, return flight details, total price, and booking URL
2. **Given** itinerary summary is generated, **When** user views it, **Then** format is clean markdown/text that can be easily copied and pasted
3. **Given** user has not explicitly selected a flight, **When** conversation suggests strong interest (multiple questions about one option), **Then** agent proactively offers to generate summary
4. **Given** summary includes booking link, **When** user clicks it, **Then** they are directed to the airline's website with pre-filled search parameters including carrier, flight number/date, origin/destination, and passenger count when airline APIs support parameterization; fallback to generic search URLs with origin/destination if direct booking links unavailable

---

### User Story 5 - Graceful Error Handling and Fallbacks (Priority: P2)

When external services fail (Amadeus API down, OpenAI rate limits, Redis unavailable), system gracefully degrades with user-friendly messages, fallback to mock data where appropriate, and automatic retries for transient failures.

**Why this priority**: Important for production readiness but not critical for MVP validation. Can be tested manually during development. Core hypothesis can be validated even with occasional errors as long as they're logged properly.

**Independent Test**: Simulate Amadeus API timeout → user sees "I'm having trouble reaching our flight provider, let me try again..." → system retries → if still failing, shows apologetic message. Tests resilience without impacting core value proposition testing.

**Acceptance Scenarios**:

1. **Given** Amadeus API times out during search, **When** error occurs, **Then** agent shows conversational error message: "I'm having trouble reaching our flight provider right now. Let me try again..." and retries up to 3 times
2. **Given** all Amadeus retry attempts fail, **When** agent cannot retrieve real data, **Then** it shows static mock flight data with prominent disclaimer: "I'm showing sample flights while our provider is unavailable. These prices may not be current."
3. **Given** user session expires (60 min TTL), **When** user sends message, **Then** agent recognizes expired session and friendly message: "It looks like our conversation timed out. Let's start fresh! Where would you like to travel?"
4. **Given** OpenAI API returns malformed response, **When** agent detects invalid JSON, **Then** it retries with strengthened schema prompt (max 2 attempts) before showing user error
5. **Given** agent extracts invalid airport code (hallucination), **When** validation check runs, **Then** agent catches error and asks user to clarify: "I couldn't find airport 'XYZ'. Could you provide the city name or valid code like 'SFO'?"

---

### User Story 6 - Session Management and Context Limits (Priority: P3)

System manages conversation session state with 60-minute TTL, handles context window limits gracefully (pruning old messages when approaching token limit), and restarts conversations cleanly when necessary.

**Why this priority**: Nice-to-have for production quality but not essential for MVP validation. Most test conversations will be short (<10 turns). This can be added after validating core hypothesis. Deferrable without impacting user experience for typical use cases.

**Independent Test**: Have a conversation with 50+ messages → system prunes old context while preserving critical parameters → user can still search flights. Tests edge case handling without affecting typical user journeys.

**Acceptance Scenarios**:

1. **Given** conversation reaches 40+ messages or 7000+ tokens, **When** context window threshold exceeded, **Then** agent summarizes older messages and preserves last 3 exchanges + extracted parameters
2. **Given** conversation context is pruned, **When** user continues conversing, **Then** agent still remembers origin, destination, dates from early in conversation
3. **Given** user sends message to expired session (>60 min inactive), **When** session not found in Redis, **Then** agent starts new session with friendly message explaining timeout
4. **Given** conversation has multiple topic switches (flights → hotels → flights), **When** user returns to flight search, **Then** agent recognizes context switch and asks if they want to start fresh search

---

### Edge Cases

- **What happens when user provides past dates?** Agent validates dates and responds: "Travel dates must be in the future. When would you like to depart?"
- **What happens when user requests flights for 10+ passengers?** Agent validates passenger count (max 9) and asks user to contact airline directly for group bookings
- **What happens when no flights found for criteria?** Agent explains no results and suggests alternatives: "I couldn't find flights for those exact dates. Would you like to try dates a day earlier or later?"
- **What happens when user requests "cheaper flights" but refinement (<80% of lowest price) returns no results?** Agent explains constraint too tight and suggests relaxing: "I couldn't find flights cheaper than $X. Would you like to see flights under $Y instead?" (where Y is 90% of current lowest)
- **What happens when user asks non-travel questions?** Agent enforces scope: "I'm a travel assistant focused on flight search. How can I help with your travel plans?"
- **What happens when user tries prompt injection ("ignore previous instructions")?** Agent detects injection pattern and responds: "I'm here to help with flight searches. What destination are you interested in?"
- **What happens when Amadeus API returns zero results?** Agent checks if issue is API error vs no availability, provides appropriate message
- **What happens when user types extremely long messages (>2000 chars)?** System truncates input and processes first 2000 chars, logs truncation event
- **What happens when user provides invalid airport codes?** Agent validates against known IATA codes or Amadeus location API, asks for clarification if invalid
- **What happens during high OpenAI demand (rate limits)?** Agent shows friendly message: "I'm experiencing high demand. Please wait a moment..." and retries with exponential backoff
- **What happens when Redis connection drops?** System falls back to in-memory session (single instance), logs error, session may be lost on restart

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract travel intent from natural language input including origin, destination, departure date, return date, and passenger count
- **FR-002**: System MUST maintain conversation context across at least 5 turns within a single session
- **FR-003**: System MUST search round-trip flights using Amadeus Self-Service API (free tier, 2000 calls/month)
- **FR-004**: System MUST display 3-5 flight options sorted by multi-factor weighted scoring algorithm: price (50% weight), duration (30% weight), direct flights preference (20% weight bonus)
- **FR-005**: System MUST ask clarifying questions when user input is ambiguous or missing critical parameters (max 1-2 questions per turn)
- **FR-006**: System MUST validate extracted parameters against business rules (future dates, valid airport codes, passenger count 1-9)
- **FR-007**: System MUST handle search refinement requests ("cheaper options", "direct flights", "earlier dates") without requiring user to repeat all parameters. For "cheaper" requests, filter to flights priced <80% of the lowest price currently shown
- **FR-008**: System MUST store session state in Redis with 60 minutes (3600 seconds) TTL
- **FR-009**: System MUST generate formatted itinerary summaries with flight details and booking links
- **FR-010**: System MUST enforce scope boundaries and politely decline non-travel requests
- **FR-011**: System MUST detect and prevent prompt injection attempts
- **FR-012**: System MUST validate LLM responses with Pydantic schemas to prevent hallucinations
- **FR-013**: System MUST implement retry logic for transient API failures (max 3 retries with exponential backoff)
- **FR-014**: System MUST provide user-friendly error messages (never expose technical details or stack traces)
- **FR-015**: System MUST log all agent decisions, tool invocations, and API calls with structured JSON format
- **FR-016**: System MUST track confidence scores for intent extraction and trigger clarification when <0.7
- **FR-017**: System MUST fallback to static mock flight dataset (3-5 realistic flights for popular routes) when Amadeus API unavailable, with clear disclaimer message: "I'm showing sample flights while our provider is unavailable. These prices may not be current."
- **FR-018**: System MUST prune conversation history when approaching context window limit (preserve last 3 exchanges + parameters)
- **FR-019**: System MUST rate limit conversations to prevent abuse (50 messages per session, 10 sessions per IP per hour)
- **FR-020**: System MUST complete flight searches within 5 seconds (p95 latency)

### Key Entities

- **Session**: Represents an active conversation with TTL, contains conversation_history (list of messages), extracted_parameters (origin, destination, dates, passengers, preferences), last_search_results, last_search_lowest_price (for refinement calculations), created_at timestamp, last_activity timestamp
- **TravelIntent**: Extracted structured data from user input, includes origin (IATA code), destination (IATA code), departure_date (ISO 8601), return_date (ISO 8601), passengers (integer 1-9), max_price (optional integer), prefer_direct (boolean), confidence_score (float 0-1)
- **FlightOption**: Represents a single flight search result, includes flight_id, airline, price_usd, currency, duration_minutes, stops, outbound_segment (FlightSegment), return_segment (FlightSegment), booking_url
- **FlightSegment**: Represents one leg of a flight, includes departure (airport code, time), arrival (airport code, time), flight_number, aircraft_type
- **ConversationMessage**: Single turn in conversation, includes role (user/assistant/system), content (text), timestamp, metadata (tool calls, extracted params)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a flight search from initial intent to viewing results in under 60 seconds (measured end-to-end)
- **SC-002**: Users can complete the search in fewer than 6 conversational turns on average (from vague intent like "I want to travel" to seeing results)
- **SC-003**: Intent extraction achieves 80%+ accuracy on 50-sample golden dataset (correctly extracts origin, destination, dates when present)
- **SC-004**: System handles at least 1000 concurrent chat sessions without degradation (measured via load testing)
- **SC-005**: 90%+ of flight searches complete successfully within 5 seconds (p95 latency, excluding API failures)
- **SC-006**: Users rate the conversational experience as "better than traditional search" in post-search survey (70%+ positive)
- **SC-007**: System correctly detects and rejects 95%+ of out-of-scope requests without processing them as flight searches
- **SC-008**: Hallucination rate (invalid airport codes, impossible dates, unrealistic prices) is less than 5% across all responses
- **SC-009**: Session stability: 99%+ of sessions maintain context without data loss for duration of session (up to 60 minutes)
- **SC-010**: API failure recovery: 90%+ of transient API failures are recovered via retry logic without user-visible errors
- **SC-011**: User abandonment rate is less than 40% (users who start a conversation but don't complete a search)
- **SC-012**: Cost per conversation stays under $0.05 (OpenAI tokens + infrastructure)
- **SC-013**: System uptime is 90%+ during 7-day MVP validation period (excluding planned maintenance)
- **SC-014**: Clarification questions are asked in less than 30% of conversations (most users provide enough detail initially)
- **SC-015**: Users successfully refine search results (cheaper, faster, direct flights) in 50%+ of multi-turn conversations
