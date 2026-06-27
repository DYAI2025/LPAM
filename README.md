# LPAM — VPS Agent Memory Harness for GBrain, Hermes, Plumbline, and Obsidian

<p align="center">
  <strong>LPAM is a VPS deployment harness for a GBrain HTTP backend, Plumbline, and an Obsidian-compatible Markdown vault.</strong><br>
  It clones <a href="https://github.com/garrytan/gbrain">GBrain</a>, mounts your Plumbline checkout, and keeps a server-side vault directory available for Obsidian workflows.
</p>

<p align="center">
  <a href="#what-this-repository-is">Overview</a> ·
  <a href="#verified-repository-facts">Verified facts</a> ·
  <a href="#installation">Installation</a> ·
  <a href="#hermes-and-agent-integration">Agent integration</a> ·
  <a href="#licenses-and-attribution">Licenses</a>
</p>

---

## What this repository is

**LPAM** is a small deployment harness, not a fork of GBrain, Obsidian, Hermes, or Plumbline. The tracked files in this repository are Docker and shell glue for running a cloned GBrain backend together with a mounted Plumbline checkout and a Markdown vault directory on a VPS.

The current harness is built around these components:

| Component | Source / ownership | Role in LPAM |
|---|---|---|
| **GBrain** | External upstream: `https://github.com/garrytan/gbrain.git` | Cloned into `./backend`; upstream package metadata describes it as a Postgres-native personal knowledge brain with hybrid RAG search. |
| **Plumbline** | First-party dependency: `https://github.com/DYAI2025/Plumbline.git` | Required host workspace and validation source for this VPS setup. |
| **Obsidian vault** | User-owned local data directory, usually opened with Obsidian | LPAM creates/mounts `/root/obsidian-vault`; it does not install or redistribute Obsidian. |
| **Frontend explorer** | Optional local `./frontend` app | Docker can build it only when a compatible local app with `package.json` and `bun.lock` exists. |
| **LPAM harness** | This repository | Installation, Docker Compose orchestration, validation, and documentation. |

## Verified repository facts

This README was checked against the files currently committed in this repository:

```text
LPAM/
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── install.sh
├── run_all.sh
└── README.md
```

Facts validated from the tracked LPAM files and upstream GBrain metadata:

- `Dockerfile.backend` expects `./backend/package.json` and `./backend/bun.lock` to exist before `docker compose build` runs.
- `Dockerfile.frontend` expects `./frontend/package.json` and `./frontend/bun.lock` to exist before the optional frontend profile can be built.
- `docker-compose.yml` mounts `/root/Plumbline` read-only and `/root/obsidian-vault` read/write into the backend container, and it keeps the frontend behind an explicit Compose profile.
- `install.sh` clones GBrain from `https://github.com/garrytan/gbrain.git`, ensures Plumbline exists, and creates the Obsidian-compatible vault directory.
- `run_all.sh` now resolves paths from the LPAM checkout instead of assuming `/root/lpam`, and it uses `rg` for the privacy scan.
- GBrain upstream `package.json` declares `license: MIT`; its upstream `LICENSE` file is MIT. LPAM does not copy GBrain source into this repository, but an installed `./backend` checkout carries the upstream license.

## Architecture

```mermaid
flowchart TD
    Agent[Hermes / Claude / Codex / MCP client] -->|HTTP MCP| Backend[GBrain backend\nBun runtime\nPort 3000]
    Backend -->|persistent PGLite data| Brain[(./backend/brain)]
    Backend -->|read-only project context| Plumbline[/root/Plumbline]
    Backend -->|Markdown knowledge| Vault[/root/obsidian-vault\nObsidian-compatible vault]
    Backend -->|optional local models| Ollama[Ollama\n172.17.0.1:11434]
    Backend -->|optional vector service| Qdrant[Qdrant\n172.17.0.1:6333]
    Operator[Human operator] -->|Obsidian desktop app| Vault
    Operator -->|browser, if frontend exists| Frontend[Optional frontend\nNginx\nPort 8080]
    Frontend --> Backend
```

### Backend container

