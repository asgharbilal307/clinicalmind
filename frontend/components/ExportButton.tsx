"use client";

import { useState } from "react";

interface ExportButtonProps {
  query: string;
  topK?: number;
}

export function ExportButton({ query, topK = 20 }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setIsExporting(true);
    setError(null);

    try {
      const API_BASE =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const res = await fetch(`${API_BASE}/export/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: topK }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Export failed: ${res.status}`);
      }

      // Trigger browser download
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        `clinicalmind_${query.slice(0, 40).replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_-]/g, "")}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleExport}
        disabled={isExporting}
        className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all disabled:opacity-50"
        style={{
          background: "var(--color-ink)",
          color: "var(--color-paper)",
        }}
      >
        {isExporting ? (
          <>
            <span
              className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin"
            />
            Generating PDF…
          </>
        ) : (
          <>
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M7 1v8M4 6l3 3 3-3M2 11h10" />
            </svg>
            Export PDF
          </>
        )}
      </button>
      {error && (
        <span className="text-[11px]" style={{ color: "var(--color-contradict)" }}>
          {error}
        </span>
      )}
    </div>
  );
}