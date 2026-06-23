import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClinicalMind — Where Evidence Argues With Itself",
  description: "An evidence intelligence platform that surfaces contradictions in medical literature instead of hiding them in a one-sided summary.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}