"""
IDX Financial Statement Scraper — Direct Download from idx.co.id

Downloads official financial statements (xlsx) directly from IDX portal.
More reliable and accurate than yfinance for Indonesian listed companies.
"""
import os
import logging
import pandas as pd
import cloudscraper
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Sector, Company, FinancialPeriod, FinancialMetric,
    MetricDefinition, EtlLog,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# IDX base URL pattern for audited annual reports
IDX_BASE_URL = (
    "https://www.idx.co.id/Portals/0/StaticData/"
    "ListedCompanies/Corporate_Actions/New_Info_JSX/"
    "Jenis_Informasi/01_Laporan_Keuangan/"
    "02_Soft_Copy_Laporan_Keuangan/"
    "Laporan%20Keuangan%20Tahun%20{year}/Audit/"
)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../data/idx_reports")


def _create_scraper():
    """Create a cloudscraper instance that mimics a real browser."""
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    scraper.headers.update({"Referer": "https://www.idx.co.id/"})
    return scraper


def _get_ticker_list(db: Session, sector_filter: str = None, limit: int = None) -> list[str]:
    """Get tickers from DB or return all known tickers."""
    query = db.query(Company.ticker)
    if sector_filter:
        sector = db.query(Sector).filter(Sector.code == sector_filter.upper()).first()
        if sector:
            query = query.filter(Company.sector_id == sector.id)
    tickers = [r[0] for r in query.all()]

    if limit:
        tickers = tickers[:limit]

    return tickers


def _get_metric_definitions(db: Session) -> dict:
    """Load metric definition cache: code -> id"""
    defs = db.query(MetricDefinition).all()
    return {d.code: d.id for d in defs}


# ── Mapping: IDX xlsx column → our metric code ──────────
# These map common IDX financial statement column headers to our EAV metric codes.
# The actual headers vary by company, so we try multiple possible names.
BALANCE_SHEET_MAP = {
    "Kas dan Setara Kas": "cash_equivalent",
    "Cash and Cash Equivalents": "cash_equivalent",
    "Jumlah Aset Lancar": "current_assets",
    "Total Current Assets": "current_assets",
    "Jumlah Aset": "total_assets",
    "Total Assets": "total_assets",
    "Aset": "total_assets",
    "Piutang Usaha": "accounts_receivable",
    "Trade Receivables": "accounts_receivable",
    "Persediaan": "inventory",
    "Inventories": "inventory",
    "Jumlah Liabilitas Jangka Pendek": "current_liabilities",
    "Total Current Liabilities": "current_liabilities",
    "Jumlah Liabilitas Jangka Panjang": "long_term_debt",
    "Total Non-Current Liabilities": "long_term_debt",
    "Jumlah Liabilitas": "total_liabilities",
    "Total Liabilities": "total_liabilities",
    "Liabilitas": "total_liabilities",
    "Jumlah Ekuitas": "total_equity",
    "Total Equity": "total_equity",
    "Ekuitas": "total_equity",
}

INCOME_STATEMENT_MAP = {
    "Pendapatan": "total_revenue",
    "Revenue": "total_revenue",
    "Penjualan Neto": "total_revenue",
    "Net Revenue": "total_revenue",
    "Penjualan dan pendapatan usaha": "total_revenue",
    "Beban Pokok Penjualan": "total_cogs",
    "Cost of Revenue": "total_cogs",
    "Beban pokok penjualan dan pendapatan": "total_cogs",
    "Laba Bruto": "gross_profit",
    "Gross Profit": "gross_profit",
    "Jumlah laba bruto": "gross_profit",
    "Laba Usaha": "ebit",
    "Operating Income": "ebit",
    "Laba (rugi) usaha": "ebit",
    "Jumlah laba (rugi) usaha": "ebit",
    "Beban Bunga": "interest_expense",
    "Interest Expense": "interest_expense",
    "Beban bunga dan keuangan": "interest_expense",
    "Laba Sebelum Pajak": "ebt",
    "Income Before Tax": "ebt",
    "Laba (rugi) sebelum pajak penghasilan": "ebt",
    "Jumlah laba (rugi) sebelum pajak penghasilan": "ebt",
    "Laba Bersih": "net_income",
    "Net Income": "net_income",
    "Profit for the Period": "net_income",
    "Laba (rugi) tahun berjalan": "net_income",
    "Jumlah laba (rugi) tahun berjalan": "net_income",
    "Laba (rugi) bersih tahun berjalan": "net_income",
    "Laba (rugi) bersih": "net_income",
    "Laba (rugi) yang dapat diatribusikan ke entitas induk": "net_income",
}


