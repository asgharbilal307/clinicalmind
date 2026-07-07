"use client";

const STAGES = [
  "Retrieving relevant studies…",
  "Classifying each study's stance…",
  "Weighing evidence by study quality…",
  "Drafting the referee's verdict…",
];

import { useEffect, useState } from "react";

export function DebateLoadingState() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStage((s) => Math.min(s + 1, STAGES.length - 1));
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-24 gap-6 px-6" aria-live="polite">
      <div className="flex items-center gap-6 max-w-md">
        <div className="w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "linear-gradient(135deg, var(--color-accent), #0D4C3E)", boxShadow: "0 8px 24px rgba(15, 110, 86, 0.25)" }}>
          <svg className="w-8 h-8 text-white animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2v4" stroke="rgba(255,255,255,0.95)" strokeWidth="2" strokeLinecap="round" />
            <path d="M12 18v4" stroke="rgba(255,255,255,0.25)" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <div className="text-left">
          <p className="text-base font-semibold mb-1" style={{ color: "var(--color-ink)" }}>{STAGES[stage]}</p>
          <p className="text-sm" style={{ color: "var(--color-ink-soft)" }}>This may take a few seconds for complex queries.</p>
          <div className="mt-3 flex gap-1">
            {STAGES.map((_, i) => (
              <div
                key={i}
                className="h-1 rounded-full transition-all"
                style={{
                  width: i <= stage ? "12px" : "4px",
                  background: i <= stage ? "var(--color-accent)" : "rgba(0, 0, 0, 0.1)"
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}