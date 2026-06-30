#!/usr/bin/env bash
# Install the daily model-health watcher cron. Idempotent (replaces its own line).
#
# Env:
#   HERMES_HOME  hermes home          (default: /root/.hermes)
#   PYTHON       python with PyYAML   (default: $HERMES_HOME/hermes-agent/venv/bin/python, else system python3)
#   SCHEDULE     cron schedule        (default: "17 6 * * *")
set -euo pipefail
cd "$(dirname "$0")"
SCRIPT="$(pwd)/model_health_check.py"

HERMES_HOME="${HERMES_HOME:-/root/.hermes}"
PYTHON="${PYTHON:-$HERMES_HOME/hermes-agent/venv/bin/python}"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"
SCHEDULE="${SCHEDULE:-17 6 * * *}"
LOG="$HERMES_HOME/logs/model-health-cron.log"

mkdir -p "$HERMES_HOME/logs"
chmod +x "$SCRIPT"

LINE="$SCHEDULE HERMES_HOME=$HERMES_HOME $PYTHON $SCRIPT >> $LOG 2>&1"

# Replace any existing watcher line; preserve the rest of the crontab.
{ crontab -l 2>/dev/null | grep -vF "model_health_check.py" | grep -v '^# LPAM model-health watcher$'
  echo "# LPAM model-health watcher"
  echo "$LINE"
} | crontab -

echo "==> installed cron:"
echo "    $LINE"
echo "==> smoke-test now (no writes):"
echo "    HERMES_HOME=$HERMES_HOME $PYTHON $SCRIPT --dry-run"
