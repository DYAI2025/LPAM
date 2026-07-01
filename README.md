# LPAM — Long‑Term Persistent Agent Memory for Hermes, MCP Agents, and VPS Automation

<p align="center">
  <strong>Deploy a persistent, searchable agent memory layer on your VPS.</strong><br>
  LPAM combines the <code>gbrain</code> MCP memory backend, the <code>gbrain-atlas</code> visual frontend, persistent Docker volumes, and VPS-ready validation scripts for AI agents such as Hermes.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#hermes-agent-integration">Hermes Integration</a> ·
  <a href="#operations-on-a-vps">VPS Operations</a> ·
  <a href="#security-and-privacy">Security</a>
</p>

---

## What Is LPAM?

**LPAM** is a lightweight deployment harness for a persistent AI-agent memory stack. It is designed for operators who want agents such as **Hermes**, Claude-compatible automation, MCP clients, or custom VPS agents to store, retrieve, inspect, and validate long-term operational context.

The repository does not vendor the full application code. Instead, it provides a reproducible harness that:

- clones the **gbrain core engine** as the backend;
- clones **gbrain-atlas** as the frontend memory explorer;
- builds both services with Bun and Docker;
- persists the backend brain database across restarts;
- mounts a host-side Plumbline directory for read-only observation;
- mirrors Markdown knowledge into an Obsidian-compatible vault;
- exposes an HTTP MCP server for agent clients;
- provides a final validation gate for CI, integration tests, and privacy checks.

This makes LPAM suitable for **VPS-hosted agent memory**, **MCP memory servers**, **AI automation infrastructure**, **Hermes agent deployments**, **agentic operations**, and **long-term knowledge persistence**.

## Key Features

### Agent Memory Backend

- Runs `gbrain serve --http` in a containerized Bun runtime.
- Exposes the MCP-compatible HTTP server on port `3000` by default.
- Persists `./backend/brain` so agent memory survives container restarts and rebuilds.
- Supports runtime connections to host-side Ollama and Qdrant endpoints through Docker environment variables.

### Visual Memory Frontend

- Builds `gbrain-atlas` with Vite and React.
- Serves the static production bundle through Nginx.
- Exposes the UI on host port `8080` by default.
- Gives humans a browser-accessible way to inspect memory structures and operational state.

### VPS-Ready Deployment

- Docker Compose orchestrates the backend and frontend together.
- Host mounts are prepared for `/root/Plumbline` and `/root/obsidian-vault`.
- Restart policy is set to `unless-stopped` for long-running VPS services.
- The install script bootstraps backend and frontend repositories in place.

### Final Gate Validation

- Runs the existing Plumbline CI script.
- Runs backend integration tests for MCP client hardening.
- Searches persistent memory and vault paths for common secret markers before declaring a true-green state.

## Repository Layout

```text
LPAM/
├── Dockerfile.backend     # Bun-based gbrain backend image
├── Dockerfile.frontend    # Bun build + Nginx static frontend image
├── docker-compose.yml     # VPS service orchestration
├── install.sh             # Bootstrap script for backend and frontend clones
├── run_all.sh             # Final gate validation script
└── README.md              # Project documentation
```

After running `install.sh`, the following generated directories are expected:

```text
LPAM/
├── backend/               # cloned from DYAI2025/gbrain
│   └── brain/             # persistent PGLite brain directory
└── frontend/              # cloned from DYAI2025/gbrain-atlas
```

## Architecture

```mermaid
flowchart TD
    Hermes[Hermes or MCP Agent] -->|HTTP MCP requests| Backend[gbrain backend\nBun runtime\nPort 3000]
    Backend -->|persistent memory| Brain[(./backend/brain\nPGLite brain)]
    Backend -->|read-only host context| Plumbline[/root/Plumbline\nmounted read-only]
    Backend -->|Markdown mirror| Vault[/root/obsidian-vault\nObsidian vault]
    Backend -->|optional embeddings / LLM runtime| Ollama[Host Ollama\n172.17.0.1:11434]
    Backend -->|optional vector store| Qdrant[Host Qdrant\n172.17.0.1:6333]
    Frontend[gbrain-atlas frontend\nNginx\nPort 8080] -->|API / visualization| Backend
    Operator[Human operator] -->|browser| Frontend
```

### Backend Container

The backend image is based on `oven/bun:latest`. During build it copies the backend `package.json` and `bun.lock`, installs dependencies with `bun install --frozen-lockfile`, copies the backend source, exposes port `3000`, and starts `gbrain serve --http`.

