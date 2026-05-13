"""
Ratio Calculator — computes all 28 financial ratios from raw EAV metric values
and stores them back into financial_metrics as computed=True.

Usage:
    from app.etl.ratio_calculator import calculate_ratios_for_period
"""
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models import FinancialPeriod, FinancialMetric, MetricDefinition

log = logging.getLogger(__name__)


def _get_values(db: Session, period_id: int) -> Dict[str, Optional[float]]:
    """Load all raw metric values for a period into a flat dict."""
    rows = (
        db.query(MetricDefinition.code, FinancialMetric.metric_value)
        .join(FinancialMetric, FinancialMetric.metric_definition_id == MetricDefinition.id)
        .filter(FinancialMetric.period_id == period_id)
        .all()
    )
    return {code: (float(val) if val is not None else None) for code, val in rows}


def _safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    """Safe division — returns None if denominator is zero or None."""
    if num is None or den is None or den == 0:
        return None
    return num / den


def _upsert_ratio(db: Session, period_id: int, code: str, value: Optional[float],
                  defn_cache: Dict[str, int]):
    """Upsert a computed ratio value."""
    if value is None:
        return
    defn_id = defn_cache.get(code)
    if not defn_id:
        return

    existing = db.query(FinancialMetric).filter(
        FinancialMetric.period_id == period_id,
        FinancialMetric.metric_definition_id == defn_id,
    ).first()

    rounded = round(value, 6)
    if existing:
        existing.metric_value = rounded
        existing.is_computed = True
    else:
        db.add(FinancialMetric(
            period_id=period_id,
            metric_definition_id=defn_id,
            metric_value=rounded,
            is_computed=True,
        ))


def calculate_ratios_for_period(db: Session, period_id: int) -> Dict[str, Optional[float]]:
    """
    Compute all 28 financial ratios for a given period.
    Returns dict of {ratio_code: value}.
    """
    v = _get_values(db, period_id)

    # Load all ratio metric_definition ids
    ratio_defns = db.query(MetricDefinition.code, MetricDefinition.id).all()
    defn_cache = {code: did for code, did in ratio_defns}

    # ── Helper aliases ──
    CA  = v.get('total_current_assets')
    CL  = v.get('total_current_liab')
    WC  = (CA - CL) if CA and CL else None
    TA  = v.get('total_assets')
    FA  = v.get('fixed_assets_net')
    TL  = v.get('total_liabilities')
    LTD = v.get('total_ltd')
    NW  = v.get('total_equity')  # Net Worth = Equity
    INT = v.get('interest_expense')
    EBIT = v.get('ebit')
    EBITDA = v.get('ebitda')
    EBT = v.get('ebt')
    EAT = v.get('net_income')
    GP  = v.get('gross_profit')
    SALES = v.get('total_revenue')
    COGS  = v.get('total_cogs')
    SGA   = v.get('admin_expense')
    CFO   = v.get('cfo')
    CAPEX = v.get('capex')
    DA    = v.get('depreciation_amort')
    INTANG = v.get('intangible_assets')

    # ── FOCF = EAT + D&A + CFO-based approach ──
    # Per methodology: FOCF = EAT + (D&A) + ΔWC + ΔCAPEX + ΔLTD
    # Simplified with available data: FOCF = CFO - CAPEX
    FOCF = None
    if CFO is not None and CAPEX is not None:
        FOCF = CFO - abs(CAPEX)  # CAPEX from yfinance is usually negative
    elif CFO is not None:
        FOCF = CFO

    # Capital = LTD + Equity
    CAPITAL = (LTD + NW) if (LTD and NW) else NW

    ratios: Dict[str, Optional[float]] = {}

    # ── 1. LIQUIDITY ──
    ratios['current_ratio']     = _safe_div(CA, CL)
    ratios['wc_leverage']       = _safe_div(CL, WC)
    cash = v.get('cash')
    ar   = v.get('accounts_receivable')
    quick_num = sum(x for x in [cash, ar] if x) if any([cash, ar]) else None
    ratios['quick_ratio']       = _safe_div(quick_num, CL)

    # ── 2. SOLVENCY ──
    ratios['interest_coverage'] = _safe_div(EBIT, INT)
    ratios['coverage_measure']  = _safe_div(EBITDA, INT)

    # ── 3. LEVERAGE ──
    ratios['ffo_to_total_debt']    = _safe_div(CFO, TL)
    ratios['ltd_to_capital']       = _safe_div(LTD, CAPITAL)
    ratios['total_debt_to_equity'] = _safe_div(TL, NW)
    ratios['debt_to_net_worth']    = _safe_div(TL, NW)
    tang_nw = (NW - INTANG) if (NW and INTANG) else NW
    ratios['debt_to_tangible_nw']  = _safe_div(TL, tang_nw)
    ratios['debt_to_assets']       = _safe_div(TL, TA)
    ratios['ltd_to_assets']        = _safe_div(LTD, TA)
    ratios['total_coverage_ratio'] = _safe_div(CA, TL)
    ratios['fixed_assets_ratio']   = _safe_div(FA, TA)

    # ── 4. EARNINGS ──
    ratios['pretax_roc']           = _safe_div(EBT, CAPITAL)
    ratios['op_income_to_sales']   = _safe_div(EBIT, SALES)
    ratios['roa']                  = _safe_div(EAT, TA)
    ratios['roe']                  = _safe_div(EAT, NW)
    ratios['gross_profit_margin']  = _safe_div(GP, SALES)
    ratios['net_profit_margin']    = _safe_div(EAT, SALES)
    ratios['operating_leverage']   = _safe_div(GP, EBT)
    ratios['operating_profit']     = _safe_div(EBIT, SALES)
    ratios['roi']                  = _safe_div(EAT, TA)

    # ── 5. EFFICIENCY ──
    ratios['asset_turnover']       = _safe_div(SALES, TA)
    ratios['cost_of_sales']        = _safe_div(COGS, SALES)
    ratios['overhead_ratio']       = _safe_div(SGA, SALES)

    # ── 6. CASH FLOW ADEQUACY (KEY RATIO #5) ──
    ratios['focf_to_total_debt']   = _safe_div(FOCF, TL)

    # Persist computed ratios
    for code, value in ratios.items():
        _upsert_ratio(db, period_id, code, value, defn_cache)

    db.flush()
    return ratios


def calculate_ratios_for_company(db: Session, company_id: int, year: int = None):
    """Calculate ratios for all periods of a company (or a specific year)."""
    query = db.query(FinancialPeriod).filter(FinancialPeriod.company_id == company_id)
    if year:
        query = query.filter(FinancialPeriod.fiscal_year == year)
    periods = query.all()

    for period in periods:
        try:
            ratios = calculate_ratios_for_period(db, period.id)
            db.commit()
            log.info(f"  Ratios computed for period {period.id} ({period.fiscal_year} {period.period_type})")
        except Exception as e:
            db.rollback()
            log.error(f"  Failed for period {period.id}: {e}")

    return len(periods)


def run_ratio_calculation_all(db: Session):
    """Compute ratios for all periods in the database."""
    periods = db.query(FinancialPeriod).all()
    log.info(f"Computing ratios for {len(periods)} periods...")
    ok = 0
    for period in periods:
        try:
            calculate_ratios_for_period(db, period.id)
            db.commit()
            ok += 1
        except Exception as e:
            db.rollback()
            log.warning(f"Period {period.id} failed: {e}")
    log.info(f"Done: {ok}/{len(periods)} periods computed.")
