# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## What this repo is

LPAM is a **deployment kit** for a self-hosted, all-free personal-AI memory + voice
stack (Nous Hermes agent + gbrain long-term memory + local voice). It ships config
templates, systemd units, glue scripts, and docs — **not** application source, and
**not** any third-party binaries (see `THIRD-PARTY.md`). The two app components are
**cloned in place** by `install.sh` (they are gitignored, NOT git submodules — there
is no `.gitmodules`):

- `backend/` ← **`DYAI2025/gbrain` fork** (v0.42.x). Bun MCP server. **Must be the
  fork, not `garrytan/gbrain` upstream** — the fork adds the HTTP MCP server
  (`gbrain serve --http` → OAuth transport). Upstream garrytan is **stdio-only**;
  using it makes the backend exit under systemd and crash-loop. Overridable via `GBRAIN_REPO`.
- `frontend/` ← `DYAI2025/gbrain-atlas` (Vite/React UI, nginx). Overridable via `ATLAS_REPO`.

## Storage engine: PGLite vs Postgres (important)

The shipped `docker-compose.yml` uses gbrain's default **PGLite** (embedded WASM
Postgres, `:3000`). **The reference VPS deployment runs on real Postgres 17** (`:3131`)
because PGLite has hard failure modes at scale:
- Concurrent access → `Aborted()` (single-connection WASM). A stdio-server crash-loop
  triggers this repeatedly.
- Large existing brains fail to open under any Bun/Node runtime (WASM abort).
For a durable deployment prefer Postgres: create a DB + role, `CREATE EXTENSION vector, pg_trgm`,
set gbrain `config.json` `engine: postgres` + `GBRAIN_DATABASE_URL`, `gbrain init --url <URL>`,
`apply-migrations --yes`. Postgres allows concurrent connections → no crash-loop.

## Repo layout

```
install.sh · bootstrap.sh (--vps|--local) · docker-compose.yml · Dockerfile.* · .env.example
LICENSE · THIRD-PARTY.md · README.md · run_all.sh
backend/  frontend/            # CLONED by install.sh (gitignored)
vps/      systemd/ (unit templates, @@TOKENS@@ + gateway User=root) ·
          scripts/ (model_health_check.py, install-cron.sh, privacy-gate.sh,
                    sync-repo-docs.sh, install-repo-hooks.sh) · bootstrap.sh
hermes-config/  config.yaml.template · SOUL.md.template · .env.example · hooks/(gbrain_peek/promote)
local/    tunnel-9119.sh · ollama-tailnet.sh · desktop-*.sh · atlas-launcher.sh ·
          ptt-turn.sh · vault-mcp.py · hermes-ptt.lua · connection.json.template · launchagents/
docker/nginx.conf · docs/(topology,tailscale,hermes-install,voice,troubleshooting,graph-sync)
```

## Commands

```bash
./install.sh                              # clone backend(DYAI fork)+frontend, bun install, init brain
docker compose up --build                 # backend :3000 (compose/PGLite default)
docker compose --profile frontend up      # + gbrain-atlas UI :8080
./bootstrap.sh --vps                       # render+install systemd units (run on VPS as root)
./bootstrap.sh --local                     # macOS glue: tunnel + ollama + connection.json
./vps/scripts/install-repo-hooks.sh <repo> --backfill   # add a repo to the semantic graph
```
No repo-level build/lint/test. Backend tests live in the gbrain checkout (`bun test`).

## All-free stack (no paid keys — this is a hard constraint)

- **LLM:** OpenRouter **free** models only (account has zero credits → paid = 402).
  `fallback_model` is a **YAML list** (a JSON string silently disables it).
  `vps/scripts/model_health_check.py` (daily cron) auto-replaces models pulled from
  OpenRouter (detected via `/models` membership) with a working free one.
- **Embeddings:** local ollama `nomic-embed-text` (**768d**) via `OLLAMA_BASE_URL=…/v1`
  (OpenAI-compat). content_chunks column must match (vector(768)). bge-m3 is 1024 — mismatch.
- **TTS:** Hermes `tts.provider: edge` (Microsoft Edge voices — **free, no key**).
  NOT `openai` (needs a key → "TTS configuration error") and NOT paid elevenlabs.
- **STT:** Groq whisper (free tier).

## Semantic graph auto-sync

Wired repos push their curated docs (README + `docs/`) into gbrain on commit/pull via
`post-commit`+`post-merge` hooks → `sync-repo-docs.sh` → `gbrain import` (content-hash
incremental, local embeddings, free). Add a repo: `install-repo-hooks.sh <repo>`. Scope
is docs-only on purpose (whole-repo md floods the graph). See `docs/graph-sync.md`.

## Sharp edges (hard-won)

- gbrain backend MUST be the DYAI fork (HTTP MCP); garrytan upstream = stdio-only crash-loop.
- PGLite WASM: concurrent-access `Aborted()`; can't open large brains; a brain's Postgres
  data dir is recoverable only by a PG built **without `USE_FLOAT8_BYVAL`** + `pg_resetwal`.
- Hermes `fallback_model` must be a YAML list; TTS must be `edge` (free); embedding dim
  must match the model (768 for nomic) or embed fails.
- `gbrain import` uses git-aware `collectSyncableFiles` (`git ls-files`, honors .gitignore) —
  stage import dirs **outside** any git worktree (e.g. `/tmp`), or it finds 0 files.
- systemd host paths / secrets are tokenized (`@@…@@`); the gateway runs as **root**
  (hermes home under `/root`); never commit `.env`/`*.token`/`connection.json`.
- VPS is AMD64 — Docker images built on Apple Silicon won't run (`--platform linux/amd64`).

## When making changes

Backend behavior → work in the `backend/` gbrain checkout (the DYAI fork), not here.
Keep secrets out of the repo. The full incident + rescue history is in the operator's
memory notes, not the repo.
