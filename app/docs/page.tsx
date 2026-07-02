import Link from "next/link";
import { Card } from "@/components/Card";
import { docsSidebar } from "@/config/sidebars";

const quickLinks = [
  {
    title: "Getting Started",
    description: "Understand the active beta runtime and where to begin.",
    href: "/docs/getting-started/overview"
  },
  {
    title: "Engine Architecture",
    description: "Observed source layout, build options, and runtime boundaries.",
    href: "/docs/engine/architecture"
  },
  {
    title: "DotTalk++",
    description: "Language guide, syntax, REPL, examples, curriculum.",
    href: "/docs/dottalk/language-guide"
  },
  {
    title: "Developer Resources",
    description: "Current project truth, handbook, onboarding, and standards.",
    href: "/docs/dev/project-truth"
  }
];

export default function DocsLandingPage() {
  const count = docsSidebar.reduce((n, g) => n + g.items.length, 0);

  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Documentation</h1>
        <p className="text-muted">
          References for the local DotTalk++ / x64base runtime, command surfaces, engine work, and
          teaching workflows. ({count} pages)
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {quickLinks.map((l) => (
          <Card key={l.href} title={l.title} description={l.description} href={l.href} />
        ))}
      </div>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <h2 className="text-lg font-semibold tracking-tight">Browse by section</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {docsSidebar.map((g) => (
            <div key={g.label} className="rounded-2xl border border-border bg-bg/20 p-4">
              <div className="text-sm font-semibold">{g.label}</div>
              <ul className="mt-2 space-y-1 text-sm">
                {g.items.slice(0, 4).map((i) => (
                  <li key={i.href}>
                    <Link href={i.href} className="text-brand hover:underline">
                      {i.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
