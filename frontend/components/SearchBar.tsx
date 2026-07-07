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
          className="w-full resize-none rounded-2xl border px-6 py-5 pr-40 text-base leading-relaxed focus:outline-none focus:ring-2 focus:ring-offset-0 transition-all"
          style={{
            background: "rgba(255, 255, 255, 0.9)",
            borderColor: "rgba(15, 110, 86, 0.3)",
            color: "var(--color-ink)",
            fontFamily: "var(--font-body)",
            boxShadow: "0 8px 24px rgba(15, 110, 86, 0.08)"
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
          className="absolute right-4 bottom-4 px-6 py-2.5 rounded-full text-sm font-semibold transition-all disabled:opacity-40 hover:scale-105 accent-btn"
        >
          {isLoading ? "Debating…" : "Debate"}
        </button>
      </form>

      <div className="mt-5">
        <p className="text-xs font-semibold mb-3" style={{ color: "var(--color-ink-soft)" }}>
          Try these questions:
        </p>
        <div className="flex flex-col gap-2">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => !isLoading && onSubmit(q)}
              disabled={isLoading}
              className="text-sm px-4 py-3 rounded-xl border transition-all hover:scale-[1.02] hover:shadow-md disabled:opacity-40 font-medium text-left"
              style={{ 
                borderColor: "rgba(15, 110, 86, 0.5)", 
                color: "var(--color-ink)",
                background: "rgba(15, 110, 86, 0.12)",
                cursor: isLoading ? "not-allowed" : "pointer"
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}