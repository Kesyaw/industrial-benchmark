"""
ETL & File Upload routes.

POST /api/upload-pdf
POST /api/etl/seed
POST /api/etl/compute-ratios
POST /api/etl/idx-download
GET  /api/etl/logs
"""
import os
import shutil
import logging
import traceback

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EtlRunRequest
from app.models import EtlLog
from app.services.benchmark_engine import calculate_benchmark
from app.services.pdf_extractor import extract_financial_data_from_pdf
from app.services.xlsx_extractor import extract_financial_data_from_xlsx

log = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_ALLOWED_EXTENSIONS = {".pdf", ".xlsx"}


@router.post("/api/upload-pdf")
async def upload_report(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF or XLSX files are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == ".pdf":
            financial_data = extract_financial_data_from_pdf(file_path, file.filename)
        else:
            financial_data = extract_financial_data_from_xlsx(file_path, file.filename)

        result = calculate_benchmark(financial_data, db=db)
        return {
            "message":          f"Processed {file.filename}",
            "extracted_data":   financial_data.model_dump(),
            "benchmark_result": result.model_dump(),
        }
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post("/api/etl/seed")
def run_seed():
    """Seed the database with sectors, metric definitions, and benchmark thresholds."""
    from app.etl.seeder import run_all_seeds
    try:
        run_all_seeds()
        return {"status": "ok", "message": "Database seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/etl/compute-ratios")
def compute_all_ratios(db: Session = Depends(get_db)):
    """Compute all financial ratios for every period in the DB."""
    from app.etl.ratio_calculator import run_ratio_calculation_all
    try:
        run_ratio_calculation_all(db)
        return {"status": "ok", "message": "Ratios computed for all periods"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/etl/idx-download")
def run_idx_download(req: EtlRunRequest):
    """Download financial statements directly from idx.co.id."""
    from app.etl.idx_direct_scraper import run_idx_download
    try:
        run_idx_download(
            sector_filter=req.sector_filter,
            year=req.year or 2024,
            limit=req.limit,
        )
        return {"status": "ok", "message": "IDX direct download completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/etl/logs")
def get_etl_logs(db: Session = Depends(get_db)):
    logs = db.query(EtlLog).order_by(EtlLog.run_at.desc()).limit(20).all()
    return [
        {
            "id":            l.id,
            "run_at":        str(l.run_at),
            "source":        l.source,
            "total":         l.tickers_total,
            "success":       l.tickers_success,
            "failed":        l.tickers_failed,
            "duration_secs": float(l.duration_secs) if l.duration_secs else None,
        }
        for l in logs
    ]
