#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command python3
require_command node
require_command npm

if [[ ! -f "$ROOT_DIR/backend/.env" ]]; then
  cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
fi

if [[ ! -f "$ROOT_DIR/frontend/.env" ]]; then
  cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"
fi

python3 -m venv "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$ROOT_DIR/.venv/bin/pip" install -r "$ROOT_DIR/requirements.txt"

(
  cd "$ROOT_DIR/frontend"
  npm install
)

echo "Setup complete."
