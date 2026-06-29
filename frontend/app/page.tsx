"use client";

import { useState } from "react";
import { api, DebateOutput, ApiError } from "@/lib/api";
import { SearchBar } from "@/components/SearchBar";
import { TensionBar } from "@/components/TensionBar";
import { StudyCard } from "@/components/StudyCard";
import { DebateLoadingState } from "@/components/DebateLoadingState";
import { ForestPlot } from "@/components/ForestPlot";

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
      <header className="px-6 pt-16 pb-8 max-w-4xl mx-auto text-center hero-card rounded-3xl">
        <p
          className="font-mono text-xs uppercase tracking-[0.2em] mb-4"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Evidence Intelligence
        </p>
        <h1
          className="text-4xl sm:text-5xl leading-[1.1] mb-4"
          style={{ fontFamily: "var(--font-display)", color: "var(--color-ink)" }}
        >
          Where evidence argues with itself.
        </h1>
        <p
          className="text-base sm:text-lg max-w-2xl mx-auto"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Most medical AI averages studies into one tidy answer. ClinicalMind splits
          them into camps, weighs the evidence, and tells you why the science disagrees.
        </p>
      </header>

      {/* Search */}
      <section className="px-6 max-w-3xl mx-auto mb-12 -mt-6">
        <SearchBar onSubmit={runDebate} isLoading={isLoading} />
      </section>

      {/* Results */}
      <section className="px-6 max-w-5xl mx-auto pb-24">
        {isLoading && <DebateLoadingState />}

        {error && (
          <div
            className="max-w-xl mx-auto p-5 rounded-xl text-sm text-center"
            style={{ background: "var(--color-contradict-bg)", color: "var(--color-contradict)" }}
          >
            {error}
          </div>
        )}

        {isInsufficient && (
          <div
            className="max-w-xl mx-auto p-6 rounded-xl text-center"
            style={{ background: "var(--color-neutral-bg)" }}
          >
            <p className="text-sm font-medium mb-1" style={{ color: "var(--color-ink)" }}>
              Not enough evidence to stage a debate.
            </p>
            <p className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
              {result?.verdict}
            </p>
          </div>
        )}

        {hasDebate && result && (
          <div className="space-y-10">
            {/* Question recap + tension bar */}
            <div
              className="p-6 rounded-2xl"
              style={{ background: "var(--color-paper-raised)", border: "1px solid var(--color-border)" }}
            >
              <p
                className="text-lg mb-5"
                style={{ fontFamily: "var(--font-display)", color: "var(--color-ink)" }}
              >
                &ldquo;{result.query}&rdquo;
              </p>
              <TensionBar
                supportingCount={result.supporting.length}
                contradictingCount={result.contradicting.length}
                consensusStrength={result.consensus_strength}
              />
            </div>

            {/* Referee verdict */}
            <div
              className="p-6 rounded-2xl"
              style={{ background: "var(--color-verdict-bg)" }}
            >
              <p
                className="font-mono text-xs uppercase tracking-wider mb-2"
                style={{ color: "var(--color-verdict)" }}
              >
                Why the evidence disagrees
              </p>
              <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--color-ink)" }}>
                {result.conflict_explanation}
              </p>
              <p
                className="font-mono text-xs uppercase tracking-wider mb-2"
                style={{ color: "var(--color-verdict)" }}
              >
                Referee&rsquo;s verdict
              </p>
              <p className="text-sm leading-relaxed" style={{ color: "var(--color-ink)" }}>
                {result.verdict}
              </p>
            </div>

            {/* Funding bias banner — only shown when bias is detected */}
            {result.funding_bias?.bias_flag && result.funding_bias.bias_note && (
              <div
                className="p-4 rounded-xl flex gap-3 items-start"
                style={{ background: "#FFF8E8", border: "1px solid #F0D080" }}
              >
                <span className="text-lg leading-none mt-0.5">⚠️</span>
                <div>
                  <p
                    className="font-mono text-xs uppercase tracking-wider mb-1"
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
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <h2
                  className="text-sm font-medium mb-3 flex items-center gap-2"
                  style={{ color: "var(--color-support)" }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: "var(--color-support)" }} />
                  Supports the claim
                </h2>
                <div className="space-y-3">
                  {result.supporting.map((s) => (
                    <StudyCard key={s.pmid} study={s} variant="support" />
                  ))}
                </div>
              </div>

              <div>
                <h2
                  className="text-sm font-medium mb-3 flex items-center gap-2"
                  style={{ color: "var(--color-contradict)" }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: "var(--color-contradict)" }} />
                  Contradicts the claim
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
                  className="text-sm font-medium mb-3 flex items-center gap-2"
                  style={{ color: "var(--color-neutral)" }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: "var(--color-neutral)" }} />
                  Inconclusive or unrelated
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
          <div className="text-center py-16">
            <p className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
              Try one of the example questions above, or ask your own.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}