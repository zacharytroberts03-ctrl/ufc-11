import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider, Show, UserButton } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FightZ — UFC Fight Analysis",
  description:
    "Specialist-agent fight analysis, fighter ratings, and calculated odds for UFC events.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        variables: {
          colorPrimary: "#dc0000",
          colorBackground: "#1a1a1a",
        },
      }}
    >
      <html lang="en" className={inter.variable}>
        <body className="min-h-screen text-ufc-text">
          {/* Nav */}
          <header className="sticky top-0 z-50 border-b-2 border-ufc-red bg-[#111111]/95 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
              <a href="/" className="flex items-center gap-2 group">
                <span className="text-white text-xl font-black tracking-tighter">
                  Fight
                </span>
                <span className="text-ufc-red text-xl font-black tracking-tighter">
                  Z
                </span>
              </a>

              <div className="flex items-center gap-2">
                <Show when="signed-out">
                  <a
                    href="/sign-in"
                    className="text-white text-sm font-semibold px-3 py-2 rounded hover:bg-white/10 transition-colors min-h-[44px] inline-flex items-center"
                  >
                    Sign In
                  </a>
                  <a
                    href="/sign-up"
                    className="bg-ufc-red text-white text-sm font-bold px-4 py-2 rounded hover:bg-ufc-red-dark transition-colors min-h-[44px] inline-flex items-center"
                  >
                    Sign Up
                  </a>
                </Show>
                <Show when="signed-in">
                  <a
                    href="/account"
                    className="text-white text-sm font-semibold px-3 py-2 rounded hover:bg-white/10 transition-colors min-h-[44px] hidden sm:inline-flex items-center"
                  >
                    Account
                  </a>
                  <UserButton
                    appearance={{
                      elements: {
                        avatarBox: "w-9 h-9",
                      },
                    }}
                  />
                </Show>
              </div>
            </div>
          </header>

          <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">{children}</main>

          <footer className="border-t-2 border-ufc-red mt-16 py-8 text-center text-ufc-muted text-xs">
            <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 mb-3">
              <a
                href="/privacy"
                className="hover:text-white transition-colors py-1 px-1 min-h-[44px] inline-flex items-center"
              >
                Privacy
              </a>
              <span className="opacity-40">·</span>
              <a
                href="/terms"
                className="hover:text-white transition-colors py-1 px-1 min-h-[44px] inline-flex items-center"
              >
                Terms
              </a>
            </div>
            <div>Stats from ufcstats.com · Odds from The Odds API</div>
          </footer>
        </body>
      </html>
    </ClerkProvider>
  );
}
