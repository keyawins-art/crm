#!/bin/bash

echo "Starting CRM Backend..."
cd backend
# Using nohup to keep it running after closing SSH
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
cd ..

echo "Starting CRM Frontend..."
cd frontend
# --host 0.0.0.0 is required to access the frontend from outside the server
nohup npm run dev -- --host 0.0.0.0 > frontend.log 2>&1 &
cd ..

echo "Both servers are running in the background!"
echo "Backend logs: tail -f backend/backend.log"
echo "Frontend logs: tail -f frontend/frontend.log"
