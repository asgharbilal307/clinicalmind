"use client";

import { useState } from "react";
import { api, DebateOutput, ApiError } from "@/lib/api";
import { SearchBar } from "@/components/SearchBar";
import { TensionBar } from "@/components/TensionBar";
import { StudyCard } from "@/components/StudyCard";
import { DebateLoadingState } from "@/components/DebateLoadingState";
import { ForestPlot } from "@/components/ForestPlot";
import { ExportButton } from "@/components/ExportButton";
import { IngestPanel } from "@/components/IngestPanel";

export default function Home() {
  const [result, setResult] = useState<DebateOutput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runDebate(query: string) {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.debate(query, 20);
      setResult(data);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError("Something went wrong reaching the ClinicalMind API. Is the backend running?");
      }
    } finally {
      setIsLoading(false);
    }
  }

  const hasDebate =
    result && (result.supporting.length > 0 || result.contradicting.length > 0);
  const isInsufficient =
    result && result.consensus_strength === "Insufficient evidence" && !hasDebate;

  return (
    <main className="min-h-screen">
      {/* Hero */}
      <header className="px-6 pt-20 pb-12 max-w-4xl mx-auto text-center hero-card rounded-3xl mt-8 mb-16">
        <p
          className="font-mono text-xs uppercase tracking-[0.3em] mb-6 font-semibold"
          style={{ color: "var(--color-accent)" }}
        >
          🔬 Evidence Intelligence
        </p>
        <h1
          className="text-5xl sm:text-6xl leading-[1.1] mb-6 font-bold"
          style={{ fontFamily: "var(--font-display)", color: "var(--color-ink)" }}
        >
          Where evidence <span className="gradient-text">argues with itself.</span>
        </h1>
        <p
          className="text-base sm:text-lg max-w-2xl mx-auto leading-relaxed"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Most medical AI averages studies into one tidy answer. ClinicalMind splits
          them into camps, weighs the evidence, and tells you why the science disagrees.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-effect text-xs">
            <span>✓</span> Evidence-based
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-effect text-xs">
            <span>✓</span> Transparent
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-effect text-xs">
            <span>✓</span> Nuanced
          </div>
        </div>
      </header>

      {/* Search */}
      <section className="px-6 max-w-2xl mx-auto mb-16">
        <SearchBar onSubmit={runDebate} isLoading={isLoading} />
        <div className="mt-4 flex justify-center">
          <IngestPanel />
        </div>
      </section>

      {/* Results */}
      <section className="px-6 max-w-5xl mx-auto pb-24">
        {isLoading && <DebateLoadingState />}

        {error && (
          <div
            className="max-w-xl mx-auto p-6 rounded-xl text-sm text-center font-medium border"
            style={{ background: "var(--color-contradict-bg)", color: "var(--color-contradict)", borderColor: "var(--color-contradict)" }}
          >
            ⚠️ {error}
          </div>
        )}

        {isInsufficient && (
          <div
            className="max-w-xl mx-auto p-8 rounded-2xl text-center border"
            style={{ background: "var(--color-neutral-bg)", borderColor: "var(--color-neutral)" }}
          >
            <p className="text-base font-semibold mb-2" style={{ color: "var(--color-ink)" }}>
              Not enough evidence to stage a debate.
            </p>
            <p className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
              {result?.verdict}
            </p>
          </div>
        )}

        {hasDebate && result && (
          <div className="space-y-8">
            {/* Question recap + tension bar */}
            <div
              className="p-8 rounded-2xl border"
              style={{ background: "rgba(255, 255, 255, 0.95)", borderColor: "rgba(15, 110, 86, 0.1)", boxShadow: "0 8px 24px rgba(15, 110, 86, 0.08)" }}
            >
              <p
                className="text-2xl mb-8 leading-relaxed font-bold"
                style={{ fontFamily: "var(--font-display)", color: "var(--color-ink)" }}
              >
                &ldquo;<span className="gradient-text">{result.query}</span>&rdquo;
              </p>
              <TensionBar
                supportingCount={result.supporting.length}
                contradictingCount={result.contradicting.length}
                consensusStrength={result.consensus_strength}
              />

              {/* Export button */}
              <div className="flex justify-end mt-8">
                <ExportButton query={result.query} topK={20} />
              </div>
            </div>

            {/* Referee verdict */}
            <div
              className="p-8 rounded-2xl border"
              style={{ background: "var(--color-verdict-bg)", borderColor: "var(--color-verdict)" }}
            >
              <p
                className="font-mono text-xs uppercase tracking-wider mb-3 font-bold"
                style={{ color: "var(--color-verdict)" }}
              >
                🔎 Why the evidence disagrees
              </p>
              <p className="text-base leading-relaxed mb-6" style={{ color: "var(--color-ink)" }}>
                {result.conflict_explanation}
              </p>
              <p
                className="font-mono text-xs uppercase tracking-wider mb-3 font-bold"
                style={{ color: "var(--color-verdict)" }}
              >
                ⚖️ Referee&rsquo;s verdict
              </p>
              <p className="text-base leading-relaxed" style={{ color: "var(--color-ink)" }}>
                {result.verdict}
              </p>
            </div>

            {/* Funding bias banner — only shown when bias is detected */}
            {result.funding_bias?.bias_flag && result.funding_bias.bias_note && (
              <div
                className="p-5 rounded-2xl flex gap-4 items-start border"
                style={{ background: "#FFFBF0", borderColor: "#F0D080" }}
              >
                <span className="text-2xl leading-none mt-0.5 flex-shrink-0">⚠️</span>
                <div className="flex-1">
                  <p
                    className="font-mono text-xs uppercase tracking-wider mb-2 font-bold"
                    style={{ color: "#8B6914" }}
                  >
                    Funding bias detected
                  </p>
                  <p className="text-sm leading-relaxed" style={{ color: "#5C4A0A" }}>
                    {result.funding_bias.bias_note}
                  </p>
                </div>
              </div>
            )}

            {/* Forest plot */}
            <ForestPlot
              supporting={result.supporting}
              contradicting={result.contradicting}
            />

            {/* Two-camp grid */}
            <div className="grid sm:grid-cols-2 gap-8">
              <div>
                <h2
                  className="text-lg font-bold mb-4 flex items-center gap-2"
                  style={{ color: "var(--color-support)" }}
                >
                  <span className="w-3 h-3 rounded-full" style={{ background: "var(--color-support)" }} />
                  ✓ Supports the claim
                </h2>
                <div className="space-y-3">
                  {result.supporting.map((s) => (
                    <StudyCard key={s.pmid} study={s} variant="support" />
                  ))}
                </div>
              </div>

              <div>
                <h2
                  className="text-lg font-bold mb-4 flex items-center gap-2"
                  style={{ color: "var(--color-contradict)" }}
                >
                  <span className="w-3 h-3 rounded-full" style={{ background: "var(--color-contradict)" }} />
                  ✗ Contradicts the claim
                </h2>
                <div className="space-y-3">
                  {result.contradicting.map((s) => (
                    <StudyCard key={s.pmid} study={s} variant="contradict" />
                  ))}
                </div>
              </div>
            </div>

            {/* Neutral studies */}
            {result.neutral.length > 0 && (
              <div>
                <h2
                  className="text-lg font-bold mb-4 flex items-center gap-2"
                  style={{ color: "var(--color-neutral)" }}
                >
                  <span className="w-3 h-3 rounded-full" style={{ background: "var(--color-neutral)" }} />
                  ◇ Inconclusive or unrelated
                </h2>
                <div className="grid sm:grid-cols-2 gap-3">
                  {result.neutral.map((s) => (
                    <StudyCard key={s.pmid} study={s} variant="neutral" />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!isLoading && !result && !error && (
          <div className="text-center py-20">
            <p className="text-base" style={{ color: "var(--color-ink-soft)" }}>
              Try one of the example questions above, or ask your own clinical question.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}