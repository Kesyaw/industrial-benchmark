-- ============================================================
-- FINANCIAL DATA WAREHOUSE — Industrial Benchmark
-- Architecture: EAV (Entity-Attribute-Value) + Dimensional
-- ============================================================

-- ─────────────────────────────────────────────
-- DIMENSION 1: SECTORS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sectors (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) UNIQUE NOT NULL,   -- e.g. 'TRADE', 'BANK', 'MINE'
    name_id         VARCHAR(100) NOT NULL,          -- Indonesian name
    name_en         VARCHAR(100) NOT NULL,          -- English name
    is_financial    BOOLEAN DEFAULT FALSE,          -- Banks/Insurance → different ratios
    has_inventory   BOOLEAN DEFAULT FALSE,          -- Mfg/Trade → COGS/Inventory exist
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DIMENSION 2: COMPANIES (Master)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) UNIQUE NOT NULL,   -- e.g. 'AALI', 'BBCA'
    name            VARCHAR(255) NOT NULL,
    sector_id       INTEGER REFERENCES sectors(id),
    subsector       VARCHAR(150),
    listing_date    DATE,
    currency        VARCHAR(5) DEFAULT 'IDR',
    market_cap      BIGINT,
    is_active       BOOLEAN DEFAULT TRUE,
    idx_url         TEXT,                           -- Direct link to IDX company page
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DIMENSION 3: FINANCIAL PERIODS
-- ─────────────────────────────────────────────
CREATE TYPE period_type_enum AS ENUM ('annual', 'Q1', 'Q2', 'Q3', 'Q4');

CREATE TABLE IF NOT EXISTS financial_periods (
    id              SERIAL PRIMARY KEY,
    company_id      INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    fiscal_year     SMALLINT NOT NULL,             -- e.g. 2023
    period_type     period_type_enum NOT NULL,
    period_end_date DATE NOT NULL,
    source          VARCHAR(50) DEFAULT 'idx_api', -- idx_api | xls_upload | pdf_extract | yfinance
    is_audited      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (company_id, fiscal_year, period_type)
);

-- ─────────────────────────────────────────────
-- EAV CORE: METRIC DEFINITIONS (The Key to Flexibility)
-- ─────────────────────────────────────────────
CREATE TYPE metric_category_enum AS ENUM (
    'balance_sheet',
    'income_statement',
    'cash_flow',
    'ratio',
    'benchmark',
    'writeoff'
);

