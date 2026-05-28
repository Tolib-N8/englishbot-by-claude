# englishbot — personal English tutor

A local web app where **Claude is your English teacher**. Powered by your
Claude Pro/Max subscription via the Claude Agent SDK — **no API key, no extra cost**.

It corrects your mistakes, builds a personal vocabulary deck with spaced
repetition, and keeps an **Obsidian-style knowledge vault** that both you and
the bot read — so the tutor remembers what you've already covered across sessions.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + SQLite + Alembic
- **Frontend:** Next.js 14 (App Router) + Tailwind + shadcn-style UI + TanStack Query
- **AI:** Claude via [`claude-agent-sdk`](https://docs.claude.com/en/api/agent-sdk/overview) — reuses your local Claude Code login
- **Storage:** `./data/data.db` (SQLite) + `./vault/` (markdown notes)

## Features

- **Chat tutor** — Claude replies in English at your level (A1–A2 by default),
  switches to Russian when you're stuck, and lists your mistakes with
  Russian explanations in a side panel (SSE streaming).
- **Vocabulary** — extract useful words/phrases from any chat message into a
  personal dictionary.
- **Flashcards (SRS)** — Anki-style review using the SM-2 algorithm
  (Again / Hard / Good / Easy).
- **Knowledge vault** — click "Сохранить сессию" after a chat and the tutor
  writes linked markdown notes (`topics/`, `vocabulary/`, `sessions/`) with
  `[[wiki-links]]`. Before the next chat, a vault snapshot is fed back to
  Claude so it builds on what you already know. Open `vault/` in Obsidian to
  browse the graph.

Future phases: grammar exercises and pronunciation evaluation.

## Prerequisites

1. **Claude Code installed and logged in.** Run `claude` once and finish
   `/login` with your Pro/Max account — the SDK reuses that session.
2. Python 3.11+ and Node 20+.

## Quick start

```bash
git clone git@github.com:Tolib-N8/englishbot-by-claude.git
cd englishbot-by-claude

cp .env.example .env          # defaults are fine — no API key needed
make install                  # backend/.venv + frontend/node_modules
make migrate                  # creates data/data.db

# Run everything with one command:
./englishbot start            # boots backend (:8000) + frontend (:3000)
# → open http://localhost:3000
```

## The `englishbot` command

A single controller so the app doesn't waste resources when idle:

```bash
englishbot start          # boot backend + frontend (idempotent, waits for health)
englishbot stop           # kill both, free CPU/RAM
englishbot restart        # stop then start
englishbot status         # show PIDs + port reachability
englishbot logs [be|fe]   # tail logs live
englishbot open           # open the UI in your browser
```

Symlink it into your PATH for global use:

```bash
ln -sf "$PWD/englishbot" ~/.local/bin/englishbot
```

PIDs and logs live in `data/.run/`. Each service runs in its own process
group, so `stop` cleanly terminates the whole tree (including `next-server`).

## How the Claude integration works

- The backend invokes the `claude` CLI under the hood, so it must run on the
  same machine where you logged in. (That's why the backend isn't Dockerized.)
- Usage counts against your normal Pro/Max limits — if you hit them, the SDK
  returns an error; try again later.
- Claude is a **pure text generator** here. Vault notes are written by Python
  after parsing Claude's structured output — the SDK is never granted
  filesystem access.

## Make targets

| Command | What it does |
|---|---|
| `make install` | Install backend + frontend deps |
| `make backend-dev` | uvicorn at :8000 |
| `make frontend-dev` | next dev at :3000 |
| `make migrate` | Run Alembic migrations |
| `make revision msg="..."` | New migration |
| `make test` | Backend pytest suite |
| `make fmt` | Format backend (ruff) |

## Project layout

```
backend/    FastAPI app — models, services, api/v1, alembic
frontend/   Next.js 14 app — chat, flashcards, vocab, notes pages
vault/      Obsidian-style markdown knowledge base (topics/vocab/sessions)
data/       SQLite DB + runtime PIDs/logs
englishbot  start/stop CLI
```

## License

Personal project. Use freely.
