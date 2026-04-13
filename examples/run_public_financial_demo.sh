#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$ROOT_DIR/.tools"
LOG_DIR="$ROOT_DIR/.demo-logs"
mkdir -p "$TOOLS_DIR" "$LOG_DIR"

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64)
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    ;;
  aarch64|arm64)
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    ;;
  *)
    echo "Unsupported architecture for cloudflared quick tunnel: $ARCH" >&2
    exit 1
    ;;
esac

CLOUDFLARED_BIN="$TOOLS_DIR/cloudflared"
if [[ ! -x "$CLOUDFLARED_BIN" ]]; then
  echo "Downloading cloudflared to $CLOUDFLARED_BIN"
  curl -fsSL "$CLOUDFLARED_URL" -o "$CLOUDFLARED_BIN"
  chmod +x "$CLOUDFLARED_BIN"
fi

APP_LOG="$LOG_DIR/webapp.log"
TUNNEL_LOG="$LOG_DIR/cloudflared.log"

cleanup() {
  if [[ -n "${TUNNEL_PID:-}" ]]; then
    kill "$TUNNEL_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${APP_PID:-}" ]]; then
    kill "$APP_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

export WEBAPP_DEMO_MODE=1
unset ALPHAVANTAGE_API_KEY
unset ALPHA_VANTAGE_API_KEY
unset FRED_API_KEY
unset LLM_MODEL_ID
unset LLM_API_KEY
unset LLM_BASE_URL

cd "$ROOT_DIR"
PYTHONPATH=src python3.10 -m cave_agent.webapp >"$APP_LOG" 2>&1 &
APP_PID=$!

for _ in {1..40}; do
  if curl -fsS http://127.0.0.1:8000/ >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -fsS http://127.0.0.1:8000/ >/dev/null 2>&1; then
  echo "Web app failed to start. Check $APP_LOG" >&2
  exit 1
fi

echo "Starting Cloudflare quick tunnel"
"$CLOUDFLARED_BIN" tunnel --url http://127.0.0.1:8000 --protocol http2 --no-autoupdate >"$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

PUBLIC_URL=""
for _ in {1..60}; do
  if [[ -f "$TUNNEL_LOG" ]]; then
    PUBLIC_URL="$(grep -Eo 'https://[-a-z0-9]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -n 1 || true)"
    if [[ -n "$PUBLIC_URL" ]]; then
      break
    fi
  fi
  sleep 1
done

if [[ -z "$PUBLIC_URL" ]]; then
  echo "Failed to obtain a public URL. Check $TUNNEL_LOG" >&2
  exit 1
fi

cat <<EOF

Public demo URL:
  $PUBLIC_URL

Local logs:
  app     -> $APP_LOG
  tunnel  -> $TUNNEL_LOG

Notes:
  - This is a temporary Cloudflare quick tunnel.
  - Keep this shell running to keep the public URL alive.
  - The UI now falls back to polling if SSE is unavailable over the tunnel.

EOF

wait "$TUNNEL_PID"
