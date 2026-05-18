/**
 * API client library — centralizes all fetch calls to the backend.
 * Base URL is read from NEXT_PUBLIC_API_URL env var with localhost fallback.
 */
import type { Sector, Company, CompanyDetail, BenchmarkResult, LeaderboardEntry } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

export const api = {
  getSectors: (): Promise<Sector[]> =>
    apiFetch("/api/sectors"),

  getCompanies: (sector: string): Promise<Company[]> =>
    apiFetch(`/api/companies?sector=${sector}`),

  getCompanyDetail: (ticker: string): Promise<CompanyDetail> =>
    apiFetch(`/api/companies/${ticker}`),

  getCompanyBenchmark: (ticker: string, year: number): Promise<BenchmarkResult> =>
    apiFetch(`/api/companies/${ticker}/benchmark/${year}`),

  getSectorLeaderboard: (sectorCode: string, year = 2025): Promise<{ leaderboard: LeaderboardEntry[] }> =>
    apiFetch(`/api/benchmark/sector/${sectorCode}/year/${year}`),

  postBenchmark: (data: Record<string, unknown>): Promise<BenchmarkResult> =>
    apiFetch("/api/benchmark", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  uploadReport: (file: File): Promise<{ benchmark_result: BenchmarkResult }> => {
    const fd = new FormData();
    fd.append("file", file);
    return apiFetch("/api/upload-pdf", { method: "POST", body: fd });
  },

  downloadPdfReport: async (result: BenchmarkResult): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/benchmark/report-from-result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    });
    if (!res.ok) throw new Error("Failed to generate PDF");
    return res.blob();
  },
};
