#!/usr/bin/env bash
set -euo pipefail

# --- config: change these for each challenge ---
SRC="dummy_agent.c"                     # source file in this source/ dir
OUTNAME="dummy_agent_linux_x86_64"   # output binary name placed in ../artifacts
# ------------------------------------------------

# Resolve paths relative to this script so it works when run from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # this is .../challengeX/source
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"                  # parent: challengeX/
OUTDIR="$REPO_ROOT/artifacts"

mkdir -p "$OUTDIR"

# Build inside an amd64 gcc container so the produced binary is linux x86_64 ELF.
# We mount the REPO_ROOT (parent of source/) as /work so ../artifacts on host
# is accessible at /work/artifacts inside the container.
docker run --rm --platform linux/amd64 \
  -v "$REPO_ROOT":/work -w /work/source gcc:12 \
  bash -lc "gcc -O0 -fno-stack-protector -g $SRC -o /work/artifacts/$OUTNAME && chmod +x /work/artifacts/$OUTNAME"

echo "Built $OUTDIR/$OUTNAME"
file "$OUTDIR/$OUTNAME"
ls -l "$OUTDIR/$OUTNAME"
sha256sum "$OUTDIR/$OUTNAME" || true
