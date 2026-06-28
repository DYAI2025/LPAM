# LPAM (Local Plumbline Agent Machinery)

This repository serves as a bootstrap harness for the Hermes-Plumbline MVP.
It currently contains:
- Dockerfiles and docker-compose.yml for backend and frontend services
- An install script to bootstrap the gbrain and gbrain-atlas repositories (optional)
- Empty backend/ and frontend/ directories (to be populated by bootstrap or by adding source code)

## Current State

This snapshot is a **bootstrap harness** and does **not** contain the backend or frontend source code.
To run the services, you must either:
1. Use the bootstrap option to clone the gbrain and gbrain-atlas repositories, or
2. Provide your own backend and frontend source code in the respective directories.

## Validation

Once the backend and frontend source are present, you can validate the Plumbline MVP by running the validation commands documented in `docs/plans/2026-06-25-lpam-hermes-plumbline-mvp.md`.

## Installation

To bootstrap the gbrain and gbrain-atlas repositories (which contain the backend and frontend source):

```bash
./install.sh --bootstrap
```

To perform a dry-run (see what would be done without making changes):

```bash
./install.sh --dry-run
```

To force removal of existing backend and frontend directories (use with caution):

```bash
./install.sh --force
```

## Notes

- The bootstrap option is optional for the Plumbline MVP; you can also manually place the backend and frontend source in the respective directories.
- The install script includes safety checks to prevent accidental deletion of non-empty directories unless `--force` is specified.