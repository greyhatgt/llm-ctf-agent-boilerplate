#!/usr/bin/env bash
set -euo pipefail

# --- config for this challenge ---
OUTNAME="qr_flag.png"                 # output image name in ../artifacts
FLAG_TEXT="flag{qr_scan_readable_OMcDMGWDaZ}"  # must match challenge.json
# ----------------------------------

# Resolve paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACTS_DIR="$CHAL_ROOT/artifacts"

mkdir -p "$ARTIFACTS_DIR"

# ROT10 the flag before encoding into the QR image
# example: A->K, B->L ... Q->A, R->B, etc. (case-preserving)
rot10() {
  # shellcheck disable=SC2018,SC2019
  tr 'A-Za-z' 'K-ZA-Jk-za-j'
}

QR_TEXT=$(printf "%s" "$FLAG_TEXT" | rot10)

qrencode -o "${ARTIFACTS_DIR}/${OUTNAME}" -s 10 -m 2 -l M "$QR_TEXT"

echo "Created $ARTIFACTS_DIR/$OUTNAME (contents are ROT10 of the flag)"
