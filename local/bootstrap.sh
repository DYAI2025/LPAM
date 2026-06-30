#!/usr/bin/env bash
# LPAM LOCAL bootstrap (macOS) — install the Mac-side glue that connects the
# Hermes desktop app to your VPS brain + serves local Ollama over Tailscale.
# Idempotent. Run from the repo root after the VPS side is up.
#
# Required:
#   DASHBOARD_TOKEN   the token printed by vps/bootstrap.sh (or in vps/.dashboard-token)
# Optional:
#   BRIDGE_DIR        where to install the glue   (default: ~/.hermes-bridge)
#   VPS_HOST          VPS hostname / tailnet name (for the ssh-config reminder)
set -euo pipefail
cd "$(dirname "$0")/.."                       # repo root

[ "$(uname)" = "Darwin" ] || { echo "This bootstrap is macOS-only (launchd/AppleScript)."; exit 1; }

BRIDGE_DIR="${BRIDGE_DIR:-$HOME/.hermes-bridge}"
LA_DIR="$HOME/Library/LaunchAgents"
HERMES_APP_SUPPORT="$HOME/Library/Application Support/Hermes"
DASHBOARD_TOKEN="${DASHBOARD_TOKEN:-}"
[ -z "$DASHBOARD_TOKEN" ] && [ -f vps/.dashboard-token ] && DASHBOARD_TOKEN="$(cat vps/.dashboard-token)"
if [ -z "$DASHBOARD_TOKEN" ]; then
  echo "ERROR: set DASHBOARD_TOKEN (from the VPS bootstrap output / vps/.dashboard-token)"; exit 1
fi

mkdir -p "$BRIDGE_DIR" "$LA_DIR" "$HERMES_APP_SUPPORT"

# 1. Glue scripts -> BRIDGE_DIR
echo "==> Installing glue scripts to $BRIDGE_DIR"
for f in tunnel-9119.sh ollama-tailnet.sh desktop-remote-launcher.sh desktop-local.sh atlas-launcher.sh; do
  cp "local/$f" "$BRIDGE_DIR/$f"; chmod +x "$BRIDGE_DIR/$f"
done

# 2. Dashboard token -> token file (used by desktop-remote-launcher.sh)
printf '%s' "$DASHBOARD_TOKEN" > "$BRIDGE_DIR/desktop-remote.token"
chmod 600 "$BRIDGE_DIR/desktop-remote.token"

# 3. connection.json (desktop app remote mode)
sed "s#@@DASHBOARD_TOKEN@@#${DASHBOARD_TOKEN}#g" local/connection.json.template \
  > "$HERMES_APP_SUPPORT/connection.json"
chmod 600 "$HERMES_APP_SUPPORT/connection.json"
echo "==> Wrote $HERMES_APP_SUPPORT/connection.json (mode: remote)"

# 4. LaunchAgents (render @@HERMES_BRIDGE@@, load)
for p in com.hermes.tunnel9119 com.hermes.ollama-tailnet; do
  sed "s#@@HERMES_BRIDGE@@#${BRIDGE_DIR}#g" "local/launchagents/${p}.plist" > "$LA_DIR/${p}.plist"
  launchctl unload "$LA_DIR/${p}.plist" 2>/dev/null || true
  launchctl load -w "$LA_DIR/${p}.plist"
  echo "==> loaded LaunchAgent $p"
done

echo
echo "==> Done. Remaining manual steps:"
echo "  1. Add the ssh alias: append local/ssh-config-snippet to ~/.ssh/config"
echo "     (set HostName to your VPS${VPS_HOST:+ = $VPS_HOST}; see docs/tailscale.md)."
echo "  2. Quit the GUI Ollama.app if installed (it binds 127.0.0.1 and conflicts on :11434)."
echo "  3. Connect the desktop app to the VPS brain:  $BRIDGE_DIR/desktop-remote-launcher.sh"
echo "     (revert to local brain:  $BRIDGE_DIR/desktop-local.sh)"
echo "  4. Verify the tunnel:  curl http://127.0.0.1:9119/api/status"
