"use client";

import { StanceResult } from "@/lib/api";

interface ForestPlotProps {
  supporting: StanceResult[];
  contradicting: StanceResult[];
}

const QUALITY_OPACITY: Record<string, number> = {
  high: 1.0,
  medium: 0.65,
  low: 0.35,
  unknown: 0.5,
};

const STUDY_TYPE_SHORT: Record<string, string> = {
  "meta-analysis": "MA",
  "systematic-review": "SR",
  rct: "RCT",
  cohort: "Cohort",
  "case-control": "CC",
  "case-report": "CR",
  unknown: "—",
};

function ForestBar({
  study,
  direction,
  maxConfidence,
}: {
  study: StanceResult;
  direction: "support" | "contradict";
  maxConfidence: number;
}) {
  const pct = maxConfidence > 0 ? (study.confidence / maxConfidence) * 100 : 50;
  const opacity = QUALITY_OPACITY[study.quality_score ?? "unknown"];
  const color =
    direction === "support" ? "var(--color-support)" : "var(--color-contradict)";
  const align = direction === "support" ? "flex-start" : "flex-end";

  const label = study.title.length > 48
    ? study.title.slice(0, 48) + "…"
    : study.title;

  return (
    <a
      href={`https://pubmed.ncbi.nlm.nih.gov/${study.pmid}/`}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-center gap-3 py-1.5 hover:bg-black/[0.02] rounded-lg px-2 transition-colors"
      style={{ textDecoration: "none" }}
    >
      {/* Study label — left side */}
      <div className="flex items-center gap-1.5 w-52 shrink-0">
        <span
          className="font-mono text-[10px] px-1.5 py-0.5 rounded shrink-0"
          style={{
            background: "var(--color-background-secondary)",
            color: "var(--color-text-secondary)",
          }}
        >
          {STUDY_TYPE_SHORT[study.study_type] ?? "—"}
        </span>
        <span
          className="text-[11px] truncate group-hover:underline"
          style={{ color: "var(--color-text-secondary)" }}
          title={study.title}
        >
          {label}
        </span>
      </div>

      {/* Bar track */}
      <div className="flex-1 relative h-5 flex items-center">
        {/* Center axis line */}
        <div
          className="absolute inset-y-0 left-1/2 w-px"
          style={{ background: "var(--color-border-secondary)" }}
        />

        {/* Bar — grows from center outward */}
        <div
          className="absolute inset-y-1 flex items-center"
          style={{
            [direction === "support" ? "left" : "right"]: "50%",
            width: `${pct / 2}%`,
            justifyContent: align,
          }}
        >
          <div
            className="h-full rounded-sm transition-all duration-500"
            style={{
              width: "100%",
              background: color,
              opacity,
            }}
          />
        </div>
      </div>

      {/* Confidence % — right side */}
      <span
        className="font-mono text-[10px] w-9 text-right shrink-0"
        style={{ color: "var(--color-text-tertiary)" }}
      >
        {Math.round(study.confidence * 100)}%
      </span>

      {/* Sample size — optional */}
      <span
        className="font-mono text-[10px] w-14 text-right shrink-0 hidden sm:block"
        style={{ color: "var(--color-text-tertiary)" }}
      >
        {study.sample_size ? `n=${study.sample_size.toLocaleString()}` : ""}
      </span>
    </a>
  );
}

export function ForestPlot({ supporting, contradicting }: ForestPlotProps) {
  const all = [...supporting, ...contradicting];
  if (all.length === 0) return null;

  const maxConfidence = Math.max(...all.map((s) => s.confidence));

  // Sort each camp: highest confidence first, then by sample size
  const sortedSupporting = [...supporting].sort(
    (a, b) =>
      b.confidence - a.confidence ||
      (b.sample_size ?? 0) - (a.sample_size ?? 0)
  );
  const sortedContradicting = [...contradicting].sort(
    (a, b) =>
      b.confidence - a.confidence ||
      (b.sample_size ?? 0) - (a.sample_size ?? 0)
  );

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "var(--color-background-primary)",
        border: "1px solid var(--color-border-tertiary)",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: "var(--color-border-tertiary)" }}
      >
        <div className="flex items-center gap-2">
          <span
            className="font-mono text-[10px] uppercase tracking-wider"
            style={{ color: "var(--color-text-secondary)" }}
          >
            Forest Plot
          </span>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full"
            style={{
              background: "var(--color-background-secondary)",
              color: "var(--color-text-tertiary)",
            }}
          >
            bar length = classifier confidence · opacity = study quality
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <span style={{ color: "var(--color-contradict)" }}>← Contradicts</span>
          <span style={{ color: "var(--color-support)" }}>Supports →</span>
        </div>
      </div>

      {/* Column headers */}
      <div
        className="flex items-center gap-3 px-4 py-1.5 border-b"
        style={{
          borderColor: "var(--color-border-tertiary)",
          background: "var(--color-background-secondary)",
        }}
      >
        <div className="w-52 shrink-0" />
        <div className="flex-1" />
        <span
          className="font-mono text-[10px] w-9 text-right shrink-0"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Conf.
        </span>
        <span
          className="font-mono text-[10px] w-14 text-right shrink-0 hidden sm:block"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Sample
        </span>
      </div>

      <div className="px-2 py-2">
        {/* Supporting studies */}
        {sortedSupporting.length > 0 && (
          <div className="mb-1">
            <p
              className="font-mono text-[10px] uppercase tracking-wider px-2 py-1"
              style={{ color: "var(--color-support)" }}
            >
              Supporting ({sortedSupporting.length})
            </p>
            {sortedSupporting.map((s) => (
              <ForestBar
                key={s.pmid}
                study={s}
                direction="support"
                maxConfidence={maxConfidence}
              />
            ))}
          </div>
        )}

        {/* Divider */}
        {sortedSupporting.length > 0 && sortedContradicting.length > 0 && (
          <div
            className="my-2 border-t border-dashed"
            style={{ borderColor: "var(--color-border-tertiary)" }}
          />
        )}

        {/* Contradicting studies */}
        {sortedContradicting.length > 0 && (
          <div>
            <p
              className="font-mono text-[10px] uppercase tracking-wider px-2 py-1"
              style={{ color: "var(--color-contradict)" }}
            >
              Contradicting ({sortedContradicting.length})
            </p>
            {sortedContradicting.map((s) => (
              <ForestBar
                key={s.pmid}
                study={s}
                direction="contradict"
                maxConfidence={maxConfidence}
              />
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div
        className="flex items-center gap-4 px-4 py-2 border-t"
        style={{
          borderColor: "var(--color-border-tertiary)",
          background: "var(--color-background-secondary)",
        }}
      >
        <span
          className="text-[10px]"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Quality:
        </span>
        {[
          { label: "High", opacity: 1.0 },
          { label: "Medium", opacity: 0.65 },
          { label: "Low", opacity: 0.35 },
        ].map(({ label, opacity }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div
              className="w-6 h-2.5 rounded-sm"
              style={{
                background: "var(--color-support)",
                opacity,
              }}
            />
            <span
              className="text-[10px]"
              style={{ color: "var(--color-text-tertiary)" }}
            >
              {label}
            </span>
          </div>
        ))}
        <span
          className="text-[10px] ml-auto"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Click any row to open study on PubMed
        </span>
      </div>
    </div>
  );
}