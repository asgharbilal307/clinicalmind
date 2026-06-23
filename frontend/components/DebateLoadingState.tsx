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
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-2 h-2 rounded-full animate-bounce"
            style={{
              background: "var(--color-ink-soft)",
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
      <p className="text-sm" style={{ color: "var(--color-ink-soft)" }}>
        {STAGES[stage]}
      </p>
    </div>
  );
}