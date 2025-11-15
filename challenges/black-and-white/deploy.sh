#!/bin/bash
set -e

echo "Stopping old container if exists..."
sudo podman stop black-and-white 2>/dev/null || true
sudo podman rm black-and-white 2>/dev/null || true

echo "Building image..."
sudo podman build -t black-and-white:latest -f docker/Dockerfile docker/

echo "Starting container..."
sudo podman run -d --name black-and-white --restart=always -p 0.0.0.0:9215:9215 black-and-white:latest

echo "Waiting for container to start..."
sleep 3

echo "Container status:"
sudo podman ps | grep black-and-white

echo "Testing connection..."
printf "test\n" | nc localhost 9215 2>&1 | head -3 || echo "Connection test failed"

echo "✅ Deployment complete!"

