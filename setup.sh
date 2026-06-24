#!/bin/bash
set -e

echo "Setting up Harness for gbrain framework..."

# Backend: clone gbrain core engine
echo "Setting up backend..."
rm -rf backend
git clone https://github.com/DYAI2025/gbrain.git backend
cd backend
# Install dependencies
bun install
# Initialize a fresh brain (PGLite) inside the backend directory
echo "Initializing brain (PGLite) in ./brain..."
gbrain init --pglite --path ./brain
cd ..

# Frontend: clone gbrain-atlas
echo "Setting up frontend..."
rm -rf frontend
git clone https://github.com/DYAI2025/gbrain-atlas.git frontend
echo "Setup complete."
