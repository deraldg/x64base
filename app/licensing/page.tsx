import { Card } from "@/components/Card";

const items = [
  { href: "/licensing/overview", title: "Overview", description: "How the hybrid licensing model fits together." },
  { href: "/licensing/mit-license-engine", title: "MIT License (Engine)", description: "Open licensing for the core engine." },
  {
    href: "/licensing/dottalk-educational-license",
    title: "DotTalk++ Educational License",
    description: "Use DotTalk++ in classrooms and curricula."
  },
  {
    href: "/licensing/labtalk-non-profit-license",
    title: "LabTalk Non-Profit License",
    description: "Free usage for non-profits and learning labs."
  }
];

export default function LicensingPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Tentative Licensing Agreement</h1>
        <p className="text-muted">
          x64base uses a hybrid model: open licensing for the core engine, educational licensing for DotTalk++,
          and a free non-profit edition via LabTalk.
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
