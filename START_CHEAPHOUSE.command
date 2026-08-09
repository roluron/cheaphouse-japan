#!/bin/zsh
set -e

PROJECT_DIR="${0:A:h}"
WEB_DIR="$PROJECT_DIR/web"
CHEAPHOUSE_PORT="${PORT:-3000}"
CHEAPHOUSE_URL="http://localhost:$CHEAPHOUSE_PORT"

cd "$WEB_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js is required. Install it from https://nodejs.org and double-click this file again."
  read -r "?Press Return to close."
  exit 1
fi

if [[ ! -d node_modules ]]; then
  echo "Preparing CheapHouse for the first launch..."
  npm install
fi

(
  for attempt in {1..60}; do
    if curl --silent --fail "$CHEAPHOUSE_URL" >/dev/null 2>&1; then
      open "$CHEAPHOUSE_URL"
      exit 0
    fi
    sleep 1
  done
) &

echo "CheapHouse is starting at $CHEAPHOUSE_URL"
echo "Keep this window open. Press Control-C to stop."
npm run dev -- --port "$CHEAPHOUSE_PORT"

