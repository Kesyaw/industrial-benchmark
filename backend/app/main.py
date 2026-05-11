from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io

app = FastAPI(title="Industrial Benchmark API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FinancialData(BaseModel):
    company_name: str
    revenue: float
    net_income: float
    total_assets: float
    total_liabilities: float
    total_equity: float

@app.get("/")
def read_root():
    return {"message": "Welcome to Industrial Benchmark API"}

@app.post("/api/benchmark")
def benchmark_data(data: FinancialData):
    # Basic benchmark calculation (placeholder)
    roe = data.net_income / data.total_equity if data.total_equity != 0 else 0
    roa = data.net_income / data.total_assets if data.total_assets != 0 else 0
    der = data.total_liabilities / data.total_equity if data.total_equity != 0 else 0

    return {
        "company": data.company_name,
        "ratios": {
            "ROE": round(roe, 4),
            "ROA": round(roa, 4),
            "DER": round(der, 4)
        },
        "status": "Healthy" if roe > 0.1 else "Needs Improvement"
    }

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # Placeholder for PDF extraction
    # In reality, we'd use pdfplumber or camelot here to parse the file
    content = await file.read()
    
    # Fake extracted data for demonstration
    extracted_data = {
        "company_name": file.filename.split(".")[0],
        "revenue": 1000000,
        "net_income": 150000,
        "total_assets": 5000000,
        "total_liabilities": 2000000,
        "total_equity": 3000000
    }
    return {"message": f"Successfully parsed {file.filename}", "data": extracted_data}
