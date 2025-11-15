#!/bin/bash
set -e

echo "Stopping old container if exists..."
sudo podman stop 0xoperation-mask 2>/dev/null || true
sudo podman rm 0xoperation-mask 2>/dev/null || true

echo "Building image..."
sudo podman build -t 0xoperation-mask:latest -f docker/Dockerfile docker/

echo "Starting container..."
sudo podman run -d --name 0xoperation-mask --restart=always -p 0.0.0.0:9217:9217 0xoperation-mask:latest

echo "Waiting for container to start..."
sleep 3

echo "Container status:"
sudo podman ps | grep 0xoperation-mask

echo "Testing connection..."
printf "test\n" | nc localhost 9217 2>&1 | head -3 || echo "Connection test failed"

echo "✅ Deployment complete!"

