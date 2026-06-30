#!/bin/bash
# LPAM installer — populate submodules (gbrain backend + gbrain-atlas frontend),
# install backend deps, initialize a fresh PGLite brain. Idempotent.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> LPAM setup"

# 1. Submodules. Prefer .gitmodules: pins backend/frontend to the commits this
#    repo recorded (reproducible for anyone cloning). Fall back to upstream tips
#    only if .gitmodules is somehow missing.
if [ -f .gitmodules ]; then
  echo "==> Initializing submodules at pinned commits…"
  git submodule sync --recursive
  git submodule update --init --recursive
else
  echo "==> No .gitmodules found — cloning upstream tips (fallback)…"
  rm -rf backend frontend
  git clone https://github.com/DYAI2025/gbrain.git backend
  git clone https://github.com/DYAI2025/gbrain-atlas.git frontend
fi

# 2. Backend dependencies (bun) + PGLite brain.
BRAIN_DIR="${GBRAIN_BRAIN_DIR:-./brain}"   # relative to backend/, matches compose mount ./backend/brain
cd backend
echo "==> Installing backend deps (bun install)…"
bun install

# gbrain CLI is provided by the backend package after install.
if command -v gbrain >/dev/null 2>&1; then
  GBRAIN_BIN="gbrain"
elif command -v bunx >/dev/null 2>&1; then
  GBRAIN_BIN="bunx gbrain"
else
  echo "Error: neither 'gbrain' nor 'bunx' is available on PATH."
  echo "Please install the gbrain CLI (via the backend package) or bun (for 'bunx gbrain') before running this script."
  exit 1
fi

if [ ! -e "$BRAIN_DIR" ]; then
  echo "==> Initializing PGLite brain at backend/$BRAIN_DIR…"
  $GBRAIN_BIN init --pglite --path "$BRAIN_DIR"
else
  echo "==> Brain already exists at backend/$BRAIN_DIR — skipping init."
fi
cd ..

echo "==> Setup complete."
echo "    Next: cp .env.example .env  (fill values), then: docker compose up --build"
