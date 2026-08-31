# Memory — Digital FTE

> **Source of truth for this project. Read this first, every session.** It holds the current
> phase, what's done / in progress / next, the locked decisions, and the session log.
> Keep it current — future sessions rely on it.

## Current status
- **Phase:** Phase 2 ✅ dashboard done → Phase 1 remainder next (real Gmail/Slack + scheduler)
- **Last updated:** 2026-08-31
- **How to run:** backend → `cd backend && uv run uvicorn app.main:app` (:8000); frontend → `cd frontend && npm run dev` (:3000).
- **One-liner:** A provider-agnostic autonomous AI employee that watches Gmail & Slack, drafts actions with the AI provider of your choice, routes them through human approval, and executes them — self-hostable in one command.

## Locked decisions
> Decisions we've committed to, with *why*. Don't relitigate these without a reason.

| # | Decision | Why |
|---|----------|-----|
| D1 | **Open-core model**: one codebase, two distribution doors — self-host first, hosted SaaS later. | Fastest path to a first paying client with **$0 infra spend**; SaaS layers on top later without a rewrite. |
| D2 | **Pluggable AI-provider abstraction**, default **Mistral free API**. | Bring-your-own-provider is a differentiator + avoids lock-in; Mistral's free tier keeps build/demo at $0 while using a *real* API (works self-host and SaaS). |
| D3 | **SQLite** as source of truth (swap to Postgres for SaaS). | Embedded, zero external service, ships inside the download. **Fully replaces Obsidian** as the state store. |
| D4 | **FastAPI backend + in-process scheduler** (no Redis/Celery). | Keeps the existing Python engine; no extra services to run = $0 and one-command simple. |
| D5 | **Next.js + Tailwind dashboard**. | Polished, client-facing UI for demos/selling; the only interface (no Obsidian). |
| D6 | **Channels = Gmail + Slack only** (official APIs). | Dropped WhatsApp/LinkedIn — their Playwright automation violates ToS and risks client account bans/liability. |
| D7 | **Docker Compose one-command install**. | The "download and run with one command" deliverable clients pay for. |
| D8 | **$0 build/demo budget**. | Every paid service (Claude API, cloud hosting, domain) is deferred to the SaaS phase, funded by a paying client. |

## Completed
- **Phase 0 — Foundation.** Repo restructured (`backend/`+`frontend/`+`docker/`, old scripts in `_archive/`). FastAPI + SQLAlchemy + SQLite skeleton with env-driven config. `LLMProvider` abstraction + Mistral impl + registry. Endpoints verified via TestClient; SQLite auto-creates on startup.

- **Phase 2 — Dashboard.** ✅ Next.js 16 + React 19 + Tailwind v4. Overview (stat cards + actions + activity), Inbox (list + detail + approve/reject + simulate modal), Activity, Settings. Typed API client + CORS. Driven in-browser end-to-end with live Mistral (simulate → process → pending → approve).

## Next up
- **Phase 1 remainder:** real `GmailWatcher` (needs Gmail OAuth `credentials.json`) + `SlackWatcher` (needs Slack bot token) writing Items to DB; register real Gmail/Slack executors into the `executor` seam; APScheduler loop; a Connections UI to enter creds.
- **Phase 3:** Docker Compose one-command install + product README.
- Mistral key is set and working in `backend/.env`.

## Open questions / bugs
- Product name: using **"Digital FTE"** (Full-Time Employee) for now — confirm or rename.
- Mistral free-tier rate limits vs. demo needs — validate once wired.

---

## Session log
> After **every** task: *what was attempted · result · errors · outputs/logs · fix applied ·
> next step.* Newest at the bottom.

### 2026-08-31 — Session 1
- **Attempted:** cloned `yarrbakr/Digital-FTE`, set up `origin` + `upstream` remotes; agreed direction (productize the hackathon "AI Employee" into a sellable, one-command self-host product built open-core-ready for SaaS); initialized the playbook.
- **Result:** repo in place on branch `feat/saas-replatform`; playbook scaffolded with 8 locked decisions. Existing Bronze-tier root `CLAUDE.md` replaced with the playbook `CLAUDE.md` (old one described the architecture we're removing).
- **Next:** restructure the repo and stand up the core skeleton (FastAPI + SQLite + `LLMProvider`/Mistral).

### 2026-08-31 — Session 1 (cont.) — Phase 0 build
- **Attempted:** restructure repo + stand up backend foundation (FastAPI + SQLite + provider abstraction).
- **Result:** ✅ done. `backend/app/{config,db,providers,main}` created; `uv sync` OK on Python 3.13; TestClient shows /health, /api/config, /api/providers working; /api/providers/test returns clean 502 with no key (correct); SQLite `digital_fte.db` auto-created on startup. Old scripts archived to `_archive/`; `.gitignore` fixed (blanket `*.json` removed, `*.db` added).
- **Next:** Phase 1 — watchers (Gmail/Slack) → DB, orchestrator + provider analyze, approval state machine, executors, scheduler.

### 2026-08-31 — Session 1 (cont.) — Phase 1 brain
- **Attempted:** build the core pipeline brain (analyzer, orchestrator, approval state machine, executor seam, API).
- **Result:** ✅ verified end-to-end with LIVE Mistral. Ingested urgent invoice email → analyzer set priority=high + drafted a professional reply → approve → execute (simulated) → done. Files: app/services/{analyzer,pipeline,executor,ai}.py, app/schemas.py, app/api/items.py; router wired into main. All $0, no OAuth needed for the demo path.
- **Next:** real Gmail + Slack watchers (need creds), register real executors, APScheduler timer loop.

### 2026-08-31 — Session 1 (cont.) — Phase 2 dashboard
- **Attempted:** build the Next.js dashboard on top of the pipeline API and verify in-browser.
- **Result:** ✅ Scaffolded Next.js 16 (React 19, Tailwind v4). Built design tokens (light/dark), Sidebar, ui primitives, typed api client; Overview/Inbox/Activity/Settings pages; added CORS to backend. Ran both servers and drove the full loop in the browser with LIVE Mistral: simulate incoming gmail → Process new → analyzer set high priority + drafted reply → item moved to Pending → approval screen with Approve/Reject shown. Looks polished and sellable.
- **Errors/fixes:** first backend bg-start double-forked via trailing `&` (orphaned but serving); second bind failed (port in use) — harmless, one instance serves :8000. Browser ref clicks occasionally needed coordinate fallback after re-render.
- **Next:** Phase 1 remainder (real Gmail/Slack + scheduler + connections UI), then Phase 3 (Docker one-command install).
