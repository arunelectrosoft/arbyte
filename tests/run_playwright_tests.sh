#!/usr/bin/env bash
# Run the Playwright test suite in CLI (default) or GUI mode.
#
# CLI mode (default):
#   ./tests/run_playwright_tests.sh [PAGE_SELECTION]
#   PAGE_SELECTION is "all" (default) or a comma-separated list of page
#   names defined in tests/test_config.py, e.g. "home,contact".
#
# GUI mode:
#   ./tests/run_playwright_tests.sh --gui
#   Opens a checkbox dialog (tests/gui_page_selector.py) to pick pages.
#
# The site under test, its pages, base URL, and authentication are all
# defined in tests/test_config.py, so this script can be reused for
# other sites by editing that config file only.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$ROOT_DIR/tests"
VENV_DIR="$TEST_DIR/.venv"
HOST="127.0.0.1"
PORT="4000"
BASE_URL="http://${HOST}:${PORT}"
SERVER_PID=""
MODE="cli"
PAGE_SELECTION="all"

# Corporate proxy settings must never intercept requests to the local test
# server. Preserve any existing exclusions while adding both local hostnames.
export NO_PROXY="127.0.0.1,localhost${NO_PROXY:+,$NO_PROXY}"
export no_proxy="127.0.0.1,localhost${no_proxy:+,$no_proxy}"

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID"
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

show_usage() {
  cat <<'USAGE'
Usage: run_playwright_tests.sh [--gui] [PAGE_SELECTION]

  PAGE_SELECTION   "all" (default) or a comma-separated list of page
                   names from tests/test_config.py (e.g. "home,contact")
  --gui            Open a checkbox dialog to choose pages instead of
                   passing PAGE_SELECTION on the command line
  -h, --help       Show this help
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --gui)
      MODE="gui"
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    *)
      PAGE_SELECTION="$arg"
      ;;
  esac
done

cd "$ROOT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --quiet -r "$TEST_DIR/requirements.txt"
"$VENV_DIR/bin/python" -m playwright install chromium

if [[ "$MODE" == "gui" ]]; then
  if ! PAGE_SELECTION="$(cd "$TEST_DIR" && "$VENV_DIR/bin/python" gui_page_selector.py)"; then
    echo "No pages selected. Aborting."
    exit 1
  fi
  echo "Selected pages: $PAGE_SELECTION"
fi

# Explicit paths keep Jekyll anchored at the repository root even when this
# script is invoked from tests/. --no-watch also prevents Listen from scanning
# tests/.venv, whose lib and lib64 entries resolve to the same directory.
bundle exec jekyll serve \
  --source "$ROOT_DIR" \
  --destination "$ROOT_DIR/_site" \
  --config "$ROOT_DIR/_config.yml" \
  --host "$HOST" \
  --port "$PORT" \
  --no-watch > "$TEST_DIR/jekyll-server.log" 2>&1 &
SERVER_PID=$!

# First-run generation can take well over 30s on slower/networked
# filesystems (e.g. a Windows drive mounted into WSL), so allow up to two
# minutes before giving up.
for _ in {1..120}; do
  if curl --silent --fail --noproxy "*" "$BASE_URL/index.html" > /dev/null; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Jekyll server exited before becoming ready:"
    cat "$TEST_DIR/jekyll-server.log"
    exit 1
  fi
  sleep 1
done

if ! curl --silent --fail --noproxy "*" "$BASE_URL/index.html" > /dev/null; then
  echo "Jekyll server did not start. See $TEST_DIR/jekyll-server.log"
  exit 1
fi

BASE_URL="$BASE_URL" PAGE_SELECTION="$PAGE_SELECTION" \
  "$VENV_DIR/bin/python" -m pytest "$TEST_DIR/test_site_pages.py" -v
