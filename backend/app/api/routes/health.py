from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import db_ping

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> JSONResponse:
    if db_ping():
        return JSONResponse(status_code=200, content={"status": "ok"})
    return JSONResponse(status_code=503, content={"status": "not_ready"})
