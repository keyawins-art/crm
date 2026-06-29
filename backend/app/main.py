from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.crm import router as crm_router
from app.api.dashboard import router as dashboard_router

app = FastAPI(title="Enterprise CRM API")
app.include_router(auth_router)
app.include_router(crm_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {
        "message": "CRM Backend Running Successfully"
    }