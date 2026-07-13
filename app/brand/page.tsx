import { Card } from "@/components/Card";

const items = [
  { href: "/brand/visual-identity", title: "Visual Identity", description: "Palette, type, and iconography." },
  { href: "/brand/usage-guide", title: "Usage Guide", description: "Tone, wording, and naming conventions." },
  { href: "/brand/logo-concepts", title: "Logo Concepts", description: "Concept directions and application notes." },
  { href: "/brand/trademarks", title: "Trademark Notes", description: "Attribution and status notes for project names." }
];

export default function BrandPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Project Identity</h1>
        <p className="text-muted">
          Supporting notes for naming, visual consistency, and attribution. The engine, Laboratory Campus,
          documentation, and learning work remain the primary public story.
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
