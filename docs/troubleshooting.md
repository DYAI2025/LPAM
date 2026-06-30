# Troubleshooting

Hard-won lessons from running this stack. Most issues are model availability,
stale session state, or the two-machine coupling.

## `HTTP 404: No endpoints found for <model>` (mid-conversation)

A model your config references was **pulled** from OpenRouter (free/stealth models
disappear without notice). The agent retries 3× on the primary and does **not**
fall through `fallback_model` on a 404 — so the fix must remove the dead id, not
rely on failover.

A dead model hides in more than `config.yaml`:
- `config.yaml` → `model.default` and the `fallback_model` list.
- `~/.hermes/state.db` → **per-session pins**: `sessions.model`, `sessions.model_config`
  (JSON), and `sessions.system_prompt` (Hermes injects `Current default model: <id>`).
  Resumed sessions + sub-sessions use the stored pin, bypassing both `config.yaml`
  and the desktop app's picker.

**Fix:** run the watcher (`vps/scripts/model_health_check.py`) — it scrubs all of
the above and restarts the services. Manually:
```bash
# config
sed -i 's#<dead-id>#<new-id>#g' ~/.hermes/config.yaml
# session pins
sqlite3 ~/.hermes/state.db "UPDATE sessions SET model=REPLACE(model,'<dead-id>','<new-id>'),
  model_config=REPLACE(model_config,'<dead-id>','<new-id>'),
  system_prompt=REPLACE(system_prompt,'<dead-id>','<new-id>');"
systemctl restart hermes-dashboard hermes-control hermes-gateway
```

## `HTTP 429: ... temporarily rate-limited upstream`

The model is alive but **throttled** (normal for big free models — 405B/80B/120B
throttle hardest; mid-size like gemma-4-31b / nemotron-3-ultra-550b are more
reliable). This is NOT a config error — retrying or the fallback chain recovers.
Do not "fix" it by swapping models. If it's constant, switch the default to a
smaller free model, or add OpenRouter credits and use a cheap paid model.

`/api/v1/models` membership distinguishes the two: a **pulled** model is absent
from the list; a **throttled** one is present. That's how the watcher avoids
churning on 429s.

## `HTTP 402: Insufficient credits`

Your OpenRouter account has no credits → every *paid* model 402s. Either add
credits (openrouter.ai/settings/credits) or stay on `:free` models (the watcher's
`PRIORITY` list).

## `HTTP 401: User not found` when testing with curl

Your key parse is wrong (stray quote/whitespace). `.env` values may be quoted;
strip quotes AND whitespace before use. Note `/api/v1/models` is a **public**
endpoint — it returns 200 even with a bad key, so it's not a validity test; use a
`/chat/completions` call.

## Gateway service crash-loops: `CHDIR ... Permission denied`

The unit ran as `User=hermes` but its `WorkingDirectory`/home is under `/root`
(mode 700) — the `hermes` user can't traverse it. The shipped
`vps/systemd/hermes-gateway.service` runs as **root** to match its siblings.
Telegram won't work while the gateway is down (it inherits gbrain MCP from config
automatically once running).

## Docker: image built on Mac won't run on the VPS

ARM (Apple Silicon) vs AMD64 mismatch. Build on the VPS, or:
```bash
docker compose build --platform linux/amd64
```
Frozen-lockfile builds also require `bun.lock` to exist (run `install.sh` first).

## Hermes config schema drift

Hermes config is versioned (`_config_version`). After a Hermes update, keys in
`hermes-config/config.yaml.template` may be renamed/removed. Merge by intent and
run `hermes doctor` — it flags problems (e.g. `fallback_model should be a dict …`
if you used a JSON string instead of a YAML list).

## Embeddings slow / timing out

CPU embedding on the VPS is slow. The intended topology runs Ollama (`bge-m3`) on
a Mac over Tailscale (~200× faster) — point `OLLAMA_BASE_URL` in
`10-embedder.conf` at the Mac's tailnet IP, and bump `GBRAIN_AI_EMBED_TIMEOUT_MS`.
