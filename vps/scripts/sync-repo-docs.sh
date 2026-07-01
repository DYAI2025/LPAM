#!/bin/bash
# sync-repo-docs.sh <repo-path> — ingest a repo's curated docs (README + docs/)
# into the gbrain semantic graph. Called by the repo's post-commit/post-merge hooks
# (see install-repo-hooks.sh). Scoped (docs+README only, no vendored/generated md)
# and incremental (gbrain import dedups by content-hash → only changed docs re-embed).
#
# Env (sensible defaults):
#   GBRAIN_HOME         gbrain data dir + DATABASE_URL file (default: /root/.gbrain)
#   GBRAIN_DIR          gbrain checkout with src/cli.ts    (default: /root/gbrain)
#   BUN_BIN             bun binary                          (default: $(command -v bun))
#   OLLAMA_BASE_URL     OpenAI-compat embeddings endpoint   (default: http://localhost:11434/v1)
#   GBRAIN_DATABASE_URL postgres URL                        (default: read from $GBRAIN_HOME/DATABASE_URL)
set -uo pipefail
REPO="${1:?usage: sync-repo-docs.sh <repo-path>}"
NAME="$(basename "$REPO")"
GBRAIN_HOME="${GBRAIN_HOME:-/root/.gbrain}"
GBRAIN_DIR="${GBRAIN_DIR:-/root/gbrain}"
BUN="${BUN_BIN:-$(command -v bun 2>/dev/null || echo /root/.bun/bin/bun)}"
LOG="$GBRAIN_HOME/repo-sync.log"

# Staging MUST live outside any git worktree: gbrain's git-aware collector
# (`git ls-files`) honors .gitignore, so a staging dir under a git repo (e.g. /root)
# gets skipped and import finds 0 files. /tmp is safe.
STAGE="/tmp/gbrain-stage-$NAME"
rm -rf "$STAGE"; mkdir -p "$STAGE/$NAME"

# Curated set: root README(s) + the docs/ tree, namespaced under <repo>/ so slugs
# never collide across repos (e.g. plumbline/docs/x vs brain/docs/x).
for f in "$REPO"/README*.md "$REPO"/readme*.md; do [ -f "$f" ] && cp "$f" "$STAGE/$NAME/"; done
[ -d "$REPO/docs" ] && cp -r "$REPO/docs" "$STAGE/$NAME/docs" 2>/dev/null

n=$(find "$STAGE" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
[ "$n" -gt 0 ] || { echo "$(date -Is) $NAME: no README/docs — skip" >>"$LOG"; rm -rf "$STAGE"; exit 0; }

export GBRAIN_DATABASE_URL="${GBRAIN_DATABASE_URL:-$(cat "$GBRAIN_HOME/DATABASE_URL" 2>/dev/null)}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434/v1}"
export GBRAIN_AI_EMBED_TIMEOUT_MS="${GBRAIN_AI_EMBED_TIMEOUT_MS:-600000}"

cd "$GBRAIN_DIR" || { echo "$(date -Is) $NAME: no gbrain dir $GBRAIN_DIR" >>"$LOG"; exit 1; }
echo "$(date -Is) $NAME: import start ($n md)" >>"$LOG"
"$BUN" run src/cli.ts import "$STAGE" >>"$LOG" 2>&1
echo "$(date -Is) $NAME: import done" >>"$LOG"
rm -rf "$STAGE"
