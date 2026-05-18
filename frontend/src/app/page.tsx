"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import type {
  Sector, Company, CompanyDetail, BenchmarkResult,
  LeaderboardEntry, TabId, ExplorerTabId,
} from "@/types";
import SectorSelect from "./components/SectorSelect";
import BenchmarkResultPanel from "./components/BenchmarkResultPanel";

// ── Shared style constants ──────────────────────────────────────────────────
const INPUT_CLS = "w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500";
const LABEL_CLS = "block text-xs font-medium text-neutral-400 mb-1";

function getPredicateColor(predicate: string): string {
  switch (predicate) {
    case "Sangat Sehat": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    case "Sehat":        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    case "Cukup Sehat":  return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
    case "Kurang Sehat": return "bg-orange-500/10 text-orange-400 border-orange-500/20";
    default:             return "bg-rose-500/10 text-rose-400 border-rose-500/20";
  }
}

// ── Initial form state ──────────────────────────────────────────────────────
const INITIAL_FORM = {
  company_name: "", sector_code: "TRADE",
  current_assets: "", current_liabilities: "", ebit: "", interest_expense: "",
  ebitda: "", total_debt: "", total_equity: "", long_term_debt: "",
  total_assets: "", gross_profit: "", net_income: "", revenue: "",
  free_operating_cash_flow: "",
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════════
export default function Home() {
  // ── State ────────────────────────────────────────────────────────────────
  const [sectors, setSectors]               = useState<Sector[]>([]);
  const [companies, setCompanies]           = useState<Company[]>([]);
  const [selectedSector, setSelectedSector] = useState("TRADE");
  const [selectedCompany, setSelectedCompany] = useState("");
  const [companyDetail, setCompanyDetail]   = useState<CompanyDetail | null>(null);

  const [activeTab, setActiveTab]         = useState<TabId>("explorer");
  const [explorerTab, setExplorerTab]     = useState<ExplorerTabId>("laporan");
  const [explorerResult, setExplorerResult] = useState<BenchmarkResult | null>(null);
  const [loadingBenchmark, setLoadingBenchmark] = useState(false);

  const [leaderboard, setLeaderboard]           = useState<LeaderboardEntry[]>([]);
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);

  const [formData, setFormData] = useState(INITIAL_FORM);
  const [manualResult, setManualResult] = useState<BenchmarkResult | null>(null);
  const [uploadResult, setUploadResult] = useState<BenchmarkResult | null>(null);
  const [loading, setLoading]           = useState(false);

  const fileInputRef   = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // ── Data loading ─────────────────────────────────────────────────────────
  useEffect(() => {
    api.getSectors().then(setSectors).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedSector) {
      api.getCompanies(selectedSector).then(setCompanies).catch(() => setCompanies([]));
    }
  }, [selectedSector]);

  useEffect(() => {
    if (activeTab === "leaderboard" && selectedSector) {
      loadLeaderboard(selectedSector);
    }
  }, [activeTab, selectedSector]);

  // ── Handlers ─────────────────────────────────────────────────────────────
  const loadCompanyDetail = async (ticker: string) => {
    setSelectedCompany(ticker);
    setExplorerTab("laporan");
    setExplorerResult(null);
    try {
      const data = await api.getCompanyDetail(ticker);
      setCompanyDetail(data);
    } catch {
      setCompanyDetail(null);
    }
  };

  const loadBenchmark = async (ticker: string, year: number) => {
    setLoadingBenchmark(true);
    try {
      const data = await api.getCompanyBenchmark(ticker, year);
      setExplorerResult(data);
    } catch {
      setExplorerResult(null);
    } finally {
      setLoadingBenchmark(false);
    }
  };

  const loadLeaderboard = async (sectorCode: string) => {
    setLoadingLeaderboard(true);
    try {
      const data = await api.getSectorLeaderboard(sectorCode);
      setLeaderboard(data.leaderboard || []);
    } catch {
      setLeaderboard([]);
    } finally {
      setLoadingLeaderboard(false);
    }
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmitManual = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await api.postBenchmark({
        ...formData,
        current_assets:           Number(formData.current_assets),
        current_liabilities:      Number(formData.current_liabilities),
        ebit:                     Number(formData.ebit),
        interest_expense:         Number(formData.interest_expense),
        ebitda:                   Number(formData.ebitda || formData.ebit),
        total_debt:               Number(formData.total_debt),
        total_equity:             Number(formData.total_equity),
        long_term_debt:           Number(formData.long_term_debt || 0),
        total_assets:             Number(formData.total_assets || 0),
        gross_profit:             Number(formData.gross_profit || 0),
        net_income:               Number(formData.net_income || 0),
        revenue:                  Number(formData.revenue || 0),
        free_operating_cash_flow: Number(formData.free_operating_cash_flow),
      });
      setManualResult(result);
    } catch (err: unknown) {
      alert(`Error: ${err instanceof Error ? err.message : "Failed"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setLoading(true);
    try {
      const data = await api.uploadReport(selectedFile);
      setUploadResult(data.benchmark_result);
    } catch (err: unknown) {
      alert(`Error: ${err instanceof Error ? err.message : "Failed"}`);
    } finally {
      setLoading(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
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
        <div className="flex space-x-2 bg-neutral-900/50 p-1.5 rounded-xl border border-neutral-800 max-w-2xl mx-auto">
          {(["explorer", "leaderboard", "manual", "upload"] as TabId[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all capitalize ${
                activeTab === tab
                  ? "bg-neutral-800 text-white shadow-sm"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              {tab === "explorer"    ? "Explorer"
               : tab === "leaderboard" ? "Sector Leaderboard"
               : tab === "manual"      ? "Manual Entry"
               : "Report Upload"}
            </button>
          ))}
        </div>

        {/* ═══ EXPLORER TAB ═══ */}
        {activeTab === "explorer" && (
          <div className="grid lg:grid-cols-12 gap-6">
            {/* Sidebar */}
            <div className="lg:col-span-4 space-y-4">
              <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-5 space-y-4">
                <h3 className="font-semibold text-white">Sectors</h3>
                <SectorSelect sectors={sectors} value={selectedSector} onChange={setSelectedSector} />
              </div>
              <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-5 space-y-2 max-h-[500px] overflow-y-auto">
                <h3 className="font-semibold text-white mb-3">Companies ({companies.length})</h3>
                {companies.length === 0 ? (
                  <p className="text-neutral-500 text-sm">No companies found.</p>
                ) : companies.map((c) => (
                  <button key={c.ticker} onClick={() => loadCompanyDetail(c.ticker)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all ${
                      selectedCompany === c.ticker
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "text-neutral-300 hover:bg-neutral-800 border border-transparent"
                    }`}>
                    <span className="font-mono font-bold">{c.ticker}</span>
                    <span className="text-neutral-500 ml-2 text-xs">{c.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Company Detail Panel */}
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

                  {/* Sub-tabs */}
                  <div className="flex space-x-6 border-b border-neutral-800">
                    {(["laporan", "analisa"] as ExplorerTabId[]).map((tab) => (
                      <button key={tab}
                        onClick={() => {
                          setExplorerTab(tab);
                          if (tab === "analisa" && !explorerResult && companyDetail.periods?.[0]) {
                            loadBenchmark(companyDetail.company.ticker, companyDetail.periods[0].fiscal_year);
                          }
                        }}
                        className={`pb-2 text-sm font-medium transition-colors ${
                          explorerTab === tab
                            ? "text-emerald-400 border-b-2 border-emerald-400"
                            : "text-neutral-500 hover:text-neutral-300"
                        }`}>
                        {tab === "laporan" ? "Laporan Keuangan" : "Analisa Benchmark"}
                      </button>
                    ))}
                  </div>

                  {explorerTab === "laporan" ? (
                    companyDetail.periods?.map((p) => (
                      <div key={p.period_id} className="space-y-3">
                        <h3 className="text-sm font-semibold text-emerald-400 border-b border-neutral-800 pb-2">
                          FY {p.fiscal_year} ({p.period_type}) — {p.source}
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {p.metrics?.slice(0, 30).map((m) => (
                            <div key={m.code} className="bg-neutral-950 rounded-lg p-3 border border-neutral-800/50">
                              <p className="text-[10px] text-neutral-500 uppercase tracking-wider">{m.name_en}</p>
                              <p className="text-sm font-mono text-white mt-0.5">
                                {m.value != null
                                  ? (m.unit === "IDR" ? (m.value / 1e9).toFixed(2) + "B" : m.value.toFixed(4))
                                  : "—"}
                              </p>
                            </div>
                          ))}
                        </div>
                        {(p.metrics?.length ?? 0) > 30 && (
                          <p className="text-xs text-neutral-500">+ {p.metrics.length - 30} more metrics</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="space-y-6">
                      {loadingBenchmark ? (
                        <p className="text-neutral-500 text-center py-10">Calculating benchmark...</p>
                      ) : explorerResult ? (
                        <BenchmarkResultPanel result={explorerResult} compact />
                      ) : (
                        <p className="text-neutral-500 text-center py-10">No benchmark data available.</p>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center text-center min-h-[400px]">
                  <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13h2v8H3zm6-4h2v12H9zm6-3h2v15h-2zm6-2h2v17h-2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-neutral-300">Select a Company</h3>
                  <p className="text-neutral-500 mt-2 max-w-sm">Choose a sector and click on a company to view its data.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ═══ LEADERBOARD TAB ═══ */}
        {activeTab === "leaderboard" && (
          <div className="grid lg:grid-cols-12 gap-6">
            <div className="lg:col-span-4 space-y-4">
              <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-5 space-y-4">
                <h3 className="font-semibold text-white">Select Sector</h3>
                <SectorSelect sectors={sectors} value={selectedSector} onChange={setSelectedSector} />
              </div>
            </div>
            <div className="lg:col-span-8">
              <div className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-6 min-h-[500px]">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold">Sector Leaderboard (2025)</h2>
                    <p className="text-neutral-400">Comparing companies in {selectedSector}</p>
                  </div>
                </div>
                {loadingLeaderboard ? (
                  <p className="text-neutral-500 text-center py-10">Calculating rankings...</p>
                ) : leaderboard.length > 0 ? (
                  <div className="space-y-3">
                    {leaderboard.map((item, index) => (
                      <div key={item.ticker} className="bg-neutral-950 p-4 rounded-xl border border-neutral-800/50 flex items-center justify-between hover:border-emerald-500/50 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                            index === 0 ? "bg-yellow-500/20 text-yellow-500 border border-yellow-500/50"
                            : index === 1 ? "bg-neutral-400/20 text-neutral-400 border border-neutral-400/50"
                            : index === 2 ? "bg-amber-700/20 text-amber-600 border border-amber-600/50"
                            : "bg-neutral-800 text-neutral-500 border border-neutral-700"
                          }`}>{index + 1}</div>
                          <div>
                            <h4 className="font-bold text-white text-lg leading-none">{item.ticker}</h4>
                            <p className="text-xs text-neutral-500 mt-1">{item.company_name}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xl font-mono font-bold text-white mb-1">{item.score.toFixed(2)}</div>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getPredicateColor(item.predicate)}`}>
                            {item.predicate}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-4">
                      <svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <p className="text-neutral-500">No companies found in this sector for 2025.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ═══ MANUAL TAB ═══ */}
        {activeTab === "manual" && (
          <div className="grid lg:grid-cols-12 gap-8">
            <section className="lg:col-span-5 bg-neutral-900/50 backdrop-blur-xl border border-neutral-800 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 -mt-20 -mr-20 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
              <form onSubmit={handleSubmitManual} className="space-y-4 relative z-10">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={LABEL_CLS}>Company Name</label>
                    <input type="text" name="company_name" required value={formData.company_name}
                      onChange={handleFormChange} className={INPUT_CLS} placeholder="PT ABC Tbk" />
                  </div>
                  <div>
                    <label className={LABEL_CLS}>Sector</label>
                    <select name="sector_code" value={formData.sector_code} onChange={handleFormChange} className={INPUT_CLS}>
                      {sectors.map((s) => <option key={s.code} value={s.code}>{s.code}</option>)}
                    </select>
                  </div>
                </div>
                {[
                  ["current_assets", "Current Assets"], ["current_liabilities", "Current Liabilities"],
                  ["ebit", "EBIT"], ["interest_expense", "Interest Expense"],
                  ["total_debt", "Total Debt (TL)"], ["total_equity", "Total Equity (NW)"],
                ].reduce<[string, string][][]>((rows, field, i) => {
                  if (i % 2 === 0) rows.push([]);
                  rows[rows.length - 1].push(field as [string, string]);
                  return rows;
                }, []).map((pair, i) => (
                  <div key={i} className="grid grid-cols-2 gap-4">
                    {pair.map(([name, label]) => (
                      <div key={name}>
                        <label className={LABEL_CLS}>{label}</label>
                        <input type="number" step="any" name={name} required
                          value={formData[name as keyof typeof formData]}
                          onChange={handleFormChange} className={INPUT_CLS} placeholder="0" />
                      </div>
                    ))}
                  </div>
                ))}
                <div>
                  <label className={LABEL_CLS}>Free Operating Cash Flow (FOCF)</label>
                  <input type="number" step="any" name="free_operating_cash_flow" required
                    value={formData.free_operating_cash_flow}
                    onChange={handleFormChange} className={INPUT_CLS} placeholder="0" />
                </div>
                <button type="submit" disabled={loading}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50 mt-2">
                  {loading ? "Calculating..." : "Calculate Benchmark"}
                </button>
              </form>
            </section>

            <section className="lg:col-span-7">
              {manualResult ? (
                <BenchmarkResultPanel result={manualResult} />
              ) : (
                <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-2xl p-8 min-h-[400px] flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-2">
                    <svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-neutral-300">Awaiting Data</h3>
                  <p className="text-neutral-500 max-w-sm">Enter financial data and click Calculate to see the benchmark result.</p>
                </div>
              )}
            </section>
          </div>
        )}

        {/* ═══ UPLOAD TAB ═══ */}
        {activeTab === "upload" && (
          <div className="grid lg:grid-cols-12 gap-8">
            <section className="lg:col-span-5 bg-neutral-900/50 border border-neutral-800 rounded-2xl p-6">
              <form onSubmit={handleSubmitUpload} className="space-y-5">
                <div className="border-2 border-dashed border-neutral-700 rounded-2xl p-10 text-center hover:border-emerald-500/50 transition-colors cursor-pointer bg-neutral-950/50"
                  onClick={() => fileInputRef.current?.click()}>
                  <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,.xlsx"
                    onChange={(e) => e.target.files?.[0] && setSelectedFile(e.target.files[0])} />
                  <div className="w-16 h-16 mx-auto bg-neutral-800 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-white mb-1">
                    {selectedFile ? selectedFile.name : "Click to upload report"}
                  </h3>
                  <p className="text-sm text-neutral-500">Upload Annual Report (PDF or XLSX)</p>
                </div>
                <button type="submit" disabled={loading || !selectedFile}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3.5 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50">
                  {loading ? "Extracting..." : "Extract Data & Analyze"}
                </button>
              </form>
            </section>

            <section className="lg:col-span-7">
              {uploadResult ? (
                <BenchmarkResultPanel result={uploadResult} />
              ) : (
                <div className="bg-neutral-900/30 border border-neutral-800 border-dashed rounded-2xl p-8 min-h-[400px] flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-neutral-800/50 flex items-center justify-center mb-2">
                    <svg className="w-8 h-8 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-neutral-300">Upload Report</h3>
                  <p className="text-neutral-500 max-w-sm">Upload a PDF or XLSX Annual Report to extract and benchmark.</p>
                </div>
              )}
            </section>
          </div>
        )}

      </div>
    </main>
  );
}
