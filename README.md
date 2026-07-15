# CRM Project

This is a modern CRM application featuring role-based access control, automated workflows, email tracking, and document management.

## Setup Instructions

### 1. Database
Ensure PostgreSQL is installed and running. Create a database named `crm_db`.

### 2. Configuration
Copy the `.env.example` file to `.env` in the `backend/` directory and fill in the required values (especially `SECRET_KEY` and `ENCRYPTION_KEY`).

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
python create_admin.py  # Follow prompts to create the initial admin user
python seed.py          # Optional: seed initial dummy data
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Architecture
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Frontend:** Next.js (or React/Vite), TypeScript, TailwindCSS
