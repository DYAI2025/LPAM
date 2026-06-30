#!/bin/bash
# ============================================================================
# Connect the LOCAL Hermes Electron desktop app to the REMOTE VPS Hermes brain.
# One click: ensures the VPS dashboard API is up (with our shared token), opens
# an SSH tunnel, then (re)launches the desktop Electron app in REMOTE mode.
#
#   Mac Electron app ──HERMES_DESKTOP_REMOTE_URL=http://127.0.0.1:PORT──┐
#   localhost:PORT ──SSH -L──> VPS 127.0.0.1:PORT (hermes dashboard)
#                                         └─ talks to VPS gateway/brain
#
# Revert to the local brain: local/desktop-local.sh
# Env overrides: HERMES_SSH_ALIAS (ssh alias), HERMES_APP_BIN (path to the
# Hermes.app binary — e.g. /Applications/Hermes.app/Contents/MacOS/Hermes).
# ============================================================================
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

PORT=9119
HOSTALIAS="${HERMES_SSH_ALIAS:-hermes-brain}"
BIN="${HERMES_APP_BIN:-$HOME/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app/Contents/MacOS/Hermes}"
TOKFILE="$HOME/.hermes-bridge/desktop-remote.token"
LOG="$HOME/.hermes-bridge/desktop-remote.log"
ts(){ date "+%Y-%m-%dT%H:%M:%S%z"; }
log(){ printf '%s\t%s\n' "$(ts)" "$*" >>"$LOG"; }

TOK="$(cat "$TOKFILE" 2>/dev/null)"
[ -z "$TOK" ] && { echo "no token at $TOKFILE (copy the VPS dashboard token there)"; exit 1; }

# 1. Ensure the VPS dashboard (desktop API) is running on 127.0.0.1:PORT with OUR token.
log "ensuring VPS hermes dashboard on :$PORT"
ssh "$HOSTALIAS" 'bash -l -s' >>"$LOG" 2>&1 <<REMOTE
if curl -s -o /dev/null --max-time 4 http://127.0.0.1:$PORT/api/status; then
  echo "vps dashboard already up"
else
  HERMES_DASHBOARD_SESSION_TOKEN='$TOK' setsid nohup hermes dashboard --no-open --host 127.0.0.1 --port $PORT --skip-build >/root/.hermes/desktop-dashboard.log 2>&1 &
  sleep 8
fi
REMOTE

# 2. Open the SSH tunnel (IPv4-bound; idempotent).
if ! curl -s -o /dev/null --max-time 3 http://127.0.0.1:$PORT/api/status; then
  log "opening tunnel $PORT"
  ssh -fN -o ExitOnForwardFailure=yes -o ConnectTimeout=10 \
      -L "127.0.0.1:${PORT}:127.0.0.1:${PORT}" "$HOSTALIAS" 2>>"$LOG" || log "tunnel rc=$?"
  for _ in $(seq 1 16); do curl -s -o /dev/null --max-time 2 http://127.0.0.1:$PORT/api/status && break; sleep 0.5; done
fi

# 3. Verify the brain is reachable before touching the app.
if ! curl -s --max-time 5 -H "X-Hermes-Session-Token: $TOK" http://127.0.0.1:$PORT/api/status >/dev/null; then
  log "VPS brain not reachable — aborting, leaving app as-is"
  osascript -e 'display notification "VPS-Brain nicht erreichbar" with title "Hermes Remote"' 2>/dev/null
  exit 1
fi

# 4. Restart the desktop app in REMOTE mode.
log "relaunching desktop in remote mode -> http://127.0.0.1:$PORT"
osascript -e 'quit app "Hermes"' 2>/dev/null; sleep 2
pkill -f "Hermes.app/Contents/MacOS/Hermes" 2>/dev/null; sleep 2
HERMES_DESKTOP_REMOTE_URL="http://127.0.0.1:${PORT}" \
HERMES_DESKTOP_REMOTE_TOKEN="$TOK" \
nohup "$BIN" >>"$LOG" 2>&1 &
log "launched pid=$!"
osascript -e 'display notification "Desktop-App nutzt jetzt das VPS-Gehirn" with title "Hermes Remote ✓"' 2>/dev/null
