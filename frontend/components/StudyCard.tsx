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
      className="block p-4 rounded-xl bg-[var(--color-paper-raised)] card-hoverable focus-visible:outline-2 focus-visible:outline-offset-2"
      style={{ borderLeft: `3px solid ${styles.border}`, outlineColor: styles.border }}
    >
      {/* Top row — study type + quality + confidence */}
      <div className="flex items-start flex-wrap gap-1.5 mb-2">
        <span
          className="font-mono text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full"
          style={{ background: styles.badge, color: styles.badgeText }}
        >
          {STUDY_TYPE_LABELS[study.study_type] ?? "Study"}
        </span>

        {study.quality_score && study.quality_score !== "unknown" && (
          <span
            className="font-mono text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full"
            style={{ background: quality.bg, color: quality.color }}
          >
            {quality.label}
          </span>
        )}

        {fundingLabel && (
          <span
            className="font-mono text-[10px] px-2 py-0.5 rounded-full"
            style={{ background: "var(--color-background-secondary)", color: "var(--color-text-secondary)" }}
          >
            {fundingLabel}
          </span>
        )}

        <span
          className="font-mono text-[10px] ml-auto"
          style={{ color: "var(--color-ink-soft)" }}
        >
          {Math.round(study.confidence * 100)}% confidence
        </span>
      </div>

      {/* Claim */}
      <p className="text-sm leading-snug mb-2" style={{ color: "var(--color-ink)" }}>
        {study.claim}
      </p>

      {/* Reason */}
      <p className="text-xs mb-3" style={{ color: "var(--color-ink-soft)" }}>
        {study.reason}
      </p>

      {/* Population context if available */}
      {(study.pop_age_group || study.pop_condition) && (
        <p className="text-[11px] mb-2" style={{ color: "var(--color-ink-soft)" }}>
          Population:{" "}
          {[study.pop_age_group, study.pop_condition, study.pop_severity]
            .filter(Boolean)
            .filter(v => v !== "unknown")
            .join(", ")}
        </p>
      )}

      {/* Footer */}
      <div
        className="flex items-center gap-2 text-[11px] pt-2 border-t flex-wrap"
        style={{ color: "var(--color-ink-soft)" }}
      >
        <span className="font-mono">PMID {study.pmid}</span>
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