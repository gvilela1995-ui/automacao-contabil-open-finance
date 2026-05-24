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
  apt-get install -y docker.io docker-compose-plugin
  systemctl enable --now docker
fi

if [ ! -d "$APP_DIR/.git" ]; then
  mkdir -p "$(dirname "$APP_DIR")"
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

cd "$APP_DIR"
docker compose up -d --build

echo "Sistema publicado em: http://31.97.86.86:8877"
