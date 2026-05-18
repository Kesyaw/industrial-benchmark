"""
IDX Data Extraction Script

Extracts Current Year and Prior Year financial data from IDX XLSX reports
and saves them as CSV files with Period column (Current/Prior).

Usage:
    python backend/scripts/extract_idx_data.py
"""
import pandas as pd
import glob
import os

# ── Paths (relative to this script's location) ─────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR   = os.path.join(_SCRIPT_DIR, "..", "data", "idx_reports")
OUTPUT_DIR  = os.path.join(_SCRIPT_DIR, "..", "data", "processed")

# ── Variables to extract per sheet ─────────────────────────────────────────
VARS_1000000 = [
    "Nama entitas", "Kode entitas", "Sektor", "Subsektor", "Industri", "Subindustri"
]

VARS_1210000 = [
    "Aset", "Aset lancar", "Aset tidak lancar",
    "Liabilitas", "Liabilitas jangka pendek", "Liabilitas jangka panjang",
    "Ekuitas", "Kas dan setara kas", "Piutang usaha", "Persediaan",
]

VARS_1321000 = [
    "Penjualan dan pendapatan usaha", "Beban pokok penjualan dan pendapatan",
    "Jumlah laba kotor", "Laba (rugi) sebelum pajak penghasilan",
    "Laba (rugi) tahun berjalan",
]

VARS_1410000 = [
    "Posisi ekuitas", "Laba (rugi)", "Total komprehensif"
]


def _find_row_value(df: pd.DataFrame, var: str, col_idx: int) -> object:
    """Find a variable row and return value at col_idx. Tries exact then prefix match."""
    var_lower = var.lower()
    for row_idx in range(len(df)):
        cell = str(df.iloc[row_idx, 0]).strip().lower()
        if cell == var_lower or cell.startswith(var_lower):
            return df.iloc[row_idx, col_idx] if col_idx < len(df.columns) else None
    return None


def _extract_general_info(df: pd.DataFrame, variables: list) -> dict:
    """Extract single-column general info (sheet 1000000)."""
    return {var: _find_row_value(df, var, col_idx=1) for var in variables}


def _extract_two_period(df: pd.DataFrame, variables: list) -> tuple[dict, dict]:
    """
    Extract Current Year (col 1) and Prior Year (col 2) for financial sheets.
    Returns a tuple of (current_dict, prior_dict).
    """
    current = {var: _find_row_value(df, var, col_idx=1) for var in variables}
    prior   = {var: _find_row_value(df, var, col_idx=2) for var in variables}
    return current, prior


def _extract_equity_changes(df: pd.DataFrame, variables: list) -> dict:
    """Extract equity column data from sheet 1410000."""
    ekuitas_col = None
    for row_idx in range(min(15, len(df))):
        for col_idx in range(len(df.columns)):
            if str(df.iloc[row_idx, col_idx]).strip().lower() == "ekuitas":
                ekuitas_col = col_idx
                break
        if ekuitas_col is not None:
            break

    if ekuitas_col is None:
        ekuitas_col = len(df.columns) - 2

    return {var: _find_row_value(df, var, col_idx=ekuitas_col) for var in variables}


def _read_sheet(filepath: str, sheet_name: str) -> pd.DataFrame | None:
    """Safely read an Excel sheet. Returns None on error."""
    try:
        return pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    except Exception:
        return None


def _reorder_columns(df: pd.DataFrame, first_cols: list) -> pd.DataFrame:
    """Move specified columns to the front."""
    remaining = [c for c in df.columns if c not in first_cols]
    return df[first_cols + remaining]


def process_file(filepath: str) -> dict:
    """
    Process a single IDX XLSX file.
    Returns a dict with keys: info, balance_sheet (list of 2), income (list of 2), equity.
    """
    filename = os.path.basename(filepath)
    ticker   = filename.replace(".xlsx", "")

    result = {
        "info": None,
        "balance_sheet": [],
        "income":        [],
        "equity":        [],
    }

    # General info — single record
    df = _read_sheet(filepath, "1000000")
    if df is not None:
        row = _extract_general_info(df, VARS_1000000)
        row.update({"Ticker": ticker, "File": filename})
        result["info"] = row

    # Balance sheet — two periods
    df = _read_sheet(filepath, "1210000")
    if df is not None:
        curr, prior = _extract_two_period(df, VARS_1210000)
        for rec, period_label in [(curr, "Current"), (prior, "Prior")]:
            rec.update({"Ticker": ticker, "File": filename, "Period": period_label})
            result["balance_sheet"].append(rec)

    # Income statement — two periods
    df = _read_sheet(filepath, "1321000")
    if df is not None:
        curr, prior = _extract_two_period(df, VARS_1321000)
        for rec, period_label in [(curr, "Current"), (prior, "Prior")]:
            rec.update({"Ticker": ticker, "File": filename, "Period": period_label})
            result["income"].append(rec)

    # Equity changes — single period (current only)
    df = _read_sheet(filepath, "1410000")
    if df is not None:
        row = _extract_equity_changes(df, VARS_1410000)
        row.update({"Ticker": ticker, "File": filename, "Period": "Current"})
        result["equity"].append(row)

    return result


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    print(f"Found {len(files)} files to process.")

    all_info, all_balance, all_income, all_equity = [], [], [], []

    for i, filepath in enumerate(files):
        if i % 50 == 0:
            print(f"  Processing {i + 1}/{len(files)}...")
        data = process_file(filepath)
        if data["info"]:
            all_info.append(data["info"])
        all_balance.extend(data["balance_sheet"])
        all_income.extend(data["income"])
        all_equity.extend(data["equity"])

    # Build DataFrames and reorder columns
    df_info    = _reorder_columns(pd.DataFrame(all_info),    ["Ticker", "File"])
    df_balance = _reorder_columns(pd.DataFrame(all_balance), ["Ticker", "File", "Period"])
    df_income  = _reorder_columns(pd.DataFrame(all_income),  ["Ticker", "File", "Period"])
    df_equity  = _reorder_columns(pd.DataFrame(all_equity),  ["Ticker", "File", "Period"])

    # Save to CSV
    df_info.to_csv(   os.path.join(OUTPUT_DIR, "benchmark_1000000.csv"), index=False)
    df_balance.to_csv(os.path.join(OUTPUT_DIR, "benchmark_1210000.csv"), index=False)
    df_income.to_csv( os.path.join(OUTPUT_DIR, "benchmark_1321000.csv"), index=False)
    df_equity.to_csv( os.path.join(OUTPUT_DIR, "benchmark_1410000.csv"), index=False)

    print(f"\nExtraction complete. Output → {OUTPUT_DIR}")
    print(f"  benchmark_1000000.csv : {len(df_info)} rows")
    print(f"  benchmark_1210000.csv : {len(df_balance)} rows ({len(df_balance)//2} companies × 2 periods)")
    print(f"  benchmark_1321000.csv : {len(df_income)} rows")
    print(f"  benchmark_1410000.csv : {len(df_equity)} rows")


if __name__ == "__main__":
    main()
