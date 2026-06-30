#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GBRAIN_REPO="${GBRAIN_REPO:-https://github.com/garrytan/gbrain.git}"
PLUMBLINE_REPO="${PLUMBLINE_REPO:-https://github.com/DYAI2025/Plumbline.git}"
PLUMBLINE_DIR="${PLUMBLINE_DIR:-/root/Plumbline}"
VAULT_DIR="${VAULT_DIR:-/root/obsidian-vault}"

cd "$ROOT_DIR"

echo "Setting up LPAM (GBrain + Plumbline + Obsidian vault harness)..."
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v bun >/dev/null || { echo "bun is required for local bootstrap. Install from https://bun.sh first." >&2; exit 1; }

# Backend: clone Garry Tan's upstream GBrain core engine.
echo "Setting up GBrain backend from $GBRAIN_REPO..."
rm -rf backend
git clone "$GBRAIN_REPO" backend
cd backend
bun install

echo "Initializing GBrain brain (PGLite) in ./backend/brain..."
gbrain init --pglite --path ./brain
cd "$ROOT_DIR"

# Plumbline is required by docker-compose.yml and run_all.sh.
echo "Ensuring Plumbline exists at $PLUMBLINE_DIR..."
if [ ! -d "$PLUMBLINE_DIR/.git" ]; then
  mkdir -p "$(dirname "$PLUMBLINE_DIR")"
  git clone "$PLUMBLINE_REPO" "$PLUMBLINE_DIR"
else
  echo "Plumbline already present; leaving existing checkout untouched."
fi

# Obsidian vault directory is a host-side data directory, not software vendored here.
echo "Ensuring Obsidian-compatible vault directory exists at $VAULT_DIR..."
mkdir -p "$VAULT_DIR"

cat <<MSG
Setup complete.

Next steps:
  1. If you use a frontend explorer, place it in ./frontend with package.json and bun.lock.
  2. Run: docker compose up -d --build
  3. Connect Hermes or another MCP client to: http://<vps-host>:3000
MSG
