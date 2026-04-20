import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InvestResearch — AI-Powered Investment Dashboard",
  description: "An AI-powered investment research dashboard that dynamically gathers financial data from multiple sources, analyzes it using an intelligent agent, and presents structured, explainable insights.",
  keywords: ["investment", "research", "AI", "financial analysis", "stock market", "dashboard"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
