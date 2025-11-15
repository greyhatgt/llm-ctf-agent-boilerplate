#!/bin/bash
set -e

echo "Stopping old container if exists..."
sudo podman stop dadbeef-bomb 2>/dev/null || true
sudo podman rm dadbeef-bomb 2>/dev/null || true

echo "Building image..."
sudo podman build -t dadbeef-bomb:latest -f docker/Dockerfile docker/

echo "Starting container..."
sudo podman run -d --name dadbeef-bomb --restart=always -p 0.0.0.0:9225:9225 dadbeef-bomb:latest

echo "Waiting for container to start..."
sleep 3

echo "Container status:"
sudo podman ps | grep dadbeef-bomb

echo "Testing connection..."
printf "test\n" | nc localhost 9225 2>&1 | head -3 || echo "Connection test failed"

echo "✅ Deployment complete!"

