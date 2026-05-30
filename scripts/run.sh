#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  echo "Missing .venv. Run scripts/setup.sh first." >&2
  exit 1
fi

if [[ ! -f "$ROOT_DIR/backend/.env" ]]; then
  cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
fi

if [[ ! -f "$ROOT_DIR/frontend/.env" ]]; then
  cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"
fi

set -a
# shellcheck disable=SC1091
source "$ROOT_DIR/backend/.env"
# shellcheck disable=SC1091
source "$ROOT_DIR/frontend/.env"
set +a

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_HOST="${FRONTEND_HOST:-${VITE_DEV_HOST:-127.0.0.1}}"
FRONTEND_PORT="${FRONTEND_PORT:-${VITE_DEV_PORT:-5173}}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

(
  cd "$ROOT_DIR"
  "$ROOT_DIR/.venv/bin/python" -m uvicorn backend.app.main:app \
    --reload \
    --host "$BACKEND_HOST" \
    --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

(
  cd "$ROOT_DIR/frontend"
  npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo "Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"

wait -n "$BACKEND_PID" "$FRONTEND_PID"
