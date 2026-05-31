# englishbot — your personal English tutor

A **self-hosted** English-learning app where Claude is your private tutor.
The server runs on **your own computer** using your Claude Pro/Max
subscription — no Anthropic API key, no usage fees, no cloud.

> **Self-hosted means**: you install the server once on your PC. All your
> data — conversations, level assessment, flashcards, vocabulary, pronunciation
> recordings — stays in `./data/` and `./vault/` on your machine. Other devices
> (your phone, laptop, etc.) connect to your server over the local network or
> via Tailscale. There is no central service — if your PC is off, your clients
> show an error.

## What it does

- **Chat tutor** (`/chat`) — Claude replies in English at your level, switches
  to Russian when you're stuck, and lists your grammar mistakes with Russian
  explanations. Replies stream over SSE in real time.
- **IELTS / CEFR level assessment** (`/level`) — Claude analyses your actual
  written English from chats, gives an honest CEFR level + IELTS band with
  per-skill breakdown, and builds a step-by-step roadmap to your target band.
  Set your target (e.g. 6.5) from a dropdown.
- **Grammar exercises** (`/exercises`) — topics suggested from your roadmap;
  Claude generates fill-blank / MCQ / translation tasks at your level. Local
  grading for short answers; lenient Claude grader for translations.
- **Vocabulary + SRS flashcards** (`/vocab`, `/flashcards`) — extract useful
  words from any chat message; review with the SM-2 algorithm
  (Again / Hard / Good / Easy).
- **Pronunciation practice** (`/pronounce`) — read a generated phrase aloud,
  Whisper transcribes locally, words are colour-coded matched / heard-as / missed,
  Claude gives a Russian tip about which sound to practice.
- **Knowledge vault** (`/notes`) — Obsidian-style markdown notes (`topics/`,
  `vocabulary/`, `sessions/`) with `[[wiki-links]]`. Click "Сохранить сессию"
  in chat and Claude writes a session summary linking to topics and words;
  the next chat reuses this so the bot remembers what you've covered. The
  `vault/` folder is a valid Obsidian vault — open it in Obsidian to see the
  graph.

## Architecture

```
                                                    Your PC
                                          (Claude Code is logged in here)
                                                       |
                                  ┌────────────────────┴─────────────────────┐
                                  │  FastAPI backend (:8000)                 │
                                  │    └─ Claude Agent SDK ─→ Claude Pro/Max │
                                  │  Next.js web (:3000)                     │
                                  │  data/data.db  +  vault/                 │
                                  └────────────────────┬─────────────────────┘
                                                       │ HTTP (Tailscale or LAN)
                            ┌──────────────────────────┼──────────────────────────┐
                            │                          │                          │
                       Phone (Flutter)        Laptop (browser/Flutter)        Other devices
```

- **One server, many clients.** All your devices see the same data because
  there's a single database and vault on your PC.
- **Authentication: none yet.** The whole stack assumes you are the only user.
  If you expose port 8000 to the public internet, anyone reaching it has full
  access. Use **Tailscale** (private network) or your home Wi-Fi.

---

## Requirements

### Server (your PC — the one running Claude Code)

| Required | Why |
|---|---|
| **Claude Code installed + logged in** with a Pro or Max subscription | The backend talks to Claude via `claude-agent-sdk`, which reuses the OAuth session in `~/.claude/`. No API key is used. |
| **Python 3.11+** | Backend (FastAPI). |
| **Node 20+** | Frontend (Next.js). |
| **ffmpeg** | Required by faster-whisper for audio decoding (pronunciation). |
| **Linux, macOS, or Windows** | Tested on Arch Linux. Anywhere Claude Code runs. |
| **~2 GB free RAM** | Backend + frontend + Whisper `small.en` model (lazy-loaded on first pronunciation request). |
| **~500 MB disk** | Includes the Whisper model cache. |

### Network (optional but recommended)

| Tool | Why |
|---|---|
| **Tailscale** | Lets your phone reach the backend from anywhere (not just home Wi-Fi). Both the PC and the phone install Tailscale, log into the same account, done. |

### Clients

