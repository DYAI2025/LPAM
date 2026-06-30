#!/bin/bash
# Persistent SSH local-forward Mac:9119 -> VPS 127.0.0.1:9119 (hermes dashboard API).
# Run in FOREGROUND (no -f) so launchd tracks it and KeepAlive restarts it on drop.
# ServerAlive* makes ssh notice dead links fast so launchd can respawn.
# Set HERMES_SSH_ALIAS to your ssh host alias (see local/ssh-config-snippet).
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"
ALIAS="${HERMES_SSH_ALIAS:-hermes-brain}"
exec ssh -N \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -o ConnectTimeout=10 \
  -L 127.0.0.1:9119:127.0.0.1:9119 \
  "$ALIAS"
