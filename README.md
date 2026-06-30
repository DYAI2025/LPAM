# LPAM

A deployment kit for a **personal AI brain**: the gbrain memory/RAG engine + the
gbrain-atlas graph UI, plus the glue to wire it into the **Nous Hermes** agent and
desktop app as long-term persistent memory, with a configurable model fallback
chain and local live voice.

> **Read [`THIRD-PARTY.md`](THIRD-PARTY.md) first.** LPAM ships config + glue, not
> binaries. The Hermes agent/app are Nous Research products you install yourself.

## What you get

| Capability | Status |
|---|---|
| gbrain backend (MCP + PGLite brain) + gbrain-atlas frontend, via Docker | ✅ this kit |
| gbrain as long-term memory for Hermes (MCP + peek/promote hooks) | 🧩 roadmap (PR2) |
| VPS productionization (systemd units, privacy gate) | 🧩 roadmap (PR3) |
| Auto-healing model fallback chain (watcher + cron) | 🧩 roadmap (PR4) |
| Hermes desktop app → your own VPS brain (remote mode over Tailscale tunnel) | 🧩 roadmap (PR5) |
| Local live voice (TTS/STT, push-to-talk) | 🧩 roadmap (PR6) |

The full author runbook for the complete setup lives in [`SETUP.md`](SETUP.md).

## Topology (opinionated)

This is a **two-machine** design joined by Tailscale:

```
  Local (Mac/PC)                         VPS (Ubuntu, AMD64)
  ─────────────────                      ────────────────────
  • Hermes desktop app (remote mode)     • gbrain backend (MCP + brain)
  • Ollama (fast embeddings/TTS)   ⇄     • gbrain-atlas frontend
  • SSH tunnel → VPS dashboard           • Hermes agent + services (systemd)
                    (Tailscale tailnet)  • Qdrant
```

A single-machine or non-Mac setup degrades (no local voice/calendar, slower
embeddings, or no persistent brain). See [`docs/topology.md`](docs/topology.md) (roadmap).

## Prerequisites

| | |
|---|---|
| VPS | Ubuntu (AMD64), root SSH, Docker, bun, Ollama, Qdrant |
| Local | Mac/PC, Tailscale; (Mac for the full voice surface) |
| Accounts/keys | Nous account, `OPENROUTER_API_KEY`, `MCP_GBRAIN_API_KEY`, (optional) `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN` |

## Quickstart (gbrain stack — available now)

```bash
# 1. Clone WITH submodules (populates backend/ = gbrain, frontend/ = gbrain-atlas)
git clone --recurse-submodules https://github.com/DYAI2025/LPAM.git
cd LPAM
# (already cloned without --recurse-submodules? run: git submodule update --init --recursive)

# 2. Configure
cp .env.example .env        # then edit: set MCP_GBRAIN_API_KEY, point OLLAMA/QDRANT hosts

# 3. Populate submodules + install backend deps + init a fresh brain
./install.sh

# 4. Build & run (backend :3000, frontend :8080)
docker compose up --build
```

Verify: the frontend at `http://localhost:8080`, the gbrain MCP endpoint at
`http://localhost:3000/mcp`.

> **ARM vs AMD:** images built on an Apple-Silicon Mac won't run on an AMD64 VPS.
> Build on the VPS, or use `docker compose build --platform linux/amd64`.

## Repo layout (target — built out across PRs)

```
LPAM/
├─ install.sh · docker-compose.yml · .env.example · .gitmodules   # this kit (PR1)
├─ backend/ frontend/        # submodules: gbrain, gbrain-atlas
├─ hermes-config/            # config.yaml.template, hooks/, SOUL.md   (PR2)
├─ vps/                      # systemd units, scripts, privacy gate    (PR3-4)
├─ local/                    # tunnel, ollama, desktop launchers       (PR5-6)
└─ docs/                     # topology, tailscale, hermes-install, voice
```

## License

MIT (the kit). See [`LICENSE`](LICENSE) and [`THIRD-PARTY.md`](THIRD-PARTY.md).
