import type { Sector } from "@/types";

interface SectorSelectProps {
  sectors: Sector[];
  value: string;
  onChange: (code: string) => void;
  className?: string;
}

export default function SectorSelect({ sectors, value, onChange, className = "" }: SectorSelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 ${className}`}
    >
      {sectors.map((s) => (
        <option key={s.code} value={s.code}>
          {s.name_en} ({s.code})
        </option>
      ))}
    </select>
  );
}
