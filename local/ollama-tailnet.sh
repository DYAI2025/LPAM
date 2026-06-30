#!/bin/bash
# Run ollama serve bound to all interfaces so the VPS gbrain can embed via this Mac
# (Apple Silicon ~200x faster than the CPU VPS) over Tailscale.
# Managed by LaunchAgent com.hermes.ollama-tailnet. The GUI Ollama.app binds 127.0.0.1
# only and conflicts on port 11434 — quit it (and remove its login item) so this wins.
# Point the VPS backend's OLLAMA_BASE_URL at this Mac's tailnet IP (see vps 10-embedder.conf).
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_KEEP_ALIVE="30m"
export OLLAMA_NUM_PARALLEL="4"
exec ollama serve
