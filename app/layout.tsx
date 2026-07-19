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
    default: "x64base — A C++20 DBF Runtime and DotTalk++ Shell",
    template: "%s — x64base"
  },
  description:
    "Open, inspect, index, relate, and script DBF-family data with the active-beta x64base C++20 runtime and DotTalk++ shell.",
  openGraph: {
    type: "website",
    title: "x64base",
    description:
      "An active-beta C++20 DBF-family runtime and inspectable DotTalk++ command shell.",
    url: "https://x64base.com",
    siteName: "x64base",
    images: [
      {
        url: "/images/brand/x64base-campus-social-card.png",
        width: 1730,
        height: 909,
        alt: "x64base — A glass-box database engine and configurable Laboratory Campus"
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: "x64base",
    description:
      "An active-beta C++20 DBF-family runtime and inspectable DotTalk++ command shell.",
    images: ["/images/brand/x64base-campus-social-card.png"]
  },
  icons: {
    icon: [
      {
        url: "/images/brand/x64base-smiling-database-site-icon.jpg",
        type: "image/jpeg"
      }
    ],
    shortcut: ["/images/brand/x64base-smiling-database-site-icon.jpg"],
    apple: ["/images/brand/x64base-smiling-database-site-icon.jpg"]
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen">
        <div className="border-b border-border bg-card/40 px-4 py-1.5 text-center text-xs text-muted">
          This site is <span className="text-fg">AI-generated</span> from the x64base project
          {" · "}
          <span className="font-mono text-brand">ALPHA</span>
          {" · "}
          Updated 2026-07-19
        </div>
        <Navbar />
        <main className="mx-auto w-full max-w-6xl px-4 py-10">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
