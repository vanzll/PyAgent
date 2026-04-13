#!/usr/bin/env bash
set -euo pipefail

export WEBAPP_DEMO_MODE=1
unset ALPHAVANTAGE_API_KEY
unset ALPHA_VANTAGE_API_KEY
unset FRED_API_KEY
unset LLM_MODEL_ID
unset LLM_API_KEY
unset LLM_BASE_URL

echo "Starting CaveAgent Financial Research Agent in deterministic demo mode..."
echo "Open http://localhost:8000"

cave-agent-webapp
