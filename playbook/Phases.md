# Phases — Digital FTE

> The build, broken into phases. Work **one phase at a time** — don't build ahead. Check
> items off as they ship. Confirm the current phase from `Memory.md` before starting.

## Phase 0 — Foundation ✅
- [x] Scaffold the playbook (Memory / Architecture / Phases / CLAUDE.md).
- [x] Restructure repo into `backend/` + `frontend/` + `docker/`; archive the old hackathon scripts (`_archive/`).
- [x] FastAPI skeleton + SQLAlchemy + SQLite; `.env` + config loader. Verified: `/health`, `/api/config`, `/api/providers`, `/api/providers/test`.
- [x] `LLMProvider` abstraction with a **Mistral** implementation (free API) + registry + a `provider` setting.

## Phase 1 — Core engine re-platform
- [x] SQLite schema for Item / Draft / Connection / Setting / LogEntry.
- [x] Orchestrator: pick `NEW` items → analyze via provider → `Draft` + priority → `PENDING_APPROVAL`. **Verified end-to-end with live Mistral.**
- [x] Approval state machine (approve/reject) + pluggable `executor` seam (simulated send for now).
- [x] Pipeline API: ingest / process / list / detail / approve / reject / execute / logs.
- [ ] `Watcher` interface + `GmailWatcher` (writes Items to DB) — needs Gmail OAuth.
- [ ] `SlackWatcher` (Slack Bot API) — needs Slack bot token.
- [ ] Real Gmail/Slack executors registered into the `executor` seam.
- [ ] In-process APScheduler wiring the whole pipeline on a timer.

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