CREATE TABLE IF NOT EXISTS metric_definitions (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(80) UNIQUE NOT NULL,   -- e.g. 'total_current_assets', 'npl_ratio'
    name_id         VARCHAR(150) NOT NULL,          -- Indonesian label from template
    name_en         VARCHAR(150) NOT NULL,
    category        metric_category_enum NOT NULL,
    sector_id       INTEGER REFERENCES sectors(id), -- NULL = applies to ALL sectors
    unit            VARCHAR(20) DEFAULT 'IDR',      -- IDR | percentage | ratio | times
    formula         TEXT,                           -- Optional: human-readable formula
    is_key_ratio    BOOLEAN DEFAULT FALSE,          -- True for the 5 main benchmark ratios
    sort_order      SMALLINT DEFAULT 0,             -- Display order in template
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- EAV CORE: FINANCIAL METRICS (All Values Live Here)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS financial_metrics (
    id                  BIGSERIAL PRIMARY KEY,
    period_id           INTEGER REFERENCES financial_periods(id) ON DELETE CASCADE,
    metric_definition_id INTEGER REFERENCES metric_definitions(id),
    metric_value        NUMERIC(25, 6),             -- Handles both large IDR values & small ratios
    raw_value           TEXT,                       -- Original value before parsing (audit trail)
    is_computed         BOOLEAN DEFAULT FALSE,      -- TRUE = calculated ratio, FALSE = raw from report
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (period_id, metric_definition_id)
);

-- Index for fast lookups
CREATE INDEX idx_financial_metrics_period ON financial_metrics(period_id);
CREATE INDEX idx_financial_metrics_definition ON financial_metrics(metric_definition_id);

-- ─────────────────────────────────────────────
-- BENCHMARK THRESHOLDS (Per Sector, Per Ratio)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS benchmark_thresholds (
    id              SERIAL PRIMARY KEY,
    sector_id       INTEGER REFERENCES sectors(id),
    metric_code     VARCHAR(80) NOT NULL,           -- FK to metric_definitions.code
    level           SMALLINT NOT NULL CHECK (level BETWEEN 1 AND 5),
    level_label     VARCHAR(50) NOT NULL,           -- e.g. 'Tidak Likuid', 'Sangat Baik'
    range_min       NUMERIC(20, 6),                 -- NULL = no lower bound (-∞)
    range_max       NUMERIC(20, 6),                 -- NULL = no upper bound (+∞)
    score           SMALLINT NOT NULL,              -- 1, 25, 50, 75, 100
    direction       VARCHAR(5) DEFAULT 'asc'        -- 'asc' (higher=better) | 'desc' (lower=better)
);

-- ─────────────────────────────────────────────
-- ASSET WRITE-OFFS (Penyusutan Aktiva Tetap)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS asset_writeoffs (
    id                  SERIAL PRIMARY KEY,
    company_id          INTEGER REFERENCES companies(id),
    period_id           INTEGER REFERENCES financial_periods(id),
    asset_category      VARCHAR(100) NOT NULL,      -- e.g. 'Aset Tetap', 'Piutang Tak Tertagih'
    asset_name          VARCHAR(255),               -- Description of the specific asset
    acquisition_date    DATE,
    acquisition_cost    BIGINT,
    accumulated_depr    BIGINT,                     -- Akumulasi Penyusutan sebelumnya
    book_value_before   BIGINT NOT NULL,            -- Nilai Buku Sebelum Penghapusan
    writeoff_amount     BIGINT NOT NULL,            -- Nilai Penghapusan
    book_value_after    BIGINT GENERATED ALWAYS AS (book_value_before - writeoff_amount) STORED,
    annual_depr_rate    NUMERIC(5, 2),              -- % penyusutan per tahun
    useful_life_years   SMALLINT,
    writeoff_date       DATE,
    reason              TEXT,                       -- Alasan penghapusan
    approved_by         VARCHAR(100),              -- Pejabat yang menyetujui
    reference_doc       VARCHAR(255),              -- Nomor SK/Surat Keputusan
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- SCORING LOG (Audit Trail for Benchmark Scoring)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS benchmark_scores (
    id                  SERIAL PRIMARY KEY,
    period_id           INTEGER REFERENCES financial_periods(id),
    metric_code         VARCHAR(80) NOT NULL,
    ratio_value         NUMERIC(20, 6),
    score               SMALLINT,
    level               SMALLINT,
    level_label         VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id                  SERIAL PRIMARY KEY,
    period_id           INTEGER REFERENCES financial_periods(id) UNIQUE,
    average_score       NUMERIC(6, 2),
    health_predicate    VARCHAR(50),               -- Sangat Sehat | Sehat | Cukup Sehat | Kurang Sehat | Tidak Sehat
    analyst_name        VARCHAR(100),
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DEBITUR INFO (Nasabah/Credit Customer)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS debitur_profiles (
    id                  SERIAL PRIMARY KEY,
    no_nasabah          VARCHAR(50) UNIQUE,
    nama_nasabah        VARCHAR(255) NOT NULL,
    company_id          INTEGER REFERENCES companies(id),
    tipe_fasilitas      VARCHAR(100),              -- KMK, KI, KSG, etc.
    nilai_fasilitas     BIGINT,
    tanggal_lap_keu     DATE,
    tanggal_rating      DATE,
    rating_perusahaan   VARCHAR(50),
    level_risiko        VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- ETL RUN LOG
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS etl_logs (
    id              SERIAL PRIMARY KEY,
    run_at          TIMESTAMPTZ DEFAULT NOW(),
    source          VARCHAR(50),
    tickers_total   INTEGER,
    tickers_success INTEGER,
    tickers_failed  INTEGER,
    duration_secs   NUMERIC(10, 2),
    error_details   TEXT
);

-- ─────────────────────────────────────────────
-- COMMENTS
-- ─────────────────────────────────────────────
COMMENT ON TABLE sectors IS 'IDX sector dimension — 16 sectors from BEI classification';
COMMENT ON TABLE companies IS 'Master company table — all IDX-listed companies (~900)';
COMMENT ON TABLE financial_periods IS 'Time dimension — annual/quarterly per company';
COMMENT ON TABLE metric_definitions IS 'EAV dictionary — defines every financial variable. Sector-specific metrics have sector_id set, universal metrics have NULL';
COMMENT ON TABLE financial_metrics IS 'EAV fact table — all financial values (raw & computed ratios) live here';
COMMENT ON TABLE benchmark_thresholds IS 'Scoring table from Bank Sumsel Babel methodology — 5 levels × 5 scores per ratio per sector';
COMMENT ON TABLE asset_writeoffs IS 'Penyusutan Aktiva Tetap — separate write-off tracking as per template';
COMMENT ON TABLE benchmark_scores IS 'Audit log of each ratio score per evaluation';
COMMENT ON TABLE benchmark_results IS 'Final health predicate result per company-period';
COMMENT ON TABLE debitur_profiles IS 'Credit customer (nasabah) information for the scoring sheet';
