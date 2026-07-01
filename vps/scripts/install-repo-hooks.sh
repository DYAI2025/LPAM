#!/bin/bash
# install-repo-hooks.sh <repo-path> [--backfill] — wire a repo into the gbrain
# semantic graph. THE natural way to ADD a repo: run this once per repo.
#
# Installs post-commit + post-merge git hooks so the repo's curated docs
# (README + docs/) auto-sync into gbrain on every commit AND on every pull/merge
# (covers repos whose dev happens elsewhere and land on this host via `git pull`).
# Deploys the canonical helper to $GBRAIN_HOME/sync-repo-docs.sh.
#
# Example:  ./vps/scripts/install-repo-hooks.sh /root/my-new-project --backfill
set -euo pipefail
REPO="${1:?usage: install-repo-hooks.sh <repo-path> [--backfill]}"
REPO="$(cd "$REPO" && pwd)"
[ -d "$REPO/.git" ] || { echo "not a git repo: $REPO" >&2; exit 1; }

GBRAIN_HOME="${GBRAIN_HOME:-/root/.gbrain}"
HELPER_SRC="$(cd "$(dirname "$0")" && pwd)/sync-repo-docs.sh"
HELPER="$GBRAIN_HOME/sync-repo-docs.sh"
install -D -m755 "$HELPER_SRC" "$HELPER"

for h in post-commit post-merge; do
  hook="$REPO/.git/hooks/$h"
  cat > "$hook" <<HK
#!/bin/bash
# gbrain semantic-graph auto-sync (README + docs/ → gbrain on commit/pull)
nohup "$HELPER" "$REPO" >/dev/null 2>&1 &
exit 0
HK
  chmod +x "$hook"
done
echo "✓ wired $REPO → gbrain (post-commit + post-merge)"

if [ "${2:-}" = "--backfill" ]; then
  echo "→ initial backfill…"
  "$HELPER" "$REPO"
  echo "✓ backfill done (see $GBRAIN_HOME/repo-sync.log)"
fi
