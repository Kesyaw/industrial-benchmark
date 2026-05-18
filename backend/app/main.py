"""
Industrial Benchmark API — FastAPI Application Entry Point

All route definitions are organized into routers:
  - routers/health.py     → Health check endpoints
  - routers/companies.py  → Sectors & companies data
  - routers/benchmark.py  → Benchmark scoring & leaderboard
  - routers/etl.py        → ETL triggers & file uploads
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, companies, benchmark, etl

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Industrial Benchmark API",
    description="Financial Data Warehouse & Industry Benchmark Scoring Engine",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(companies.router)
app.include_router(benchmark.router)
app.include_router(etl.router)
