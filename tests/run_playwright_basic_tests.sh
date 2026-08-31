#!/usr/bin/env bash
# Fast local smoke checks plus desktop/mobile screenshots.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$ROOT_DIR/tests"
VENV_DIR="$TEST_DIR/.venv"
HOST="127.0.0.1"
PORT="4000"
BASE_URL="${BASE_URL:-http://${HOST}:${PORT}}"
SERVER_PID=""

export NO_PROXY="127.0.0.1,localhost${NO_PROXY:+,$NO_PROXY}"
export no_proxy="127.0.0.1,localhost${no_proxy:+,$no_proxy}"

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID"
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

cd "$ROOT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --quiet \
    -r "$TEST_DIR/requirements.txt"
  "$VENV_DIR/bin/python" -m playwright install chromium
fi

# Reuse a healthy local server when one is already running. Otherwise start an
# isolated no-watch Jekyll process and stop only that process when tests finish.
if ! curl --silent --fail --noproxy "*" "$BASE_URL/index.html" >/dev/null; then
  bundle exec jekyll serve \
    --source "$ROOT_DIR" \
    --destination "$ROOT_DIR/_site" \
    --config "$ROOT_DIR/_config.yml" \
    --host "$HOST" \
    --port "$PORT" \
    --no-watch >"$TEST_DIR/jekyll-server.log" 2>&1 &
  SERVER_PID=$!

  for _ in {1..120}; do
    if curl --silent --fail --noproxy "*" "$BASE_URL/index.html" >/dev/null; then
      break
    fi
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
      echo "Jekyll exited before becoming ready:"
      cat "$TEST_DIR/jekyll-server.log"
      exit 1
    fi
    sleep 1
  done
fi

if ! curl --silent --fail --noproxy "*" "$BASE_URL/index.html" >/dev/null; then
  echo "Site is unavailable at $BASE_URL"
  exit 1
fi

echo "Running quick browser checks..."
BASE_URL="$BASE_URL" "$VENV_DIR/bin/python" -m pytest \
  "$TEST_DIR/test_site_basic.py" -q

echo "Refreshing visual snapshots..."
BASE_URL="$BASE_URL" "$VENV_DIR/bin/python" "$TEST_DIR/visual_check.py"

echo "Basic checks and visual snapshots completed successfully."
