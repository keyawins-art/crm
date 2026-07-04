#!/bin/bash
echo "🔄 Restarting CRM Services (Backend, Nginx, Pinggy)..."

sudo systemctl restart crm-backend.service
sudo systemctl restart nginx.service
sudo systemctl restart pinggy.service

echo "✅ Services Restarted Successfully!"
echo "⏳ Waiting for new Pinggy URL..."
sleep 4

echo "------------------------------------------------"
echo "🌐 Your new Pinggy URLs:"
sudo journalctl -u pinggy.service -n 20 | grep -o 'http[s]*://[^ ]*pinggy[^ ]*' | tail -n 2
echo "------------------------------------------------"
