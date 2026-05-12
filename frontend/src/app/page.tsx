"use client";

import { useState, useRef } from "react";

export default function Home() {
  const [formData, setFormData] = useState({
    company_name: "",
    current_assets: "",
    current_liabilities: "",
    ebit: "",
    interest_expense: "",
    total_debt: "",
    total_equity: "",
    free_operating_cash_flow: "",
  });

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"manual" | "pdf">("pdf");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmitManual = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch("http://localhost:8000/api/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: formData.company_name,
          current_assets: Number(formData.current_assets),
          current_liabilities: Number(formData.current_liabilities),
          ebit: Number(formData.ebit),
          interest_expense: Number(formData.interest_expense),
          total_debt: Number(formData.total_debt),
          total_equity: Number(formData.total_equity),
          free_operating_cash_flow: Number(formData.free_operating_cash_flow),
        }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error calculating benchmark:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitPDF = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    const formDataObj = new FormData();
    formDataObj.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:8000/api/upload-pdf", {
        method: "POST",
        body: formDataObj,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Failed to process PDF");
      }
      
      setResult(data.benchmark_result);
      
      // Update form data with extracted values
      if (data.extracted_data) {
        setFormData({
          company_name: data.extracted_data.company_name || "",
          current_assets: data.extracted_data.current_assets?.toString() || "",
          current_liabilities: data.extracted_data.current_liabilities?.toString() || "",
          ebit: data.extracted_data.ebit?.toString() || "",
          interest_expense: data.extracted_data.interest_expense?.toString() || "",
          total_debt: data.extracted_data.total_debt?.toString() || "",
          total_equity: data.extracted_data.total_equity?.toString() || "",
          free_operating_cash_flow: data.extracted_data.free_operating_cash_flow?.toString() || "",
        });
        setActiveTab("manual"); // Switch to manual tab to show extracted data
      }
    } catch (error: any) {
      console.error("Error uploading PDF:", error);
      alert(`Failed to process PDF:\n${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getPredicateColor = (predicate: str) => {
    switch (predicate) {
      case "Sangat Sehat": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "Sehat": return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "Cukup Sehat": return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      case "Kurang Sehat": return "bg-orange-500/10 text-orange-400 border-orange-500/20";
      default: return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    }
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-white p-8 font-sans selection:bg-emerald-500 selection:text-white pb-20">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="space-y-4 text-center py-12">
          <div className="inline-block px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-medium border border-emerald-500/20 mb-4">
            AI-Assisted ETL & Analytics
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-200 to-neutral-500">
            Industrial Benchmark
            <br />& Risk Analysis
          </h1>
          <p className="text-neutral-400 max-w-2xl mx-auto text-lg">
            Extract data from Annual Reports via PDF, calculate key health ratios, and determine company risk predicates automatically.
          </p>
        </header>

        <div className="grid lg:grid-cols-12 gap-8 items-start">
          {/* Input Section */}
          <section className="lg:col-span-5 bg-neutral-900/50 backdrop-blur-xl border border-neutral-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 -mt-20 -mr-20 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
            
            <div className="flex space-x-2 mb-6 bg-neutral-950 p-1 rounded-xl relative z-10 border border-neutral-800">
              <button
                onClick={() => setActiveTab("pdf")}
                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "pdf" ? "bg-neutral-800 text-white shadow-sm" : "text-neutral-400 hover:text-white"}`}
              >
                PDF Upload (ETL)
              </button>
              <button
                onClick={() => setActiveTab("manual")}
                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === "manual" ? "bg-neutral-800 text-white shadow-sm" : "text-neutral-400 hover:text-white"}`}
              >
                Manual Entry
              </button>
            </div>

            {activeTab === "pdf" ? (
              <form onSubmit={handleSubmitPDF} className="space-y-5 relative z-10">
                <div 
                  className="border-2 border-dashed border-neutral-700 rounded-2xl p-10 text-center hover:border-emerald-500/50 transition-colors cursor-pointer bg-neutral-950/50"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    accept=".pdf" 
                    onChange={handleFileChange}
                  />
                  <div className="w-16 h-16 mx-auto bg-neutral-800 rounded-full flex items-center justify-center mb-4 text-emerald-400">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-white mb-1">
                    {selectedFile ? selectedFile.name : "Click or drag PDF to upload"}
                  </h3>
                  <p className="text-sm text-neutral-500">
                    Upload an Annual Report (LK Tahunan) PDF to automatically extract financial ratios.
                  </p>
                </div>
                
                <button
                  type="submit"
                  disabled={loading || !selectedFile}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3.5 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Extracting & Analyzing..." : "Extract PDF & Analyze"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleSubmitManual} className="space-y-4 relative z-10">
                <div>
                  <label className="block text-xs font-medium text-neutral-400 mb-1">Company Name</label>
                  <input type="text" name="company_name" required value={formData.company_name} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="PT ABC Tbk" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-400 mb-1">Current Assets</label>
                    <input type="number" step="any" name="current_assets" required value={formData.current_assets} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-neutral-400 mb-1">Current Liab.</label>
                    <input type="number" step="any" name="current_liabilities" required value={formData.current_liabilities} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-400 mb-1">EBIT</label>
                    <input type="number" step="any" name="ebit" required value={formData.ebit} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-neutral-400 mb-1">Interest Exp.</label>
                    <input type="number" step="any" name="interest_expense" required value={formData.interest_expense} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-400 mb-1">Total Debt</label>
                    <input type="number" step="any" name="total_debt" required value={formData.total_debt} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-neutral-400 mb-1">Total Equity</label>
                    <input type="number" step="any" name="total_equity" required value={formData.total_equity} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-400 mb-1">Free Operating Cash Flow (FOCF)</label>
                  <input type="number" step="any" name="free_operating_cash_flow" required value={formData.free_operating_cash_flow} onChange={handleChange} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500" placeholder="0" />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50 mt-4"
                >
                  {loading ? "Calculating..." : "Calculate Benchmark"}
                </button>
              </form>
            )}
          </section>

          {/* Results Section */}
          <section className="lg:col-span-7 h-full">
            {result ? (
              <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-8 shadow-xl h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                  <span className="text-9xl font-black">{result.average_score}</span>
                </div>
                
                <div className="flex items-center justify-between mb-8 relative z-10">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1">Health Report</h2>
                    <p className="text-neutral-400 font-medium">{result.company}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-neutral-500 mb-1">Avg Score: <span className="text-white font-bold">{result.average_score}</span></div>
                    <span className={`px-4 py-1.5 rounded-full text-sm font-bold tracking-wide border ${getPredicateColor(result.health_predicate)}`}>
                      {result.health_predicate}
                    </span>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4 relative z-10">
                  <div className="bg-neutral-950 p-4 rounded-2xl border border-neutral-800/50 flex flex-col justify-between">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="text-neutral-400 text-xs font-medium mb-1">Current Ratio</p>
                        <p className="text-2xl font-mono font-semibold text-white">{result.ratios.current_ratio}</p>
                      </div>
                      <div className="bg-neutral-900 px-2 py-1 rounded text-xs font-mono text-emerald-400">Score: {result.scores.current_ratio_score}</div>
                    </div>
                  </div>
                  
                  <div className="bg-neutral-950 p-4 rounded-2xl border border-neutral-800/50 flex flex-col justify-between">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="text-neutral-400 text-xs font-medium mb-1">Interest Coverage</p>
                        <p className="text-2xl font-mono font-semibold text-white">{result.ratios.interest_coverage}</p>
                      </div>
                      <div className="bg-neutral-900 px-2 py-1 rounded text-xs font-mono text-emerald-400">Score: {result.scores.interest_coverage_score}</div>
                    </div>
                  </div>

                  <div className="bg-neutral-950 p-4 rounded-2xl border border-neutral-800/50 flex flex-col justify-between">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="text-neutral-400 text-xs font-medium mb-1">Debt to Equity</p>
                        <p className="text-2xl font-mono font-semibold text-white">{result.ratios.total_debt_to_equity}</p>
                      </div>
                      <div className="bg-neutral-900 px-2 py-1 rounded text-xs font-mono text-emerald-400">Score: {result.scores.total_debt_to_equity_score}</div>
                    </div>
                  </div>

                  <div className="bg-neutral-950 p-4 rounded-2xl border border-neutral-800/50 flex flex-col justify-between">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="text-neutral-400 text-xs font-medium mb-1">Debt to Capitalization</p>
                        <p className="text-2xl font-mono font-semibold text-white">{result.ratios.debt_to_capitalization}</p>
                      </div>
                      <div className="bg-neutral-900 px-2 py-1 rounded text-xs font-mono text-emerald-400">Score: {result.scores.debt_to_capitalization_score}</div>
                    </div>
                  </div>

                  <div className="bg-neutral-950 p-4 rounded-2xl border border-neutral-800/50 flex flex-col justify-between sm:col-span-2">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="text-neutral-400 text-xs font-medium mb-1">Free Operating Cash Flow to Debt</p>
                        <p className="text-2xl font-mono font-semibold text-white">{result.ratios.focf_to_total_debt}</p>
                      </div>
                      <div className="bg-neutral-900 px-2 py-1 rounded text-xs font-mono text-emerald-400">Score: {result.scores.focf_to_total_debt_score}</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-3xl p-8 h-full min-h-[400px] flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-2">
                  <svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-neutral-300">Awaiting Data</h3>
                <p className="text-neutral-500 max-w-sm mx-auto">
                  Upload an Annual Report PDF to automatically extract data, or switch to manual entry to input figures directly.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
