import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Starfield from "@/components/Starfield";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });

export const metadata: Metadata = {
  title: "JRE Cosmic — Jyotish Reasoning Engine",
  description:
    "A classical Vedic astrology reasoning engine for empirical validation and beta testing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${playfair.variable}`}>
        <Starfield />
        <div className="relative z-10 min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <footer className="border-t border-white/5 py-5 text-center text-xs" style={{ color: 'var(--cosmic-muted)' }}>
            <div className="max-w-5xl mx-auto px-4">
              <p className="mb-1">
                JRE v1.0.0-beta — Engine frozen. No reasoning logic changes during beta.
              </p>
              <p style={{ opacity: 0.5 }}>
                Computational interpretation based on classical Vedic astrology rulesets (BPHS, Phaladeepika).
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
