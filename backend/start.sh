#!/usr/bin/env bash
# start.sh — Production start script for KrishiBondhu Backend + AI Service
# Runs both AI Service on 0.0.0.0:8001 and Main Backend on 0.0.0.0:$PORT

set -e

PORT="${PORT:-10000}"

# 1. Start AI Service on 0.0.0.0:8001 in background (if not already started)
AI_DIR=""
if [ -d "./ai-service" ]; then
    AI_DIR="./ai-service"
elif [ -d "../ai-service" ]; then
    AI_DIR="../ai-service"
fi

if [ -n "$AI_DIR" ]; then
    echo "🤖 Starting AI Service on 0.0.0.0:8001 in background..."
    PYTHONPATH="$AI_DIR" python -m uvicorn app.main:app --app-dir "$AI_DIR" --host 0.0.0.0 --port 8001 &
    sleep 2
fi

# 2. Start Main KrishiBondhu Backend on 0.0.0.0:$PORT
echo "🌾 Starting Main KrishiBondhu Backend on 0.0.0.0:$PORT ..."
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 2 \
    --log-level info
