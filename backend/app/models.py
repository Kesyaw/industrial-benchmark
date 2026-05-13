"""
SQLAlchemy ORM models — mirrors the EAV schema in db/init.sql
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, BigInteger, Column, Date, DateTime, Enum,
    ForeignKey, Integer, Numeric, SmallInteger, String, Text,
    UniqueConstraint, Index, text,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
import enum


# ─────────────────────────────────────────
# Python Enums matching SQL ENUM types
# ─────────────────────────────────────────
class PeriodTypeEnum(str, enum.Enum):
    annual = "annual"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class MetricCategoryEnum(str, enum.Enum):
    balance_sheet = "balance_sheet"
    income_statement = "income_statement"
    cash_flow = "cash_flow"
    ratio = "ratio"
    benchmark = "benchmark"
    writeoff = "writeoff"


# ─────────────────────────────────────────
# SECTORS
# ─────────────────────────────────────────
class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name_id = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    is_financial = Column(Boolean, default=False)
    has_inventory = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    companies: Mapped[List["Company"]] = relationship("Company", back_populates="sector")
    metric_definitions: Mapped[List["MetricDefinition"]] = relationship("MetricDefinition", back_populates="sector")
    benchmark_thresholds: Mapped[List["BenchmarkThreshold"]] = relationship("BenchmarkThreshold", back_populates="sector")


# ─────────────────────────────────────────
# COMPANIES
# ─────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    subsector = Column(String(150))
    listing_date = Column(Date)
    currency = Column(String(5), default="IDR")
    market_cap = Column(BigInteger)
    is_active = Column(Boolean, default=True)
    idx_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.utcnow)

    sector: Mapped[Optional["Sector"]] = relationship("Sector", back_populates="companies")
    financial_periods: Mapped[List["FinancialPeriod"]] = relationship("FinancialPeriod", back_populates="company")
    asset_writeoffs: Mapped[List["AssetWriteoff"]] = relationship("AssetWriteoff", back_populates="company")
    debitur_profiles: Mapped[List["DebiturProfile"]] = relationship("DebiturProfile", back_populates="company")


# ─────────────────────────────────────────
# FINANCIAL PERIODS
# ─────────────────────────────────────────
class FinancialPeriod(Base):
    __tablename__ = "financial_periods"
    __table_args__ = (UniqueConstraint("company_id", "fiscal_year", "period_type"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    fiscal_year = Column(SmallInteger, nullable=False)
    period_type = Column(Enum(PeriodTypeEnum, name="period_type_enum"), nullable=False)
    period_end_date = Column(Date, nullable=False)
    source = Column(String(50), default="idx_api")
    is_audited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="financial_periods")
    financial_metrics: Mapped[List["FinancialMetric"]] = relationship("FinancialMetric", back_populates="period")
    asset_writeoffs: Mapped[List["AssetWriteoff"]] = relationship("AssetWriteoff", back_populates="period")
    benchmark_scores: Mapped[List["BenchmarkScore"]] = relationship("BenchmarkScore", back_populates="period")
    benchmark_result: Mapped[Optional["BenchmarkResult"]] = relationship("BenchmarkResult", back_populates="period", uselist=False)


# ─────────────────────────────────────────
# METRIC DEFINITIONS (EAV Dictionary)
# ─────────────────────────────────────────
class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id = Column(Integer, primary_key=True)
    code = Column(String(80), unique=True, nullable=False)
    name_id = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    category = Column(Enum(MetricCategoryEnum, name="metric_category_enum"), nullable=False)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)  # NULL = all sectors
    unit = Column(String(20), default="IDR")
    formula = Column(Text)
    is_key_ratio = Column(Boolean, default=False)
    sort_order = Column(SmallInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    sector: Mapped[Optional["Sector"]] = relationship("Sector", back_populates="metric_definitions")
    financial_metrics: Mapped[List["FinancialMetric"]] = relationship("FinancialMetric", back_populates="metric_definition")


# ─────────────────────────────────────────
# FINANCIAL METRICS (EAV Fact Table)
# ─────────────────────────────────────────
class FinancialMetric(Base):
    __tablename__ = "financial_metrics"
    __table_args__ = (
        UniqueConstraint("period_id", "metric_definition_id"),
        Index("idx_financial_metrics_period", "period_id"),
        Index("idx_financial_metrics_definition", "metric_definition_id"),
    )

    id = Column(BigInteger, primary_key=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id", ondelete="CASCADE"))
    metric_definition_id = Column(Integer, ForeignKey("metric_definitions.id"))
    metric_value = Column(Numeric(25, 6))
    raw_value = Column(Text)
    is_computed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    period: Mapped[Optional["FinancialPeriod"]] = relationship("FinancialPeriod", back_populates="financial_metrics")
    metric_definition: Mapped[Optional["MetricDefinition"]] = relationship("MetricDefinition", back_populates="financial_metrics")


# ─────────────────────────────────────────
# BENCHMARK THRESHOLDS
# ─────────────────────────────────────────
class BenchmarkThreshold(Base):
    __tablename__ = "benchmark_thresholds"

    id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    metric_code = Column(String(80), nullable=False)
    level = Column(SmallInteger, nullable=False)
    level_label = Column(String(50), nullable=False)
    range_min = Column(Numeric(20, 6))
    range_max = Column(Numeric(20, 6))
    score = Column(SmallInteger, nullable=False)
    direction = Column(String(5), default="asc")

    sector: Mapped[Optional["Sector"]] = relationship("Sector", back_populates="benchmark_thresholds")


# ─────────────────────────────────────────
# ASSET WRITE-OFFS (Penyusutan Aktiva Tetap)
# ─────────────────────────────────────────
class AssetWriteoff(Base):
    __tablename__ = "asset_writeoffs"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    period_id = Column(Integer, ForeignKey("financial_periods.id"))
    asset_category = Column(String(100), nullable=False)
    asset_name = Column(String(255))
    acquisition_date = Column(Date)
    acquisition_cost = Column(BigInteger)
    accumulated_depr = Column(BigInteger)
    book_value_before = Column(BigInteger, nullable=False)
    writeoff_amount = Column(BigInteger, nullable=False)
    annual_depr_rate = Column(Numeric(5, 2))
    useful_life_years = Column(SmallInteger)
    writeoff_date = Column(Date)
    reason = Column(Text)
    approved_by = Column(String(100))
    reference_doc = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="asset_writeoffs")
    period: Mapped[Optional["FinancialPeriod"]] = relationship("FinancialPeriod", back_populates="asset_writeoffs")


# ─────────────────────────────────────────
# BENCHMARK SCORES & RESULTS
# ─────────────────────────────────────────
class BenchmarkScore(Base):
    __tablename__ = "benchmark_scores"

    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id"))
    metric_code = Column(String(80), nullable=False)
    ratio_value = Column(Numeric(20, 6))
    score = Column(SmallInteger)
    level = Column(SmallInteger)
    level_label = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    period: Mapped[Optional["FinancialPeriod"]] = relationship("FinancialPeriod", back_populates="benchmark_scores")


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id"), unique=True)
    average_score = Column(Numeric(6, 2))
    health_predicate = Column(String(50))
    analyst_name = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    period: Mapped[Optional["FinancialPeriod"]] = relationship("FinancialPeriod", back_populates="benchmark_result")


# ─────────────────────────────────────────
# DEBITUR PROFILES (Nasabah)
# ─────────────────────────────────────────
class DebiturProfile(Base):
    __tablename__ = "debitur_profiles"

    id = Column(Integer, primary_key=True)
    no_nasabah = Column(String(50), unique=True)
    nama_nasabah = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    tipe_fasilitas = Column(String(100))
    nilai_fasilitas = Column(BigInteger)
    tanggal_lap_keu = Column(Date)
    tanggal_rating = Column(Date)
    rating_perusahaan = Column(String(50))
    level_risiko = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="debitur_profiles")


# ─────────────────────────────────────────
# ETL LOGS
# ─────────────────────────────────────────
class EtlLog(Base):
    __tablename__ = "etl_logs"

    id = Column(Integer, primary_key=True)
    run_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    source = Column(String(50))
    tickers_total = Column(Integer)
    tickers_success = Column(Integer)
    tickers_failed = Column(Integer)
    duration_secs = Column(Numeric(10, 2))
    error_details = Column(Text)
