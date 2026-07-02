import { Card } from "@/components/Card";

const items = [
  { href: "/brand/trademarks", title: "Trademarks", description: "Marks, attribution, and usage rules." },
  { href: "/brand/usage-guide", title: "Usage Guide", description: "Tone, wording, and naming conventions." },
  { href: "/brand/visual-identity", title: "Visual Identity", description: "Palette, type, and iconography." },
  { href: "/brand/logo-concepts", title: "Logo Concepts", description: "Concept directions and application notes." }
];

export default function BrandPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Brand</h1>
        <p className="text-muted">
          Technical, educational, historical, and modern. This section gathers trademark language, usage guidance,
          and the visual identity system.
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
