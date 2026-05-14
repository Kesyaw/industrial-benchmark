"""
Industrial Benchmark API — FastAPI Application

Routes:
  GET  /                          → Health check
  GET  /api/health                → DB health check
  GET  /api/sectors               → List all sectors
  GET  /api/companies             → List companies (optional ?sector=TRADE)
  GET  /api/companies/{ticker}    → Company detail with metrics
  POST /api/benchmark             → Manual benchmark calculation
  POST /api/upload-pdf            → PDF upload + extract + benchmark
  POST /api/etl/run               → Trigger ETL pull from IDX
  POST /api/etl/seed              → Seed DB with reference data
  POST /api/etl/compute-ratios    → Compute ratios for all periods
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
import os
import shutil
import logging

from app.config import settings
from app.database import get_db, check_connection
from app.schemas import (
    FinancialData, BenchmarkResult, SectorOut, CompanyOut,
    EtlRunRequest, MetricValueOut, PeriodSummaryOut,
)
from app.models import (
    Sector, Company, FinancialPeriod, FinancialMetric,
    MetricDefinition, EtlLog,
)
from app.services.benchmark_engine import calculate_benchmark
from app.services.pdf_extractor import extract_financial_data_from_pdf
from app.services.report_generator import generate_benchmark_pdf

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Industrial Benchmark API",
    description="Financial Data Warehouse & Industry Benchmark Scoring Engine",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data/pdfs")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "Industrial Benchmark API v2.0", "status": "running"}


@app.get("/api/health")
def health_check():
    db_ok = check_connection()
    return {
        "api": "ok",
        "database": "connected" if db_ok else "disconnected",
    }


# ─────────────────────────────────────────
# SECTORS
# ─────────────────────────────────────────
@app.get("/api/sectors", response_model=list[SectorOut])
def list_sectors(db: Session = Depends(get_db)):
    return db.query(Sector).order_by(Sector.name_en).all()


# ─────────────────────────────────────────
# COMPANIES
# ─────────────────────────────────────────
@app.get("/api/companies", response_model=list[CompanyOut])
def list_companies(sector: str = None, db: Session = Depends(get_db)):
    query = db.query(Company)
    if sector:
        sec = db.query(Sector).filter(Sector.code == sector.upper()).first()
        if sec:
            query = query.filter(Company.sector_id == sec.id)
    return query.order_by(Company.ticker).limit(500).all()


@app.get("/api/companies/{ticker}")
def get_company_detail(ticker: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

    periods = (
        db.query(FinancialPeriod)
        .filter(FinancialPeriod.company_id == company.id)
        .order_by(FinancialPeriod.fiscal_year.desc())
        .all()
    )

    result_periods = []
    for p in periods:
        metrics_raw = (
            db.query(MetricDefinition.code, MetricDefinition.name_id,
                     MetricDefinition.name_en, MetricDefinition.category,
                     MetricDefinition.unit, FinancialMetric.metric_value)
            .join(FinancialMetric, FinancialMetric.metric_definition_id == MetricDefinition.id)
            .filter(FinancialMetric.period_id == p.id)
            .order_by(MetricDefinition.sort_order)
            .all()
        )
        metrics = [
            MetricValueOut(
                code=m.code, name_id=m.name_id, name_en=m.name_en,
                category=m.category, unit=m.unit,
                value=float(m.metric_value) if m.metric_value else None,
            )
            for m in metrics_raw
        ]
        result_periods.append({
            "period_id": p.id,
            "fiscal_year": p.fiscal_year,
            "period_type": p.period_type.value if hasattr(p.period_type, 'value') else str(p.period_type),
            "source": p.source,
            "metrics": metrics,
        })

    sector = db.query(Sector).filter(Sector.id == company.sector_id).first()

    return {
        "company": CompanyOut.model_validate(company),
        "sector": SectorOut.model_validate(sector) if sector else None,
        "periods": result_periods,
    }


# ─────────────────────────────────────────
# BENCHMARK (manual input)
# ─────────────────────────────────────────
@app.post("/api/benchmark", response_model=BenchmarkResult)
def benchmark_manual(data: FinancialData, db: Session = Depends(get_db)):
    return calculate_benchmark(data, db=db)


# ─────────────────────────────────────────
# BENCHMARK BY SECTOR (industry averages)
# ─────────────────────────────────────────
@app.get("/api/benchmark/sector/{sector_code}")
def get_sector_benchmark(sector_code: str, db: Session = Depends(get_db)):
    sector = db.query(Sector).filter(Sector.code == sector_code.upper()).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {sector_code} not found")

    from app.models import BenchmarkThreshold
    thresholds = (
        db.query(BenchmarkThreshold)
        .filter(BenchmarkThreshold.sector_id == sector.id)
        .order_by(BenchmarkThreshold.metric_code, BenchmarkThreshold.level)
        .all()
    )

    result = {}
    for t in thresholds:
        if t.metric_code not in result:
            result[t.metric_code] = []
        result[t.metric_code].append({
            "level": t.level,
            "label": t.level_label,
            "min": float(t.range_min) if t.range_min else None,
            "max": float(t.range_max) if t.range_max else None,
            "score": t.score,
        })

    return {"sector": SectorOut.model_validate(sector), "thresholds": result}


# ─────────────────────────────────────────
# PDF UPLOAD (backward-compatible)
# ─────────────────────────────────────────
@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        financial_data = extract_financial_data_from_pdf(file_path, file.filename)
        result = calculate_benchmark(financial_data, db=db)
        return {
            "message": f"Processed {file.filename}",
            "extracted_data": financial_data.model_dump(),
            "benchmark_result": result.model_dump(),
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    finally:
        pass  # keep file for audit


# ─────────────────────────────────────────
# ETL ENDPOINTS
# ─────────────────────────────────────────
@app.post("/api/etl/seed")
def run_seed(db: Session = Depends(get_db)):
    """Seed the database with sectors, metric definitions, and benchmark thresholds."""
    from app.etl.seeder import run_all_seeds
    try:
        run_all_seeds()
        return {"status": "ok", "message": "Database seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etl/run")
def run_etl_endpoint(req: EtlRunRequest, db: Session = Depends(get_db)):
    """Trigger IDX data pull via ETL pipeline."""
    from app.etl.idx_scraper import run_etl
    try:
        run_etl(
            sector_filter=req.sector_filter,
            year=req.year,
            limit=req.limit,
        )
        return {"status": "ok", "message": "ETL completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etl/compute-ratios")
def compute_all_ratios(db: Session = Depends(get_db)):
    """Compute all 28 financial ratios for every period in the DB."""
    from app.etl.ratio_calculator import run_ratio_calculation_all
    try:
        run_ratio_calculation_all(db)
        return {"status": "ok", "message": "Ratios computed for all periods"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etl/idx-download")
def run_idx_download_endpoint(req: EtlRunRequest, db: Session = Depends(get_db)):
    """Download financial statements directly from idx.co.id (more reliable than yfinance)."""
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


# ─────────────────────────────────────────
# ETL LOGS
# ─────────────────────────────────────────
@app.get("/api/etl/logs")
def get_etl_logs(db: Session = Depends(get_db)):
    logs = db.query(EtlLog).order_by(EtlLog.run_at.desc()).limit(20).all()
    return [
        {
            "id": l.id,
            "run_at": str(l.run_at),
            "source": l.source,
            "total": l.tickers_total,
            "success": l.tickers_success,
            "failed": l.tickers_failed,
            "duration_secs": float(l.duration_secs) if l.duration_secs else None,
        }
        for l in logs
    ]


# ─────────────────────────────────────────
# PDF REPORT DOWNLOAD
# ─────────────────────────────────────────
@app.post("/api/benchmark/report")
def download_benchmark_report(data: FinancialData, db: Session = Depends(get_db)):
    """Calculate benchmark and return a downloadable PDF report."""
    result = calculate_benchmark(data, db=db)
    pdf_bytes = generate_benchmark_pdf(result.model_dump())
    company_name = data.company_name.replace(" ", "_") if data.company_name else "report"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="benchmark_{company_name}.pdf"'
        },
    )


@app.post("/api/benchmark/report-from-result")
def download_report_from_result(result: dict):
    """Generate PDF from an existing benchmark result dict (from frontend)."""
    pdf_bytes = generate_benchmark_pdf(result)
    company = result.get("company", "report").replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="benchmark_{company}.pdf"'
        },
    )
