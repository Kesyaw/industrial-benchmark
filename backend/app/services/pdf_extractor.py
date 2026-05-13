import pdfplumber
import re
from app.schemas import FinancialData

def extract_financial_data_from_pdf(pdf_path: str, filename: str) -> FinancialData:
    """
    Extracts financial data from a PDF file using basic keyword heuristics.
    Note: Real-world annual reports are highly unstructured and complex.
    This is a basic ETL demonstration that attempts to find numerical values near keywords.
    """
    extracted_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from the first 20 pages (usually where summary financials are)
        # to avoid scanning hundreds of pages unnecessarily
        for i, page in enumerate(pdf.pages[:20]):
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    
    # Heuristic parsing (Very basic mock-up)
    # In a real system, we'd use NLP/LLM or strict table parsing coordinates
    
    def find_value_near_keyword(keyword: str, text: str, default: float = 0.0) -> float:
        # Look for the keyword, then find the first number that follows it
        pattern = re.compile(rf"(?:{keyword}).*?([\d\.,]+)", re.IGNORECASE | re.DOTALL)
        match = pattern.search(text)
        if match and match.group(1):
            # Clean the number string (remove dots for thousands separator, replace comma with dot)
            num_str = match.group(1).replace(".", "").replace(",", ".")
            try:
                return float(num_str)
            except ValueError:
                pass
        return default

    # Searching for Indonesian financial keywords
    company_name = filename.replace(".pdf", "")
    current_assets = find_value_near_keyword(r"Aset Lancar|Total Aset Lancar|Jumlah Aset Lancar", extracted_text, 1000000.0)
    current_liabilities = find_value_near_keyword(r"Liabilitas Jangka Pendek|Total Liabilitas Lancar", extracted_text, 500000.0)
    ebit = find_value_near_keyword(r"Laba Usaha|Laba Sebelum Beban Pajak", extracted_text, 250000.0)
    interest_expense = find_value_near_keyword(r"Beban Keuangan|Beban Bunga", extracted_text, 0.0)
    total_debt = find_value_near_keyword(r"Total Liabilitas|Jumlah Liabilitas", extracted_text, 1200000.0)
    total_equity = find_value_near_keyword(r"Total Ekuitas|Jumlah Ekuitas", extracted_text, 3000000.0)
    focf = find_value_near_keyword(r"Kas Neto yang Diperoleh dari Aktivitas Operasi|Arus Kas Operasi", extracted_text, 300000.0)

    # Note: If values are 0 (not found), we inject some mock data to allow testing
    # Since we don't have the actual PDF yet, this ensures the system doesn't crash on division by zero
    if current_assets == 0: current_assets = 1000000.0
    if current_liabilities == 0: current_liabilities = 500000.0
    if total_equity == 0: total_equity = 3000000.0

    return FinancialData(
        company_name=company_name,
        sector_code="TRADE",  # default — user can change later
        current_assets=current_assets,
        current_liabilities=current_liabilities,
        ebit=ebit,
        interest_expense=interest_expense,
        ebitda=ebit,  # approximate — D&A not extracted from PDF yet
        total_debt=total_debt,
        total_equity=total_equity,
        long_term_debt=0.0,
        total_assets=current_assets + total_debt,  # rough estimate
        gross_profit=0.0,
        net_income=0.0,
        revenue=0.0,
        free_operating_cash_flow=focf
    )
