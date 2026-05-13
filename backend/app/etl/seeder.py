"""
Database seeder — runs all SQL seed files in order:
  1. seed_sectors.sql
  2. seed_metrics.sql
  3. seed_benchmarks.sql

Usage:
    python -m app.etl.seeder
"""
import os
import logging
from sqlalchemy import text
from app.database import SessionLocal

log = logging.getLogger(__name__)

SEED_DIR = os.path.join(os.path.dirname(__file__), "../../db")

SEED_FILES = [
    "seed_sectors.sql",
    "seed_metrics.sql",
    "seed_benchmarks.sql",
]


def run_seed_file(db, filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    # Split on semicolons, skip empty
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        db.execute(text(stmt))
    db.commit()
    log.info(f"  ✅ Seeded: {os.path.basename(filepath)}")


def run_all_seeds():
    db = SessionLocal()
    try:
        for fname in SEED_FILES:
            path = os.path.abspath(os.path.join(SEED_DIR, fname))
            if os.path.exists(path):
                run_seed_file(db, path)
            else:
                log.warning(f"  ⚠️  Seed file not found: {path}")
        log.info("All seeds complete.")
    except Exception as e:
        db.rollback()
        log.error(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_all_seeds()
