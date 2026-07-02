import { Card } from "@/components/Card";

const items = [
  {
    title: "Origin Story (1993–2026)",
    description: "How the x64base lineage began and why it matters.",
    href: "/about/origin-story"
  },
  { title: "Timeline", description: "Key milestones from 1993 to 2026.", href: "/about/timeline" },
  { title: "Brand Story", description: "Tone, positioning, and the codex-style clarity.", href: "/about/brand-story" },
  { title: "Mission & Vision", description: "Why x64base exists and where it’s going.", href: "/about/mission-vision" }
];

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">About</h1>
        <p className="text-muted">
          x64base is built on three decades of engineering, teaching, and historical computing experience.
          This section captures the lineage, intent, and brand foundations.
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