def download_idx_report(ticker: str, year: int, scraper) -> str | None:
    """
    Download a financial statement xlsx from IDX.
    Returns the local file path if successful, None otherwise.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    base_url = IDX_BASE_URL.format(year=year)
    filename = f"FinancialStatement-{year}-Tahunan-{ticker}.xlsx"
    url = f"{base_url}{ticker}/{filename}"

    local_path = os.path.join(DOWNLOAD_DIR, f"{ticker}_{year}.xlsx")

    # Skip if already downloaded
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        log.info(f"  Already downloaded: {local_path}")
        return local_path

    try:
        log.info(f"  Downloading {ticker} ({year}) from IDX...")
        response = scraper.get(url, timeout=30)

        if response.status_code == 200 and len(response.content) > 1000:
            with open(local_path, "wb") as f:
                f.write(response.content)
            log.info(f"  SUCCESS: {ticker} -> {local_path}")
            return local_path
        else:
            log.warning(f"  FAILED: {ticker} (status={response.status_code}, size={len(response.content)})")
            return None
    except Exception as e:
        log.error(f"  ERROR downloading {ticker}: {e}")
        return None


def parse_idx_xlsx(filepath: str, db: Session, company: Company, year: int, defn_cache: dict):
    """
    Parse an IDX xlsx financial statement and store metrics in DB.
    """
    try:
        xls = pd.ExcelFile(filepath)
    except Exception as e:
        log.error(f"  Cannot open xlsx {filepath}: {e}")
        return False

    # Create or get period
    period = (
        db.query(FinancialPeriod)
        .filter(
            FinancialPeriod.company_id == company.id,
            FinancialPeriod.fiscal_year == year,
            FinancialPeriod.period_type == "annual",
        )
        .first()
    )
    if not period:
        period = FinancialPeriod(
            company_id=company.id,
            fiscal_year=year,
            period_type="annual",
            source="idx_direct",
        )
        db.add(period)
        db.flush()

    metrics_saved = 0

    # Try to find and parse each sheet
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            # Try to find the relevant data — IDX xlsx formats vary
            mapping = {k.lower(): v for k, v in {**BALANCE_SHEET_MAP, **INCOME_STATEMENT_MAP}.items()}
            for idx_row in range(len(df)):
                for idx_col in range(len(df.columns)):
                    cell_val = str(df.iloc[idx_row, idx_col]).strip().lower()
                    if cell_val in mapping:
                        metric_code = mapping[cell_val]
                        # Try to get the numeric value from the next column(s)
                        for val_col in range(idx_col + 1, min(idx_col + 5, len(df.columns))):
                            raw_val = df.iloc[idx_row, val_col]
                            try:
                                numeric_val = float(str(raw_val).replace(",", "").replace(" ", ""))
                                if metric_code in defn_cache:
                                    # Upsert metric
                                    existing = (
                                        db.query(FinancialMetric)
                                        .filter(
                                            FinancialMetric.period_id == period.id,
                                            FinancialMetric.metric_definition_id == defn_cache[metric_code],
                                        )
                                        .first()
                                    )
                                    if existing:
                                        existing.metric_value = numeric_val
                                    else:
                                        db.add(FinancialMetric(
                                            period_id=period.id,
                                            metric_definition_id=defn_cache[metric_code],
                                            metric_value=numeric_val,
                                            source="idx_direct",
                                        ))
                                    metrics_saved += 1
                                break
                            except (ValueError, TypeError):
                                continue
        except Exception as e:
            log.warning(f"  Error parsing sheet '{sheet_name}': {e}")
            continue

    if metrics_saved > 0:
        db.commit()
        log.info(f"  Parsed {metrics_saved} metrics for {company.ticker} ({year})")
    return metrics_saved > 0


def run_idx_download(
    sector_filter: str = None,
    year: int = 2024,
    limit: int = None,
    ticker_list: list[str] = None,
):
    """
    Main entry point: download financial statements from IDX and parse them.
    """
    db = SessionLocal()
    scraper = _create_scraper()
    defn_cache = _get_metric_definitions(db)

    start = datetime.utcnow()

    if ticker_list:
        tickers = [t.upper().strip() for t in ticker_list]
    else:
        tickers = _get_ticker_list(db, sector_filter, limit)

    if not tickers:
        log.warning("No tickers found. Run the basic ETL first to populate companies.")
        db.close()
        return

    log.info(f"IDX Direct Download: {len(tickers)} tickers for year {year}")

    success = 0
    failed = 0

    for ticker in tickers:
        # Ensure company exists
        company = db.query(Company).filter(Company.ticker == ticker).first()
        if not company:
            company = Company(ticker=ticker, name=f"{ticker} (IDX)")
            db.add(company)
            db.flush()

        filepath = download_idx_report(ticker, year, scraper)
        if filepath:
            ok = parse_idx_xlsx(filepath, db, company, year, defn_cache)
            if ok:
                success += 1
            else:
                failed += 1
        else:
            failed += 1

    # Log ETL run
    duration = (datetime.utcnow() - start).total_seconds()
    etl_log = EtlLog(
        source="idx_direct",
        tickers_total=len(tickers),
        tickers_success=success,
        tickers_failed=failed,
        duration_secs=duration,
    )
    db.add(etl_log)
    db.commit()

    log.info(f"IDX Download complete: {success}/{len(tickers)} success, {duration:.1f}s")
    db.close()
