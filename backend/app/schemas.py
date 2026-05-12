from pydantic import BaseModel
from typing import Optional

class FinancialData(BaseModel):
    company_name: str
    current_assets: float
    current_liabilities: float
    ebit: float
    interest_expense: float
    total_debt: float
    total_equity: float
    free_operating_cash_flow: float

class BenchmarkResult(BaseModel):
    company: str
    ratios: dict
    scores: dict
    average_score: float
    health_predicate: str
