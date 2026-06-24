#!/usr/bin/env bash
set -e

echo "🔧 LPAM Bootstrap: Installing dependencies and initializing empty brain..."

# Backend: gbrain core engine
echo "📦 Cloning gbrain core engine..."
rm -rf backend
git clone https://github.com/DYAI2025/gbrain.git backend
cd backend
bun install
echo "🧠 Initializing PGLite brain (empty, content-agnostic)..."
gbrain init --pglite --path ./brain
cd ..

# Frontend: gbrain-atlas
echo "📦 Cloning gbrain-atlas frontend..."
rm -rf frontend
git clone https://github.com/DYAI2025/gbrain-atlas.git frontend

echo "✅ LPAM bootstrap complete."
echo "To start the stack: docker compose up -d"
