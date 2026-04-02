#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "============================================================"
echo "  Word2LaTeX Converter | Linux/macOS Launcher"
echo "============================================================"

echo "[1/5] Freeing ports 3000, 5173, 8000..."
for port in 8000 5173 3000; do
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"$port" || true)"
    if [[ -n "$pids" ]]; then
      echo "      - Killing PID(s) on port $port: $pids"
      kill -9 $pids || true
    fi
  fi
done

echo "[2/5] Cleaning __pycache__..."
find "$ROOT_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} + >/dev/null 2>&1 || true

echo "[3/5] Preparing Python environment..."
if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  python3 -m venv "$ROOT_DIR/.venv"
fi
source "$ROOT_DIR/.venv/bin/activate"
pip install -r "$ROOT_DIR/backend/requirements.txt" --disable-pip-version-check -q

echo "[4/5] Starting backend :8000 ..."
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > "$ROOT_DIR/outputs/backend.log" 2>&1 &
BACKEND_PID=$!

echo "[5/5] Starting frontend :5173 ..."
cd "$ROOT_DIR/frontend"
if [[ ! -d node_modules ]]; then
  npm install --prefer-offline
fi
npm run dev > "$ROOT_DIR/outputs/frontend.log" 2>&1 &
FRONTEND_PID=$!

cd "$ROOT_DIR"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "App URL: http://localhost:5173"
echo "Logs: outputs/backend.log and outputs/frontend.log"
echo "Press Ctrl+C to stop both services."

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
wait
