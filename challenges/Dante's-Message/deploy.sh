#!/bin/bash
set -e

echo "Stopping old container if exists..."
sudo podman stop dante-message 2>/dev/null || true
sudo podman rm dante-message 2>/dev/null || true

echo "Building image..."
sudo podman build -t dante-message:latest -f docker/Dockerfile docker/

echo "Starting container..."
sudo podman run -d --name dante-message --restart=always -p 0.0.0.0:9205:9205 dante-message:latest

echo "Waiting for container to start..."
sleep 3

echo "Container status:"
sudo podman ps | grep dante-message

echo "Testing connection..."
printf "test\n" | nc localhost 9205 2>&1 | head -3 || echo "Connection test failed"

echo "✅ Deployment complete!"

