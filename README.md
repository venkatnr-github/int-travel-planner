# AI Travel Planner

A conversational flight search application powered by AI that extracts user intent from natural language, searches flights via the Amadeus API, and provides intelligent recommendations through multi-turn dialogue.

## Overview

AI Travel Planner replaces traditional form-based flight search with a natural language interface. Users describe their travel plans conversationally, and an AI agent extracts structured parameters, searches for flights, and presents personalized recommendations—all without filling out forms.

### Key Features

- **Natural Language Search**: Describe your travel plans in plain English ("I want to fly from SFO to Paris next month for a week")
- **Multi-Turn Conversations**: Refine searches through dialogue ("show me cheaper options", "I prefer direct flights")
- **Intelligent Clarification**: Smart questions when information is ambiguous or missing
- **Ranked Results**: Flights sorted by relevance using weighted scoring (price, duration, direct flight preference)
- **Itinerary Summaries**: Formatted summaries with booking links for selected flights
- **Graceful Error Handling**: Resilient design with retries, fallbacks, and user-friendly error messages

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.11+ / FastAPI | Async API with WebSocket support |
| AI Agent | OpenAI GPT-4 / Agents SDK | Intent extraction and conversation |
| Session Store | Redis | Low-latency session management with TTL |
| Flight Data | Amadeus Self-Service API | Real-time flight search |
| Frontend | React 18+ / shadcn/ui | Modern chat interface |
| Validation | Pydantic | Schema validation and type safety |

## Project Structure

```
int-travel-planner/
├── backend/
│   ├── app/
│   │   ├── agents/           # AI agent orchestration and tools
│   │   ├── api/              # HTTP/WebSocket endpoints
│   │   ├── config/           # Configuration management
│   │   ├── models/           # Pydantic data models
│   │   ├── prompts/          # Versioned prompt templates
│   │   ├── services/         # External API clients
│   │   ├── utils/            # Logging, exceptions, metrics
│   │   └── validators/       # Input validation
│   └── tests/                # Unit, integration, and golden dataset tests
├── frontend/
│   └── src/                  # React chat interface components
├── specs/                    # Feature specifications
│   └── 001-conversational-flight-search/
│       ├── spec.md           # Feature specification
│       ├── plan.md           # Implementation plan
│       └── tasks.md          # Task breakdown
├── docs/                     # API and error documentation
├── .specify/                 # Project governance
│   └── memory/
│       └── constitution.md   # Development principles
└── docker-compose.yml        # Local development setup
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis 7.0+ (or Upstash account)
- OpenAI API key
- Amadeus Self-Service API credentials

### Backend Setup

1. Clone the repository and navigate to the backend:
   ```bash
   git clone https://github.com/venkatnr-github/int-travel-planner.git
   cd int-travel-planner/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=sk-...
   # AMADEUS_API_KEY=...
   # AMADEUS_API_SECRET=...
   # REDIS_URL=redis://localhost:6379
   ```

5. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

6. Run the backend:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. Verify with health check:
   ```bash
   curl http://localhost:8000/health/ready
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```

2. Configure the API endpoint:
   ```bash
   cp .env.example .env.local
   # Edit .env.local:
   # VITE_API_URL=http://localhost:8000
   ```

3. Start the frontend:
   ```bash
   npm run dev
   ```

4. Open your browser at http://localhost:5173

### Docker Setup (Alternative)

Run the entire stack with Docker Compose:

```bash
docker-compose up -d
```

## Usage Examples

### Basic Flight Search

Send a natural language request:

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to fly from SFO to Paris on December 1 for a week"}'
```

### Search Refinement

Continue the conversation to refine results:

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sess_abc123", "message": "show me cheaper options"}'
```

### WebSocket Connection

Connect via WebSocket for real-time chat:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
};

ws.send(JSON.stringify({
  type: 'message',
  content: 'I need a flight to Tokyo next month'
}));
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Development Mode

Enable mock data for testing without API calls:

```bash
# In .env:
ENABLE_MOCK_DATA=true
```

### Code Quality

The project uses automated quality gates:

- **Linting**: ruff, black, isort
- **Type Checking**: mypy
- **Security**: bandit, pip-audit
- **AI Quality**: Golden dataset regression tests

## Architecture

### Core Principles

This project follows a constitution-driven development approach:

1. **Conversational-First**: Natural language interaction over forms
2. **Agent-Orchestrated**: Business logic as composable AI tools
3. **MVP Scope Discipline**: Focused on flight search validation
4. **Session-Based Statelessness**: Redis sessions with TTL
5. **Single Integration Simplicity**: Amadeus API only
6. **Observability**: Comprehensive structured logging
7. **AI-First Engineering**: Prompts as code with versioning

### Flight Ranking Algorithm

Results are sorted using multi-factor weighted scoring:

- **Price (50%)**: Lower prices score higher
- **Duration (30%)**: Shorter flights score higher
- **Direct Flights (20%)**: Non-stop flights get bonus points

## API Documentation

See [docs/api.md](docs/api.md) for full API documentation.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat/message` | POST | Send a chat message |
| `/ws/chat` | WebSocket | Real-time chat connection |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe with dependency checks |

## Error Handling

See [docs/error-codes.md](docs/error-codes.md) for error code reference.

The system provides user-friendly error messages and graceful degradation:

- **API Timeouts**: Automatic retries with exponential backoff
- **Service Unavailable**: Fallback to mock data with disclaimer
- **Session Expiry**: Friendly restart message
- **Invalid Input**: Helpful clarification requests

## Contributing

Contributions are welcome! Please ensure your changes:

1. Align with the constitution principles in `.specify/memory/constitution.md`
2. Include appropriate tests
3. Pass all CI quality gates
4. Follow the existing code style

## License

This project is proprietary. All rights reserved.

## Status

**Current Phase**: MVP Development  
**Feature Branch**: `001-conversational-flight-search`

---

Built with ❤️ using conversational AI
