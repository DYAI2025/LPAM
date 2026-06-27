#!/usr/bin/env bash
set -e

echo "Running LPAM Final Gate Validation..."

# 1. Run existing Plumbline CI
echo "Stage 1: Plumbline CI"
bash /root/Plumbline/config/claude/tests/run_all.sh

# 2. Run new Integration Tests
echo "Stage 2: Integration Tests"
cd /root/lpam/backend && bun test test/mcp-client-hardening.test.ts

# 3. Privacy Leak Check
echo "Stage 3: Privacy Leak Check"
# Search for secrets in the vault and brain
leaks=$(grep -rE "API_KEY|SECRET|PASSWORD|TOKEN" /root/obsidian-vault /root/lpam/backend/brain | grep -v "example" || true)
if [ -n "$leaks" ]; then
    echo "PRIVACY LEAK DETECTED:"
    echo "$leaks"
    exit 1
fi

echo "----------------------------------------"
echo "FINAL GATE: TRUE-GREEN"
echo "----------------------------------------"
