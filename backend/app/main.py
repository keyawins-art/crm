from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.crm import router as crm_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notifications_router
from app.api.documents import router as documents_router
from app.api.reports import router as reports_router
from app.api.tasks import router as tasks_router
from app.api.meetings import router as meetings_router

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


@app.get("/")
def root():
    return {
        "message": "CRM Backend Running Successfully"
    }