### Frontend Container

The frontend image uses a two-stage build. The first stage installs and builds the Vite/React app with Bun. The second stage copies the generated `dist` directory into an `nginx:alpine` image and serves it on port `80` inside the container.

### Compose Runtime

`docker-compose.yml` defines two services:

| Service | Host Port | Container Port | Purpose |
|---|---:|---:|---|
| `backend` | `3000` | `3000` | HTTP MCP memory server |
| `frontend` | `8080` | `80` | Browser UI for memory exploration |

The backend service mounts three important paths:

| Host Path | Container Path | Mode | Purpose |
|---|---|---|---|
| `./backend/brain` | `/app/brain` | read/write | persistent brain database |
| `/root/Plumbline` | `/root/Plumbline` | read-only | host-side Plumbline context and watcher input |
| `/root/obsidian-vault` | `/app/vault` | read/write | persistent Markdown vault mirror |

## Prerequisites

### Required

- A Linux VPS or server with shell access.
- Git.
- Docker Engine.
- Docker Compose v2 or compatible `docker-compose`.
- Bun available on the host if you want to run `install.sh` directly outside Docker.
- Network access to clone the backend and frontend repositories.

### Expected VPS Paths

LPAM is opinionated for a root-operated VPS setup. Before starting the stack, make sure these paths exist if you want all mounted integrations to work:

```bash
mkdir -p /root/Plumbline
mkdir -p /root/obsidian-vault
```

If you run as a non-root user, update `docker-compose.yml` to point to your actual Plumbline and vault directories.

### Optional Services

The backend is configured to reach optional host services through Docker bridge addresses:

```text
OLLAMA_HOST=http://172.17.0.1:11434
QDRANT_HOST=http://172.17.0.1:6333
```

Use these when your gbrain backend needs local LLM inference, embeddings, semantic search, or vector storage. If your VPS uses a different Docker network setup, adjust these environment variables.

## Quick Start

### 1. Clone LPAM

```bash
git clone <your-lpam-repository-url> LPAM
cd LPAM
```

### 2. Bootstrap Backend and Frontend

```bash
bash install.sh
```

The installer will:

