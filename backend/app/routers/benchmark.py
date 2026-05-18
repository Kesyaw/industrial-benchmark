"""
Benchmark routes.

POST /api/benchmark
GET  /api/benchmark/sector/{sector_code}
GET  /api/benchmark/sector/{sector_code}/year/{year}
POST /api/benchmark/report
POST /api/benchmark/report-from-result
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FinancialData, BenchmarkResult, SectorOut
from app.models import Sector, Company, FinancialPeriod, FinancialMetric, MetricDefinition, BenchmarkThreshold
from app.services.benchmark_engine import calculate_benchmark
from app.services.report_generator import generate_benchmark_pdf
from app.utils.metric_mapper import build_financial_data

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/benchmark")


def _get_sector_or_404(sector_code: str, db: Session) -> Sector:
    sector = db.query(Sector).filter(Sector.code == sector_code.upper()).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {sector_code} not found")
    return sector


def _fetch_period_metrics(period_ids: list, db: Session) -> dict:
    """Fetch all metrics for a list of period IDs. Returns {period_id: {code: value}}."""
    metrics = (
        db.query(FinancialMetric.period_id, MetricDefinition.code, FinancialMetric.metric_value)
        .join(MetricDefinition, FinancialMetric.metric_definition_id == MetricDefinition.id)
        .filter(FinancialMetric.period_id.in_(period_ids))
        .all()
    )
    result: dict = {}
    for pid, code, val in metrics:
        if pid not in result:
            result[pid] = {}
        if val is not None:
            result[pid][code] = float(val)
    return result


@router.post("", response_model=BenchmarkResult)
def benchmark_manual(data: FinancialData, db: Session = Depends(get_db)):
    """Calculate benchmark from manually entered financial data."""
    return calculate_benchmark(data, db=db)


@router.get("/sector/{sector_code}")
def get_sector_thresholds(sector_code: str, db: Session = Depends(get_db)):
    """Return DB benchmark thresholds for a sector."""
    sector = _get_sector_or_404(sector_code, db)
    thresholds = (
        db.query(BenchmarkThreshold)
        .filter(BenchmarkThreshold.sector_id == sector.id)
        .order_by(BenchmarkThreshold.metric_code, BenchmarkThreshold.level)
        .all()
    )
    result: dict = {}
    for t in thresholds:
        if t.metric_code not in result:
            result[t.metric_code] = []
        result[t.metric_code].append({
            "level": t.level,
            "label": t.level_label,
            "min":   float(t.range_min) if t.range_min else None,
            "max":   float(t.range_max) if t.range_max else None,
            "score": t.score,
        })
    return {"sector": SectorOut.model_validate(sector), "thresholds": result}


@router.get("/sector/{sector_code}/year/{year}")
def get_sector_leaderboard(sector_code: str, year: int, db: Session = Depends(get_db)):
    """Return a ranked leaderboard of companies within a sector."""
    sector = _get_sector_or_404(sector_code, db)

    companies = db.query(Company).filter(Company.sector_id == sector.id).all()
    if not companies:
        return {"sector": SectorOut.model_validate(sector), "year": year, "leaderboard": []}

    company_ids = [c.id for c in companies]
    periods = db.query(FinancialPeriod).filter(
        FinancialPeriod.company_id.in_(company_ids),
        FinancialPeriod.fiscal_year == year,
    ).all()

    if not periods:
        return {"sector": SectorOut.model_validate(sector), "year": year, "leaderboard": []}

    period_by_company = {p.company_id: p for p in periods}
    metrics_by_period = _fetch_period_metrics([p.id for p in periods], db)

    leaderboard = []
    for company in companies:
        period = period_by_company.get(company.id)
        if not period:
            continue
        extracted = metrics_by_period.get(period.id, {})
        fin_data = build_financial_data(company.ticker, sector.code, extracted)
        result = calculate_benchmark(fin_data, db=db)
        leaderboard.append({
            "ticker":       company.ticker,
            "company_name": company.name,
            "score":        result.average_score,
            "predicate":    result.health_predicate,
        })

    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    return {"sector": SectorOut.model_validate(sector), "year": year, "leaderboard": leaderboard}


@router.post("/report")
def download_benchmark_report(data: FinancialData, db: Session = Depends(get_db)):
    """Calculate benchmark and return downloadable PDF."""
    result = calculate_benchmark(data, db=db)
    pdf_bytes = generate_benchmark_pdf(result.model_dump())
    filename = (data.company_name or "report").replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="benchmark_{filename}.pdf"'},
    )


@router.post("/report-from-result")
def download_report_from_result(result: dict):
    """Generate PDF from an existing benchmark result dict (from frontend)."""
    pdf_bytes = generate_benchmark_pdf(result)
    company = result.get("company", "report").replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="benchmark_{company}.pdf"'},
    )
