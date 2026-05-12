from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

from app.schemas import FinancialData, BenchmarkResult
from app.services.pdf_extractor import extract_financial_data_from_pdf
from app.services.benchmark_engine import calculate_benchmark

app = FastAPI(title="Industrial Benchmark API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data/pdfs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to Industrial Benchmark API"}

@app.post("/api/benchmark", response_model=BenchmarkResult)
def benchmark_data(data: FinancialData):
    # Process manual input via the benchmark engine
    return calculate_benchmark(data)

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file temporarily
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Extract data
        financial_data = extract_financial_data_from_pdf(file_path, file.filename)
        
        # Calculate benchmark
        result = calculate_benchmark(financial_data)
        
        return {
            "message": f"Successfully processed {file.filename}",
            "extracted_data": financial_data.model_dump(),
            "benchmark_result": result.model_dump()
        }
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print("ERROR IN UPLOAD PDF:", error_msg)
        raise HTTPException(status_code=500, detail=str(error_msg))
    finally:
        # Optionally, remove the file after processing
        # os.remove(file_path)
        pass
