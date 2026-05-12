#!/usr/bin/env bash
set -euo pipefail

# Render/Unix entrypoint.
# Ensures dependencies are installed in the same Python interpreter
# before starting uvicorn.

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

echo "[render_start.sh] Using interpreter: $PY_BIN"

# Belt-and-suspenders: ensure deps are installed before starting.
# This avoids cases where the build step didn't install the same env used at runtime.
if [ -f "requirements.txt" ]; then
  echo "[render_start.sh] Installing dependencies from requirements.txt (if needed)..."
  "$PY_BIN" -m pip install --no-cache-dir --break-system-packages -r requirements.txt
else
  echo "[render_start.sh] Warning: requirements.txt not found; skipping install" >&2
fi

# Hard fail early if uvicorn still isn't importable.
"$PY_BIN" -c "import uvicorn; print('uvicorn version:', uvicorn.__version__)" 

echo "[render_start.sh] Starting server on ${API_HOST:-0.0.0.0}:${PORT_TO_USE}"
exec "$PY_BIN" -m uvicorn app:app --host "${API_HOST:-0.0.0.0}" --port "$PORT_TO_USE"

