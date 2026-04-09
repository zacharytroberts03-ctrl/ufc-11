import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "UFC Fight Analyzer",
  description: "AI-powered UFC fight analysis and hedge betting calculator",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen text-ufc-text">
        {/* Nav */}
        <header className="sticky top-0 z-50 border-b-2 border-ufc-red bg-[#111111]/95 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2 group">
              <span className="text-white text-xl font-black tracking-tighter">
                UFC
              </span>
              <span className="text-white text-sm font-semibold tracking-widest uppercase opacity-80 group-hover:opacity-100 transition-opacity">
                Fight Analyzer
              </span>
            </a>
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs text-ufc-muted">
                <span className="w-1.5 h-1.5 rounded-full bg-ufc-green animate-pulse" />
                Live odds · AI analysis
              </span>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
          {children}
        </main>

        <footer className="border-t-2 border-ufc-red mt-16 py-8 text-center text-ufc-muted text-xs">
          Stats from ufcstats.com · AI by Claude · Odds from The Odds API
        </footer>
      </body>
    </html>
  );
}
