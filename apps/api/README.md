# ThinkFree API

Backend service for ThinkFree, the thinking-first learning platform.

## Architecture
- FastAPI (Async Python 3.11+)
- Pydantic v2 schemas
- SQLAlchemy 2.0 Async ORM
- PostgreSQL 15 & Redis 7
- Multi-provider LLM interface (Gemini, OpenAI, Mock)
- Dedicated local faster-whisper speech transcription
- Sandboxed code execution (Judge0 CE / subprocess sandbox)

## Running
```bash
uv run uvicorn app.main:app --reload
```

## Testing
```bash
uv run pytest
```
