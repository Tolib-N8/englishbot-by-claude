# English Learning App

Personal English tutor — local web app powered by Claude (your Pro/Max subscription, no API key).

- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + SQLite + Alembic
- **Frontend:** Next.js 14 (App Router) + Tailwind + shadcn/ui + TanStack Query
- **AI:** Claude via [`claude-agent-sdk`](https://docs.claude.com/en/api/agent-sdk/overview) — uses your local Claude Code login
- **Storage:** `./data/data.db` (SQLite)

## Prerequisites

1. **Claude Code installed and logged in.** Run `claude` once and finish `/login` with your Pro/Max account. The SDK will reuse that session.
2. Python 3.11+ and Node 20+.

## Quick start

```bash
cp .env.example .env          # all defaults are fine

make install                  # creates backend/.venv + frontend/node_modules
make migrate                  # creates data/data.db
make backend-dev              # terminal 1 — FastAPI at :8000
make frontend-dev             # terminal 2 — Next.js at :3000

xdg-open http://localhost:3000
```

## Features (Phase 1 — MVP)

- **Chat tutor** — Claude replies in English at your level, switches to Russian when you're stuck, and corrects your mistakes in a side panel.
- **Vocabulary** — extract useful words/phrases from any chat message, build a personal dictionary.
- **Flashcards (SRS)** — Anki-style review with the SM-2 algorithm. Quality buttons: Again / Hard / Good / Easy.

Future phases will add grammar exercises and pronunciation evaluation.

## Notes on the Claude Agent SDK approach

- The backend invokes the `claude` CLI under the hood, so it must run on the same machine where you logged in. Docker is not used for the backend for this reason.
- Usage counts against your normal Pro/Max limits. If you hit them, the SDK will return an error — try again later.
- No `ANTHROPIC_API_KEY` is needed in `.env`.

## Commands

| Command | What it does |
|---|---|
| `make install` | Install backend + frontend deps |
| `make backend-dev` | uvicorn at :8000 |
| `make frontend-dev` | next dev at :3000 |
| `make migrate` | Run Alembic migrations |
| `make revision msg="..."` | New migration |
| `make test` | Backend pytest suite |
| `make fmt` | Format backend |

## Project layout

```
backend/    FastAPI app, models, services, alembic
frontend/   Next.js 14 app
data/       SQLite DB (bind-mounted volume)
```
