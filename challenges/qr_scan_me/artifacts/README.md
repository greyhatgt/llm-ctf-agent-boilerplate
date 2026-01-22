QR Scan Me — Artifacts
======================

This challenge provides a QR code PNG containing the flag. Use any QR scanner (phone camera, `zbarimg`, etc.) to read `qr_flag.png` once built.

Hints
- If scanning the screen is inconvenient, right‑click the QR and save as an image, then scan the saved file with a local tool.
- Popular CLI tools: `zbarimg`, `zxing`, or Python with `pyzbar`.

Building the artifact
- From this challenge directory, run `source/build.sh` (requires Docker). The script generates `artifacts/qr_flag.png`.
