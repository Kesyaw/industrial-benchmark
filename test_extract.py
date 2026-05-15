import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.xlsx_extractor import extract_financial_data_from_xlsx

data = extract_financial_data_from_xlsx('backend/data/uploads/AALI.xlsx', 'AALI.xlsx')
print(data.model_dump())
