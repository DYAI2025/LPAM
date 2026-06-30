#!/usr/bin/env bash
# LPAM VPS bootstrap — render the systemd unit templates (substitute @@TOKENS@@)
# and install them. Idempotent. Run as root on the VPS, from the repo root.
#
# Configurable via env (sensible defaults):
#   INSTALL_DIR   repo root            (default: this repo's dir)
#   HERMES_HOME   hermes home          (default: /root/.hermes)
#   BUN_BIN       bun binary           (default: $(command -v bun) or /root/.bun/bin/bun)
#   HERMES_BIN    hermes CLI           (default: $(command -v hermes) or /root/.local/bin/hermes)
#   HCI_DIR       hermes-control dir   (default: /opt/hermes-control-interface)
#   DASHBOARD_TOKEN  dashboard session token (default: generated; saved to vps/.dashboard-token)
#   UNITS         space-separated units to install
#                 (default: "lpam-backend hermes-dashboard hermes-gateway"; add hermes-control if used)
set -euo pipefail
cd "$(dirname "$0")/.."                      # repo root
REPO="$(pwd)"

INSTALL_DIR="${INSTALL_DIR:-$REPO}"
HERMES_HOME="${HERMES_HOME:-/root/.hermes}"
BUN_BIN="${BUN_BIN:-$(command -v bun || echo /root/.bun/bin/bun)}"
HERMES_BIN="${HERMES_BIN:-$(command -v hermes || echo /root/.local/bin/hermes)}"
HCI_DIR="${HCI_DIR:-/opt/hermes-control-interface}"
UNITS="${UNITS:-lpam-backend hermes-dashboard hermes-gateway}"

# Generate + persist a dashboard token if not provided (needed by the local side).
if [ -z "${DASHBOARD_TOKEN:-}" ]; then
  if [ -f vps/.dashboard-token ]; then
    DASHBOARD_TOKEN="$(cat vps/.dashboard-token)"
  else
    DASHBOARD_TOKEN="hermes-$(head -c12 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c16)"
    echo "$DASHBOARD_TOKEN" > vps/.dashboard-token   # gitignored; copy to the local connection.json
    echo "==> generated dashboard token -> vps/.dashboard-token"
  fi
fi

render() {  # render <template> -> stdout
  sed -e "s#@@INSTALL_DIR@@#${INSTALL_DIR}#g" \
      -e "s#@@HERMES_HOME@@#${HERMES_HOME}#g" \
      -e "s#@@BUN_BIN@@#${BUN_BIN}#g" \
      -e "s#@@HERMES_BIN@@#${HERMES_BIN}#g" \
      -e "s#@@HCI_DIR@@#${HCI_DIR}#g" \
      -e "s#@@DASHBOARD_TOKEN@@#${DASHBOARD_TOKEN}#g" \
      "$1"
}

echo "==> Installing units: $UNITS"
for u in $UNITS; do
  src="vps/systemd/${u}.service"
  [ -f "$src" ] || { echo "  ! missing template $src — skipping"; continue; }
  render "$src" > "/etc/systemd/system/${u}.service"
  # drop-ins
  if [ -d "vps/systemd/${u}.service.d" ]; then
    mkdir -p "/etc/systemd/system/${u}.service.d"
    for d in "vps/systemd/${u}.service.d/"*.conf; do
      [ -e "$d" ] || continue
      render "$d" > "/etc/systemd/system/${u}.service.d/$(basename "$d")"
    done
  fi
  echo "  installed ${u}.service"
done

systemctl daemon-reload
for u in $UNITS; do
  systemctl enable --now "${u}.service" || echo "  ! enable/start failed for ${u} (check: journalctl -u ${u})"
done

echo "==> Done. Status:"
for u in $UNITS; do printf "   %-20s %s\n" "$u" "$(systemctl is-active "${u}.service" 2>/dev/null)"; done
echo "==> Dashboard token (for local connection.json): $(cat vps/.dashboard-token 2>/dev/null)"
echo "    Next: install the cron watcher (PR4), then set up the local side (PR5)."
