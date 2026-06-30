#!/bin/bash
# ============================================================================
# gbrain-atlas (memory GRAPH UI) launcher — one click.
# Opens an SSH local-forward to the LPAM atlas frontend on the VPS, then a
# chromeless browser window. Idempotent: reuses an existing tunnel.
#   Mac localhost:8088  ──SSH──>  VPS 127.0.0.1:8080 (lpam-frontend / gbrain-atlas)
# Env override: HERMES_SSH_ALIAS (ssh alias).
# ============================================================================
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

LPORT=8088                  # local port on the Mac (8080 is often busy locally)
RPORT=8080                  # VPS atlas frontend port (docker lpam-frontend)
HOSTALIAS="${HERMES_SSH_ALIAS:-hermes-brain}"
URL="http://localhost:${LPORT}/"
LOG="$HOME/.hermes-bridge/atlas-launcher.log"
ts(){ date "+%Y-%m-%dT%H:%M:%S%z"; }
log(){ printf '%s\t%s\n' "$(ts)" "$*" >>"$LOG"; }

open_browser() {
  if [ -d "/Applications/Google Chrome.app" ]; then
    open -na "Google Chrome" --args --app="$URL"
  else
    open "$URL"
  fi
}

if curl -s -o /dev/null --max-time 3 "$URL"; then
  log "tunnel already up -> open"; open_browser; exit 0
fi

log "opening ssh tunnel $LPORT:127.0.0.1:$RPORT via $HOSTALIAS"
ssh -f -N -o ExitOnForwardFailure=yes -o ConnectTimeout=10 \
    -L "127.0.0.1:${LPORT}:127.0.0.1:${RPORT}" "$HOSTALIAS" 2>>"$LOG" || log "ssh rc=$?"

for _ in $(seq 1 16); do curl -s -o /dev/null --max-time 2 "$URL" && break; sleep 0.5; done
log "open browser"; open_browser