1. remove any existing `backend` directory;
2. clone `https://github.com/DYAI2025/gbrain.git` into `backend` (the fork — HTTP MCP capable; upstream garrytan/gbrain is stdio-only and won't serve `:3131`);
3. install backend dependencies with Bun;
4. initialize a fresh PGLite brain in `backend/brain`;
5. remove any existing `frontend` directory;
6. clone `https://github.com/DYAI2025/gbrain-atlas.git` into `frontend`.

### 3. Create Required Host Directories

```bash
mkdir -p /root/Plumbline /root/obsidian-vault
```

### 4. Build and Start the Stack

```bash
docker compose up -d --build
```

If your server uses the legacy Compose binary, run:

```bash
docker-compose up -d --build
```

### 5. Verify Services

```bash
docker compose ps
curl http://localhost:3000
curl http://localhost:8080
```

Expected results:

- backend container is running and listening on port `3000`;
- frontend container is running and serving the UI on port `8080`;
- `./backend/brain` exists and remains on disk after restarts;
- `/root/obsidian-vault` is available inside the backend at `/app/vault`.

## Hermes Agent Integration

Hermes or any MCP-capable agent should treat LPAM as its persistent memory endpoint.

### Recommended Agent Configuration

Use the backend HTTP endpoint:

```text
http://<your-vps-hostname-or-ip>:3000
```

For local agents running on the same VPS:

```text
http://localhost:3000
```

For browser-based or remote clients, ensure that firewall rules, reverse proxies, and CORS settings allow the intended origin.

### Expected Agent Behavior

When integrated correctly, an agent such as Hermes can use LPAM to:

- write durable observations, task state, project notes, and operational memory;
- retrieve prior context across independent sessions;
- preserve VPS automation knowledge after process restarts;
- expose memory artifacts to human operators through the frontend;
- mirror selected knowledge into Markdown files for Obsidian-style review;
- combine symbolic memory, local LLM tooling, and optional vector search.

### Production Access Pattern

For production deployments, place a reverse proxy such as Caddy, Nginx, or Traefik in front of the backend and frontend:

```text
https://memory.example.com       -> frontend:8080
https://memory-api.example.com   -> backend:3000
```

Then configure Hermes to use the HTTPS backend URL. Prefer authenticated proxy access instead of exposing the backend directly to the public internet.

## Operations on a VPS

### Start Services

```bash
docker compose up -d
```

### Stop Services

```bash
docker compose down
```

### Rebuild After Updating Backend or Frontend

```bash
docker compose up -d --build
```

### View Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Restart Backend Only

```bash
docker compose restart backend
```

### Backup Persistent Memory

```bash
tar -czf lpam-brain-backup-$(date +%Y%m%d).tar.gz backend/brain /root/obsidian-vault
```

Store backups off the VPS if LPAM is used for production agent memory.

## Validation and Final Gate

Run the final validation gate with:

```bash
bash run_all.sh
```

The script performs three stages:

1. **Plumbline CI** via `/root/Plumbline/config/claude/tests/run_all.sh`.
2. **Integration tests** via `bun test test/mcp-client-hardening.test.ts` inside the backend.
3. **Privacy leak scan** across `/root/obsidian-vault` and `/root/lpam/backend/brain` for common secret markers such as `API_KEY`, `SECRET`, `PASSWORD`, and `TOKEN`.

A successful run ends with:

```text
FINAL GATE: TRUE-GREEN
```

> Note: `run_all.sh` is tailored to a VPS layout that uses `/root/lpam/backend`. If your clone lives at `/workspace/LPAM`, `/opt/lpam`, or another path, update the script or create a matching symlink.

## Security and Privacy

LPAM is designed for powerful long-term agent memory. Treat it as sensitive infrastructure.

### Recommended Hardening

- Do not expose port `3000` directly to the public internet without authentication.
- Restrict backend access with a VPN, firewall, private network, or authenticated reverse proxy.
- Replace permissive CORS (`GBRAIN_HTTP_CORS_ORIGIN=*`) with your production frontend origin.
- Back up `backend/brain` and `/root/obsidian-vault` securely.
- Run the final privacy leak scan before sharing vault exports or memory snapshots.
- Keep `/root/Plumbline` mounted read-only unless write access is explicitly required.
- Rotate secrets immediately if the leak scan reports sensitive values.

### Suggested Firewall Rules

For a private single-host deployment, expose only SSH and HTTPS publicly, then proxy traffic internally:

```bash
ufw allow OpenSSH
ufw allow 443/tcp
ufw enable
```

Keep direct access to `3000` and `8080` limited to trusted networks.

## Configuration Reference

### Backend Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | HTTP server port inside the backend container. |
| `GBRAIN_HTTP_CORS_ORIGIN` | `*` | Allowed CORS origin for browser and agent clients. Replace in production. |
| `OLLAMA_HOST` | `http://172.17.0.1:11434` | Optional host-side Ollama endpoint. |
| `QDRANT_HOST` | `http://172.17.0.1:6333` | Optional host-side Qdrant endpoint. |

### Ports

| Port | Used By | Description |
|---:|---|---|
| `3000` | backend | HTTP MCP server for agents. |
| `8080` | frontend | Web UI served by Nginx. |

## Troubleshooting

### `docker compose up` fails because `backend/package.json` is missing

Run the installer first:

```bash
bash install.sh
```

The Dockerfiles expect `backend/` and `frontend/` to exist.

### Backend cannot connect to Ollama or Qdrant

Check that the services are listening on the VPS host and that the container can reach them:

```bash
curl http://172.17.0.1:11434
curl http://172.17.0.1:6333
```

If Docker uses a different bridge IP, update `OLLAMA_HOST` and `QDRANT_HOST` in `docker-compose.yml`.

### Frontend is reachable but backend calls fail

Check CORS, reverse proxy routing, and whether the frontend is configured to target the correct backend URL. For production, set a specific `GBRAIN_HTTP_CORS_ORIGIN` instead of `*`.

### Memory disappears after rebuilds

Confirm that `./backend/brain` is mounted into `/app/brain` and is not deleted before rebuilding. The `.gitignore` intentionally excludes runtime brain data from Git.

## SEO / GEO Keywords

LPAM is relevant for operators searching for:

- persistent AI agent memory on VPS;
- Hermes agent memory server;
- MCP HTTP memory backend;
- gbrain Docker deployment;
- Obsidian vault agent memory;
- long-term autonomous agent context;
- self-hosted AI automation memory;
- Qdrant and Ollama agent infrastructure;
- VPS agent operations and validation gates;
- production-ready agent memory architecture.

## License

No license file is currently included in this harness repository. Add a license before distributing LPAM publicly or using it in commercial environments.
