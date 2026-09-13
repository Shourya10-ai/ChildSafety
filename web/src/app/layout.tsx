import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Child Safety — AI-Powered Child Safety Platform",
  description: "A privacy-preserving, human-in-the-loop child protection ecosystem. Moderator and authority portal for case management, AI flag review, and cross-case intelligence.",
  keywords: ["child safety", "AI", "moderation", "protection", "India"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        {children}
      </body>
    </html>
  );
}
