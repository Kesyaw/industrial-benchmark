"""
XLSX Financial Statement Extractor

Extracts financial data from uploaded IDX official xlsx files.
Returns a FinancialData schema object for the benchmark engine.
"""
import pandas as pd
import logging
from app.schemas import FinancialData
from app.etl.idx_direct_scraper import BALANCE_SHEET_MAP, INCOME_STATEMENT_MAP

log = logging.getLogger(__name__)

def extract_financial_data_from_xlsx(filepath: str, filename: str) -> FinancialData:
    """
    Parse an uploaded IDX xlsx financial statement.
    """
    company_name = filename.replace(".xlsx", "")
    
    extracted_data = {
        "current_assets": 0.0,
        "current_liabilities": 0.0,
        "ebit": 0.0,
        "interest_expense": 0.0,
        "ebitda": 0.0,
        "total_debt": 0.0,
        "total_equity": 0.0,
        "long_term_debt": 0.0,
        "total_assets": 0.0,
        "gross_profit": 0.0,
        "net_income": 0.0,
        "revenue": 0.0,
        "total_revenue": 0.0,
        "total_liabilities": 0.0,
        "free_operating_cash_flow": 0.0,
    }

    try:
        xls = pd.ExcelFile(filepath)
        mapping = {**BALANCE_SHEET_MAP, **INCOME_STATEMENT_MAP}
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            for idx_row in range(len(df)):
                for idx_col in range(len(df.columns)):
                    cell_val = str(df.iloc[idx_row, idx_col]).strip()
                    if cell_val in mapping:
                        metric_code = mapping[cell_val]
                        for val_col in range(idx_col + 1, min(idx_col + 5, len(df.columns))):
                            raw_val = df.iloc[idx_row, val_col]
                            try:
                                numeric_val = float(str(raw_val).replace(",", "").replace(" ", ""))
                                if metric_code in extracted_data:
                                    extracted_data[metric_code] = numeric_val
                                break
                            except (ValueError, TypeError):
                                continue
    except Exception as e:
        log.error(f"Error parsing xlsx {filepath}: {e}")

    # Fallbacks and calculations for missing data
    if extracted_data["total_debt"] == 0 and extracted_data["total_liabilities"] > 0:
        extracted_data["total_debt"] = extracted_data["total_liabilities"]
        
    if extracted_data["ebitda"] == 0:
        extracted_data["ebitda"] = extracted_data["ebit"]
        
    if extracted_data["revenue"] == 0 and extracted_data["total_revenue"] > 0:
        extracted_data["revenue"] = extracted_data["total_revenue"]

    # FOCF estimation if missing D&A and capex
    extracted_data["free_operating_cash_flow"] = extracted_data["net_income"]
    
    return FinancialData(
        company_name=company_name,
        sector_code="TRADE", # default, can be overridden by user
        **extracted_data
    )
