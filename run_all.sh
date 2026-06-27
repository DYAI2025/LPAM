#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUMBLINE_DIR="${PLUMBLINE_DIR:-/root/Plumbline}"
VAULT_DIR="${VAULT_DIR:-/root/obsidian-vault}"
BRAIN_DIR="${BRAIN_DIR:-$ROOT_DIR/backend/brain}"

echo "Running LPAM Final Gate Validation..."

# 1. Run existing Plumbline CI
echo "Stage 1: Plumbline CI"
bash "$PLUMBLINE_DIR/config/claude/tests/run_all.sh"

# 2. Run GBrain integration tests when the expected test file is available
echo "Stage 2: Integration Tests"
cd "$ROOT_DIR/backend"
if [ -f "test/mcp-client-hardening.test.ts" ]; then
  bun test test/mcp-client-hardening.test.ts
else
  echo "WARNING: test/mcp-client-hardening.test.ts not found in current GBrain checkout; running gbrain doctor instead."
  gbrain doctor
fi

# 3. Privacy Leak Check
echo "Stage 3: Privacy Leak Check"
cd "$ROOT_DIR"
leak_paths=()
[ -d "$VAULT_DIR" ] && leak_paths+=("$VAULT_DIR")
[ -d "$BRAIN_DIR" ] && leak_paths+=("$BRAIN_DIR")

if [ "${#leak_paths[@]}" -gt 0 ]; then
  leaks=$(rg -n --hidden -i "API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE KEY" "${leak_paths[@]}" -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/*.example*' || true)
  if [ -n "$leaks" ]; then
    echo "PRIVACY LEAK DETECTED:"
    echo "$leaks"
    exit 1
  fi
else
  echo "WARNING: No vault or brain directory found for privacy leak scan."
fi

echo "----------------------------------------"
echo "FINAL GATE: TRUE-GREEN"
echo "----------------------------------------"
