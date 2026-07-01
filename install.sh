#!/bin/bash
# LPAM installer — clone the gbrain backend + gbrain-atlas frontend in place,
# install deps, init a fresh PGLite brain, and ensure the host dirs exist.
# LPAM is a harness: backend/ and frontend/ are CLONED here (not vendored, not
# submodules) and are gitignored. Idempotent for the brain; re-clones the code.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# NOTE: use the DYAI2025/gbrain FORK, not garrytan/gbrain upstream. The fork adds
# the HTTP MCP server (`gbrain serve --http` → OAuth transport on :3131) that LPAM's
# whole stack (Hermes desktop remote mode, the dashboard) depends on. Upstream
# garrytan/gbrain is stdio-only (no HTTP) — using it makes lpam-backend crash-loop.
GBRAIN_REPO="${GBRAIN_REPO:-https://github.com/DYAI2025/gbrain.git}"
ATLAS_REPO="${ATLAS_REPO:-https://github.com/DYAI2025/gbrain-atlas.git}"
PLUMBLINE_REPO="${PLUMBLINE_REPO:-https://github.com/DYAI2025/Plumbline.git}"
PLUMBLINE_DIR="${PLUMBLINE_DIR:-/root/Plumbline}"
VAULT_DIR="${VAULT_DIR:-/root/obsidian-vault}"

cd "$ROOT_DIR"

echo "Setting up LPAM (GBrain + gbrain-atlas + Plumbline + Obsidian vault harness)..."
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v bun >/dev/null || { echo "bun is required. Install from https://bun.sh first." >&2; exit 1; }

# Backend: clone the GBrain core engine (DYAI2025/gbrain fork — HTTP MCP capable).
echo "Setting up GBrain backend from $GBRAIN_REPO..."
rm -rf backend
git clone "$GBRAIN_REPO" backend
( cd backend && bun install )

# gbrain CLI ships with the backend package; fall back to bunx if not on PATH.
GBRAIN_BIN="gbrain"
command -v gbrain >/dev/null 2>&1 || GBRAIN_BIN="bunx gbrain"
if [ ! -e backend/brain ]; then
  echo "Initializing GBrain brain (PGLite) in ./backend/brain..."
  ( cd backend && $GBRAIN_BIN init --pglite --path ./brain )
else
  echo "Brain already exists at backend/brain — skipping init."
fi

# Frontend: clone gbrain-atlas (Vite + React) and produce its lockfile.
echo "Setting up gbrain-atlas frontend from $ATLAS_REPO..."
rm -rf frontend
git clone "$ATLAS_REPO" frontend
( cd frontend && bun install )

# Plumbline is referenced by docker-compose.yml (optional mount) and run_all.sh.
echo "Ensuring Plumbline exists at $PLUMBLINE_DIR..."
if [ ! -d "$PLUMBLINE_DIR/.git" ]; then
  mkdir -p "$(dirname "$PLUMBLINE_DIR")"
  git clone "$PLUMBLINE_REPO" "$PLUMBLINE_DIR" || echo "  (Plumbline clone failed — optional; skipping)"
else
  echo "Plumbline already present; leaving existing checkout untouched."
fi

# Obsidian vault is a host-side data directory, not software vendored here.
echo "Ensuring Obsidian-compatible vault directory exists at $VAULT_DIR..."
mkdir -p "$VAULT_DIR"

cat <<MSG
Setup complete.

Next steps:
  1. cp .env.example .env  (set MCP_GBRAIN_API_KEY, OLLAMA/QDRANT hosts)
  2. docker compose up -d --build           # backend :3000
     docker compose --profile frontend up -d --build   # + atlas UI :8080
  3. Connect Hermes / an MCP client to: http://<host>:3000/mcp
MSG
