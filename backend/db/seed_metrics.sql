-- ============================================================
-- SEED: Metric Definitions (28 ratios + balance sheet + income statement)
-- sector_id = NULL means applies to ALL sectors
-- ============================================================

-- Balance Sheet items
INSERT INTO metric_definitions (code, name_id, name_en, category, unit, is_key_ratio, sort_order) VALUES
('cash',                 'Kas & Setara Kas',              'Cash & Equivalents',         'balance_sheet', 'IDR', FALSE, 10),
('accounts_receivable',  'Piutang Usaha',                 'Accounts Receivable',         'balance_sheet', 'IDR', FALSE, 11),
('inventory',            'Persediaan',                    'Inventory',                   'balance_sheet', 'IDR', FALSE, 12),
('other_current_assets', 'Aset Lancar Lainnya',           'Other Current Assets',        'balance_sheet', 'IDR', FALSE, 13),
('total_current_assets', 'Total Aset Lancar',             'Total Current Assets (CA)',    'balance_sheet', 'IDR', FALSE, 14),
('fixed_assets_net',     'Aset Tetap Bersih',             'Net Fixed Assets (FA)',        'balance_sheet', 'IDR', FALSE, 15),
('intangible_assets',    'Aset Tidak Berwujud',           'Intangible Assets',           'balance_sheet', 'IDR', FALSE, 16),
('total_assets',         'Total Aset',                    'Total Assets (TA)',            'balance_sheet', 'IDR', FALSE, 17),
('accounts_payable',     'Hutang Usaha',                  'Accounts Payable',            'balance_sheet', 'IDR', FALSE, 20),
('short_term_bank_loan', 'Pinjaman Bank',                 'Short-Term Bank Loan',        'balance_sheet', 'IDR', FALSE, 21),
('accrued_expenses',     'Beban Yang Akan Dibayar',       'Accrued Expenses',            'balance_sheet', 'IDR', FALSE, 22),
('tax_payable',          'Pajak Yang Akan Dibayar',       'Tax Payable',                 'balance_sheet', 'IDR', FALSE, 23),
('other_current_liab',   'Hutang Lainnya',                'Other Current Liabilities',   'balance_sheet', 'IDR', FALSE, 24),
('total_current_liab',   'Total Kewajiban Lancar',        'Total Current Liabilities (CL)','balance_sheet','IDR',FALSE, 25),
('ltd_bank',             'Pinjaman Bank Jk Panjang',      'LT Bank Loan',                'balance_sheet', 'IDR', FALSE, 30),
('ltd_shareholder',      'Pinjaman Dari Pemegang Saham',  'Shareholder Loan',            'balance_sheet', 'IDR', FALSE, 31),
('ltd_other',            'Pinjaman Jk Panjang Lainnya',   'Other LTD',                   'balance_sheet', 'IDR', FALSE, 32),
('total_ltd',            'Total Hutang Jangka Panjang',   'Total Long-Term Debt (LTD)',   'balance_sheet', 'IDR', FALSE, 33),
('total_liabilities',    'Total Kewajiban',               'Total Liabilities (TL)',       'balance_sheet', 'IDR', FALSE, 34),
('paid_in_capital',      'Modal Disetor',                 'Paid-in Capital',             'balance_sheet', 'IDR', FALSE, 40),
('additional_capital',   'Tambahan Modal',                'Additional Paid-in Capital',  'balance_sheet', 'IDR', FALSE, 41),
('retained_earnings',    'Saldo Laba Yang Ditahan',       'Retained Earnings',           'balance_sheet', 'IDR', FALSE, 42),
('current_year_profit',  'Saldo Laba Tahun Berjalan',     'Current Year Profit',         'balance_sheet', 'IDR', FALSE, 43),
('total_equity',         'Total Modal / Ekuitas',         'Total Equity (NW)',            'balance_sheet', 'IDR', FALSE, 44)
ON CONFLICT (code) DO NOTHING;

-- Income Statement items
INSERT INTO metric_definitions (code, name_id, name_en, category, unit, is_key_ratio, sort_order) VALUES
('total_revenue',        'Total Penjualan',               'Total Revenue (Sales)',        'income_statement', 'IDR', FALSE, 60),
('total_cogs',           'HPP / Biaya Operasional',       'COGS / Total Operating Costs', 'income_statement', 'IDR', FALSE, 61),
('gross_profit',         'Gross Profit',                  'Gross Profit (GP)',            'income_statement', 'IDR', FALSE, 62),
('admin_expense',        'Biaya Administrasi & Umum',     'Admin & General Expenses (SGA)','income_statement','IDR', FALSE, 63),
('marketing_expense',    'Biaya Pemasaran',               'Marketing Expenses',          'income_statement', 'IDR', FALSE, 64),
('ebitda',               'EBITDA',                        'EBITDA',                      'income_statement', 'IDR', FALSE, 65),
('depreciation_amort',   'Amortisasi & Penyusutan',       'Depreciation & Amortization (D&A)', 'income_statement','IDR',FALSE,66),
('ebit',                 'EBIT / Laba Usaha',             'EBIT',                        'income_statement', 'IDR', FALSE, 67),
('interest_expense',     'Beban Bunga',                   'Interest Expense',            'income_statement', 'IDR', FALSE, 68),
('ebt',                  'EBT / Laba Sebelum Pajak',      'EBT',                         'income_statement', 'IDR', FALSE, 69),
('income_tax',           'Pajak',                         'Income Tax',                  'income_statement', 'IDR', FALSE, 70),
('net_income',           'EAT / Laba Bersih',             'Net Income (EAT)',             'income_statement', 'IDR', FALSE, 71)
ON CONFLICT (code) DO NOTHING;

