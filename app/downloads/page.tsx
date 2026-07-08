import Link from "next/link";
import { Archive, BookOpen, Download, FileText, Github, PackageCheck, ScrollText } from "lucide-react";
import { Card } from "@/components/Card";

const startingPoints = [
  {
    title: "Source Repository",
    description: "Public source, history, issues, and the GitHub Pages publication branch.",
    href: "https://github.com/deraldg/x64base",
    icon: Github,
    external: true
  },
  {
    title: "Build Instructions",
    description: "Current Windows, POSIX, WSL/Ubuntu, and macOS-oriented build notes.",
    href: "/docs/getting-started/installation",
    icon: BookOpen
  },
  {
    title: "Runtime Footprint",
    description: "Observed release payload: dottalkpp.exe, lmdb.dll, sqlite3.dll, and what each file does.",
    href: "/docs/engine/runtime-footprint",
    icon: PackageCheck
  },
  {
    title: "Command Catalog",
    description: "The reviewed command surface that should be regenerated as DotTalk++ changes.",
    href: "/docs/dottalk/command-catalog",
    icon: ScrollText
  },
  {
    title: "Runtime Evidence",
    description: "Screenshots and proof artifacts curated as evidence, not release polish claims.",
    href: "/docs/labtalk/runtime-evidence",
    icon: Archive
  },
  {
    title: "Important Documents",
    description: "A map of SelfDoc, MDO, generated manuals, matrices, and proof-backed documentation layers.",
    href: "/docs/dev/important-documents",
    icon: FileText
  }
];

export default function DownloadsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">downloads</p>
        <h1 className="text-3xl font-semibold tracking-tight">A place to start</h1>
        <p className="text-muted">
          This page collects the practical starting points for x64base and DotTalk++. It is not a
          packaged-product storefront; it points to source, build notes, runtime evidence, command
          references, and the current release-shape documentation.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-card/40 p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Current public source</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              The canonical public project location is GitHub. Built runtime bundles should be
              treated as staged artifacts only when they are explicitly published and versioned.
            </p>
          </div>
          <a
            href="https://github.com/deraldg/x64base"
            target="_blank"
            rel="noreferrer"
            className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-border bg-bg/40 px-4 py-2 text-sm font-semibold text-fg transition hover:border-brand/60"
          >
            <Github size={16} aria-hidden="true" />
            GitHub
          </a>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {startingPoints.map((item) => {
          const Icon = item.icon;
          const body = (
            <Card title={item.title} description={item.description}>
              <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
            </Card>
          );

          return item.external ? (
            <a key={item.href} href={item.href} target="_blank" rel="noreferrer" className="block">
              {body}
            </a>
          ) : (
            <Link key={item.href} href={item.href} className="block">
              {body}
            </Link>
          );
        })}
      </div>

      <section className="rounded-lg border border-border bg-card/35 p-5 text-sm leading-6 text-muted">
        <div className="flex items-start gap-3">
          <Download className="mt-1 h-5 w-5 shrink-0 text-brand" aria-hidden="true" />
          <p>
            As release packaging matures, this page can grow into a manifest for reviewed binaries,
            source archives, generated manuals, diagrams, checksums, and proof bundles. Until then,
            it stays deliberately simple: start with the source, build notes, and evidence pages.
          </p>
        </div>
      </section>
    </div>
  );
}
