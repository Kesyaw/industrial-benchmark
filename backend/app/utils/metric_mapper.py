"""
Metric Mapper Utility

Converts raw IDX metric codes (from DB) to FinancialData schema fields.
Centralizes the mapping logic to avoid duplication across endpoints.
"""
from app.schemas import FinancialData


# Maps DB metric codes → FinancialData field names
# Supports both IDX-specific codes and legacy English codes
_METRIC_MAP = {
    "current_assets":        ["aset_lancar", "current_assets"],
    "current_liabilities":   ["liabilitas_jangka_pendek", "current_liabilities"],
    "ebit":                  ["laba_rugi_sebelum_pajak_penghasilan", "ebit"],
    "ebitda":                ["laba_rugi_sebelum_pajak_penghasilan", "ebitda"],
    "total_debt":            ["liabilitas", "total_debt"],
    "total_equity":          ["ekuitas", "total_equity"],
    "long_term_debt":        ["liabilitas_jangka_panjang", "long_term_debt"],
    "total_assets":          ["aset", "total_assets"],
    "gross_profit":          ["jumlah_laba_kotor", "gross_profit"],
    "net_income":            ["laba_rugi_tahun_berjalan", "net_income"],
    "revenue":               ["penjualan_dan_pendapatan_usaha", "revenue"],
    "free_operating_cash_flow": ["laba_rugi_tahun_berjalan", "free_operating_cash_flow"],
    "interest_expense":      ["interest_expense"],
}


def _resolve(extracted: dict, candidates: list, default: float = 0.0) -> float:
    """Return first non-zero match from candidate keys in extracted metrics."""
    for key in candidates:
        val = extracted.get(key)
        if val is not None and val != 0.0:
            return val
    return default


def build_financial_data(ticker: str, sector_code: str, extracted: dict) -> FinancialData:
    """
    Build a FinancialData object from a flat dict of DB metric codes → values.

    Args:
        ticker: Company ticker symbol (used as company_name).
        sector_code: Sector code for benchmark threshold lookup.
        extracted: Dict mapping metric_definition.code → float value.

    Returns:
        FinancialData ready for calculate_benchmark().
    """
    return FinancialData(
        company_name=ticker,
        sector_code=sector_code,
        current_assets=          _resolve(extracted, _METRIC_MAP["current_assets"]),
        current_liabilities=     _resolve(extracted, _METRIC_MAP["current_liabilities"]),
        ebit=                    _resolve(extracted, _METRIC_MAP["ebit"]),
        interest_expense=        _resolve(extracted, _METRIC_MAP["interest_expense"]),
        ebitda=                  _resolve(extracted, _METRIC_MAP["ebitda"]),
        total_debt=              _resolve(extracted, _METRIC_MAP["total_debt"]),
        total_equity=            _resolve(extracted, _METRIC_MAP["total_equity"]),
        long_term_debt=          _resolve(extracted, _METRIC_MAP["long_term_debt"]),
        total_assets=            _resolve(extracted, _METRIC_MAP["total_assets"]),
        gross_profit=            _resolve(extracted, _METRIC_MAP["gross_profit"]),
        net_income=              _resolve(extracted, _METRIC_MAP["net_income"]),
        revenue=                 _resolve(extracted, _METRIC_MAP["revenue"]),
        free_operating_cash_flow=_resolve(extracted, _METRIC_MAP["free_operating_cash_flow"]),
    )
