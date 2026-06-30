from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

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

app = FastAPI(title="Enterprise CRM API")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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