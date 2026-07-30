# CRM Server Deployment & Operations Guide

Yeh document is project ke pure setup ka 'Source of Truth' hai. Isme bataya gaya hai ki server par cheezein kaise set hui hain, code kaise update hota hai, autostart kaise kaam karta hai, aur internet par ye kaise live hai.

---

## 1. Full Setup (Ye Kaam Kaise Karta Hai?)

Server par humne 3 alag-alag layers banaye hain jo ek sath milkar CRM chalate hain:

1. **Frontend (React/Vite):** 
   Frontend ko build karne ke baad jo files banti hain (`dist` folder me), unhe **Nginx** (Port 3000) serve karta hai.
2. **Backend (FastAPI/Python):** 
   Python ka backend ek background service me **Port 8001** par chalta hai. Nginx khud-ba-khud `/crm`, `/auth`, aur `/dashboard` ki API requests ko 8001 par forward (proxy) kar deta hai.
3. **Internet Tunnel (Ngrok):** 
   Internet se (mobile/ghar se) access karne ke liye humne **Ngrok** use kiya hai. Ngrok ka internal API **Port 4041** par chalta hai aur yeh Nginx (Port 3000) ko sidha tumhare fixed internet link (`https://plank-rubber-abiding.ngrok-free.dev`) se jodta hai. Yeh setup server par maujood ERP ke purane Ngrok (Port 4040) se bilkul alag hai.

---

## 2. Server Autostart Kaise Hota Hai?

Agar server achanak se band ho jaye, light chali jaye ya reboot ho, toh tumhe manually kuch start karne ki zarurat nahi hai. 
Humne Linux (Ubuntu) ke **Systemd** me 3 background services banayi hain jo server start hote hi automatic chalu ho jati hain:

1. `nginx.service` (Frontend serve karne ke liye)
2. `crm-backend.service` (Python API start karne ke liye)
3. `crm-ngrok.service` (CRM ko fixed internet link par live karne ke liye)

Agar kabhi kisi service ko manually band ya chalu karna ho:
```bash
sudo systemctl stop crm-backend.service    # Stop karne ke liye
sudo systemctl start crm-backend.service   # Start karne ke liye
sudo systemctl status crm-backend.service  # Status check karne ke liye
```

---

## 3. Code Update Kaise Karein (Git Pull)

Jab tum apne PC (Windows) par code me changes karke GitHub par Push karte ho, toh Server par us naye code ko apply karne ke liye yeh steps follow karo:

**Step 1:** Server par SSH se login karo:
```bash
ssh keya@192.168.1.16
```

**Step 2:** GitHub se naya code Pull karo:
```bash
cd ~/crm
git pull origin main
```

**Step 3 (Agar Frontend change hua hai):** Naya build banao:
```bash
cd ~/crm/frontend
npm run build
```

**Step 4 (Agar Python me nai library add ki hai):** Dependencies install karo:
```bash
cd ~/crm/backend
source venv/bin/activate
pip install -r requirements.txt
```

**Step 5:** Setup ko Restart karo (taaki naya code apply ho):
```bash
bash ~/crm/backend/restart_crm.sh
```

---

## 4. One-Click Restart Script

Server par ek script banai gayi hai: `~/crm/backend/restart_crm.sh`.
Jab bhi tum Git pull karke yeh script chalaoge, yeh automatically Backend, Nginx, aur Ngrok ko restart karegi aur tumhara fixed link print karegi.

**Script Run Karne Ka Command:**
```bash
bash ~/crm/backend/restart_crm.sh
```

---

## 5. AI Copilot (Ollama) Deploy Kaise Karein?

CRM Copilot local Ollama model use karta hai. Model browser ko expose nahi hota; backend hi `127.0.0.1:11434` par model se baat karta hai. Current default model `qwen3:4b` hai.

Pehle verify karein ki model server par available hai:

```bash
ollama list
# Agar qwen3:4b na dikhe:
ollama pull qwen3:4b
```

Code update ke baad AI-enabled deployment ke liye:

```bash
cd ~/crm
git pull origin main
bash deploy_ai.sh
```

`deploy_ai.sh` dependencies install karta hai, frontend build karta hai, `/ai/` Nginx proxy ko validate karta hai, aur CRM services restart karta hai. Optional backend environment settings (`backend/.env`) hain:

```bash
AI_ENABLED=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_TIMEOUT_SECONDS=90
```

AI issue diagnose karne ke liye:

```bash
curl http://127.0.0.1:11434/api/tags
sudo journalctl -u crm-backend.service -n 100 --no-pager
```

## 6. Troubleshooting (Error Aaye Toh Kya Karein?)

Agar website nahi chal rahi ya koi error aa raha hai, toh Logs check karna sabse zaroori hai.

**Backend Errors (Python crashes) dekhne ke liye:**
```bash
sudo journalctl -u crm-backend.service -f
```
*(Exit karne ke liye `Ctrl + C` dabayein)*

**Nginx Errors (500, 404) dekhne ke liye:**
```bash
sudo tail -f /var/log/nginx/error.log
```

**Ngrok Status Check karne ke liye:**
```bash
sudo journalctl -u crm-ngrok.service -n 50
```

---

## 7. Database Access

Agar database (PostgreSQL) directly check karna ho:
```bash
PGPASSWORD=Keya123 psql -U postgres -h localhost -d crm_db
```
*(Exit karne ke liye `\q` likhkar Enter dabayein)*
