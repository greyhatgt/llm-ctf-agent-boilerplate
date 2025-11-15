#!/bin/bash
set -e

echo "Stopping old container if exists..."
sudo podman stop blackp1nk-circuitsat 2>/dev/null || true
sudo podman rm blackp1nk-circuitsat 2>/dev/null || true

echo "Building image..."
sudo podman build -t blackp1nk-circuitsat:latest -f docker/Dockerfile .

echo "Starting container..."
sudo podman run -d --name blackp1nk-circuitsat --restart=always -p 0.0.0.0:9218:9218 blackp1nk-circuitsat:latest

echo "Waiting for container to start..."
sleep 3

echo "Container status:"
sudo podman ps | grep blackp1nk-circuitsat

echo "Testing connection..."
printf "test\n" | nc localhost 9218 2>&1 | head -3 || echo "Connection test failed"

echo "✅ Deployment complete!"