- **Browser**: open the web UI in any modern browser (Chrome, Firefox, Safari) — works on desktop and mobile. No install needed.
- **Native apps** (optional, nicer UX on phone):
  - **Android** — install the APK from the [GitHub Releases](https://github.com/Tolib-N8/englishbot-by-claude/releases)
  - **iOS** — install the unsigned IPA via [AltStore](https://altstore.io/) (free Apple ID, re-signs every 7 days)
  - **Windows** — extract the ZIP, run `englishbot.exe`
  - **Linux** — `chmod +x EnglishTutor-x86_64.AppImage && ./EnglishTutor-x86_64.AppImage`

> ⚠️ **Pre-built native apps bake in the Tailscale URL of the original author**
> (`100.68.45.17:8000`). To use them with **your own** server, open Settings
> in the app and change the backend URL to your own Tailscale IP. If you want
> to publish your own builds with your IP baked in, see "Releasing your own
> builds" below.

---

## Install the server (step by step)

### 1. Install and log into Claude Code

If you don't have it yet: https://claude.com/claude-code. Then in any terminal:

```bash
claude            # opens an interactive session
# inside the session:
/login            # opens browser → log in with your Pro or Max Apple/Google account
/exit
```

Verify: `claude --help` works without errors.

### 2. Install Python 3.11+, Node 20+, ffmpeg

Pick the line for your OS:

```bash
# Arch / Manjaro
sudo pacman -S python nodejs npm ffmpeg

# Ubuntu / Debian
sudo apt install python3.11 python3.11-venv nodejs npm ffmpeg

# macOS (Homebrew)
brew install python@3.11 node ffmpeg
```

### 3. Clone and install

```bash
git clone https://github.com/Tolib-N8/englishbot-by-claude.git
cd englishbot-by-claude

cp .env.example .env          # defaults are fine — no API key needed
make install                  # backend Python venv + frontend npm install
make migrate                  # creates data/data.db
```

### 4. Run it

```bash
./englishbot start            # starts backend (:8000) + frontend (:3000)
# → open http://localhost:3000 in your browser
```

For convenience, symlink the CLI into your `$PATH`:

```bash
ln -sf "$PWD/englishbot" ~/.local/bin/englishbot
# now `englishbot start | stop | status | logs` from anywhere
```

### 5. (Optional) Set up Tailscale so your phone can reach the server

1. Install Tailscale on your PC and your phone, log in with the same account.
2. On the PC: `tailscale ip -4` → note the IP (looks like `100.x.y.z`).
3. In the native app or web browser on the phone, use `http://100.x.y.z:8000`
   (for the API) and `http://100.x.y.z:3000` (for the web UI).
4. The included Settings screen of the native app lets you change the
   backend URL.

The backend listens on `0.0.0.0:8000` by default so any device on your
network (LAN or Tailscale) can reach it. To restrict to localhost, run
`BACKEND_HOST=127.0.0.1 englishbot start`.

---

## The `englishbot` command

```bash
englishbot start          # boot backend + frontend (idempotent)
englishbot stop           # kill both, free CPU/RAM
englishbot restart        # stop then start
englishbot status         # show PIDs + port reachability
englishbot logs [be|fe]   # tail logs live
englishbot open           # open the UI in your browser
```

PIDs and logs live in `data/.run/`. Each service runs in its own process
group, so `stop` cleanly terminates the whole tree.

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

---

## How the Claude integration works

- The backend invokes the `claude` CLI under the hood, so it must run on the
  same machine where you logged in. (That's why the backend isn't Dockerized.)
- Usage counts against your normal Pro/Max limits — if you hit them, the SDK
  returns an error; try again later.
- Claude is a **pure text generator** in this app. Vault notes and exercise
  grading happen in Python after parsing Claude's structured output —
  the SDK is never granted filesystem access.

## Releasing your own builds

Want your own APK/IPA/EXE/AppImage with your own Tailscale IP baked in?
GitHub Actions handles it.

1. Fork or push the repo to your GitHub.
2. Repo Settings → **Secrets and variables** → **Variables** → create
   `BACKEND_URL` = `http://100.x.y.z:8000` (your Tailscale IP).
3. Tag and push:
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```
4. The workflow in `.github/workflows/release.yml` builds APK (Ubuntu),
   EXE (Windows), AppImage (Linux), and unsigned IPA (macOS), then publishes
   them as a GitHub Release. ~10–15 minutes.

---

## Project layout

```
backend/    FastAPI app — models, services, api/v1, alembic migrations
frontend/   Next.js 14 web UI — all screens listed under Features
mobile/     Flutter client for Android / iOS / Windows / Linux
vault/      Obsidian-style markdown knowledge base (gitignored content)
data/       SQLite DB + audio recordings + runtime PIDs/logs (gitignored)
englishbot  start/stop CLI
.github/workflows/release.yml   CI that builds release artifacts on tag
```

## Honest constraints

- **Single user.** No auth, no user accounts. Designed for one person.
- **Server must stay running.** If your PC is off, clients show "no
  connection". You can sleep/wake; restart with `englishbot start`.
- **Public hosting would need a different architecture.** The Agent-SDK
  approach is tied to your Pro login; publishing to the world would mean
  switching to the paid Anthropic API + multi-user auth + hosting.
- **Whisper runs on CPU.** Pronunciation analysis takes a few seconds per
  clip on a modern machine. The model is downloaded on first use (~250 MB)
  to `~/.cache/huggingface/`.

## License

Personal project. Use freely.
