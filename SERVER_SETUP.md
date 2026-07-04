# CRM Server Deployment & Operations Guide

This document provides complete details on how your CRM project is hosted on the Ubuntu Server (`192.168.1.16`), how to update it, and how to troubleshoot any issues in the future.

---

## 1. Architecture Overview

Your project is divided into three main components, and everything is served through a single Pinggy link on **Port 3000**.

*   **Frontend (React/Vite):** After the build process, the static files are served by **Nginx** (on Port 3000).
*   **Backend (FastAPI/Python):** Runs on a `uvicorn` server on **Port 8001**. Nginx automatically forwards (proxies) any `/crm`, `/auth`, or `/dashboard` API requests to Port 8001.
*   **Database:** PostgreSQL server is running locally on port `5432`.
*   **Pinggy Tunnel:** Uses `autossh` to establish a secure tunnel that exposes Port 3000 to the public internet (via a Pinggy URL).

---

## 2. How to Pull New Code & Update the Server

Whenever you modify code on your local system (`D:\CRM`) and push it to GitHub, follow these steps to apply the changes to the server:

**Step 1:** Log into the server
```bash
ssh keya@192.168.1.16
```

**Step 2:** Pull the latest code
```bash
cd ~/crm
git pull
```

**Step 3:** If there are changes in the **Frontend**, rebuild it
```bash
cd ~/crm/frontend
npm run build
```

**Step 4:** If you added dependencies to the **Backend** (Python), install them
```bash
cd ~/crm/backend
source venv/bin/activate
pip install -r requirements.txt
```

**Step 5:** Restart the services (to apply the new code)
```bash
cd ~
./restart_crm.sh
```

---

## 3. How Server Auto-Restart Works

We have set up **Systemd Services** on the server. The advantage of this is that if the server crashes, reboots, or loses power, everything will start back up automatically.

The following services are configured on your server:
1.  `nginx.service`: To serve the frontend.
2.  `crm-backend.service`: To auto-start the Python backend.
3.  `pinggy.service`: To automatically establish and reconnect the Pinggy tunnel.

If you ever need to manually turn these services on/off, use these commands:
```bash
sudo systemctl stop crm-backend.service    # To stop the service
sudo systemctl start crm-backend.service   # To start the service
sudo systemctl status crm-backend.service  # To check the status
```

---

## 4. One-Click Restart (Shortcut)

Whenever you want to completely refresh the project or apply new code, run the bash script placed in your home directory:

```bash
# Run this in your SSH terminal
cd ~
./restart_crm.sh
```
This script will automatically:
1. Restart the Backend, Nginx, and Pinggy.
2. Extract the **New Pinggy URL** and print it directly on your screen.

---

## 5. Troubleshooting & Logs

If something seems wrong with the system, checking the "Logs" is the most important step.

**To view Backend Errors (Python crashes):**
```bash
sudo journalctl -u crm-backend.service -f
```
*(Press `Ctrl + C` to exit)*

**To view Nginx Errors (like 500, 404, etc.):**
```bash
sudo tail -f /var/log/nginx/error.log
```

**To manually extract the new Pinggy URL:**
```bash
sudo journalctl -u pinggy.service -n 50 | grep "http"
```

---

## 6. Database Access

If you ever need to manually check the database in the future, you can log into PostgreSQL from the server terminal like this:
```bash
PGPASSWORD=Keya123 psql -U postgres -h localhost -d crm_db
```
*(Type `\q` and press Enter to exit)*
