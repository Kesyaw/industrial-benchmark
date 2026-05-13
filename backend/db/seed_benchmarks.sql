-- ============================================================
-- SEED: Benchmark Thresholds — Trade Sector
-- Source: Bank Sumsel Babel methodology
-- 5 key ratios × 5 levels × score (1,25,50,75,100)
-- ============================================================

-- 1. Current Ratio (asc — higher = more liquid = better)
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'current_ratio', 1, 'Tidak Likuid',  NULL, 1.73, 1, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'current_ratio', 2, 'Kurang Likuid', 1.74, 1.94, 25, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'current_ratio', 3, 'Cukup Likuid',  1.95, 2.15, 50, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'current_ratio', 4, 'Likuid',        2.16, 2.37, 75, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'current_ratio', 5, 'Sangat Likuid', 2.38, NULL, 100, 'asc' FROM sectors s WHERE s.code = 'TRADE';

-- 2. Interest Coverage / Times Interest Earned (asc)
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'interest_coverage', 1, 'Tidak Baik',  NULL, 7.68, 1, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'interest_coverage', 2, 'Kurang Baik', 7.69, 19.76, 25, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'interest_coverage', 3, 'Cukup Baik',  19.77, 31.84, 50, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'interest_coverage', 4, 'Baik',        31.85, 43.92, 75, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'interest_coverage', 5, 'Sangat Baik', 43.93, NULL, 100, 'asc' FROM sectors s WHERE s.code = 'TRADE';

-- 3. Total Debt to Equity (desc — lower = better)
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'total_debt_to_equity', 1, 'Sangat Baik',  NULL, 1.00, 100, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'total_debt_to_equity', 2, 'Baik',         1.01, 1.13, 75, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'total_debt_to_equity', 3, 'Cukup Baik',   1.14, 1.26, 50, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'total_debt_to_equity', 4, 'Kurang Baik',  1.27, 1.39, 25, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'total_debt_to_equity', 5, 'Tidak Baik',   1.40, NULL, 1, 'desc' FROM sectors s WHERE s.code = 'TRADE';

-- 4. Debt to Net Worth (desc — lower = better)
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'debt_to_net_worth', 1, 'Sangat Baik',  NULL, 0.51, 100, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'debt_to_net_worth', 2, 'Baik',         0.52, 0.58, 75, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'debt_to_net_worth', 3, 'Cukup Baik',   0.59, 0.65, 50, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'debt_to_net_worth', 4, 'Kurang Baik',  0.66, 0.72, 25, 'desc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'debt_to_net_worth', 5, 'Tidak Baik',   0.73, NULL, 1, 'desc' FROM sectors s WHERE s.code = 'TRADE';

-- 5. FOCF to Total Debt (asc — higher = better)
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'focf_to_total_debt', 1, 'Tidak Baik',   NULL, -3.53, 1, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'focf_to_total_debt', 2, 'Kurang Baik', -3.52, -2.02, 25, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'focf_to_total_debt', 3, 'Cukup Baik',  -2.01, -0.50, 50, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'focf_to_total_debt', 4, 'Baik',        -0.49, 1.02, 75, 'asc' FROM sectors s WHERE s.code = 'TRADE';
INSERT INTO benchmark_thresholds (sector_id, metric_code, level, level_label, range_min, range_max, score, direction)
SELECT s.id, 'focf_to_total_debt', 5, 'Sangat Baik',  1.03, NULL, 100, 'asc' FROM sectors s WHERE s.code = 'TRADE';
