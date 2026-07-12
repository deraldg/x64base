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
    "x64base and DotTalk++ form the glass-but-real substrate of a configurable Laboratory Campus for building, inspecting, documenting, and teaching data systems.",
  openGraph: {
    type: "website",
    title: "x64base",
    description:
      "A glass-but-real database engine, language, documentation system, and configurable Laboratory Campus.",
    url: "https://x64base.com",
    siteName: "x64base",
    images: [
      {
        url: "/og.png",
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
      "A glass-but-real database engine, language, documentation system, and configurable Laboratory Campus.",
    images: ["/og.png"]
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
        <Navbar />
        <main className="mx-auto w-full max-w-6xl px-4 py-10">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
