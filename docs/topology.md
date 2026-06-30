# Topology

LPAM's full experience is a **two-machine** design joined by Tailscale: a VPS
holds the brain + services, a local Mac runs the desktop app, local Ollama (fast
embeddings), and the SSH tunnel.

```
  LOCAL  (Mac / Apple Silicon)                 Tailscale         VPS  (Ubuntu, AMD64)
  ─────────────────────────────                 tailnet          ──────────────────────────────
  • Hermes desktop app (Electron)                                • lpam-backend  (gbrain MCP :3131)
      └ connection.json: mode=remote ──┐                         • gbrain-atlas  (frontend :8080)
  • SSH tunnel 127.0.0.1:9119 ──────────┼── ssh -L 9119 ───────▶ • hermes-dashboard (:9119, desktop API)
  • ollama serve 0.0.0.0:11434 ◀────────┼── embeddings (bge-m3) ─ • hermes-gateway (Telegram, …)
  • LaunchAgents keep both alive        │                         • hermes-control (HCI, optional)
                                        └── atlas UI :8088→:8080  • Qdrant (vector store)
```

## Who talks to whom
- **Desktop app → VPS brain:** `connection.json` (`mode: remote`, `http://127.0.0.1:9119`)
  rides the SSH tunnel to the VPS `hermes-dashboard`. Token must match the VPS unit.
- **VPS embeddings → Mac Ollama:** the VPS `lpam-backend` points `OLLAMA_BASE_URL`
  at the Mac's tailnet IP (Apple Silicon embeds ~200× faster than the CPU VPS).
- **gbrain memory:** the Hermes config's `mcp_servers.gbrain` + the peek/promote
  hooks read/write the brain on the VPS (`:3131/mcp`).

## Degraded modes (honest)
- **VPS only, no Mac:** no desktop app / local voice; embeddings fall back to a
  (slow) VPS Ollama or a cloud embedder.
- **Mac only, no VPS:** the desktop app runs its own local `~/.hermes` backend
  (`desktop-local.sh`), but there's no always-on shared brain.
- **Non-Mac local:** the voice surface (macOS `say`, whisper, Hammerspoon PTT) and
  the AppleScript launchers don't apply; the tunnel + connection.json still work.

The topology is opinionated. Set it up fully for the intended experience.
