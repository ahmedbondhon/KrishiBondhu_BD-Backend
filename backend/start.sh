#!/usr/bin/env bash
# start.sh — Render.com production start script for KrishiBondhu Backend
# Uses `python -m uvicorn` to avoid PATH issues with status 127 on Linux

set -e

PORT="${PORT:-10000}"

echo "🌾 Starting KrishiBondhu Backend on port $PORT ..."

exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 2 \
    --log-level info
