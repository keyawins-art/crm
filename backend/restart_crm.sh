#!/bin/bash
echo "📦 Building Frontend..."
cd ~/crm/frontend || { echo "❌ Frontend directory not found!"; exit 1; }
npm run build

echo "🔄 Restarting CRM Services (Backend, Nginx, Ngrok)..."

sudo systemctl restart crm-backend.service
sudo systemctl restart nginx.service
sudo systemctl restart crm-ngrok.service

echo "✅ Services Restarted Successfully!"
echo "------------------------------------------------"
echo "🌐 Your CRM is running at your Fixed Ngrok URL:"
echo "https://plank-rubber-abiding.ngrok-free.dev"
echo "------------------------------------------------"
