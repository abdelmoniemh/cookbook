#!/usr/bin/env bash
# Pull the latest code, sync Python deps, rebuild the UI and restart the service.
set -euo pipefail
cd "$(dirname "$0")/.."

git pull --ff-only
uv sync --frozen
if [ -f web/package.json ]; then
    (cd web && npm ci && npm run build)
fi
systemctl --user restart cookbook
sleep 2
systemctl --user --no-pager --lines=0 status cookbook
curl -fsS http://127.0.0.1:8000/api/health && echo
