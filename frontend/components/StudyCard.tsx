"use client";

import { StanceResult } from "@/lib/api";

interface StudyCardProps {
  study: StanceResult;
  variant: "support" | "contradict" | "neutral";
}

const STUDY_TYPE_LABELS: Record<string, string> = {
  "meta-analysis": "Meta-analysis",
  "systematic-review": "Systematic review",
  rct: "RCT",
  cohort: "Cohort study",
  "case-control": "Case-control",
  "case-report": "Case report",
  unknown: "Study",
};

const QUALITY_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  high:    { bg: "#E8F5F0", color: "#085041", label: "High quality" },
  medium:  { bg: "#FBF1DF", color: "#633806", label: "Medium quality" },
  low:     { bg: "#FBEEE9", color: "#7A2E1F", label: "Low quality" },
  unknown: { bg: "var(--color-background-secondary)", color: "var(--color-text-secondary)", label: "Quality unknown" },
};

const FUNDING_LABELS: Record<string, string> = {
  industry:   "💊 Industry",
  government: "🏛 Government",
  university: "🎓 University",
  mixed:      "Mixed funding",
  unknown:    "",
};

const VARIANT_STYLES = {
  support:   { border: "var(--color-support)", badge: "var(--color-support-bg)", badgeText: "var(--color-support)" },
  contradict:{ border: "var(--color-contradict)", badge: "var(--color-contradict-bg)", badgeText: "var(--color-contradict)" },
  neutral:   { border: "var(--color-neutral)", badge: "var(--color-neutral-bg)", badgeText: "var(--color-neutral)" },
};

export function StudyCard({ study, variant }: StudyCardProps) {
  const styles = VARIANT_STYLES[variant];
  const quality = QUALITY_STYLES[study.quality_score ?? "unknown"];
  const fundingLabel = FUNDING_LABELS[study.funding_source ?? "unknown"] ?? "";

  return (
    <a
      href={`https://pubmed.ncbi.nlm.nih.gov/${study.pmid}/`}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-5 rounded-xl bg-white card-hoverable focus-visible:outline-2 focus-visible:outline-offset-2 border transition-colors"
      style={{ 
        borderLeft: `4px solid ${styles.border}`,
        borderColor: "rgba(0, 0, 0, 0.08)",
        outlineColor: styles.border,
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)"
      }}
    >
      {/* Top row — study type + quality + confidence */}
      <div className="flex items-start flex-wrap gap-2 mb-3">
        <span
          className="font-mono text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-semibold"
          style={{ background: styles.badge, color: styles.badgeText }}
        >
          {STUDY_TYPE_LABELS[study.study_type] ?? "Study"}
        </span>

        {study.quality_score && study.quality_score !== "unknown" && (
          <span
            className="font-mono text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-semibold"
            style={{ background: quality.bg, color: quality.color }}
          >
            {quality.label}
          </span>
        )}

        {fundingLabel && (
          <span
            className="font-mono text-[10px] px-2.5 py-1 rounded-full font-semibold"
            style={{ background: "rgba(15, 110, 86, 0.1)", color: "var(--color-accent)" }}
          >
            {fundingLabel}
          </span>
        )}

        <span
          className="font-mono text-[10px] ml-auto font-medium"
          style={{ color: "var(--color-ink-soft)" }}
        >
          {Math.round(study.confidence * 100)}% confidence
        </span>
      </div>

      {/* Claim */}
      <p className="text-sm leading-snug mb-3 font-semibold" style={{ color: "var(--color-ink)" }}>
        {study.claim}
      </p>

      {/* Reason */}
      <p className="text-xs mb-3 leading-relaxed" style={{ color: "var(--color-ink-soft)" }}>
        {study.reason}
      </p>

      {/* Population context if available */}
      {(study.pop_age_group || study.pop_condition) && (
        <p className="text-xs mb-3 p-2 rounded-lg" style={{ background: "rgba(15, 110, 86, 0.06)", color: "var(--color-ink-soft)" }}>
          <span className="font-semibold text-accent">👥 Population:</span>{" "}
          {[study.pop_age_group, study.pop_condition, study.pop_severity]
            .filter(Boolean)
            .filter(v => v !== "unknown")
            .join(", ")}
        </p>
      )}

      {/* Footer */}
      <div
        className="flex items-center gap-2 text-[11px] pt-3 border-t flex-wrap"
        style={{ color: "var(--color-ink-soft)", borderColor: "rgba(0, 0, 0, 0.06)" }}
      >
        <span className="font-mono font-semibold">PMID {study.pmid}</span>
        {study.year && <span>· {study.year}</span>}
        {study.journal && <span className="truncate">· {study.journal}</span>}
        {study.sample_size && <span>· n={study.sample_size.toLocaleString()}</span>}
        {study.quality_duration_weeks && (
          <span>· {study.quality_duration_weeks}w duration</span>
        )}
      </div>
    </a>
  );
}