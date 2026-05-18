"""
Benchmark Engine — DB-driven scoring using benchmark_thresholds.

Scores a company's 5 key ratios against sector-specific thresholds
loaded from the database, then computes the health predicate.
"""
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models import BenchmarkThreshold, Sector
from app.schemas import FinancialData, BenchmarkResult, RatioScore

log = logging.getLogger(__name__)

# ── Health predicate table (from Bank Sumsel Babel methodology) ──
# Score range → Predicate
# 76–100  → Sangat Sehat
# 51–75   → Sehat
# 26–50   → Cukup Sehat
# 2–25    → Kurang Sehat
# 0–1     → Tidak Sehat

HEALTH_THRESHOLDS = [
    (76, "Sangat Sehat"),
    (51, "Sehat"),
    (26, "Cukup Sehat"),
    (2,  "Kurang Sehat"),
]

# ── Fallback hardcoded thresholds (if DB is empty) ──
FALLBACK_THRESHOLDS: Dict[str, list] = {
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

KEY_RATIOS = [
    "current_ratio",
    "interest_coverage",
    "total_debt_to_equity",
    "debt_to_net_worth",
    "focf_to_total_debt",
]


def _health_predicate(avg_score: float) -> str:
    for min_score, label in HEALTH_THRESHOLDS:
        if avg_score >= min_score:
            return label
    return "Tidak Sehat"


def _compute_ratios(data: FinancialData) -> Dict[str, Optional[float]]:
    """Compute 5 key ratios from financial input data."""
    ca   = data.current_assets
    cl   = data.current_liabilities
    ebit = data.ebit
    int_ = data.interest_expense
    tl   = data.total_debt
    nw   = data.total_equity
    focf = data.free_operating_cash_flow

    def safe_divide(numerator: float, denominator: float) -> Optional[float]:
        return round(numerator / denominator, 4) if denominator != 0 else None

    return {
        "current_ratio":        safe_divide(ca, cl),
        "interest_coverage":    safe_divide(ebit, int_),
        "total_debt_to_equity": safe_divide(tl, nw),
        "debt_to_net_worth":    safe_divide(tl, nw),
        "focf_to_total_debt":   safe_divide(focf, tl),
    }


def _score_ratio(value: Optional[float], thresholds: List[BenchmarkThreshold]) -> RatioScore:
    """Score a single ratio value against its DB threshold levels."""
    # FIX: Guard must come before any access to thresholds[0]
    if not thresholds:
        return RatioScore(
            ratio_code="unknown", ratio_name="unknown",
            ratio_value=value, level=None, level_label="N/A", score=None,
        )

    code = thresholds[0].metric_code

    if value is None:
        return RatioScore(
            ratio_code=code, ratio_name=code,
            ratio_value=None, level=None, level_label="N/A", score=None,
        )

    for t in sorted(thresholds, key=lambda x: x.level):
        lo = float(t.range_min) if t.range_min is not None else float("-inf")
        hi = float(t.range_max) if t.range_max is not None else float("inf")
        if lo <= value <= hi:
            return RatioScore(
                ratio_code=code, ratio_name=code,
                ratio_value=round(value, 4),
                level=t.level, level_label=t.level_label, score=t.score,
            )

    # No match — assign worst level as fallback
    worst = sorted(thresholds, key=lambda x: x.level)[0]
    return RatioScore(
        ratio_code=code, ratio_name=code,
        ratio_value=round(value, 4),
        level=worst.level, level_label=worst.level_label, score=worst.score,
    )


def _fallback_score(value: Optional[float], code: str) -> int:
    """Score using hardcoded fallback thresholds when DB has no data."""
    if value is None:
        return 0
    for lo, hi, score in FALLBACK_THRESHOLDS.get(code, []):
        lo_v = lo if lo is not None else float("-inf")
        hi_v = hi if hi is not None else float("inf")
        if lo_v <= value <= hi_v:
            return score
    return 1


def _score_with_db(ratios: Dict[str, Optional[float]], sector_id: Optional[int], db: Session) -> List[RatioScore]:
    """Score all ratios using DB thresholds, falling back when unavailable."""
    details = []
    for code in KEY_RATIOS:
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
                ratio_value=round(val, 4) if val is not None else None,
                level=None, level_label="Fallback", score=s,
            )
        details.append(detail)
    return details


def _score_without_db(ratios: Dict[str, Optional[float]]) -> List[RatioScore]:
    """Score all ratios using hardcoded fallback thresholds only."""
    return [
        RatioScore(
            ratio_code=code, ratio_name=code,
            ratio_value=round(val, 4) if val is not None else None,
            level=None, level_label="Fallback",
            score=_fallback_score(val, code),
        )
        for code in KEY_RATIOS
        for val in [ratios.get(code)]
    ]


def calculate_benchmark(data: FinancialData, db: Optional[Session] = None) -> BenchmarkResult:
    """
    Calculate benchmark health score for a company.
    Uses DB thresholds if available, otherwise falls back to hardcoded values.
    """
    ratios = _compute_ratios(data)

    if db:
        sector = db.query(Sector).filter(Sector.code == data.sector_code).first()
        sector_id = sector.id if sector else None
        details = _score_with_db(ratios, sector_id, db)
    else:
        details = _score_without_db(ratios)

    scores = {d.ratio_code: d.score for d in details}
    valid_scores = [v for v in scores.values() if v is not None and v > 0]
    avg = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

    return BenchmarkResult(
        company=data.company_name,
        sector_code=data.sector_code,
        ratios=ratios,
        scores=scores,
        score_details=details,
        average_score=avg,
        health_predicate=_health_predicate(avg),
    )
