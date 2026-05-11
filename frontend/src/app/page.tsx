"use client";

import { useState } from "react";

export default function Home() {
  const [formData, setFormData] = useState({
    company_name: "",
    revenue: "",
    net_income: "",
    total_assets: "",
    total_liabilities: "",
    total_equity: "",
  });

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch("http://localhost:8000/api/benchmark", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          company_name: formData.company_name,
          revenue: Number(formData.revenue),
          net_income: Number(formData.net_income),
          total_assets: Number(formData.total_assets),
          total_liabilities: Number(formData.total_liabilities),
          total_equity: Number(formData.total_equity),
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

  return (
    <main className="min-h-screen bg-neutral-950 text-white p-8 font-sans selection:bg-emerald-500 selection:text-white">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <header className="space-y-4 text-center py-12">
          <div className="inline-block px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-medium border border-emerald-500/20 mb-4">
            AI-Powered Analytics
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-200 to-neutral-500">
            Industrial Benchmark
            <br />& Risk Analysis
          </h1>
          <p className="text-neutral-400 max-w-2xl mx-auto text-lg">
            Transform complex financial reports into actionable insights. Assess credit risk, evaluate investments, and monitor performance in seconds.
          </p>
        </header>

        <div className="grid md:grid-cols-2 gap-8 items-start">
          {/* Form Section */}
          <section className="bg-neutral-900/50 backdrop-blur-xl border border-neutral-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 -mt-20 -mr-20 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
            
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Financial Data Input
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
              <div>
                <label className="block text-sm font-medium text-neutral-400 mb-1">Company Name</label>
                <input
                  type="text"
                  name="company_name"
                  required
                  value={formData.company_name}
                  onChange={handleChange}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                  placeholder="e.g. PT Astra Agro Lestari Tbk"
                />
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-neutral-400 mb-1">Revenue</label>
                  <input
                    type="number"
                    name="revenue"
                    required
                    value={formData.revenue}
                    onChange={handleChange}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-400 mb-1">Net Income</label>
                  <input
                    type="number"
                    name="net_income"
                    required
                    value={formData.net_income}
                    onChange={handleChange}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                    placeholder="0"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-neutral-400 mb-1">Total Assets</label>
                  <input
                    type="number"
                    name="total_assets"
                    required
                    value={formData.total_assets}
                    onChange={handleChange}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-400 mb-1">Total Liabilities</label>
                  <input
                    type="number"
                    name="total_liabilities"
                    required
                    value={formData.total_liabilities}
                    onChange={handleChange}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                    placeholder="0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-400 mb-1">Total Equity</label>
                <input
                  type="number"
                  name="total_equity"
                  required
                  value={formData.total_equity}
                  onChange={handleChange}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                  placeholder="0"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3.5 px-4 rounded-xl transition-all duration-200 shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] disabled:opacity-70 disabled:cursor-not-allowed mt-4"
              >
                {loading ? "Analyzing..." : "Generate Risk Report"}
              </button>
            </form>
          </section>

          {/* Results Section */}
          <section className="h-full">
            {result ? (
              <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-8 shadow-xl h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center justify-between mb-8">
                  <h2 className="text-2xl font-bold text-white">Analysis Result</h2>
                  <span className={`px-4 py-1.5 rounded-full text-sm font-bold tracking-wide ${result.status === "Healthy" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {result.status}
                  </span>
                </div>

                <div className="mb-8">
                  <p className="text-neutral-400 text-sm uppercase tracking-wider font-semibold mb-2">Target Entity</p>
                  <p className="text-3xl font-bold text-white">{result.company}</p>
                </div>

                <div className="grid grid-cols-1 gap-4 mt-auto">
                  <div className="bg-neutral-950 p-5 rounded-2xl border border-neutral-800/50 flex items-center justify-between group hover:border-emerald-500/30 transition-colors">
                    <div>
                      <p className="text-neutral-400 font-medium mb-1">Return on Equity (ROE)</p>
                      <p className="text-xs text-neutral-500">Net Income / Total Equity</p>
                    </div>
                    <p className="text-3xl font-mono font-semibold text-emerald-400">{(result.ratios.ROE * 100).toFixed(2)}%</p>
                  </div>
                  
                  <div className="bg-neutral-950 p-5 rounded-2xl border border-neutral-800/50 flex items-center justify-between group hover:border-emerald-500/30 transition-colors">
                    <div>
                      <p className="text-neutral-400 font-medium mb-1">Return on Assets (ROA)</p>
                      <p className="text-xs text-neutral-500">Net Income / Total Assets</p>
                    </div>
                    <p className="text-3xl font-mono font-semibold text-emerald-400">{(result.ratios.ROA * 100).toFixed(2)}%</p>
                  </div>

                  <div className="bg-neutral-950 p-5 rounded-2xl border border-neutral-800/50 flex items-center justify-between group hover:border-emerald-500/30 transition-colors">
                    <div>
                      <p className="text-neutral-400 font-medium mb-1">Debt to Equity (DER)</p>
                      <p className="text-xs text-neutral-500">Total Liabilities / Total Equity</p>
                    </div>
                    <p className="text-3xl font-mono font-semibold text-emerald-400">{result.ratios.DER.toFixed(2)}x</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-3xl p-8 h-full flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-2">
                  <svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-neutral-300">Awaiting Data</h3>
                <p className="text-neutral-500 max-w-xs mx-auto">
                  Input financial figures or upload an annual report PDF to generate a comprehensive risk analysis and benchmark.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
