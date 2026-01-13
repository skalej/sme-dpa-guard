from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, reviews
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(reviews.router)
