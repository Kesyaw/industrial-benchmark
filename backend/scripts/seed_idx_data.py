import os
import sys
import pandas as pd
from datetime import date
from decimal import Decimal

# Add backend dir to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models import (
    Sector, Company, MetricDefinition, FinancialPeriod, FinancialMetric,
    PeriodTypeEnum, MetricCategoryEnum
)

def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True

def main():
    db = SessionLocal()
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    
    # 1. Load CSVs
    try:
        df_1000000 = pd.read_csv(os.path.join(data_dir, 'benchmark_1000000.csv'))
        df_1210000 = pd.read_csv(os.path.join(data_dir, 'benchmark_1210000.csv'))
        df_1321000 = pd.read_csv(os.path.join(data_dir, 'benchmark_1321000.csv'))
        df_1410000 = pd.read_csv(os.path.join(data_dir, 'benchmark_1410000.csv'))
    except FileNotFoundError as e:
        print(f"Error loading CSVs: {e}")
        return

    # 2. Seed Sectors and Companies
    print("Seeding Sectors and Companies...")
    for _, row in df_1000000.iterrows():
        ticker = row.get('Kode entitas')
        if pd.isna(ticker): continue
        
        sector_name = str(row.get('Sektor', 'Unknown'))
        sector_code = sector_name.split('.')[0].strip() if '.' in sector_name else 'UNK'
        
        sector, _ = get_or_create(
            db, Sector, 
            code=sector_code[:20],
            defaults={
                'name_id': sector_name[:100],
                'name_en': sector_name[:100]
            }
        )
        
        company, _ = get_or_create(
            db, Company,
            ticker=str(ticker)[:10],
            defaults={
                'name': str(row.get('Nama entitas', ticker))[:255],
                'sector_id': sector.id,
                'subsector': str(row.get('Subsektor', ''))[:150]
            }
        )

    db.commit()

    # 3. Seed Metric Definitions
    print("Seeding Metric Definitions...")
    metrics_mapping = [
        # Balance Sheet (1210000)
        ('Aset', 'Aset', 'Total Assets', MetricCategoryEnum.balance_sheet),
        ('Aset lancar', 'Aset lancar', 'Current assets', MetricCategoryEnum.balance_sheet),
        ('Aset tidak lancar', 'Aset tidak lancar', 'Non-current assets', MetricCategoryEnum.balance_sheet),
        ('Liabilitas', 'Liabilitas', 'Total Liabilities', MetricCategoryEnum.balance_sheet),
        ('Liabilitas jangka pendek', 'Liabilitas jangka pendek', 'Current liabilities', MetricCategoryEnum.balance_sheet),
        ('Liabilitas jangka panjang', 'Liabilitas jangka panjang', 'Non-current liabilities', MetricCategoryEnum.balance_sheet),
        ('Ekuitas', 'Ekuitas', 'Total Equity', MetricCategoryEnum.balance_sheet),
        ('Kas dan setara kas', 'Kas dan setara kas', 'Cash and cash equivalents', MetricCategoryEnum.balance_sheet),
        ('Piutang usaha', 'Piutang usaha', 'Trade receivables', MetricCategoryEnum.balance_sheet),
        ('Persediaan', 'Persediaan', 'Inventories', MetricCategoryEnum.balance_sheet),
        
        # P&L (1321000)
        ('Penjualan dan pendapatan usaha', 'Penjualan', 'Sales and revenue', MetricCategoryEnum.income_statement),
        ('Beban pokok penjualan dan pendapatan', 'Beban Pokok', 'Cost of sales', MetricCategoryEnum.income_statement),
        ('Jumlah laba kotor', 'Laba Kotor', 'Gross profit', MetricCategoryEnum.income_statement),
        ('Laba (rugi) sebelum pajak penghasilan', 'Laba Sebelum Pajak', 'Profit before tax', MetricCategoryEnum.income_statement),
        ('Laba (rugi) tahun berjalan', 'Laba Bersih', 'Net profit', MetricCategoryEnum.income_statement),
        
        # Equity Changes (1410000)
        ('Posisi ekuitas', 'Posisi ekuitas', 'Equity position', MetricCategoryEnum.balance_sheet),
        ('Laba (rugi)', 'Laba (rugi) komprehensif', 'Comprehensive income', MetricCategoryEnum.income_statement),
        ('Total komprehensif', 'Total komprehensif', 'Total comprehensive income', MetricCategoryEnum.income_statement),
    ]

    metric_defs = {}
    for code, name_id, name_en, category in metrics_mapping:
        safe_code = code.replace(' ', '_').replace('(', '').replace(')', '').lower()[:80]
        mdef, _ = get_or_create(
            db, MetricDefinition,
            code=safe_code,
            defaults={
                'name_id': name_id[:150],
                'name_en': name_en[:150],
                'category': category
            }
        )
        metric_defs[code] = mdef.id

    db.commit()

    # 4. Seed Financial Periods and Metrics
    print("Seeding Financial Periods and Metrics...")
    # Process each company's dataframe records
    def process_df_metrics(df):
        for _, row in df.iterrows():
            ticker = row.get('Ticker')
            if pd.isna(ticker): continue
            
            company = db.query(Company).filter_by(ticker=str(ticker)).first()
            if not company: continue
            
            # Determine Year based on Period column if it exists
            period_val = row.get('Period', 'Current')
            if period_val == 'Prior':
                fiscal_year = 2024
                period_end = date(2024, 12, 31)
            else:
                fiscal_year = 2025
                period_end = date(2025, 12, 31)
            
            period, _ = get_or_create(
                db, FinancialPeriod,
                company_id=company.id,
                fiscal_year=fiscal_year,
                period_type=PeriodTypeEnum.annual,
                defaults={
                    'period_end_date': period_end,
                    'source': 'idx_extracted_csv',
                    'is_audited': True
                }
            )

            for col in df.columns:
                if col in ['Ticker', 'File', 'Period']: continue
                if col not in metric_defs: continue
                
                val = row[col]
                if pd.isna(val): continue
                
                # Insert metric
                try:
                    num_val = Decimal(str(val))
                    get_or_create(
                        db, FinancialMetric,
                        period_id=period.id,
                        metric_definition_id=metric_defs[col],
                        defaults={
                            'metric_value': num_val,
                            'raw_value': str(val),
                            'is_computed': False
                        }
                    )
                except Exception as e:
                    pass

    process_df_metrics(df_1210000)
    process_df_metrics(df_1321000)
    process_df_metrics(df_1410000)

    db.commit()
    print("Seeding completed successfully!")

if __name__ == '__main__':
    main()
