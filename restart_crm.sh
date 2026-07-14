#!/bin/bash

echo "Stopping existing CRM Backend and Frontend..."

# Stop the backend (uvicorn)
echo "Killing backend..."
pkill -f "uvicorn app.main:app" || echo "Backend was not running."

# Stop the frontend (vite)
echo "Killing frontend..."
pkill -f "vite" || echo "Frontend was not running."

# Wait a moment to ensure ports are freed
echo "Waiting for processes to close..."
sleep 2

# Start the CRM using the existing start script
if [ -f "./start.sh" ]; then
    echo "Restarting CRM..."
    chmod +x start.sh
    ./start.sh
else
    echo "Error: ./start.sh not found. Please run this from the CRM root directory."
    exit 1
fi
