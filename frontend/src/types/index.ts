// Centralized TypeScript type definitions for the Industrial Benchmark app.
// Import from here instead of defining inline types throughout components.

export interface Sector {
  id: number;
  code: string;
  name_id: string;
  name_en: string;
  is_financial: boolean;
}

export interface Company {
  id: number;
  ticker: string;
  name: string;
  sector_id: number | null;
  subsector?: string;
}

export interface MetricValue {
  code: string;
  name_id: string;
  name_en: string;
  category: string;
  unit: string;
  value: number | null;
}

export interface FinancialPeriod {
  period_id: number;
  fiscal_year: number;
  period_type: string;
  source: string;
  metrics: MetricValue[];
}

export interface CompanyDetail {
  company: Company;
  sector: Sector | null;
  periods: FinancialPeriod[];
}

export interface ScoreDetail {
  ratio_code: string;
  ratio_value: number | null;
  level_label: string | null;
  score: number | null;
}

export interface BenchmarkResult {
  company: string;
  sector_code: string;
  ratios: Record<string, number | null>;
  scores: Record<string, number | null>;
  score_details: ScoreDetail[];
  average_score: number;
  health_predicate: string;
}

export interface LeaderboardEntry {
  ticker: string;
  company_name: string;
  score: number;
  predicate: string;
}

export type TabId = "explorer" | "leaderboard" | "manual" | "upload";
export type ExplorerTabId = "laporan" | "analisa";
