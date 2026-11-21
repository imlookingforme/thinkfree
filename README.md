# ThinkFree

> **"Duolingo for independent thinking"**  
> A thinking-first learning platform that keeps AI from replacing the student's brain.

Originated from BITS Pilani course project (Innovation and Design Thinking, BITS F102, Group 68).

---

## 🌟 Core Concept & Problem
Undergraduate engineering students increasingly use AI tools as cognitive shortcuts, skipping the deep-thinking struggle. ThinkFree restores the learning loop through an enforcement state machine:
1. **ATTEMPT (AI Locked):** AI assistance is physically locked until genuine effort is recorded or a structured "I'm stuck" declaration is provided.
2. **GUIDED (AI Unlocked):** Socratic tutor ladder providing Guide, Help, Hint, and Critical Hint rungs with leak-guard protection. Never reveals full answers.
3. **VALIDATE (AI Locked Again):** Student proves understanding via voice/text solution explanation or solving an isomorphic variant.
4. **DONE:** Mastery graph updated via Bayesian Knowledge Tracing; spaced reviews scheduled via SM-2.

---

## 🏗️ Architecture & Monorepo Layout
```
├── apps/
│   ├── api/             # FastAPI, SQLAlchemy 2 Async, Pydantic v2, Alembic
│   └── web/             # React 18, TypeScript (strict), Vite, Tailwind CSS, Zustand
├── packages/
│   └── shared/          # Generated TypeScript OpenAPI client & domain types
├── infra/
│   └── docker-compose.yml # PostgreSQL 15, Redis 7, Judge0 CE Cluster, API, Web
└── docs/                # Architecture docs, scoring specifications, design references
```

---

## 🚀 Quickstart

### Prerequisites
- Docker & Docker Compose
- Node.js >= 20, `pnpm`
- Python >= 3.11, `uv`

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env with your GEMINI_API_KEY if testing with live LLM
```

### 2. Run with Docker Compose
```bash
docker compose -f infra/docker-compose.yml up -d
```
- Web UI: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Judge0 CE: http://localhost:2358

### 3. Run Locally (Dev Mode)
**Backend:**
```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
pnpm install
pnpm dev:web
```

---

## 🧪 Testing
```bash
# Backend pytest suite (Auth, Sessions, Scoring, State Machine)
cd apps/api
uv run pytest

# Frontend type-check and lint
pnpm typecheck:web
pnpm lint:web
```
