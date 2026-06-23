"use client";

import { useState, FormEvent } from "react";

interface SearchBarProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const EXAMPLE_QUERIES = [
  "Does intermittent fasting lead to greater weight loss than continuous calorie restriction?",
  "Does vitamin D supplementation reduce the risk of depression?",
  "Should statins be prescribed to healthy adults for primary prevention?",
];

export function SearchBar({ onSubmit, isLoading }: SearchBarProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (value.trim() && !isLoading) {
      onSubmit(value.trim());
    }
  }

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask a clinical question the literature disagrees on…"
          rows={2}
          className="w-full resize-none rounded-2xl border px-5 py-4 pr-32 text-base leading-relaxed focus-visible:outline-2 focus-visible:outline-offset-2"
          style={{
            background: "var(--color-paper-raised)",
            borderColor: "var(--color-border)",
            color: "var(--color-ink)",
            fontFamily: "var(--font-body)",
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !value.trim()}
          className="absolute right-3 bottom-3 px-5 py-2 rounded-full text-sm font-medium transition-opacity disabled:opacity-40"
          style={{ background: "var(--color-ink)", color: "var(--color-paper)" }}
        >
          {isLoading ? "Debating…" : "Debate"}
        </button>
      </form>

      <div className="flex flex-wrap gap-2 mt-3">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => !isLoading && onSubmit(q)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-full border transition-colors hover:bg-black/5 disabled:opacity-40"
            style={{ borderColor: "var(--color-border)", color: "var(--color-ink-soft)" }}
          >
            {q.length > 50 ? q.slice(0, 50) + "…" : q}
          </button>
        ))}
      </div>
    </div>
  );
}