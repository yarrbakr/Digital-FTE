# Phases — Digital FTE

> The build, broken into phases. Work **one phase at a time** — don't build ahead. Check
> items off as they ship. Confirm the current phase from `Memory.md` before starting.

## Phase 0 — Foundation
- [x] Scaffold the playbook (Memory / Architecture / Phases / CLAUDE.md).
- [ ] Restructure repo into `backend/` + `frontend/` + `docker/`; archive the old hackathon scripts.
- [ ] FastAPI skeleton + SQLAlchemy + SQLite; `.env` + config loader.
- [ ] `LLMProvider` abstraction with a **Mistral** implementation (free API) + a `provider` setting.

## Phase 1 — Core engine re-platform
- [ ] SQLite schema for Item / Draft / Connection / Setting / LogEntry.
- [ ] `Watcher` interface + `GmailWatcher` (writes Items to DB, not Obsidian).
- [ ] `SlackWatcher` (Slack Bot API).
- [ ] Orchestrator: pick `NEW` items → `LLMProvider.analyze` → `Draft` + priority → `PENDING_APPROVAL`.
- [ ] Approval state machine + `Action` executors (Gmail send / Slack post).
- [ ] In-process APScheduler wiring the whole pipeline.

## Phase 2 — Web dashboard (Next.js)
- [ ] Dashboard shell + API client to FastAPI.
- [ ] Inbox / drafts list; approve / reject actions.
- [ ] Connections screen: connect Gmail, connect Slack, set AI provider + key/model.
- [ ] Settings (polling interval, priority keywords) + status/overview page.

## Phase 3 — One-command install (sellable self-host v1)
- [ ] Dockerfile(s) + `docker-compose.yml` (backend + frontend + volume for SQLite).
- [ ] One-command install script + `.env` bootstrap + first-run onboarding.
- [ ] Rewrite README as product/install docs; demo script for showcasing to clients.

---
_Backlog / later:_
- **Phase 4 — SaaS door:** multi-tenancy (`tenant_id`), auth, Stripe billing, Postgres, hosted deploy, per-tenant provider metering, Google OAuth verification.
- More providers (Claude, OpenAI, Ollama), more channels, analytics, audit export.
