#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if command -v python3.12 >/dev/null; then PY_BIN=python3.12; else PY_BIN=python3; fi
exec "$PY_BIN" app.py
