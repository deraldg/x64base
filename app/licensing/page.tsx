import { Card } from "@/components/Card";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "x64base Licensing — Tentative MIT Status",
  description: "Current tentative MIT licensing status for the x64base public source, pending final review."
};

const items = [
  { href: "/licensing/overview", title: "Overview", description: "The current tentative decision and remaining review gate." },
  { href: "/licensing/mit-license-engine", title: "Tentative MIT License", description: "Proposed licensing for the public engine and runtime source." },
  {
    href: "/licensing/dottalk-educational-license",
    title: "DotTalk++ Educational License",
    description: "Planned guidance; no separate educational license is active."
  },
  {
    href: "/licensing/labtalk-non-profit-license",
    title: "LabTalk Non-Profit License",
    description: "Planned guidance; no separate non-profit license is active."
  },
  {
    href: "/licensing/third-party-acknowledgements",
    title: "Third-Party Acknowledgements",
    description: "Credits and official links for libraries, tools, and website dependencies."
  }
];

export default function LicensingPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Tentative Licensing Agreement</h1>
        <p className="text-muted">
          The public repository currently carries a tentative MIT license pending final maintainer and legal
          review. Earlier hybrid-license pages are retained only to clarify that separate educational and
          non-profit terms are planned, not active grants.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((i) => (
          <Card key={i.href} title={i.title} description={i.description} href={i.href} />
        ))}
      </div>
    </div>
  );
}
