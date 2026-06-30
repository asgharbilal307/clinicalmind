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
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs uppercase tracking-wider" style={{ color: "var(--color-support)" }}>
            {supportingCount} supporting
          </span>
          <span className="text-xs text-[10px] px-2 py-0.5 rounded-full" style={{ background: "var(--color-support-bg)", color: "var(--color-support)" }}>Support</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[10px] px-2 py-0.5 rounded-full" style={{ background: "var(--color-contradict-bg)", color: "var(--color-contradict)" }}>Contradict</span>
          <span className="font-mono text-xs uppercase tracking-wider" style={{ color: "var(--color-contradict)" }}>
            {contradictingCount} contradicting
          </span>
        </div>
      </div>

      <div className="relative h-4 rounded-full overflow-hidden" style={{ background: "var(--color-background-secondary)" }}>
        <div
          className="absolute inset-y-0 left-0 transition-all duration-700 ease-out"
          style={{
            width: `${supportPct}%`,
            background: "linear-gradient(90deg, var(--color-support), color-mix(in srgb, var(--color-support) 75%, white 25%))",
          }}
        />
        <div
          className="absolute inset-y-0 right-0 transition-all duration-700 ease-out"
          style={{
            width: `${100 - supportPct}%`,
            background: "linear-gradient(90deg, color-mix(in srgb, var(--color-contradict) 75%, white 25%), var(--color-contradict))",
          }}
        />
        {/* fulcrum */}
        <div className="absolute top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full border" style={{ background: "var(--color-paper)", borderColor: "var(--color-border)" }} />
      </div>

      <div className="flex items-center justify-center mt-3">
        <span className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: "var(--color-verdict-bg)", color: "var(--color-verdict)" }}>
          {CONSENSUS_COPY[consensusStrength]} — {consensusStrength}
        </span>
      </div>
    </div>
  );
}