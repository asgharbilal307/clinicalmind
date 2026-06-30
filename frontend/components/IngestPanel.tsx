"use client";

import { useState, FormEvent } from "react";
import { api, ApiError } from "@/lib/api";

interface IngestPanelProps {
  onIngestComplete?: (topic: string) => void;
}

const MAX_RESULTS = 25; // capped low to protect shared Groq quota on a public demo
const COOLDOWN_SECONDS = 120; // prevents rapid repeated ingestion from one visitor

type IngestState = "idle" | "loading" | "success" | "error";

export function IngestPanel({ onIngestComplete }: IngestPanelProps) {
  const [topic, setTopic] = useState("");
  const [state, setState] = useState<IngestState>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const now = Date.now();
  const onCooldown = cooldownUntil !== null && now < cooldownUntil;
  const cooldownRemaining = onCooldown
    ? Math.ceil((cooldownUntil! - now) / 1000)
    : 0;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!topic.trim() || state === "loading" || onCooldown) return;

    setState("loading");
    setMessage(null);

    try {
      const result = await api.ingest(topic.trim(), MAX_RESULTS);
      setState("success");
      setMessage(
        `Ingested ${result.abstracts_stored} new studies, ` +
          `${result.claims_extracted} claims extracted, ` +
          `${result.metadata_extracted} metadata records. ` +
          `You can now ask questions about "${topic.trim()}".`
      );
      setCooldownUntil(Date.now() + COOLDOWN_SECONDS * 1000);
      onIngestComplete?.(topic.trim());
      setTopic("");
    } catch (e) {
      setState("error");
      setMessage(
        e instanceof ApiError
          ? e.message
          : "Couldn't reach the ingestion service. Try again shortly."
      );
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-colors hover:bg-black/5"
        style={{ borderColor: "var(--color-border)", color: "var(--color-ink-soft)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <path d="M6 2v8M2 6h8" />
        </svg>
        Add a new topic to the evidence base
      </button>
    );
  }

  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: "var(--color-paper-raised)", border: "1px solid var(--color-border)" }}
    >
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium" style={{ color: "var(--color-ink)" }}>
          Ingest a new topic from PubMed
        </p>
        <button
          onClick={() => setIsOpen(false)}
          className="text-xs"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Close
        </button>
      </div>

      <p className="text-xs mb-3" style={{ color: "var(--color-ink-soft)" }}>
        Pulls up to {MAX_RESULTS} abstracts live from PubMed, extracts claims and
        Phase 2 metadata (funding, quality, population) with an LLM. Takes roughly
        3–5 minutes.
      </p>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. melatonin sleep quality"
          disabled={state === "loading" || onCooldown}
          className="flex-1 rounded-full border px-4 py-2 text-sm disabled:opacity-50"
          style={{
            background: "var(--color-paper)",
            borderColor: "var(--color-border)",
            color: "var(--color-ink)",
          }}
        />
        <button
          type="submit"
          disabled={!topic.trim() || state === "loading" || onCooldown}
          className="px-4 py-2 rounded-full text-sm font-medium disabled:opacity-40 whitespace-nowrap"
          style={{ background: "var(--color-ink)", color: "var(--color-paper)" }}
        >
          {state === "loading"
            ? "Ingesting…"
            : onCooldown
              ? `Wait ${cooldownRemaining}s`
              : "Ingest"}
        </button>
      </form>

      {state === "loading" && (
        <div className="flex items-center gap-2 mt-3">
          <span className="w-3 h-3 rounded-full border-2 border-black/10 border-t-black/40 animate-spin" />
          <p className="text-xs" style={{ color: "var(--color-ink-soft)" }}>
            Fetching abstracts, extracting claims and metadata — this runs sequentially
            to respect free-tier rate limits, please be patient.
          </p>
        </div>
      )}

      {message && state !== "loading" && (
        <p
          className="text-xs mt-3 p-2 rounded-lg"
          style={{
            background: state === "success" ? "var(--color-support-bg)" : "var(--color-contradict-bg)",
            color: state === "success" ? "var(--color-support)" : "var(--color-contradict)",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}