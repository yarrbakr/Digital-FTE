# Memory — Digital FTE

> **Source of truth for this project. Read this first, every session.** It holds the current
> phase, what's done / in progress / next, the locked decisions, and the session log.
> Keep it current — future sessions rely on it.

## Current status
- **Phase:** Phase 0 — Foundation
- **Last updated:** 2026-08-31
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
- _nothing yet_

## In progress
- Phase 0 — playbook scaffolded; repo restructure next.

## Next up
- Restructure repo into `backend/` + `frontend/` + `docker/`; stand up the FastAPI skeleton, SQLite schema, and the `LLMProvider` abstraction (Mistral default).

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