The backend Dockerfile uses `oven/bun:latest`, installs the cloned backend dependencies with `bun install --frozen-lockfile`, exposes port `3000`, and starts `gbrain serve --http`.

### Optional frontend container

The frontend Dockerfile is valid only when a compatible frontend app exists in `./frontend`. It builds a Bun/Vite/React-style app and serves the resulting `dist` directory with `nginx:alpine`. Because this LPAM repository does not currently include or reliably bootstrap a public frontend source, treat the frontend as optional until you place a compatible app there.

### Runtime mounts

| Host path | Container path | Mode | Purpose |
|---|---|---|---|
| `./backend/brain` | `/app/brain` | read/write | Persistent GBrain PGLite memory. |
| `/root/Plumbline` | `/root/Plumbline` | read-only | Plumbline workspace required by this setup. |
| `/root/obsidian-vault` | `/app/vault` | read/write | Markdown vault for Obsidian and agent-readable notes. |

## Prerequisites

Required on the VPS:

- Linux shell access.
- Git.
- Bun for local bootstrap (`install.sh` runs `bun install` and `gbrain init`).
- Docker Engine and Docker Compose for containerized operation.
- Network access to clone GBrain and Plumbline.
- Enough disk space for a growing memory database and Markdown vault.

Optional but commonly used:

- Obsidian desktop or mobile app pointed at the same Markdown vault directory through your sync strategy.
- Ollama on the VPS host at `http://172.17.0.1:11434`.
- Qdrant on the VPS host at `http://172.17.0.1:6333`.
- A reverse proxy such as Caddy, Nginx, or Traefik for HTTPS and authentication.

## Installation

### 1. Clone LPAM

```bash
git clone <your-lpam-repository-url> LPAM
cd LPAM
```

### 2. Bootstrap GBrain, Plumbline, and the vault

```bash
bash install.sh
```

The installer performs these actions:

1. clones `https://github.com/garrytan/gbrain.git` into `./backend`;
2. installs GBrain dependencies with Bun;
3. initializes a local PGLite brain at `./backend/brain`;
4. clones `https://github.com/DYAI2025/Plumbline.git` into `/root/Plumbline` if it is not already present;
5. creates `/root/obsidian-vault` for Markdown files used with Obsidian.

You can override paths and repositories:

```bash
GBRAIN_REPO=https://github.com/garrytan/gbrain.git \
PLUMBLINE_REPO=https://github.com/DYAI2025/Plumbline.git \
PLUMBLINE_DIR=/root/Plumbline \
VAULT_DIR=/root/obsidian-vault \
bash install.sh
```

### 3. Build and run the backend

If you do not have a compatible frontend in `./frontend`, start only the backend:

```bash
docker compose up -d --build backend
```

If you have added a compatible frontend app with `package.json` and `bun.lock`, start both services with the frontend profile:

```bash
docker compose --profile frontend up -d --build
```

### 4. Verify the running service

```bash
docker compose ps
curl http://localhost:3000
```

Expected result for this harness: the backend container is running, host port `3000` maps to container port `3000`, and `./backend/brain` is mounted into the container at `/app/brain`.

## Hermes and agent integration

Configure Hermes, Claude Code, Codex, or another MCP-capable agent to use the GBrain backend endpoint:

```text
http://<your-vps-host-or-ip>:3000
```

For agents running on the same VPS:

```text
http://localhost:3000
```

Expected behavior from the LPAM wiring:

- agent clients point at the GBrain HTTP server exposed by this harness;
- `./backend/brain` remains on the host as the mounted backend data directory;
- `/root/Plumbline` is available read-only inside the backend container;
- `/root/obsidian-vault` is mounted into the backend container as `/app/vault`;
- `OLLAMA_HOST` and `QDRANT_HOST` are passed to the backend container as environment variables.

For production use, put HTTPS and authentication in front of the backend. Do not expose unauthenticated port `3000` directly to the public internet.

## Obsidian usage model

LPAM does not install Obsidian. Obsidian is desktop/mobile software that reads and writes local Markdown vaults. In this setup, `/root/obsidian-vault` is simply the server-side Markdown directory mounted into the GBrain container as `/app/vault`.

A practical workflow is:

