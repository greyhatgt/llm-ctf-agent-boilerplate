#!/bin/bash
set -e

echo "Stopping old container if exists..."
sudo podman stop averagejoes-badauth 2>/dev/null || true
sudo podman rm averagejoes-badauth 2>/dev/null || true

echo "Building image..."
sudo podman build -t averagejoes-badauth:latest -f docker/Dockerfile docker/

echo "Starting container..."
sudo podman run -d --name averagejoes-badauth --restart=always -p 0.0.0.0:9214:9214 averagejoes-badauth:latest

echo "Waiting for container to start..."
sleep 3

echo "Container status:"
sudo podman ps | grep averagejoes-badauth

echo "Testing connection..."
printf "test\n" | nc localhost 9214 2>&1 | head -3 || echo "Connection test failed"

echo "✅ Deployment complete!"

