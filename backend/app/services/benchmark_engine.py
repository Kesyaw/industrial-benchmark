"""
Benchmark Engine — DB-driven scoring using benchmark_thresholds.

Scores a company's 5 key ratios against sector-specific thresholds
loaded from the database, then computes the health predicate.
"""
import logging
from typing import Optional, Dict, List
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import BenchmarkThreshold, Sector
from app.schemas import FinancialData, BenchmarkResult, RatioScore

log = logging.getLogger(__name__)

# ── Health predicate table (from Bank Sumsel Babel methodology) ──
# Score = 1         → Tidak Sehat
# 2  <= s <= 25     → Kurang Sehat
# 26 <= s <= 50     → Cukup Sehat
# 51 <= s <= 75     → Sehat
# 76 <= s <= 100    → Sangat Sehat

def _health_predicate(avg_score: float) -> str:
    if avg_score >= 76:
        return "Sangat Sehat"
    elif avg_score >= 51:
        return "Sehat"
    elif avg_score >= 26:
        return "Cukup Sehat"
    elif avg_score >= 2:
        return "Kurang Sehat"
    else:
        return "Tidak Sehat"


def _compute_ratios(data: FinancialData) -> Dict[str, Optional[float]]:
    """Compute the 5 key ratios from manual input data."""
    CA = data.current_assets
    CL = data.current_liabilities
    EBIT = data.ebit
    INT = data.interest_expense
    TL = data.total_debt          # total liabilities
    NW = data.total_equity        # net worth
    FOCF = data.free_operating_cash_flow

    current_ratio = CA / CL if CL != 0 else None
    interest_coverage = EBIT / INT if INT != 0 else None
    total_debt_to_equity = TL / NW if NW != 0 else None
    debt_to_net_worth = TL / NW if NW != 0 else None
    focf_to_total_debt = FOCF / TL if TL != 0 else None

    return {
        "current_ratio": round(current_ratio, 4) if current_ratio is not None else None,
        "interest_coverage": round(interest_coverage, 4) if interest_coverage is not None else None,
        "total_debt_to_equity": round(total_debt_to_equity, 4) if total_debt_to_equity is not None else None,
        "debt_to_net_worth": round(debt_to_net_worth, 4) if debt_to_net_worth is not None else None,
        "focf_to_total_debt": round(focf_to_total_debt, 4) if focf_to_total_debt is not None else None,
    }


def _score_ratio(value: Optional[float], thresholds: List[BenchmarkThreshold]) -> RatioScore:
    """Score a single ratio value against its threshold levels."""
    if not thresholds:
        return RatioScore(
            ratio_code=thresholds[0].metric_code if thresholds else "unknown",
            ratio_name="",
            ratio_value=value,
            level=None,
            level_label=None,
            score=None,
        )

    code = thresholds[0].metric_code

    # If the ratio could not be computed (e.g. no interest expense)
    if value is None:
        return RatioScore(
            ratio_code=code,
            ratio_name=code,
            ratio_value=None,
            level=None,
            level_label="N/A",
            score=None,
        )

    # Find which level this value falls into
    for t in sorted(thresholds, key=lambda x: x.level):
        lo = float(t.range_min) if t.range_min is not None else float("-inf")
        hi = float(t.range_max) if t.range_max is not None else float("inf")
        if lo <= value <= hi:
            return RatioScore(
                ratio_code=code,
                ratio_name=code,
                ratio_value=round(value, 4),
                level=t.level,
                level_label=t.level_label,
                score=t.score,
            )

    # No match — assign level 1 (worst) as fallback
    fallback = sorted(thresholds, key=lambda x: x.level)
    worst = fallback[0] if fallback else None
    return RatioScore(
        ratio_code=code,
        ratio_name=code,
        ratio_value=round(value, 4),
        level=worst.level if worst else 1,
        level_label=worst.level_label if worst else "Tidak Baik",
        score=worst.score if worst else 1,
    )


# ── Fallback hardcoded thresholds (if DB is empty) ──
FALLBACK_THRESHOLDS = {
    "current_ratio": [
        (None, 1.73, 1), (1.74, 1.94, 25), (1.95, 2.15, 50),
        (2.16, 2.37, 75), (2.38, None, 100),
    ],
    "interest_coverage": [
        (None, 7.68, 1), (7.69, 19.76, 25), (19.77, 31.84, 50),
        (31.85, 43.92, 75), (43.93, None, 100),
    ],
    "total_debt_to_equity": [
        (None, 1.00, 100), (1.01, 1.13, 75), (1.14, 1.26, 50),
        (1.27, 1.39, 25), (1.40, None, 1),
    ],
    "debt_to_net_worth": [
        (None, 0.51, 100), (0.52, 0.58, 75), (0.59, 0.65, 50),
        (0.66, 0.72, 25), (0.73, None, 1),
    ],
    "focf_to_total_debt": [
        (None, -3.53, 1), (-3.52, -2.02, 25), (-2.01, -0.50, 50),
        (-0.49, 1.02, 75), (1.03, None, 100),
    ],
}


def _fallback_score(value: Optional[float], code: str) -> int:
    """Score using hardcoded fallback thresholds."""
    if value is None:
        return 0
    ranges = FALLBACK_THRESHOLDS.get(code, [])
    for lo, hi, score in ranges:
        lo_v = lo if lo is not None else float("-inf")
        hi_v = hi if hi is not None else float("inf")
        if lo_v <= value <= hi_v:
            return score
    return 1


def calculate_benchmark(data: FinancialData, db: Session = None) -> BenchmarkResult:
    """
    Calculate benchmark for manual input.
    Uses DB thresholds if available, otherwise falls back to hardcoded Trade sector.
    """
    ratios = _compute_ratios(data)
    key_ratios = ["current_ratio", "interest_coverage", "total_debt_to_equity",
                  "debt_to_net_worth", "focf_to_total_debt"]

    scores = {}
    details: List[RatioScore] = []

    if db:
        # Try loading sector thresholds from DB
        sector = db.query(Sector).filter(Sector.code == data.sector_code).first()
        sector_id = sector.id if sector else None

        for code in key_ratios:
            thresholds = []
            if sector_id:
                thresholds = (
                    db.query(BenchmarkThreshold)
                    .filter(
                        BenchmarkThreshold.sector_id == sector_id,
                        BenchmarkThreshold.metric_code == code,
                    )
                    .order_by(BenchmarkThreshold.level)
                    .all()
                )

            val = ratios.get(code)

            if thresholds:
                detail = _score_ratio(val, thresholds)
            else:
                s = _fallback_score(val, code)
                detail = RatioScore(
                    ratio_code=code, ratio_name=code,
                    ratio_value=round(val, 4) if val else None,
                    level=None, level_label="Fallback", score=s,
                )

            details.append(detail)
            if detail.score is not None:
                scores[code] = detail.score
    else:
        # No DB — pure fallback
        for code in key_ratios:
            val = ratios.get(code)
            s = _fallback_score(val, code)
            scores[code] = s
            details.append(RatioScore(
                ratio_code=code, ratio_name=code,
                ratio_value=round(val, 4) if val else None,
                level=None, level_label="Fallback", score=s,
            ))

    # Average (skip ratios with None score, e.g. interest_coverage with 0 interest)
    valid_scores = [v for v in scores.values() if v is not None and v > 0]
    avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

    return BenchmarkResult(
        company=data.company_name,
        sector_code=data.sector_code,
        ratios=ratios,
        scores=scores,
        score_details=details,
        average_score=round(avg, 2),
        health_predicate=_health_predicate(avg),
    )
