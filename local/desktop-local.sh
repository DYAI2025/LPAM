#!/bin/bash
# Revert the Hermes desktop app to its LOCAL brain (undo desktop-remote-launcher.sh).
# Quits the remote-mode app and relaunches WITHOUT the remote env vars, so the app
# falls back to spawning its own local ~/.hermes backend. Leaves the SSH tunnel +
# VPS dashboard untouched (close them manually if desired).
# Env override: HERMES_APP_BIN (path to the Hermes.app binary).
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"
BIN="${HERMES_APP_BIN:-$HOME/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app/Contents/MacOS/Hermes}"
osascript -e 'quit app "Hermes"' 2>/dev/null; sleep 2
pkill -f "Hermes.app/Contents/MacOS/Hermes" 2>/dev/null; sleep 2
env -u HERMES_DESKTOP_REMOTE_URL -u HERMES_DESKTOP_REMOTE_TOKEN nohup "$BIN" >/dev/null 2>&1 &
osascript -e 'display notification "Desktop-App nutzt wieder das lokale Gehirn" with title "Hermes Local"' 2>/dev/null
echo "reverted to local brain"
