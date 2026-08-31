# Digital FTE — Backend

FastAPI + SQLite backend for Digital FTE. Provider-agnostic AI layer (default: Mistral free tier).

## Run locally

```bash
cd backend
uv sync
cp .env.example .env          # add your Mistral API key
uv run uvicorn app.main:app --reload
```

Then:
- `GET  http://localhost:8000/health`
- `GET  http://localhost:8000/api/config`
- `GET  http://localhost:8000/api/providers`
- `POST http://localhost:8000/api/providers/test`  — body: `{"prompt": "Say hi"}`

Interactive docs at `http://localhost:8000/docs`.

## Layout
- `app/config.py` — env-driven settings
- `app/db/` — SQLAlchemy engine + models (Item / Draft / Connection / Setting / LogEntry)
- `app/providers/` — `LLMProvider` abstraction + Mistral impl + registry
- `app/watchers/`, `app/actions/` — channel ingest + execution (Phase 1)
