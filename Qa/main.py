# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import qa

app = FastAPI(
    title       = "QA Automation API",
    description = "Signal-driven QA — send a signal, get a report",
    version     = "2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(qa.router, prefix="/qa", tags=["QA"])

@app.get("/health")
def health():
    return {"status": "ok"}