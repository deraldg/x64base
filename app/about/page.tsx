import { Card } from "@/components/Card";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About x64base — History, Purpose, and Architecture",
  description: "The history, purpose, evidence model, and research architecture behind x64base and DotTalk++."
};

const items = [
  { title: "Mission & Vision", description: "The Laboratory Campus direction and the project’s proof-backed purpose.", href: "/about/mission-vision" },
  {
    title: "Origin Story (1993–2026)",
    description: "How the x64base lineage began and why it matters.",
    href: "/about/origin-story"
  },
  { title: "Timeline", description: "Key milestones from 1993 to 2026.", href: "/about/timeline" },
  { title: "Project Story", description: "Tone, positioning, and the codex-style clarity.", href: "/about/brand-story" },
  { title: "Contributors", description: "Human and AI contributors recognized in the project record.", href: "/about/contributors" },
  { title: "Project Identity", description: "Naming, visual identity, attribution, and trademark notes.", href: "/brand" },
  { title: "Project Notice", description: "A concise statement of the public source’s tentative license status.", href: "/licensing" }
];

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">About</h1>
        <p className="text-muted">
          x64base is built on three decades of engineering, teaching, and historical computing experience.
          This section captures the lineage, intent, mission, and project foundations.
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
