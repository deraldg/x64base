import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  metadataBase: new URL("https://x64base.com"),
  title: {
    default: "x64base — DotTalk++ database runtime lab",
    template: "%s — x64base"
  },
  description:
    "DotTalk++ / x64base is an active beta educational database runtime for DBF-style tables, indexes, memos, metadata, command shells, browsers, and GUI experiments.",
  openGraph: {
    type: "website",
    title: "x64base",
    description:
      "An active beta educational database runtime for DBF-style tables, indexes, memos, metadata, command shells, browsers, and GUI experiments.",
    url: "https://x64base.com",
    siteName: "x64base",
    images: [{ url: "/og.svg", width: 1200, height: 630, alt: "x64base" }]
  },
  twitter: {
    card: "summary_large_image",
    title: "x64base",
    description:
      "An active beta educational database runtime for DBF-style tables, indexes, memos, metadata, command shells, browsers, and GUI experiments.",
    images: ["/og.svg"]
  },
  icons: [{ rel: "icon", url: "/favicon.svg" }]
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen">
        <Navbar />
        <main className="mx-auto w-full max-w-6xl px-4 py-10">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
