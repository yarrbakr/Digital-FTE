# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Employee system (Bronze Tier) that autonomously monitors Gmail, processes emails through Claude Code with agent skills, and organizes results in an Obsidian vault.

**Pipeline:** Gmail → GmailWatcher (polls every 2min) → creates `.md` in `/Needs_Action` → Orchestrator (polls every 60s) → invokes Claude Code with email_processing_skill → moves processed files to `/Done`

## Commands

```bash
# Install dependencies (requires uv and Python 3.14+)
uv sync

# Run the orchestrator (main entry point)
uv run python orchestrator.py

# Run the Gmail watcher standalone
uv run python watchers/gmail_watcher.py

# Verify setup (env vars, vault structure, dependencies)
uv run python test_setup.py
```

## Environment

Copy `.env.example` to `.env` and set:
- `VAULT_PATH` — absolute path to the Obsidian vault (required)
- `GMAIL_CREDENTIALS` — path to Google OAuth credentials.json (default: `./credentials.json`)
- `CHECK_INTERVAL` — polling interval in seconds (default: `120` for watcher, `60` for orchestrator)
- `SKILL_PATH` — optional custom agent skill file path

## Architecture

### Watcher Pattern

`BaseWatcher` (ABC in `watchers/base_watcher.py`) defines the contract: `check_for_updates()` returns new items, `create_action_file()` writes markdown to `/Needs_Action`. `GmailWatcher` implements this for Gmail via OAuth2. New watchers (e.g. Slack, WhatsApp) extend `BaseWatcher`.

### Orchestrator

`orchestrator.py` polls `/Needs_Action` for `.md` files, then shells out to `claude -p --dangerously-skip-permissions` with a prompt referencing `agent_skills/email_processing_skill.md`. It retries up to 3 times with a 5-minute timeout per attempt. The orchestrator runs from the vault directory as cwd.

### Obsidian Vault Folders

- `/Needs_Action` — pending items (EMAIL_*.md files)
- `/Done` — processed/archived items
- `/Logs` — daily log files and Claude output captures
- `/agent_skills` — markdown skill files that instruct Claude how to process items

### Agent Skill

`agent_skills/email_processing_skill.md` contains the full instruction set for Claude: how to parse email frontmatter, assess priority (high/medium/low based on keywords), draft responses for high-priority items, update `Dashboard.md`, and move files to `/Done`.

### Email Priority Keywords

High priority triggers: "urgent", "asap", "immediately", "important", "deadline", "critical", "emergency", "payment", "invoice", "contract", "signature required". Anything else defaults to medium.
