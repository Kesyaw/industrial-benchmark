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
import math
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
from app.services.xlsx_extractor import extract_financial_data_from_xlsx
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

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data/uploads")
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
        metrics = []
        for m in metrics_raw:
            val = None
            if m.metric_value is not None:
                try:
                    f_val = float(m.metric_value)
                    if not math.isnan(f_val):
                        val = f_val
                except ValueError:
                    pass
                    
            metrics.append(MetricValueOut(
                code=m.code, name_id=m.name_id, name_en=m.name_en,
                category=m.category, unit=m.unit,
                value=val,
            ))
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

@app.get("/api/companies/{ticker}/benchmark/{year}")
def get_company_benchmark_by_year(ticker: str, year: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
        
    period = db.query(FinancialPeriod).filter(
        FinancialPeriod.company_id == company.id,
        FinancialPeriod.fiscal_year == year
    ).first()
    
    if not period:
        raise HTTPException(status_code=404, detail=f"No data for {ticker} in {year}")
        
    metrics = (
        db.query(MetricDefinition.code, FinancialMetric.metric_value)
        .join(FinancialMetric, FinancialMetric.metric_definition_id == MetricDefinition.id)
        .filter(FinancialMetric.period_id == period.id)
        .all()
    )
    
    extracted_data = {m.code: float(m.metric_value) for m in metrics if m.metric_value is not None}
    sector = db.query(Sector).filter(Sector.id == company.sector_id).first()
    
    data_dict = {
        "company_name": company.ticker,
        "sector_code": sector.code if sector else "TRADE",
        "current_assets": extracted_data.get("aset_lancar", extracted_data.get("current_assets", 0.0)),
        "current_liabilities": extracted_data.get("liabilitas_jangka_pendek", extracted_data.get("current_liabilities", 0.0)),
        "ebit": extracted_data.get("laba_rugi_sebelum_pajak_penghasilan", extracted_data.get("ebit", 0.0)),
        "interest_expense": extracted_data.get("interest_expense", 0.0),
        "ebitda": extracted_data.get("laba_rugi_sebelum_pajak_penghasilan", extracted_data.get("ebitda", 0.0)),
        "total_debt": extracted_data.get("liabilitas", extracted_data.get("total_debt", 0.0)),
        "total_equity": extracted_data.get("ekuitas", extracted_data.get("total_equity", 0.0)),
        "long_term_debt": extracted_data.get("liabilitas_jangka_panjang", extracted_data.get("long_term_debt", 0.0)),
        "total_assets": extracted_data.get("aset", extracted_data.get("total_assets", 0.0)),
        "gross_profit": extracted_data.get("jumlah_laba_kotor", extracted_data.get("gross_profit", 0.0)),
        "net_income": extracted_data.get("laba_rugi_tahun_berjalan", extracted_data.get("net_income", 0.0)),
        "revenue": extracted_data.get("penjualan_dan_pendapatan_usaha", extracted_data.get("revenue", 0.0)),
        "free_operating_cash_flow": extracted_data.get("laba_rugi_tahun_berjalan", extracted_data.get("free_operating_cash_flow", 0.0)),
    }
    
    fin_data = FinancialData(**data_dict)
    result = calculate_benchmark(fin_data, db=db)
    return result

# ─────────────────────────────────────────
# BENCHMARK SECTOR LEADERBOARD
# ─────────────────────────────────────────
@app.get("/api/benchmark/sector/{sector_code}/year/{year}")
def get_sector_leaderboard_by_year(sector_code: str, year: int, db: Session = Depends(get_db)):
    """Returns a leaderboard of companies within a sector based on their benchmark score."""
    sector = db.query(Sector).filter(Sector.code == sector_code.upper()).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {sector_code} not found")

    companies = db.query(Company).filter(Company.sector_id == sector.id).all()
    company_ids = [c.id for c in companies]
    
    if not company_ids:
        return {"sector": SectorOut.model_validate(sector), "year": year, "leaderboard": []}
        
    periods = db.query(FinancialPeriod).filter(
        FinancialPeriod.company_id.in_(company_ids),
        FinancialPeriod.fiscal_year == year
    ).all()
    
    period_dict = {p.company_id: p for p in periods}
    period_ids = [p.id for p in periods]
    
    if not period_ids:
        return {"sector": SectorOut.model_validate(sector), "year": year, "leaderboard": []}

    metrics = (
        db.query(FinancialMetric.period_id, MetricDefinition.code, FinancialMetric.metric_value)
        .join(MetricDefinition, FinancialMetric.metric_definition_id == MetricDefinition.id)
        .filter(FinancialMetric.period_id.in_(period_ids))
        .all()
    )
    
    metrics_by_period = {}
    for pid, code, val in metrics:
        if pid not in metrics_by_period:
            metrics_by_period[pid] = {}
        if val is not None:
            metrics_by_period[pid][code] = float(val)
            
    leaderboard = []
    for company in companies:
        period = period_dict.get(company.id)
        if not period:
            continue
            
        extracted = metrics_by_period.get(period.id, {})
        
        data_dict = {
            "company_name": company.ticker,
            "sector_code": sector.code,
            "current_assets": extracted.get("aset_lancar", extracted.get("current_assets", 0.0)),
            "current_liabilities": extracted.get("liabilitas_jangka_pendek", extracted.get("current_liabilities", 0.0)),
            "ebit": extracted.get("laba_rugi_sebelum_pajak_penghasilan", extracted.get("ebit", 0.0)),
            "interest_expense": extracted.get("interest_expense", 0.0),
            "ebitda": extracted.get("laba_rugi_sebelum_pajak_penghasilan", extracted.get("ebitda", 0.0)),
            "total_debt": extracted.get("liabilitas", extracted.get("total_debt", 0.0)),
            "total_equity": extracted.get("ekuitas", extracted.get("total_equity", 0.0)),
            "long_term_debt": extracted.get("liabilitas_jangka_panjang", extracted.get("long_term_debt", 0.0)),
            "total_assets": extracted.get("aset", extracted.get("total_assets", 0.0)),
            "gross_profit": extracted.get("jumlah_laba_kotor", extracted.get("gross_profit", 0.0)),
            "net_income": extracted.get("laba_rugi_tahun_berjalan", extracted.get("net_income", 0.0)),
            "revenue": extracted.get("penjualan_dan_pendapatan_usaha", extracted.get("revenue", 0.0)),
            "free_operating_cash_flow": extracted.get("laba_rugi_tahun_berjalan", extracted.get("free_operating_cash_flow", 0.0)),
        }
        
        fin_data = FinancialData(**data_dict)
        result = calculate_benchmark(fin_data, db=db)
        
        leaderboard.append({
            "ticker": company.ticker,
            "company_name": company.name,
            "score": result.average_score,
            "predicate": result.health_predicate
        })
        
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "sector": SectorOut.model_validate(sector),
        "year": year,
        "leaderboard": leaderboard
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
# REPORT UPLOAD (PDF or XLSX)
# ─────────────────────────────────────────
@app.post("/api/upload-pdf")
async def upload_report(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only PDF or XLSX files are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if file.filename.endswith(".pdf"):
            financial_data = extract_financial_data_from_pdf(file_path, file.filename)
        else:
            financial_data = extract_financial_data_from_xlsx(file_path, file.filename)
            
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
