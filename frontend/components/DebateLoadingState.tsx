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
    <div className="flex flex-col items-center justify-center py-20 gap-4" aria-live="polite">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: "linear-gradient(90deg, var(--color-accent), #0b5f4a)" }}>
          <svg className="w-6 h-6 text-white animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2v4" stroke="rgba(255,255,255,0.95)" strokeWidth="2" strokeLinecap="round" />
            <path d="M12 18v4" stroke="rgba(255,255,255,0.25)" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <div className="text-left">
          <p className="text-sm font-medium" style={{ color: "var(--color-ink)" }}>{STAGES[stage]}</p>
          <p className="text-xs" style={{ color: "var(--color-ink-soft)" }}>This may take a few seconds for complex queries.</p>
        </div>
      </div>
    </div>
  );
}