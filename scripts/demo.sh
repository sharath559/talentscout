#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run talent_scout --offline --metrics
uv run python scripts/evaluate.py
