#!/usr/bin/env bash
set -euo pipefail

# Render/Unix entrypoint.
# Uses python3 if available, otherwise falls back to python.

PY_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
else
  echo "Error: python3/python not found in PATH" >&2
  exit 127
fi

# Use Render's standard $PORT if provided
PORT_TO_USE="${PORT:-${API_PORT:-8000}}"
exec "$PY_BIN" -m uvicorn app:app --host "${API_HOST:-0.0.0.0}" --port "$PORT_TO_USE"

