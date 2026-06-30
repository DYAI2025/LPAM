# Third-party components

LPAM is an **orchestration + deployment kit**. It ships configuration templates,
systemd units, glue scripts, and docs — it does **not** bundle or redistribute
the third-party software it integrates with. You install those yourself.

## Not redistributed — you must install with your own account

- **Nous Hermes agent + Hermes desktop app** (Nous Research).
  The `hermes` CLI (`~/.hermes/hermes-agent`) and the Electron desktop app are
  Nous Research products. LPAM ships config that *targets* Hermes
  (`config.yaml` template, hooks, systemd units) but never the binaries.
  Requires your own Nous account / `auth.json`. See `docs/hermes-install.md`.
  > Hermes config schema is versioned (`_config_version`). If your installed
  > Hermes drifts from the version these templates target, some keys may be
  > renamed/removed. Treat the templates as best-effort and pin a known version.

## Installed by you (open-source / vendor), referenced by this kit

- **Ollama** + the `bge-m3` embedding model (embeddings; optionally local TTS).
- **Qdrant** — vector store (runs on the VPS host).
- **Docker** + **bun** — build/runtime for the gbrain stack.
- **Tailscale** — the network fabric joining your local machine ↔ VPS.
- **whisper.cpp**, **sox/rec**, **Hammerspoon**, macOS `say` / Calendar — the
  optional local voice surface (macOS-specific).

## Shipped as submodules (the author's own repos, MIT)

- `backend/`  → [`DYAI2025/gbrain`](https://github.com/DYAI2025/gbrain) — the brain/MCP engine.
- `frontend/` → [`DYAI2025/gbrain-atlas`](https://github.com/DYAI2025/gbrain-atlas) — the graph UI.

These populate on `git clone --recurse-submodules` (or via `install.sh`) at the
commits this repo pins.

## Accounts / API keys you provide

`OPENROUTER_API_KEY`, `MCP_GBRAIN_API_KEY`, `GROQ_API_KEY`,
`VOICE_TOOLS_OPENAI_KEY`, `TELEGRAM_BOT_TOKEN`, a Nous account, and a VPS.
All go in `.env` files that are gitignored — never commit them.
