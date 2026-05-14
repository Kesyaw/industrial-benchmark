"use client";

import { useState, useRef, useEffect } from "react";

const API = "http://localhost:8000";

interface Sector { id: number; code: string; name_id: string; name_en: string; is_financial: boolean; }
interface Company { id: number; ticker: string; name: string; sector_id: number | null; }
interface ScoreDetail { ratio_code: string; ratio_value: number | null; level_label: string; score: number | null; }
interface BenchmarkResult {
  company: string; sector_code: string;
  ratios: Record<string, number | null>;
  scores: Record<string, number | null>;
  score_details: ScoreDetail[];
  average_score: number; health_predicate: string;
}

export default function Home() {
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedSector, setSelectedSector] = useState("TRADE");
  const [selectedCompany, setSelectedCompany] = useState<string>("");
  const [companyDetail, setCompanyDetail] = useState<any>(null);

  const [formData, setFormData] = useState({
    company_name: "", sector_code: "TRADE",
    current_assets: "", current_liabilities: "", ebit: "", interest_expense: "",
    ebitda: "", total_debt: "", total_equity: "", long_term_debt: "",
    total_assets: "", gross_profit: "", net_income: "", revenue: "",
    free_operating_cash_flow: "",
  });

  const [result, setResult] = useState<BenchmarkResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"explorer" | "manual" | "pdf">("explorer");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [etlRunning, setEtlRunning] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/sectors`).then(r => r.json()).then(setSectors).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedSector) {
      fetch(`${API}/api/companies?sector=${selectedSector}`)
        .then(r => r.json()).then(setCompanies).catch(() => setCompanies([]));
    }
  }, [selectedSector]);

  const loadCompanyDetail = async (ticker: string) => {
    setSelectedCompany(ticker);
    try {
      const r = await fetch(`${API}/api/companies/${ticker}`);
      const data = await r.json();
      setCompanyDetail(data);
    } catch { setCompanyDetail(null); }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
  };

  const handleSubmitManual = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/benchmark`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: formData.company_name, sector_code: formData.sector_code,
          current_assets: Number(formData.current_assets), current_liabilities: Number(formData.current_liabilities),
          ebit: Number(formData.ebit), interest_expense: Number(formData.interest_expense),
          ebitda: Number(formData.ebitda || formData.ebit),
          total_debt: Number(formData.total_debt), total_equity: Number(formData.total_equity),
          long_term_debt: Number(formData.long_term_debt || 0),
          total_assets: Number(formData.total_assets || 0),
          gross_profit: Number(formData.gross_profit || 0),
          net_income: Number(formData.net_income || 0),
          revenue: Number(formData.revenue || 0),
          free_operating_cash_flow: Number(formData.free_operating_cash_flow),
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed");
      setResult(data);
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally { setLoading(false); }
  };

  const handleSubmitPDF = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setLoading(true);
    const fd = new FormData();
    fd.append("file", selectedFile);
    try {
      const response = await fetch(`${API}/api/upload-pdf`, { method: "POST", body: fd });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed");
      setResult(data.benchmark_result);
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally { setLoading(false); }
  };

  const runEtl = async () => {
    setEtlRunning(true);
    try {
      const r = await fetch(`${API}/api/etl/idx-download`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sector_filter: null, year: 2024, limit: 20 }),
      });
      const data = await r.json();
      alert(data.message || "ETL completed!");
      // Refresh companies
      if (selectedSector) {
        const cr = await fetch(`${API}/api/companies?sector=${selectedSector}`);
        setCompanies(await cr.json());
      }
    } catch (error: any) {
      alert(`ETL Error: ${error.message}`);
    } finally { setEtlRunning(false); }
  };

  const downloadPdf = async () => {
    if (!result) return;
    try {
      const response = await fetch(`${API}/api/benchmark/report-from-result`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(result),
      });
      if (!response.ok) throw new Error("Failed to generate PDF");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `benchmark_${result.company?.replace(/\s+/g, "_") || "report"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      alert(`PDF Error: ${error.message}`);
    }
  };

  const getPredicateColor = (predicate: string) => {
    switch (predicate) {
      case "Sangat Sehat": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "Sehat": return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "Cukup Sehat": return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      case "Kurang Sehat": return "bg-orange-500/10 text-orange-400 border-orange-500/20";
      default: return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    }
  };

  const getLevelColor = (score: number | null) => {
    if (!score) return "text-neutral-500";
    if (score >= 76) return "text-emerald-400";
    if (score >= 51) return "text-blue-400";
    if (score >= 26) return "text-yellow-400";
    return "text-rose-400";
  };

  const formatNum = (v: number | null | undefined) => v != null ? v.toLocaleString("id-ID", { maximumFractionDigits: 4 }) : "—";

  const inputCls = "w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500";
  const labelCls = "block text-xs font-medium text-neutral-400 mb-1";

  return (
    <main className="min-h-screen bg-neutral-950 text-white p-6 md:p-8 font-sans selection:bg-emerald-500 selection:text-white pb-20">
      <div className="max-w-7xl mx-auto space-y-10">
        {/* Header */}
        <header className="space-y-4 text-center py-8">
          <div className="inline-block px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-medium border border-emerald-500/20 mb-4">
            Financial Data Warehouse & Analytics
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-200 to-neutral-500">
            Industrial Benchmark<br />& Risk Analysis
          </h1>
          <p className="text-neutral-400 max-w-2xl mx-auto">
            {sectors.length} IDX sectors loaded • {companies.length} companies in {selectedSector}
          </p>
        </header>

        {/* Tab Navigation */}
        <div className="flex space-x-2 bg-neutral-900/50 p-1.5 rounded-xl border border-neutral-800 max-w-lg mx-auto">
          {(["explorer", "manual", "pdf"] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all capitalize ${activeTab === tab ? "bg-neutral-800 text-white shadow-sm" : "text-neutral-400 hover:text-white"}`}>
              {tab === "explorer" ? "Explorer" : tab === "manual" ? "Manual Entry" : "PDF Upload"}
            </button>
          ))}
        </div>

        {/* ═══════════ EXPLORER TAB ═══════════ */}
        {activeTab === "explorer" && (
          <div className="grid lg:grid-cols-12 gap-6">
            {/* Sidebar */}
            <div className="lg:col-span-4 space-y-4">
              {/* Sector Picker + ETL */}
              <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white">Sectors</h3>
                  <button onClick={runEtl} disabled={etlRunning}
                    className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition disabled:opacity-50">
                    {etlRunning ? "Pulling..." : "Pull IDX Data"}
                  </button>
                </div>
                <select value={selectedSector} onChange={e => setSelectedSector(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-emerald-500">
                  {sectors.map(s => <option key={s.code} value={s.code}>{s.name_en} ({s.code})</option>)}
                </select>
              </div>

              {/* Company List */}
              <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-5 space-y-2 max-h-[500px] overflow-y-auto">
                <h3 className="font-semibold text-white mb-3">Companies ({companies.length})</h3>
                {companies.length === 0 ? (
                  <p className="text-neutral-500 text-sm">No companies found. Run ETL to pull data.</p>
                ) : companies.map(c => (
                  <button key={c.ticker} onClick={() => loadCompanyDetail(c.ticker)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all ${selectedCompany === c.ticker ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "text-neutral-300 hover:bg-neutral-800 border border-transparent"}`}>
                    <span className="font-mono font-bold">{c.ticker}</span>
                    <span className="text-neutral-500 ml-2 text-xs">{c.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Company Detail */}
            <div className="lg:col-span-8">
              {companyDetail ? (
                <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold">{companyDetail.company?.ticker}</h2>
                      <p className="text-neutral-400">{companyDetail.company?.name}</p>
                    </div>
                    {companyDetail.sector && (
                      <span className="px-3 py-1 rounded-full bg-neutral-800 text-neutral-300 text-xs border border-neutral-700">
                        {companyDetail.sector.name_en}
                      </span>
                    )}
                  </div>

                  {companyDetail.periods?.map((p: any) => (
                    <div key={p.period_id} className="space-y-3">
                      <h3 className="text-sm font-semibold text-emerald-400 border-b border-neutral-800 pb-2">
                        FY {p.fiscal_year} ({p.period_type}) — {p.source}
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {p.metrics?.slice(0, 30).map((m: any) => (
                          <div key={m.code} className="bg-neutral-950 rounded-lg p-3 border border-neutral-800/50">
                            <p className="text-[10px] text-neutral-500 uppercase tracking-wider">{m.name_en}</p>
                            <p className="text-sm font-mono text-white mt-0.5">
                              {m.value != null ? (m.unit === "IDR" ? (m.value / 1e9).toFixed(2) + "B" : m.value.toFixed(4)) : "—"}
                            </p>
                          </div>
                        ))}
                      </div>
                      {p.metrics?.length > 30 && (
                        <p className="text-xs text-neutral-500">+ {p.metrics.length - 30} more metrics</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center text-center min-h-[400px]">
                  <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-4"><svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13h2v8H3zm6-4h2v12H9zm6-3h2v15h-2zm6-2h2v17h-2z" /></svg></div>
                  <h3 className="text-xl font-semibold text-neutral-300">Select a Company</h3>
                  <p className="text-neutral-500 mt-2 max-w-sm">Choose a sector and click on a company to view its financial data and computed ratios.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ═══════════ MANUAL TAB ═══════════ */}
        {activeTab === "manual" && (
          <div className="grid lg:grid-cols-12 gap-8">
            <section className="lg:col-span-5 bg-neutral-900/50 backdrop-blur-xl border border-neutral-800 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 -mt-20 -mr-20 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
              <form onSubmit={handleSubmitManual} className="space-y-4 relative z-10">
                <div className="grid grid-cols-2 gap-4">
                  <div><label className={labelCls}>Company Name</label>
                    <input type="text" name="company_name" required value={formData.company_name} onChange={handleChange} className={inputCls} placeholder="PT ABC Tbk" /></div>
                  <div><label className={labelCls}>Sector</label>
                    <select name="sector_code" value={formData.sector_code} onChange={handleChange} className={inputCls}>
                      {sectors.map(s => <option key={s.code} value={s.code}>{s.code}</option>)}
                    </select></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className={labelCls}>Current Assets</label><input type="number" step="any" name="current_assets" required value={formData.current_assets} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                  <div><label className={labelCls}>Current Liabilities</label><input type="number" step="any" name="current_liabilities" required value={formData.current_liabilities} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className={labelCls}>EBIT</label><input type="number" step="any" name="ebit" required value={formData.ebit} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                  <div><label className={labelCls}>Interest Expense</label><input type="number" step="any" name="interest_expense" required value={formData.interest_expense} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className={labelCls}>Total Debt (TL)</label><input type="number" step="any" name="total_debt" required value={formData.total_debt} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                  <div><label className={labelCls}>Total Equity (NW)</label><input type="number" step="any" name="total_equity" required value={formData.total_equity} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                </div>
                <div><label className={labelCls}>Free Operating Cash Flow (FOCF)</label><input type="number" step="any" name="free_operating_cash_flow" required value={formData.free_operating_cash_flow} onChange={handleChange} className={inputCls} placeholder="0" /></div>
                <button type="submit" disabled={loading}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50 mt-2">
                  {loading ? "Calculating..." : "Calculate Benchmark"}
                </button>
              </form>
            </section>

            {/* Result Panel */}
            <section className="lg:col-span-7">
              {result ? (
                <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                    <span className="text-8xl font-black">{result.average_score}</span>
                  </div>
                  <div className="flex items-center justify-between mb-6 relative z-10">
                    <div>
                      <h2 className="text-2xl font-bold">Health Report</h2>
                      <p className="text-neutral-400">{result.company} — <span className="text-neutral-500">{result.sector_code}</span></p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-neutral-500 mb-1">Avg: <span className="text-white font-bold">{result.average_score}</span></div>
                      <span className={`px-4 py-1.5 rounded-full text-sm font-bold border ${getPredicateColor(result.health_predicate)}`}>
                        {result.health_predicate}
                      </span>
                    </div>
                  </div>
                  <div className="grid sm:grid-cols-2 gap-3 relative z-10">
                    {result.score_details?.map(d => (
                      <div key={d.ratio_code} className={`bg-neutral-950 p-4 rounded-xl border border-neutral-800/50 ${d.ratio_code === "focf_to_total_debt" ? "sm:col-span-2" : ""}`}>
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-neutral-400 text-xs font-medium mb-1">{d.ratio_code.replace(/_/g, " ").toUpperCase()}</p>
                            <p className="text-2xl font-mono font-semibold text-white">{formatNum(d.ratio_value)}</p>
                          </div>
                          <div className="text-right">
                            <div className={`text-xs font-mono font-bold ${getLevelColor(d.score)}`}>Score: {d.score ?? "—"}</div>
                            <div className="text-[10px] text-neutral-500 mt-0.5">{d.level_label}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <button onClick={downloadPdf}
                    className="mt-4 w-full py-2.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-sm font-medium border border-neutral-700 transition-all flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3" /></svg>
                    Download PDF Report
                  </button>
                </div>
              ) : (
                <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-2xl p-8 min-h-[400px] flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-2"><svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>
                  <h3 className="text-xl font-semibold text-neutral-300">Awaiting Data</h3>
                  <p className="text-neutral-500 max-w-sm">Enter financial data and click Calculate to see the benchmark result.</p>
                </div>
              )}
            </section>
          </div>
        )}

        {/* ═══════════ PDF TAB ═══════════ */}
        {activeTab === "pdf" && (
          <div className="grid lg:grid-cols-12 gap-8">
            <section className="lg:col-span-5 bg-neutral-900/50 border border-neutral-800 rounded-2xl p-6">
              <form onSubmit={handleSubmitPDF} className="space-y-5">
                <div className="border-2 border-dashed border-neutral-700 rounded-2xl p-10 text-center hover:border-emerald-500/50 transition-colors cursor-pointer bg-neutral-950/50"
                  onClick={() => fileInputRef.current?.click()}>
                  <input type="file" ref={fileInputRef} className="hidden" accept=".pdf" onChange={handleFileChange} />
                  <div className="w-16 h-16 mx-auto bg-neutral-800 rounded-full flex items-center justify-center mb-4"><svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg></div>
                  <h3 className="text-lg font-medium text-white mb-1">{selectedFile ? selectedFile.name : "Click to upload PDF"}</h3>
                  <p className="text-sm text-neutral-500">Upload an Annual Report (LK Tahunan) PDF</p>
                </div>
                <button type="submit" disabled={loading || !selectedFile}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3.5 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50">
                  {loading ? "Extracting..." : "Extract PDF & Analyze"}
                </button>
              </form>
            </section>
            <section className="lg:col-span-7">
              {result ? (
                <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8 relative overflow-hidden">
                  <div className="flex items-center justify-between mb-6">
                    <div><h2 className="text-2xl font-bold">PDF Result</h2><p className="text-neutral-400">{result.company}</p></div>
                    <span className={`px-4 py-1.5 rounded-full text-sm font-bold border ${getPredicateColor(result.health_predicate)}`}>{result.health_predicate}</span>
                  </div>
                  <div className="grid sm:grid-cols-2 gap-3">
                    {result.score_details?.map(d => (
                      <div key={d.ratio_code} className="bg-neutral-950 p-4 rounded-xl border border-neutral-800/50">
                        <p className="text-neutral-400 text-xs mb-1">{d.ratio_code.replace(/_/g, " ")}</p>
                        <p className="text-xl font-mono text-white">{formatNum(d.ratio_value)}</p>
                        <p className={`text-xs mt-1 ${getLevelColor(d.score)}`}>{d.level_label} — Score: {d.score ?? "—"}</p>
                      </div>
                    ))}
                  </div>
                  <button onClick={downloadPdf}
                    className="mt-4 w-full py-2.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-sm font-medium border border-neutral-700 transition-all flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3" /></svg>
                    Download PDF Report
                  </button>
                </div>
              ) : (
                <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-2xl p-8 min-h-[400px] flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-2"><svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>
                  <h3 className="text-xl font-semibold text-neutral-300">Upload PDF</h3>
                  <p className="text-neutral-500 max-w-sm">Upload an Annual Report PDF to automatically extract financial data and calculate benchmark.</p>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
