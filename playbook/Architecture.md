# Architecture — Digital FTE

> How the system is built, and *why*. Update whenever the stack, data model, or a major
> flow changes.

## Stack (and why)
| Layer | Choice | Why |
|-------|--------|-----|
| Backend / API | **FastAPI** (Python 3.13+, `uv`) | Keeps the existing Python engine; async, typed, one process. |
| State store | **SQLite** (via SQLAlchemy) | Embedded, zero-service, ships in the download. Swappable to Postgres for SaaS through the same ORM. |
| AI layer | **`LLMProvider` abstraction**; default **Mistral** (free API) | Bring-your-own-provider; no lock-in; $0 during build. Swappable to Claude/OpenAI/Ollama. |
| Scheduler / worker | **APScheduler** (in-process) | Polls channels + runs the pipeline without Redis/Celery. Zero extra services. |
| Channels | **Gmail API** + **Slack Bot API** | Official APIs, no ToS/ban risk. Pluggable `Watcher` + `Action` interfaces. |
| Dashboard | **Next.js + Tailwind** | Polished client-facing UI; the only interface (Obsidian removed). |
| Packaging | **Docker Compose** | One-command install for self-host clients. |
| Secrets | Local `.env` + encrypted values in SQLite | No external vault needed at $0. |

## System overview
Digital FTE is a **watch → draft → approve → act** pipeline. Channel **Watchers** (Gmail, Slack)
poll for new items and persist them to SQLite. A **scheduler-driven orchestrator** picks up new
items, calls the configured **LLM provider** to analyze + draft a response/action, and stores the
draft in a `PENDING_APPROVAL` state. The human reviews drafts in the **Next.js dashboard** and
approves or rejects. Approved items are executed by channel **Action** handlers (send Gmail /
post Slack), then marked `DONE` (or `FAILED`). Everything is one FastAPI process + SQLite +
the dashboard — no Obsidian, no external services.

**Open-core split:** the pipeline above is the shared **core**. The **self-host door** runs it
as a single-tenant Docker Compose stack. The **SaaS door** (later) adds a thin layer on top —
multi-tenancy, auth, Stripe billing, Postgres, per-tenant provider metering — without changing
the core.

## Data model
_Core entities (SQLite; finalize schema in Phase 1):_
- **Item** — a unit of work from a channel. `id, channel, external_id, subject, body, sender, received_at, priority, status`. Status: `NEW → DRAFTED → PENDING_APPROVAL → APPROVED → DONE | FAILED | REJECTED`.
- **Draft** — the AI-produced action for an Item. `id, item_id, provider, action_type, content, created_at`.
- **Connection** — a configured channel/provider credential. `id, kind (gmail|slack|provider), config (encrypted), status`.
- **Setting** — key/value app config (active provider, model, polling interval, priority keywords).
- **LogEntry** — pipeline/audit events (replaces the Obsidian `/Logs` files).

_(SaaS adds `Tenant`/`Org` + `User` and a `tenant_id` FK on every row.)_

## Key flows
1. **Ingest:** Scheduler tick → `GmailWatcher.check()` / `SlackWatcher.check()` → new `Item` rows (`status=NEW`).
2. **Draft:** Orchestrator picks `NEW` items → `LLMProvider.analyze(item)` → priority + `Draft` → `status=PENDING_APPROVAL`.
3. **Approve:** Dashboard lists pending drafts → human approves/rejects → `status=APPROVED|REJECTED`.
4. **Act:** Executor picks `APPROVED` → channel `Action.execute(draft)` (send email / post Slack) → `status=DONE|FAILED`.
5. **Observe:** Every step writes a `LogEntry`; dashboard shows status + counts.

## Constraints & boundaries
- **$0 to build and demo** — no paid service in the self-host path; paid pieces (Claude API, cloud hosting, domain) are SaaS-only.
- **Provider-agnostic** — never hard-code one AI vendor in the pipeline.
- **Human-in-the-loop** — nothing is sent/posted without explicit approval.
- **Out of scope (for now):** WhatsApp, LinkedIn, multi-tenancy, billing, Obsidian, mobile app.
