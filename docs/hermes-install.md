# Wiring gbrain into Hermes (long-term memory)

This connects the **Nous Hermes** agent to the gbrain brain (from PR1) so Hermes
gains persistent long-term memory, a configurable model fallback chain, and voice.

> **LPAM does not ship Hermes.** Hermes (the `hermes` CLI/agent and the desktop
> app) is a Nous Research product — install it yourself with your own Nous
> account. See [`../THIRD-PARTY.md`](../THIRD-PARTY.md). These files are an
> *overlay* applied on top of your own Hermes install.

## Prerequisites
- gbrain backend running and reachable (PR1: `docker compose up`, or systemd). Note its MCP URL (default `http://127.0.0.1:3131/mcp`).
- The same `MCP_GBRAIN_API_KEY` you set in the repo-root `.env`.
- Hermes installed (`~/.hermes` exists, you've run `hermes setup` / logged in).
- `jq` and `curl` on PATH (the hooks need them).

## Steps

1. **Env.** Copy the Hermes env template and fill it:
   ```bash
   cp hermes-config/.env.example ~/.hermes/.env   # then edit: OPENROUTER_API_KEY, MCP_GBRAIN_API_KEY, GBRAIN_MCP_URL, voice/telegram keys
   ```
   `MCP_GBRAIN_API_KEY` must equal the value the gbrain backend uses.

2. **Hooks.** Install the memory pipeline:
   ```bash
   mkdir -p ~/.hermes/hooks ~/.hermes/logs
   cp hermes-config/hooks/gbrain_peek.sh hermes-config/hooks/gbrain_promote.sh ~/.hermes/hooks/
   chmod +x ~/.hermes/hooks/*.sh
   ```

3. **SOUL.** Persona + the memory-use instruction:
   ```bash
   cp hermes-config/SOUL.md.template ~/.hermes/SOUL.md   # edit the persona section
   ```

4. **Config overlay.** Merge the blocks from `hermes-config/config.yaml.template`
   into your `~/.hermes/config.yaml` (the file `hermes setup` generated — do NOT
   replace the whole file). Substitute `@@HERMES_HOME@@` with your absolute hermes
   home, e.g.:
   ```bash
   sed "s#@@HERMES_HOME@@#$HOME/.hermes#g" hermes-config/config.yaml.template
   ```
   Copy the resulting `model`, `fallback_model`, `mcp_servers`, `hooks`,
   `memory`, `smart_model_routing`, `tts`, `stt`, `platform_toolsets` blocks in.

5. **Validate + restart.**
   ```bash
   hermes doctor          # expect no fallback_model schema error
   # restart your hermes service(s), e.g.: systemctl restart hermes-dashboard
   ```

## How the memory pipeline works
- **`gbrain_peek.sh`** (`pre_llm_call`): every turn, queries gbrain (breadth, `SCORE_FLOOR=0.15`, top `4`) and injects a `[gbrain]` digest. Fail-open — never blocks a turn.
- **`gbrain_promote.sh`** (`post_llm_call`): returns instantly, then runs `extract_facts` **detached** so the hook timeout can't kill consolidation. `extract_facts` is the notability gate (persists durable facts, skips trivia).
- The `SOUL.md` instruction tells the agent to *dive* (`query`/`recall`) when the digest hints at relevant memory, and to *write* (`put_page`) durable facts.

## Notes
- **Schema drift:** Hermes config schema is versioned. If your installed Hermes renamed/removed keys, merge by intent, not blindly. `hermes doctor` flags problems.
- **Telegram** inherits gbrain MCP automatically (its toolset list has no `no_mcp` sentinel). No extra wiring needed beyond a running gateway.
- Model fallback flakiness (free-model 429s) is handled by the watcher in a later PR.
