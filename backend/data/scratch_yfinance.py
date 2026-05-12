import yfinance as yf

tickers = ["BBCA.JK", "TLKM.JK"]

for t in tickers:
    stock = yf.Ticker(t)
    bs = stock.balance_sheet
    inc = stock.financials
    cf = stock.cashflow
    print(f"--- {t} ---")
    if not bs.empty:
        print("Balance Sheet available")
    if not inc.empty:
        print("Income Statement available")
    if not cf.empty:
        print("Cashflow available")
