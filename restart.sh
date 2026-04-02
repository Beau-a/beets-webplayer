#!/usr/bin/env bash
# restart.sh — stop any running beets-webplayer backend and start a fresh one.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
LOG_FILE="/tmp/beets-webplayer.log"

# ── Kill existing instance ────────────────────────────────────────────────────
mapfile -t EXISTING < <(pgrep -f "uvicorn app.main" 2>/dev/null || true)
if [ ${#EXISTING[@]} -gt 0 ]; then
  echo "Stopping existing backend (PID ${EXISTING[*]})…"
  kill "${EXISTING[@]}" 2>/dev/null || true
  # Wait up to 5 s for all to exit
  for i in $(seq 1 10); do
    sleep 0.5
    STILL_ALIVE=()
    for pid in "${EXISTING[@]}"; do
      kill -0 "$pid" 2>/dev/null && STILL_ALIVE+=("$pid")
    done
    [ ${#STILL_ALIVE[@]} -eq 0 ] && break
  done
  # Force-kill any stragglers
  for pid in "${STILL_ALIVE[@]:-}"; do
    kill -9 "$pid" 2>/dev/null || true
  done
fi

# ── Rebuild frontend ─────────────────────────────────────────────────────────
FRONTEND_DIR="$SCRIPT_DIR/frontend"
if [ -f "$FRONTEND_DIR/package.json" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Building frontend…"
  cd "$FRONTEND_DIR"
  npm run build --silent
  echo "Frontend built."
else
  echo "Skipping frontend build (node_modules not found — run install.sh first)."
fi

# ── Activate venv ─────────────────────────────────────────────────────────────
VENV="$BACKEND_DIR/venv"
if [ ! -f "$VENV/bin/activate" ]; then
  echo "ERROR: virtualenv not found at $VENV. Run install.sh first." >&2
  exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# ── Read port from .env (default 5000) ───────────────────────────────────────
ENV_FILE="$BACKEND_DIR/.env"
PORT=5000
if [ -f "$ENV_FILE" ]; then
  PORT_LINE=$(grep -E '^PORT=' "$ENV_FILE" 2>/dev/null || true)
  [ -n "$PORT_LINE" ] && PORT="${PORT_LINE#PORT=}"
fi

# ── Start backend ─────────────────────────────────────────────────────────────
echo "Starting backend on port $PORT (log → $LOG_FILE)…"
cd "$BACKEND_DIR"
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "PID: $NEW_PID"

# ── Wait for it to be ready ───────────────────────────────────────────────────
echo -n "Waiting for startup"
for i in $(seq 1 20); do
  sleep 0.5
  if curl -sf "http://localhost:$PORT/api/albums?page_size=1" > /dev/null 2>&1; then
    echo " ready."
    echo "Backend running at http://localhost:$PORT"
    exit 0
  fi
  echo -n "."
done

echo ""
echo "WARNING: backend did not respond after 10 s. Check $LOG_FILE for errors."
exit 1
