#!/bin/bash
set -euo pipefail

DRY_RUN=false
FORCE=false
BOOTSTRAP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --bootstrap)
            BOOTSTRAP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# Function to simulate or run a command
run() {
    if $DRY_RUN; then
        echo "[DRY-RUN] $*"
    else
        "$@"
    fi
}

# Check if directories exist and are non-empty (unless --force)
if [[ ! $FORCE = true ]]; then
    for dir in "$BACKEND_DIR" "$FRONTEND_DIR"; do
        if [[ -d "$dir" && -n "$(ls -A "$dir")" ]]; then
            echo "Error: $dir exists and is not empty. Use --force to remove."
            exit 1
        fi
    done
fi

if $DRY_RUN; then
    echo "Dry run: would remove $BACKEND_DIR and $FRONTEND_DIR if they exist and are non-empty."
    if $BOOTSTRAP; then
        echo "Dry run: would then clone gbrain and gbrain-atlas repositories."
    fi
    exit 0
fi

# Remove directories if they exist
for dir in "$BACKEND_DIR" "$FRONTEND_DIR"; do
    if [[ -d "$dir" ]]; then
        run rm -rf "$dir"
        echo "Removed $dir"
    fi
done

if $BOOTSTRAP; then
    # Clone gbrain and gbrain-atlas
    run git clone https://github.com/DYAI2025/gbrain.git "$BACKEND_DIR"
    run git clone https://github.com/DYAI2025/gbrain-atlas.git "$FRONTEND_DIR"
    echo "Bootstrapped gbrain and gbrain-atlas."
fi