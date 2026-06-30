# Local live voice + vault MCP (macOS)

Push-to-talk to the VPS Hermes brain (record → local whisper → `hermes -z` →
spoken reply), plus a zero-dep MCP server over an Obsidian vault. macOS-specific
(uses `say`, sox, Hammerspoon, TCC permissions).

## Prerequisites
```bash
brew install sox                       # mic recording (rec) + VAD
# whisper.cpp (STT): build it and fetch a model
git clone https://github.com/ggerganov/whisper.cpp && cd whisper.cpp && make
bash ./models/download-ggml-model.sh base     # → models/ggml-base.bin
# Hammerspoon (hotkey): https://www.hammerspoon.org  (or: brew install --cask hammerspoon)
```
Also assumes the local SSH alias `hermes-brain` from PR5 (`local/ssh-config-snippet`)
and a Hermes install reachable via it.

## Push-to-talk
1. **Config:** `cp local/voice.config.example ~/.hermes-bridge/config`, then set
   `STT_MODEL` to your absolute `ggml-*.bin` path (+ voice/lang to taste).
2. **Script:** `cp local/ptt-turn.sh ~/.hermes-bridge/ && chmod +x ~/.hermes-bridge/ptt-turn.sh`
3. **Hotkey:** append `local/hermes-ptt.lua` to `~/.hammerspoon/init.lua` (it expects
   `~/.hermes-bridge/ptt-turn.sh`), then reload Hammerspoon. Press **Option+Space**
   to speak one turn (VAD auto-stops on silence).
4. **Permissions (TCC):** grant **Microphone** to Hammerspoon (and your terminal if
   you test from there) in System Settings → Privacy & Security. First run may also
   prompt for Automation.

Test without the hotkey: `~/.hermes-bridge/ptt-turn.sh` (speak after the Tink sound).

## Vault MCP
A stdio MCP server over an Obsidian vault (`vault_search` / `vault_read` /
`vault_map` / `vault_links`). Vault path = `$VAULT_DIR` or `~/SemanticMind-Vault`.

Register for a local MCP client (e.g. Claude Code, user scope):
```bash
claude mcp add --scope user vault -- env VAULT_DIR="$HOME/MyVault" \
  python3 "$PWD/local/vault-mcp.py"
```
Or wire it into Hermes by adding an `mcp_servers.vault` block in `~/.hermes/config.yaml`
pointing at the script (stdio). Smoke-test:
```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"vault_search","arguments":{"query":"mcp"}}}' \
  | VAULT_DIR="$HOME/MyVault" python3 local/vault-mcp.py
```

## Calendar broker (advanced add-on — documented, not shipped)
The author's setup also lets the VPS Hermes create/read **macOS Calendar** events.
It is intentionally NOT shipped here because the VPS side is an **SSH forced-command
wrapper** (security-sensitive) and the Mac side is TCC-gated and bespoke. The shape,
if you want to build it:
- **Mac GUI broker** (a per-user LaunchAgent like `com.hermes.calendar-agent`) runs
  inside the logged-in Aqua session — only there does AppleScript get Calendar/TCC
  access (an SSH session gets error `-1743`). It polls a `~/.hermes-bridge/queue` for
  `*.req` files, runs `osascript`, writes `*.res`/`*.rc`. Read/create only — never delete.
- **VPS → Mac** writes those `*.req` files over SSH, ideally behind a
  `command="…"`-restricted authorized_keys entry so the VPS key can only invoke the
  broker, not a general shell.
- First Calendar access triggers a one-time Automation prompt — approve it.

Build it per your own threat model; don't expose an unrestricted key.