1. keep long-term agent notes as Markdown in `/root/obsidian-vault`;
2. sync or access that directory with your preferred Obsidian workflow;
3. use GBrain according to its upstream documentation for memory and retrieval;
4. use Obsidian for human review, editing, linking, and audits.

## Operations

### Start backend only

```bash
docker compose up -d backend
```

### Start backend and frontend

```bash
docker compose --profile frontend up -d
```

### Stop services

```bash
docker compose down
```

### Rebuild after upstream changes

```bash
docker compose up -d --build backend
```

### View logs

```bash
docker compose logs -f backend
```

### Back up persistent memory and Markdown notes

```bash
tar -czf lpam-memory-backup-$(date +%Y%m%d).tar.gz backend/brain /root/obsidian-vault
```

## Validation

Run the LPAM final gate:

```bash
bash run_all.sh
```

The gate now performs:

1. Plumbline CI from `$PLUMBLINE_DIR/config/claude/tests/run_all.sh`;
2. the GBrain MCP hardening test when `test/mcp-client-hardening.test.ts` exists, otherwise `gbrain doctor`;
3. a privacy scan of the configured vault and brain directories using `rg`.

A successful run ends with:

```text
FINAL GATE: TRUE-GREEN
```

## Local repository audit

The committed LPAM harness was reviewed separately from generated directories such as `backend/`, `frontend/`, `node_modules/`, and runtime brain data. The tracked-file review covered shell syntax, Docker/Compose expectations, third-party repository references, and common secret patterns.

Secret-pattern scan used during this update:

```bash
rg -n --hidden -g '!.git/**' -i '(-----BEGIN (RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}|password\s*=|api[_-]?key\s*=|secret\s*=|token\s*=)' .
```

Result: no matches in the tracked LPAM files at the time of this README update. Continue to scan generated runtime directories before publishing backups, vault exports, or deployment snapshots.

## Security and privacy

Recommended hardening for a VPS deployment:

- Restrict port `3000` with a firewall, VPN, private network, or authenticated reverse proxy.
- Replace `GBRAIN_HTTP_CORS_ORIGIN=*` in production with the exact frontend origin you trust.
- Keep `/root/Plumbline` mounted read-only unless a specific workflow requires writes.
- Treat `./backend/brain` and `/root/obsidian-vault` as sensitive data stores.
- Back up memory and vault data to encrypted storage.
- Run the final gate before publishing memory snapshots or vault exports.
- Never commit `.env`, API keys, private keys, vault secrets, or generated runtime brain data.

## Licenses and attribution

External and adjacent components to account for:

| Component | License / attribution note |
|---|---|
| GBrain (`garrytan/gbrain`) | Upstream `package.json` declares `license: MIT`, and the upstream `LICENSE` file is MIT. LPAM clones this repo into `./backend` during installation; keep the upstream license with that checkout. |
| Plumbline (`DYAI2025/Plumbline`) | First-party dependency for this VPS workflow. Users of LPAM still need a Plumbline checkout at the configured path. |
| Obsidian | Proprietary third-party software. LPAM only creates/mounts a Markdown vault directory; it does not redistribute Obsidian. Follow Obsidian's own terms for the app and sync services. |
| Docker base images | `oven/bun:latest` and `nginx:alpine` are pulled at build time. Review their image licenses and notices for production redistribution. |
| GBrain transitive dependencies | Installed from GBrain's upstream lockfile during bootstrap/build. Their licenses are not vendored or enumerated in LPAM. |

## Troubleshooting

### `docker compose build backend` cannot find `backend/package.json`

Run:

```bash
bash install.sh
```

The backend directory is generated by cloning upstream GBrain and is intentionally not committed to LPAM.

### `docker compose up` fails for the frontend

Either add a compatible frontend app in `./frontend` or start only the backend:

```bash
docker compose up -d --build backend
```

### Plumbline path errors

Ensure Plumbline exists at the path mounted by `docker-compose.yml`:

```bash
PLUMBLINE_DIR=/root/Plumbline bash install.sh
```

### Obsidian vault is empty

That is expected on a fresh install. LPAM creates the vault directory; you decide what Markdown files, notes, or synced Obsidian content belong there.
