#!/usr/bin/env bash
# LPAM top-level bootstrap dispatcher.
#   ./bootstrap.sh --vps     install + start the VPS services (run ON the VPS, as root)
#   ./bootstrap.sh --local   install the Mac-side glue (run on your Mac)
# Forwards any extra args to the chosen sub-bootstrap.
set -euo pipefail
cd "$(dirname "$0")"

usage() {
  cat <<USAGE
Usage: ./bootstrap.sh --vps | --local [extra args…]

  --vps     Render + install the systemd units and start the gbrain/Hermes
            services. Run on the VPS as root. (see vps/bootstrap.sh)
  --local   Install the SSH tunnel, Ollama LaunchAgent, and desktop
            connection.json on macOS. (see local/bootstrap.sh)

Voice setup (push-to-talk, vault MCP) is documented separately: docs/voice.md
USAGE
}

case "${1:-}" in
  --vps)   shift; [ -f vps/bootstrap.sh ]   || { echo "vps/bootstrap.sh missing (merge the VPS PR first)"; exit 1; }; exec bash vps/bootstrap.sh "$@" ;;
  --local) shift; [ -f local/bootstrap.sh ] || { echo "local/bootstrap.sh missing (merge the local PR first)"; exit 1; }; exec bash local/bootstrap.sh "$@" ;;
  -h|--help|"") usage; exit 0 ;;
  *) echo "Unknown option: $1"; echo; usage; exit 1 ;;
esac
