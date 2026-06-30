# Hermes ⇄ Mac ⇄ VPS — Reproducible Setup Runbook

Built 2026-06-27 … 2026-06-30. This is the full, reproducible documentation of the
Hermes/LPAM voice + memory infrastructure spanning the **DYAI VPS** and **Benjamin's MacBook Air**,
glued by **Tailscale**. Secrets are NEVER inlined here — only their locations/key-names.

---

## 0. Topology

```
                         Tailscale tailnet (DYAI2025@)
  MacBook Air (Apple Silicon)                         VPS srv1308064 (CPU, Ubuntu)
  100.93.33.108                                       100.115.155.7 / 76.13.130.224
  ─────────────────────────                           ──────────────────────────────
  • Hermes Desktop (Electron)  ──connection.json──┐   • lpam-backend (gbrain :3131, PGLite)
  • SSH forced-command broker  <──SSH (Tailscale)─┤   • hermes-dashboard (:9119, desktop API)
  • ollama bge-m3 (LaunchAgent, *:11434)          ├──► • hermes-control HCI (:10272, loopback)
  • Hammerspoon PTT (Cmd+Alt+H)                    │   • hermes agent (/root/.hermes, gateway)
  • Obsidian vault (~/SemanticMind-Vault)         └─  • Atlas / lpam-frontend (:8080 docker)
                                                       • Qdrant (:6333 docker)
```

Two SSH directions, both over Tailscale:
- **VPS → Mac**: Hermes drives the Mac (calendar, voice). Forced-command key, no shell.
- **Mac → VPS**: Desktop app + tunnels reach the VPS brain. Alias `hermes-brain`.

---

## 1. Tailscale (prereq)

Both machines on tailnet `DYAI2025@`. Mac = `100.93.33.108` (`macbook-air-von-benjamin`),
VPS = `100.115.155.7` (`srv1308064-1`). Mac is behind FritzBox NAT → only reachable via Tailscale.
Mac: launch Tailscale.app. VPS: `tailscale` already running.

---

## 2. VPS → Mac SSH bridge (Hermes drives the Mac)

**Mac side** (`~/.hermes-bridge/`):
- `enable-remote-login.sh` (run once, `sudo`): enables sshd via launchctl (FDA-free), restricts
  SSH to user `benjaminpoersch` (`com.apple.access_ssh` group), disables password auth.
- `~/.ssh/authorized_keys`: ONE line — `restrict,from="100.115.155.7",command="/Users/benjaminpoersch/.hermes-bridge/calendar-bridge.sh" ssh-ed25519 <hermes pubkey> hermes-vps-to-mac`
- `calendar-bridge.sh`: forced-command target. Validates `$SSH_ORIGINAL_COMMAND`, denies destructive
  tokens/metachars, enqueues to `queue/`, waits for the broker.
- `calendar-agent.sh` + LaunchAgent `com.hermes.calendar-agent`: the in-GUI-session **broker**.
  Runs osascript→Calendar (works because it has an Aqua session; osascript over SSH alone = -1743),
  and the voice verbs. Restart: `launchctl kickstart -k gui/$(id -u)/com.hermes.calendar-agent`.

**VPS side**: dedicated key `~/.ssh/hermes_mac`; `~/.ssh/config` `Host mac` → `100.93.33.108`,
User `benjaminpoersch`, IdentityFile `~/.ssh/hermes_mac`, ControlMaster auto.

**Verbs** (`ssh mac <verb>`): `version ping calendars list create verify say listen`. No delete/overwrite.

---

## 3. Voice (TTS / STT / push-to-talk)

- **TTS**: `ssh mac say <text>` → macOS `say` via the broker (reliable speaker output).
- **STT**: `ssh mac listen [secs]` → sox `rec` with VAD (`REC_SILENCE`) → whisper.cpp `whisper-cli`
  (model `~/.openhuman/bin/whisper/ggml-base.bin`, lang de, `STT_PROMPT` hotword bias) → text.
  Config in `~/.hermes-bridge/config`. LaunchAgent gets a minimal PATH → the broker exports `/opt/homebrew/bin`.
