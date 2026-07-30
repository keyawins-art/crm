#!/usr/bin/env bash
# Deploy the Ollama-backed CRM Copilot on the existing Ubuntu CRM server.
set -euo pipefail

CRM_DIR="${CRM_DIR:-$HOME/crm}"
cd "$CRM_DIR"

echo "Updating backend dependencies…"
"$CRM_DIR/backend/venv/bin/pip" install -r "$CRM_DIR/backend/requirements.txt"

echo "Building frontend…"
cd "$CRM_DIR/frontend"
npm run build

echo "Installing CRM Nginx config…"
sudo install -m 0644 "$CRM_DIR/nginx_crm.conf" /etc/nginx/sites-available/crm
sudo ln -sfn /etc/nginx/sites-available/crm /etc/nginx/sites-enabled/crm
sudo nginx -t

echo "Restarting CRM services…"
sudo systemctl restart crm-backend.service nginx.service crm-ngrok.service

echo "Checking API and Ollama model…"
curl --fail --silent http://127.0.0.1:8001/ >/dev/null
ollama list | grep -F "${OLLAMA_MODEL:-qwen3:4b}" >/dev/null
echo "CRM Copilot deployment completed."
