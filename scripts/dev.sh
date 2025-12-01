#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python3 scripts/which_python.py >/dev/null 2>&1 || true
python3 app.py &
BACKEND_PID=$!
for i in {1..30}; do
  if curl -sSf http://127.0.0.1:5000/api/v1/health >/dev/null 2>&1; then break; fi
  sleep 1
done
if command -v osascript >/dev/null 2>&1; then
  osascript -e 'tell application "Terminal" to do script "cd '"$ROOT_DIR"'/frontend; npm run build; npm run dev"'
else
  (cd "$ROOT_DIR/frontend" && npm run build && npm run dev)
fi
wait $BACKEND_PID
