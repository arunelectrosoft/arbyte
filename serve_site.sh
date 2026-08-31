#!/usr/bin/env bash
# Build and serve the Jekyll site reliably from any working directory.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${JEKYLL_HOST:-127.0.0.1}"
PORT="${JEKYLL_PORT:-4000}"

cd "$ROOT_DIR"

bundle exec jekyll clean \
  --source "$ROOT_DIR" \
  --destination "$ROOT_DIR/_site" \
  --config "$ROOT_DIR/_config.yml"

# Watching is deliberately disabled on /mnt/* WSL filesystems. It is slow and
# may follow tests/.venv/lib and tests/.venv/lib64 to the same directory,
# causing Listen's "directory is already being watched" fatal error.
exec bundle exec jekyll serve \
  --source "$ROOT_DIR" \
  --destination "$ROOT_DIR/_site" \
  --config "$ROOT_DIR/_config.yml" \
  --host "$HOST" \
  --port "$PORT" \
  --baseurl "" \
  --no-watch
