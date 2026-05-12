from app.schemas import FinancialData, BenchmarkResult

def calculate_benchmark(data: FinancialData) -> BenchmarkResult:
    # 1. Current ratio = Current Assets / Current Liabilities
    current_ratio = data.current_assets / data.current_liabilities if data.current_liabilities != 0 else 0
    
    # 2. Interest coverage = EBIT / Interest Expense
    interest_coverage = data.ebit / data.interest_expense if data.interest_expense != 0 else 0
    
    # 3. Total debt to equity = Total Debt / Total Equity
    total_debt_to_equity = data.total_debt / data.total_equity if data.total_equity != 0 else 0
    
    # 4. Debt to capitalization = Total Debt / (Total Debt + Total Equity)
    total_capitalization = data.total_debt + data.total_equity
    debt_to_capitalization = data.total_debt / total_capitalization if total_capitalization != 0 else 0
    
    # 5. Free operating cash flow to total debt = FOCF / Total Debt
    focf_to_total_debt = data.free_operating_cash_flow / data.total_debt if data.total_debt != 0 else 0

    ratios = {
        "current_ratio": round(current_ratio, 2),
        "interest_coverage": round(interest_coverage, 2),
        "total_debt_to_equity": round(total_debt_to_equity, 2),
        "debt_to_capitalization": round(debt_to_capitalization, 2),
        "focf_to_total_debt": round(focf_to_total_debt, 2)
    }

    # Scoring Mechanism (Placeholder thresholds)
    # The higher the current ratio, the better (liquidity)
    cr_score = 100 if current_ratio >= 2.0 else (80 if current_ratio >= 1.5 else 60)
    
    # The higher the interest coverage, the better (solvency)
    # If there's no interest expense, it's very safe, give max score
    ic_score = 100 if data.interest_expense == 0 else (100 if interest_coverage >= 5.0 else (80 if interest_coverage >= 3.0 else 60))
    
    # The lower the debt to equity, the better
    der_score = 100 if total_debt_to_equity <= 0.5 else (80 if total_debt_to_equity <= 1.0 else 60)
    
    # The lower the debt to capitalization, the better
    dtc_score = 100 if debt_to_capitalization <= 0.3 else (80 if debt_to_capitalization <= 0.5 else 60)
    
    # The higher the FOCF to debt, the better
    focf_score = 100 if focf_to_total_debt >= 1.0 else (80 if focf_to_total_debt >= 0.5 else 60)

    scores = {
        "current_ratio_score": cr_score,
        "interest_coverage_score": ic_score,
        "total_debt_to_equity_score": der_score,
        "debt_to_capitalization_score": dtc_score,
        "focf_to_total_debt_score": focf_score
    }

    # Calculate average score
    average_score = sum(scores.values()) / len(scores)

    # Determine health predicate (Placeholder ranges)
    if average_score >= 90:
        predicate = "Sangat Sehat"
    elif average_score >= 75:
        predicate = "Sehat"
    elif average_score >= 60:
        predicate = "Cukup Sehat"
    elif average_score >= 45:
        predicate = "Kurang Sehat"
    else:
        predicate = "Tidak Sehat"

    return BenchmarkResult(
        company=data.company_name,
        ratios=ratios,
        scores=scores,
        average_score=round(average_score, 2),
        health_predicate=predicate
    )
