import Image from "next/image";
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

      <figure className="overflow-hidden rounded-lg border border-border bg-card shadow-soft">
        <Image
          src="/images/brand/x64base-campus-social-card.png"
          alt="x64base — A glass-box database engine and configurable Laboratory Campus"
          width={1730}
          height={909}
          className="h-auto w-full"
        />
        <figcaption className="border-t border-border px-4 py-3 text-sm text-muted">
          Current x64base and Laboratory Campus social card.
        </figcaption>
      </figure>

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((i) => (
          <Card key={i.href} title={i.title} description={i.description} href={i.href} />
        ))}
      </div>
    </div>
  );
}
