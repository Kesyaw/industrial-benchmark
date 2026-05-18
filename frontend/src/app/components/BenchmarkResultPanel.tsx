import type { BenchmarkResult } from "@/types";
import { api } from "@/lib/api";
import ScoreCard from "./ScoreCard";

interface BenchmarkResultPanelProps {
  result: BenchmarkResult;
  /** Optional variant for compact mode (e.g. Explorer tab) */
  compact?: boolean;
}

function getPredicateColor(predicate: string): string {
  switch (predicate) {
    case "Sangat Sehat": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    case "Sehat":        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    case "Cukup Sehat":  return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
    case "Kurang Sehat": return "bg-orange-500/10 text-orange-400 border-orange-500/20";
    default:             return "bg-rose-500/10 text-rose-400 border-rose-500/20";
  }
}

async function handleDownloadPdf(result: BenchmarkResult) {
  try {
    const blob = await api.downloadPdfReport(result);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark_${(result.company || "report").replace(/\s+/g, "_")}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err: unknown) {
    alert(`PDF Error: ${err instanceof Error ? err.message : "Unknown error"}`);
  }
}

export default function BenchmarkResultPanel({ result, compact = false }: BenchmarkResultPanelProps) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 relative overflow-hidden">
      {/* Score watermark (only in non-compact mode) */}
      {!compact && (
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <span className="text-8xl font-black">{result.average_score}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div>
          <h2 className="text-xl font-bold">Analysis Result</h2>
          <p className="text-neutral-400">{result.company}</p>
        </div>
        <div className="text-right">
          {!compact && (
            <div className="text-sm text-neutral-500 mb-1">
              Avg: <span className="text-white font-bold">{result.average_score}</span>
            </div>
          )}
          <span className={`px-4 py-1.5 rounded-full text-sm font-bold border ${getPredicateColor(result.health_predicate)}`}>
            {result.health_predicate}
          </span>
        </div>
      </div>

      {/* Score Cards Grid */}
      <div className="grid sm:grid-cols-2 gap-3 relative z-10">
        {result.score_details?.map((d) => (
          <ScoreCard
            key={d.ratio_code}
            detail={d}
            fullWidth={d.ratio_code === "focf_to_total_debt"}
          />
        ))}
      </div>

      {/* Download Button */}
      <button
        onClick={() => handleDownloadPdf(result)}
        className="mt-4 w-full py-2.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-sm font-medium border border-neutral-700 transition-all flex items-center justify-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3" />
        </svg>
        Download PDF Report
      </button>
    </div>
  );
}
