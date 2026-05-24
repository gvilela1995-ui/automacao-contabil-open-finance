#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gabriel-automacao-contabil-open-finance}"
REPO_URL="${REPO_URL:-}"

if [ -z "$REPO_URL" ]; then
  echo "Defina REPO_URL com o link do seu GitHub."
  echo "Exemplo: REPO_URL=https://github.com/seu-usuario/seu-repo.git bash deploy_hostinger.sh"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  apt-get update
  apt-get install -y git
fi

if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y docker.io
  systemctl enable --now docker
fi

if [ ! -d "$APP_DIR/.git" ]; then
  mkdir -p "$(dirname "$APP_DIR")"
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

cd "$APP_DIR"
docker build -t automacao-contabil-open-finance:latest .
docker rm -f automacao-contabil >/dev/null 2>&1 || true
docker run -d \
  --name automacao-contabil \
  --restart unless-stopped \
  -p 8877:8765 \
  -v "$APP_DIR/data:/app/data" \
  -v "$APP_DIR/config:/app/config" \
  -v "$APP_DIR/logs:/app/logs" \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8765 \
  automacao-contabil-open-finance:latest

echo "Sistema publicado em: http://31.97.86.86:8877"