- **Push-to-talk** (Mac-initiated, the safe way): Hammerspoon `~/.hammerspoon/init.lua` binds
  **Cmd+Alt+H** → `~/.hermes-bridge/ptt-turn.sh`: VAD record → whisper → `ssh hermes-brain 'bash -l -s'`
  + `hermes -z "<text>"` (the REAL Hermes agent, NOT opencode) → `say`. Mic active only for that turn.
  Mic TCC granted to `sox`. Revert/disable: edit init.lua.

---

## 4. Mac → VPS: Hermes Desktop app uses the VPS brain

The Electron desktop app (`~/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app`,
NOT `/Applications/Hermes.app` which is only the Tauri installer) auto-connects to the VPS brain:

- **Auto-connect**: `~/Library/Application Support/Hermes/connection.json` (mode 600):
  `{"mode":"remote","remote":{"url":"http://127.0.0.1:9119","authMode":"token","token":{"encoding":"plain","value":"<dashboard session token>"}},"profiles":{}}`.
  The Electron boot path accepts `encoding:"plain"`. Every normal launch → remote. (Gateway is token-auth:
  `/api/status` `auth_required:false`.)
- **VPS dashboard** = the desktop API. systemd `hermes-dashboard.service`:
  `hermes dashboard --no-open --host 127.0.0.1 --port 9119 --skip-build`, with
  `Environment=HERMES_DASHBOARD_SESSION_TOKEN=<tok>`, `Restart=always`.
- **Tunnel**: Mac LaunchAgent `com.hermes.tunnel9119` (`~/.hermes-bridge/tunnel-9119.sh`) keeps
  `ssh -N -L 127.0.0.1:9119:127.0.0.1:9119 hermes-brain` alive (RunAtLoad+KeepAlive).
- Mac `~/.ssh/config` alias `hermes-brain`/`vps` → root@VPS, ControlMaster.
- Force-reconnect tool: `~/Applications/Hermes Desktop (VPS).app`. Revert to local brain:
  `~/.hermes-bridge/desktop-local.sh`.

---

## 5. gbrain memory (the brain Hermes uses)

LPAM backend = gbrain, systemd `lpam-backend.service`, `bun run src/cli.ts serve --http`, PGLite at
`/root/.gbrain/brain.pglite`, MCP at `http://127.0.0.1:3131/mcp` (OAuth2.1/Bearer).

**Embedder = `ollama:bge-m3` (1024d)** — multilingual, long context, symmetric (no prefix). Config in
systemd drop-in `/etc/systemd/system/lpam-backend.service.d/10-embedder.conf`:
```
Environment=GBRAIN_EMBEDDING_MODEL=ollama:bge-m3
Environment=GBRAIN_EMBEDDING_DIMENSIONS=1024      # ← MUST set; ollama recipe defaults to 768 (nomic) → dim mismatch
Environment=OLLAMA_BASE_URL=http://localhost:11434/v1   # VPS-local for ongoing (reliable); 100.93.33.108 for fast Mac-accelerated bulk
Environment=OLLAMA_API_KEY=ollama
Environment=GBRAIN_AI_EMBED_TIMEOUT_MS=300000
```

**Mac-accelerated bulk embedding** (CPU VPS embeds bge-m3 ~39s/call; Apple Silicon ~0.19s warm):
Mac LaunchAgent `com.hermes.ollama-tailnet` runs `OLLAMA_HOST=0.0.0.0:11434 ollama serve` so the VPS
can embed via the Mac over Tailscale. For a one-time bulk, point `OLLAMA_BASE_URL` at the Mac, ingest,
then switch back to `localhost`. (Disabled the conflicting `homebrew.mxcl.ollama` agent.)

**Wiring into Hermes**: `hermes mcp add gbrain --url http://127.0.0.1:3131/mcp --auth header` with a
minted bearer token (admin flow: `/admin/login` with the bootstrap token from
`journalctl -u lpam-backend` → `/admin/api/api-keys`). Token stored `~/.hermes/.env` as `MCP_GBRAIN_API_KEY`.

**Memory pipeline** (deterministic, `~/.hermes/config.yaml` `hooks:` + `hooks_auto_accept:true`):
- `pre_llm_call` → `~/.hermes/hooks/gbrain_peek.sh` — shallow gbrain `query`, injects `[gbrain]` digest every turn.
- `post_llm_call` → `~/.hermes/hooks/gbrain_promote.sh` — async `extract_facts` (salience gate, self-persists).
- SOUL.md appended: use the digest, deep-dive via query/recall, write durable facts via put_page.

