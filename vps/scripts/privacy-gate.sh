#!/usr/bin/env bash
# Privacy / final-gate validation. Portable rework of the original run_all.sh:
# host paths are parameterized and the author-specific stages are optional.
# Succeeds only when it prints the literal sentinel: FINAL GATE: TRUE-GREEN
#
# Env:
#   VAULT_DIR      Obsidian vault to scan         (default: ./vault)
#   BRAIN_DIR      gbrain brain dir to scan       (default: ./backend/brain)
#   BACKEND_DIR    backend dir for the test stage (default: ./backend; empty = skip)
#   PLUMBLINE_DIR  Plumbline checkout for CI       (default: empty = skip)
set -euo pipefail
cd "$(dirname "$0")/../.."                   # repo root

VAULT_DIR="${VAULT_DIR:-./vault}"
BRAIN_DIR="${BRAIN_DIR:-./backend/brain}"
BACKEND_DIR="${BACKEND_DIR:-./backend}"
PLUMBLINE_DIR="${PLUMBLINE_DIR:-}"

echo "Running LPAM Final Gate Validation..."

# Stage 1 — Plumbline CI (optional; author-specific governance suite).
if [ -n "$PLUMBLINE_DIR" ] && [ -f "$PLUMBLINE_DIR/config/claude/tests/run_all.sh" ]; then
  echo "Stage 1: Plumbline CI"
  bash "$PLUMBLINE_DIR/config/claude/tests/run_all.sh"
else
  echo "Stage 1: Plumbline CI — skipped (set PLUMBLINE_DIR to enable)"
fi

# Stage 2 — backend integration test (optional).
if [ -n "$BACKEND_DIR" ] && [ -f "$BACKEND_DIR/test/mcp-client-hardening.test.ts" ]; then
  echo "Stage 2: Integration Tests"
  ( cd "$BACKEND_DIR" && bun test test/mcp-client-hardening.test.ts )
else
  echo "Stage 2: Integration Tests — skipped (no backend test found)"
fi

# Stage 3 — privacy leak gate (the hard gate). Fails the build on any non-example secret.
echo "Stage 3: Privacy Leak Check ($VAULT_DIR, $BRAIN_DIR)"
scan_targets=()
[ -e "$VAULT_DIR" ] && scan_targets+=("$VAULT_DIR")
[ -e "$BRAIN_DIR" ] && scan_targets+=("$BRAIN_DIR")
if [ ${#scan_targets[@]} -gt 0 ]; then
  leaks="$(grep -rE "API_KEY|SECRET|PASSWORD|TOKEN" "${scan_targets[@]}" 2>/dev/null | grep -v "example" || true)"
  if [ -n "$leaks" ]; then
    echo "PRIVACY LEAK DETECTED:"
    echo "$leaks"
    exit 1
  fi
else
  echo "  (nothing to scan — VAULT_DIR/BRAIN_DIR not present)"
fi

echo "----------------------------------------"
echo "FINAL GATE: TRUE-GREEN"
echo "----------------------------------------"
