from fastapi import FastAPI

from app.api.crm import router as crm_router

app = FastAPI(title="Enterprise CRM API")
app.include_router(crm_router)


@app.get("/")
def root():
    return {
        "message": "CRM Backend Running Successfully"
    }