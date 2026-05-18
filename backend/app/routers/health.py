"""Health check routes."""
from fastapi import APIRouter
from app.database import check_connection

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "Industrial Benchmark API v2.0", "status": "running"}


@router.get("/api/health")
def health_check():
    db_ok = check_connection()
    return {
        "api": "ok",
        "database": "connected" if db_ok else "disconnected",
    }
