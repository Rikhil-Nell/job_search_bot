# CastLink Job Search Bot

A microservice for CastLink, an acting and entertainment platform, that provides intelligent job search and recommendation capabilities using FastAPI, async PostgreSQL, and LLM-powered conversational agents.

## Features

- **Conversational Job Search**: Users can interact with the bot to find acting and entertainment jobs using natural language
- **Personalized Recommendations**: Supports both explicit search filters and personalized searches based on user profile data
- **FastAPI Microservice**: Exposes a `/chat` endpoint for frontend integration
- **Async PostgreSQL**: Uses `asyncpg` with connection pooling for efficient, non-blocking database access
- **LLM Integration**: Utilizes OpenAI or Groq models via [pydantic-ai](https://github.com/pydantic/pydantic-ai) for natural language understanding and tool-calling
- **Structured JSON Results**: Returns job search results in a strict JSON format for frontend consumption
- **Health Check Endpoint**: `/health` endpoint for service and database status
- **Extensible Tools**: Modular tool functions for job search and recommendations

## Project Structure

```
job_search_bot/
├── src/
│   ├── app.py              # FastAPI app and endpoints
│   ├── agent.py            # LLM agent and orchestration logic
│   ├── db.py               # Database manager and user profile logic
│   ├── tools.py            # Job search tools (SQL queries)
│   ├── settings.py         # Environment/configuration management
│   └── tests/
│       └── agent_test.py   # CLI test for agent logic
├── prompt.md               # System prompt for the agent
├── .env                    # Environment variables (not committed)
├── pyproject.toml          # Python dependencies
├── Dockerfile              # Production-ready Docker build
├── .gitignore
└── README.md
```

## Setup

### 1. Requirements

- Python 3.13+
- PostgreSQL database
- [uv](https://github.com/astral-sh/uv) (for dependency management, optional)
- [Docker](https://www.docker.com/) (optional, for containerization)

### 2. Environment Variables

Copy `.env` and fill in your secrets:

```bash
GROQ_API_KEY=...
OPENAI_API_KEY=...
DB_URL=postgresql://user:password@host:port/dbname
LOGFIRE_WRITE_TOKEN=...
```

### 3. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -r requirements.txt
# or, if using pyproject.toml:
uv pip install

# Using pip
pip install -r requirements.txt
```

### 4. Database

- Ensure your PostgreSQL database is running and accessible
- The schema should include tables: `job_posts`, `user_profile`, `city`, `country`, `job_category`, `job_type`, `currency`, and `user`

### 5. Running the Service

#### Development

```bash
uvicorn src.app:app --reload
```

#### Production (Docker)

```bash
docker build -t job-search-bot .
docker run -p 8000:8000 --env-file .env job-search-bot
```

## Usage

### API Endpoints

#### `POST /chat`

**Request:**
```json
{
  "user_id": "123",
  "message": "Find me acting jobs in Los Angeles"
}
```

**Response:**
- Plain text for general queries
- Strict JSON for job search results (see `prompt.md` for format)

#### `GET /health`

Returns service and database status.

## Testing

A CLI test script is provided:

```bash
python src/tests/agent_test.py
```

This runs the agent logic directly (no API), useful for debugging and development.

## Customization

- **Prompt & Instructions**: See `prompt.md` for system prompt and formatting rules
- **Tools**: Add or modify job search tools in `src/tools.py`
- **Agent Logic**: Customize LLM provider, model, and orchestration in `src/agent.py`

## Development Notes

- Uses FastAPI dependency injection for DB connections (no globals)
- All database access is async and pooled
- Strict separation of concerns: API, agent, DB, tools
- Logging and error handling via `logfire` and standard logging
- Designed as a microservice for integration into a larger CastLink platform

## License

MIT (add your license here)

## Authors

- [Your Name Here]