# clawDeploy

Managed “one big button” deployment for **NullClaw (nullclawd)** / OpenClaw.

This repo is evolving from a Fly.io template generator into a **managed VPS deployer**: a script that spins up a new bot instance on *our* server with minimal user input.

## MVP target (what we’re building now)

**Goal:** deploy a fresh **nullclawd** instance on our VPS from a single input:

- `TELEGRAM_BOT_TOKEN` (user provides)

Everything else is fixed or preconfigured on the server:

- LLM provider: **OpenRouter**
- Model: **fixed** (set in `.env` once)
- Networking: behind our reverse proxy (Traefik/Caddy/Nginx)
- Storage: per-bot persistent volume/directory

In other words: user pays → enters Telegram bot token → gets a URL + gateway token.

---

## Repository contents (current)

- `deployer.py` — generator for Fly.io deployment files (legacy / early prototype)
- `templates/` — Fly.io templates for nullclaw/openclaw (legacy / early prototype)

The **VPS managed deploy** path will live alongside (or replace) the Fly generator once stable.

---

## Planned VPS deploy workflow

### 0) Server prerequisites

On the VPS (our infra):

- Docker + Docker Compose
- Reverse proxy (recommended): Traefik or Caddy
- A base domain (optional but recommended): `bots.example.com`
- A place to store persistent data:
  - `/var/lib/clawdeploy/bots/<bot-id>/` (host path) **or** Docker volumes

### 1) Server-wide configuration (`.env`)

Create `.env` on the VPS (or in the deployer working directory):

```env
# --- OpenRouter (server-owned) ---
OPENROUTER_API_KEY=...                 # stored only on server
OPENROUTER_MODEL=anthropic/claude-sonnet-4
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# --- Product / routing ---
BASE_DOMAIN=bots.example.com            # optional
PUBLIC_BASE_URL=https://bots.example.com

# --- Security defaults ---
DEFAULT_RATE_LIMIT_RPS=5
DEFAULT_RATE_LIMIT_BURST=20
DEFAULT_CPU_LIMIT=1
DEFAULT_MEM_LIMIT=512m

# --- Optional: billing/support metadata ---
SUPPORT_EMAIL=support@example.com
```

### 2) Per-bot input

For each new bot we only require:

- `TELEGRAM_BOT_TOKEN`

Optional inputs (later):
- `BOT_NAME` (used for subdomain / container name)
- region/plan

### 3) What gets created per bot

For each bot instance the deployer should:

- generate a unique `bot-id`
- create persistent storage (directory or volume)
- generate a **gateway token** for that bot
- start a container with limits (CPU/RAM)
- attach routing:
  - `https://<bot-id>.bots.example.com/`

### 4) What the user receives

- Bot URL
- Gateway token (or admin token)
- Minimal “next steps” instructions

---

## Billing model (important)

We treat **hosting** and **LLM usage** as **separate** concerns.

- **Hosting fee** covers the bot container, storage, routing, and basic ops.
- **LLM usage** (tokens) is paid **separately**.

### LLM usage: pay-as-you-go / prepay

Default plan assumptions:

- OpenRouter is the default LLM gateway.
- If a user wants to burn **millions of tokens per hour** — that’s fine, but it must be backed by **prepayment / balance**.

Implementation note (how we’ll enforce this):

- Each bot has a `balance` (or `spend_limit`) tracked server-side.
- Once the balance is depleted, LLM calls are paused (bot stays online, but LLM requests are rejected until topped up).

This avoids “one tester accidentally burns the whole shared key”.

---

## Security model (MVP, practical)

We assume hosted instances will be attacked and abused. MVP must include:

- **Rate limits at the reverse proxy** (RPS / burst / conn limit)
- **Container resource limits** (CPU/RAM/pids)
- **Kill switch**: ability to suspend/disable a bot instantly
- **Auto-suspend policy** for obvious anomalies:
  - sustained high CPU/RAM
  - abnormal RPS

### Terms / disclaimer (recommended)

> We reserve the right to suspend or delete any bot at any time if we suspect abuse,
> policy violations, or risk to infrastructure. Data may be removed without recovery.

**LLM billing note:** heavy usage is allowed, but only against a funded balance.
If the balance hits zero, LLM calls pause until topped up.

(We’ll publish a short ToS once billing is connected.)

---

## Roadmap

- [ ] VPS deploy script (nullclawd first)
- [ ] Reverse-proxy routing template
- [ ] Minimal admin CLI: list/suspend/destroy bots
- [ ] Stripe checkout + webhook → deploy job
- [ ] Optional: OpenClaw tier (bigger RAM, always-on)

---

## Contributing

If you want to help:

- keep it boring and reliable
- prefer simple primitives over heavy frameworks
- propose defaults that are safe for hosted multi-tenant operation
