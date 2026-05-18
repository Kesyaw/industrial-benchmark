"""
Company & Sector routes.

GET /api/sectors
GET /api/companies
GET /api/companies/{ticker}
GET /api/companies/{ticker}/benchmark/{year}
"""
import math
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SectorOut, CompanyOut, MetricValueOut
from app.models import Sector, Company, FinancialPeriod, FinancialMetric, MetricDefinition
from app.services.benchmark_engine import calculate_benchmark
from app.utils.metric_mapper import build_financial_data

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/sectors", response_model=list[SectorOut])
def list_sectors(db: Session = Depends(get_db)):
    return db.query(Sector).order_by(Sector.name_en).all()


@router.get("/api/companies", response_model=list[CompanyOut])
def list_companies(sector: str = None, db: Session = Depends(get_db)):
    query = db.query(Company)
    if sector:
        sec = db.query(Sector).filter(Sector.code == sector.upper()).first()
        if sec:
            query = query.filter(Company.sector_id == sec.id)
    return query.order_by(Company.ticker).limit(500).all()


@router.get("/api/companies/{ticker}")
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
            db.query(
                MetricDefinition.code, MetricDefinition.name_id,
                MetricDefinition.name_en, MetricDefinition.category,
                MetricDefinition.unit, FinancialMetric.metric_value,
            )
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
                    val = f_val if not math.isnan(f_val) else None
                except (ValueError, TypeError):
                    pass
            metrics.append(MetricValueOut(
                code=m.code, name_id=m.name_id, name_en=m.name_en,
                category=m.category, unit=m.unit or "IDR", value=val,
            ))

        result_periods.append({
            "period_id":   p.id,
            "fiscal_year": p.fiscal_year,
            "period_type": p.period_type.value if hasattr(p.period_type, "value") else str(p.period_type),
            "source":      p.source,
            "metrics":     metrics,
        })

    sector = db.query(Sector).filter(Sector.id == company.sector_id).first()
    return {
        "company": CompanyOut.model_validate(company),
        "sector":  SectorOut.model_validate(sector) if sector else None,
        "periods": result_periods,
    }


@router.get("/api/companies/{ticker}/benchmark/{year}")
def get_company_benchmark(ticker: str, year: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

    period = db.query(FinancialPeriod).filter(
        FinancialPeriod.company_id == company.id,
        FinancialPeriod.fiscal_year == year,
    ).first()
    if not period:
        raise HTTPException(status_code=404, detail=f"No data for {ticker} in {year}")

    metrics = (
        db.query(MetricDefinition.code, FinancialMetric.metric_value)
        .join(FinancialMetric, FinancialMetric.metric_definition_id == MetricDefinition.id)
        .filter(FinancialMetric.period_id == period.id)
        .all()
    )
    extracted = {m.code: float(m.metric_value) for m in metrics if m.metric_value is not None}

    sector = db.query(Sector).filter(Sector.id == company.sector_id).first()
    sector_code = sector.code if sector else "TRADE"

    fin_data = build_financial_data(company.ticker, sector_code, extracted)
    return calculate_benchmark(fin_data, db=db)
