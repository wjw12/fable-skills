#!/usr/bin/env bash
# Run image.py, loading OPENAI_API_KEY from ./.env when it exists.
set -euo pipefail
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
uv run --with openai python "$(dirname "$0")/image.py" "$@"
