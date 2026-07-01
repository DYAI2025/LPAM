# Semantic graph auto-sync (repo docs → gbrain)

Keep the gbrain semantic graph continuously in sync with your projects: each wired
repo pushes its **curated docs (README + `docs/`)** into gbrain on every commit and
every pull. Adding projects is meant to be a **natural, incremental process** — one
command per new repo, then it maintains itself.

## How it works
- Per-repo git hooks: **`post-commit`** (fires on a local commit) + **`post-merge`**
  (fires on `git pull`/merge — covers repos whose dev happens elsewhere).
- The hook runs `vps/scripts/sync-repo-docs.sh <repo>` (detached — never slows the commit).
- The helper copies only `README*` + `docs/**` (namespaced under `<repo>/`) into a
  `/tmp` staging dir (must be outside any git worktree, or gbrain's `git ls-files`
  collector skips it), then `gbrain import` chunks + embeds them.
- **Incremental + free:** `gbrain import` dedups by content-hash, so only *changed*
  docs re-embed, via the **local** ollama (`nomic-embed-text`, 768d) — zero API cost,
  no polling, work happens only on real changes.

## Add a repo (the natural process)
```bash
# once per repo — installs both hooks + (optional) an initial backfill
./vps/scripts/install-repo-hooks.sh /root/<repo> --backfill
```
From then on, every commit/pull to that repo updates the graph automatically.

## Scope choice — why docs only
Whole-repo markdown sync is deliberately avoided: large repos carry hundreds of
vendored/generated `.md` files (e.g. one project had 857 md / 1.4 GB) → hours of
CPU embedding + graph bloat + low signal. `README + docs/` is the curated,
high-signal project knowledge. To ingest more of a specific repo, point the helper
at a wider path or add a `docs/`-style curated tree.

## Currently wired (reference deployment)
`Brain`, `bazodiac-signature-prototypes`, `hermes-control-interface`, `hippo-memory`,
`browser-harness`, `Plumbline`. Log: `/root/.gbrain/repo-sync.log`.

## Notes
- The Obsidian **vault** (`~/SemanticMind-Vault`, exposed via the `vault-mcp.py` MCP)
  is a *separate*, manually-curated human graph — not part of this git auto-sync.
- Query the graph: `gbrain query "<question>"` (hybrid keyword + vector) or via the
  MCP tools Hermes uses.
