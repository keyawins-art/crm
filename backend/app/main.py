import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.crm import router as crm_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notifications_router
from app.api.documents import router as documents_router
from app.api.reports import router as reports_router
from app.api.tasks import router as tasks_router
from app.api.meetings import router as meetings_router
from app.api.calls import router as calls_router
from app.api.calendar import router as calendar_router
from app.api.emails import router as emails_router
from app.api.files import router as files_router
from app.api.workflows import router as workflows_router
from app.api.integrations import router as integrations_router
from app.api.knowledge_base import router as kb_router
from app.api.sales_process import router as sales_process_router
from app.api.tickets import router as tickets_router

description = """
**CRM Backend API** provides a complete suite of endpoints to manage the sales lifecycle.

## Features
* **Authentication**: JWT-based login and registration.
* **Core CRM**: Leads, Accounts, Contacts, Opportunities.
* **Sales Process**: Quotations, Sales Orders, Invoices, Payments.
* **Support**: Ticketing system and Knowledge Base.
* **Analytics**: Real-time KPI dashboard and charts.
"""

# ---------------------------------------------------------------------------
# Rate limiter (slowapi) — keyed by client IP
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="NextGen CRM API",
    description=description,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@crm.example.com",
    },
    license_info={
        "name": "Proprietary",
    }
)

# Attach limiter to the app (slowapi stores it in app.state)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — explicit origin allowlist from env var
# ---------------------------------------------------------------------------
_cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(crm_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(documents_router)
app.include_router(reports_router)
app.include_router(tasks_router)
app.include_router(meetings_router)
app.include_router(calls_router)
app.include_router(calendar_router)
app.include_router(emails_router)
app.include_router(files_router)
app.include_router(workflows_router)
app.include_router(integrations_router)
app.include_router(kb_router)
app.include_router(sales_process_router)
app.include_router(tickets_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Database integrity error: Invalid related entity ID or duplicate value."}
    )

@app.get("/")
def root():
    return {
        "message": "CRM Backend Running Successfully"
    }