"""
IDX ETL Scraper — pulls all listed companies from idx.co.id (free API)
then fetches financial statements via yfinance for each ticker.

Usage:
    python -m app.etl.idx_scraper
    python -m app.etl.idx_scraper --sector TRADE --year 2023
"""
import time
import logging
import argparse
from datetime import date, datetime
from typing import Optional

import requests
import yfinance as yf
from tqdm import tqdm
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Company, Sector, FinancialPeriod, FinancialMetric, MetricDefinition, EtlLog

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
# IDX Free API — returns all listed companies
# ─────────────────────────────────────────
IDX_COMPANY_LIST_URL = (
    "https://www.idx.co.id/primary/ListedCompany/GetCompanyProfiles"
    "?start=0&length=9999&json=true"
)

# IDX sector name → our sector code mapping
IDX_SECTOR_MAP = {
    "Consumer Goods Industry":      "CONSUMER",
    "Basic Industry and Chemicals": "BASIC_IND",
    "Miscellaneous Industry":       "MISC_IND",
    "Infrastructure, Utilities":    "INFRA",
    "Finance":                      "FINANCE",
    "Trade, Services":              "SERVICES",
    "Mining":                       "MINING",
    "Agriculture":                  "AGRI",
    "Property, Real Estate":        "PROPERTY",
    "Transportation":               "TRANSPORT",
    "Banking":                      "BANKING",
    "Chemical":                     "CHEMICAL",
    "Building Construction":        "CONSTRUCT",
    "Investment":                   "INVESTMENT",
    "Trade":                        "TRADE",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IDX-Benchmark-ETL/1.0)",
    "Accept": "application/json",
}


