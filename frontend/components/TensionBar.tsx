"use client";

import { ConsensusStrength } from "@/lib/api";

interface TensionBarProps {
  supportingCount: number;
  contradictingCount: number;
  consensusStrength: ConsensusStrength;
}

const CONSENSUS_COPY: Record<ConsensusStrength, string> = {
  "Strong support": "Evidence strongly converges",
  "Moderate support": "Evidence leans one way",
  "Weak support": "Evidence tilts slightly",
  Contested: "Evidence is genuinely split",
  "Insufficient evidence": "Not enough evidence to judge",
};

export function TensionBar({
  supportingCount,
  contradictingCount,
  consensusStrength,
}: TensionBarProps) {
  const total = supportingCount + contradictingCount;
  const supportPct = total === 0 ? 50 : (supportingCount / total) * 100;

  return (
    <div className="w-full p-6 rounded-2xl" style={{ background: "rgba(255, 255, 255, 0.9)", boxShadow: "0 8px 24px rgba(15, 110, 86, 0.08)", border: "1px solid rgba(15, 110, 86, 0.1)" }}>
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-bold" style={{ color: "var(--color-support)" }}>
            🟢 {supportingCount} Supporting
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-bold" style={{ color: "var(--color-contradict)" }}>
            🔴 {contradictingCount} Contradicting
          </span>
        </div>
      </div>

      <div className="relative h-6 rounded-full overflow-hidden mb-5" style={{ background: "rgba(0, 0, 0, 0.05)", border: "1px solid rgba(0, 0, 0, 0.08)" }}>
        <div
          className="absolute inset-y-0 left-0 transition-all duration-700 ease-out"
          style={{
            width: `${supportPct}%`,
            background: "linear-gradient(90deg, #0F6E56, #1A8E72)",
            boxShadow: "inset -2px 0 4px rgba(0, 0, 0, 0.1)"
          }}
        />
        <div
          className="absolute inset-y-0 right-0 transition-all duration-700 ease-out"
          style={{
            width: `${100 - supportPct}%`,
            background: "linear-gradient(90deg, #B8462F, #D65940)",
            boxShadow: "inset 2px 0 4px rgba(0, 0, 0, 0.1)"
          }}
        />
        {/* fulcrum */}
        <div className="absolute top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full border-2" style={{ background: "white", borderColor: "var(--color-accent)", boxShadow: "0 2px 6px rgba(0, 0, 0, 0.15)" }} />
      </div>

      <div className="flex items-center justify-center">
        <span className="px-4 py-2 rounded-full text-sm font-semibold" style={{ background: "var(--color-verdict-bg)", color: "var(--color-verdict)" }}>
          {CONSENSUS_COPY[consensusStrength]} — <strong>{consensusStrength}</strong>
        </span>
      </div>
    </div>
  );
}