import type { ScoreDetail } from "@/types";

interface ScoreCardProps {
  detail: ScoreDetail;
  fullWidth?: boolean;
}

function getLevelColor(score: number | null): string {
  if (!score) return "text-neutral-500";
  if (score >= 76) return "text-emerald-400";
  if (score >= 51) return "text-blue-400";
  if (score >= 26) return "text-yellow-400";
  return "text-rose-400";
}

function formatNum(v: number | null | undefined): string {
  return v != null ? v.toLocaleString("id-ID", { maximumFractionDigits: 4 }) : "—";
}

export default function ScoreCard({ detail, fullWidth = false }: ScoreCardProps) {
  return (
    <div
      className={`bg-neutral-950 p-4 rounded-xl border border-neutral-800/50 ${
        fullWidth ? "sm:col-span-2" : ""
      }`}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="text-neutral-400 text-xs font-medium mb-1">
            {detail.ratio_code.replace(/_/g, " ").toUpperCase()}
          </p>
          <p className="text-2xl font-mono font-semibold text-white">
            {formatNum(detail.ratio_value)}
          </p>
        </div>
        <div className="text-right">
          <div className={`text-xs font-mono font-bold ${getLevelColor(detail.score)}`}>
            Score: {detail.score ?? "—"}
          </div>
          <div className="text-[10px] text-neutral-500 mt-0.5">{detail.level_label}</div>
        </div>
      </div>
    </div>
  );
}