def fetch_idx_company_list() -> list[dict]:
    """Fetch all listed companies from IDX free API."""
    log.info("Fetching company list from IDX API...")
    try:
        resp = requests.get(IDX_COMPANY_LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        companies = data.get("data", [])
        log.info(f"  → {len(companies)} companies fetched from IDX")
        return companies
    except Exception as e:
        log.error(f"IDX API failed: {e}. Falling back to known ticker list.")
        return []


def get_sector_id(db: Session, sector_name: str) -> Optional[int]:
    """Map IDX sector name to our sector id."""
    code = None
    for k, v in IDX_SECTOR_MAP.items():
        if k.lower() in sector_name.lower():
            code = v
            break
    if not code:
        code = "MISC_IND"  # default fallback
    sector = db.query(Sector).filter(Sector.code == code).first()
    return sector.id if sector else None


def upsert_company(db: Session, ticker: str, name: str, sector_name: str) -> Optional[Company]:
    """Create or update a company record."""
    sector_id = get_sector_id(db, sector_name)
    company = db.query(Company).filter(Company.ticker == ticker).first()
    if not company:
        company = Company(ticker=ticker, name=name, sector_id=sector_id, is_active=True)
        db.add(company)
    else:
        company.name = name
        company.sector_id = sector_id
    db.flush()
    return company


def get_or_create_period(db: Session, company_id: int, year: int, period_type: str) -> FinancialPeriod:
    """Get or create a financial period record."""
    from app.models import PeriodTypeEnum
    period = db.query(FinancialPeriod).filter(
        FinancialPeriod.company_id == company_id,
        FinancialPeriod.fiscal_year == year,
        FinancialPeriod.period_type == period_type,
    ).first()
    if not period:
        period = FinancialPeriod(
            company_id=company_id,
            fiscal_year=year,
            period_type=period_type,
            period_end_date=date(year, 12, 31),
            source="yfinance",
            is_audited=False,
        )
        db.add(period)
        db.flush()
    return period


def upsert_metric(db: Session, period_id: int, code: str, value, raw: str = None):
    """Upsert a single financial metric value."""
    defn = db.query(MetricDefinition).filter(MetricDefinition.code == code).first()
    if not defn:
        return
    existing = db.query(FinancialMetric).filter(
        FinancialMetric.period_id == period_id,
        FinancialMetric.metric_definition_id == defn.id,
    ).first()
    if existing:
        existing.metric_value = value
        existing.raw_value = str(raw or value)
    else:
        db.add(FinancialMetric(
            period_id=period_id,
            metric_definition_id=defn.id,
            metric_value=value,
            raw_value=str(raw or value),
            is_computed=False,
        ))


def safe_get(df, key: str, col_idx: int = 0):
    """Safely extract a value from a yfinance DataFrame."""
    try:
        if df is None or df.empty:
            return None
        # Find rows matching key (case-insensitive partial match)
        matches = [r for r in df.index if key.lower() in str(r).lower()]
        if not matches:
            return None
        val = df.loc[matches[0]].iloc[col_idx]
        if val is None:
            return None
        return float(val)
    except Exception:
        return None


def pull_financials_yfinance(ticker_jk: str, year: int, db: Session, company_id: int):
    """Pull balance sheet, income statement, cash flow from yfinance and store."""
    try:
        stock = yf.Ticker(ticker_jk)
        bs = stock.balance_sheet     # columns = fiscal year dates
        inc = stock.financials
        cf = stock.cashflow

        # Find column index for the target year
        def find_col(df, target_year):
            if df is None or df.empty:
                return None
            for i, col in enumerate(df.columns):
                if hasattr(col, 'year') and col.year == target_year:
                    return i
            return 0  # fallback to most recent

        bs_col = find_col(bs, year)
        inc_col = find_col(inc, year)
        cf_col = find_col(cf, year)

        period = get_or_create_period(db, company_id, year, "annual")

        # ── Balance Sheet ──
        upsert_metric(db, period.id, 'cash',                 safe_get(bs, 'Cash', bs_col))
        upsert_metric(db, period.id, 'accounts_receivable',  safe_get(bs, 'Receivable', bs_col))
        upsert_metric(db, period.id, 'inventory',            safe_get(bs, 'Inventory', bs_col))
        upsert_metric(db, period.id, 'total_current_assets', safe_get(bs, 'Current Assets', bs_col))
        upsert_metric(db, period.id, 'fixed_assets_net',     safe_get(bs, 'Net PPE', bs_col))
        upsert_metric(db, period.id, 'intangible_assets',    safe_get(bs, 'Intangible', bs_col))
        upsert_metric(db, period.id, 'total_assets',         safe_get(bs, 'Total Assets', bs_col))
        upsert_metric(db, period.id, 'total_current_liab',   safe_get(bs, 'Current Liabilities', bs_col))
        upsert_metric(db, period.id, 'total_ltd',            safe_get(bs, 'Long Term Debt', bs_col))
        upsert_metric(db, period.id, 'total_liabilities',    safe_get(bs, 'Total Liabilities', bs_col))
        upsert_metric(db, period.id, 'total_equity',         safe_get(bs, 'Stockholders Equity', bs_col))
        upsert_metric(db, period.id, 'paid_in_capital',      safe_get(bs, 'Common Stock', bs_col))
        upsert_metric(db, period.id, 'retained_earnings',    safe_get(bs, 'Retained Earnings', bs_col))

        # ── Income Statement ──
        upsert_metric(db, period.id, 'total_revenue',        safe_get(inc, 'Total Revenue', inc_col))
        upsert_metric(db, period.id, 'total_cogs',           safe_get(inc, 'Cost Of Revenue', inc_col))
        upsert_metric(db, period.id, 'gross_profit',         safe_get(inc, 'Gross Profit', inc_col))
        upsert_metric(db, period.id, 'ebitda',               safe_get(inc, 'EBITDA', inc_col))
        upsert_metric(db, period.id, 'ebit',                 safe_get(inc, 'EBIT', inc_col))
        upsert_metric(db, period.id, 'interest_expense',     safe_get(inc, 'Interest Expense', inc_col))
        upsert_metric(db, period.id, 'ebt',                  safe_get(inc, 'Pretax Income', inc_col))
        upsert_metric(db, period.id, 'income_tax',           safe_get(inc, 'Tax Provision', inc_col))
        upsert_metric(db, period.id, 'net_income',           safe_get(inc, 'Net Income', inc_col))
        upsert_metric(db, period.id, 'depreciation_amort',   safe_get(inc, 'Reconciled Depreciation', inc_col))
        upsert_metric(db, period.id, 'admin_expense',        safe_get(inc, 'General And Administrative', inc_col))

        # ── Cash Flow ──
        upsert_metric(db, period.id, 'cfo',   safe_get(cf, 'Operating Cash Flow', cf_col))
        upsert_metric(db, period.id, 'capex', safe_get(cf, 'Capital Expenditure', cf_col))

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        log.warning(f"  [{ticker_jk}] yfinance error: {e}")
        return False


def run_etl(sector_filter: str = None, year: int = None, limit: int = None):
    """Main ETL loop — fetches all IDX companies and stores financials."""
    if year is None:
        year = datetime.now().year - 1  # default: previous year

    db: Session = SessionLocal()
    start_time = time.time()
    success_count = 0
    failed = []

    try:
        # Step 1: Get company list from IDX
        raw_companies = fetch_idx_company_list()

        if not raw_companies:
            log.warning("IDX API returned empty. Using yfinance ticker discovery.")
            # Fallback: use known IDX blue-chip tickers
            raw_companies = _fallback_ticker_list()

        # Step 2: Filter by sector if requested
        if sector_filter:
            raw_companies = [
                c for c in raw_companies
                if sector_filter.lower() in str(c.get("Sector", "")).lower()
            ]
            log.info(f"Filtered to {len(raw_companies)} companies in sector '{sector_filter}'")

        if limit:
            raw_companies = raw_companies[:limit]

        log.info(f"Starting ETL for {len(raw_companies)} companies, year={year}")

        # Step 3: Loop and pull
        for raw in tqdm(raw_companies, desc="Pulling IDX financials"):
            ticker = raw.get("StockCode", raw.get("ticker", "")).strip()
            name = raw.get("CompanyName", raw.get("name", ticker))
            sector_name = raw.get("Sector", raw.get("sector", "Miscellaneous"))

            if not ticker:
                continue

            ticker_jk = f"{ticker}.JK"

            try:
                company = upsert_company(db, ticker, name, sector_name)
                ok = pull_financials_yfinance(ticker_jk, year, db, company.id)
                if ok:
                    success_count += 1
                else:
                    failed.append(ticker)
            except Exception as e:
                db.rollback()
                log.error(f"  [{ticker}] Unexpected error: {e}")
                failed.append(ticker)

            time.sleep(0.3)  # rate-limit: be polite to yfinance

        duration = round(time.time() - start_time, 2)
        log.info(f"\n✅ ETL complete: {success_count}/{len(raw_companies)} ok | {len(failed)} failed | {duration}s")

        if failed:
            log.warning(f"Failed tickers: {failed[:20]}{'...' if len(failed) > 20 else ''}")

        # Log the run
        db.add(EtlLog(
            source="yfinance+idx_api",
            tickers_total=len(raw_companies),
            tickers_success=success_count,
            tickers_failed=len(failed),
            duration_secs=duration,
            error_details=str(failed[:50]) if failed else None,
        ))
        db.commit()

    finally:
        db.close()


def _fallback_ticker_list() -> list[dict]:
    """Fallback ticker list when IDX API is unavailable."""
    tickers = [
        # Banking
        {"StockCode": "BBCA", "CompanyName": "Bank Central Asia Tbk", "Sector": "Banking"},
        {"StockCode": "BBRI", "CompanyName": "Bank Rakyat Indonesia Tbk", "Sector": "Banking"},
        {"StockCode": "BMRI", "CompanyName": "Bank Mandiri Tbk", "Sector": "Banking"},
        {"StockCode": "BBNI", "CompanyName": "Bank Negara Indonesia Tbk", "Sector": "Banking"},
        {"StockCode": "BSDE", "CompanyName": "Bumi Serpong Damai Tbk", "Sector": "Property, Real Estate"},
        # Consumer Goods
        {"StockCode": "UNVR", "CompanyName": "Unilever Indonesia Tbk", "Sector": "Consumer Goods Industry"},
        {"StockCode": "ICBP", "CompanyName": "Indofood CBP Sukses Makmur Tbk", "Sector": "Consumer Goods Industry"},
        {"StockCode": "INDF", "CompanyName": "Indofood Sukses Makmur Tbk", "Sector": "Consumer Goods Industry"},
        {"StockCode": "HMSP", "CompanyName": "HM Sampoerna Tbk", "Sector": "Consumer Goods Industry"},
        # Telecom / Infra
        {"StockCode": "TLKM", "CompanyName": "Telekomunikasi Indonesia Tbk", "Sector": "Infrastructure, Utilities"},
        {"StockCode": "EXCL",  "CompanyName": "XL Axiata Tbk", "Sector": "Infrastructure, Utilities"},
        # Mining
        {"StockCode": "ANTM", "CompanyName": "Aneka Tambang Tbk", "Sector": "Mining"},
        {"StockCode": "PTBA", "CompanyName": "Tambang Batubara Bukit Asam Tbk", "Sector": "Mining"},
        {"StockCode": "ADRO", "CompanyName": "Adaro Energy Indonesia Tbk", "Sector": "Mining"},
        # Agriculture
        {"StockCode": "AALI", "CompanyName": "Astra Agro Lestari Tbk", "Sector": "Agriculture"},
        {"StockCode": "LSIP", "CompanyName": "PP London Sumatra Indonesia Tbk", "Sector": "Agriculture"},
        # Trade
        {"StockCode": "MAPI", "CompanyName": "Mitra Adiperkasa Tbk", "Sector": "Trade"},
        {"StockCode": "RALS", "CompanyName": "Ramayana Lestari Sentosa Tbk", "Sector": "Trade"},
        # Property
        {"StockCode": "CTRA", "CompanyName": "Ciputra Development Tbk", "Sector": "Property, Real Estate"},
        {"StockCode": "PWON", "CompanyName": "Pakuwon Jati Tbk", "Sector": "Property, Real Estate"},
    ]
    return tickers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IDX Financial Data ETL")
    parser.add_argument("--sector", type=str, default=None, help="Filter by sector name")
    parser.add_argument("--year",   type=int, default=None, help="Fiscal year (default: last year)")
    parser.add_argument("--limit",  type=int, default=None, help="Limit number of tickers (for testing)")
    args = parser.parse_args()
    run_etl(sector_filter=args.sector, year=args.year, limit=args.limit)
