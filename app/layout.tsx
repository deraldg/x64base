import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import currentWork from "@/public/artifacts/current-work-v1.json";

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

const siteVersion = process.env.NEXT_PUBLIC_SITE_VERSION ?? "local-preview";
const isLocalPreview = siteVersion === "local-preview";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen">
        {/* Theme no-flash: apply the stored preference (light default, owner
            ruling 2026-08-11) before anything paints. Runs synchronously as the
            first element in body; ThemeToggle keeps it in sync afterward. */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var t=localStorage.getItem('theme')||'light';var d=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);}catch(e){}})();"
          }}
        />
        <div className="border-b border-border bg-card/40 px-4 py-1.5 text-center text-xs text-muted">
          <span className="font-mono text-brand">WEBSITE ALPHA</span>
          {" · "}
          <span className="text-fg">AI-assisted, source-reviewed documentation</span>
          {" · "}
          Updated {currentWork.as_of_date}
          {isLocalPreview ? (
            <>
              {" · "}
              <span className="font-mono text-brand">LOCAL PREVIEW</span>
              {" · "}
              <a
                href="https://x64base.com"
                className="font-semibold text-brand underline underline-offset-4 hover:text-fg"
              >
                Go to the live site &rarr;
              </a>
            </>
          ) : null}
        </div>
        <Navbar />
        <main className="mx-auto w-full max-w-6xl px-4 py-10" data-pagefind-body>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
