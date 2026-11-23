#!/usr/bin/env bash
# Pull latest main, rebuild the image, and restart the container.
# Host ./data (config.env, roles panel, tickets) stays mounted — secrets/state are not wiped.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BRANCH="${UPDATE_BRANCH:-main}"
REMOTE="${UPDATE_REMOTE:-origin}"

if [[ ! -f docker-compose.yml ]]; then
  echo "error: docker-compose.yml not found in $ROOT" >&2
  exit 1
fi

if [[ ! -f data/config/config.env ]]; then
  echo "error: data/config/config.env missing." >&2
  echo "Copy data/config/config-template.env to data/config/config.env and fill in values first." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: $ROOT is not a git repository" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "error: working tree has local changes. Commit, stash, or discard them before updating." >&2
  git status --short >&2
  exit 1
fi

echo "==> Fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

echo "==> Checking out $BRANCH and fast-forwarding"
git checkout "$BRANCH"
git merge --ff-only "$REMOTE/$BRANCH"

echo "==> Rebuilding image and restarting container (./data mount unchanged)"
docker compose up -d --build

echo "==> Done. Current revision: $(git rev-parse --short HEAD)"
docker compose ps
