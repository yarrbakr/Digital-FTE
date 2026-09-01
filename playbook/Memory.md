# Memory — Digital FTE

> **Source of truth for this project. Read this first, every session.** It holds the current
> phase, what's done / in progress / next, the locked decisions, and the session log.
> Keep it current — future sessions rely on it.

## Current status
- **Phase:** Phase 1 ✅ complete (real Gmail + Slack + scheduler wired) → Phase 3 next (Docker one-command install)
- **Last updated:** 2026-09-01
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
- **Phase 3:** Docker Compose one-command install + product README (the sellable download).
- Mistral key is set and working in `backend/.env`.
- **Gmail = IMAP + App Password** (chose over OAuth for the test account: 2-min setup, $0, no Google Cloud project). Trade-off: per-account, not the multi-tenant path — revisit OAuth for hosted SaaS (Phase 4).
- **Connect creds in the dashboard → Settings → Channels** (stored encrypted via Fernet in `.fte_key`).

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

### 2026-09-01 — Session 2 — Phase 1 remainder: real Gmail + Slack + scheduler
- **Attempted:** wire real channels + the automatic scheduler + a credential store & Connections UI. User chose **Gmail = IMAP + App Password** (over OAuth) for the test account.
- **Result:** ✅ Built: `services/crypto.py` (Fernet, key in git-ignored `.fte_key` or derived from `SECRET_KEY`); `services/connections.py` (encrypted connection CRUD + KV cursor store); `watchers/gmail.py` (IMAP unseen fetch, stdlib, Message-ID dedup, marks \Seen) + `watchers/slack.py` (`slack_sdk`, member channels, per-channel ts cursor); `services/watch.py` (poll all connected); `actions/gmail_send.py` (SMTP reply, threaded) + `actions/slack_post.py` (in-thread post) + `actions/__init__.register_all` (into executor seam, simulate if unconnected); `services/scheduler.py` (APScheduler BackgroundScheduler tick = watch → process, NOT auto-execute); `api/connections.py` (list / connect gmail+slack with live validation / delete / `POST /api/watch/run`). Wired routers + `register_executors()` + `scheduler.start/stop` into `main.py` lifespan; `/api/config` now reports scheduler state. Frontend: `lib/api.ts` connection types+methods; Settings page rebuilt with Gmail/Slack connect forms, status pills, disconnect, and "Check for new messages now"; `.fte-input` promoted to `globals.css`. Added `scheduler_enabled` to config; `.fte_key` git-ignored.
- **Verified:** backend imports clean; crypto encrypt/decrypt roundtrips; TestClient shows scheduler_running=true, empty connections, `watch/run`={} with none connected, and **bad Gmail creds → 400 with a live IMAP `AUTHENTICATIONFAILED`** (proves the real IMAP path). Frontend `tsc --noEmit` clean.
- **Not yet done by user:** connect a real test Gmail (needs App Password) + Slack (needs bot token) and drive a live send. Setup steps handed to the user.
- **Next:** user connects the test creds & we verify a live send; then **Phase 3** (Docker one-command install).

### 2026-09-01 — Session 2 (cont.) — live channels verified
- **Attempted:** user set up real creds and connected both channels in the dashboard.
- **Result:** ✅ **LIVE on real accounts.** Slack app "Digital FTE" (bot @dental_bot) installed to the user's own "New Workspace"; first webhook-only token failed with `missing_scope` (had only `incoming-webhook`) → fixed by adding Bot Token Scopes (channels:read/history, chat:write, groups:read/history) + reinstall + new `xoxb-` token. Gmail connected via App Password. Inbox now shows real ingested items (Slack #general "hey there"; real Gmail: flight tracking, YouTube receipts). All came in `Low` + `Done` with no draft — correct: analyzer triaged them `action=none` (no-reply notifications), so no draft/approval needed.
- **Note/UX:** detail pane shows "No draft yet — run Process new" on Done items — misleading; should say "triaged as no action needed." Offered to fix.
- **Next:** drive a reply-worthy message (e.g. Slack "book a cleaning next week") through draft→approve→execute for a real in-thread Slack send; then **Phase 3**. Product read = dental-clinic demo.

### 2026-09-01 — Session 2 (cont.) — graph-first dashboard redesign
- **Attempted:** make the UI more interactive / graph-heavy with little text, using Stitch MCP for the design and 21st.dev MCP for buttons+graphs.
- **Result:** ✅ Backend: added `services/stats.py` + `GET /api/stats` (status/priority/channel splits, 14-day throughput, approval rate). Frontend: installed recharts + cva + clsx + tailwind-merge + lucide-react + @radix-ui/react-slot; `lib/utils.ts` (cn); `components/ui/smooth-button.tsx` (adapted from 21st "Smooth Button", re-themed to our CSS vars, gradient + press-scale); `components/charts.tsx` (themed recharts: ThroughputChart stacked-area, Donut w/ center total, PriorityBars, Gauge radial, MiniBars sparkline); rewrote `Sidebar.tsx` to an icon-only rail (lucide + hover tooltips); rewrote `app/page.tsx` Overview into a control room (KPI tiles + gauge, throughput, status donut, priority bars, channel donut, needs-approval queue). Verified live in browser against real data (92 items, 80 done, 12 pending, gmail 90/slack 2).
- **Errors/fixes:** recharts Pie/RadialBar enter-animation stuck at frame 0 when the browser pane runs hidden (rAF paused) → donut rendered as a thin sliver. Fixed by `isAnimationActive={false}` on all charts (also better for the 5s re-poll). Browser-pane screenshots go stale when hidden — DOM inspection confirmed all charts render.
- **Design:** Stitch project `2875154216124828334`, design system `assets/12647908629833099406` (dark, indigo #6d76ff, Space Grotesk/Geist, rounded-12). **21st.dev free tier = 2 component retrievals/day** — spent on "Advanced Stats" (recharts+chart wrapper) and "Smooth Button". Screenshot saved to scratchpad.
- **Next:** optional — extend minimal-text/graph treatment to Inbox; the "No draft yet → triaged" copy fix; then **Phase 3** (Docker install).

### 2026-09-01 — Session 2 (cont.) — extend redesign to Inbox / Settings / Activity
- **Attempted:** carry the control-room look (compact header, icons, SmoothButton, minimal text) across the rest of the app.
- **Result:** ✅ Rewrote `app/inbox/page.tsx` (compact header with filter pills + live counts, channel-icon list rows w/ priority dots, cleaner detail, SmoothButton approve/reject/execute, icon channel toggle in the simulate modal) — and **fixed the misleading "No draft yet → run Process new" copy**: Done items now read "Triaged — the AI judged this needs no reply." Rewrote `app/settings/page.tsx` (header + "Check now", channel cards w/ Mail/Hash icons + status dots, provider/storage cards, trimmed prose) and `app/logs/page.tsx` (header + event/error count pills). Deleted now-unused `components/PageHeader.tsx`.
- **Verified in-browser:** Inbox (pending item → AI draft + reasoning + green Approve/red Reject; Done item → new triaged copy), Settings (both channels connected, provider/storage), no console errors, tsc clean.
- **Next:** **push** (awaiting user's yes) then **Phase 3** (Docker one-command install).
