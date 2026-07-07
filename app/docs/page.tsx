import Link from "next/link";
import {
  Archive,
  BarChart3,
  BookOpen,
  Boxes,
  Code2,
  Database,
  FileText,
  GitBranch,
  GraduationCap,
  LayoutPanelTop,
  MonitorCog,
  Network,
  Ruler,
  ScrollText,
  TerminalSquare
} from "lucide-react";
import { Card } from "@/components/Card";
import { docsSidebar } from "@/config/sidebars";

const quickLinks = [
  {
    title: "Getting Started",
    description: "Understand the active beta runtime and where to begin.",
    href: "/docs/getting-started/overview",
    icon: BookOpen
  },
  {
    title: "Engine Architecture",
    description: "Observed source layout, build options, and runtime boundaries.",
    href: "/docs/engine/architecture",
    icon: Database
  },
  {
    title: "DotTalk++",
    description: "Language guide, syntax, REPL, examples, curriculum.",
    href: "/docs/dottalk/language-guide",
    icon: TerminalSquare
  },
  {
    title: "Developer Resources",
    description: "Current project truth, handbook, onboarding, and standards.",
    href: "/docs/dev/project-truth",
    icon: FileText
  }
];

const sectionSummary = [
  {
    title: "Feature comparison",
    description: "Compare x64base with Harbour, xHarbour, Alaska Xbase++, XSharp, dBASE tools, and Python DBF libraries.",
    href: "/docs/engine/ecosystem-feature-comparison",
    icon: BarChart3
  },
  {
    title: "x64 capacity math",
    description: "Teach why records, offsets, memos, indexes, locks, and APIs must all move from x32 to x64 together.",
    href: "/docs/engine/x64-capacity-math",
    icon: Ruler
  },
  {
    title: "Application UI DSL lane",
    description: "Track the proposed path for menus, windows, dialogs, controls, and event handlers in DotTalk++.",
    href: "/docs/dev/application-ui-dsl-lane",
    icon: LayoutPanelTop
  },
  {
    title: "Historical source lineage",
    description: "Preserve xBase, XDLL, DotTalk recovery, AI false starts, and modern DotTalk++ with proof labels.",
    href: "/docs/dev/historical-source-lineage",
    icon: Archive
  },
  {
    title: "Current work lanes",
    description: "Review active, planned, and alpha lanes without flattening them into finished-product claims.",
    href: "/docs/dev/current-lanes",
    icon: GitBranch
  },
  {
    title: "Site improvement plan",
    description: "Track documentation deficiencies, under-development lanes, and academic review needs.",
    href: "/docs/dev/site-improvement-plan",
    icon: FileText
  },
  {
    title: "SelfDoc publication",
    description: "See how local documentation layers feed generated manuals and the public website.",
    href: "/docs/dev/selfdoc-website-publication",
    icon: ScrollText
  },
  {
    title: "Website documentation matrix",
    description: "Map each public section to its source lane, data-mining feed, proof artifact, and status.",
    href: "/docs/dev/website-documentation-matrix",
    icon: Network
  },
  {
    title: "Parallel GUI/TUI",
    description: "Understand the supplied workbench surfaces and the shared engine boundary.",
    href: "/docs/talk-family/parallel-gui-tui",
    icon: MonitorCog
  },
  {
    title: "Laboratory Campus",
    description: "Follow the alpha education and collaboration area for database literacy and runtime proof work.",
    href: "/docs/labtalk/overview",
    icon: GraduationCap
  }
];

const commandSummary = [
  {
    title: "DotScript",
    description: "Scripts, variables, control flow, comments, line continuation, and one-level nesting.",
    href: "/docs/dottalk/dotscript-language-guide",
    icon: Code2
  },
  {
    title: "Data mutators",
    description: "REPLACE, CALC, CALCWRITE, MULTIREP, table buffering, dirty/stale state, commit, and rollback.",
    href: "/docs/dottalk/data-mutators",
    icon: Boxes
  },
  {
    title: "Command catalog",
    description: "The harvested command surface that should be regenerated when runtime commands change.",
    href: "/docs/dottalk/command-catalog",
    icon: TerminalSquare
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
        {quickLinks.map((l) => {
          const Icon = l.icon;
          return (
            <Card key={l.href} title={l.title} description={l.description} href={l.href}>
              <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
            </Card>
          );
        })}
      </div>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="max-w-3xl">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">section summary</p>
          <h2 className="mt-3 text-lg font-semibold tracking-tight">Pretty entry points for the current documentation shape</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            These links surface the important sections without pushing every lane onto the homepage.
          </p>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sectionSummary.map((l) => {
            const Icon = l.icon;
            return (
              <Card key={l.href} title={l.title} description={l.description} href={l.href}>
                <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
              </Card>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="max-w-3xl">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">command surfaces</p>
          <h2 className="mt-3 text-lg font-semibold tracking-tight">Script, mutate, and inspect</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            DotTalk++ already has data-programming lanes; the new UI DSL lane captures what is not implemented yet.
          </p>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {commandSummary.map((l) => {
            const Icon = l.icon;
            return (
              <Card key={l.href} title={l.title} description={l.description} href={l.href}>
                <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
              </Card>
            );
          })}
        </div>
      </section>

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