-- Cash Flow items
INSERT INTO metric_definitions (code, name_id, name_en, category, unit, formula, is_key_ratio, sort_order) VALUES
('cfo',   'Arus Kas dari Operasi',    'Cash from Operations', 'cash_flow', 'IDR', NULL, FALSE, 80),
('capex', 'Belanja Modal',            'Capital Expenditure',  'cash_flow', 'IDR', NULL, FALSE, 81),
('focf',  'Arus Kas Operasi Bebas',   'Free Operating Cash Flow (FOCF)', 'cash_flow', 'IDR',
          'EAT + D&A + ΔWC + ΔCAPEX + ΔLTD', FALSE, 82)
ON CONFLICT (code) DO NOTHING;

-- 28 Financial Ratios (computed)
INSERT INTO metric_definitions (code, name_id, name_en, category, unit, formula, is_key_ratio, sort_order) VALUES
-- Liquidity
('current_ratio',        'Current Ratio',                         'Current Ratio',          'ratio','ratio',    'CA / CL',                    TRUE,  200),
('wc_leverage',          'Working Capital Leverage (CL/WC)',      'WC Leverage',            'ratio','ratio',    'CL / (CA-CL)',               FALSE, 201),
('quick_ratio',          'Quick Ratio',                           'Quick Ratio',            'ratio','ratio',    '(Cash+AR) / CL',             FALSE, 202),
-- Solvency
('interest_coverage',    'Times Interest Earned (EBIT/Interest)', 'Interest Coverage',      'ratio','times',    'EBIT / Interest',            TRUE,  210),
('coverage_measure',     'Coverage Measure (EBITDA/Interest)',    'EBITDA Coverage',        'ratio','times',    'EBITDA / Interest',          FALSE, 211),
-- Leverage
('ffo_to_total_debt',    'Funds from Operations to Total Debt',   'FFO / Total Debt',       'ratio','ratio',    'CFO / TL',                   FALSE, 220),
('ltd_to_capital',       'Long Term Debt to Capital',             'LTD / Capital',          'ratio','ratio',    'LTD / (LTD+Equity)',         FALSE, 221),
('total_debt_to_equity', 'Total Debt to Equity',                  'Total D/E',              'ratio','ratio',    'TL / NW',                    TRUE,  222),
('debt_to_net_worth',    'Debt to Net Worth (TL/NW)',             'Debt / NW',              'ratio','ratio',    'TL / NW',                    TRUE,  223),
('debt_to_tangible_nw',  'Debt to Tangible Net Worth',            'Debt / Tangible NW',     'ratio','ratio',    'TL / (Eq - Intangibles)',    FALSE, 224),
('debt_to_assets',       'Debt to Assets',                        'Debt / TA',              'ratio','ratio',    'TL / TA',                    FALSE, 225),
('ltd_to_assets',        'LT Debt to Total Assets',               'LTD / TA',               'ratio','ratio',    'LTD / TA',                   FALSE, 226),
('total_coverage_ratio', 'Total Coverage Ratio (CA/TL)',          'CA / TL',                'ratio','ratio',    'CA / TL',                    FALSE, 227),
('fixed_assets_ratio',   'Fixed Assets to Total Assets',          'FA / TA',                'ratio','ratio',    'Net FA / TA',                FALSE, 228),
-- Earnings
('pretax_roc',           'Pretax Return on Capital',              'Pretax ROC',             'ratio','percentage','EBT / Capital',             FALSE, 230),
('op_income_to_sales',   'Operating Income to Sales',             'EBIT / Sales',           'ratio','percentage','EBIT / Sales',              FALSE, 231),
('roa',                  'Return on Assets (RoA)',                'ROA',                    'ratio','percentage','EAT / TA',                  FALSE, 232),
('roe',                  'Return on Equity (RoE)',                'ROE',                    'ratio','percentage','EAT / Equity',              FALSE, 233),
('gross_profit_margin',  'Gross Profit Margin (Gross PM)',        'GPM',                    'ratio','percentage','GP / Sales',                FALSE, 234),
('net_profit_margin',    'Net Profit Margin (Net PM)',            'NPM',                    'ratio','percentage','EAT / Sales',               FALSE, 235),
('operating_leverage',   'Operating Leverage (GP/EBT)',           'Op Leverage',            'ratio','ratio',    'GP / EBT',                   FALSE, 236),
('operating_profit',     'Operating Profit',                      'Operating Profit Margin','ratio','percentage','EBIT / Sales',              FALSE, 237),
('roi',                  'Return on Investment (RoI)',            'ROI',                    'ratio','percentage','EAT / TA',                  FALSE, 238),
-- Efficiency
('asset_turnover',       'Assets Turn-Over',                      'Asset Turnover',         'ratio','times',    'Sales / TA',                 FALSE, 240),
('cost_of_sales',        'Cost of Sales',                         'Cost of Sales Ratio',    'ratio','percentage','COGS / Sales',              FALSE, 241),
('overhead_ratio',       'Over-Head Ratio',                       'Overhead Ratio',         'ratio','percentage','SGA / Sales',               FALSE, 242),
-- Cash Flow Adequacy (KEY RATIO #5)
('focf_to_total_debt',   'Free Operating Cash Flow to Total Debt','FOCF / Total Debt',      'ratio','ratio',    'FOCF / TL',                  TRUE,  250)
ON CONFLICT (code) DO NOTHING;