**Content**: 23 project/repo docs + 6 infra/user pages ingested from the Mac's `~/Semantic_Repo_Docus`.
35 project→project graph edges added via `add_link` (link_source `claude-synthesis`). Hermes also
maintains his own page taxonomy (repos/ projects/ systems/ people/ meta/).

---

## 6. Obsidian vault (human + Claude facing graph)

`~/SemanticMind-Vault` — built by a workflow that extracted each project's ontological fingerprint and
synthesized shared concept nodes + links. 23 Projects/ + 37 Concepts/ + _MOC.md, 408 wikilinks.
Rebuild: `…/scratchpad/build_vault.py`. Open: `obsidian://open?path=/Users/benjaminpoersch/SemanticMind-Vault`.

---

## 7. Reproduction order (clean machine)

1. Tailscale up on both; confirm `ssh hermes-brain` and `tailscale ping 100.93.33.108`.
2. VPS: docker compose (qdrant, lpam-frontend); `lpam-backend`, `hermes-dashboard`, `hermes-control` systemd units.
3. VPS: gbrain init `--pglite --embedding-model ollama:bge-m3` with `GBRAIN_EMBEDDING_DIMENSIONS=1024`; pull `bge-m3` in VPS ollama; mint MCP bearer; `hermes mcp add gbrain`.
4. Mac: `enable-remote-login.sh` (sudo); drop the Hermes pubkey forced-command line in authorized_keys; load LaunchAgents `com.hermes.calendar-agent`, `com.hermes.tunnel9119`, `com.hermes.ollama-tailnet`.
5. Mac: write `connection.json`; launch the Electron Hermes app → auto-connects.
6. VPS: register the `hooks:` block + `hooks_auto_accept:true`; copy the 3 hook scripts; append SOUL.md.
7. Ingest content + add_link edges. Build the Obsidian vault.

---

## 8. Gotchas (hard-won)

- osascript over SSH = `-1743` (no Aqua session) → must go through an in-session LaunchAgent broker.
- macOS has no `setsid`/`timeout` → use `nohup … &` / `gtimeout`. LaunchAgents get a minimal PATH → export `/opt/homebrew/bin`.
- `open -a` does NOT inherit env vars → launch the inner macOS binary directly when env is needed.
- `ssh -L 9119:…` binds IPv6-only → use `-L 127.0.0.1:9119:…`.
- gbrain PGLite is single-writer → CLI maintenance contends with the running daemon; stop the daemon for `config set`/`embed`, and DON'T run two operators (Hermes + you) on it at once.
- gbrain `embedding_model` is immutable post-init → re-init to change embedder; re-init wipes `access_tokens` → re-mint the MCP bearer.
- gbrain ollama recipe `default_dims:768` → bge-m3 (1024) needs `GBRAIN_EMBEDDING_DIMENSIONS=1024` or `dim mismatch`.
- `nomic-embed-text` is DEGENERATE via gbrain (no search_query/document prefixes) — different queries return identical results. Use bge-m3.
- `mxbai-embed-large`/`all-minilm` have 512/256 context → dense German chunks overflow. bge-m3 (8192 ctx) is the fit.
- gbrain `put_page` uses the `content` field (not `body`); MCP put_page skips link extraction (`auto_links: skipped: remote`) → build edges with `add_link` or CLI `extract`.
- Obsidian alias links in prose use a PLAIN pipe `[[t|a]]`; the escaped `\|` is only for inside tables.
- pkill self-match: `pkill -f run-ingest.sh` kills its own cmdline → use `pgrep -f '[r]un-ingest.sh'`.

## 9. Secrets / where they live (values NOT here)
- Mac: `~/.hermes/.env` (`MCP_GBRAIN_API_KEY`), `~/.hermes/auth.json` (Hermes provider creds), `~/Library/Application Support/Hermes/connection.json` (dashboard token).
- VPS: `/root/.hermes/.env`, `/root/lpam/backend` brain config, `/etc/systemd/system/lpam-backend.service.d/10-embedder.conf`, gbrain admin bootstrap token in `journalctl -u lpam-backend`.
- SSH keys: VPS `~/.ssh/hermes_mac` (→ Mac), Mac `~/.ssh/id_ed25519` (→ VPS).
