"""
Pydantic schemas for API request/response models.
"""
from typing import Optional, Dict, List
from pydantic import BaseModel
from datetime import date


# ── Sector ──
class SectorOut(BaseModel):
    id: int
    code: str
    name_id: str
    name_en: str
    is_financial: bool
    has_inventory: bool

    class Config:
        from_attributes = True


# ── Company ──
class CompanyOut(BaseModel):
    id: int
    ticker: str
    name: str
    sector_id: Optional[int]
    subsector: Optional[str]
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


# ── Manual Benchmark Input (backward-compatible with existing frontend) ──
class FinancialData(BaseModel):
    company_name: str
    sector_code: str = "TRADE"         # NEW: which sector benchmark to use
    current_assets: float
    current_liabilities: float
    ebit: float
    interest_expense: float = 0.0
    ebitda: float = 0.0
    total_debt: float                  # = total_liabilities (TL)
    total_equity: float                # = net worth (NW)
    long_term_debt: float = 0.0
    total_assets: float = 0.0
    gross_profit: float = 0.0
    net_income: float = 0.0
    revenue: float = 0.0
    free_operating_cash_flow: float


# ── Benchmark Score per ratio ──
class RatioScore(BaseModel):
    ratio_code: str
    ratio_name: str
    ratio_value: Optional[float]
    level: Optional[int]
    level_label: Optional[str]
    score: Optional[int]


# ── Benchmark Result ──
class BenchmarkResult(BaseModel):
    company: str
    sector_code: str
    ratios: Dict[str, Optional[float]]
    scores: Dict[str, Optional[int]]
    score_details: List[RatioScore] = []
    average_score: float
    health_predicate: str


# ── ETL trigger request ──
class EtlRunRequest(BaseModel):
    sector_filter: Optional[str] = None
    year: Optional[int] = None
    limit: Optional[int] = 20   # default small for safety


# ── Financial Metric value ──
class MetricValueOut(BaseModel):
    code: str
    name_id: str
    name_en: str
    category: str
    unit: str
    value: Optional[float]

    class Config:
        from_attributes = True


# ── Company Period Summary ──
class PeriodSummaryOut(BaseModel):
    period_id: int
    fiscal_year: int
    period_type: str
    source: str
    metrics: List[MetricValueOut] = []

    class Config:
        from_attributes = True


# ── Asset Write-off ──
class AssetWriteoffIn(BaseModel):
    company_id: int
    period_id: Optional[int] = None
    asset_category: str
    asset_name: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[int] = None
    accumulated_depr: Optional[int] = None
    book_value_before: int
    writeoff_amount: int
    annual_depr_rate: Optional[float] = None
    useful_life_years: Optional[int] = None
    writeoff_date: Optional[date] = None
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    reference_doc: Optional[str] = None
    notes: Optional[str] = None


class AssetWriteoffOut(AssetWriteoffIn):
    id: int
    book_value_after: Optional[int]

    class Config:
        from_attributes = True
